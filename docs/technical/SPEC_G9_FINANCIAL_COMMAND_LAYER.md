# SPEC_G9_FINANCIAL_COMMAND_LAYER

**Tipo:** specifica prescrittiva (cosa-deve-essere-vero; silente sul come dove possibile). Bridge Chat→Code.
**Data:** 2026-06-30 · **Branch:** `FitManager_Studio`
**Stato:** ⏳ **DA IMPLEMENTARE** (G9.0→G9.6). Governance docs-only. Zero codice prodotto.
**Blocco proposto:** **G9** — elevazione del write-model del dominio contrattuale-economico. Ratifica
`ADR-022`. Sette gate sequenziali, branch sempre rilasciabile.
**Mappa di verità:** `docs/adr/ADR-022-financial-command-layer-ledger-load-bearing.md` ·
`docs/technical/FINANCIAL_DOMAIN_MODEL.md` · `docs/technical/TASSONOMIA_FINANZIARIA.md` ·
`api/services/contract_state.py` · `api/services/contract_settlement.py` · `api/services/cash_categories.py` ·
`api/routers/contracts.py` · `api/routers/rates.py` · `tests/test_financial_invariants_harness.py`

> **Nota sulle coordinate.** I riferimenti `file:riga` sono lo snapshot 2026-06-30 (post-G8.3); gli **esiti
> sono durevoli, le righe vanno riverificate** a implementazione (come da prassi `AUDIT_PRE_G7.3`). Ogni gate
> è behavior-preserving fino a **G9.4** (primo gate che cambia comportamento osservabile, e solo dietro
> feature-flag).

---

## Impact map

- **Obiettivo:** rendere il **ledger `CashMovement` load-bearing** (fonte di verità della cassa) e dotare il
  SSoT di lettura (`contract_state.py`) del suo **gemello di scrittura** — penna unica di posting +
  transition executor + invarianti imposti — così che gli scenari secondari si **assorbano per costruzione**
  invece di richiedere una toppa + un ADR ciascuno.
- **Layer toccati:** backend (nuovo package `api/services/financial/`: `ledger.py`, `transitions.py`,
  `invariant_gate.py`; `contract_state.py`/`contract_settlement.py` **collaboratori intatti**; router
  `contracts.py`/`rates.py` **assottigliati**; `dashboard.py` reconciliation bidirezionale; `check-all.sh`
  grep→test semantici; `api/types/money.py` a G9.6). Frontend: **invariato** (HTTP identico fino a G9.4; a
  G9.4 solo nuovi 409 dietro flag).
- **Invarianti da preservare (asse DENARO e dominio):** `residuo()` net-aware, Strada B, `residuo == 0 ⟺
  saldato`, cassa-immutabile/integrità di periodo (ADR-019), asse EROGATO (ADR-016), `Rinviato` fuori
  occupazione (ADR-017), bilateralità (ADR-018), INV-RATE (ADR-021), wallet/receivable fuori da `residuo()`
  (ADR-020). **G9 non cambia cosa il sistema calcola — cambia chi e come lo scrive.**

**Tesi falsificabile (fine G9):** (1) **nessun endpoint scrive `contract.totale_versato +=` o
`totale_rimborsato +=` a mano** — l'unico scrittore è la penna (`post_inflow`/`post_outflow`); (2)
`project_columns_from_ledger(id)` riproduce `totale_versato`/`totale_rimborsato` **al centesimo** da
`Σ` postings su **ogni** contratto reale; (3) `assert_contract_invariants` gira a runtime su **tutte** le
transizioni denaro (non solo reopen); (4) i **4 grep-guard** di `check-all.sh` sono stati sostituiti da
test semantici sul simbolo; (5) un `Hypothesis RuleBasedStateMachine` esplora migliaia di sequenze
stato×transizione senza violare un invariante; (6) la `/reconciliation` su un DB sano riporta **0
divergenti** by-construction (non più audit load-bearing).

---

## 0. Problema reale da correggere (sintesi audit)

1. **Ledger consultivo, non load-bearing.** Le colonne `totale_versato`/`totale_rimborsato`/`quota_stornata`
   sono una seconda verità sincronizzata a mano in ~7 siti (`contracts.py:1663/1724/1751/2038`, `rates.py`
   pay/unpay, `incassa-residuo`). `quota_stornata` (`:1751`) **entra nel `residuo()` ma non ha posting**; il
   fold R2-bis del reopen (`:2038`) è una rettifica **senza movimento**.
