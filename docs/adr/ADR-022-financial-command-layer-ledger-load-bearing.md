# ADR-022 — Financial command layer: il ledger diventa load-bearing (penna unica + transition executor + invarianti imposti)

- Date: 2026-06-30
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); review senior multi-agente code-grounded di Claude Code (8 reader + 5 lenti indipendenti + sintesi)
- Related upgrade ID: programma di elevazione architetturale del dominio contrattuale-economico (blocco **G9**, sequenza G9.0→G9.6)
- Trigger: osservazione del founder dopo G8.3 — «continuano a uscire scenari secondari che gestiamo singolarmente; le SSoT non sono come dovrebbero, mancano strati che unifichino le variabili»
- Audit fondante: review architetturale `docs/operations/AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md` (questa stessa analisi, da depositare a corredo)
- Consolida (NON supersede): il **meta-pattern** che `ADR-016`→`ADR-021` istanziano scenario per scenario — una grandezza carica deve restare funzione pura di pochi fatti-sorgente, e ogni transizione deve preservarla. Quegli ADR restano decisioni valide; ADR-022 fornisce loro lo **strato di scrittura** che presupponevano e che non esisteva.
- Correlati: `ADR-014` (gestione finanziaria), `ADR-019` (cassa-immutabile, residuo net-aware), `ADR-021` (INV-RATE), `FINANCIAL_DOMAIN_MODEL.md`, `TASSONOMIA_FINANZIARIA.md`; spec di dettaglio `SPEC_G9_FINANCIAL_COMMAND_LAYER.md`

## Context

Il dominio contrattuale-economico è stato costruito in ~25 sotto-blocchi (G6, G7.0→G7.10, G8.1→G8.3)
governati da **8 ADR (014-021)** e ~10 spec. Il read-model è eccellente e **già centralizzato**:
`api/services/contract_state.py` è un SSoT **puro** (zero DB) — `residuo()` net-aware (`:73-87`),
`netto_incassato()` (`:90-95`), `recompute_stato_pagamento()` (`:260-270`),
`assert_contract_invariants()` con I1/I4/I5/I6 (`:329-426`) — affiancato da `contract_settlement.py`
(conguaglio puro) e da un harness invariante×transizione (`tests/test_financial_invariants_harness.py`).

Il problema **non è il read-model**. È che **manca il suo gemello di scrittura**, e di conseguenza:

1. **Il ledger non è load-bearing, è consultivo.** `CashMovement` (`movimenti_cassa`) è dichiarato «mastro
   sacro/immutabile», ma le colonne denormalizzate del contratto (`totale_versato`, `totale_rimborsato`,
   `quota_stornata`) sono una **seconda verità** tenuta in sync **a mano** in ~7 siti di scrittura sparsi
   (`contracts.py:1663/1724/1751/2038`, `rates.py` pay/unpay, `incassa-residuo` ~`:1407`): ognuno un
   `contract.totale_versato += …` accanto a un `CashMovement` creato a parte. La prova provata:
   **`quota_stornata` (`contracts.py:1751`) è l'unico euro che entra nella formula del `residuo()` ma non
   ha alcun posting nel ledger** (è un memorandum puro), e il **fold R2-bis del reopen** (`contracts.py:2038`)
   è una ri-attribuzione contabile **senza movimento**, esistente solo per far tornare la formula.
2. **La coreografia delle transizioni vive nei router.** `terminate_contract` (~256 righe inline,
   `contracts.py:1573-1828`) e `reopen_contract` (~182 righe, `:1916-2098`) sono sequenze transazionali a
   mano che devono *ricordarsi* N passi ripetuti (muta colonne → crea movimento → soft-delete rate →
   `_reconcile_rate_plan` → `recompute_stato_pagamento` → `log_audit` → `log_contract_lifecycle_transition`
   → `_sync_contract_chiuso` → `_log_invariant_violations`). L'auto-close è **duplicato** (path
   payment-driven inline in `rates.py` vs credit-driven in `agenda.py:301`).
