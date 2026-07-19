# API Layer — Backend Rules

FastAPI + SQLModel + SQLite (PostgreSQL-ready). Multi-tenant via JWT.

## Coordinamento

Per task cross-layer, coordinare esplicitamente per evitare conflitti.
A fine task: verifiche reali e note sui rischi residui.

## Architettura

```
api/
├── main.py              App factory, CORS (HTTPS), lifespan (backup+seed+integrity), security headers, Swagger gating (compiled), router mount
├── config.py            DATABASE_URL (env/port-auto), CATALOG_DATABASE_URL, JWT_SECRET, DATA_DIR (sys.frozen-aware), log env
├── database.py          Tri-engine (business + catalog + nutrition) + session factories + CATALOG/NUTRITION_TABLE_NAMES
├── logging_config.py    Bootstrap logging locale (`data/logs/fitmanager.log`, rotazione idempotente)
├── dependencies.py      get_current_trainer() → JWT validation
├── seed_exercises.py    Seed builtin in catalog.db: 500 esercizi + 940 relazioni + 750 media nei JSON → in DB 466 attivi / 894 / 750 (idempotente, seed media potato 2026-06-13)
├── auth/
│   ├── router.py        POST /login, /register, /reset-password, /setup-status (rate-limited via auth_limiter)
│   ├── service.py       bcrypt hash, JWT create/validate
│   └── schemas.py       TokenResponse, LoginRequest, PasswordResetRequest (con current_password)
├── models/              SQLModel ORM (table=True) — 22 modelli
│   ├── trainer.py       trainers (tenant root, saldo_iniziale_cassa)
│   ├── client.py        clienti
│   ├── contract.py      contratti (+ relationships: rates, movements, rinnovo_di FK self-referencing)
│   ├── rate.py          rate_programmate
│   ├── event.py         agenda
│   ├── movement.py      movimenti_cassa (ledger)
│   ├── recurring_expense.py  spese_ricorrenti
│   ├── exercise.py      esercizi → catalog.db (builtin, no trainer_id, read-only)
│   ├── exercise_media.py esercizi_media → catalog.db (foto start/end builtin)
│   ├── exercise_relation.py esercizi_relazioni → catalog.db (progressione/regressione/variante)
│   ├── workout.py       schede_allenamento + sessioni_scheda + esercizi_sessione + blocchi
│   ├── workout_log.py   allenamenti_eseguiti (monitoraggio compliance)
│   ├── measurement.py   misurazioni + valori_misurazione
│   ├── goal.py          obiettivi_cliente
│   ├── muscle.py        muscoli + esercizi_muscoli → catalog.db (no FK, application-level integrity)
│   ├── joint.py         articolazioni + esercizi_articolazioni → catalog.db (no FK)
│   ├── medical_condition.py condizioni_mediche + esercizi_condizioni → catalog.db (no FK)
│   ├── audit_log.py     audit_log (timeline modifiche)
│   ├── communication_log.py communication_log (log comunicazioni WhatsApp/tel/email)
│   ├── credito_terminazione.py crediti_terminazione → credito differito post-chiusura (G7.10, receivable FUORI da residuo())
│   ├── credito_cliente.py    crediti_cliente → wallet del cliente (G8.1/ADR-020, customer credit balance FUORI da residuo())
│   ├── todo.py          todos (trainer-owned)
│   └── share_token.py   share_tokens (UUID4 monouso per portale pubblico anamnesi)
├── routers/             REST endpoints con Bouncer Pattern — router dominio + runtime/support
│   ├── _audit.py        log_audit() helper condiviso
│   ├── agenda.py        CRUD eventi + credit guard + _sync_contract_chiuso
│   ├── assistant.py     Parse + commit NLP (feature flag ASSISTANT_V1_ENABLED)
│   ├── backup.py        Backup/Restore/Export/Verify (7 endpoint, WAL-safe)
│   ├── clients.py       CRUD clienti
│   ├── contracts.py     CRUD contratti + batch fetch enriched + renew + incassa-residuo (G6) + terminate/settlement-preview/reopen (G7.3-G7.4, bilaterale ADR-018) + crediti-terminazione incassa/annulla (G7.10)
│   ├── dashboard.py     KPI + alerts + clinical readiness + inline resolution (13 GET, ~980 LOC)
│   ├── exercises.py     Catalogo esercizi read-only da catalog.db + safety-map (catalog_session)
│   ├── goals.py         CRUD obiettivi + progress tracking (dual session)
│   ├── measurements.py  CRUD misurazioni + valori (dual session)
│   ├── movements.py     Ledger + pending/confirm + forecast + saldo + audit-log
│   ├── rates.py         CRUD rate + pay/unpay atomic
│   ├── recurring_expenses.py  CRUD spese fisse + close/rettifica
│   ├── system.py        Surface runtime/support: health, support snapshot, connectivity status/config/verify/portal validation
│   ├── todos.py         CRUD todos + toggle completato
│   ├── training_methodology.py  MyTrainer: qualita' metodologica programmi allenamento
│   ├── training_science.py  Generazione piani + analisi 4D + mesociclo (5 endpoint, zero DB)
│   ├── workout_logs.py  CRUD log allenamenti (monitoraggio)
│   ├── workouts.py      CRUD schede + sessioni + esercizi (deep IDOR chain)
│   ├── workspace.py     Cockpit operativo: today + session-prep + cases (4 GET read-only)
│   ├── communications.py Log comunicazioni WhatsApp/tel/email (POST log + GET registro all/per-cliente)
│   ├── training_intelligence.py Training Intelligence: dose-response muscolo×muscolo, balance, intensity, recovery, alert (1 GET, dual session)
│   ├── workout_diff.py  Workout Diff: piano vs eseguito per esercizio, compliance %, punti deboli/forti (1 GET, dual session)
│   └── public_portal.py Portale pubblico anamnesi + workout: generate token (JWT) + validate + submit (7 endpoint pubblici, portal_limiter via rate_limiter.py, feature flag PUBLIC_PORTAL_ENABLED)
├── schemas/             Pydantic v2 — schema dominio + runtime/system contracts
│   ├── assistant.py     ParseRequest/Response, CommitRequest/Response (6 schema)
│   ├── exercise.py      ExerciseCreate/Update/Response + media/relazioni/tassonomia
│   ├── financial.py     Contract/Rate/Movement/Dashboard/ClinicalReadiness/PaymentReceipt/RenewalChainItem DTOs
│   ├── goal.py          GoalCreate/Update/Response + progress
│   ├── measurement.py   MeasurementCreate/Response + valori
│   ├── public.py        ShareTokenCreate/Response, AnamnesiValidate/Submit (portale pubblico)
│   ├── safety.py        SafetyMapResponse + ExerciseSafetyEntry
│   ├── system.py        Health/SupportSnapshot + ConnectivityStatus/Config/Verify/PortalValidation contracts
│   ├── workspace.py     SessionPrepItem/HealthCheck/Alert/Hint/Response + OperationalCase + WorkspaceTodayResponse (~255 LOC)
│   ├── workout.py       WorkoutPlan/Session/Exercise Create/Update/Response
│   └── workout_log.py   WorkoutLogCreate/Response
└── services/            Business logic — servizi dominio + runtime/support + parser assistant + training science
    ├── contract_state.py  SSoT derivazione stato di vita contratto (Lifecycle 4 stati + sotto-stato denaro, funzioni pure)
    ├── cash_categories.py  SSoT categorie cassa + predicato "movimento contrattuale" bidirezionale (IN/OUT)
    ├── condition_rules.py  Regole deterministiche anamnesi → condizioni (80 pattern rules)
    ├── goal_engine.py      Calcolo progresso obiettivi
    ├── license.py          Verifica licenza JWT RSA (4-tier key resolution)
    ├── system_runtime.py   Helper condivisi health/support snapshot + backup metadata
    ├── connectivity_runtime.py Read-only probe Tailscale/Funnel + profile classification
    ├── connectivity_config.py  Apply idempotente `PUBLIC_PORTAL_ENABLED` / `PUBLIC_BASE_URL`
    ├── connectivity_verify.py  Verify end-to-end dell'origine pubblica via `{PUBLIC_BASE_URL}/health`
    ├── connectivity_portal_validation.py Validazione funzionale link anamnesi pubblico reale
    ├── rate_limiter.py     RateLimiter IP-based riusabile: auth_limiter (5/min, 20/h) + portal_limiter (30/min, 120/h)
    ├── safety_engine.py    Safety map per-esercizio (extract conditions + build map)
    ├── session_prep.py     Session Prep cockpit: 7-step pipeline (events + readiness + safety + contracts)
    ├── workspace_engine.py Workspace operativo: today/cases/detail + ranking + dominance matrix (~3000 LOC)
    ├── clinical_readiness.py  Readiness clinica condivisa (dashboard + myportal + session_prep)
    ├── assistant_parser/   Parser NLP deterministico (6 moduli)
    │   ├── normalizer.py, intent_classifier.py, entity_extractor.py
    │   ├── entity_resolver.py, confidence.py, orchestrator.py
    │   └── commit_dispatcher.py
    └── training_science/   Motore scientifico allenamento (10 core + 18 SMART, ~3500 LOC)
        ├── types.py, principles.py            — Fondamenta (enum, parametri carico)
        ├── muscle_contribution.py             — Matrice EMG 18x15 + dual volume
        ├── volume_model.py                    — MEV/MAV/MRV per muscolo x livello
        ├── balance_ratios.py                  — Rapporti biomeccanici (5 ratio)
        ├── split_logic.py, session_order.py   — Split + ordinamento fisiologico
        ├── plan_builder.py                    — Generatore 4 fasi + feedback loop
        ├── plan_analyzer.py                   — Analisi 4D (score 0-100)
        ├── periodization.py                   — Mesociclo a blocchi (4-6 sett)
        ├── registry/                          — SMART: 6 protocolli + evidence + selettore
        │   ├── evidence_types.py, protocol_types.py, protocol_registry.py
        │   └── protocol_selector.py
        ├── constraints/                       — SMART: constraint adapter read-only
        │   └── constraint_types.py, constraint_engine.py
        ├── demand/                            — SMART: vettore biomeccanico 10D + ceiling
        │   └── demand_types.py, demand_registry.py, demand_policy.py
        ├── runtime/                           — SMART: orchestrazione DB-aware
        │   ├── profile_resolver.py, exercise_catalog.py, exercise_ranker.py
        │   ├── plan_package_service.py, feasibility_engine.py
        │   └── validation_metadata.py, mappings.py, readiness.py
        └── validation/                        — SMART: 6 benchmark + 22 check + runner
            └── validation_catalog.py, validation_contracts.py
```

