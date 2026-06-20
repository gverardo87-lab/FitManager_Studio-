# PIANO DI IMPLEMENTAZIONE — SPEC_RINNOVI_SCADUTI_E_RETENTION (lente contratto)

**Versione:** 1.0
**Data:** 2026-06-20
**Owner:** Giacomo Verardo (AVGV Technologies)
**Esecutore:** Claude Code
**Spec:** `SPEC_RINNOVI_SCADUTI_E_RETENTION.md` (v1.0) · **ADR:** `ADR-015`

> Piano ancorato al codice reale (esplorazione 2026-06-20). Materiale di lavoro: superato dal codice
> + test. `file:riga` = fotografia al 2026-06-20. Perimetro: **lente contratto** (scaduti da
> rinnovare + esito "non rinnova"). Lente cliente (retention) = iterazione successiva (SPEC §6).

---

## 1. Ground-truth (file:riga)

- **Finestra solo-futura**: `get_expiring_contracts` (`dashboard.py:346-347`) e alert `expiring_contracts`
  (`dashboard.py:716-718`): `data_scadenza >= today AND <= today+30`, `chiuso=0`, `crediti_totali NOT NULL`,
  `crediti_usati < crediti_totali`. **Nessuna esclusione dei già-rinnovati.**
- **Nessuno stato terminale** "perso" sul `Contract` (`models/contract.py`).
- **Rinnovo figlio**: `Contract.rinnovo_di` (self-FK). "Rinnovato" = esiste figlio con `rinnovo_di = id`.
- **Aggiunta colonne**: `schema_sync` (`services/schema_sync.py`) fa ADD COLUMN delle colonne mancanti
  dai modelli ORM — idempotente, ADD-only, gira in frozen, solo crm.db. → un campo **nullable** sul
  modello si propaga ai DB deployati senza migrazione manuale. (Alembic resta per completezza.)
- **Frontend**: `/rinnovi-incassi` (`rinnovi-incassi/page.tsx`) usa `useExpiringContracts`; `RenewalCard`
  ha CTA "Rinnova" (riusa flusso SPEC_RINNOVO) + WhatsApp. Sezioni: "Contratti da rinnovare" + "Incassi in ritardo".
- **Residuo/crediti**: residuo = `prezzo_totale − totale_versato`; crediti usati = COUNT eventi PT non cancellati.

---

## 2. Modello dato — stato "non rinnova" (Criterio B)

Nuovi campi **nullable** su `Contract` (auto-propagati da schema_sync):
- `esito_rinnovo_motivo: Optional[str]` — codice motivo (null = opportunità aperta; valorizzato = perso).
- `esito_rinnovo_note: Optional[str]` — testo libero opzionale.
- `esito_rinnovo_il: Optional[date]` — quando deciso (audit/aging).

Presenza di `esito_rinnovo_motivo` = stato **perso**. Reversibile: settare i tre a null = riapre.
Set motivi (codici strutturati, **confermato founder 2026-06-20**): `prezzo`, `trasferito`,
`infortunio`, `insoddisfatto`, `altro` (con nota libera come catch-all).

> Niente hard delete, niente nuova tabella: un campo nullable basta (più semplice del pattern outcome-table,
> sufficiente per analytics di churn di base). Alembic migration + schema_sync per i DB esistenti.

---

## 3. Backend

### 3.1 Vista "clienti da recuperare" (Criterio A) — endpoint nuovo, CLIENT-AWARE
`GET /dashboard/clients-to-recover` (unità = **cliente**, 1 riga/cliente):
- Seleziona i **clienti** del trainer che hanno **≥1 contratto scaduto** (`chiuso=False`,
  `deleted_at=None`, `data_scadenza < today`) **E NON hanno alcun contratto attivo**
  (`chiuso=False AND data_scadenza >= today AND deleted_at=None`). Pattern SQL: `clienti con scaduti`
  **EXCEPT** `clienti con attivi`. Questo sussume rinnovo-figlio e nuovo-contratto-non-collegato.
- Per ogni cliente, **rappresentante** = contratto scaduto più recente (max `data_scadenza`).
- Filtro sul rappresentante: **non perso** (`esito_rinnovo_motivo IS NULL`). **NESSUN filtro
  opportunità** (v1.2): tutti i lapsed compaiono; `residuo`/`crediti_residui` = info + priorità.
- Response per riga: dati cliente + contratto rappresentante + `giorni_ritardo = today − data_scadenza`
  + `residuo` + `crediti_residui`. Ordinati per ritardo desc.
- NB: il vecchio "NOT EXISTS child rinnovo_di" **non serve più** — è sussunto da "zero contratti attivi".

