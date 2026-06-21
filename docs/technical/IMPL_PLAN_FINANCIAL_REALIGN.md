# PIANO DI IMPLEMENTAZIONE — Riallineamento al FINANCIAL_DOMAIN_MODEL

**Versione:** 1.0
**Data:** 2026-06-20
**Owner:** Giacomo Verardo (AVGV Technologies)
**Esecutore:** Claude Code
**Modello (SSoT):** `FINANCIAL_DOMAIN_MODEL.md` **v1.2** — tutte le definizioni stanno lì; qui solo il *come/dove/sequenza*.
**Supera/assorbe:** `IMPL_PLAN_RINNOVI_SCADUTI.md` (→ `docs/archive/` a fine implementazione).

> Piano UNICO del riallineamento del dominio finanziario al modello canonico. Anti-frammentazione:
> non si aprono nuovi IMPL_PLAN per i sotto-pezzi. Ogni blocco è rilasciabile; `check-all.sh` + `pytest`
> prima di ogni commit; commit per blocco.

---

## 0. Stato di partenza (cosa esiste e diverge dal modello)

- `clients-to-recover` (Step 2, `dashboard.py`): client-aware ma **include i SOSPESI** (manca lo stato
  SOSPESO) → da correggere. Rappresentante = più recente *aperto* → deve essere più recente *in assoluto*.
- `orphan_contracts`/`contracts-to-plan` ("da pianificare", SPEC_RINNOVO): filtra `chiuso=False` senza
  vigenza → **viola G1** (azione impossibile su scaduti).
- `kpi_attivi` (`contracts.py:list_contracts`): `sum(not chiuso)` → conta scaduti (**G4**).
- `expiring-contracts`: già esclude i rinnovati (fix fatto); resta da derivare da `contract_state`.
- Niente worklist SOSPESI; niente pagamento diretto residuo (**G6**); `esito_rinnovo_*` esiste (Step 1).
- UI `/rinnovi-incassi` "Clienti da recuperare" (Step 4-5) mostra anche sospesi → da correggere.

---

## 1. Blocco 0 — `contract_state()` SSoT (fondamento, prima di tutto)

**Nuovo modulo** `api/services/contract_state.py` — **funzione pura** (no DB), testabile:

- `contract_lifecycle(contract, crediti_usati, today) -> Lifecycle` con `Lifecycle ∈
  {ELIMINATO, CHIUSO, ATTIVO, SOSPESO, ESAURITO}` (derivazione §3 del modello).
- `crediti_residui(contract, crediti_usati)`, `residuo(contract)`.
- `money_substate(contract, rates) -> {saldato|da_pianificare|parziale|pianificato} (+ rate_scadute flag)` (§5).
- `client_engagement(lifecycles, ultimo_contatto, giorni_lapse, today) -> {ingaggiato|lapsed_caldo|lapsed_freddo}`
  (§4.1; `freddo` da `communication_log` + `SOGLIA_CHURN_GG`).
- Costanti `SOGLIA_IN_SCADENZA_GG=30`, `SOGLIA_CHURN_GG=90` definite **qui** (§4.2), importate da tutti.

**Caller**: i crediti_usati restano batch-fetch (anti-N+1) nei router; la funzione li riceve come arg.
**Test** `tests/test_contract_state.py`: i 4 quadranti + confini ("scade oggi" → ATTIVO; scaduto+crediti>0
→ SOSPESO; scaduto+crediti0 → ESAURITO; chiuso → CHIUSO) + money_substate + engagement (caldo/freddo).

> **Regola d'oro (modello §3):** dopo questo blocco, **nessun endpoint ricalcola "attivo/scaduto"** —
> tutti chiamano `contract_state`.

## 2. Blocco 1 — G1: "da pianificare" solo ATTIVO

- `orphan_contracts` (alert) e `contracts-to-plan` (endpoint): aggiungere vigenza
  (`data_scadenza IS NULL OR >= today`) → solo ATTIVO. Derivare via `contract_state`.
- Cruscotto `kpi_da_pianificare` (contracts.py) idem (solo ATTIVO).
- Test: contratto scaduto con residuo+zero rate → **NON** in "da pianificare" (va in "da incassare").

## 3. Blocco 2 — Riallineo worklist/KPI a `contract_state`

- **`clients-to-recover`**: `_lapsed_client_candidates` → ingaggiato = ATTIVO **o SOSPESO** (esclude
  sospesi); rappresentante = contratto **più recente in assoluto** (incl. CHIUSO). Test: il cliente con
  un SOSPESO non compare; rappresentante corretto (caso Dalila c29 vs c25).
