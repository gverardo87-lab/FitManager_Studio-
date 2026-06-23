# SPEC_REVISIONE_PRE_G7 — Convergenza del residuo + Copertura SOSPESO

**Tipo:** specifica prescrittiva di revisione (bridge Chat→Code).
**Stato:** verificata sul codice (bridge Code, 2026-06-23) — **da implementare prima di G7**.
**Vincolante per:** implementazione (`docs/technical/`). Claude Code è l'architetto finale della *forma* dall'interno del codebase; questo documento vincola il *cosa-deve-essere-vero*, mai il *come*.
**Origine:** redatta in Claude Chat; **i delta verificati sul codice vivo sono marcati `[Bridge Code 2026-06-23]`** (ground-truth vince sul doc).
**SSoT di dominio:** `FINANCIAL_DOMAIN_MODEL.md` (residuo §2, stati di vita §3, simmetria credito/debito-fantasma §9.5.7) · `contract_state.py` (`residuo()`).

---

## 0. Posizione nel bridge (perché questo documento esiste)

Questo documento è la cerniera del metodo di sviluppo parallelo tra G6 e G7.

- **A valle di G6 (chiuso):** la chiusura del credito-fantasma ha confermato sul campo che `residuo` deve avere un solo significato, definito in un solo posto (`contract_state.residuo()`), e che le superfici di lettura devono raccontare la stessa realtà di dominio. G6 ha blindato la *creazione* (PREREQ-prezzo, invariante `prezzo > 0` su create e update) e ha reso `incassa_residuo` un consumatore disciplinato del SSoT.
- **A monte di G7 (in arrivo):** G7 (debito-fantasma) **ridefinirà** il valore del residuo — una terminazione/rimborso abbasserà il dovuto, e `prezzo − versato` smetterà di essere la formula corretta (`residuo = prezzo − versato − quota_stornata`, FDM §2/§9.5.7). Nel momento in cui la definizione canonica cambia, ogni ricalcolo inline di `prezzo − versato` sparso nel codice diventa una bugia silenziosa.

La review post-G6 ha trovato che il residuo è ancora ricalcolato inline in più punti, e — fatto decisivo — uno di questi (`workspace_engine.py`) è stato scoperto **dopo** un inventario manuale che si riteneva completo. Questo prova ciò che è già principio acquisito nel progetto: **l'enumerazione manuale dei siti off-SSoT è strutturalmente incompleta.** Di conseguenza questo documento non può definire il lavoro come "una lista di siti da migrare": deve definirlo come una *proprietà* che renda il prossimo sito o impossibile, o immediatamente visibile.

---

## 0bis. Esito della verifica bridge `[Bridge Code 2026-06-23]`

La spec è stata verificata contro il codice vivo (workflow 15 agenti, sweep multi-angolo + verifica adversariale per ogni sito candidato). **Esito: tesi e struttura confermate; A.4 confermata incompleta per un margine più ampio del previsto.**

**La lista A.4 (4 siti) ha mancato 5 siti reali** (tutti confermati in modo adversariale). In ordine di conseguenza sotto G7:

| Sito | Superficie | Clamp `max(0,…)` | Rischio sotto G7 |
|---|---|---|---|
| `rates.py:525` | `pay_rate` B-ter — **cap anti-overpayment** | ❌ | **ALTO**: è un *guard del Contract Integrity Engine*. Con `quota_stornata>0` il cap resta `prezzo−versato` → permette pagamenti **oltre** il residuo reale |
| `rates.py:734` | `generate_payment_plan` — validazione `importo_da_rateizzare` | ✅ | MEDIO: rigetterebbe un importo corretto; la formula è anche **hard-coded nel messaggio 422** (righe 742-743) |
| `dashboard.py:497` | `contracts-to-plan` → `items[].importo_residuo` (worklist G1) | ❌ | MEDIO: residuo negativo latente; valore divergente dal SSoT |
| `DeleteContractDialog.tsx:58` (frontend) | `importoNonRiscosso` nel warning di force-delete | ❌ | MEDIO: **unico** ricalcolo residuo del frontend; stamperebbe "−€X non riscossi" su contratto sovra-pagato/stornato |
| `dashboard.py:446` | `_contracts_to_plan_candidates` — `coalesce(prezzo,0) > coalesce(versato,0)` | — | BASSO: **parafrasi ORM** (predicato `residuo>0`) che AC-A1 *non vede*; pre-filtro grezzo, il SSoT corregge a valle (Step 3 `is_rate_planificabile`) → **allowlist**, non bug comportamentale |