## Pattern Obbligatori

### Bouncer Pattern
Ogni endpoint inizia con il bouncer che verifica ownership:
```python
def _bouncer_rate(session, rate_id, trainer_id) -> Rate:
    rate = session.exec(
        select(Rate)
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(Rate.id == rate_id, Contract.trainer_id == trainer_id)
    ).first()
    if not rate:
        raise HTTPException(404, "Rata non trovata")
    return rate
```
Non trovato = 404. Mai 403 (non rivelare esistenza dati altrui).

### Deep Relational IDOR
Catena di verifica ownership attraverso FK:
- Rate → `Contract.trainer_id`
- Contract → verifica `Client.trainer_id` su POST (Relational IDOR)
- Event → `trainer_id` diretto
- Movement → `trainer_id` diretto

### Mass Assignment Prevention
Gli schema Create NON contengono mai:
- `trainer_id` (iniettato dal JWT nel router)
- `id` (auto-generato)
- Campi calcolati (`crediti_usati`, `totale_versato`, `stato`)

```python
class ContractCreate(BaseModel):
    model_config = {"extra": "forbid"}  # rifiuta campi extra
    id_cliente: int  # verificato via Relational IDOR
    # NO trainer_id, NO id
```

### Atomic Transactions
Operazioni multi-tabella usano UN singolo commit:
```python
# pay_rate: aggiorna rata + contratto + crea CashMovement
session.add(rate)
session.add(contract)
session.add(movement)
session.commit()  # UNICO commit — tutto o niente
```

