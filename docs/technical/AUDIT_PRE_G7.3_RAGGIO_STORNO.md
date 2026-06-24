# AUDIT PRE-G7.3 — Raggio d'esplosione del primo storno + test-scorciatoia + discrepanze

**Tipo:** audit code-grounded READ-ONLY (snapshot di verifica, non specifica).
**Data:** 2026-06-24 · **HEAD:** `d7bbcdc` (branch `FitManager_Studio`) · **Stato G7:** G7.0→G7.2 chiuso (586 passed / 0 xfailed).
**Metodo:** workflow multi-agente (12 agenti) — sweep code-grounded per classe → verifica adversariale (scettico che rilegge ogni sito + sweep di completezza per i siti mancati) → caccia discrepanze doc-vs-codice → sintesi. Ogni claim cita `file:riga` reale verificato, con marker `[letto-e-capito]` vs `[solo-grepped]`.
**Esito:** **ratificato da Bridge-Claude** (vedi §Ratificazione in fondo). Consolidato in `BUILD_LOG.md` 2026-06-24 "Audit consolidamento PRE-G7.3".
**SSoT di dominio:** `FINANCIAL_DOMAIN_MODEL.md` (Strada B §2/§9.5) · `TASSONOMIA_FINANZIARIA.md` §7.2 · `IMPL_PLAN_FINANCIAL_REALIGN.md` §4-§5 · `SPEC_G7.0_SCHEMA_TERMINAZIONE.md`.

