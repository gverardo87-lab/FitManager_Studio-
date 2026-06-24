# IMPL_PLAN — Riallineamento finanziario v1.3 (strategia di implementazione)

**Versione:** 1.3 (2026-06-21) · **Stato:** materiale di lavoro (effimero, → `docs/archive/` a implementazione conclusa)
**Modello (SSoT):** `FINANCIAL_DOMAIN_MODEL.md` v1.3 + `TASSONOMIA_FINANZIARIA.md` v1.2
**Supera:** `docs/archive/specs/IMPL_PLAN_RINNOVI_SCADUTI.md` (storico).

> ## 🔖 RESUME POINT — stato al 2026-06-23 (ultimo commit `3be936f`, branch `FitManager_Studio`)
>
> **FATTO (mergiato + pushato):**
> - **Blocco 0** — `api/services/contract_state.py` SSoT (4 stati + sotto-stato denaro + engagement). 
> - **Blocco 1 (G1)** — "da pianificare" solo ATTIVO; `kpi_da_incassare_scaduto`.
> - **Blocco 2 (G4 + fix SOSPESO)** — `kpi_attivi/sospesi/esauriti`; `_lapsed_client_candidates` su `is_engaged`.
> - **Prereq P** — `cash_categories.py` (predicato cassa bidir.) · fix Forecast `Contract.chiuso==False` ·
>   `log_contract_lifecycle_transition` (audit transizione chiuso) in pay/unpay/agenda.
> - **Blocco 3** — worklist "Contratti sospesi" + **Estendi** (`GET /dashboard/suspended-contracts` + alert
>   + UI `/rinnovi-incassi`); 2 bottoni chiusura disegnati **disabilitati** (→ G7).
> - **Review bridge processata** (`ALLINEAMENTO_REVIEW_CODICE_v1.3` su Desktop): NOW-fix (AlertItem union,
>   `giorni_ritardo` clamp), delta modello assorbiti (guard **allowlist** §9.5.6/§4.7, 9ª query monthly_revenue),
>   **fix tz** `completed_today_count` (workspace).
> - **PREREQ-prezzo** (`d934948`) — invariante `prezzo_totale > 0` su `ContractCreate` **e** `ContractUpdate`
>   (FDM §9.5.7). Chiude il caso `prezzo None`/`prezzo ≤ 0` a monte: il residuo `prezzo − versato` è ora sempre
>   ben definito (vedi §3, G6 può assumere `prezzo > 0`).
> - **SPEC_VOCABOLARIO Giro 1** (`91cbc39`) — `is_insolvente` SSoT in `contract_state.py`; lista `/contratti` +
>   dettaglio derivano lo stato dal SSoT (niente ricalcolo inline); nuovo modulo frontend `lib/contract-status.tsx`.
> - **data_scadenza-null** (`3be936f`) — carnet **senza scadenza** first-class (FDM §2): `ContractCreate.data_scadenza`
>   reso `Optional` + checkbox UI "Senza scadenza". Decisione 1 dell'audit invarianti Contract.
> - **Blocco 4 (G6)** — `POST /contracts/{id}/incassa-residuo` (incasso ENTRATA diretto, senza rata): bouncer
>   → guard chiuso → residuo via SSoT → cap → `totale_versato +=` + auto-close canonico (`_sync_contract_chiuso`)
>   → audit, UN solo commit. Riusa `RatePayment`. Frontend: `useIncassaResiduo` + `IncassaResiduoDialog` su
>   SuspendedCard (`/rinnovi-incassi`) + dropdown `ContractsTable`. **+16 test** (`test_incassa_residuo.py`).
>   Review adversariale (13 agenti) → 4 fix: **`residuo` SSoT esposto su `ContractListResponse`** (il frontend
>   legge, non ricalcola — §8.1/§8.9), dialog `open` disaccoppiato dal target, test ledger-reale, assert categoria.
>   **Implementato, suite verde — commit pendente.**
>
> Suite **549 passed / 1 xfailed / 0 failed** (533 baseline + 16 G6).
>
> **⏭️ PROSSIMO: Blocco terminazione G7** (§4): schema (`totale_rimborsato`/`quota_stornata`/`data_chiusura`/`motivo_chiusura`),
> conguaglio puro policy-pluggable, endpoint atomico 2 gambe. **Rispettare i 4 BLOCKER §4.7** (residuo→SSoT;
> guard riapertura ALLOWLIST + il completamento marca `motivo_chiusura=COMPLETAMENTO`; soft-delete solo non-saldate;
> financial-trend doppia decomposizione). Allora `test_manual_close_not_reopened_by_agenda_edit` passa da xfail→xpass: **togliere il marker**.
>
> **DECISIONI APERTE da Giacomo (solo per G7, NON bloccano G6):** policy valorizzazione conguaglio (tributarista);
> enum `motivo_chiusura` (esito vs ragione); se togliere `chiuso` da `update_contract`; R/T per i 3 contratti muti (id 4/9/13).
>
> **Metodo:** model→spec→codice; commit per blocco con `check-all.sh`+`pytest` verde; bridge per i delta modello.