3. **Gli invarianti sono osservati, non imposti.** `assert_contract_invariants` è completo e corretto su
   I1-I6, ma è cablato a runtime **su 1 sola transizione su ~7** (reopen, `contracts.py:2094`) e in
   **log-only**. Le altre difese sono **testuali**: 4 grep-guard fragili in `tools/scripts/check-all.sh:40-84`
   (ADR-016/017/018/019) che impongono via stringa ciò che l'architettura dovrebbe garantire. La
   `/reconciliation` (`dashboard.py:193-201`) è la diagnosi stessa: un audit **post-facto** che ammette che
   la verità è il ledger ma la scopre dopo, ed è pure **monca** (controlla solo `versato == Σ ENTRATA`, mai
   il lato `rimborsato`).
4. **Il denaro è float.** Dead-zone sparse (`±0.009`, `≤0.01`) e `round(·, 2)` ovunque (~150 punti), con
   contraddizioni latenti (`is_saldato` ≤0.01 vs `money_substate` ≤0.009).

**Meta-finding.** Tutti gli 8 ADR sono istanze della **stessa legge riscoperta**: finché ogni endpoint può
scrivere la colonna da solo, ogni nuovo scenario è un'occasione per dimenticarne uno → nasce un ADR che
mette a verbale la regola che il codice non sa imporre. **Il treadmill non è incompetenza: è l'assenza
dello strato di scrittura gemello del SSoT di lettura.** Le «regole di disciplina manuale» nei commenti
(«MAI modificare `crediti_usati` senza chiamare `_sync_contract_chiuso()`», «MAI riusare `!= 'Cancellato'`
sui siti credito») sono il sintomo: disciplina al posto di garanzia strutturale.

## Decision Drivers

- **Un solo SSoT del denaro, anche in scrittura.** Se `residuo()`/`netto` sono la verità in lettura, le
  loro variabili-sorgente non possono essere scritte da N punti scoordinati.
- **Assorbire gli scenari, non inseguirli.** «Aggiungere uno scenario» deve diventare «aggiungere una
  posting-rule + una transizione», non «editare un router da 250 righe + scrivere un ADR + aggiungere un
  grep-guard».
- **Strumenta-poi-imponi.** Un senior non promuove un invariante a 409 al buio sui dati reali di
  Chiara/Alessio (che potrebbero già divergere per ragioni legacy): prima misura, poi impone.
- **Evolvere, non riscrivere.** L'investimento esistente (`contract_state.py`/`contract_settlement.py` puri
  e corretti; harness; 718 test verdi) è la **rete di sicurezza dell'evoluzione**, non zavorra.
- **Profilo di rischio da founder solo.** Branch sempre rilasciabile, adozione endpoint-per-endpoint, ogni
  gate behavior-preserving fino al gate di enforcement esplicito.
- **Convergenza con lo stato dell'arte** (Stripe/Chargebee/QuickBooks): ledger immutabile load-bearing,
  posizione ricalcolata, postings bilanciati, denaro in interi.

## Considered Options

### Option A — Status quo (continuare scenario per scenario)
- Pro: zero costo immediato; ogni toppa è piccola.
- Contro: il treadmill continua — gli 8 ADR diventano 15; ogni nuovo canale di incasso/transizione riapre
  la stessa classe di buchi (lo dimostra ADR-021, che ha dovuto generalizzare a posteriori una
  riconciliazione nata reopen-only); la manutenibilità resta **lineare col numero di scenari**.

### Option B — Rewrite verso event-sourcing / CQRS completo
- Pro: il gold standard teorico (eventi come unica verità, proiezioni derivate).
- Contro: **big-bang**; butta l'investimento (i moduli puri, l'harness, 718 test); alto rischio per un
  founder solo con clienti reali in produzione; payoff lontano. Sproporzionato.