### 3.2 Fix "in scadenza" — escludere i già-rinnovati
Aggiungere `NOT EXISTS (child rinnovo_di)` a `get_expiring_contracts` (`:346`) e all'alert
`expiring_contracts` (`:716`). Correzione del bug secondario.

### 3.3 Azione "Non rinnova" (Criterio B) — endpoint
`POST /contracts/{id}/renewal-outcome` (bouncer ownership 404-mai-403 + `log_audit`):
- body: `{ motivo: str, note?: str }` → set `esito_rinnovo_*`; `data = today`.
- reversibilità: `DELETE /contracts/{id}/renewal-outcome` (o `motivo=null`) → riapre.
- Validazione `motivo` contro il set consentito.

### 3.4 Alert dashboard "clienti da recuperare"
Nuova categoria alert `clients_to_recover` in `get_dashboard_alerts` (come `orphan_contracts`),
**conteggio per CLIENTI** ("N clienti da recuperare"), non per contratti — risolve la fallacia
sollevata dal founder (un cliente con 2 scaduti = 1, non 2). Link a `/rinnovi-incassi`.

---

## 4. Frontend

- **Tipo** `ClientToRecoverItem` (dati cliente + contratto rappresentante + `giorni_ritardo`, residuo/crediti).
- **Hook** `useClientsToRecover` (clone di `useExpiringContracts`) + `useMarkRenewalOutcome` /
  `useReopenRenewalOutcome` (invalidano `["clients-to-recover"]`, `["contracts"]`, `["dashboard"]`).
- **`/rinnovi-incassi`**: nuova sezione **"Clienti da recuperare"** (1 card/cliente), con aging
  (badge "Scaduto da Ngg"), CTA **"Rinnova"** (riusa `ContractSheet` renewal — pre-fill sequenziale
  `max(scadenza+1, oggi)` funziona già per gli scaduti) + **"Non rinnova"** (sul contratto rappresentante).
- **Dialog "Non rinnova"**: select motivo (5 codici) + note opzionale → `useMarkRenewalOutcome`. Azione
  MEDIA (AlertDialog standard), non distruttiva/reversibile.
- KPI strip: "Da recuperare" = **conteggio clienti** lapsed.

---

## 5. Test

`tests/test_clients_to_recover.py` (client-aware):
- Cliente con scaduto e **zero attivi** → compare (1 riga).
- Cliente con scaduto **+ contratto attivo non collegato** (nuovo manuale) → **NON compare** (il caso del founder).
- Cliente con scaduto + figlio rinnovo attivo → non compare (sussunto).
- Cliente con **2 scaduti** e zero attivi → **1 sola riga** (rappresentante = più recente), conta come 1.
- Rappresentante marcato "non rinnova" → escluso; reversibile → ricompare.
- Cliente che ha **completato e pagato tutto** (residuo 0) lapsed → **compare comunque** (no filtro opportunità, v1.2).
- `giorni_ritardo` corretto; multi-tenant.
- `renewal-outcome`: ownership 404, motivo invalido 422, audit.

---

## 6. Sequenza

1. **Modello + migrazione** (campi `esito_rinnovo_*` su Contract; Alembic + verifica schema_sync).
2. **Backend A** endpoint `clients-to-recover` (client-aware: scaduti EXCEPT attivi) + fix esclusione rinnovati su expiring.
3. **Backend B** endpoint `renewal-outcome` (set/reopen) + audit.
4. **Frontend** sezione "Clienti da recuperare" in `/rinnovi-incassi` + dialog "Non rinnova" + hook.
5. **Alert dashboard** `clients_to_recover` (conteggio clienti).
6. **Test** (`test_clients_to_recover.py`) + verifica e2e (skill `/verify`, zero scritture dove possibile).

Ogni step rilasciabile; `check-all.sh` + `pytest`; commit per step.

## 7. Decisioni founder (chiuse 2026-06-20)

- ✅ **Rilevazione client-aware**: cliente senza contratti attivi (`chiuso=False AND data_scadenza>=oggi`).
- ✅ **Unità = cliente** (1 riga/cliente, conta clienti); rappresentante = scaduto più recente.
- ✅ **Attivo** = aperto E non scaduto.
- ✅ **Set motivi**: prezzo, trasferito, infortunio, insoddisfatto, altro (+ nota).
- ✅ **Alert dashboard** sì, conteggio clienti.
- ✅ **Nessun filtro opportunità** (v1.2): surface di tutti i lapsed; residuo/crediti = info+priorità (anti-perdita silenziosa anche del cliente "completato").

## 8. Bridge rule

Output non banale (forma stato perso, query scaduti, aging, dialog) → learning capture + `BUILD_LOG`.
A fine: aggiornare `api/CLAUDE.md` (nuovi endpoint + Contract Integrity: stato esito_rinnovo).
