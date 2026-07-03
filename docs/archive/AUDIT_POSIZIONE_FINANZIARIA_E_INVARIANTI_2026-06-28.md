# Audit architetturale — Posizione finanziaria, invarianti e livelli (CONTRATTO vs CLIENTE)

> **Tipo:** audit READ-ONLY (zero codice modificato, zero migrazioni). Senior software architect.
> **Data:** 2026-06-28 · **Branch:** FitManager_Studio · **Dominio:** terminazione / riapertura / posizione cliente
> **Ground truth:** il codice vivo, sopra ogni spec/ADR/BUILD_LOG. Le contraddizioni doc↔codice sono segnalate (§Appendice A).
> **Regola d'oro rispettata:** ogni raccomandazione è accompagnata dalla fetta minima che chiude la classe di bug, senza migrazione di massa e senza toccare G1. I costi alti sono NOMINATI ma messi "in panchina".

---

## 0. Esito in una pagina (TL;DR)

**La tesi è CONFERMATA per il lato-scrittura, ma va CORRETTA su un punto sostanziale: il lato-lettura È già centralizzato.**

Esiste un SSoT reale e rispettato per la *derivazione* della posizione: `api/services/contract_state.py` (funzioni pure — `residuo()`, `netto_incassato()`, `is_saldato()`, `Lifecycle`, sotto-stato denaro). La "regola d'oro" («nessun endpoint ricalcola residuo/attivo/scaduto inline») è davvero seguita: ogni cap, KPI e worklist delega a `cstate.residuo()`.

Ciò che **non** esiste è un SSoT della *mutazione*. Ogni transizione di stato (`terminate`, `reopen`, `incassa_residuo`, `pay_rate`, `unpay_rate`, `eroga_credito_cliente`, `incassa_credito_terminazione`) è una **procedura inline** che **ri-costruisce a mano** gli stessi invarianti globali (`residuo()==0` su chiuso, `netto≥0`, "nessun euro sparisce"). Non c'è un punto unico che li applichi/verifichi dopo ogni scrittura, e **non esiste la "posizione economica del CLIENTE" come entità di prima classe**.

> **Radice (una frase):** il dominio finanziario ha un **read-model centralizzato** (`contract_state.py`) ma un **write-model decentralizzato** — ogni transizione re-asserisce a mano gli invarianti, `contract_state` può solo *segnalarne* la violazione, mai *impedirla*, e i clamp `max(0, …)` trasformano ogni errore aritmetico in **perdita silenziosa** invece che in errore. Da qui, e dal mismatch di livello del wallet (saldo del CLIENTE con ciclo di vita legato al CONTRATTO), discende la classe ricorrente di bug.

**Caso-sonda (secondo contratto):** la posizione del cliente attraverso due contratti **non vive da nessuna parte**. `residuo()` è funzione pura di UN contratto. Il wallet (`crediti_cliente`) è l'unico oggetto a livello-cliente, ma è una **strada a senso unico** (solo cash-out: non può pagare un altro contratto). Un credito generato da A **non è applicabile** a B.