### Option C — Financial command layer evolutivo (scelta)
- Uno **strato di scrittura sottile** in due metà, costruito **sopra** i moduli puri esistenti (che restano
  il cuore, diventano i collaboratori del layer): (a) una **penna unica** di posting; (b) un **transition
  executor** (command-handler per transizione). Più la promozione degli invarianti da osservati a imposti,
  e — differito — un value-type `Money`.
- Pro: il più semplice a parità di guadagno strutturale; **strangler-fig** (una transizione/endpoint alla
  volta, suite sempre verde); rende I5 vero **per costruzione** invece che verificato dopo; converge coi
  best CRM; adottabile a branch sempre rilasciabile.
- Contro: tocca codice load-bearing (i ~7 siti di scrittura, i corpi di terminate/reopen) — mitigato dalla
  rilocazione behavior-preserving e dalla telemetria log-only che precede ogni enforcement.

## Decision

**Option C.** Si introduce un **financial command layer** che rende il ledger load-bearing, governato da
sette decisioni founder vincolanti (2026-06-30):

1. **D-LEDGER-LOAD-BEARING** — il `CashMovement` è la **fonte di verità della cassa**. `totale_versato` e
   `totale_rimborsato` diventano **proiezioni verificate** del ledger (cache derivabile), non verità
   parallele tenute in sync a mano. Esiste una funzione inversa `project_columns_from_ledger(contract_id)`
   (inverso esatto della query già scritta in `/reconciliation`, `dashboard.py:193-201`, estesa al lato
   rimborso) usata come **asserzione pre-commit**.
2. **D-PENNA-UNICA** — un **unico punto di scrittura** della cassa: `post_inflow(...)` / `post_outflow(...)`
   in `api/services/financial/ledger.py`. In **una** funzione: crea il `CashMovement` **e** applica il
   delta-colonna (mappato via `cash_categories.signed_contractual_amount`, `:53-62`, già una posting-rule
   embrionale) **e** richiama `recompute_stato_pagamento`. **Nessun endpoint scrive più
   `contract.totale_versato += …` a mano.** Con una penna sola, **I5 (`totale_versato == Σ ENTRATA`)
   diventa vero per costruzione**.
3. **D-STORNO-HA-CASA** — le grandezze «cariche» oggi senza posting acquistano casa nel ledger:
   `quota_stornata` (`contracts.py:1751`) diventa `Σ` di postings di **contra-ricavo non-cash** (movimento
   di storno esplicito), e il **fold R2-bis del reopen** (`contracts.py:2038`) diventa un **posting di
   rettifica esplicito**, non un fudge di colonna. Esito: `residuo = prezzo − Σ(postings firmati)`, una
   **somma verificabile** invece di un dato hand-synced. (Wallet `crediti_cliente` e receivable
   `crediti_terminazione` restano tabelle — UI/worklist immutate — ma le loro variazioni si **specchiano**
   come postings così il residuo le veda dal ledger.)
4. **D-TRANSITION-EXECUTOR** — ogni transizione di stato del contratto (terminate, reopen, pay, unpay,
   incassa-residuo, eroga-wallet, incassa/annulla credito) passa per un **command-handler unico** in
   `api/services/financial/transitions.py`: carica lo stato → calcola la **decisione pura** (riusa
   `compute_settlement`/`contract_state`, **intatti**) → emette i postings **via la penna** → ri-deriva le
   colonne dal ledger → **asserisce gli invarianti come post-condizione** → committa atomico. I **router
   diventano sottili** (~30 righe: bouncer + parse + delega + serialize). La FSM `chiuso`/`motivo_chiusura`
   diventa una **tabella di transizione esplicita**; l'auto-close oggi **duplicato** (`rates.py` inline vs
   `agenda.py:301` `_sync_contract_chiuso`) si **unifica**.