> Successore consolidato del piano di riallineamento, allineato a FDM v1.3 + TASSONOMIA v1.2.
> Prodotto da workflow Claude Code (**6 progettisti d'area + 4 verifiche adversariali + sintesi**),
> ancorato al codice reale del branch `FitManager_Studio`. I `required_changes` dei verdetti sono
> recepiti nei blocchi (sez. 9 per tracciabilità). Tutte le citazioni `file:riga` verificate sul codice vivo.
>
> Citazioni portanti confermate sul codice: `ContractUpdate` accetta `data_scadenza`+`chiuso` con
> `extra:forbid`; `RatePayment` riusabile per G6; `residuo` calcolato **inline** a `contracts.py:127` e
> `financial.py:274` (NON via SSoT); `contract_state.residuo()` (`:59-60`) da estendere con `quota_stornata`.

---

## 0. Preludio — installare gli SSoT + stato (Blocchi 0-2 fatti, cosa resta)

**NESSUN codice prima di questi passi documentali** (bridge rule: il modello è già deciso, qui si allinea la documentazione vincolante):

1. Copiare **FDM v1.3** + **TASSONOMIA v1.2** in `docs/technical/` (sostituiscono v1.2/v1.1). Aggiornare `docs/INDEX.md` e `BUILD_LOG.md`.
2. Aggiornare `docs/technical/IMPL_PLAN_FINANCIAL_REALIGN.md` alla v1.3:
   - Blocco 3 **ri-scoped** a "Estendi-solo" (le due chiusure si disegnano disabilitate);
   - inserire un **Blocco Prereq P** (P1/P2/P3) prima della terminazione;
   - inserire il **NUOVO Blocco Terminazione (G7)** dopo il Blocco 4;
   - registrare la remediation come runbook a sé.
3. Annotare in `api/CLAUDE.md`: predicato cassa bidirezionale + audit della transizione lifecycle del contratto.

**Stato del codice (già mergiato):**
- **Blocco 0 DONE** — `api/services/contract_state.py` SSoT puro + `tests/test_contract_state.py` (53 test). `Lifecycle` derivato `contract_state.py:76-84`; `residuo()` `:59-60`; `crediti_residui()` `:55-56`; `is_engaged` `:120-122`.
- **Blocco 1 DONE (G1)** — `dashboard.py` `_contracts_to_plan_candidates`; `contracts.py list_contracts` `kpi_da_incassare_scaduto` (invariante `residuo = a_rate + da_pianificare + da_incassare_scaduto`).
- **Blocco 2 DONE (G4 + fix SOSPESO)** — `contracts.py` `kpi_attivi/kpi_sospesi/kpi_esauriti`; `dashboard.py` `_lapsed_client_candidates` su `is_engaged` + `_crediti_usati_map` (`:519-533`) + `_coerce_date` (`:515-516`) riusabili.

**Cosa resta:** Blocco 3, Blocco 4 (G6), Prereq P, Blocco Terminazione (G7), Remediation runbook.

---

## 1. Sequenza & dipendenze

```
[Prereq P — read-side, no-op, BUILDABLE NOW]
   P0  api/services/cash_categories.py  (modulo neutro: costanti + set + predicati)
   P1  fix Forecast chiuso==False  (movements.py:1432-1441)   ── hard prerequisite
   P2  log_contract_lifecycle_transition (_audit.py)  + wiring pay_rate/agenda
   P3  read-side netting cablato in difesa (stats/burn/forecast-medie)  ── inerte finché G7 non scrive RIMBORSO
        │
        ▼
[Blocco 3 — Contratti sospesi + ESTENDI]  (INDIPENDENTE, zero schema, rilasciabile da solo)
   GET /dashboard/suspended-contracts + alert + sezione /rinnovi-incassi
   ESTENDI = PUT /contracts/{id} (riuso puro)
   2 bottoni chiusura DISEGNATI ma DISABILITATI ("disponibile a breve")
        │
        ▼
[Blocco 4 — G6 incassa residuo diretto]  (zero schema; consuma cash_categories di P0)
   POST /contracts/{id}/incassa-residuo  (prima cassa ENTRATA diretta sul contratto)
        │
        ▼
[Blocco Terminazione — G7]  (SCHEMA: 4 colonne plain + categoria RIMBORSO_CONTRATTO)
   contract_settlement.py (conguaglio puro, policy pluggable)
   POST /terminate /close /reopen /unterminate (atomici)
   accende numericamente i consumatori netto di P3 + le viste contrattuali dipendenti
   abilita i 2 bottoni di chiusura del Blocco 3
        │
        ▼
[Remediation runbook — 3 contratti muti id 4/9/13]  (dato vivo, procedura a sé)
   gamba REOPEN: disponibile ORA  |  gamba TERMINATE: solo dopo merge G7
```

**Buildable ORA vs bloccato dalla policy:**
- **Buildable ORA (~95%)**: tutta la struttura — schema, predicati, endpoint, transazioni atomiche, allineamento query, frontend, test.
- **Policy-gated (solo numerico)**: la **valorizzazione** di `valore_servizio_reso` (pro-sedute? base prezzo unitario? recesso forfettario IT) e la legittimità del forfeit in decadenza → decisione tributarista. Mitigato da `SettlementPolicy` pluggable + default `pro_sedute` marcato **PROVISIONAL**. La spec/meccanismo NON è bloccata; si sostituisce solo la formula.
- **Blocco 3 e Blocco 4 NON sono policy-gated**: nessun conguaglio, nessuna valorizzazione.

---

## 2. Blocco 3 — Contratti sospesi + ESTENDI

> **✅ STATO (2026-06-21, implementato).** Backend: helper `_suspended_contracts_candidates`
> (deriva SOSPESO da `contract_state`) + endpoint `GET /dashboard/suspended-contracts` + alert
> `suspended_contracts` (count == len, stesso helper). ESTENDI = `PUT /contracts/{id}` (riuso puro,
> nessun codice backend). Frontend: `SuspendedContractItem`, `useSuspendedContracts`, `SuspendedCard`
> + `ExtendDialog` (DatePicker minDate=oggi, default +30g) + KPI "Sospesi" + sezione in
> `/rinnovi-incassi`, icona alert in `AlertHub`. I 2 bottoni di chiusura disegnati **disabilitati**
> ("disponibile col prossimo aggiornamento") → atterrano in G7. Dual-debt esplicito (sedute vs denaro).
> Test: `test_suspended_contracts` (11). Suite 485 passed, next build verde.

**Scope.** Rendere visibile e azionabile lo stato **SOSPESO** (`chiuso=False` + scaduto + `crediti_residui>0`), oggi l'unico stato non-terminale "homeless". Unità = **CONTRATTO**. Azione attiva unica = **ESTENDI** (riporta ad ATTIVO spostando `data_scadenza`). I due bottoni di chiusura (`chiudi-con-conguaglio`, `decadi`) si **disegnano disabilitati** per comunicare il modello dei 3 modi di morte, ma vivono in G7 (design-scope ≠ build-scope: tutte le chiusure stanno nel blocco terminazione per non frammentare la migrazione schema). **Zero schema change.**

**Riuso (file:riga):**
- Derivazione SOSPESO: `contract_state.py:76-84` (`Lifecycle.SOSPESO`). Vietato ricalcolare inline.
- `crediti_residui()`/`residuo()`: `contract_state.py:55-60` (popolano i campi sedute/denaro della card — dual-debt).
- `is_engaged` già conta SOSPESO come ingaggiato: `contract_state.py:120-122` → il SOSPESO è già escluso da clients-to-recover, nessuna modifica lì.
- `_crediti_usati_map` (batch anti-N+1) `dashboard.py:519-533`; `_coerce_date` `:515-516`.
- Pattern helper-unico endpoint+alert (`count==len(items)`): `dashboard.py:546-594` (lapsed) + `426-477`.
- Costruzione `AlertItem` + grammatica sing/plur + link: `dashboard.py:857-868`.
- **ESTENDI = ZERO codice backend**: `update_contract` accetta `data_scadenza`; estendere in avanti NON attiva il contract-shortening guard (`contracts.py:618-657`, verdetto 1 confermato: il guard scatta solo all'accorciamento) né il cross-field guard (scadenza>inizio, `:621`); il lifecycle ri-deriva ad ATTIVO; audit già loggato dal diff generico.
- `ContractUpdate` ammette già `data_scadenza` con `extra:"forbid"`, NO `trainer_id` (**verificato** `financial.py:85-93`).
- `useUpdateContract` invalida `['dashboard']` come **prefisso** (`useContracts.ts:96-115`) → copre `['dashboard','suspended-contracts']` e `['dashboard','alerts']` senza nuova invalidazione.
- Template UI: `RecoverCard` (`rinnovi-incassi/page.tsx:293-404`); struttura pagina `:410-588`; `AlertHub` ALERT_ICON map `:35-44` + navigazione via `item.link` `:161-163`.

**Nuovo codice:**
- Helper `_suspended_contracts_candidates(session, trainer_id, today)` accanto a `_lapsed_client_candidates`: pre-filtro SQL (`chiuso==False`, `deleted_at None`, `crediti_totali != None`, `data_scadenza < today`) → `_crediti_usati_map` → derivazione `contract_lifecycle`, tieni SOLO `SOSPESO`. **Unità=contratto** (no collapse per cliente). Ordina per `giorni_ritardo` desc (aging invertito). Helper unico per endpoint+alert.
- Endpoint `GET /dashboard/suspended-contracts` → `{items, total}`: `contract_id`, `client_*`, `tipo_pacchetto`, `data_inizio`, `data_scadenza`, `giorni_ritardo`, `crediti_totali/usati/residui`, `residuo` (asse denaro), `prezzo_totale`. Read-only, multi-tenant via JWT.
- Alert category `suspended_contracts` in `get_dashboard_alerts` (severity `warning`, `count=len(helper)`, link `/rinnovi-incassi`).
- Frontend: `SuspendedContractItem` (`types/api.ts`); `useSuspendedContracts` (`useDashboard.ts`, queryKey `['dashboard','suspended-contracts']`); `SuspendedContractCard` + `ExtendDialog` inline (DatePicker `minDate=oggi`, default oggi+30g via `SOGLIA_IN_SCADENZA`); sezione "Contratti sospesi" + KpiCard "Sospesi" prima di "Clienti da recuperare"; voce `ALERT_ICON['suspended_contracts']`.
- **Dual-debt UX esplicita**: label `"N sedute da recuperare"` (asse crediti) vs `"Denaro da incassare €X"` (asse denaro), due debiti distinti, NON duplicazione.

**Test (`tests/test_suspended_contracts.py`, stile `test_clients_to_recover`):** appare SOSPESO; ESAURITO non compare; ATTIVO non compare; chiuso non compare; `crediti_totali=None` (solo denaro) non compare (confine asse-crediti vs asse-denaro → va in G6); ESTENDI rimuove dalla worklist; ESTENDI → `kpi_attivi+1/kpi_sospesi-1`; cliente del SOSPESO non in clients-to-recover; unità=contratto (2 contratti SOSPESO → 2 righe); aging invertito; alert `count==len(items)` + grammatica; multi-tenant; empty.

**Gate:** `bash tools/scripts/check-all.sh` + `pytest tests/`.

**Rischi (mitigati):** i 2 bottoni di chiusura cablati per errore → render **SOLO** `disabled`+tooltip, nessun `onClick`/hook/colonna; **code-review gate**: il diff del Blocco 3 NON deve toccare `models/contract.py`, `alembic/`, `schema_sync`, né aggiungere categorie movimento. ESTENDI verso data ≤ oggi → `minDate=oggi` + il backend valida `scadenza>inizio`. Drift alert↔worklist → stesso helper condiviso.

**Buildable now: SÌ, interamente.** Backend additivo (1 helper + 1 GET + 1 alert), frontend additivo, zero schema.

---

## 3. Blocco 4 — G6 incassa residuo diretto

> **✅ STATO (2026-06-23, implementato — commit pendente).** Endpoint `POST /contracts/{id}/incassa-residuo`
> in `api/routers/contracts.py` (riusa `RatePayment`, `_sync_contract_chiuso` da `agenda.py`,
> `CATEGORIA_PAGAMENTO_RATA` da `cash_categories`). Audit: la transizione `chiuso` è loggata **solo** da
> `_sync_contract_chiuso` (P2) → G6 rispecchia `pay_rate` (no doppio log). Frontend: `useIncassaResiduo`
> (invalidazione = `usePayRate`) + `IncassaResiduoDialog` riusabile, su `SuspendedCard` (`/rinnovi-incassi`)
> e dropdown `ContractsTable` (gated `lifecycle ∈ {sospeso,esaurito}` + residuo>0). **+16 test**
> (`tests/test_incassa_residuo.py`). **Fix da review adversariale:** il `residuo` ora è esposto dal SSoT su
> `ContractListResponse` (`residuo=state.residuo`) e il frontend lo **legge** (niente ricalcolo inline,
> §8.1/§8.9, forward-safe per G7); `open` del dialog condiviso disaccoppiato dal target (no glitch in
> fade-out); test riconciliazione interroga il libro mastro reale; assert `categoria==PAGAMENTO_RATA`.

**Scope.** Prima **cassa ENTRATA diretta sul contratto senza rata**: `POST /contracts/{id}/incassa-residuo` registra una ENTRATA legata al contratto, incrementa `totale_versato` (Strada B, LORDO crescente), ricalcola `stato_pagamento`, fa scattare l'auto-close date-independent, con bouncer 404 + cap anti-overpayment + audit atomico. Rende azionabile `kpi_da_incassare_scaduto` (Blocco 1). **Gemello in ENTRATA del rimborso G7.** Zero schema/migrazioni.

**Riuso (file:riga):**
- Bouncer `_bouncer_contract_owned` `contracts.py:902-913`.
- Costruzione `CashMovement` ENTRATA legato al contratto (pattern acconto) `contracts.py:564-580` + `flush` per `contract.id`.
- Costante categoria: **da `cash_categories.py` (P0)**, non importata cross-router da `rates.py:44` (recepito da verdetto 1 — evita refactor futuro del G6 import).
- Cap anti-overpayment a livello contratto: `rates.py:524-532` (`importo > residuo+0.01 → 422`).
- Incremento `totale_versato += importo` + ricalcolo `stato_pagamento`: `rates.py:547-557`.
- Auto-close **canonico** `_sync_contract_chiuso` `agenda.py:299-329` (no commit, DB-aware, early-return su `crediti_totali` None — verdetto confermato).
- Body riusabile **as-is**: `RatePayment` (`importo gt=0`, metodo validato, `data_pagamento` default oggi, `extra:"forbid"`, NO `id_contratto/id_cliente`) — **verificato** `financial.py:157-183`.
- Audit diff + `log_audit` senza commit: `rates.py:598-601` + `_audit.py`.
- Single-commit: `rates.py:602`.
- Hook+invalidazione simmetrica da clonare: `useRates.ts:196-205` (`usePayRate`).

**Nuovo codice / flusso endpoint:** (A) bouncer 404 → (B) guard chiuso 400 → (C) `residuo = round(max(0, prezzo - versato), 2)`; se `≤0.009 → 400`. Con **PREREQ-prezzo** (`d934948`, invariante `prezzo_totale > 0` garantita su `ContractCreate` **e** `ContractUpdate`, FDM §9.5.7) il caso `prezzo None` **non esiste più**: G6 può assumere `prezzo > 0` e il guard a 400 segnala solo il residuo già saldato → (D) cap `importo > residuo+0.01 → 422` → (E) `totale_versato += importo` + ricalcolo stato → (F) `CashMovement` ENTRATA (`categoria=CATEGORIA_PAGAMENTO_RATA`, `id_contratto` set, `id_rata=None`, note `"Incasso residuo diretto - {cliente}"`) → (G) auto-close via `_sync_contract_chiuso(session, contract.id)` → (H) `log_audit` contract UPDATE con diff `totale_versato`+`stato_pagamento` **E `chiuso`** (colma il gap di `pay_rate`) → **UN solo `session.commit()`**. Nessuno storno, nessuna modifica a ritroso di `totale_versato`.
- **Categoria movimento**: riusare `CATEGORIA_PAGAMENTO_RATA` (coerente col predicato del modello, distinguibile via `id_rata IS NULL` + note). Verdetti confermano: saldo/reconciliation/trend chiavano su `id_contratto`, NON su categoria → zero silent-loss. Una categoria distinta è rinviata/abbinata all'allineamento del predicato in G7.
- Frontend: `useIncassaResiduo` (invalidazione **identica** a `usePayRate`: `contract, contracts, dashboard, movements, movement-stats, financial-trend, aging-report, cash-balance` + toast; date via `toISOLocal`); `IncassaResiduoDialog` (UX clonata da `PayRateForm`, quick "Tutto (€residuo)" cap-limitato); surface nel bucket "da incassare scaduto" in `contratti/page.tsx` + `rinnovi-incassi/page.tsx`. Label "denaro da incassare" distinta da "sedute da recuperare".

**Test (`tests/test_incassa_residuo.py`, mirror `test_pay_rate`):** incasso su residuo>0; `CashMovement` ENTRATA con `id_contratto` set/`id_rata None`; **BOUNDARY** auto-close ESAURITO+ultimo residuo → `chiuso=True`; **BOUNDARY** no-close su SOSPESO saldato con crediti residui; overpayment 422; residuo 0/contratto chiuso 400; deep IDOR 404; reconciliation allineata; atomicità su input invalido; audit con transizione `chiuso`.

**Rischi (mitigati):** drift dell'invariante auto-close (3 sedi: `rates.py:559-571` inline, `agenda.py:299-329` helper, ora consumo G6) → riusare il canonico `_sync_contract_chiuso`; flag tech-debt: consolidare in un helper unico quando si tocca G7. Rate-fantasma post auto-close → **dipendenza esplicita: fix Forecast P1**. Import-cycle: **verdetti confermano nessun ciclo**; con P0 la costante viene da `cash_categories.py`, l'unico import cross-router residuo è `_sync_contract_chiuso` da `agenda.py` (sicuro).

**Buildable now: SÌ.** Zero schema, endpoint additivo. Prerequisito da schedulare insieme: fix Forecast P1.

---

## 4. Blocco Terminazione (G7) — schema + conguaglio puro + endpoint atomico a 2 gambe

> **Consolidamento (verdetto 1):** casa unica del conguaglio puro = **`api/services/contract_settlement.py`** (mantiene `contract_state.py` minimale); le estensioni SSoT degli assi (`residuo()` esteso, `netto_incassato()`) restano in `contract_state.py`. Casa unica costanti/predicato cassa = **`api/services/cash_categories.py`** (P0).

**Scope.** Terza modalità di morte: terminazione anticipata umana su contratto vivo, conguaglio su **base sedute**, Strada B + invariante no-debito-fantasma. CHIUSO sempre qualificato da `motivo_chiusura`. Tutto derivato da `contract_state`, transazione **unica atomica**.

### 4.1 Schema (BUILDABLE NOW — struttura non policy-gated)
4 colonne **PLAIN** su `contratti` (pitfall #15: **niente `foreign_key=`**, gemelle di `esito_rinnovo_motivo`), `api/models/contract.py` dopo `:55`:
- `totale_rimborsato: float = Field(default=0)` — monotonico, LORDO rimborsi.
- `quota_stornata: float = Field(default=0)` — write-off (porta `residuo`→0 senza riscrivere `prezzo_totale`). **Campo storno-residuo CONFERMATO necessario**: `residuo()` è usato anche nel dettaglio (non solo nelle worklist gated da lifecycle).
- `data_chiusura: Optional[date] = None`.
- `motivo_chiusura: Optional[str] = Field(default=None, index=True)` — `COMPLETAMENTO|CONSUNZIONE|TERMINAZIONE_RIMBORSO|TERMINAZIONE_DECADENZA`. `non_rinnova` **NON entra qui** (resta `esito_rinnovo_motivo`, asse cliente ortogonale).
- Categoria movimento `RIMBORSO_CONTRATTO` (USCITA) = valore TEXT di `CashMovement.categoria`, **nessuna DDL**.

**Migrazione doppio binario:**
- Alembic `add_termination_fields_to_contratti`, **`down_revision='b2f1a9c7d4e3'`** (verdetto 4: head unico tra 31 revisioni, mai usato come down_revision). `batch_alter_table` add_column ×4 + `create_index('ix_contratti_motivo_chiusura', ['motivo_chiusura'])` — **nome indice identico** a `ix_{table}_{column}` di schema_sync (convergenza/idempotenza).
- `schema_sync` auto-ADD-column dai metadata ORM al boot per DB deployati (Chiara/Alessio), idempotente, frozen-safe (`schema_sync.py:405-443`; `_resolve_default` `:127-154`). Zero codice schema_sync nuovo.

### 4.2 Conguaglio puro policy-pluggable (BUILDABLE NOW — solo valorizzazione policy-gated)
`api/services/contract_settlement.py` (zero DB, specchio di `contract_state.py`):
- `SettlementPolicy(mode, base_valorizzazione, arrotondamento)` **PLUGGABLE**.
- `valore_servizio_reso(sedute_erogate, prezzo_totale, crediti_totali, policy)` — default pro-sedute `prezzo*sedute/crediti`, marcato **PROVISIONAL**.
- `conguaglio = valore_servizio_reso − totale_versato` (firmato); `<0 → RIMBORSO` (`importo=abs`); `>=0 → SALDO_A_PERDERE` (write-off); `~0 → NULLO`.
- **BASE SEDUTE, mai tempo.** `sedute_erogate` = `count(Event Completato PT)` batch-fetch, **derivato server-side** (determinismo): NON è input dell'endpoint.

### 4.3 Estensione SSoT (BUILDABLE NOW)
In `contract_state.py`:
- `residuo()` (`:59-60`) esteso: `round(max(prezzo − versato − getattr(contract,'quota_stornata',0), 0.0), 2)`. **`getattr` con default 0 NON-negoziabile** (verdetto 1: i 53 test usano `SimpleNamespace` senza il campo; la finestra pre-G7 in produzione non ha la colonna). Firma invariata → si propaga a `money_substate`/`is_residuo_incassabile_diretto`/`evaluate_contract`.
- `netto_incassato(contract) = round(max(totale_versato − getattr(contract,'totale_rimborsato',0), 0), 2)` — DERIVATO, **mai ridurre `totale_versato`**.

### 4.4 Endpoint atomico a 2 gambe (BUILDABLE NOW)
`POST /contracts/{id}/terminate` (schema `ContractTerminate`: `motivo_chiusura`, `note?`, `metodo_rimborso?`, `data_chiusura?=today`; `extra:forbid`; **NO campi calcolati/`totale_versato`/`totale_rimborsato` in input — mass-assignment**). Flusso, **UN solo `session.commit()`**:
1. bouncer 404 → guard `chiuso==False` else 400.
2. deriva `sedute_erogate` (PT completati) → `compute_settlement`.
3. **GAMBA RIMBORSO** (se `rimborso_dovuto>0` e `motivo=TERMINAZIONE_RIMBORSO`, richiede `metodo_rimborso` else 422): `CashMovement` USCITA `RIMBORSO_CONTRATTO` + `contract.totale_rimborsato += importo`. **Mai toccare `totale_versato`.**
4. **GAMBA STORNO**: `contract.quota_stornata += residuo_corrente` (→ `residuo()`=0, `prezzo_totale` immutato) + **soft-delete rate non-saldate**.
5. `chiuso=True` + `motivo_chiusura` + `data_chiusura`.
6. `log_audit` su contract (set completo, **incluso snapshot `sedute_erogate`**) + movement CREATE + rate DELETE.

Companion read-only `GET /contracts/{id}/settlement-preview` → `ContractSettlement` (zero side-effect, pattern `ImpactPreviewResponse` `movements.py:149-159`): il dialog mostra rimborso/storno PRIMA della conferma (SSoT backend).

`POST /contracts/{id}/close` = bottone "decadi" (`TERMINAZIONE_DECADENZA`): **storno-only**, zero USCITA (forfeit auditato, non silente).

`POST /contracts/{id}/reopen` (o `PUT chiuso=False`, **già supportato** da `ContractUpdate.chiuso`, verificato `financial.py:93`): `chiuso=False` + azzera `motivo_chiusura`/`data_chiusura`. Zero cassa. Path REOPEN del runbook, **disponibile ORA**.

`POST /contracts/{id}/unterminate`: inverso per chiusure con denaro — soft-delete del `CashMovement` RIMBORSO **via ORM (`deleted_at=now`), NON via endpoint** (`delete_movement` blocca `id_contratto!=None`, `movements.py:1278-1283`; pattern `unpay_rate` `rates.py:679-682`), `totale_rimborsato -=`, `quota_stornata=0`, ripristina rate, `chiuso=False`. Atomico+audit.

**Riuso scheletri (file:riga):** `pay_rate` build-then-single-commit `rates.py:547-602`; `unpay_rate` reversal+soft-delete `rates.py:612-696`; STORNO compensativo `recurring_expenses.py:588-609`; bouncer `contracts.py:902-913`; conteggio sedute erogate `contracts.py:713-720`; template renew movimento `contracts.py:859-896`; `_to_response_with_rates` `contracts.py:124-131`; `ImpactPreviewResponse` `movements.py:149-159`; dialog distruttivo `DeleteContractDialog.tsx`.

### 4.5 ContractResponse + frontend (BUILDABLE NOW)
`ContractResponse` (`financial.py:96-114`) += `totale_rimborsato`, `quota_stornata`, `data_chiusura`, `motivo_chiusura` + `netto_incassato` come `@computed_field`. `ContractListResponse`/`ContractWithRatesResponse` ereditano. **`_to_response_with_rates` deve delegare `residuo` a `contract_state.residuo()`** (vedi 4.7). `types/api.ts` `Contract` (`:611-627`) += i 5 campi (`float→number`, `Optional→string|null`). Hook `useTerminateContract`+`useSettlementPreview` (invalidazione `contract/contracts/movements/movement-stats/aging-report/forecast/cash-balance/dashboard`); `TerminateContractDialog` (conferma testuale, preview conguaglio, motivo + `metodo_rimborso` condizionale); **abilitazione dei 2 bottoni del Blocco 3**.

### 4.6 INVARIANTE fonte-unica-dell'importo (verdetto 2, BLOCKER)
`importo_rimborso = round(abs(conguaglio), 2)` calcolato **UNA volta** e usato identico per `movement.importo` E per `totale_rimborsato +=` (specchio `pay_rate` `rates.py:551,584`). Idem: `residuo()` in **una variabile unica** per `quota_stornata +=`. Senza questo, la leg di reconciliation diverge silenziosamente **anche dentro un solo commit**.

### 4.7 ANTI-PATTERN espliciti (verdetti 2 e 3, BLOCKER-grade)
- **G7 NON chiama mai `_sync_contract_chiuso`** (`agenda.py:299-329`). È credito-driven: terminare un SOSPESO (saldato, crediti residui) farebbe `should_be_chiuso=False` → **RESET `chiuso=False` dentro lo stesso commit, annullando la terminazione**. G7 setta `chiuso/motivo/data_chiusura` direttamente. È il punto in cui l'infra condivisa con G6 **deve divergere**.
- **⚠️ Guard ALLOWLIST sul ramo di RIAPERTURA di `_sync_contract_chiuso` (LOAD-BEARING, review bridge §1 + addendum §6).** Non basta che il `terminate` non chiami `_sync`: l'agenda lo chiama **comunque** (`create/update/delete_event`) sugli eventi PT del cliente. Oggi il ramo di auto-riapertura (`chiuso=True→False` quando i crediti non sono esauriti) riapre **qualsiasi** chiusura non-da-completamento → stato zombie `chiuso=False ∧ quota_stornata>0` (viola §9.5.6). **Fix vincolante — ALLOWLIST, non denylist:** il ramo di riapertura scatta **SOLO se `motivo_chiusura == COMPLETAMENTO`**; ogni altro valore — `TERMINAZIONE_*` **e `NULL` (chiusura manuale/legacy)** — non si riapre (solo `reopen`/`unterminate` espliciti). ⚠️ Una **denylist** (`motivo ∈ TERMINAZIONE_* o quota_stornata>0`) **manca il caso reale** della chiusura manuale (`motivo=NULL`, nessuno storno) = quello che il test esercita → lo strict-xfail non diventerebbe **mai** xpass. **Due prerequisiti:** (1) i percorsi di auto-close per completamento (`pay_rate`; ramo di chiusura di `_sync_contract_chiuso`) **devono scrivere `motivo_chiusura = COMPLETAMENTO`** — senza, la allowlist congela anche le riaperture legittime di completamento; (2) doppio significato del `NULL` dichiarato (guard = non-riaprire; runbook = completamento implicito → un completamento legacy non si auto-riapre più, direzione sicura). **Alternativa (decisione Giacomo):** togliere `chiuso` da `update_contract` → solo `terminate`/`close` chiudono (scrivono il motivo) → la chiusura-manuale-senza-motivo non esiste più. Tracciato da `test_lifecycle_audit.test_manual_close_not_reopened_by_agenda_edit` (**xfail strict** → xpass **solo** quando atterrano **entrambi** i prerequisiti). Delta modello in FDM §9.5.6.
- **`residuo` nel dettaglio è MANDATORY-fix.** `contracts.py:127` calcola `residuo` inline (**verificato**), `financial.py:274` lo documenta. Dopo lo storno mostrerebbe **debito-fantasma nel punto più guardato della UI**. Delegare a `contract_state.residuo()`. `importo_da_rateizzare` (`:130`) e `disallineamento` (`:131`) ereditano la correzione. Test: terminato → `residuo==0` AND `somma_rate_pendenti==0` AND `piano_allineato==True`.
- **Soft-delete rate = TUTTE le non-saldate (PENDENTE+PARZIALE, qualsiasi data), ESCLUSE le SALDATA.** **NON riusare `delete_contract:761-788` verbatim** (cancella anche SALDATA + i loro `CashMovement` ENTRATA → distrugge denaro incassato, rompe l'àncora `totale_versato == Σ ENTRATA`). Le SALDATA e i loro movimenti **sopravvivono**.
- **Snapshot `sedute_erogate` nell'audit** al momento della terminazione: `crediti_usati` è event-derived e può driftare; è l'unico record che soddisfa no-silent-loss per le sedute forfettate.
- **Invariante `quota_stornata>0 ⟹ chiuso=True`**: i KPI inline residuo (`contracts.py:285-286,314`) NON sottraggono `quota_stornata`, safe SOLO perché filtrano `if not c.chiuso`. Documentare/asserire l'invariante (o migrare quelle formule a `residuo()`).

### 4.8 Idempotenza (verdetto 2 — ridimensionato)
Il guard `chiuso==False → 400` è **read-time, non DB-level**. Sotto concorrenza due `terminate` potrebbero produrre doppio rimborso. **Rischio residuo LOW** (app single-user localhost). Hardening opzionale: `UPDATE ... WHERE chiuso=0` + rowcount check. Non vendere come idempotenza forte.

### 4.9 Vincolo post-commit
Tutte le mutazioni DB **PRIMA** del `session.commit()` unico; dopo, solo `refresh`+serializzazione. `flush` prima del `log_audit` del movement per popolarne l'`id`, stessa transazione.

**Test:** `test_contract_settlement.py` (puro); `test_contract_terminate.py` (transazione unica/rollback; rimborso crea USCITA + `totale_rimborsato` cresce, `totale_versato`/`prezzo_totale` INVARIATI; storno → `residuo()=0`; soft-delete solo non-saldate; bouncer 404; mass-assignment; reversibilità; decadenza storno-only); `test_contract_state.py` (residuo con `quota_stornata`); `test_schema_sync.py` (4 colonne + indice, **ZERO FK** via `PRAGMA foreign_key_list`); no-silent-loss.

**Buildable now: ~95%.** Policy-gated solo la valorizzazione numerica e la legittimità del forfeit. **Dipendenza: dopo G6.**

---

## 5. Predicato cassa contrattuale bidirezionale + allineamento 9 query

**SSoT unico:** `api/services/cash_categories.py` (P0, zero DB, zero import di router) — **introdotto PER PRIMO** (verdetto 1, evita refactor del G6 import):
- Costanti `CATEGORIA_ACCONTO_CONTRATTO`, `CATEGORIA_PAGAMENTO_RATA`, `CATEGORIA_RIMBORSO_CONTRATTO`, `CATEGORIA_STORNO_SPESA_FISSA`.
- Set `CONTRACT_CASH_IN={ACCONTO,PAGAMENTO_RATA}`, `CONTRACT_CASH_OUT={RIMBORSO_CONTRATTO}`.
- Predicati `is_contract_inflow/outflow`, `signed_contractual_amount` (+IN/−OUT). Esposto in 3 forme (booleano Python; costanti+set per where ORM; bound-param nelle 2 query raw-SQL reconciliation) → **una fonte, zero drift Python↔SQL**.
- Consolidare `contracts.py:42` e `rates.py:44` importando da qui (zero cambio valore stringa).

**Modello mentale (specchio `STORNO_SPESA_FISSA`, `movements.py:1132-1156`):** il rimborso è **contra-ricavo, non costo**.
**Single-treatment (verdetto 3):** in `stats` il rimborso riduce **SOLO** le entrate ED è escluso dalle uscite variabili — **mai entrambi** (il `margine_netto` è identico, farlo due volte sottrae due volte).

| # | Query | file:riga | Trattamento | Edit |
|---|-------|-----------|-------------|------|
| 1 | `_compute_saldo`/`get_balance` | `movements.py:66-69,89-105`/`373-440` | **Saldo reale (netto)** — `_signed_importo` rende USCITA negativa | **NESSUNO** (test non-regressione) |
| 2 | `_compute_variable_burn_rate` | `movements.py:298-310` | **Burn — ESCLUDE rimborso** | `NOT RIMBORSO_CONTRATTO` al filtro USCITA |
| 3 | `get_movement_stats` | `movements.py:1139-1158,1170-1189` | **Margine — contra-ricavo**: sottrae da entrate, esclude da uscite variabili; day-bucket come riduzione entrate | edit |
| 4 | `get_forecast` (medie burn) | `movements.py:1486-1496,1524-1533` | **ESCLUDE rimborso** | edit |
| 5 | `get_forecast` (entrate certe) | `movements.py:1432-1441` | **FIX P1 phantom-income** | `Contract.chiuso == False` |
| 6 | `get_financial_trend` | `movements.py:1609-1654` | **Vista contrattuale (netto)**: `incassi_contratti`/`cash_flow_reale` sottraggono rimborso + campo `rimborsi_contratti` | edit (dipende da G7) |
| 7 | `get_reconciliation` | `dashboard.py:177-208,127-138` | **Àncora (LORDO) INVARIATA** + **NUOVA leg separata** `totale_rimborsato` vs `Σ USCITA RIMBORSO` | additivo (dipende da G7) |
| 8 | `get_cash_audit_log` (flow_hint) | `movements.py:899-905` | **flow_hint segno-aware** per OUT contrattuali | edit |
| 9 | `get_dashboard_summary` (`monthly_revenue`) | `dashboard.py:84-94` | **Vista contrattuale (netto), bridge §2.2**: KPI revenue del mese su `tipo==ENTRATA + id_contratto` → sottrarre i `RIMBORSO_CONTRATTO` del mese | edit (dipende da G7) |

**Invarianti (verdetti):**
- **Reconciliation resta LORDO** (verdetto 3): entrambe le leg sommano solo ENTRATA via `CASE WHEN tipo='ENTRATA'`; il rimborso USCITA contribuisce 0. **MAI** foldare il rimborso nella somma ENTRATA. La leg rimborso è **separata e parallela**.
- **`financial-trend`: preservare ENTRAMBe le decomposizioni** (verdetto 3, BLOCKER): `incassi_contratti` ha due scomposizioni lorde indipendenti — `nuovi+rinnovi` (`:1644-1647`) E `acconti+rate` (`:1649-1652`). Scelta: o nettare entrambe (testando anche nuovi/rinnovi), **oppure** tenere `incassi_contratti` lordo + `rimborsi_contratti` come **contra-linea separata** (raccomandato: nessun numero che "sparisce"). I sotto-tagli restano lordi.
- **Netto-vs-lordo per-vista (FDM §9.5):** card "Incassato" → netto; serie Andamento → netto; Saldo → già netto; "Venduto" → `prezzo_totale`; Reconciliation → lordo. Commento inline `netto`/`lordo`/`àncora` su ogni query toccata.

**Buildable now: ~90%.** Landabili SUBITO (no-op finché G7 non scrive RIMBORSO): P0 + consolidamento costanti + #2/#3/#4/#8 + P1 (#5). Dipendono da G7: leg reconciliation (#7), netting di `financial-trend` (#6).

### 5-bis (D4) — guardia: `data_chiusura` non nel futuro `[Bridge ratify 2026-06-24]`

Agganciato a G7.5 (non a un blocco proprio): condivide il terreno-cassa che G7.5 sta già allineando — forecast + protezione-cassa sono i posti dove un rimborso datato-futuro andrebbe a finire, quindi guardia e allineamento-viste atterrano coerenti.

- **Tesi:** un rimborso da terminazione è denaro che esce ora o è già uscito, mai un impegno futuro. `ContractTerminate.data_chiusura > date.today()` → 422.
- **Dove:** validator su `ContractTerminate` (schema) oppure check nel router `terminate_contract`. Posizionamento dal vivo: lo schema è preferibile se il messaggio può essere didattico come `PREZZO_OBBLIGATORIO_MSG`; il router se serve `date.today()` runtime.
- **Interazione da VERIFICARE, non assumere:** `test_terminate_burn_esclude_rimborso` data il rimborso nel **mese scorso** (passato) per esercitare l'esclusione-burn nella finestra `_prev_months`. La guardia blocca solo il **futuro** → quel test resta valido; confermarlo girando la suite, non a occhio (guardia-nuova × test-esistente = punto di drift mappa/territorio).
- **Confine — NON toccare il gemello G6.** `incassa_residuo` (`data_pagamento` libero) ha lo stesso tema sul lato ENTRATA, ma è fuori scope: irrigidire solo l'USCITA in questo giro, l'entrata resta com'è (nessuna regressione G6). Coerenza ENTRATA/USCITA da valutare in futuro, non ora.
- **AC:** `data_chiusura` futura → 422; odierna/passata → 200; suite pre-esistente invariata (incl. il test burn nel mese scorso).

### 5-ter (D2) — microcopy: avviso prenotate-escluse nella preview `[Bridge ratify 2026-06-24]`

Rifinitura frontend di G7.3 senza dipendenze, accodata a D4 per non aprire un commit isolato.

- **Tesi:** D1=A (base conguaglio = sedute **Completate**) rende il calcolo corretto ma non auto-evidente. `TerminateContractDialog` mostra "N / M erogate" ma non esplicita che le sedute solo *prenotate* sono escluse dal calcolo.
- **Decisione (founder, `[Bridge ratify 2026-06-24]`):** strada code-grounded precisa → **aggiungere `sedute_prenotate` a `ContractSettlementPreview`**. Scartata l'approssimazione `sedute_totali − sedute_erogate > 0` (includeva i crediti mai prenotati → avviso mostrato dove non si applica = il rumore che D2 nasce per evitare).
- **Natura del campo — NON una nuova SSoT.** `sedute_prenotate` è una **proiezione derivata** della fonte unica dei conteggi-sedute (la tabella `Event`), gemello esatto di `_count_sedute_erogate`: `count(Event)` con `stato == "Programmato"`, categoria PT, `deleted_at == None`, per quel contratto. NON una colonna sul contratto, NON un valore memorizzato — calcolato on-read come tutti gli altri conteggi (cfr. `crediti_usati` ORM sovrascritto a runtime dal `credit_breakdown` proprio perché driftava). La regola "i conteggi-sedute si derivano da `Event` ogni volta, mai si duplicano" regge.
- **Dove (code-grounded, verificare sul vivo):**
  - Helper backend: gemello di `_count_sedute_erogate` (`contracts.py`), filtro `Event.stato == "Programmato"`. Dal vivo: valutare un solo helper parametrico `_count_sedute_by_stato(session, contract_id, stato)` (DRY, copre erogate+prenotate) o due espliciti (leggibilità) — entrambi rispettano la SSoT-`Event`.
  - Schema: `sedute_prenotate: int` su `ContractSettlementPreview` (`financial.py`), accanto a `sedute_erogate`/`sedute_totali`.
  - Popolamento: in `_build_settlement_preview`/`_settlement_for`, stesso punto dove si conta `sedute_erogate`.
  - Type sync: `sedute_prenotate: number` su `ContractSettlementPreview` (`types/api.ts`).
- **Avviso frontend (ora preciso):** in `TerminateContractDialog.tsx`, mostrare la riga *"Le sedute prenotate ma non ancora svolte non riducono il rimborso"* **solo se `sedute_prenotate > 0`**. Vero per costruzione: appare quando esiste qualcosa di prenotato da escludere, mai sui crediti liberi.
- **Confine — il campo è SOLO display.** `sedute_prenotate` entra nella preview per trasparenza UI; **NON** entra nel calcolo del conguaglio (D1=A: la base resta `sedute_erogate`/Completate). Nessuna riga di `compute_settlement` lo legge.
- **Costo:** non più "zero backend" — un helper-query (pattern esistente) + un campo schema + un campo TS. Trascurabile, e l'avviso è ora veritiero. Resta dentro la finestra G7.5, stesso commit di D4.
- **AC:** preview di contratto con Programmati → `sedute_prenotate > 0` → avviso mostrato; preview senza Programmati (solo crediti liberi o tutto erogato) → `sedute_prenotate == 0` → avviso assente; `next build` verde; **nessun test di `compute_settlement` cambia** (campo display-only).

**Collocazione commit (D2+D4):** un **Commit dedicato dentro la finestra G7.5** (guardia D4 + riga D2), tesi falsificabile propria. NON un commit isolato fuori-sequenza prima di G7.4: la catena resta `G7.4 → G7.5 (+D2/D4) → G7.6 → G1`. G7.3a/b sono già committati e verdi → non rimetterci mano.

---

## 6. Prerequisiti trasversali (Blocco "Prereq P", PRIMA di G7)

> **✅ STATO (2026-06-21, implementato).** Round Prereq P limitato ai pezzi con **effetto reale e
> testabile subito**: **P0** (`api/services/cash_categories.py` — predicato cassa bidirezionale +
> consolidamento costanti `ACCONTO_CONTRATTO`/`PAGAMENTO_RATA`, literal residuo in `movements.py`
> consolidato), **P1** (fix Forecast `Contract.chiuso==False`), **P2** (`log_contract_lifecycle_transition`
> in `_audit.py` + wiring `pay_rate`/`unpay_rate`/`agenda._sync_contract_chiuso`). Test: `test_cash_categories`
> (6), `test_forecast_phantom` (2), `test_lifecycle_audit` (4). **Raffinamento di scope:** le esclusioni-query
> #2/#3/#4/#8 (sez. 5) e **P3 netto-per-vista** restano **codice inerte finché G7 non scrive `RIMBORSO`** →
> spostate **dentro il blocco G7**, dove sono esercitabili end-to-end con un rimborso reale (no dead code
> non testabile). La regola di boot di P3 (no query ORM su `Contract` prima di `sync_schema`) resta valida
> e va rispettata quando G7 aggiunge le colonne.

**P1 — Fix Forecast rate-fantasma** (`movements.py:1432-1441`): aggiungere `Contract.chiuso == False` alle entrate certe. **Hard prerequisite, NON differibile** (verdetto 3): protegge i CHIUSO legacy con rate PENDENTI future e belt-and-suspenders per i neo-terminati. Aging già safe (`rates.py:182-188`). Test: CHIUSO non-eliminato con rata PENDENTE futura → NON in proiezione; controprova open → contata.

**P2 — Audit della transizione → CHIUSO** (verdetti 1 e 3): oggi `pay_rate` auto-chiude ma logga solo `totale_versato`+`stato_pagamento` (`rates.py:598-601`); `_sync_contract_chiuso` flippa senza `log_audit`. Nuovo `log_contract_lifecycle_transition(...)` in `_audit.py` (NON committa; idempotente: solo se `old_chiuso != contract.chiuso`; firma pronta per G6/G7). Wiring: `pay_rate` (motivo `completamento`), `agenda._sync_contract_chiuso`. I campi `motivo_*` viaggiano nel JSON `changes` finché G7 non aggiunge le colonne (zero schema in P2). **Verdetto 1:** nessun test esistente asserisce su audit/chiuso → safe.

**P3 — Netto vs lordo per-vista** (read-side, cablato in difesa): vedi sez. 5. `netto_incassato`/`kpi_incassato` (`contracts.py:232`) usano `getattr(...,0)` → **numericamente inerti (==lordo)** finché G7 non produce rimborsi. **Verdetto 4 (load-bearing):** la vera protezione contro "no such column" sui DB deployati è l'ordine di boot (`main.py:237-241`: `create_db_and_tables` → `sync_schema` PRIMA di servire), NON il `getattr`. **Regola:** mai una query ORM su `Contract` nel lifespan prima di `sync_schema`.

**Buildable now: SÌ** per P1/P2/P3 read-side. Soft-dependency su G7 solo per la colonna `totale_rimborsato` (gestita da `getattr`).

---

## 7. Remediation runbook — 3 contratti muti (id 4/9/13, dato vivo)

**Deliverable a sé** (`docs/operations/RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md`), procedura **per-contratto, auditata, reversibile, MAI bulk**.

**Stato reale (crm.db Chiara):** `chiuso=1`, `data_scadenza` FUTURA, `totale_versato==prezzo_totale` (saldati, residuo 0), `crediti_usati=0` (tutte le sedute da erogare), `motivo/data/conguaglio` assenti. **Anomalia:** l'auto-close richiede `SALDATO AND crediti_usati>=crediti_totali`; con `crediti_usati=0` NON poteva scattare → chiusura **manuale o da import**.

**Decisione per-contratto (mai bulk):**
- **OPZIONE R (REOPEN, default)** se relazione viva / chiusura erronea: `PUT update_contract chiuso=False` (**nessuna dipendenza da schema G7, disponibile ORA**), zero cassa, log_audit, reversibile.
- **OPZIONE T (TERMINAZIONE retroattiva)** se rapporto finito: endpoint `terminate` (**solo DOPO G7**). Conguaglio: `sedute_erogate=0` → `conguaglio=−totale_versato` → **RIMBORSO PIENO dovuto**. **Attenzione:** se non c'è stato rimborso reale, correggere `sedute_erogate` o trattare come chiusura erronea → R.

**Step per contratto:** (1) **backup** `cp crm.db crm.db.bak`; (2) snapshot pre (`_compute_saldo`, `/reconciliation`, dump contratto, audit_log); (3) decisione R/T col trainer; (4) esecuzione **SOLO via endpoint**; (5) snapshot post (R: `totale_versato==Σ ENTRATA` invariato, lifecycle→ATTIVO; T: `Σ USCITA RIMBORSO==totale_rimborsato`, lifecycle→CHIUSO+motivo; zero rate PENDENTI; audit presenti); (6) reversibilità documentata. **Un contratto alla volta.** I legacy NULL si leggono come `COMPLETAMENTO implicito`.

---

## 8. Standard di qualità trasversali (per OGNI blocco)

1. **`contract_state` unica fonte** — mai ricalcolare attivo/scaduto/residuo/lifecycle inline (regola d'oro §10). Ogni nuovo punto di lettura del residuo delega a `contract_state.residuo()`.
2. **Bouncer/IDOR** — ogni endpoint `_bouncer_contract_owned` → 404, mai 403.
3. **Atomic single-commit** — build-then-single-commit; `log_audit`/`flush` nella stessa transazione; nessuna mutazione post-commit.
4. **Audit** — ogni CREATE/UPDATE/DELETE business loggato; transizione lifecycle via `log_contract_lifecycle_transition` (P2).
5. **Soft-delete** — `deleted_at`; SELECT filtra `deleted_at == None`; soft-delete movimenti via ORM.
6. **Batch anti-N+1** — `_crediti_usati_map`, multi-entity select.
7. **Migrazione** — Alembic (`down_revision='b2f1a9c7d4e3'`) + schema_sync ADD-column. Colonne **PLAIN**, mai FK cross-DB (#15). Indice `ix_{table}_{column}`. Documentare nullability drift.
8. **Quality gate** — `check-all.sh` (ruff+next build) + `pytest tests/` verde PRIMA di ogni commit. Rieseguire i 53 test `contract_state` dopo l'estensione di `residuo()`.
9. **Type sync** — `Optional[X]`→`X|null`; `toISOLocal` per le date; nessun calcolo finanziario nel frontend (consuma il netto dal backend).
10. **Commit per blocco rilasciabile** (`area: descrizione`).
11. **Verifica e2e** dove osservabile (crm.db reale): `/forecast`, `/financial-trend`, `/stats`, `/reconciliation` a fine Prereq P e G7.
12. **Learning capture** — predicato cassa bidirezionale; fonte-unica-dell'importo; anti-pattern `_sync_contract_chiuso` in terminazione.

---

## 9. Nodi risolti dai verdetti adversariali

| Concern (verdetto) | Verdetto | Change recepito |
|---|---|---|
| ESTENDI zero-backend-code | confermato | Blocco 3: PUT riusato, shortening guard non scatta in avanti |
| G6 riusa auto-close canonico | confermato | Blocco 4: `_sync_contract_chiuso`, no copia |
| Forecast phantom-income | confermato | P1 hard prerequisite |
| Audit gap transizione chiuso | confermato | P2 helper unico |
| Import-cycle G6/G7 | non esiste | modulo neutro `cash_categories.py` mantenuto |
| `getattr` su nuovi campi | load-bearing | 4.3: gate di code-review non-negoziabile |
| 2 G7 mini-plan duplicati | hygiene | unificati in sez. 4; conguaglio → `contract_settlement.py` |
| 3 nomi modulo categoria | hygiene | unico `cash_categories.py`, introdotto per PRIMO |
| ContractUpdate/RatePayment reuse | verificato | `financial.py:85-93` e `:157-183` → "zero schema" Blocco 3/G6 |
| Atomicità half-write | risk | 4.6 fonte-unica-importo (BLOCKER) |
| `_sync_contract_chiuso` riaprirebbe SOSPESO terminato | risk | 4.7 anti-pattern: G7 setta `chiuso` direttamente |
| Idempotenza terminate | overstated | 4.8 LOW (read-time, single-user) |
| un-terminate via endpoint protetto | risk | 4.4: soft-delete via ORM |
| Vincolo post-commit | risk | 4.9 |
| residuo inline = debito-fantasma UI | **BLOCKER** | 4.7: delega `contracts.py:127`+`financial.py:274` a `residuo()`, MANDATORY+test |
| Scope soft-delete rate | contraddittorio | 4.7: **tutte le non-saldate**, escluse SALDATA; NO riuso verbatim |
| Refund double-count (burn+contra-ricavo) | risk | sez. 5: single-treatment |
| financial-trend doppia decomposizione | **BLOCKER** | sez. 5: preservare nuovi/rinnovi E acconti/rate, o contra-linea separata |
| netto_incassato == valore reso | qualificato | vero solo nel ramo rimborso; ramo write-off → `netto=versato`+storno auditato |
| Invariante `quota_stornata>0 ⟹ chiuso` | fragile coupling | 4.7: documentare/asserire o migrare KPI inline |
| Snapshot sedute_erogate | no-silent-loss | 4.7: snapshot nell'audit |
| Reconciliation refund-leg | risk | sez. 5 #7: leg separata |
| Schema G7 PLAIN/Alembic head/boot-order | ok | 4.1 + std #7: `down_revision='b2f1a9c7d4e3'`, no Contract query pre-`sync_schema` |
| Nullability drift schema_sync | low | std #7: documentare |

---

## 10. Cosa serve da Giacomo prima di partire

1. **Policy di valorizzazione del conguaglio (tributarista)** — pro-sedute lineare? base `prezzo/crediti_totali`? recesso forfettario IT? + legittimità del forfeit. **NON blocca Blocco 3/4 né la struttura di G7**: `SettlementPolicy` pluggable + default `pro_sedute` PROVISIONAL. Necessaria prima di **abilitare in produzione i numeri** di rimborso.
2. **Naming categoria movimento** — conferma `RIMBORSO_CONTRATTO` (USCITA) in `cash_categories.py`.
3. **Conferma campo-storno** — `quota_stornata` accumulatore monotonico (gemello di `totale_rimborsato`), `residuo()` esteso a sottrarlo. Verdetti la confermano necessaria; serve OK al nome/semantica prima della migrazione.
4. **Decisione per i 3 contratti muti** — R (reopen, default) vs T (terminazione retroattiva) per ciascuno; richiede contesto trainer. R eseguibile ora, T dopo G7.

---

## 11. Differiti / roadmap (post-G1)

### G7.x-override (D1→D) — override umano dell'importo di rimborso `[Bridge ratify 2026-06-24]`

**DIFFERITO post-G1. NON schedulato nella catena G7 attuale** (`G7.4 → G7.5 → G7.6 → G1 → [G7.x-override]`).

- **Cos'è:** il software *propone* il conguaglio calcolato; l'umano può *sovrascrivere* l'importo finale. A (comportamento attuale, ratificato D1: il motore calcola e applica) è il caso particolare in cui l'umano accetta sempre la proposta.
- **Perché è il completamento di §0, non una feature in più:** §0/ADR-014 fondano il *downgrade epistemico* (il software propone, non afferma l'obbligo legale). Oggi A lo onora nel microcopy ma **applica** il numero calcolato. D risolve la tensione alla radice: se l'umano dissente sul numero, il software sta davvero solo proponendo.
- **A NON è debito tecnico verso D:** il motore (`compute_settlement`, due gambe, anteprima) è esattamente ciò che D riusa. D aggiunge solo `importo_rimborso_override: Optional[float]` + logica per preferirlo al calcolato. Il motore non si rifà.
- **⚠️ GUARDIA CRITICA (fissata ora, da rispettare quando si apre):** l'override apre una porta al **mass-assignment** oggi chiusa per design (`ContractTerminate` non accetta importi). D deve aprirla SOLO per l'importo rimborso, SOLO quando l'esito è RIMBORSO, **CON UN CAP**: l'override non può superare `netto_incassato` (non si rimborsa più di quanto incassato al netto). Senza cap, D è una via per scrivere USCITE arbitrarie sul ledger. È il bordo di D — conoscerlo prima di aprirlo.
- **Sequenza:** dopo G1 (cifratura). Coerente con "legale prima, eleganza dopo" — D è eleganza che rinforza il legale.

---

_File chiave: `api/services/{contract_state,contract_settlement(new),cash_categories(new)}.py`, `api/routers/{contracts,rates,agenda,movements,dashboard,_audit}.py`, `api/schemas/financial.py`, `api/models/contract.py`, `api/services/schema_sync.py`, `alembic/versions/` (nuova revision, down_revision `b2f1a9c7d4e3`), `frontend/src/hooks/{useContracts,useDashboard,useRates}.ts`, `frontend/src/app/(dashboard)/{contratti,rinnovi-incassi,cassa}/page.tsx`, `frontend/src/types/api.ts`, `docs/technical/IMPL_PLAN_FINANCIAL_REALIGN.md`, `docs/operations/RUNBOOK_REMEDIATION_CONTRATTI_MUTI.md` (new)._