**Fetta minima (dettaglio §5):** ① guard osservabile `assert_contract_invariants()` (output-invariante, log→409) → ② reopen riconcilia il wallet già parzialmente erogato (l'unico vero money-bug) → ③ guard orfani su `delete_client`/`delete_contract` → ④ estrazione `recompute_stato_pagamento()` (de-dup, oracolo = byte-identità della suite). **In panchina:** transition-layer a funnel unico, `ClientPosition` materializzata, wallet auto-spendibile cross-contratto.

---

## FASE 1 — Enumerazione meccanica (fatti)

Coordinate `file:funzione` (i numeri di riga driftano: i siti sono descritti anche per **ruolo**). Modelli: `Contract`→`api/models/contract.py`; `CreditoCliente`→`api/models/credito_cliente.py`; `CreditoTerminazione`→`api/models/credito_terminazione.py`; `CashMovement`→`api/models/movement.py`.

### 1.1 — Scritture sui campi finanziari del Contratto (GRUPPO A)

| Campo | Sito (`file:funzione`) | Operazione | Guard? |
|---|---|---|---|
| `quota_stornata` | `contracts.py:terminate_contract` (~1674) | `+= residuo_pre − incasso_ora + rimborso_out` (gamba STORNO, sempre) | endpoint-guard `chiuso`→400 |
| | `contracts.py:reopen_contract` (~1936) | `= 0` (storno inverso) | endpoint-guard `not chiuso`→400 |
| `totale_versato` | `contracts.py:create_contract`/`renew_contract` | `= acconto` (costruttore) | `if acconto>0` per il CashMovement |
| | `contracts.py:incassa_residuo` (~1333) | `+= importo` | B `chiuso`, C `residuo>0`, D cap |
| | `contracts.py:terminate_contract` (~1647) | `+= incasso_ora` (ramo CREDITO_TRAINER/INCASSA_ORA) | annidato in azione + cap + `>0.009` |
| | `contracts.py:incassa_credito_terminazione` (~2189) | `+= importo` | stato/residuo/importo/cap |
| | `rates.py:pay_rate` (~569) | `+= importo` | B/B-bis/B-ter |
| | `rates.py:unpay_rate` (~692) | `= max(0, versato − storno)` **(unico DECREMENTO)** | B + **B-bis H1 409** |
| `totale_rimborsato` | `contracts.py:terminate_contract` (~1586) | `+= rimborso_out` (ramo CREDITO_CLIENTE) | annidato in esito + metodo + `>0.009` |
| `chiuso` | `contracts.py:terminate_contract` (~1695) | `= True` **diretto** (mai `_sync`) | endpoint-guard |
| | `contracts.py:reopen_contract` (~1968) | `= False` | endpoint-guard |
| | `rates.py:pay_rate` (~589) | `= True` (auto-close) | `SALDATO ∧ crediti_usati≥totali` |
| | `rates.py:unpay_rate` (~711) | `= False` (auto-reopen) | `chiuso ∧ ≠SALDATO ∧ motivo==COMPLETAMENTO` |
| | `agenda.py:_sync_contract_chiuso` (~341) | `= should_be_chiuso` | reopen-allowlist + delta |
| `motivo_chiusura` | terminate (~1696) / reopen (~1969) / pay_rate (~590) / unpay_rate (~712) / `_sync` (~343/345) | set derivato dall'esito o `COMPLETAMENTO`/`None` | come sopra |
| `stato_pagamento` | **pay_rate (~572) · unpay_rate (~695) · incassa_residuo (~1334) · reopen (~1960)** | ricalcolo SALDATO/PARZIALE/PENDENTE | if/elif locali, **4 copie divergenti** |
| `data_chiusura` (Contract) | terminate (~1697) / reopen (~1970) | set/None | endpoint-guard |
| `chiusa_da_terminazione` (Rate) | terminate (~1689) / reopen (~1950) | marker True/False per l'inverso-esatto delle rate | loop |

### 1.2 — Crediti (GRUPPO B)

**`CreditoCliente` (wallet — saldo a favore del cliente)**
- **CREATE:** `contracts.py:terminate_contract` (~1590) — il non-rimborsato (`credito_cliente − rimborso_out`) → wallet, `causale=RIMBORSO_DIFFERITO`, `id_contratto_origine=contract.id`. Guard: `esito==CREDITO_CLIENTE ∧ wallet_credit>0.009`.
- **ANNULLA:** `contracts.py:reopen_contract` R4 (~1915–1933) — `stato="ANNULLATO"` per OGNI wallet con `id_contratto_origine==contract.id ∧ stato≠ANNULLATO`. **Loop incondizionato: nessuna lettura di `importo_erogato`.**
- **EROGA (incrementa `importo_erogato`):** `clients.py:eroga_credito_cliente` (~1123) → `CashMovement` USCITA `RIMBORSO_CONTRATTO` con **`id_contratto=None`** (~1118). A saldo → `SALDATO`. Guard: stato/residuo/importo/cap.

**`CreditoTerminazione` (receivable — credito a favore del trainer)**
- **CREATE:** `contracts.py:terminate_contract` (~1659) — ramo `A_CREDITO`, `id_contratto=contract.id`.
- **ANNULLA:** `contracts.py:reopen_contract` R3 (~1907) · `contracts.py:annulla_credito_terminazione` (~2229).
- **INCASSA (incrementa `importo_incassato` + `totale_versato`):** `contracts.py:incassa_credito_terminazione` (~2192). A saldo → `SALDATO`.

> Nessun `.deleted_at` sui due modelli credito: il ciclo di vita passa **solo** da `stato` (APERTO/SALDATO/ANNULLATO).

### 1.3 — CashMovement legati al contratto (GRUPPO C)

CREATE (tutti con `id_contratto=contract.id`, salvo dove indicato): acconto/rinnovo (`ACCONTO_CONTRATTO`), `incassa_residuo`+`pay_rate` (`PAGAMENTO_RATA`), `terminate` rimborso (`RIMBORSO_CONTRATTO` USCITA) e incasso (`INCASSO_CONGUAGLIO_CONTRATTO` ENTRATA), `incassa_credito_terminazione` (`INCASSO_CONGUAGLIO_CONTRATTO`). **Eccezione di modello:** `eroga_credito_cliente` crea `RIMBORSO_CONTRATTO` USCITA con **`id_contratto=None`** (decoupled — ADR-019/020).

SOFT-DELETE: `unpay_rate` (~728, movimenti della rata), `delete_contract` (~1070/~1102, reverse/cascade). **`reopen_contract` NON soft-cancella alcun CashMovement** (ADR-019, "cassa immutabile"; gambe delete C/C-bis rimosse).

### 1.4 — Call-graph (centralizzazione effettiva)

- **Read-model centralizzato:** `contract_state.residuo()` / `netto_incassato()` / `is_saldato()` chiamati da contracts, rates, dashboard (`:514/695/737`), `workspace_engine` (`:1151/1339/1439`), e dalle response DTO (`financial.py` `ContractResponse`/`ContractWithRatesResponse`, `residuo` delegato — `:456/517`). **Confermato: nessun ricalcolo inline del residuo.**
- **Write-model NON centralizzato:** `_sync_contract_chiuso` (chiuso/motivo) è condiviso da agenda + `incassa_residuo`, ma **terminate/reopen lo bypassano deliberatamente**; `compute_settlement` ha un solo chiamante (`_settlement_for`); `_reconcile_rate_plan` un solo chiamante (reopen); `_cap_rateizzabile` due (create/update rate). **Non esiste alcun `apply_transition()` / `assert_invariants()` comune.**

### 1.5 — Frontend (sintesi; dettaglio enumerato a parte)

- **Ricalcoli client-side di denaro** (≠ lettura API): `netto = versato − rimborsato` in `ContractFinancialHero.tsx` (~42) e `ContractsTable.tsx` (~181); saldo progressivo in `ContractHistoryTab.tsx` `CashLedgerCard` (~83); split rimborso/wallet in `TerminateContractDialog.tsx` (~94, `Math.max(creditoCliente − rimborso, 0)`); valore ~ crediti in `ExpiringContractsSheet.tsx` (~189). Il resto (residuo, breakdown rate) è **letto** dall'API.
- **Aggregazione wallet per-cliente:** unico punto = `ContrattiTab.tsx` `WalletCreditBadge` (~20, `reduce` sui `crediti_cliente` APERTO del cliente). Nessun KPI cross-cliente.
- **Asimmetrie di invalidazione (`hooks/useContracts.ts`):** `useEroghaRimborso` **non** invalida `contract`/`contracts` (è USCITA a livello cliente); `useIncassaResiduo` **non** invalida `forecast`/`workspace`/`client-wallet`, mentre il gemello `useTerminateContract` sì. Sintomo dello stesso confine sfocato CONTRATTO/CLIENTE.

---

## FASE 2 — Matrice sito × invariante

**Invarianti del dominio** (estratti da codice + commenti):

- **I1** — `residuo() == 0` su un contratto chiuso (FDM §3.1; commento terminate gamba E).
- **I2** — `totale_versato == Σ ENTRATA[id_contratto]` (àncora cassa; commento terminate F, `/dashboard/reconciliation`).
- **I3** — `totale_rimborsato == Σ USCITA RIMBORSO_CONTRATTO[id_contratto]` (commento `eroga_credito_cliente`).
- **I4** — `netto ≥ 0` **senza** che il clamp `max(0, …)` mascheri `Σuscita > Σentrata` (commento H1, unpay_rate).
- **I5** — *(il profondo)* "nessun euro dato/ricevuto dal cliente sparisce attraverso una transizione, **a livello CLIENTE**".

| Sito | I1 residuo==0 su chiuso | I2 versato==ΣENTRATA | I3 rimborsato==ΣUSCITA | I4 netto≥0 senza maschera | I5 nessun euro perso (CLIENTE) |
|---|---|---|---|---|---|
| `pay_rate` | n/a (apre) | **mantiene** (CashMovement gemello) | n/a | assume (clamp non in gioco) | assume |
| `unpay_rate` | n/a | **mantiene** (decrementa + soft-del movimento) | n/a | **VERIFICA** (guard H1 409 — unico presidio) | assume |
| `incassa_residuo` | n/a | **mantiene** | n/a | assume | assume |
| `terminate` (CREDITO_CLIENTE) | **ri-stabilisce a mano** (gamba E: `quota += residuo_pre + rimborso_out`) | **mantiene** | **mantiene** | assume | **ri-stabilisce** (refund + wallet = overpay) ✅ |
| `terminate` (CREDITO_TRAINER) | **ri-stabilisce** (gamba E: `quota += residuo_pre − incasso_ora`) | **mantiene** | n/a | assume | assume |
| `reopen` | **ri-stabilisce** (`quota=0` + residuo net-aware) | **mantiene** (cassa immutabile) | **mantiene** | assume | **VIOLA** sul wallet già erogato (§4.2 Bug-1) ❌ |
| `eroga_credito_cliente` | n/a (contratto già 0) | n/a (`id_contratto=None`) | **per costruzione fuori da I3** | assume | **dipende da reopen** (traccia solo in `importo_erogato`) |
| `incassa_credito_terminazione` | **assume** (quota ha già assorbito) | **mantiene** | n/a | assume | assume |

**Dove un clamp `max(0,…)` trasforma una violazione in silenzio:**
- `contract_state.netto_incassato` (`:90–95`): `max(versato − rimborsato, 0)` → **maschera** `rimborsato > versato`.
- `contract_state.residuo` (`:73–87`): `max(prezzo − netto − quota, 0)` → **maschera** `netto + quota > prezzo` (over-storno/over-rimborso).
- **Unico presidio strutturale:** il guard **H1** in `unpay_rate` (`rates.py:662–678`) blocca a 409 l'unica via *nota* in cui `versato` scenderebbe sotto `rimborsato`. È un **point-patch**, non una garanzia: ogni nuova via che alteri `versato`/`rimborsato`/`quota` può re-introdurre la violazione, e i clamp la nasconderanno (esattamente ciò che succede in §4.2 Bug-1, dove infatti il clamp non scatta ma l'euro sparisce dalla posizione-cliente).