### Batch Fetch (anti N+1)
Liste enriched usano 4 query batch:
```python
contracts = session.exec(query).all()  # 1. contratti
all_rates = session.exec(select(Rate).where(Rate.id_contratto.in_(ids))).all()  # 2. rate
clients = session.exec(select(Client).where(Client.id.in_(client_ids))).all()  # 3. clienti
event_counts = session.exec(select(Event.id_contratto, func.count(...)).group_by(...))  # 4. crediti usati
```

### Payment History Enrichment
Il dettaglio contratto (`get_contract`) carica lo storico pagamenti per ogni rata:
```python
# receipt_map: dict[int, list[CashMovement]] — tutte le rate (non solo SALDATE)
movements = session.exec(
    select(CashMovement).where(
        CashMovement.id_rata.in_(rate_ids),
        CashMovement.tipo == "ENTRATA",
        CashMovement.deleted_at == None,
    ).order_by(CashMovement.data_effettiva.asc())
).all()
# Ogni rata riceve campo `pagamenti: list[RatePaymentReceipt]` (cronologico)
# Backward-compat: `data_pagamento` e `metodo_pagamento` = ultimo pagamento
```

### Stato finanziario del contratto — SSoT `contract_state.py`
`api/services/contract_state.py` è l'**unica fonte** della derivazione dello stato di vita del contratto
(`Lifecycle` ∈ ATTIVO/SOSPESO/ESAURITO/CHIUSO/ELIMINATO) e del sotto-stato denaro. Funzioni **pure**
(no DB): i caller passano `crediti_usati` (batch-fetch) e `today`. **Regola d'oro:** nessun endpoint/KPI
ricalcola "attivo/scaduto/residuo" inline — tutti derivano da qui (`residuo()`, `crediti_residui()`,
`is_rate_planificabile()`, `is_engaged()`, costanti `SOGLIA_IN_SCADENZA_GG`/`SOGLIA_CHURN_GG`). Modello
vincolante: `docs/technical/FINANCIAL_DOMAIN_MODEL.md` (v1.3) + `TASSONOMIA_FINANZIARIA.md` (v1.2).

**Già in codice (Blocchi 0-4 + Prereq P + terminazione G7.0→G7.10):**
- `cash_categories.py` — predicato cassa **bidirezionale** (IN `ACCONTO_CONTRATTO`/`PAGAMENTO_RATA`/`INCASSO_CONGUAGLIO_CONTRATTO`, OUT `RIMBORSO_CONTRATTO`); fonte unica delle costanti categoria.
- **Audit della transizione `chiuso`**: `log_contract_lifecycle_transition()` in `_audit.py` (idempotente, no-commit), cablato in `pay_rate` (completamento), `unpay_rate` (riapertura_pagamento), `agenda._sync_contract_chiuso` (completamento/riapertura_crediti).
- Worklist finanziarie derivate da `contract_state`: `contracts-to-plan` (G1), `clients-to-recover` (lapsed), `suspended-contracts` (SOSPESO).
- Forecast: filtra `Contract.chiuso == False` sulle entrate certe (no entrata-fantasma da rate PENDENTI su contratti chiusi).
- **G6 incasso residuo diretto**: `POST /contracts/{id}/incassa-residuo` (`contracts.py`) — ENTRATA legata al contratto senza rata (categoria `PAGAMENTO_RATA`, `id_rata=None`), `totale_versato +=`, auto-close canonico via `_sync_contract_chiuso` (la transizione `chiuso` la logga lui, no doppio audit — G6 rispecchia `pay_rate`), residuo dal SSoT `contract_state.residuo()`, bouncer 404 + cap overpayment 422, UN solo commit. Riusa lo schema `RatePayment`. Il `residuo` SSoT è ora esposto anche su `ContractListResponse` (`residuo`) → il frontend lo **legge** (mai ricalcolo inline).