**Conseguenza per la strategia (rafforza la spec, non la smentisce):** `rates.py:525/734` non sono convergenza cosmetica — sono **guard di integrità**. Section A non protegge solo i numeri mostrati, protegge le **difese sui pagamenti** dal cambio semantico di G7. Questo eleva Section A da "terreno pulito" a "prerequisito di sicurezza del Contract Integrity Engine".

**Già conformi (delega al SSoT confermata):** detail `_to_response_with_rates` (`contracts.py:130`), `incassa_residuo` (`:1030`), list-item (`:409` via `evaluate_contract`), dashboard suspended/recover (`:677/:719`). La convergenza è quindi **parzialmente già fatta** (G6 + Giro 1). Frontend: `ContractsTable`, `ContractFinancialHero`, `SuspendedCard`/`rinnovi-incassi`, `PaymentPlanTab` **leggono** già il campo backend — l'unico ricalcolo TS residuo è `DeleteContractDialog.tsx:58`.

---

## 1. Principio-madre (vale per entrambe le sezioni)

> **Le superfici devono raccontare la stessa realtà di dominio.**

Da questo principio discendono due lavori distinti, scoperti nella stessa review ma di natura diversa:

- **Sezione A — Convergenza del residuo.** Una sola formula, un solo posto. Problema di *duplicazione di calcolo derivato*.
- **Sezione B — Copertura SOSPESO nel workspace.** Tre superfici devono vedere lo stesso insieme di contratti. Problema di *completezza delle viste*.

### 1.1 Vincolo di processo — NON negoziabile

**Le Sezioni A e B NON condividono un commit.**

Motivazione (è la ragione tecnica per cui la regola esiste, non una preferenza stilistica):

- La Sezione A è un **refactoring a output invariante**: la sua tesi falsificabile è «il comportamento osservabile non cambia». Si verifica con un oracolo gratuito — l'output di prima. Identico = corretto.
- La Sezione B è un **cambiamento funzionale**: la sua tesi falsificabile è «il workspace ora include i SOSPESO». Non ha oracolo gratuito; richiede test che descrivano il comportamento nuovo.

Mescolarle in un commit produce un diff con due tesi falsificabili diverse e nessuna falsificabile pulitamente: davanti a una riga che cambia il valore restituito, «è giusto che cambi?» non avrebbe risposta univoca. Il rumore di B accecherebbe la verifica di A. → Commit separati, idealmente PR/branch separati.

---

## SEZIONE A — Convergenza del residuo (refactoring, output-invariante)

### A.1 Invariante da garantire

> **Esiste una sola funzione che definisce il valore del residuo di un contratto: `contract_state.residuo()`. Nessun altro codice — backend, query SQL, aggregati, frontend — ricalcola quel valore per conto proprio.**

Questo è l'unico requisito sostanziale di tutta la Sezione A. Tutto il resto sono i meccanismi che lo rendono *vero e duraturo* invece che *sperato*.

### A.2 Perché un invariante e non una lista

Il residuo è un **valore derivato**, non un dato in ingresso. Un dato in ingresso (es. il prezzo) ha un unico punto di entrata dove piazzare un guardiano — ed è ciò che PREREQ-prezzo ha fatto in G6. Un valore derivato può essere ri-derivato in qualsiasi punto che abbia in mano un `Contract`: non esiste un collo di bottiglia naturale. Per questo i valori derivati sono più pericolosi dei dati grezzi — la definizione vive in un posto, la ri-derivazione germoglia ovunque e ogni copia sembra innocua finché la definizione canonica non cambia. G7 cambia la definizione canonica.