**Lettura della matrice:** nessuna riga **verifica** I1; tutte la **ri-stabiliscono** o la **assumono**. `contract_state` può solo *segnalare* `residuo()>0 su chiuso` (es. in `/dashboard/reconciliation`), mai impedirlo al momento della scrittura. È la firma del write-model decentralizzato.

---

## FASE 3 — Mappa dei livelli (CONTRATTO vs CLIENTE)

### 3.1 — Assegnazione corretta

| Livello | Proprietà |
|---|---|
| **CONTRATTO** | `prezzo_totale`, `totale_versato`, `totale_rimborsato`, `quota_stornata`, `residuo()`, rate, `chiuso/motivo/data_chiusura`, **`crediti_terminazione`** (receivable di UN contratto: corretto) |
| **CLIENTE** | il **saldo** del wallet (`crediti_cliente` ha `id_cliente`+`trainer_id`; erogato come cassa-cliente `id_contratto=None`; sommato per-cliente in `WalletCreditBadge`) |

### 3.2 — Mismatch di livello (il difetto noto + altri)

1. **Wallet — saldo CLIENTE, ciclo di vita CONTRATTO (il caso noto).** `crediti_cliente.id_contratto_origine` (`models/credito_cliente.py:36`) lega il wallet al contratto che l'ha generato. Conseguenza: `reopen(A)` lo **annulla** interrogando `id_contratto_origine==A` (`contracts.py:1921`). Un saldo a livello-cliente è quindi **governato da un evento a livello-contratto**. Il commento `financial.py:475` lo certifica esplicitamente: *«L'erogazione wallet (`id_contratto=None`) NON è qui (cassa a livello cliente, sul profilo)»* — la cassa del contratto **esclude** per design la cassa-cliente, e non esiste una vista cassa-cliente che netti tra contratti. **È la cucitura su cui la posizione si frammenta.**