5. **D-INVARIANTI-IMPOSTI** — `assert_contract_invariants` passa da **log-only-su-1-transizione** a **gate
   centralizzato su tutte** (`api/services/financial/invariant_gate.py`). **Strumenta-poi-imponi:** prima
   log-only ovunque (telemetria di violazione), poi promozione mirata a **409 + rollback** sui soli
   invarianti che la telemetria mostra puliti (feature-flag `INVARIANT_ENFORCEMENT`: raise in CI/dev/test,
   log in prod inizialmente). I **4 grep-guard testuali** (`check-all.sh:40-84`) si **ritirano**, sostituiti
   da **test semantici sul simbolo reale** (es. `assert CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO in
   CONTRACT_CASH_IN`) + un **property-based test** (`Hypothesis RuleBasedStateMachine`) che esplora
   stato×transizione riusando i builder dell'harness.
6. **D-MONEY-DIFFERITO** — il denaro non è float: il value-type `Money` (centesimi interi, un solo rounding
   mode, non-negativo) in `api/types/money.py` è la **fondazione numerica** che rende gli invarianti
   uguaglianze **esatte** invece di tolleranze. Ma è **differito all'ultimo gate** (G9.6): pervasivo (~150
   epsilon + ~200 `round()`), payoff diffuso, basso rischio-reale per un singolo trainer. Si introduce
   **dietro** `contract_state.py`/`contract_settlement.py` lasciando le firme `float→float` invariate (i
   ~15 consumer non cambiano una riga), validato dall'harness come oracolo di non-regressione; la fase
   storage (colonne + `CashMovement.importo` a INTEGER) è l'ultimo miglio, via `schema_sync` (Alembic è
   FROZEN sui DB deployati).
7. **D-STAGING** — il **principio** è stella polare immediata; il **build si stadia** G9.0→G9.6 (vedi
   `SPEC_G9`), **branch sempre rilasciabile**, ogni gate **behavior-preserving** fino al gate di
   enforcement esplicito (G9.4). L'ordine è vincolante: **strumenta (G9.0) → penna (G9.1) → storno-ha-casa
   (G9.2) → executor (G9.3) → impone (G9.4) → property-test (G9.5) → Money (G9.6)**. Non si costruisce
   l'executor prima della penna, non si accende il gate prima della telemetria, non si parte da Money.

**Invarianti che NON cambiano (asse DENARO e semantica di dominio):** `residuo()` net-aware (ADR-019),
Strada B (`totale_versato` lordo immutabile a ritroso, netto derivato), `residuo == 0 ⟺ saldato`,
cassa-immutabile/integrità di periodo (ADR-019), asse EROGATO (ADR-016), `Rinviato` fuori occupazione
(ADR-017), bilateralità (ADR-018), INV-RATE (ADR-021), wallet/receivable fuori da `residuo()` (ADR-020,
G7.10). **Questo ADR non cambia cosa il sistema calcola — cambia chi e come lo scrive.** Le ancore di
riconciliazione, da verificate-a-posteriori, diventano vere-per-costruzione.

## Consequences

- **Positive:** la doppia-verità ledger↔colonne si chiude **alla radice** (I5 per costruzione); aggiungere
  uno scenario diventa **additivo** (posting-rule + transizione) invece che lineare-col-numero-di-scenari;
  gli invarianti vengono **imposti** dal runtime, non sperati via grep; gli scenari secondari vengono
  **trovati da una macchina generativa** (Hypothesis) prima del cliente reale, non da un test-per-bug
  scritto dopo; i router tornano sottili e testabili; il denaro quadra al centesimo (G9.6). La
  `/reconciliation` passa da **load-bearing a rete di sicurezza periodica**. La maggior parte degli scenari
  che oggi richiederebbero un ADR diventa **non-problema**.