> ⚠️ **Caveat coordinate.** Questo è uno snapshot al commit `d7bbcdc`. I `file:riga` qui dentro sono accurati a quella data ma **driftano di pochi-decine di righe per commit successivo** (lo dimostra l'audit stesso: i riferimenti in IMPL_PLAN/FDM/BUILD_LOG erano pervasivamente driftati). Le **decisioni e gli esiti** sono durevoli; le **coordinate** vanno riverificate sul codice al momento di G7.3. La memory cattura solo gli esiti, non le righe — di proposito.

---

## Domanda 1 — Raggio d'esplosione del primo storno

Siti reali nel raggio del primo `RIMBORSO_CONTRATTO` (USCITA con `id_contratto`) / primo `quota_stornata>0`. Ordinata A→B→C→D. I siti cross-lente compaiono una sola volta sotto la classe più saliente, con le altre classi tra parentesi. `[missed]` = trovato in verifica, non dal finder.

| file:riga | classe | cosa legge/calcola | oggi (zero) | sotto G7.3 (storno>0) | azione G7.3 | understanding |
|---|---|---|---|---|---|---|
| `contracts.py:242` | A (anche C) | `kpi_incassato = sum(totale_versato)`, incl. chiusi (235-238 senza filtro `chiuso`) | == lordo | **SOVRASTIMA di Σ rimborsato; card "Incassato" mente** | **DEVE-USARE-netto**: `sum(netto_incassato(c))`. Unico vero sovrastimante aggregato BE | letto-e-capito |
| `contratti/page.tsx:129` | A | `case 'incassato': return kpi_incassato` — consumer puro card "Incassato" | == lordo (eredita) | sovrastima ereditata, nessuna aritmetica FE | NESSUNA (auto-corregge col fix BE) | letto-e-capito `[missed]` |
| `contracts.py:128,131` | A | `versato`→`percentuale_versata`; `importo_da_rateizzare` usa residuo SSoT (130/133) | == %lordo | %lordo display per-contratto | NESSUNA (label "versato"=lordo) | letto-e-capito |
| `clients.py:367,418` | A (anche B) | `sum(totale_versato)` WHERE `chiuso==False` → ClientEnrichedResponse | lordo aperti | invariante-safe: terminato⟹chiuso→escluso | NESSUNA (dipende da terminato⟹chiuso) | letto-e-capito |
| `clients.py:698,805` | A (anche B) | gemello list_clients Q3 `sum(totale_versato)` group_by, `chiuso==False` (705) | lordo aperti | invariante-safe come :367 | NESSUNA | letto-e-capito |
| `dashboard.py:127-138` | D (anche A/C) | ledger-alert/divergent_count: `HAVING ROUND(versato − Σ ENTRATA)>0.01`, JOIN filtra `tipo='ENTRATA'` (132) | == lordo == Σ ENTRATA, count 0 | **INVARIANTE REGGE**: refund=USCITA fuori dal JOIN; cieco al lato rimborso | NESSUNA sull'àncora; **ADDITIVO** opz. leg rimborso. Usare netto qui ROMPEREBBE | letto-e-capito |
| `dashboard.py:177-208` | D (anche A/C) | `get_reconciliation`: `ledger=Σ(CASE tipo='ENTRATA')` (179); `delta=versato−ledger` (191) | delta≈0 aligned | **INVARIANTE REGGE** (resta aligned); cieco al rimborso | NESSUNA sull'àncora; **ADDITIVO** nuova leg `totale_rimborsato == Σ USCITA RIMBORSO` | letto-e-capito |
| `dashboard.py:446` (+474-475) | B (anche A) | prefiltro `prezzo>versato` inline SENZA −quota, `chiuso==False` (445); Step3 ricalcola via `evaluate_contract→residuo()` (474) | prezzo>versato ≡ residuo>0 | safe: chiuso esclude terminati + Step3 SSoT | NESSUNA (where-clause grezza confermata safe) | letto-e-capito |
| `dashboard.py:504` | A | `totale_versato` item da-pianificare; gating `is_rate_planificabile` ATTIVO (475) | == lordo | ATTIVO → mai rimborsato → gross==net | NESSUNA | letto-e-capito |
| `financial.py:148-153` | A | `netto_incassato` computed_field → `netto_incassato(self)` | == versato | diventa load-bearing (`versato−rimborsato`), già in JSON | NESSUNA al campo; **gap = NESSUN consumer FE lo legge** | letto-e-capito `[missed]` |
| `ContractFinancialHero.tsx:40` | A | KpiCard "Totale Versato" | == lordo | lordo display; netto disponibile non letto | NESSUNA obbligatoria (opz. riga "Netto incassato") | letto-e-capito |
| `ContractsTable.tsx:164` | A | progress bar `versato/prezzo` | == lordo | %lordo per-riga | NESSUNA | letto-e-capito |
| `ContrattiTab.tsx:54` | A | `versato/prezzo` per contratto (include chiusi, badge "Chiuso") | == lordo | lordo terminato visibile (label "versato") | NESSUNA obbligatoria | letto-e-capito |
| `PaymentPlanTab.tsx:227` | A | riga "Totale versato" breakdown | == lordo | lordo display; daRateizzare usa residuo SSoT (228) | NESSUNA | letto-e-capito |
| `ClientsTable.tsx:142` | A | progress bar Finanze (sorgente `chiuso==False`) | lordo aperti | invariante-safe (eredita filtro) | NESSUNA | letto-e-capito |
| `CommandPalette.tsx:171` | A | stat "Versato" ClientPreview | lordo aperti | invariante-safe | NESSUNA | letto-e-capito |
| `DeleteContractDialog.tsx:63,162` | A | `hasPagamenti`; testo "Mantieni i {versato} già incassati"; importoNonRiscosso usa `residuo` SSoT (61) | == lordo | edge: "già incassati"=lordo su un terminato/rimborsato | NESSUNA obbligatoria (edge minore) | letto-e-capito |
| `rates.py:95-96` (`_cap_rateizzabile`) | A/B | `acconto=versato−Σsaldato`; `cap=prezzo−acconto`. Rate-capacity, NON residuo | cap su lordo | NON tocca residuo; sovrastimerebbe lo spazio se quota>0 | NESSUNA. **FLAG difensivo**: update_rate (350→394) chiama SENZA chiuso-guard | letto-e-capito `[missed]` |
| `contract_state.py:59-65` (`residuo()`) | B | `max(prezzo−versato−quota_stornata,0)` | quota=0 → byte-identico pre-G7 | **CAMBIA: residuo cala di quota** (chiude il debito-fantasma) | NESSUNA (già esteso G7.1) | letto-e-capito |
| `contracts.py:130,133,134` | B | dettaglio: `residuo=cstate.residuo`; `importo_da_rateizzare`; `disallineamento` | prezzo−versato | cala di quota automaticamente | NESSUNA (delega completa) | letto-e-capito |
| `contracts.py:296,324` | B | `kpi_residuo=Σ cstate.residuo(c) if not c.chiuso`; resto da_pianificare | Σ(prezzo−versato) aperti | cala; ma quota>0⟹chiuso → esclusi (doppia rete) | NESSUNA | letto-e-capito |
| `contracts.py:409` | B | `residuo=state.residuo` (da `evaluate_contract`) → ContractListResponse | prezzo−versato | cala; fonte del campo letto dal FE | NESSUNA | letto-e-capito |
| `contracts.py:1023,1030,1038` (incassa_residuo) | B | chiuso-guard + `cstate.residuo` + cap 422; stato_pagamento LORDO (1048) | prezzo−versato | cap cala; guard blocca i terminati | NESSUNA | letto-e-capito |
| `rates.py:526` (pay_rate cap) | B | `residuo_contratto=cstate.residuo`, cap 422 | prezzo−versato | cap cala di quota | NESSUNA (drift doc: era :525) | letto-e-capito |
| `rates.py:744,746` (generate_plan) | B | `residuo_atteso=cstate.residuo`, validazione 422; chiuso-guard (736) | prezzo−versato | cala+guard | NESSUNA (drift doc: era :734) | letto-e-capito |
| `dashboard.py:497,677,719` | B | residuo item to-plan/recover/suspended = `cstate.residuo` | prezzo−versato | ogni riga cala di quota | NESSUNA | letto-e-capito |
| `workspace_engine.py:1151,1338,1437,1487` | B | cockpit cases `cstate.residuo`; `total_due_amount` usa prezzo (lordo, asse venduto) | prezzo−versato | cala di quota; due assi distinti corretti | NESSUNA | letto-e-capito |
| `workspace_engine.py:1035-1036` | B | payment_overdue: `Σ(rate.previsto−saldato)` rate scadute (rate-based) | somma residui rate scadute | invariante: quota abbassa il residuo contratto, non le rate; rate non-saldate soft-deleted | NESSUNA | letto-e-capito `[missed]` |
| `contract_settlement.py:81-121` | B/D | conguaglio puro: `importo_rimborso=round(abs(conguaglio))` (106), `quota_da_stornare=residuo_corrente` (119); riceve residuo dal caller | funzione PURA, zero DB, mai chiamata | **G7.3 la accende** → produce quota>0 e importo rimborso | **VINCOLO fonte-unica-importo**: G7.3 passi `residuo_corrente=cstate.residuo()` PRE-storno; un solo `importo_rimborso` per movement E `totale_rimborsato +=` | letto-e-capito |
| frontend residuo readers (`Hero:41`, `Table:63`, `Delete:61`, rinnovi `342/421/461/516`) | B | leggono `contract.residuo`/`item.residuo` dal SSoT, zero ricalcolo | mostra valore backend | riflette il calo senza modifiche FE | NESSUNA (convergenza FE completa) | letto-e-capito |
| `ContractsTable.tsx:162-165` + `ClientsTable.tsx:141-143` | B | progress bar `ratio=versato/prezzo` | ratio lordo | display lordo (non riflette quota) | NESSUNA funzionale (cosmetica) | letto-e-capito `[missed]` |
| `clienti/[id]/page.tsx:105` | B | orphan: `rate_totali===0 && prezzo>0` (proxy prezzo, non residuo) | flag su qualsiasi aperto senza rate | invariante per G7.3 (terminati=chiuso fuori da activeContracts); imprecisione PRE-esistente | NESSUNA per G7.3 (debito: usare `residuo>0`) | letto-e-capito `[missed]` |
| `movements.py:67-119` (`_signed_importo`/`_compute_saldo`) | C | saldo signed `+ENTRATA / −USCITA` | saldo reale, no rimborso | **INVARIANTE**: refund USCITA → saldo cala (giusto, denaro uscito) | NESSUNA (pietra angolare) | letto-e-capito |
| `movements.py:373-440` (`get_balance`) | C | saldo invariante (418); `totale_uscite_storico=SUM(USCITA)` (397-402) | solo spese | saldo OK; `totale_uscite_storico` CRESCE del rimborso (solo display, NON alimenta protezione) | DIPENDE-DALL'USO (display-only, no edit obbligatorio) | letto-e-capito |
| `movements.py:291-311` (`_compute_variable_burn_rate`) | C | media uscite variabili `USCITA AND id_spesa_ricorrente IS NULL` | solo spese variabili | **CAMBIA: refund matcha → GONFIA il burn** | **EDIT (G7.5 — ma vedi eccezione §Ratificazione)**: escludere RIMBORSO (`cash_categories.is_contract_outflow`) | letto-e-capito |
| `movements.py:314-370` (`_build_cash_protection`) | C | `costo_operativo=fisse+burn` → soglia/copertura/stato | corretto | indiretto: eredita burn gonfiato → **stato può degradare a CRITICO falso** | **NESSUN fix proprio**: il burn è il SUO UNICO ingresso uscite-variabili (verificato `:314-370`: legge solo `RecurringExpense` + `_compute_variable_burn_rate`; `saldo_attuale` già corretto) → **risanata in G7.3 a monte** se la burn-exclusion entra in G7.3; in G7.5 solo VERIFICARE che non legga il rimborso per altra via `[Bridge ratify 2026-06-24]` | letto-e-capito `[missed]` |
| `movements.py:1105-1208` (`get_movement_stats`) | C | `uscite_variabili` (1149-1152), `margine_netto`, chart per-giorno | margine corretto | CAMBIA: refund in uscite_var → margine scende; chart in uscite | **EDIT (G7.5)**: escludi da uscite, sottrai da entrate, chart come riduzione (specchio STORNO_SPESA_FISSA) | letto-e-capito |
| `movements.py:1487-1498` (past_var_totals) | C | proiezione uscite var 90gg | solo spese | CAMBIA: refund gonfia proiezione | **EDIT (G7.5)**: escludere RIMBORSO | letto-e-capito |
| `movements.py:1524-1535` (past_total_uscite, burn KPI) | C | `burn_rate_mensile` su SUM(USCITA) totale | tutte le uscite | CAMBIA: refund gonfia burn KPI | **EDIT (G7.5)** — seconda query distinta nello stesso endpoint | letto-e-capito |
| `movements.py:1611-1656` (`get_financial_trend`) | C | `incassi_contratti`, filtro `tipo=='ENTRATA'` (1614) | Σ ENTRATE | CAMBIA per UNDER-SUBTRACT: refund USCITA invisibile → sovrastima netto | **EDIT (G7.5)**: leg USCITA additiva + campo `rimborsi_contratti` | letto-e-capito |
| `movements.py:1661-1675` (buckets_venduto) | C | `Σ prezzo_totale` per data_vendita (competenza) | prezzi pieni | **INVARIANTE**: prezzo lordo immutabile; refund≠prezzo | NESSUNA (vista competenza) | letto-e-capito |
| `movements.py:900-906` (flow_hint) | C | hardcode rate/contract→ENTRATA | contract sempre incasso | mislabel: terminazione (contract-entity) forzata ENTRATA | **EDIT (G7.5)**: flow_hint segno-aware | letto-e-capito |
| `movements.py:833-848` (flow_filter) | C | ramo `flow_filter` hardcoda `entity_type=='contract'` in ENTRATA (847) | contract in ramo ENTRATA | **gemello query-level dell'hint**: terminazione filtrata "USCITA" invisibile | **EDIT (G7.5)** in coppia col flow_hint | letto-e-capito `[missed]` |
| `movements.py:1056-1063` (list_movements saldo) | C | running balance signed periodo | corretto | **INVARIANTE**: refund sottratto giusto | NESSUNA | letto-e-capito `[missed]` |
| `movements.py:1434-1450` (get_forecast entrate-certe) | C | rate PENDENTE/PARZIALE `chiuso==False`, residuo da rate | somma rate future | **INVARIANTE-GIÀ-SAFE**: aggrega RATE non CashMovement; chiuso-guard è fix P1 phantom-income | NESSUNA — **ECCEDENZA nello scope-rimborso** (IMPL_PLAN §5 #5) | letto-e-capito |
| `dashboard.py:84-94` (monthly_revenue) | C | `SUM(importo) WHERE tipo='ENTRATA' AND id_contratto!=None` mese | incassi mese | CAMBIA per UNDER-SUBTRACT: refund USCITA non sottratto → sovrastima | **EDIT (G7.5)**: sottrarre RIMBORSO del mese | letto-e-capito |
| `test_incassa_residuo.py:117-131` | D | `assert sum(entrate)==700==totale_versato` — UNICA rete eseguibile dell'invariante | passa (no refund) | regge sotto G7.3 (incassa-residuo non scrive USCITA); canarino dell'àncora | **aggiungere test gemello terminate** (`Σ ENTRATA==versato` post-rimborso + `netto==Σ ENTRATA−Σ RIMBORSO`) | letto-e-capito |
| `contracts.py:695-843` (delete_contract cascade) | D | soft-delete TUTTE le rate incl. SALDATA + TUTTI i CashMovement (813-818) + contratto (831) | safe: il contratto esce dal set via `deleted_at` (filtro 133/183) | **terminate NON soft-elimina il contratto → se riusasse il cascade, Σ ENTRATA scende ma versato resta lordo → DIVERGENZA PERMANENTE** | **NON riusare verbatim**: terminate soft-delete SOLO rate non-saldate, MAI SALDATA né i loro CashMovement ENTRATA | letto-e-capito |

**Sintesi Domanda 1.** Le "9 query del log" non sono un inventario verificato: sul codice sono **~8 comportamenti-query che CAMBIANO** sotto un `RIMBORSO_CONTRATTO` (burn variabile, movement-stats, le 2 query di get_forecast, financial-trend, monthly_revenue, flow_hint **+ flow_filter gemello**, `get_balance.totale_uscite` dipende-dall'uso) **+ ~8 correttamente invarianti**. **In eccesso**: IMPL_PLAN §5 #5 `get_forecast entrate-certe` è una guardia phantom-income rate-based (refund strutturalmente invisibile) → da declassare. **Mancanti da entrambe le liste**: `contracts.py:242 kpi_incassato` (FDM impone il netto), `_build_cash_protection` (output protezione a valle del burn), `flow_filter` (gemello dell'hint). Le due liste divergono per uno scambio di slot → **TASSONOMIA §7.2 è più fedele** al codice. — **Convergenza residuo Sez. A (Classe B): COMPLETA.** Ogni calcolo di "denaro ancora dovuto" delega a `contract_state.residuo()` (≥13 call-site backend + letture FE); l'UNICA where-clause ORM `prezzo>versato` (dashboard.py:446) è safe (filtro chiuso + Step3 SSoT). — **Invariante D (`totale_versato == Σ ENTRATA`): REGGE** sotto G7.3 su ogni sito (refund=USCITA escluso dalle somme ENTRATA, `totale_versato` lordo immutabile). G7.3 è **ADDITIVO** (nuova leg `totale_rimborsato == Σ USCITA RIMBORSO`). L'UNICO modo di romperla è soft-deletare una rata SALDATA + il suo CashMovement ENTRATA → vietato in terminate.

---

## Domanda 2 — Test-scorciatoia PUT chiuso=True da migrare

`chiuso` sparisce da `ContractUpdate` (`financial.py:109`, `extra:"forbid"`) → i 16 payload `PUT {"chiuso": True}` daranno 422.

| file:riga | cosa testa | categoria | azione G7.3 | understanding |
|---|---|---|---|---|
| `test_contract_integrity.py:53` | close→POST /rates→400 "chiuso" (guard create_rate) | scorciatoia | migra-meccanica | letto-e-capito |
| `test_contract_integrity.py:68` | close→generate-plan→400 | scorciatoia | migra-meccanica | letto-e-capito |
| `test_contract_integrity.py:84` | close→POST /events→400 | scorciatoia | migra-meccanica | letto-e-capito |
| `test_contract_integrity.py:105` | `test_close_contract_via_update`: PUT chiuso=True→200+GET chiuso=True. **Unico test in cui il canale PUT È il soggetto** | **presidio-transizione** | **ripensa** (riscrivere su terminate, NON cancellare) | letto-e-capito |
| `test_contract_integrity.py:116` | close→DELETE /clients→204 (chiuso non blocca delete cliente) | scorciatoia | migra-meccanica | letto-e-capito |
| `test_contract_integrity.py:422` | close→crediti_residui includono il chiuso | scorciatoia | migra-meccanica | letto-e-capito |
| `test_contract_integrity.py:467` | `test_kpi_fatturato_includes_closed` (regressione INC-2026-06-08) | scorciatoia | **migrabile a QUALSIASI motivo — invariante sotto storno** (legge `prezzo_totale`, non versato/rimborsato — verificato `contracts.py:241`); è il PIÙ libero dei 16 test, NON vincolato a money-neutral `[Bridge ratify 2026-06-24]` | letto-e-capito |
| `test_aging_report.py:91` | rata scaduta+close→aging rate_scadute==0 | scorciatoia | migra-meccanica | letto-e-capito |
| `test_clients_to_recover.py:94` | close più recente→rappresentante=CHIUSO più recente | scorciatoia | migra-meccanica | letto-e-capito |
| `test_clients_to_recover.py:103` | close contratto "muto" scadenza FUTURA→giorni_ritardo clampato 0 | scorciatoia | migra-meccanica (terminate deve accettare scadenza futura) | letto-e-capito |
| `test_contracts_to_plan.py:89` | close→contracts-to-plan total==0 | scorciatoia | migra-meccanica | letto-e-capito |
| `test_contracts_to_plan.py:146` | close→KPI cruscotto (di stato) tutti 0 | scorciatoia | migra-meccanica | letto-e-capito |
| `test_forecast_phantom.py:45` | close con rata pendente→forecast toglie entrata-fantasma | scorciatoia | migra-meccanica | letto-e-capito |
| `test_incassa_residuo.py:206` | close→POST /incassa-residuo→400 "chiuso" (guard G6) | scorciatoia | migra-meccanica | letto-e-capito |
| `test_lifecycle_audit.py:164` | `test_manual_close_not_reopened_by_agenda_edit` (AC-7.2): close MANUALE via PUT (motivo=NULL)+edit-agenda→NON riapre. **Unico test del ramo NULL della reopen-allowlist** | **presidio-transizione (PRESIDIO TRAVESTITO)** | **ripensa** (vedi sotto) | letto-e-capito |
| `test_suspended_contracts.py:90` | close scaduto+crediti→suspended total==0 | scorciatoia | migra-meccanica | letto-e-capito |
| `test_lifecycle_audit.py:200` | `test_terminazione_non_si_riapre_da_agenda` (AC-7.2-4): chiuso/motivo=TERMINAZIONE_RIMBORSO/quota=200 via **ORM session**, edit-agenda non riapre | forward-guard (NON nei 16) | **non-toccare** | letto-e-capito |
| `test_lifecycle_audit.py:224` | `test_terminazione_non_si_riapre_da_unpay` (gemello payment-driven): via **ORM session**, unpay non riapre | forward-guard (NON nei 16) | **non-toccare** | letto-e-capito |

**Conteggio reale vs "~15": sono 16** payload `PUT {"chiuso": True}` in 8 file (la memory sottostimava di 1, verosimilmente un sito multi-riga di `test_contract_integrity.py`). I 2 forward-guard ORM (lifecycle_audit:200/:224) e i costruttori fake (SimpleNamespace, fixture) NON usano il canale PUT → fuori dai 16, immuni alla rimozione di `chiuso` da `ContractUpdate`.

**Presidio travestito da scorciatoia (il finding che evita di cancellare un presidio): `test_lifecycle_audit.py:164`.** Sembra una banale chiusura manuale, ma è l'**UNICO** test del ramo NULL della reopen-allowlist G7.2 (il NULL è il contro-esempio che una denylist mancherebbe). Il suo carico-portante è esattamente che `update_contract` lascia `motivo_chiusura=NULL`. Una migrazione **meccanica** a `terminate(CONSUNZIONE)` lo lascerebbe VERDE (`CONSUNZIONE != COMPLETAMENTO` → non riapre) ma **smetterebbe di esercitare il ramo NULL** — presidio distrutto in silenzio. Peggio: se ogni chiusura post-G7.3 passa da terminate (che setta sempre un motivo), lo stato `chiuso=True ∧ motivo=NULL` diventa non costruibile via API → il ramo NULL della allowlist diventa difensivo-irraggiungibile (delta FDM §9.5.6). Va ricondotto a simulazione ORM (come i forward-guard) o ritirato con nota esplicita — **decisione di modello, non meccanica**. **Correzione alla premessa della domanda**: `test_manual_close_*` NON è un forward-guard "non-toccare"; ne esiste uno solo ed è questo presidio-travestito.

---

## Domanda 3 — Discrepanze codice-vs-log

| topic | doc dichiara | codice mostra (file:riga) | severity |
|---|---|---|---|
| `kpi_incassato` assente da entrambe le liste, mentre FDM ne impone il netto | FDM §9.5: card "Incassato"→netto. IMPL_PLAN §5/TASSONOMIA §7.2 elencano solo movements.py+dashboard.py, mai contracts.py | `contracts.py:242` somma lordo su tutti incl. chiusi→card "Incassato"; sotto G7.3 sovrastima. Rimpiazzo `netto_incassato` pronto e inutilizzato (contract_state.py:68 + financial.py:148-153), non inventariato | **high** |
| Le due liste "9 query" divergono e nessuna combacia col codice | IMPL_PLAN §5 #5=get_forecast entrate-certe (movements.py:1432-1441); TASSONOMIA non la elenca, usa #8=get_balance(totale_uscite) (396-415) | (a) `movements.py:1434-1450` aggrega RATE con chiuso==False, mai CashMovement→refund invisibile→**in eccesso**. (b) `movements.py:397-402` totale_uscite_storico CRESCE col refund; IMPL_PLAN la maschera no-edit in #1→**TASSONOMIA più fedele** | **high** |
| `flow_filter` (gemello del flow_hint) mancante da entrambe | IMPL_PLAN §5 #8 / TASSONOMIA §7.2 #7 citano solo il flow_hint (movements.py:899-905) | `movements.py:847` hardcoda `entity_type=='contract'` in ENTRATA: stesso bug; fixando solo l'hint, il filtro lo contraddice | medium |
| Claim "KPI inline residuo che NON sottraggono quota_stornata" è **STALE** | IMPL_PLAN §4.7 + FDM §9.5.6: i KPI inline (contracts.py:285-286,314) "non sottraggono quota, migrare o asserire" | Migrazione **già avvenuta** (6d5ba31): `contracts.py:296` `Σ residuo(c)`, `:324` delega. Nessun residuo inline; righe citate driftate. Il BLOCKER §4.7 indirizza lavoro già risolto | medium |
| Conteggio query incoerente fra i doc | api/CLAUDE.md: "8 query"; IMPL_PLAN/TASSONOMIA/SPEC_G7.0/BUILD_LOG: "9 query" | ~8 cambiano + ~8 invarianti; nessuna lista è inventario completo; governance oscilla 8↔9 | medium |
| Conteggio "~15 test" | BUILD_LOG: "~15 test" | grep payload `PUT {"chiuso":True}` = **16 siti** (7 in test_contract_integrity.py + 9 single-line) | low |
| Marcatura COMPLETAMENTO: conteggio giusto (2 call-site) ma righe driftate | BUILD_LOG: 2 call-site (pay_rate rates.py:570 + ramo _sync agenda.py:331); incassa_residuo eredita | **CONTEGGIO esatto** (2 write + ereditarietà via contracts.py:1074), ma righe driftate: write motivo a `rates.py:571` e `agenda.py:340` | low |

**Conferme verificate (non discrepanze):** marcatura COMPLETAMENTO = esattamente 2 write-site + ereditarietà via `_sync`; 4 colonne terminazione PLAIN, zero FK, solo INDEX su `motivo_chiusura` (contract.py:67-72, coerente AC-7.0-1); `ContractResponse` espone i 5 campi + `netto_incassato` computed (financial.py:139-153); `dashboard.py:446` UNICA where-clause prezzo-vs-versato e converge (Step3 SSoT). **Risolve un NON-VERIFICATO della Domanda 2**: `kpi_fatturato=sum(prezzo_totale)` (contracts.py:241) → né `quota_stornata` né `totale_rimborsato` lo cambiano → `test_kpi_fatturato_includes_closed_contracts` sopravvive anche a un terminate CON denaro. **Nota trasversale**: i riferimenti di riga in IMPL_PLAN/FDM/BUILD_LOG sono **pervasivamente driftati** di pochi-decine di righe per commit successivi.

---

## INPUT CHE QUESTO AUDIT NON PUÒ DARE

Separazione netta tra **fatto-di-codice** (mappato sopra, deterministico) e **decisione esterna** (tributarista/founder) che blocca G7.3.

**I 3 input noti che bloccano G7.3:**
1. **Policy conguaglio — `SettlementPolicy.mode`** (tributarista). `compute_settlement` (contract_settlement.py:81-121) è pura e mai cablata; `pro_sedute` è PROVISIONAL. Senza la policy non è determinato *quanto* vale lo storno/rimborso → l'intera valorizzazione di `quota_stornata`/`totale_rimborsato` è sospesa.
2. **Conferma enum `motivo_chiusura`** (founder/dominio). I 4 valori ESISTONO già e sono asseriti nei test (test_contract_settlement.py:97-99, test_termination_schema.py:14). Ciò che resta NON è l'esistenza ma la **semantica**: quale motivo assegna l'endpoint terminate per una **chiusura senza movimento di denaro** (CONSUNZIONE è il candidato naturale).
3. **R/T per i 3 contratti muti id 4/9/13** (founder sui dati reali). Definisce il comportamento atteso di terminate su contratti con scadenza futura / senza rate.

**Decisioni esterne aggiuntive emerse dall'audit:**
4. **Target di migrazione delle scorciatoie + del presidio-NULL** (dipende da #2). Senza un motivo confermato, le scorciatoie non hanno un bersaglio deterministico. **`test_kpi_fatturato` (`:467`) ESCE dalla lista money-neutral** `[Bridge ratify 2026-06-24]`: è invariante sotto qualsiasi storno (legge `prezzo_totale`, non versato/rimborsato — verificato `contracts.py:241`) → migrabile a qualsiasi motivo. Restano ~13 scorciatoie + il presidio-NULL legate alla decisione sul motivo (#2).
5. **Destino del ramo NULL della reopen-allowlist** (decisione di modello, delta FDM §9.5.6): se ogni chiusura post-G7.3 passa da terminate, lo stato `chiuso=True ∧ motivo=NULL` diventa non costruibile via API → il presidio `test_lifecycle_audit.py:164` va ricondotto a ORM o ritirato con nota.
6. **`terminate` deve accettare chiusura con scadenza futura** (da confermare con #3), pena la non-migrabilità di `test_clients_to_recover.py:103`.

Tutto il resto (raggio Classi A-D, convergenza residuo, invariante riconciliazione, inventario reale delle query, conteggio test) è **fatto-di-codice verificato** ed eseguibile non appena #1 e #2 sono fissate.

---

## Ratificazione (Bridge-Claude, 2026-06-24)

Bridge ha ratificato l'audit e ne ha derivato le correzioni al pacchetto G7.3 che avrebbe scritto:

- **Confine G7.3 vs G7.5 confermato.** G7.3 = endpoint a 2 gambe + accendere `compute_settlement` (fonte-unica-importo: `residuo()` PRE-storno, un solo importo per il movement E per il `+=`) + scrivere `quota_stornata`/`totale_rimborsato` + USCITA RIMBORSO + soft-delete selettivo + `kpi_incassato`→netto + decisione presidio-NULL. **G7.5** = allineamento delle viste-cassa che riflettono il rimborso (burn, movement-stats, le 2 forecast, financial-trend, monthly_revenue, **coppia flow_hint+flow_filter mai uno solo**, `_build_cash_protection` — già risanata in G7.3 via burn, in G7.5 solo VERIFICA, nessun fix proprio `[Bridge ratify 2026-06-24]`).
- **Esclusione-burn → DENTRO G7.3 (decisione finale Bridge, alternativa scartata).** La catena `_compute_variable_burn_rate` → `_build_cash_protection` è l'**unica** query con profilo-**ALLARME** (falso CRITICO sulla protezione cassa), non cosmetico/conservativo: un rimborso una-tantum entra nella media uscite-variabili → gonfia `costo_operativo` → flippa lo stato a CRITICO falso nell'istante del primo storno. L'esclusione-burn (`NOT is_contract_outflow` sul filtro USCITA-variabili, predicato P0 già esistente) entra in **G7.3**, non G7.5. L'alternativa "lasciarla in G7.5 + garantire adiacenza" è **scartata**: lascerebbe una finestra in cui un trainer reale termina e vede un falso CRITICO — categoria diversa da un numero impreciso. **Criterio di confine adottato:** la linea G7.3/G7.5 non è "endpoint vs viste" in astratto — è *ciò che il primo storno reale attiva e quindi rende testabile ORA* (la burn-exclusion è esercitabile end-to-end nello stesso test del terminate, che crea il primo rimborso vero → niente dead code) *vs ciò che richiede un rimborso simulato per essere esercitato* (le altre ~7 esclusioni → G7.5). **Conseguenza a valle:** spostando il burn in G7.3, `_build_cash_protection` è **risanata in G7.3 gratis** (dipendenza a valle); in G7.5 resta solo verificare che non legga il rimborso per un'altra via. Le altre viste G7.5 driftano cosmetico (label), conservativo (margine sottostimato) od ottimistico-display (revenue/trend sovrastimati): nessun allarme.
- **Riformulazione BLOCKER §4.7 — B-2 ha due metà (correzione load-bearing).** B-1 (residuo→SSoT) incassato in Sez. A. **B-2 metà difensiva** (guardia allowlist su `_sync_contract_chiuso`+`unpay_rate` contro la riapertura-automatica di un terminato) = incassata in **G7.2**, 6 test. **B-2 metà attiva** — «terminate setta `chiuso`/`motivo`/`data` **direttamente** e **non chiama mai** `_sync_contract_chiuso`, che su un SOSPESO terminato (saldato, crediti residui → `should_be_chiuso=False`) resetterebbe `chiuso=False` nello stesso commit, auto-annullando la terminazione» = **viva, dentro l'endpoint G7.3**, con **test dedicato** (termina un SOSPESO saldato-con-crediti-residui → verifica che resti `chiuso` dopo il commit, cioè che `_sync` non l'abbia toccato). NB: far dipendere la sicurezza dall'ordine (scrivere il motivo *prima* di chiamare `_sync` così la guardia lo ferma) è fragile → la regola pulita è che terminate non imbocchi affatto quella via. Vivi dentro G7.3: **B-2-attiva** + **B-3** (cascade non-verbatim). **B-4** (financial-trend doppia decomposizione) vivo ma vincolo di **G7.5**. G7.3 NON deve "far rispettare" B-1.
- **Rinumerazione "8 cambiano + 8 invarianti" = DA RATIFICARE in G7.5, non fatto** (tocca la governance: api/CLAUDE.md=8 vs altri=9; TASSONOMIA §7.2 più fedele). In G7.5: un solo numero verificato + liste vecchie marcate superseded.

### Perimetro G7.3 (come Bridge lo scriverà alla `SettlementPolicy`)

1. **Endpoint `terminate` a 2 gambe** (rimborso / write-off) → accende `compute_settlement` (puro, G7.1) e traduce il `Settlement` in scritture.
2. **Fonte-unica-importo:** `residuo_corrente = contract_state.residuo()` PRE-storno; un solo importo per il `CashMovement` USCITA **E** per `quota_stornata`/`totale_rimborsato +=`.
3. **Soft-delete selettivo (B-3):** solo rate non-saldate, mai SALDATA né i loro `CashMovement` (preserva `Σ ENTRATA == totale_versato`).
4. **`kpi_incassato` → `netto_incassato()`** (HIGH, unico sovrastimante aggregato, si rompe nell'istante del primo storno).
5. **Esclusione-burn** (`NOT is_contract_outflow` sul filtro USCITA-variabili) — unica esclusione-cassa in G7.3 (profilo-allarme + testabile dal rimborso vero; risana anche `_build_cash_protection` a valle).
6. **Regola-endpoint B-2-attiva:** terminate setta `chiuso`/`motivo`/`data_chiusura` diretto, mai `_sync_contract_chiuso`; test sul SOSPESO saldato-con-crediti.
7. **Presidio-NULL** (`test_lifecycle_audit.py:164`): decisione di modello (ricondurre a ORM o ritirare con nota), **non** migrazione meccanica — legata alla decisione esterna #5.

**Fuori da G7.3, in G7.5:** le altre ~7 esclusioni-cassa, coppia `flow_hint`+`flow_filter` (mai uno solo), **B-4** financial-trend, ratifica rinumerazione "8+8" con liste vecchie superseded. (`_build_cash_protection` è già risanata in G7.3 via burn; in G7.5 resta solo verificare che non abbia altri ingressi-rimborso diretti.)

**G7.3 resta BLOCCATO sulle 6 decisioni esterne.** Quando arriva la `SettlementPolicy`, Bridge riscrive il pacchetto G7.3 da questa mappa verificata, con questo perimetro.