2. **`delete_client` ragiona solo per contratti (cieco al saldo-cliente).** `clients.py:986–999` fa RESTRICT solo su `Contract.chiuso==False`. Non considera wallet/receivable APERTI. → Si può soft-eliminare un cliente a cui **devi** denaro (wallet APERTO) o che **ti** deve (receivable APERTO): l'obbligazione a livello-cliente resta **orfana** (e la worklist `rimborsi-da-erogare`/`crediti-da-incassare` fa join su `Client` senza filtrare `Client.deleted_at`).

3. **`delete_contract` non riconcilia i crediti che ha generato.** `contracts.py:1009–1104`: il RESTRICT guarda rate pendenti e crediti-sedute, **non** wallet (`id_contratto_origine`) né receivable (`id_contratto`). Il cascade soft-elimina rate+movimenti, **non** i due crediti. → Eliminando il contratto-origine si **orfana** il wallet/receivable. È la stessa identica failure-mode del *pitfall #10* (tabella con FK dimenticata dal cascade): nuova tabella ⇒ ogni path a mano va aggiornato, e non lo è stato.

4. **Nessuna lettura di "posizione-cliente" da nessuna parte.** `workspace_engine.py` (cockpit operativo) **non** referenzia wallet/receivable. `DashboardSummary`, `ClientResponse` non hanno alcun aggregato finanziario cross-contratto. La domanda *«questo cliente, sommando i suoi contratti e i suoi crediti, è in credito o in debito netto?»* è **non rispondibile** dal sistema attuale. La posizione-cliente vera spazia su `Σ residuo(contratti aperti)`, `Σ wallet APERTO` (gli devi), `Σ receivable APERTO` (ti deve) — **nessuno di questi è mai sommato insieme**.