2. **Coreografia nei router.** terminate ~256 righe (`:1573-1828`), reopen ~182 (`:1916-2098`); auto-close
   duplicato (`rates.py` inline vs `agenda.py:301`).
3. **Invarianti osservati, non imposti.** `assert_contract_invariants` cablato solo su reopen (`:2094`,
   log-only); 4 grep-guard testuali (`check-all.sh:40-84`); `/reconciliation` post-facto e monca
   (`dashboard.py:193-201`, solo lato versato).
4. **Denaro in float.** ~150 dead-zone/`round`, contraddizione `is_saldato` (≤0.01) vs `money_substate`
   (≤0.009).

## 1. Ciò che NON cambia

- I **moduli puri** `contract_state.py` e `contract_settlement.py` restano il cuore e **non cambiano firma**
  (diventano i collaboratori del layer). `residuo()` net-aware, `compute_settlement`, gli enum.
- Tutte le **decisioni di dominio** ADR-016→021 (asse EROGATO, rinvio-libera-credito, bilateralità,
  cassa-immutabile, residuo net-aware, wallet/receivable fuori da residuo, INV-RATE).
- Le **ancore** `totale_versato == Σ ENTRATA` / `totale_rimborsato == Σ USCITA RIMBORSO + Σ wallet
  riassorbito` (I5): reggono **meglio** (diventano vere per costruzione).
- Il **frontend** (HTTP identico fino a G9.4; a G9.4 solo nuovi 409 dietro flag, su violazioni che oggi sono
  già bug).

## 2. Il principio (ADR-022)

Il SSoT di **lettura** (`contract_state.py`) ha bisogno del suo gemello di **scrittura**, in due metà:
**(A) penna unica** — l'unico punto che muta le colonne cassa; **(B) transition executor** — l'unico punto
che applica una transizione e ne asserisce gli invarianti. Con questi, il **ledger è load-bearing**: le
colonne sono proiezioni verificate, non verità parallele. *Strumenta-poi-imponi; evolvi, non riscrivere.*

---

## G9.0 — Sensore invarianti ovunque (log-only) + riconciliazione bidirezionale

**Mossa a leva più alta / rischio più basso. Zero cambio di comportamento.** Il checker è già scritto e
corretto su I1-I6; gli manca solo di girare su più di 1 transizione.

- **G9.0-a — sensore ovunque.** Estrarre l'helper oggi locale a `contracts.py` (`_log_invariant_violations`,
  cablato a runtime solo su reopen `:2094`) in `api/services/financial/invariant_gate.py` e invocarlo,
  **ancora log-only**, in coda a **tutte** le transizioni denaro: `terminate`, `pay_rate`, `unpay_rate`,
  `incassa-residuo`, `eroga` wallet, `incassa`/`annulla` `credito_terminazione`. Emette un log strutturato
  per violazione (codice I*, transizione, `contract_id`) → **telemetria** che de-risca G9.4.
- **G9.0-b — reconciliation bidirezionale.** Completare `/reconciliation` (`dashboard.py:193-201`) col lato
  mancante `totale_rimborsato == Σ USCITA RIMBORSO[id_contratto]` (oggi controlla solo il versato).
- **G9.0-c — quick-win gratuiti (stesso gate, costo ~0):** (1) collassare le **due formule `residuo`
  duplicate** dei DTO (`financial.py:274-275` `CreditoTerminazioneResponse`, `:296-297`
  `CreditoClienteResponse`) in un helper puro condiviso; (2) correggere il **KPI gross-SQL** di
  `dashboard.py` (confronto `prezzo > versato` LORDO) a net-aware riusando `cstate`.