> **✅ Terminazione anticipata — IMPLEMENTATA (G7.0→G7.4, IMPL_PLAN_FINANCIAL_REALIGN §4 + SPEC_G7.0/G7.3):** schema 4 colonne (`totale_rimborsato`/`quota_stornata`/`data_chiusura`/`motivo_chiusura`, `contract.py`, PLAIN), categoria `RIMBORSO_CONTRATTO` (`cash_categories.py`), `netto_incassato`, conguaglio puro su base sedute Completate (`contract_settlement.py`, policy `pro_sedute` **PROVISIONAL** — valorizzazione gated dal tributarista), **`POST /terminate` + `GET /settlement-preview` (G7.3) + `POST /reopen` (G7.4)** (2 gambe: storno sempre + rimborso se overpaid; reopen è l'inverso esplicito state-driven), `kpi_incassato`→`netto_incassato()`, esclusione del rimborso dal burn variabile. **`chiuso` rimosso da `ContractUpdate`**: la chiusura passa SOLO da auto-close (completamento) o `POST /terminate`. **✅ G7.5 (2026-06-25):** query-cassa allineate al rimborso contra-ricavo (movement-stats/forecast/monthly_revenue + financial-trend contra-line + D4 guardia `data_chiusura` non-futura + D2 `sedute_prenotate` display). **✅ G7.6:** runbook bonifica contratti muti (`docs/operations/RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md`, data-driven, esecuzione trainer-driven). **✅ G7.7-R1/H1:** `unpay_rate` rifiuta **409** su contratto terminato (storno/rimborso) — senza, decrementerebbe `totale_versato` sotto `totale_rimborsato` e il clamp di `netto_incassato()` maschererebbe l'over-rimborso; path canonico = `POST /reopen`. **✅ G7.8/ADR-017:** il rinvio libera il credito — **occupazione-credito = `Programmato + Completato`**, `Rinviato` escluso (era contato come usato: `contracts.py:149` + i siti credito §3.1 + 5 produttori bridge incl. `rates.py` auto-close; `compute_settlement` invariato → asse denaro byte-identico). **✅ G7.7 (remediation audit):** H1 (`unpay`→409 su terminato) · M1 (reopen marker `chiusa_da_terminazione`) · M2 (guard `chiuso` su `update_rate`) · R4/R5 (trasparenza erogato↔occupazione) · R6 (igiene + grep-guard). **✅ G7.9 / ADR-018 (terminazione BILATERALE):** esito **balance-based** `CREDITO_CLIENTE/TRAINER/PARI` (`SALDO_A_PERDERE` esce dal modulo puro → azione del router); ramo `CREDITO_TRAINER` esige **scelta esplicita** (mai write-off implicito) — `INCASSA_ORA` (ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO`, importo editabile `[0, R−V]` solo verso il basso, `totale_versato +=`) oppure `RINUNCIA_ESPRESSA` (nota obbligatoria, audit `saldo_trainer_rinunciato`); `motivo_chiusura=TERMINAZIONE_SALDO_TRAINER`; `reopen` inverte anche la nuova ENTRATA (**1ª volta che decrementa `totale_versato`**, eccezione sanzionata come `unpay_rate`); ramo `CREDITO_CLIENTE`/RIMBORSO **byte-identico**; FE dialog a 3 vie. La nuova categoria entra negli aggregati cassa per `tipo==ENTRATA`+`id_contratto` (mai allowlist) → auto-inclusa come ricavo; grep-guard ADR-018 in `check-all.sh`. **✅ G7.10 (credito differito):** l'azione `A_CREDITO` della terminazione crea un receivable **`crediti_terminazione`** (tabella nuova, FK `id_contratto`/`id_cliente`/`trainer_id`; `create_db_and_tables` la crea al boot su tutti i DB — migrazione `b2c3d4e5f6a7` = record formale) FUORI da `residuo()`: il dovuto è stornato dal contratto e **ri-tracciato** nel receivable (mai una Rate su contratto chiuso; `residuo()==0` su CHIUSO preservato). Endpoint `POST /contracts/{id}/crediti-terminazione/{cid}/incassa` (anche parziale → `SALDATO`, ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO` + `totale_versato +=`; **niente `_sync`**, il contratto resta chiuso) **+ `/annulla`** (rinuncia residuo → `ANNULLATO`, zero cassa) **+ `GET /dashboard/crediti-da-incassare`** (worklist aging-driven, gemella G6). `reopen` esteso (gamba **C-ter**: receivable → `ANNULLATO`; gli incassi parziali sono già invertiti da C-bis, stessa categoria). **✅ G8.1 / ADR-019+020 (integrità contabile + wallet cliente) — SUPERA l'inverso-esatto di reopen:** `residuo()` ora **NET-AWARE** (`prezzo − netto_incassato − quota_stornata`, `netto = versato − rimborsato`; backward-compat, byte-identico dove `rimborsato=0`). **`reopen` NON-distruttivo "ricalcola-e-instrada"** (ADR-019): NON cancella più i `CashMovement` di terminazione (gambe delete C/C-bis RIMOSSE) — la cassa resta (fatti datati fiscalmente intoccabili), il residuo si ricalcola, `quota_stornata→0`, receivable+wallet→`ANNULLATO`, rate ripristinate; `compute_settlement` net-aware (`reso` vs `netto`) → ri-terminare un riaperto NON ri-rimborsa (PARI/CONSUNZIONE). Nuovo `GET /reopen-preview` (dry-run, R8 rinnovo-vivo). **Terminate ramo `CREDITO_CLIENTE` editabile** `[0, credito_cliente]` (default pieno, `metodo_rimborso` solo se rimborso>0); il non-rimborsato → **wallet `crediti_cliente`** (ADR-020, FUORI da `residuo()`, gemello-cliente di `crediti_terminazione`), erogabile via `POST /clients/{id}/crediti/{cid}/eroga` (USCITA `RIMBORSO_CONTRATTO`, **`id_contratto=None`** → non tocca `totale_rimborsato`/àncora di contratto, traccia da sé via `importo_erogato`) + worklist `GET /dashboard/rimborsi-da-erogare` + `GET /clients/{id}/crediti`. grep-guard ADR-019 in `check-all.sh` (reopen non soft-cancella CashMovement). **✅ G8.1.1 (reconciliation + transparency, ADR-019 Addendum):** F2 `reopen` riallinea il piano rate al residuo ricalcolato (`_reconcile_rate_plan`: taglio cronologico, PARZIALE mai sotto il saldato, sotto-copertura → "da pianificare"); F3 `_cap_rateizzabile` net-aware (`netto_incassato`); F4 sotto-stato denaro via `cstate.is_saldato()` (`residuo()≤0.01`, MAI `versato≥prezzo`) in `pay_rate`/`unpay_rate`/`incassa_residuo`; F1 `get_contract` espone `movimenti` = TUTTI i `CashMovement` `id_contratto` (acconto+rate+rimborsi+conguagli, l'erogazione wallet `id_contratto=None` è esclusa); F6 nuovo `GET /contracts/{id}/history` = timeline curata da `audit_log` (`_curate_contract_event`: terminato/riaperto entry ricca + dedup delle companion lifecycle; la pura cassa resta in F1/F5). FE: tab "Storico" del dettaglio (timeline cassa con saldo progressivo + timeline stato). Suite **691**. **✅ G8.2-prep / D1 forma-d (fotografia netta + chiude Bug-1 audit; ADR-019 Addendum II):** `reopen` ora **riassorbe** l'erogato dei wallet annullati in `totale_rimborsato` (gamba **R2-bis**) → rientra nel `residuo()` net-aware **per costruzione** (la cassa NON si tocca, ri-attribuzione gestionale; es. acconto 800/reso 200/wallet 600/eroga 250 → reopen → `totale_rimborsato=250`, `residuo()=450`, era 200 = wallet erogato perso). Ancora del rimborso **raffinata**: `totale_rimborsato == Σ USCITA RIMBORSO[id_contratto] + Σ erogato wallet RIASSORBITO` (I5). `reopen-preview` espone `wallet_erogato_riassorbito` (+ messaggio, mai silenzioso). Nuove funzioni pure in `contract_state.py`: **`posizione_netta_contratto`** (fotografia `versato − rimborsato − Σ erogato wallet vivi`, gradino per G8.2), **`assert_contract_invariants`** (I1/I4/I5 senza clamp-mask, in `reopen` via `_log_invariant_violations` **log-only**/predisposta-409), **`recompute_stato_pagamento`** (SSoT unico → de-dup 4 copie inline pay/unpay/incassa/reopen). `delete_client`/`delete_contract`: RESTRICT su posizione aperta (wallet/receivable APERTO). Harness `tests/test_financial_invariants_harness.py` (invariante×transizione). Suite **711**. **✅ Audit-residui integrità (2026-06-29, ADR-019 Addendum III + `SPEC §16`) — A/B/C backend-only, trasparenza/integrità amministrativa (asse DENARO invariato):** (A, P1) la companion lifecycle di `terminate` porta `rimborso_out` (cassa uscita), non `settlement.credito_cliente` (credito teorico) → audit grezzo a **una sola verità** sul rimborso parziale; (B, P2) il RESTRICT su wallet/receivable APERTO vale **SEMPRE** in `delete_contract` (dedentato fuori da `if not force`, simmetrico a `delete_client`) → `force` abbuona rate/crediti-seduta ma **non** orfana una posizione finanziaria; (C, P3) `_curate_contract_event` deriva la cassa preservata del reopen da `totale_rimborsato.new`+`wallet_erogato_riassorbito` (il defunto `rimborso_preservato` non era mai emesso). Suite **718**. **✅ G8.3 / ADR-021 (INV-RATE: il piano rate è una partizione del residuo):** un incasso **non-rata** (`incassa-residuo`, conguaglio) abbassava `residuo()` senza riconciliare il piano rate (riconciliato solo su reopen) → contratto SALDATO con rata PARZIALE/scaduta-**fantasma** (residuo-rata = l'incasso non-rata). Legge: contratto non chiuso → `Σ(previsto−saldato) ≤ residuo()` (eccedenza vietata, sotto-copertura "da pianificare" legittima). Tre leve: **B** `_reconcile_rate_plan` chiamata anche dopo `incassa-residuo` (taglia l'eccedenza, mai sotto il saldato); **I6** in `assert_contract_invariants(rate_attive=…)` (harness, chiude la classe); **A** proiezione nel read-model (`_to_response_with_rates` clampa `is_scaduta`/`rate_scadute` col `residuo()` → un saldato non ha rate scadute). Generalizza D-RECONCILIA-RATE (ADR-019) da reopen-only a ogni path. Asse DENARO invariato. **G8.2 (wallet auto-cross-contratto) = elevazione in panchina (D2 aperta).** **Prossimo: G1 cifratura.**

> **Consumo UI del SSoT (`docs/specs/SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` v1.1):** **Giro 1 IMPLEMENTATO** — `list_contracts`/`get_contract` attaccano alla riga i campi derivati da `evaluate_contract` (`lifecycle`, `money_substate`, `is_insolvente`, `in_scadenza`); `is_insolvente` è in `contract_state.py` (flag derivato `lifecycle ∈ {SOSPESO,ESAURITO} AND rate_scadute`, gemello di `is_rate_planificabile`); il frontend li **legge** via `frontend/src/lib/contract-status.tsx` (badge a 2 assi vita×denaro); la delega del residuo inline di `_to_response_with_rates` a `residuo()` è fatta. **Giro 2 pendente:** `rinnovi-incassi` + `workspace_engine` ancora reimplementano la classificazione off-SSoT + grep-guard in `check-all.sh`.

### Contract Integrity Engine
Il contratto e' il nodo centrale del sistema. 12 livelli di protezione:

> **Invariante di creazione (FDM §9.5.7, PREREQ-prezzo di G6):** `ContractCreate` **e** `ContractUpdate`
> impongono `prezzo_totale > 0` (`api/schemas/financial.py`, messaggio italiano didattico, non 422 crudo) —
> «niente prezzo = niente contratto»: senza prezzo non si attivano le coperture (assicurative/fiscali) né si
> incassa. Rende `residuo = 0 ⟺ saldato` vero **senza asterischi** e chiude il **credito-fantasma** (speculare
> al **debito-fantasma** che `quota_stornata` chiude in G7). Il tipo ORM resta `Optional` (legacy) → le due
> guardie di consumo del frontend (Giro 1) restano come difesa-in-profondità annotata.

1. **Residual validation** (`create_rate`, `update_rate`): via `_cap_rateizzabile()` — `acconto = totale_versato - sum(saldato)`, `cap = prezzo - acconto`, `spazio = cap - sum(previsto)`. `update_rate` usa `exclude_rate_id` per escludere la rata in modifica dal calcolo
2. **Chiuso guard**: `create_rate`, `generate_payment_plan`, `create_event(id_contratto)`
   rifiutano operazioni su contratti chiusi (400)
3. **Overpayment check** (`pay_rate`):
   - B-bis: importo ≤ residuo rata
   - B-ter: importo ≤ residuo contratto (prezzo - totale_versato)
4. **Auto-close/reopen — SIMMETRICO** (INVARIANTE critico):
   - Condizione: `chiuso = (stato_pagamento == "SALDATO") AND (crediti_usati >= crediti_totali)`
   - **Lato rate** (`rates.py`): `pay_rate` → auto-close | `unpay_rate` → auto-reopen (via stato_pagamento)
   - **Lato eventi** (`agenda.py`): `_sync_contract_chiuso()` — helper condiviso chiamato da:
     - `create_event` (crediti_usati sale)
     - `delete_event` (crediti_usati scende)
     - `update_event` quando `stato` cambia (es. Completato ↔ Cancellato)
   - **MAI** aggiungere operazioni che modificano `crediti_usati` senza chiamare `_sync_contract_chiuso()`
   - **Reopen-allowlist (G7.2):** l'auto-riapertura (credit-driven via `_sync_contract_chiuso` + payment-driven via `unpay_rate`) scatta SOLO se `motivo_chiusura == "COMPLETAMENTO"`. Le chiusure da terminazione (`TERMINAZIONE_*`) o manuali/legacy (`NULL`) NON si auto-riaprono — solo `POST /contracts/{id}/reopen` (G7.4, inverso esplicito state-driven) le riapre. Evita lo stato-zombie `chiuso=False ∧ quota_stornata>0`.
5. **Flexible rate editing** (`update_rate`): rate pagate (SALDATA/PARZIALE) modificabili con vincoli:
   - `data_scadenza`, `descrizione`: sempre modificabili
   - `importo_previsto`: modificabile se >= importo_saldato (422 altrimenti)
   - Stato auto-ricalcolato: se `saldato >= previsto` → SALDATA, altrimenti → PARZIALE
   - Residual check via `_cap_rateizzabile(exclude_rate_id=rate.id)`
6. **CashMovement date sync**: modifica `data_scadenza` su rata pagata → aggiorna atomicamente `data_effettiva` di tutti i CashMovement collegati (ENTRATA, non soft-deleted) + audit trail
7. **Delete guard**: contratto eliminabile solo se zero rate non-saldate + zero crediti residui.
   CASCADE: soft-delete rate SALDATE + tutti CashMovement + detach eventi
8. **Credit guard** (`create_event`): se `id_contratto` esplicito e `crediti_usati >= crediti_totali`
   → 400 "Crediti esauriti". Escape hatch: evento PT senza contratto (campo vuoto).
   **Occupazione-credito (G7.8/ADR-017 + G7.8-bis/Addendum I):** `crediti_usati = COUNT(PT in
   `contract_state.STATI_OCCUPAZIONE_CREDITO`)` — oggi {Programmato, Completato, Cancellato_Tardivo,
   No_Show}: le penali OCCUPANO (lezione persa per colpa del cliente); `Rinviato` e `Cancellato` liberano.
   Il predicato è un SSoT: **MAI re-inlineare la lista** (test semantico `test_occupazione_ssot.py` lo
   vieta); i siti calendario/recency a denylist `!= 'Cancellato'` restano (DISPLAY-EXEMPT); l'overlap
   usa l'asse separato `STATI_OCCUPAZIONE_SLOT` (le penali liberano lo slot, D-CALENDAR-OVERLAP).
9. **Rate date boundary** (`create_rate`, `update_rate`): `data_scadenza` rata non puo' superare
   `contract.data_scadenza` (422). `generate_payment_plan`: auto-cap Chargebee-style
   (`if due_date > contract.data_scadenza: due_date = contract.data_scadenza`).
10. **Contract shortening auto-cap** (`update_contract`): anticipando `data_scadenza`, le rate
    **NON-SALDATE** con data oltre il nuovo termine vengono **riportate alla nuova scadenza** (auto-cap
    Chargebee-style, come `generate_payment_plan`), MAI bloccate (issue C / decisione founder: era 422
    "Modifica prima le rate"). Il dovuto resta intero, le date si comprimono, ogni spostamento è auditato
    (`scadenza_anticipata`). Le SALDATE non si toccano (pagamento già avvenuto, niente riscossione futura).
11. **Expired contract detection** (lista contratti + lista clienti): `ha_rate_scadute` considera
    tutte le rate non saldate su contratti scaduti: `or_(Rate.data_scadenza < today, Contract.data_scadenza < today)`.
12. **Renewal chain** (`POST /contracts/{id}/renew`): crea nuovo contratto con `rinnovo_di = id`.
    Bouncer verifica ownership originale + client (Relational IDOR). Acconto + CashMovement atomico.
    `GET /contracts/{id}` ritorna `contratto_originale` (parent via rinnovo_di) + `rinnovi_successivi`
    (children: contratti con `rinnovo_di = id`). Schema: `RenewalChainItem` in `financial.py`.

### Conferma & Registra (Spese Ricorrenti)
Paradigma esplicito: l'utente vede le spese in attesa e le conferma manualmente.
Nessun auto-sync — `GET /stats` e' pure read-only.

**Endpoint**:
- `GET /movements/pending-expenses?anno=X&mese=Y` — calcola occorrenze non confermate
- `POST /movements/confirm-expenses` — crea CashMovement con `operatore="CONFERMA_UTENTE"`
- `POST /recurring-expenses/{id}/close` — chiusura/rettifica con cutoff contabile

**Regole chiusura/rettifica** (`/recurring-expenses/{id}/close`):
- Endpoint idempotente: può essere richiamato anche su spesa già disattivata
- Movimenti `> cutoff` devono avere storno attivo (`ENTRATA`, `categoria="STORNO_SPESA_FISSA"`)
- Movimenti `<= cutoff` non devono avere storno attivo (storno soft-delete quando non più necessario)
- Nessun hard-delete dello storico reale: solo storni e soft-delete
- `GET /movements/stats` tratta `STORNO_SPESA_FISSA` come rettifica di uscita fissa, non come entrata operativa

**Ancoraggio**: basato su `expense.data_inizio` (non `data_creazione`).
Cross-year safe con mese assoluto: `abs_target = anno * 12 + mese`.

5 frequenze supportate:
- **MENSILE**: ogni mese, key `"YYYY-MM"`
- **SETTIMANALE**: ogni lunedi del mese, key `"YYYY-MM-DD"`
- **TRIMESTRALE**: `(abs_target - abs_start) % 3 == 0`, key `"YYYY-MM"`
- **SEMESTRALE**: `(abs_target - abs_start) % 6 == 0`, key `"YYYY-MM"`
- **ANNUALE**: `mese == start.month`, key `"YYYY"`

Idempotenza: `INSERT WHERE NOT EXISTS` con dedup key `(trainer_id, id_spesa_ricorrente, mese_anno)`.

### Financial Forecast (Proiezione)
`GET /movements/forecast?mesi=3` — pure read-only, zero side effects.

Aggrega 3 fonti per produrre una proiezione finanziaria:
1. **Rate PENDENTE/PARZIALE** — `importo_residuo` raggruppato per mese scadenza (entrate certe)
2. **Spese ricorrenti attive** — occurrence engine per ogni mese futuro (uscite fisse)
3. **Storico ultimi 3 mesi** — media uscite variabili (`tipo=USCITA AND id_spesa_ricorrente IS NULL`)

Produce: 4 KPI predittivi + proiezione mensile + timeline cronologica con saldo cumulativo.
Riusa `_get_occurrences_in_month()` per le spese ricorrenti (stessa logica del pending engine).

## Convenzioni

- Nomi endpoint: italiano nel dominio (`id_cliente`, `data_scadenza`), inglese infrastruttura (`trainer_id`)
- Response: sempre Pydantic `model_validate(orm_object)` con `from_attributes=True`
- Error response: `HTTPException` con status code + detail string
- **Gestione eccezioni: catturare SOLO l'eccezione specifica attesa** (es. `except (ValueError, TypeError)` su un `json.loads`), **MAI `except Exception` largo** per controllo di flusso — degrada un errore duro in **fallimento silenzioso** (viola regola #6 Determinismo, pitfall #2/#7). L'**osservabilità/instrumentation** (es. `invariant_gate` di G9) che non deve toccare la transazione si rende **totale-per-costruzione** (funzione pura che non solleva) o si **disaccoppia post-commit**, **mai** la si avvolge in un catch. Lezione/dettaglio: `docs/specs/SPEC_G9_FINANCIAL_COMMAND_LAYER.md` §A.1-bis · `docs/learning/LEARNING_PROGRAMMAZIONE.md` §0.8.
- Logging: `import logging; logger = logging.getLogger(__name__)`
- Migrations: Alembic (`alembic/versions/`). `env.py` legge `DATABASE_URL` da environment (fallback: `alembic.ini`). Ogni migrazione va applicata a ENTRAMBI i DB (prod + dev)

## Dipendenze

```python
# Questo layer importa SOLO:
fastapi, sqlmodel, pydantic, jose, bcrypt, python-dotenv, dateutil
# NON importa MAI da: core/, streamlit, frontend/
```

## Ledger Integrity

Il libro mastro (`movimenti_cassa`) e' sacro:
- Movimenti con `id_contratto` o `id_spesa_ricorrente` → protetti da DELETE
- Ogni pagamento rata → CashMovement ENTRATA (con nota cliente)
- Ogni acconto contratto → CashMovement ENTRATA
- Ogni spesa ricorrente confermata → CashMovement USCITA
- Ogni rettifica chiusura → CashMovement ENTRATA con `categoria="STORNO_SPESA_FISSA"`
- operatore: "API" (manuale), "CONFERMA_UTENTE", "CONFERMA_CHIUSURA", "STORNO_UTENTE", "SISTEMA_RECURRING" (legacy)

## Soft Delete

Tutte le tabelle business hanno `deleted_at: Optional[datetime]`.
- SELECT: filtrano sempre `deleted_at == None`
- DELETE: impostano `deleted_at = datetime.now(timezone.utc)`
- Delete contratto: RESTRICT se rate non-saldate o crediti residui (409).
  CASCADE: soft-delete rate SALDATE + tutti CashMovement + detach eventi
- Delete cliente: RESTRICT se ha contratti attivi (chiuso=False, non eliminati)
- Sync engine: il NOT EXISTS filtra `AND deleted_at IS NULL`
- UNIQUE index: `uq_recurring_per_month` esclude record con `deleted_at IS NOT NULL`

### Workout Session Cascade (INC-2026-03-28b)

`_delete_sessions_cascade()` in `workouts.py` — ordine FK rigoroso:
```
schedule_slots → workout_logs → esercizi_sessione → blocchi → sessioni
```
Chiamata da `replace_sessions()` (PUT full-replace) e `delete_workout()`.
**Regola**: ogni nuova tabella con FK su `sessioni_scheda.id` DEVE essere aggiunta al cascade
PRIMA del delete sessioni. Violazione = 500 mascherato da errore CORS al frontend.
Test regressione: `test_workouts_crud.py::test_replace_sessions_with_schedule_no_500`.

## Audit Trail

Tabella `audit_log` + helper `log_audit()` in `api/routers/_audit.py`.
- Ogni CREATE/UPDATE/DELETE/RESTORE su entity business viene loggato quando applicabile
- Il campo `changes` contiene JSON diff campo-per-campo (solo UPDATE)
- `log_audit()` NON fa commit — il chiamante committa atomicamente
- `pay_rate` e `unpay_rate` generano 2 audit entries: rata + contratto

## Dashboard System (~980 LOC)

Endpoint in `dashboard.py` (worklist finanziarie derivate da `contract_state`):

| Endpoint | Scopo | Tipo query |
|----------|-------|------------|
| `GET /summary` | KPI aggregati (4 metriche) | `func.count/func.sum` |
| `GET /reconciliation` | Audit contratti vs ledger | Raw SQL con GROUP BY |
| `GET /alerts` | Warning proattivi (≈10 categorie, incl. orphan/clients_to_recover/suspended) | query aggregate + helper worklist |
| `GET /clinical-readiness` | Coda readiness clinica per onboarding | ORM + timeline computation |
| `GET /ghost-events` | Eventi fantasma per risoluzione inline | ORM + batch fetch clienti |
| `GET /overdue-rates` | Rate scadute per pagamento inline | ORM join 3 entita' |
| `GET /expiring-contracts` | Contratti in scadenza (ATTIVO + ≤30gg), esclude i rinnovati | ORM + batch fetch crediti |
| `GET /contracts-to-plan` | "Da pianificare" (G1): ATTIVO + residuo>0 + zero rate (`_contracts_to_plan_candidates`) | ORM + `contract_state` |
| `GET /clients-to-recover` | Clienti lapsed (non ingaggiato) per win-back (`_lapsed_client_candidates`) | ORM + `contract_state` |
| `GET /suspended-contracts` | Contratti SOSPESO (scaduti, sedute prepagate residue) (`_suspended_contracts_candidates`) | ORM + `contract_state` |
| `GET /crediti-da-incassare` | Crediti differiti APERTI (G7.10, receivable `crediti_terminazione` da terminazione A_CREDITO) | ORM join Client, aging |
| `GET /rimborsi-da-erogare` | Wallet cliente APERTI (G8.1/ADR-020, `crediti_cliente` da rimborso editabile parziale) | ORM join Client, aging |
| `GET /inactive-clients` | Clienti inattivi con ultimo evento | Raw SQL + batch fetch ultimo evento |
| `GET /birthday-clients` | Compleanni oggi + prossimi 7gg | Raw SQL + date comparison mese/giorno |

> **Pattern worklist finanziarie:** un helper `_*_candidates()` condiviso da endpoint (items) e alert
> (count) → `count == len(items)` garantito. La classificazione di stato passa SEMPRE da
> `contract_state` (mai inline). Aging "invertito" sui SOSPESO (più vecchio = più urgente: obbligazione).

### Clinical Readiness (`/clinical-readiness`)
Coda deterministica per onboarding/migrazione clienti. Per ogni cliente attivo calcola:
- **anamnesi_state**: "missing" | "legacy" | "structured" (`_get_anamnesi_state()`)
- **readiness_score**: 0-100 composito (anamnesi 40pt + misurazioni 30pt + scheda 30pt)
- **priority**: "high" | "medium" | "low" da `priority_score` deterministico
- **next_action_code/label/href**: CTA actionable con deep-link auto-start
- **timeline**: `_compute_timeline_due()` — gap immediati = overdue, review periodiche (30/21/180gg)
- **Ordinamento**: `priority_score` desc → `readiness_score` asc → cognome/nome

Schema: `ClinicalReadinessClientItem`, `ClinicalReadinessSummary`, `ClinicalReadinessResponse` in `clinical.py`.

Pattern condiviso per endpoint inline resolution:
- **Anti-N+1**: batch fetch dati correlati dopo query principale
- **Multi-entity select**: `session.exec(select(Rate, Contract, Client).join(...))` restituisce tuple
- **Date parse**: SQLite restituisce date come stringhe — `date.fromisoformat()` per confronti
- **Ordinamento urgenza**: record piu' vecchi/urgenti prima

## Safety Engine — Regole Dual-Session (INC-2026-03-28)

`api/services/safety_engine.py` costruisce la safety map per-esercizio incrociando anamnesi cliente (crm.db) con catalogo condizioni (catalog.db). Riceve due session:
- `session` → crm.db (Client, schede, contratti)
- `catalog_session` → catalog.db (Exercise, MedicalCondition, ExerciseCondition, muscoli)

**REGOLA FERREA**: la tabella `esercizi` vive in catalog.db. Ogni `select(Exercise...)` DEVE usare `catalog_session`, MAI `session`. Stessa regola per muscoli, articolazioni, condizioni mediche. Violazione = crash 500 silenzioso in produzione (mascherato da errore CORS al frontend).

Pipeline completa:
```
Client.anamnesi_json (crm.db, session)
  → extract_client_conditions() → set[condition_id]
  → condizioni_mediche (catalog.db, catalog_session)
  → esercizi_condizioni (catalog.db, catalog_session)
  → esercizi attivi (catalog.db, catalog_session)  ← BUG era qui: usava session
  → SafetyMapResponse { condition_count, entries, medication_flags }
```

Funzioni dual-session da verificare dopo ogni modifica:
- `safety_engine.build_safety_map()` — 4 query (1 crm + 3 catalog)
- `profile_resolver.resolve_plan_context()` — chiama build_safety_map
- `session_prep.py` — chiama build_safety_map
- `client_avatar.py` — chiama extract_client_conditions

Test in-memory con engine singolo NON copre bug session mismatch. Verificare manualmente con `python -c` sui database fisici separati.

Incidente completo: `docs/incidents/INC-2026-03-28-safety-engine-blind-spot.md`

## Test

Due famiglie di test:

**pytest** (`tests/`; conteggio autorevole: output della suite):
- DB SQLite in-memory, isolamento totale (StaticPool)
- `test_pay_rate.py` (12): pagamento atomico, overpayment, deep IDOR, storico pagamenti parziali
- `test_unpay_rate.py` (4): revoca pagamento, decrements, soft delete movement
- `test_rate_guards.py` (12): editing flessibile rate pagate, importo >= saldato, residuo su update, CashMovement date sync
- `test_soft_delete_integrity.py` (5): delete blocked with rates, restrict, stats filtrate
- `test_sync_recurring.py`: pending/confirm, chiusura/rettifica cutoff (anche su spesa disattivata), idempotenza, restore/rimozione storni, coerenza stats/grafico
- `test_contract_integrity.py` (16): residual, chiuso guard, auto-close, delete guards + cascade
- `test_aging_report.py` (4): bucket assignment, exclude saldate/chiusi, empty zeroes
- `test_dashboard_clinical_readiness.py`: readiness score, priority, timeline, CTA generation
- `test_workouts_crud.py` (12): create, replace_sessions, schedule generation, FK cascade (schedule slots + logs), bouncer IDOR, delete con cascade completo
- Run: `pytest tests/ -v`

**E2E** (`tools/admin_scripts/test_*.py`):
- Richiedono server avviato + DB reale
- Coprono: CRUD, IDOR, multi-tenant, mass assignment, pagamento atomico, dashboard
- Run: `python tools/admin_scripts/test_crud_idor.py` (etc.)

**Legacy** (`tests/legacy/`):
- Rotti — referenziano moduli eliminati (WorkoutGeneratorV2, ExerciseArchive)
- Da non eseguire finche' core/ non viene aggiornato