---

## FASE 4 — Diagnosi della radice

### 4.1 — Verdetto sulla tesi

| Affermazione della tesi | Verdetto |
|---|---|
| "Le transizioni sono procedure inline nei router, ciascuna responsabile di mantenere a mano gli stessi invarianti" | ✅ **CONFERMATA** (write-model decentralizzato, Fase 1.4 + Fase 2) |
| "NON esiste un punto unico che applichi questi invarianti dopo ogni transizione" | ✅ **CONFERMATA** (nessun `assert_invariants`/`apply_transition`) |
| "NÉ la nozione di posizione-CLIENTE come entità di prima classe" | ✅ **CONFERMATA** (Fase 3.2 §4) |
| "Il wallet è gestito a livello CONTRATTO quando è proprietà del CLIENTE" | ✅ **CONFERMATA con sfumatura**: *saldo* client-level, *ciclo di vita* contract-level (`id_contratto_origine`) |
| *(implicito)* "ciascuno ricalcola a mano gli stessi invarianti **incluso il residuo**" | ❌ **SMENTITA**: il **read-model è centralizzato** in `contract_state.py` e la regola d'oro è rispettata. È un risultato valido e va detto. |

La correzione non è cosmetica: dice **dove** intervenire. Il read-model non va toccato (funziona). Il difetto è interamente nel **write-model** e nella **mancanza di un livello-cliente**.