**AC-G90-1:** `assert_contract_invariants` viene invocato a runtime al termine di **ognuna** delle ~7
transizioni denaro; un test verifica la presenza della chiamata (o, meglio, che una violazione I1 iniettata
produca il log atteso) per ciascuna. **AC-G90-2:** `/reconciliation` segnala una divergenza
`totale_rimborsato` iniettata (oggi invisibile). **AC-G90-3:** le due formule `residuo` dei DTO derivano da
un unico helper (test: stesso input → stesso output, e modificare l'helper cambia entrambi). **AC-G90-4:**
comportamento HTTP **invariato** (nessun 409 nuovo); suite verde; ruff + next build verdi.

**Rischio:** basso. **Sforzo:** basso. **Behavior-preserving:** sì.

---

## G9.1 — Penna unica di posting (ledger load-bearing)

`api/services/financial/ledger.py`:

```text
post_inflow(session, *, contract, importo, categoria, metodo, data_effettiva, id_rata=None, note) -> CashMovement
post_outflow(session, *, contract, importo, categoria, metodo, data_effettiva, note) -> CashMovement
```

Ogni funzione, in **una** unità: (1) crea il `CashMovement` (tipo ENTRATA/USCITA, `trainer_id`,
`id_contratto`, ecc.); (2) applica il **delta-colonna** mappato via `cash_categories.signed_contractual_amount`
(`:53-62`) — `totale_versato += importo` per gli inflow contrattuali, `totale_rimborsato += importo` per
`RIMBORSO_CONTRATTO`; (3) richiama `cstate.recompute_stato_pagamento(contract)`. **Nessun endpoint scrive più
la colonna a mano.**

Adozione **endpoint-per-endpoint** (strangler-fig, branch sempre rilasciabile): **`pay_rate`** per primo (il
più semplice), poi **`incassa-residuo`**, poi i rami di **`terminate`** (rimborso USCITA, incasso conguaglio
ENTRATA) e l'erogazione **wallet** (`clients.py` eroga; nota: `id_contratto=None` per non toccare l'àncora di
contratto — la penna rispetta il parametro). A ogni passo i 718 test e i grep-guard restano verdi.

**AC-G91-1:** dopo la migrazione di un endpoint, `grep` di `totale_versato +=`/`totale_rimborsato +=` in quel
file → **0** occorrenze fuori da `ledger.py`. **AC-G91-2:** per ogni endpoint migrato, un test verifica che
`post_inflow/out` abbia creato il movimento **e** aggiornato la colonna **e** ricalcolato `stato_pagamento`
in un solo commit atomico (tutto-o-niente). **AC-G91-3:** `I5` (`totale_versato == Σ ENTRATA`) verificato
vero **per costruzione** sui path migrati (la telemetria G9.0 non logga più violazioni I5 su quei path).
**AC-G91-4:** HTTP invariato; i ~15 consumer di lettura **non toccati**.

**Rischio:** basso. **Sforzo:** medio. **Behavior-preserving:** sì.

---

## G9.2 — Dare casa nel ledger alle grandezze non-cash + `project_columns_from_ledger`

- **G9.2-a — `project_columns_from_ledger(session, contract_id) -> {versato, rimborsato}`** (inverso esatto
  della query di `/reconciliation`), usata come **asserzione pre-commit** nell'executor (G9.3): le colonne
  ri-derivate dal ledger devono uguagliare le colonne scritte.
- **G9.2-b — storno come posting di contra-ricavo non-cash.** `quota_stornata` (`contracts.py:1751`) — oggi
  unico euro nel `residuo()` senza posting — diventa `Σ` di postings di **storno** espliciti (categoria
  dedicata, non-cash, tracciata in `TASSONOMIA_FINANZIARIA.md`). Partire dal **solo storno** (basso
  blast-radius). Il **fold R2-bis del reopen** (`:2038`) diventa un **posting di rettifica esplicito**.
  Esito: `residuo = prezzo − Σ(postings firmati)` — una **somma verificabile**.
- **G9.2-c — specchio di wallet/receivable.** `crediti_cliente` e `crediti_terminazione` restano tabelle
  (UI/worklist immutate), ma le loro variazioni rilevanti per la posizione si **specchiano** come postings
  così il residuo le veda dal ledger (senza ramo speciale).

**AC-G92-1:** `project_columns_from_ledger` riproduce `totale_versato`/`totale_rimborsato` al centesimo su
ogni contratto del DB di test (e, in validazione, sul clone backup reale). **AC-G92-2:** `quota_stornata ==
Σ postings di storno` per ogni contratto; `residuo()` resta byte-identico al pre-G9.2 (lo storno-posting
**non cambia** il valore, **cambia** la sua derivazione). **AC-G92-3:** il fold R2-bis del reopen produce un
posting esplicito; la telemetria I5 resta pulita; `residuo` post-reopen invariato. **AC-G92-4:** harness
invariante×transizione verde (incl. sequenze composte terminate→incassa→reopen).

**Rischio:** medio. **Sforzo:** alto. **Behavior-preserving:** sì (valori invariati; cambia la derivazione).

---

## G9.3 — TransitionExecutor + FSM di chiusura esplicita

`api/services/financial/transitions.py`: command-handler tipati per transizione su un comando DTO + la penna
di G9.1. Spostare i corpi di **terminate** (`contracts.py:1573-1828`) e **reopen** (`:1916-2098`) in
`execute_terminate(ctx)` / `execute_reopen(ctx)` (strangler-fig, **una transizione alla volta**,
rilocazione quasi-verbatim → HTTP identico, suite verde al primo passaggio). `compute_settlement` e
`contract_state` restano collaboratori puri dove sono.