- **`kpi_attivi`** (G4): = conteggio stato **ATTIVO**; aggiungere conteggi separati sospesi/esauriti.
- **`expiring-contracts`** + alert: derivare da `contract_state` (ATTIVO + scadenza ≤ SOGLIA_IN_SCADENZA).
- UI `/rinnovi-incassi`: la sezione "Clienti da recuperare" eredita la correzione (esclude sospesi).

## 4. Blocco 3 — Worklist "Contratti sospesi" + azioni (SPEC §4-bis)

- Endpoint `GET /dashboard/suspended-contracts`: stato SOSPESO (unità = contratto) — cliente, sedute
  residue, giorni_ritardo, residuo. Ordinati per urgenza (aging **invertito**: più vecchio = più urgente).
- Azioni: **estendi** (PUT data_scadenza futura → torna ATTIVO; riusa update_contract) ·
  **sedute decadute** (chiusura con motivo `sedute_decadute`, §G5; reversibile/audit).
- Alert dashboard `suspended_contracts` (conteggio). UI: sezione in `/rinnovi-incassi`.
- Test: SOSPESO compare; estendi→ATTIVO (esce); decadi→CHIUSO+motivo (esce); non compare in da-recuperare.
- **UX dual-debt (assi diversi, NON doppione):** un SOSPESO con *sia* sedute residue *sia*
  residuo denaro comparirà in **"contratti sospesi"** (debito = sedute, asse crediti) **e** in
  **"da incassare scaduto"** (debito = denaro, asse denaro). È corretto per modello (§2 assi
  ortogonali). Renderlo esplicito all'utente: due debiti distinti verso la stessa persona, non
  una duplicazione. Es. badge/nota "sedute da recuperare" vs "denaro da incassare", e — se nella
  stessa vista — riga unica cliente con i due importi separati e label inequivocabili.

## 5. Blocco 4 — G6: pagamento diretto del residuo

- Azione "**incassa residuo**" su contratto (qualsiasi stato aperto con residuo>0, tipicamente
  ESAURITO/SOSPESO scaduto dove non si può rateizzare): endpoint che crea `CashMovement` ENTRATA legato
  al contratto (categoria `PAGAMENTO_RATA` o nuova `INCASSO_RESIDUO`), `totale_versato += importo`,
  **trigger auto-close** (riusa la logica `pay_rate` §E-auto), bouncer + audit. **No rata richiesta.**
- Rende azionabile **"da incassare (scaduto)"** (lista ESAURITO/SOSPESO con residuo>0).
- Test di confine: incassare l'ultimo residuo di un ESAURITO → CHIUSO (no fantasma); riconciliazione mastro.

## 6. Blocco 5 — Win-back / freddo + decadimento asimmetrico (refinement)

- `clients-to-recover`: escludere i **lapsed-freddo** (derivati da `communication_log`: ultimo contatto >
  SOGLIA_CHURN o assente, e lapse > SOGLIA_CHURN). Assunzione-proxy dichiarata (§4.1).
- Ordinamento: lapsed caldi per urgenza; eventuale sezione "freddi" separata/collassata.
- (Sospesi: decadimento invertito già nel Blocco 3.)

## 7. Blocco 6 — Differiti (quando servono)

- **G3** analytics retention/renewal-rate via continuità cliente (`SOGLIA_CHURN_GG`).
- **G5** completo: motivi terminazione (`saldo_a_perdere` su incassa-residuo parziale a chiusura).
- Worklist "da incassare (scaduto)" come vista autonoma se non assorbita dai blocchi sopra.

---

## 8. Sequenza & invariante di copertura

`Blocco 0 → 1 → 2 → 3 → 4 → 5 → (6)`. Dopo ogni blocco, verificare l'**invariante di copertura §9.4**:
ogni stato non-terminale (ATTIVO/SOSPESO/ESAURITO + cliente lapsed) ha una worklist che lo accoglie —
nessuno stato "homeless". Verifica e2e (`/verify`) a fine Blocco 3 e Blocco 4 sul `crm.db` reale.

## 9. Bridge rule

Modifiche concettuali → prima `FINANCIAL_DOMAIN_MODEL.md`, poi qui, poi codice. Output non banale →
learning capture + `BUILD_LOG.md`. A fine: `api/CLAUDE.md` (nuovi endpoint + `contract_state`), archiviare
gli IMPL_PLAN.