### 4.2 — La radice, e perché ogni bug è lo stesso difetto

> **Radice:** *read-model centralizzato + write-model decentralizzato senza un layer di transizione che applichi gli invarianti + assenza della posizione-cliente di prima classe + clamp `max(0,…)` che silenziano le violazioni.*

**Bug-1 — wallet erogato perso al reopen (vero money-bug, riproducibile).**
Sequenza: `terminate(A)` esito CREDITO_CLIENTE, `credito_cliente=300`; il trainer rimborsa `100` (`totale_rimborsato=100`) e mette `200` a wallet. Poi **eroga 50** dal wallet → USCITA `RIMBORSO_CONTRATTO` con `id_contratto=None`, `importo_erogato=50` (questi 50 **non** toccano `totale_rimborsato` di A, per design). Ora **`reopen(A)`**: R1 lascia ferma la cassa (i 100 restano in `totale_rimborsato`); R4 annulla il wallet **incondizionatamente** (non legge `importo_erogato`); il residuo net-aware si ricalcola = `P − (versato − 100)`. **Risultato:** il cliente ha incassato 150 (100+50), ma il contratto riflette solo 100; i 50 erogati dal wallet **non** sono in alcun `totale_rimborsato`, e il wallet che li tracciava è ANNULLATO. **I 50 spariscono dalla posizione** — la *cassa* è corretta (l'USCITA resta nel mastro), ma l'*attribuzione cliente↔contratto* è persa. Il clamp non scatta, eppure l'euro evapora: è I5 violata, e nessuno può accorgersene perché I5 è **non osservabile**. → discende da: reopen è un inverso *hand-listed* (annulla ciò che conosce) e la parte erogata è client-level (decoupled), fuori dalla sua lista.

**Bug-2 — wallet cross-contratto (caso-sonda).** `residuo(B)` è funzione pura di B; non esiste oggetto che veda A e B insieme; il wallet può solo essere erogato in cassa. Quindi un credito di A **non** è applicabile a B, e la posizione-cliente netta non è calcolata da nessuna parte. → discende da: **assenza della posizione-cliente di prima classe**.

**Bug-3 — drift di `stato_pagamento`.** La derivazione SALDATO/PARZIALE/PENDENTE è **ri-scritta a mano in 4 procedure** (pay_rate, unpay_rate, incassa_residuo, reopen), ognuna leggermente diversa (solo unpay/reopen gestiscono PENDENTE). Stesso invariante, N implementazioni. → write-model decentralizzato.

**Bug-4 — orfani su delete.** `delete_client`/`delete_contract` non considerano wallet/receivable APERTI (Fase 3.2 §2–3). → "nuova tabella, ogni path a mano va aggiornato": identico in forma al pitfall #10.

**Bug-5 — clamp-masking.** `netto`/`residuo` clampano a 0; l'unica difesa è il guard H1 in unpay_rate. → clamp che silenziano + nessun punto unico di verifica.

**Tutti e cinque** sono istanze di: *nessun layer di transizione + nessuna posizione-cliente ⇒ invarianti ri-asseriti a mano per-path ⇒ le omissioni diventano perdita silenziosa (clampata)*. Non sono cinque bug: sono cinque facce dello stesso difetto strutturale.

---

## FASE 5 — Struttura-bersaglio + stadiazione

### 5.1 — Struttura-bersaglio minima (la gerarchia che elimina la classe)

1. **Layer di transizione + invarianti osservabili.** Una funzione pura `assert_contract_invariants(contract, *, movements?)` in `contract_state.py` che verifica I1–I4 **senza** il mascheramento del clamp (es. espone `netto_raw = versato − rimborsato` e pretende `≥ 0`; `residuo_raw` e pretende coerenza con `chiuso`). Ogni mutazione finanziaria la chiama in coda. Nel tempo, le transizioni convergono a passare per un `apply_*` comune — **incrementale**, non big-bang.
2. **`ClientPosition` come read-model di prima classe (derivato, NON tabella).** `client_position(client_id) = Σ residuo(contratti aperti) − Σ wallet APERTO + Σ receivable APERTO`, esposto in `ClientResponse`/worklist. Rende **I5 osservabile** e risponde al caso-sonda senza stato distribuito.
3. *(oltre)* wallet auto-applicabile cross-contratto = **stato distribuito → in panchina.**

### 5.2 — Fetta minima implementabile ORA (Regola d'oro: no migrazione di massa, no G1)

| # | Cosa | Perché chiude la classe | Oracolo di test | Rischio |
|---|---|---|---|---|
| **S0** | `assert_contract_invariants()` **osservabile** (pura, in `contract_state.py`), chiamata in coda a ogni mutazione, **prima log-only (warn), poi 409**. | Trasforma ogni futura perdita silenziosa (Bug-1/5) in **segnale visibile**. È la mossa a leva più alta e rischio più basso: non cambia output. | **Byte-identità** della suite attuale (aggiunge solo osservazione: i 690+ test restano verdi). | Minimo |
| **S1** | **reopen riconcilia il wallet già erogato.** In R4, se `importo_erogato>0`, l'erogato rientra nella posizione del contratto (→ `totale_rimborsato` **oppure** receivable: **decisione founder D1**), invece di essere annullato in silenzio. | Chiude **Bug-1** (l'unico vero money-bug). | Nuovo scenario in `test_contract_reopen.py` + `test_wallet_cliente.py`: *eroga parziale → reopen → la posizione resta intera* (oggi **non testato**: ecco perché è sfuggito). Suite esistente invariata. | Localizzato |
| **S2** | **Guard orfani** su `delete_client` (RESTRICT se wallet/receivable APERTO) e `delete_contract` (RESTRICT/cascade su `id_contratto_origine`/`id_contratto`), a specchio dei RESTRICT rate/credito già presenti. | Chiude **Bug-4**. | Output-invariante per i test esistenti; +2 guard-test. | Minimo |
| **S3** | **Estrai `recompute_stato_pagamento(contract)`** in `contract_state.py`; sostituisci le 4 copie inline. | Chiude **Bug-3** (rimuove un intero asse di "stesso invariante, N implementazioni"). | **Byte-identità** della suite (refactor output-invariante). | Basso |