Pattern dell'executor (post-condizione obbligatoria):
```text
carica stato → decisione pura (compute_settlement / contract_state) → emette postings (penna G9.1)
→ project_columns_from_ledger == colonne scritte (G9.2-a) → assert_contract_invariants (gate, G9.4)
→ audit + lifecycle transition → commit atomico
```
Router → **~30 righe** (bouncer + parse comando + delega + serialize). **FSM esplicita** di
`chiuso`/`motivo_chiusura` (tabella stati×transizioni). **Unificare l'auto-close duplicato**: il path
payment-driven (`rates.py` inline) e credit-driven (`agenda.py:301` `_sync_contract_chiuso`, già con la
reopen-allowlist G7.2) convergono su un'unica transizione.

**AC-G93-1:** terminate/reopen vivono in `transitions.py`; i router `contracts.py` relativi sono ≤ ~40 righe
ciascuno. **AC-G93-2:** la suite 718 (+ nuovi) resta verde al primo passaggio (behavior-preserving);
risposta HTTP byte-identica su una matrice di scenari registrati. **AC-G93-3:** l'auto-close è **un solo**
percorso logico (test: payment-driven e credit-driven producono lo stesso stato terminale a parità di
condizioni). **AC-G93-4:** la post-condizione `project_columns == colonne` è asserita in ogni handler.

**Rischio:** medio. **Sforzo:** medio. **Behavior-preserving:** sì.

---

## G9.4 — Promuovere invarianti a gate (409 + rollback) + ritiro grep-guard + test semantici

- **G9.4-a — enforcement graduale.** Con la **telemetria di G9.0** e la cucitura di G9.3: promuovere
  **I1/I4** a **409 + rollback** dentro la post-condizione dell'executor (I5/I6 in **warn** finché la
  riconciliazione è provata pulita in prod), via feature-flag **`INVARIANT_ENFORCEMENT`** (`raise` in
  CI/dev/test, `log` in prod inizialmente, poi `raise` quando la telemetria è verde).
- **G9.4-b — ritiro grep-guard.** Convertire i **4 grep-guard testuali** (`check-all.sh:40-84`,
  ADR-016/017/018/019) in **test semantici sul simbolo reale**: es. `assert
  CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO in CONTRACT_CASH_IN`; un `import-linter` che vieta a
  `contract_settlement` di importare i predicati di occupazione (presidio ADR-016). I grep si rimuovono
  **solo dopo** che i test semantici sono verdi (no buco).

**AC-G94-1:** con `INVARIANT_ENFORCEMENT=raise`, una transizione che violerebbe I1/I4 ritorna **409 +
rollback** (zero scrittura) — test per ciascun invariante. **AC-G94-2:** con flag a `log`, comportamento
identico a oggi (rollback sicuro della decisione). **AC-G94-3:** i 4 grep-guard rimossi da `check-all.sh`
hanno un test semantico gemello che fallisce sullo stesso scenario (es. togliere
`INCASSO_CONGUAGLIO_CONTRATTO` da `CONTRACT_CASH_IN` rompe un test, non un grep). **AC-G94-4:** la
telemetria G9.0 mostra **0** violazioni I1/I4 in CI prima di accendere il `raise`.

**Rischio:** medio (mitigato dal flag e dalla telemetria). **Sforzo:** medio. **Behavior-preserving:** no
(introduce 409 dietro flag — su stati che oggi sono già bug silenziosi).

---

## G9.5 — Hypothesis stateful machine (property-based testing)

`RuleBasedStateMachine` (dipendenza **solo-test**, seed pinnato per determinismo CI) che riusa i builder
dell'harness (`tests/test_financial_invariants_harness.py`) come `rule()` (pay, unpay, terminate, incassa,
eroga, reopen, …) e `assert_contract_invariants` come **invariante post-mossa**. Da ~12 path manuali a
**migliaia di sequenze generate**. `@example` per i canary noti (es. `eroga_wallet → reopen` = Bug-1).

**AC-G95-1:** la macchina esplora sequenze casuali di transizioni mantenendo I1-I6 ad ogni passo; un bug
iniettato (regressione di un invariante) la fa fallire. **AC-G95-2:** seed pinnato → run deterministico in
CI. **AC-G95-3:** zero impatto runtime (test-only). **AC-G95-4:** i canary noti sono `@example` espliciti.