- **Negative / costo:** tocca codice load-bearing (i ~7 siti di scrittura, i corpi di terminate/reopen) —
  mitigato da rilocazione behavior-preserving + telemetria che precede l'enforcement; G9.2
  (storno-come-posting) ha blast-radius medio (parte dal solo storno); G9.6 (Money) è alto sforzo a payoff
  diffuso (perciò ultimo e gated). Nessun cambio di comportamento osservabile fino a G9.4; nessuna
  migrazione DB fino all'eventuale fase-storage di G9.6.
- **Follow-up:** spec di dettaglio per-gate in `SPEC_G9_FINANCIAL_COMMAND_LAYER.md`; a implementazione
  aggiornare `FINANCIAL_DOMAIN_MODEL.md` (ledger load-bearing, residuo come somma di postings),
  `TASSONOMIA_FINANZIARIA.md` (posting di storno contra-ricavo), `api/CLAUDE.md` (Contract Integrity Engine
  → financial command layer), `BUILD_LOG.md`. Depositare l'audit fondante
  `AUDIT_FINANCIAL_ARCHITECTURE_2026-06-30.md`.

## Rollback / Exit Strategy

Ogni gate è **indipendentemente reversibile** e behavior-preserving fino a G9.4:
- **G9.0** (sensore log-only + reconciliation bidirezionale): zero cambio di comportamento → rollback = no-op.
- **G9.1** (penna unica): adozione endpoint-per-endpoint; rollback = ripristino del `+=` inline sul singolo
  endpoint migrato (la penna è additiva finché non è l'unico scrittore).
- **G9.2** (storno-come-posting): rollback = `quota_stornata` resta colonna-memorandum (riapre il fatto che
  un euro del residuo non ha posting, ma è lo status quo).
- **G9.3** (executor): rilocazione behavior-preserving; rollback = i corpi tornano nei router (HTTP identico).
- **G9.4** (enforcement): governato da feature-flag `INVARIANT_ENFORCEMENT` → rollback = flag a `log` (torna
  osservazione); i grep-guard si ritirano **solo dopo** che i test semantici li sostituiscono (no buco).
- **G9.5** (property-test): test-only, zero impatto runtime → rollback = skip del test.
- **G9.6** (Money): introdotto dietro firme invariate, validato dall'oracolo float; rollback fase-calcolo =
  no-op; la fase-storage (INTEGER) è l'unico punto con migrazione, attivabile a valle e separatamente.

Nessun dato cancellato da nessun gate (coerente con ADR-019: la cassa non si tocca).

## Supersedes / Superseded By

- **NON supersede** alcun ADR. **Consolida** il meta-pattern di `ADR-016`→`ADR-021` fornendo lo strato di
  scrittura che presupponevano. Quegli ADR restano decisioni di dominio valide; ADR-022 è la loro **casa
  strutturale**. In particolare rende le ancore di ADR-019 (cassa-immutabile, I5) e di ADR-021 (INV-RATE)
  vere-per-costruzione invece che verificate-a-posteriori, e generalizza il rollout di
  `assert_contract_invariants` già differito da ADR-019 Addendum II/III («predisposta per 409»).
- Superseded by: —

## Stato implementazione (2026-06-30): ⏳ ACCETTATA — PIANIFICATA, zero codice.

Decisione/direzione **accettata** dal founder; implementazione **stadiata** G9.0→G9.6 (dettaglio e AC in
`SPEC_G9_FINANCIAL_COMMAND_LAYER.md`). **G1 (cifratura crm.db, ADR-013) resta in stand-by**: G9 e G1 sono
filoni indipendenti; la priorità relativa è scelta del founder. **Prossimo passo raccomandato: G9.0**
(sensore invarianti ovunque, log-only, + reconciliation bidirezionale + 2 quick-win), la mossa a leva più
alta e rischio più basso — il checker è già scritto, gira su 1/7 dei write-path, e log-only ha rischio
quasi-zero sui dati reali. Zero codice G9 prodotto a questa data.