Ordine consigliato: **S0 → S1 → S2 → S3**. S0 per primo perché rende *osservabili* gli effetti di S1/S2 e fa da rete per ogni passo successivo.

### 5.3 — In panchina (nominato, perché differirlo è corretto)

- **Transition-layer a funnel unico** (ogni mutazione attraverso un `apply_*`): churn alto sul cuore vivo, **zero nuovo comportamento**. Va fatto **incrementale dietro le asserzioni di S0**, mai come rewrite. *Se proponessi qui un rewrite del cuore finanziario, sarebbe il deliverable sbagliato.*
- **Wallet auto-spendibile cross-contratto:** stato distribuito cross-contratto; richiede il read-model `ClientPosition` + una decisione di dominio (D2). Non serve per chiudere la classe **perdita-silenziosa**. Bench.
- **`ClientPosition` materializzata (tabella):** mai — è derivabile. Se/quando serve esporla, farla come read-model calcolato. Bench.
- **Tocco a G1 (cifratura):** fuori scope, intoccabile.

### 5.4 — Decisioni di dominio da rimettere al founder (NON decise qui)

> **D1 — Wallet parzialmente erogato alla riapertura del contratto d'origine.** Quando `reopen(A)` annulla un wallet con `importo_erogato>0`, che cosa accade alla cassa **già pagata** al cliente?
>
> - **(a) Diventa un `crediti_terminazione` (receivable):** il cliente "deve indietro" l'erogato perché il contratto è di nuovo vivo. *Pro:* simmetrico, posizione intera, auditabile. *Contro:* crea un debito-cliente che potrebbe sorprendere.
> - **(b) Confluisce in `totale_rimborsato` del contratto:** l'erogato è trattato come rimborso contro il contratto riaperto → alza il `residuo()` (il cliente lo ri-paga attraverso il contratto). *Pro:* nessuna nuova entità; un solo numero. *Contro:* "rimborso" su un contratto vivo è semanticamente teso.
> - **(c) Status quo, ma esplicito + auditato (+ eventuale blocco):** il trainer "se lo tiene" (perdita), oppure `reopen` è **bloccato** quando `importo_erogato>0` finché non si gestisce. *Pro:* zero ambiguità di modello. *Contro:* attrito operativo.
>
> *(S1 implementa la scelta; oggi il codice fa silenziosamente una 4ª cosa — perde l'euro dalla posizione — che nessuno ha scelto.)*

> **D2 — Applicabilità cross-contratto del credito-cliente.** Un wallet generato dal contratto A può **ridurre il residuo** di un contratto B dello stesso cliente?
>
> - **(a) Mai (solo cash-out):** status quo, nessuno stato distribuito, più semplice.
> - **(b) Applicazione manuale ("applica credito al contratto"):** azione esplicita e auditabile, niente auto-magia. *Mediana consigliata se serve.*
> - **(c) Automatica:** stato distribuito cross-contratto — **panchina**, costo più alto.

---

## Appendice A — Contraddizioni doc↔codice (segnalate, codice vince)

1. **"reopen reconciliation CRM-grade" (BUILD_LOG/memory G8.1.1)** — il codice riconcilia il *piano rate* (`_reconcile_rate_plan`) e la cassa *legata al contratto*, **ma NON** la porzione di wallet **già erogata** (`id_contratto=None`). La "reconciliation" è **incompleta** rispetto al claim (§4.2 Bug-1).
2. **"Wallet = customer credit balance a livello cliente" (ADR-020, docstring `credito_cliente.py`, pitfall #15)** — vero per *ownership/saldo*, ma il *ciclo di vita* è contract-level (`id_contratto_origine`, annullato da `reopen(A)`). Il claim "client-level" è **metà vero** (§3.2 §1).
3. **`causale="OVERPAYMENT"` su `crediti_cliente`** — dichiarata *«predisposta — in G8.1 i guard di pagamento non producono ancora overpayment»*: **path morto** oggi (nessun produttore). Latente, da non dare per attivo.
4. **`reopen_preview` mostra `wallet_da_annullare` (conteggio)** ma **non** l'importo già erogato che andrebbe perso: la preview rassicura ("1 wallet annullato") senza segnalare i 50€ che svaniscono dalla posizione (§4.2 Bug-1).

## Appendice B — Oracoli di test esistenti (per la stadiazione)

Suite finanziaria già ricca (`tests/`), usabile come **oracolo di byte-identità** per i refactor output-invarianti (S0/S3) e da estendere per S1/S2:
`test_contract_terminate.py` · `test_contract_reopen.py` · `test_contract_settlement.py` · `test_wallet_cliente.py` · `test_credito_differito.py` · `test_contract_integrity.py` · `test_pay_rate.py` · `test_unpay_rate.py` · `test_incassa_residuo.py` · `test_residuo_convergence.py` · `test_contract_state.py` · `test_contract_history.py` · `test_rinvio_libera_credito.py` · `test_g75_cash_alignment.py` · `test_termination_schema.py` · `test_aging_report.py` · `test_financial_trend.py`.

**Gap di copertura che ha lasciato passare Bug-1:** nessun test combina *eroga parziale del wallet* → *reopen del contratto d'origine* → *verifica della posizione-cliente intera*. È esattamente lo scenario di S1.

---

*Fine audit. Zero codice modificato. Le 5 fasi precedono ogni implementazione; la fetta minima (S0→S3) è progettata per chiudere la classe di bug senza migrazione di massa e senza toccare G1.*