**Rischio:** basso. **Sforzo:** medio. **Behavior-preserving:** sì (test-only).

---

## G9.6 — (Differito, gated) Money value-type — centesimi interi

`api/types/money.py` (Decimal o interi-centesimi; **un solo** rounding mode dichiarato; non-negativo dove
dovuto), rifattorizzato **dietro** `contract_state.py` + `contract_settlement.py` lasciando le firme
`float→float` **invariate** (i ~15 consumer non cambiano una riga). Collassa le ~150 dead-zone sparse
(`±0.009`/`±0.01`) in **una costante unica** e risolve la contraddizione `is_saldato` (≤0.01) vs
`money_substate` (≤0.009). **Fase storage (ultimo miglio, separata):** colonne monetarie + `CashMovement.importo`
→ INTEGER centesimi via `schema_sync` (Alembic FROZEN sui DB deployati — vedi precedente
`schema_sync._fix_cross_db_fk`).

**Procedura sicura:** introdurre ai confini dei 2 moduli puri **side-by-side** coi float; girare un
**golden test Money-vs-float** che prova la **byte-identità** sui 12 scenari dell'harness; **solo dopo** la
verde, stringere deliberatamente `0.009 → 0.005` (mezzo centesimo, il confine corretto per EUR), preceduto da
uno **scan dei contratti reali** nella banda riclassificata.

**AC-G96-1:** golden test Money-vs-float byte-identico sui 12 scenari prima di qualunque cambio di
comportamento. **AC-G96-2:** un'unica costante epsilon (o nessuna, con interi); `is_saldato` e
`money_substate` usano lo **stesso** confine. **AC-G96-3:** la fase-storage (se eseguita) migra via
`schema_sync`, idempotente, verificata su clone backup reale; `Σ ENTRATA == totale_versato` diventa un `==`
**stretto**. **AC-G96-4:** la `/reconciliation` perde la sua ragion d'essere (divergenze impossibili per
costruzione) → declassata a rete di sicurezza periodica.

**Rischio:** basso (dietro firme invariate + oracolo). **Sforzo:** alto. **Behavior-preserving:** sì fino
allo stringimento deliberato dell'epsilon (gated, post-scan).

---

## Sequenza dei gate (vincolante)

| Gate | Goal | Dipende da | Rischio/Sforzo | Behavior |
|------|------|-----------|----------------|----------|
| **G9.0** | Sensore invarianti ovunque (log-only) + reconciliation bidirezionale + 2 quick-win | — | basso / basso | invariato |
| **G9.1** | Penna unica `post_inflow`/`post_outflow` (adozione endpoint-per-endpoint) | G9.0 (baseline telemetria) | basso / medio | invariato |
| **G9.2** | Storno/fold come postings + `project_columns_from_ledger` | G9.1 | medio / alto | invariato (valori) |
| **G9.3** | TransitionExecutor + FSM chiusura + unifica auto-close | G9.1, G9.2 | medio / medio | invariato |
| **G9.4** | Invarianti → 409+rollback (flag) + ritiro grep-guard → test semantici | G9.0, G9.3 | medio / medio | **nuovi 409 (flag)** |
| **G9.5** | Hypothesis RuleBasedStateMachine | G9.3 | basso / medio | invariato (test-only) |
| **G9.6** | *(differito)* Money value-type + fase-storage | G9.3 (gated, non blocca) | basso / alto | invariato fino a epsilon-tighten |

**Regola d'oro della sequenza:** non si costruisce l'executor (G9.3) prima della penna (G9.1); non si accende
l'enforcement (G9.4) prima della telemetria (G9.0); non si parte da Money (G9.6 ultimo). Ogni gate lascia il
branch **rilasciabile** e la suite **verde**; G9.0-G9.3 e G9.5-G9.6(calcolo) sono behavior-preserving, G9.4 è
l'unico che cambia comportamento e solo dietro flag.

## Follow-up a implementazione

A chiusura dei gate, aggiornare: `FINANCIAL_DOMAIN_MODEL.md` (ledger load-bearing; `residuo` come somma di
postings; storno-posting), `TASSONOMIA_FINANZIARIA.md` (categoria storno contra-ricavo non-cash; predicati
penna), `api/CLAUDE.md` (Contract Integrity Engine → financial command layer; penna unica come punto-di-
scrittura; invariant gate), `BUILD_LOG.md` (cronologia G9.x), e l'indice `docs/INDEX.md` / `docs/adr/README.md`.
Depositare l'audit fondante `docs/operations/AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md`.
