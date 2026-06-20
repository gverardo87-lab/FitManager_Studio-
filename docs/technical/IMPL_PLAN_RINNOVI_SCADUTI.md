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
Set motivi (codici strutturati) — **da confermare con founder**: `prezzo`, `trasferito`, `infortunio`,
`insoddisfatto`, `inattivo`, `altro`.

> Niente hard delete, niente nuova tabella: un campo nullable basta (più semplice del pattern outcome-table,
> sufficiente per analytics di churn di base). Alembic migration + schema_sync per i DB esistenti.

---

## 3. Backend

### 3.1 Vista "scaduti da rinnovare" (Criterio A) — endpoint nuovo
`GET /dashboard/expired-contracts` (modellato su `get_expiring_contracts`, stesso shape item + `giorni_ritardo`):
- `chiuso == False`, `deleted_at == None`, `trainer_id`;
- `data_scadenza < today`;
- **non rinnovato**: `NOT EXISTS (child con rinnovo_di = c.id AND deleted_at IS NULL)`;
- **non perso**: `esito_rinnovo_motivo IS NULL`;
- **opportunità residua**: `crediti_residui > 0` **OR** `prezzo_totale > totale_versato`;
- `giorni_ritardo = today − data_scadenza`; ordinati per ritardo desc; aging client-side o nel response.

### 3.2 Fix "in scadenza" — escludere i già-rinnovati
Aggiungere `NOT EXISTS (child rinnovo_di)` a `get_expiring_contracts` (`:346`) e all'alert
`expiring_contracts` (`:716`). Correzione del bug secondario.

### 3.3 Azione "Non rinnova" (Criterio B) — endpoint
`POST /contracts/{id}/renewal-outcome` (bouncer ownership 404-mai-403 + `log_audit`):
- body: `{ motivo: str, note?: str }` → set `esito_rinnovo_*`; `data = today`.
- reversibilità: `DELETE /contracts/{id}/renewal-outcome` (o `motivo=null`) → riapre.
- Validazione `motivo` contro il set consentito.

### 3.4 (Opzionale) Alert dashboard "scaduti da rinnovare"
Nuova categoria alert `expired_contracts` in `get_dashboard_alerts` (come `orphan_contracts`) — **da
decidere** se aggiungerla ora o solo la sezione in `/rinnovi-incassi`.

---

## 4. Frontend

- **Tipo** `ExpiredContractItem` (come `ExpiringContractItem` + `giorni_ritardo`, `residuo`) e
  `esito_rinnovo_*` su `Contract`/`ContractListItem` se serve in lista.
- **Hook** `useExpiredContracts` (clone di `useExpiringContracts`) + `useMarkRenewalOutcome` /
  `useReopenRenewalOutcome` (mutation, invalidano `["expired-contracts"]`, `["contracts"]`, `["dashboard"]`).
- **`/rinnovi-incassi`**: nuova sezione **"Scaduti da rinnovare"** (sopra/sotto "Contratti da rinnovare"),
  con aging (badge "Scaduto da Ngg"), CTA **"Rinnova"** (riusa `ContractSheet` renewal — il pre-fill
  sequenziale `max(scadenza+1, oggi)` funziona già anche per scaduti) + **"Non rinnova"**.
- **Dialog "Non rinnova"**: select motivo + note opzionale → `useMarkRenewalOutcome`. Azione MEDIA
  (AlertDialog standard), non distruttiva.
- KPI strip: aggiungere "Da recuperare" (scaduti) accanto a "Da rinnovare".

---

## 5. Test

`tests/test_expired_contracts.py`:
- Scaduto aperto con crediti residui / residuo > 0 → compare; saldato+crediti usati (chiuso) → no.
- Già-rinnovato (esiste figlio) → escluso da scaduti **e** da expiring.
- Marcato "non rinnova" → escluso; reversibile → ricompare.
- `giorni_ritardo` corretto; multi-tenant; opportunità nulla (residuo=0 e crediti usati) → escluso.
- `renewal-outcome`: ownership 404, motivo invalido 422, audit.

---

## 6. Sequenza

1. **Modello + migrazione** (campi `esito_rinnovo_*` su Contract; Alembic + verifica schema_sync).
2. **Backend A** endpoint `expired-contracts` + fix esclusione rinnovati su expiring.
3. **Backend B** endpoint `renewal-outcome` (set/reopen) + audit.
4. **Frontend** sezione scaduti in `/rinnovi-incassi` + dialog "Non rinnova" + hook.
5. **Test** + verifica e2e (skill `/verify`, zero scritture sul DB reale dove possibile).
6. (Opz.) Alert dashboard scaduti.

Ogni step rilasciabile; `check-all.sh` + `pytest`; commit per step.

## 7. Punti aperti (decisioni founder)

- **Set motivi** "non rinnova" (§2).
- **Alert dashboard** per scaduti: sì ora o solo sezione `/rinnovi-incassi`? (§3.4)
- Conferma definizione "opportunità residua" = crediti residui **OR** residuo economico (spec §A.2).

## 8. Bridge rule

Output non banale (forma stato perso, query scaduti, aging, dialog) → learning capture + `BUILD_LOG`.
A fine: aggiornare `api/CLAUDE.md` (nuovi endpoint + Contract Integrity: stato esito_rinnovo).