Conseguenza: il criterio di *done* di questa sezione **non è** «i siti noti sono migrati» (criterio fallibile, è la mossa già fallita in §4.7 dell'IMPL_PLAN e di nuovo qui: vedi §0bis). È «i meccanismi A.3 sono in piedi e verdi».

### A.3 Acceptance criteria (in quest'ordine — i primi due rendono il terzo duraturo)

**AC-A1 — Guard-rail in suite (rete anti-regressione).**
Deve esistere, *dentro la test suite* (gira con la suite esistente, fallisce la build), un test che fallisce se compare un ricalcolo inline del residuo fuori da `contract_state.py`. La *forma* del guard-rail è scelta di Claude Code (pattern testuale, AST, lista di sorgenti scansionate, allowlist motivata): il documento richiede solo che la proprietà sia presidiata e che una nuova occorrenza del pattern faccia diventare rossa la suite.
  - **Forma fattibile verificata `[Bridge Code 2026-06-23]`:** pytest source-scan su `api/**/*.py`, allowlist `contract_state.py`, regex sulla coppia di token `prezzo_totale … − … totale_versato`. Cattura tutte le 7 forme `python_value` in-tree (contracts.py:296/324, dashboard.py:497, rates.py:525/734, workspace_engine.py:1135/1324) ed **esclude naturalmente** il residuo *di rata* (`importo_previsto − importo_saldato`) e la percentuale (`versato/prezzo`). Nessun precedente di source-scan in `tests/` (solo `read_text` su `.env`/`.log`), ma `Path.read_text` è già in uso.
  - **Limiti reali da documentare nel test e nel `BUILD_LOG` `[Bridge Code]`:** il guard-rail sintattico è **cieco** a (1) predicati ORM/comparazione (`dashboard.py:446` `coalesce(prezzo,0) > coalesce(versato,0)` = `residuo>0`, da mettere in **allowlist** motivata — è un pre-filtro grezzo che il SSoT ri-corregge); (2) raw-SQL e forme multilinea/parafrasate; (3) **tutto il frontend TS**. È la *prima linea*, non quella definitiva: l'evoluzione naturale è un **hook di CI** dedicato — **fuori da questo giro**. AC-A2 è il backstop semantico che copre questi buchi.

**AC-A2 — Test di coerenza cross-surface (la rete che cattura anche l'ignoto).**
Deve esistere un test che, per uno stesso contratto, verifica che il residuo riportato dalle superfici di lettura **coincida**: lista contratti, dettaglio contratto, e `finance_context` del workspace (le superfici note oggi; se ne emergono altre, vanno incluse). Questo test non verifica *dove* si calcola il residuo — verifica una *proprietà di coerenza osservabile*, e quindi cattura anche i siti che non sapevamo esistessero. È l'antidoto diretto all'incompletezza dell'enumerazione manuale. Oggi passa banalmente (valori byte-identici); il giorno in cui G7 cambia `residuo()` e un sito viene dimenticato, diventa rosso.
  - **Seam wire verificati `[Bridge Code 2026-06-23]`:** lista `GET /api/contracts` → `items[].residuo` (`financial.py:278`, popolato `contracts.py:409`); dettaglio `GET /api/contracts/{id}` → `.residuo` (`financial.py:310`, popolato `contracts.py:130`); workspace `GET /api/workspace/cases?workspace=renewals_cash` → `items[].finance_context.total_residual_amount` (`workspace.py:83`).
  - **⚠️ Seam critico (la spec Chat non lo vedeva):** `total_residual_amount` è **sovraccarico per `case_kind`** — è residuo-contratto per `payment_due_soon` (`workspace_engine.py:1135`) e `contract_renewal_due` (`:1324`), ma **somma dei residui delle rate scadute** per `payment_overdue` (`:1018`). Il test cross-surface **deve pilotare la fixture** su un case-kind contract-level (`payment_due_soon`/`contract_renewal_due`), altrimenti l'uguaglianza fallisce *per definizione*, non per bug. (Inoltre la stessa incoerenza che un test cross-surface farebbe emergere oggi è il frontend `DeleteContractDialog.tsx:58`.)

**AC-A3 — Le occorrenze note delegano.**
Tutti i siti inline noti devono delegare a `contract_state.residuo()` (per-contratto; gli aggregati sommano il risultato della funzione, non ricalcolano). Vedi A.4 per l'elenco di partenza.
  - **Invariante già presidiato `[Bridge Code 2026-06-23]`:** `kpi_residuo = kpi_a_rate + kpi_da_pianificare + kpi_da_incassare_scaduto` è **già asserito** in `tests/test_contracts_to_plan.py:218-219`. Delegare `contracts.py:296/324` a `residuo()` è **byte-identico oggi** (stesso `round`/`max`/coalesce) → invariante preservato; sotto G7 la delega diventa load-bearing perché l'identità regga.

**Verifica della sezione:** poiché A è refactoring puro, l'output di ogni superficie deve restare **byte-identico** prima/dopo su `crm.db` reale. Qualunque differenza di valore è un difetto del refactoring, non un effetto atteso. (Eccezione attesa e *desiderata*: i tre siti senza clamp — `rates.py:525`, `dashboard.py:497`, `DeleteContractDialog.tsx:58` — su un contratto sovra-pagato passano da un valore negativo a `0`. È una correzione di bug latente, non una regressione: va annotata, non temuta.)

### A.4 Siti inline noti (evidenza — verificata e ESTESA dal bridge, dichiaratamente non esaustiva)

> Questa lista è il punto di partenza verificato, **non** la definizione del lavoro. Il lavoro è completo quando AC-A1/A2/A3 sono verdi, non quando questi item sono spuntati. La storia di `workspace_engine.py` (e ora dei 5 siti aggiunti dal bridge) è la prova che questa lista può essere incompleta.

**Backend — `api/routers/contracts.py` (`list_contracts`), aggregati (A.4 originale):**
1. `kpi_residuo` (`:296`) — `Σ max(0, prezzo − versato)` sui contratti aperti. Delega: `sum(cstate.residuo(c) for c in open)`.
2. il `resto` (`:324`) nel loop `da_pianificare` / `da_incassare_scaduto` (ricalcolo per-contratto dentro la somma). Delega: `cstate.residuo(c) − residui_a_rate`. **NB:** `kpi_da_incassare_scaduto` è esattamente il bucket con cui la Sezione B deve allinearsi.
3. (derivato) l'invariante `kpi_residuo = kpi_a_rate + kpi_da_pianificare + kpi_da_incassare_scaduto` deve continuare a tornare (vedi AC-A3, già testato).

**Backend — `api/services/workspace_engine.py` (A.4 originale):**
4. `_build_payment_due_soon_cases` (`:1135`) → `contract_residual_amount = round(max((prezzo or 0) − versato, 0), 2)`. **NB `[Bridge]`:** `totale_versato` qui è **senza `or 0`** (si affida al default colonna; `or 0` per coerenza difensiva).
5. `_build_contract_renewal_cases` (`:1324`) → `total_residual_amount` (stesso, `totale_versato` senza `or 0`); `total_due_amount = contract.prezzo_totale` (`:1323`) passa il prezzo **grezzo e nullable** senza `max`/coalesce. Con PREREQ-prezzo il null è irraggiungibile sui nuovi, ma per coerenza difensiva trattarlo come gli altri (`or 0`).

**Backend — siti aggiunti dal bridge `[Bridge Code 2026-06-23]`:**
6. `api/routers/rates.py:525` (`pay_rate`, B-ter) — `residuo_contratto = round(prezzo − versato, 2)` usato come **cap anti-overpayment**. Senza clamp. **PRIORITÀ ALTA** (guard di integrità: sotto G7 over-permetterebbe pagamenti). `rates.py` oggi **non importa** `contract_state` → la delega aggiunge l'import.
7. `api/routers/rates.py:734` (`generate_payment_plan`) — `residuo_atteso = round(max(0, (prezzo or 0) − (versato or 0)), 2)`, validazione 422. La formula è **anche hard-coded nel messaggio d'errore** (righe 742-743) → da correggere insieme.
8. `api/routers/dashboard.py:497` (`get_contracts_to_plan`) — `importo_residuo` inline, **senza clamp**. Delega a `cstate.residuo(contract)`.
9. `api/routers/dashboard.py:446` (`_contracts_to_plan_candidates`) — where-clause ORM `coalesce(prezzo,0) > coalesce(versato,0)` (= `residuo>0`). **Non delegabile** (è SQL): resta come pre-filtro grezzo con il SSoT come autorità (Step 3) → va in **allowlist** di AC-A1 con commento.

**Frontend — sito aggiunto dal bridge `[Bridge Code 2026-06-23]`:**
10. `frontend/src/components/contracts/DeleteContractDialog.tsx:58` — `importoNonRiscosso = (prezzo ?? 0) − (versato ?? 0)`, reso a `:110` ("… non riscossi"). Senza clamp; **unico** ricalcolo residuo del frontend. **Caveat di fix:** il prop è il `Contract` base (`types/api.ts:620`) che **non** ha `residuo` — solo `ContractListItem` (`:651`) e `ContractWithRates` (`:671`) lo portano; i caller passano un `ContractListItem` a runtime, quindi allargare il prop a `ContractListItem` (o aggiungere `residuo` a `Contract`) e leggere `c.residuo` (clamp gratis).

Nota: il dettaglio (`_to_response_with_rates:130`), `incassa_residuo` (`:1030`), il list-item (`:409`), dashboard suspended/recover (`:677/:719`) e le superfici frontend G6 **già delegano/leggono** correttamente — non vanno toccati se non per conferma.

### A.5 Direzione futura (catturata come principio, non da implementare ora)

La ragione per cui chiunque *può* scrivere `prezzo − versato` è che `prezzo_totale` e `totale_versato` sono `float` nudi e pubblicamente accessibili: un `float` invita all'aritmetica. La cura strutturale piena sarebbe rendere il residuo l'unico modo *comodo* di chiedere «quanto manca» e i campi grezzi scomodi da raggiungere per quel fine (incapsulamento per tipo / accesso scoraggiato). A ridosso della POC, il refactoring radicale dei campi è fuori scope. Si registra qui come **direzione**, non come lavoro di questo giro: il principio è *rendere la cosa giusta la cosa facile*, non combattere la tentazione con la disciplina. L'hook di CI di AC-A1 e un'eventuale guardia TS sul frontend appartengono a questa stessa direzione.

---

## SEZIONE B — Copertura SOSPESO nel workspace (cambiamento funzionale)

> **Lavoro indipendente da G7.** Non è un prerequisito del debito-fantasma: è un debito di copertura scoperto nella stessa review. Eseguibile prima, dopo o in parallelo ad A, a discrezione. NON condivide commit con A (§1.1).

### B.1 Comportamento da rendere vero

> **La superficie `renewals_cash` del workspace deve materializzare i contratti SOSPESO (scaduti, aperti, con sedute e/o residuo ancora dovuti), allineandosi a ciò che già mostrano `list_contracts` (bucket `kpi_da_incassare_scaduto`) e la pagina `rinnovi-incassi` (`useSuspendedContracts`).**

**⚠️ Correzione bridge `[Bridge Code 2026-06-23]`:** l'aggancio **deve essere `lifecycle == SOSPESO`** (derivato dal SSoT `contract_state`), **NON `residuo > 0`**. Un SOSPESO *saldato* (residuo 0) ma con sedute residue è il caso-tipo del doppio-debito: filtrare sul denaro lo perderebbe. È esattamente il criterio di `GET /dashboard/suspended-contracts` (`_suspended_contracts_candidates` chiave su `lifecycle==SOSPESO`, non sul residuo) → per essere la *terza superficie coerente*, il workspace deve usare lo stesso criterio.

### B.2 La natura del buco (verificata sul codice `[Bridge Code 2026-06-23]`)

`renewals_cash` è alimentato da tre builder contratto/rata (più le spese ricorrenti), con queste **maglie esatte**:
- **overdue** (`_load_overdue_rows`, `:949-968`): `chiuso==False` **AND** rata `PENDENTE/PARZIALE` con `data_scadenza < today`. → serve una **rata scaduta**.
- **due_soon** (`_load_due_soon_rows`, `:1068-1089`): rata con `data_scadenza ∈ [today, today+7]`.
- **renewal/expiring** (`_load_expiring_contract_rows`, `:1200-1256`): `chiuso==False` **AND** `data_scadenza ∈ [today, today+30]` **AND** crediti residui > 0.

Un contratto **SOSPESO** è scaduto (`data_scadenza < today`, fuori dalla maglia renewal per `:1216`) e non ha necessariamente rate scadute (fuori dalla maglia overdue). E **non può** avere una rata due_soon: l'integrity-guard #9 cappa le date-rata a `contract.data_scadenza < today`, quindi nessuna rata può cadere in `[today, today+7]`. Cade nel vuoto tra le maglie: **non genera alcun `OperationalCase`**. Confermato per trace. Le viste divergono **per omissione**, non per calcolo errato.

### B.3 Acceptance criteria

**AC-B1 — I SOSPESO compaiono.**
I contratti SOSPESO (lifecycle derivato dal SSoT `contract_state`, **non** ricalcolato; aggancio su `lifecycle==SOSPESO`, **non** su residuo — vedi B.1) devono comparire come `OperationalCase` nella superficie `renewals_cash`. Lo stato di vita **deve** derivare da `contract_state` (regola d'oro), mai da una nuova condizione SQL inline che reintrodurrebbe il problema della Sezione A su un altro asse. Riuso naturale: `_suspended_contracts_candidates` (`dashboard.py:597-632`) già fa esattamente questa derivazione.

**AC-B2 — Allineamento tra superfici.**
L'insieme di contratti SOSPESO mostrato dal workspace deve essere coerente con quello di `list_contracts` / `rinnovi-incassi` a parità di dato. (Punto di contatto naturale con AC-A2: se il residuo è coerente cross-surface ed entrambe le viste partono dallo stesso SSoT, l'allineamento è verificabile.)

**AC-B3 — Semantica del case esplicitata.**
Vanno decisi e documentati nel codice (e qui, a implementazione avvenuta, come learning capture): **bucket** (`CaseBucket ∈ [now, today, upcoming_3d, upcoming_7d, waiting]`, `workspace.py:11`; per uno scaduto-obbligazione presumibilmente `now`/`waiting` — scelta da motivare), **severity** (`CaseSeverity ∈ [critical, high, medium, low]`), nuovo **`CaseKind`** (es. `suspended_contract`, da aggiungere a `workspace.py:23-38`), e il **doppio asse** già reso esplicito in `rinnovi-incassi` (sedute residue ≠ denaro dovuto: due debiti distinti, non un doppione).
  - **⚠️ Merge — correzione bridge `[Bridge Code 2026-06-23]`:** la dedup tra builder **NON passa da `merge_key`** (nessun consumer lo legge). Avviene via **exclusion-set espliciti** threadati tra i builder (`overdue_contract_ids` / `due_soon_contract_ids`, `workspace_engine.py:2293-2325`, consumati a `:1106-1107` / `:1275-1278`). Poiché un nuovo `case_kind` produce un `case_id`/`merge_key` distinto, due case per lo stesso contratto **non collasserebbero** da soli. Il nuovo builder SOSPESO **deve ricevere `overdue_contract_ids`** (un SOSPESO con anche rate scadute è già mostrato come `payment_overdue`) ed essere cablato nel threading di esclusione.

**Verifica della sezione:** poiché B è cambiamento funzionale, si verifica con **test che descrivono i case attesi** (presenza, bucket, severity, no-doppione vs overdue), non con confronto all'output di prima — che per i SOSPESO non esiste.

### B.4 Confine esplicito con G7

B rende *visibili* i SOSPESO con il loro residuo **attuale** (definizione corrente). B **non** anticipa la ridefinizione del residuo da terminazione/rimborso — quella è G7. Se A è già stato fatto, B legge automaticamente il residuo dal SSoT e beneficerà della futura ridefinizione G7 senza modifiche. Questo è il vantaggio del front-loading: terreno coerente prima del cambiamento semantico.

---

## 2. Riepilogo operativo per l'implementazione

| | Sezione A | Sezione B |
|---|---|---|
| Natura | Refactoring (output invariante*) | Cambiamento funzionale |
| Tesi falsificabile | «il comportamento non cambia» | «il workspace ora include i SOSPESO» |
| Oracolo di verifica | output di prima (byte-identico*) | test che descrivono il nuovo comportamento |
| Done | AC-A1/A2/A3 verdi | AC-B1/B2/B3 verdi |
| Relazione con G7 | **prerequisito** (terreno pulito + difese pagamenti) | **indipendente** |
| Commit | separato da B | separato da A |

\* eccezione attesa: i 3 siti senza clamp passano da negativo→0 su contratti sovra-pagati (correzione di bug latente, vedi A.3).

**Regola ferrea:** A e B non condividono commit. Il guard-rail (AC-A1) è oggi un test Python in suite su `api/**/*.py` + allowlist (`contract_state.py` + `dashboard.py:446`); l'hook di CI dedicato e una guardia TS sul frontend sono direzione futura (A.5), fuori da questo giro.

---

## 3. Bridge rule (cattura post-implementazione)

A implementazione avvenuta, il codice non banale prodotto da Claude Code va digerito in chat e, dove pertinente, promosso a learning (`docs/learning/`) e annotato nel `BUILD_LOG.md`. In particolare meritano cattura: la forma scelta per il guard-rail (e i suoi limiti reali emersi), il seam del `total_residual_amount` sovraccarico (AC-A2), e le decisioni di semantica del case SOSPESO (B.3, bucket/severity/merge-via-exclusion-set), che sono scelte di dominio non deducibili dall'output di ieri.

**Cattura bridge di QUESTO documento `[Bridge Code 2026-06-23]`:** la verifica contro il codice vivo ha aggiunto 5 siti ad A.4 (di cui `rates.py:525` un guard di integrità ad alto rischio), ha qualificato AC-A1 (limiti SQL/ORM/TS), AC-A2 (campo `total_residual_amount` sovraccarico per `case_kind`), AC-B1 (aggancio su `lifecycle==SOSPESO` non su residuo) e AC-B3 (dedup via exclusion-set non `merge_key`). Tutti i siti citati `file:riga` sono verificati sul branch `FitManager_Studio` post-G6 (`3ebef34`).
