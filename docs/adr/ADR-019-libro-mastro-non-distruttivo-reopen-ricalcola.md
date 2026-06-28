# ADR-019 — Libro mastro non-distruttivo + `reopen` "ricalcola-e-instrada" (emenda G7.4 reopen-inverso-esatto)

- Date: 2026-06-28
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi senior e bridge code-grounded di Claude Code
- Related upgrade ID: programma post-G7 "integrita' contabile + completamento bilaterale" (blocco reopen-recompute; il wallet e' ADR-020)
- Audit fondante: `docs/operations/AUDIT_REOPEN_SCENARIOS_2026-06-28.md`
- Emenda: la decisione **G7.4 "reopen = inverso esatto / round-trip byte-identico"** (ADR-018 / SPEC_TERMINAZIONE_BILATERALE)
- Correlati: `ADR-016` (asse EROGATO), `ADR-018` (terminazione bilaterale); modello vivo `FINANCIAL_DOMAIN_MODEL.md`; **ADR-020** (wallet cliente, instrada il credito)

## Context

Dopo G7.9/G7.10, `reopen_contract` esegue **sempre, incondizionatamente**, lo stesso reverse: soft-cancella i
`CashMovement` di terminazione (gambe **C** rimborso USCITA, **C-bis** incasso conguaglio ENTRATA), annulla i
receivable (**C-ter**), azzera lo storno, ripristina le rate, riapre. Unica guardia: `if not chiuso -> 400`.

L'audit `AUDIT_REOPEN_SCENARIOS_2026-06-28.md` rivela che il reverse cieco e' **sbagliato in piu' scenari**:
- soft-cancella movimenti di cassa **fiscalmente rilevanti** (non esiste layer documentale: il `CashMovement`
  *e'* il dato fiscale), **scavalcando** la protezione del mastro (`delete_movement` vieta — 400 — di
  eliminare un movimento con `id_contratto`) e **mutando periodi gia' dichiarati**;
- fa **sparire reddito realmente incassato** (un conguaglio pagato dal cliente) come se non fosse mai entrato;
- ignora le **dipendenze a valle** (contratto rinnovato; in futuro: wallet speso).

Finding centrale: **`reopen` e' sovraccaricato** — un verbo per tre operazioni distinte (undo immediato /
storno-correttivo / riattivazione commerciale). La via giusta non e' "compensare ovunque" ma un **principio
unico** (origine: osservazione del founder, convergente con i best CRM aziendali).

## Decision Drivers

- **Integrita' di periodo / correttezza fiscale**: i report dei mesi passati non devono cambiare per un'azione
  di oggi; reddito incassato non puo' sparire.
- **Protezione del mastro coerente**: se `delete_movement` vieta di cancellare scritture contrattuali, nemmeno
  `reopen` deve farlo di nascosto.
- **Collassare i casi-speciali in una regola** (meno superficie, meno bug).
- **Software che propone** per l'ambiguita' residua (controllo, non blocco cieco).
- **Convergenza con lo stato dell'arte** (Stripe/Chargebee/QuickBooks: ledger non-distruttivo, reactivation che
  ricomputa, customer credit balance).

## Considered Options

### Option A — Status quo (reverse: soft-delete di tutto)
- Contro: muta periodi dichiarati; reddito incassato sparisce; scavalca la protezione del mastro; un solo
  trattamento per scenari diversi.

### Option B — Scritture compensative datate (append-only)
- Pro: mastro append-only, integrita' di periodo.
- Contro: "reverte" comunque, con macchinari (categoria-storno da escludere in tutti gli aggregati — di nuovo
  la superficie G7.5); piu' complesso del necessario per il caso base di reopen.

### Option C — "Ricalcola-e-instrada": la cassa non si tocca (scelta)
- `reopen` **non tocca** i `CashMovement` (ne' delete ne' compensa nel caso base): le scritture restano,
  datate. Toglie lo storno + annulla i receivable non-cash + **ricalcola** `residuo` (net-aware). Il credito
  (overpayment) **esce** nel wallet (ADR-020). Per le dipendenze a valle, **propone**.
- Pro: il piu' semplice; integrita' di periodo **automatica** (nulla viene cancellato); converge con i best CRM.
- Contro: **emenda** la gamba C-bis/C-ter di reopen shippata in G7.9/G7.10 (delete della cassa); tocca l'SSoT
  `residuo()` (net-aware); i test "round-trip byte-identico" cambiano.

## Decision

**Option C.** Decisioni founder vincolanti (2026-06-28):

1. **D-CASSA-IMMUTABILE** — `reopen` **non cancella** scritture di cassa. Le `ENTRATA`/`USCITA` di terminazione
   **restano** (fatti datati, fiscalmente intoccabili). Un'eventuale restituzione/recupero di denaro e' un
   **movimento nuovo esplicito**, mai una cancellazione.
2. **D-RICALCOLA** — `reopen` toglie lo storno (`quota_stornata=0`) + annulla i receivable non-cash + **ricalcola**
   `residuo` dallo stato di cassa reale. La cassa di terminazione che resta diventa semplicemente *pagamento/
   rimborso sul contratto riaperto*.
3. **D-RESIDUO-NETTO** — `residuo = prezzo − netto_incassato − quota_stornata` (`netto = versato − rimborsato`),
   net-aware. Backward-compatible (`rimborsato=0` -> identica al lordo attuale). Tocca l'SSoT `contract_state.residuo()`.
4. **D-INSTRADA** — al ricalcolo: **debito** del cliente -> resta nel **contratto** (`residuo`); **credito**
   (overpayment / posizione a favore del cliente) -> esce nel **wallet** (ADR-020). Il contratto non tiene
   residuo negativo (il clamp `max(...,0)` non scarta piu' in silenzio: l'eccedenza va al wallet).
5. **D-PROPONE** — le dipendenze a valle (wallet gia' speso su altro contratto; contratto gia' rinnovato) NON
   si gestiscono in automatico: `reopen` **classifica** lo stato e **propone** l'azione corretta all'utente
   (mai blocco cieco, mai azione silenziosa). Coerente con "proposta != obbligo".
6. **D-STAGING** — il **principio** si adotta subito come stella polare; il **build si stadia**: prima la fetta
   economica (reopen-recompute net-aware + UX-propone + wallet *tracciato e applicato a mano*); il wallet
   **auto-spendibile cross-contratto** (stato distribuito) **dopo**, su domanda reale.

**Invarianti che NON cambiano**: asse EROGATO (ADR-016), `Rinviato` fuori occupazione (ADR-017), bilateralita'
(ADR-018), Strada B (`totale_versato` lordo immutabile, netto derivato), `residuo == 0 ⟺ saldato`. Le scritture
compensative restano lo strumento per la correzione **diretta** di un movimento errato — concern separato; per
`reopen` il ricalcolo basta.

## Consequences

- **Positive**: integrita' di periodo/fiscale automatica (nulla cancellato); nessun reddito incassato che
  sparisce; protezione del mastro non piu' scavalcata; la matrice di scenari (S1/S2/S3/S6/S7) collassa su un
  trattamento unico; `reopen` diventa **sicuro** anche a settimane di distanza; convergenza con i best CRM.
- **Negative / costo**: **emenda codice fresco** (le gambe C-bis/C-ter di reopen di G7.9/G7.10 — delete della
  cassa — vengono sostituite dal ricalcolo); `residuo()` net-aware tocca l'SSoT load-bearing (~15 consumer, ma
  backward-compatible); i test "round-trip byte-identico" cambiano da «movimenti spariti» a «movimenti fermi,
  colonne nette tornano corrette»; va aggiunta la classificazione di scenario + UX-propone per S4/S5.
- **Follow-up**: spec di dettaglio (blocchi); a implementazione aggiornare `FINANCIAL_DOMAIN_MODEL.md` (residuo
  net-aware, reopen-recompute), `api/CLAUDE.md`, `BUILD_LOG.md`. Il wallet e' **ADR-020**.

## Rollback / Exit Strategy

`residuo` net-aware e' additivo/backward-compatible (rollback = tornare al lordo, ma riapre il bug del
rimborso ignorato). Reopen-recompute **sostituisce** le gambe delete: rollback = ripristino delle gambe C-bis/
C-ter (delete) — riapre pero' i problemi di integrita' fiscale di periodo. Nessuna migrazione DB in questo ADR
(il wallet, con la sua tabella, e' ADR-020). Nessun dato cancellato dalla nuova logica (e' il punto).

## Supersedes / Superseded By

- **Emenda G7.4** ("reopen = inverso esatto / round-trip byte-identico", ADR-018 / SPEC_TERMINAZIONE_BILATERALE):
  `reopen` non e' piu' "lo stato torna byte-identico al pre-terminate" ma "il contratto torna **corretto**
  rispetto alla cassa reale" (true-to-ledger). L'asse EROGATO, la bilateralita' e Strada B restano invariati.
- **Estende ADR-016/018**. Instradamento del credito -> **ADR-020**.
- Superseded by: —

## Addendum 2026-06-28 — G8.1.1 (reopen reconciliation + transparency)

Il test del flusso da parte del founder, dopo G8.1 shippato, ha confermato che il **calcolo** è
corretto ma il **contorno** (presentazione + piano rate + guard di cap/stato) non si era allineato al
modello net-aware/non-distruttivo. Tre conseguenze del principio, **non nuove decisioni** — il loro
mancato recepimento confonde l'utente:

- **D-CASSA-VISIBILE (F1, conseguenza di D-CASSA-IMMUTABILE).** Se la cassa di terminazione **resta**,
  deve essere **visibile** sul contratto: il dettaglio espone lo storico dei `CashMovement` a livello
  contratto (acconto, rimborso, conguaglio; `id_contratto` set, anche con `id_rata=None`), così il
  `residuo` net-aware **riconcilia a vista**. Senza, un residuo guidato da una cassa invisibile sembra
  sbagliato (oggi `get_contract` espone solo i movimenti legati a una rata via `id_rata`).
- **D-RECONCILIA-RATE (F2, estende D-RICALCOLA al piano rate).** `reopen` non ricalcola solo il
  `residuo`: **riconcilia anche il piano rate** al residuo ricalcolato. Decisione founder = **riallineo
  automatico** — le rate restaurate eccedenti vengono **tagliate cronologicamente** (l'ultima a cavallo
  ridotta, le successive azzerate/eliminate; una PARZIALE mai sotto `importo_saldato`); una
  sotto-copertura lascia il resto come **"da pianificare"** (mai una rata-fantasma). L'inverso-esatto
  M1/G7.7 ("ripristina le rate identiche") assumeva reopen = inverso esatto: **non vale più** sotto il
  non-distruttivo (quando la cassa resta, il residuo ripristinato ≠ pre-terminate).
- **D-NET-AWARE-OVUNQUE (F3/F4, completa D-RESIDUO-NETTO).** Ogni guard/stato che esprime "quanto è
  dovuto / saldato" deriva dal SSoT net-aware, **mai** dal LORDO `totale_versato`: `_cap_rateizzabile`
  usa `netto_incassato`; `stato_pagamento = SALDATO ⟺ residuo() ≤ 0.01` (non `versato ≥ prezzo`). Senza,
  `pay_rate` (già net) e `_cap`/auto-close (lordo) **si contraddicono**, e un riaperto-con-rimborso può
  marcare SALDATO/auto-close con `residuo() > 0` (violazione di `residuo == 0 ⟺ saldato` su CHIUSO).

**Estensione CRM-grade (F5/F6, follow-up founder 2026-06-28).** La trasparenza diventa standard CRM —
D-CASSA-VISIBILE si concretizza in due timeline sul dettaglio contratto: **(F5) storico cassa unificato**
(acconto + pagamenti rata + **rimborsi** − + **conguagli** +, con segno e **saldo netto progressivo** +
footer di riconciliazione `lordo − rimborsato = netto · residuo`); l'erogazione wallet (`id_contratto=None`,
cassa a livello CLIENTE) resta sul profilo cliente. **(F6) storico stato/attività** (Creato · Terminato
[esito + importo + motivo] · Riaperto · Saldato), da `audit_log` via `GET /contracts/{id}/history` (eventi
**curati**, read-only). Dato **già registrato** (`CashMovement` `id_contratto`; `audit_log`
`entity_type='contract'` + `log_contract_lifecycle_transition`) → **surfacing, non nuovo modello**. Eventi
curati scelta founder; audit grezzo resta in `/movements/audit-log`.

**Invarianti immutati:** `residuo == 0 ⟺ saldato`, cassa-immutabile, asse EROGATO (ADR-016), Strada B.
Dettaglio + AC in `SPEC_INTEGRITA_CONTABILE_E_WALLET.md §14` (F1–F4 §14.1-14.5, F5/F6 §14.6). È **hardening**
(completamento del recepimento del principio), non un nuovo blocco: **G8.1.1**.

**Stato implementazione (2026-06-28): ✅ IMPLEMENTATA.** F2 (`_reconcile_rate_plan` in `reopen`),
F3 (`_cap_rateizzabile` net-aware), F4 (`is_saldato()` SSoT in `pay_rate`/`unpay_rate`/`incassa_residuo`),
F1 (`get_contract` espone `movimenti` = tutti i `CashMovement` `id_contratto`), F5 (FE timeline cassa con
saldo progressivo, tab "Storico" del dettaglio) + F6 (`GET /contracts/{id}/history` eventi curati +
`_curate_contract_event` con dedup delle companion lifecycle + FE timeline stato). Suite **691** verde,
ruff + grep-guard ADR-019 + next build verdi. AC 1-10 (`SPEC §14`/§14.6) coperti da
`test_contract_state.py` · `test_contract_reopen.py` (F1+F2) · `test_wallet_cliente.py` (confine wallet) ·
`test_contract_history.py` (F6).

**Follow-up F2/F3 (2026-06-28, test di flusso del founder — contratto Garavelli):** un rimborso rende
`netto < Σ importo_saldato` (la cassa netta scende sotto i pagamenti-rata LORDI, Strada B), e il piano rate
restava ancorato al lordo mentre `residuo()` è net-aware → sotto-coperto del rimborso (residuo 770, rate 733).
Due conseguenze di **D-NET-AWARE-OVUNQUE** + **D-RECONCILIA-RATE**, non nuove decisioni:
- **F3-bis (cap):** `_cap_rateizzabile` aveva un clamp `max(0, netto − saldato)` che ingoiava il rimborso →
  `cap = prezzo`, spazio 0 → impossibile ri-rateizzare il rimborsato (incoerente con `residuo()` e
  `generate_payment_plan`, già net-aware). **Tolto il clamp**: un acconto negativo è corretto e load-bearing,
  alza il cap a `prezzo + rimborso − storno`. Inerte con `rimborsato==0`.
- **F2-bis (reopen auto-copertura, scelta founder):** `_reconcile_rate_plan` gestiva solo l'eccedenza
  (taglio); la **sotto-copertura** era no-op silenzioso ("da pianificare"). Ora copre **solo il RIMBORSO che
  resta** (`min(ammanco, totale_rimborsato)`) — l'unico € che il reopen ha aggiunto al residuo e che il
  piano ripristinato non copre — assorbendolo nell'ULTIMA rata pendente esistente (mirror del taglio). **MAI
  fabbrica una rata** né copre oltre il rimborso: l'eventuale residuo "da pianificare" originale del trainer
  resta tale (es. CONSUNZIONE/storno-puro senza pendenti → residuo torna "da pianificare" com'era; una rata
  fabbricata consumerebbe lo spazio-piano e bloccherebbe `update_rate` — regressione intercettata da `test_m2`).
Invarianti immutati (cassa-immutabile, `residuo==0 ⟺ saldato`, Strada B). Test:
`test_contract_reopen.py::test_f2_reopen_copre_ammanco_da_rimborso` + `::test_cap_rateizzabile_net_aware_con_rimborso`.

## Addendum 2026-06-28 (II) — G8.2-prep: la fotografia netta PER-CONTRATTO + chiusura D1 (forma-d)

Audit fondante: `docs/technical/AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI_2026-06-28.md`. L'audit ha
confermato che il **read-model è già centralizzato** (`contract_state.py`) ma il **write-model è
decentralizzato** (ogni transizione re-asserisce a mano gli invarianti, nessun punto unico, i clamp
`max(0,…)` silenziano le violazioni), e ha trovato un **money-bug latente (Bug-1)**: `reopen` annullava il
wallet **incondizionatamente** senza riassorbire la cassa già **erogata** (USCITA `id_contratto=None`, fuori
da `totale_rimborsato`) → quegli euro **sparivano dalla posizione** del contratto riaperto (cassa nel mastro
intatta, *attribuzione* cliente↔contratto persa). Lo scenario `eroga-parziale → reopen` non era coperto da test.

**Decisione founder D1 — CHIUSA, forma (d) "fotografia netta":** il `reopen` **NON riavvolge** il pregresso.
Al reopen scatta la **fotografia netta** della posizione cliente↔contratto e quella diventa il **punto di
partenza** del contratto riaperto. Rimborso erogato, conguaglio incassato, wallet erogato sono **termini della
stessa somma**, non casi speciali da ricollocare per-provenienza (modello billing-leader: ledger immutabile,
posizione **ricalcolata**, credito **letto** non riavvolto). Confine di questo giro: la fotografia è
**PER-CONTRATTO**; la posizione-cliente intera è elevazione successiva (**G8.2**, in panchina).

Conseguenze del principio (non nuove decisioni — completano D-CASSA-IMMUTABILE / D-RICALCOLA / D-INSTRADA):

- **D-FOTOGRAFIA-NETTA (chiude Bug-1).** Al `reopen`, l'erogato dei wallet annullati (`Σ importo_erogato`)
  viene **riassorbito** in `totale_rimborsato` (gamba **R2-bis**) → rientra nel `residuo()` net-aware **per
  costruzione** (`residuo = P − (versato − rimborsato) − 0`), non come ramo speciale. La **cassa NON si tocca**
  (le USCITA wallet restano `id_contratto=None`, datate): il fold è **ri-attribuzione gestionale** della
  posizione (mandato dell'audit: riattribuire/ricalcolare la posizione è lecito, non riscrive documenti
  fiscali). `reopen-preview` **dichiara** l'importo che rientra (`wallet_erogato_riassorbito` + messaggio
  «il cliente ha già riavuto €X, che torna dovuto»), mai silenzioso (D-PROPONE).
- **Ancora del rimborso raffinata (I5).** `totale_rimborsato == Σ USCITA RIMBORSO[id_contratto] + Σ erogato
  wallet RIASSORBITO` (wallet ANNULLATO nati dal contratto). La forma letterale (solo `id_contratto`) vale
  finché nessun wallet è stato riassorbito; il fold la estende col secondo addendo.
- **Read-model + checker osservabile.** `contract_state.posizione_netta_contratto(contract, crediti_cliente)`
  (pura, `netto = versato − rimborsato − Σ erogato wallet VIVI`) è il **gradino** che abilita G8.2 senza
  riscrittura. `contract_state.assert_contract_invariants(...)` (pura) verifica I1/I4/**I5** **senza** il
  mascheramento dei clamp; in `reopen` è cablata **log-only** (`_log_invariant_violations`, «predisposta per
  409»). Rete strutturale: harness di proprietà `tests/test_financial_invariants_harness.py` (invariante ×
  transizione), rosso su Bug-1 prima del fix.
- **Patch strutturali (audit).** `delete_client`/`delete_contract` → RESTRICT su posizione aperta
  (wallet/receivable APERTO; Bug-4: prima orfanava la posizione). Estratto
  `contract_state.recompute_stato_pagamento()` = unica derivazione SALDATO/PARZIALE/PENDENTE (Bug-3:
  4 copie inline, byte-identico).

**D2 — APERTA, in panchina:** wallet auto-spendibile **cross-contratto** (un credito di A applicabile a B) =
stato distribuito. Opzioni (a) mai/solo-cash-out · (b) applicazione manuale · (c) automatico — **decisione del
founder** a domanda reale. Vedi `SPEC_INTEGRITA_CONTABILE_E_WALLET.md §15`.

**Stato implementazione (2026-06-28): ✅ IMPLEMENTATA (G8.2-prep).** Suite **711** verde; `ruff api/` +
grep-guard ADR-016/017/018/019 + `tsc --noEmit` (FE) verdi. AC in `SPEC §15`; test:
`test_financial_invariants_harness.py` (harness) · `test_contract_reopen.py::test_reopen_riassorbe_wallet_erogato`
(fix Bug-1: acconto 800/reso 200/wallet 600/eroga 250 → reopen → `totale_rimborsato=250`, `residuo()=450`) ·
`test_wallet_cliente.py` (delete-guard Bug-4). **Invarianti immutati:** cassa-immutabile, `residuo==0 ⟺ saldato`,
asse EROGATO (ADR-016), Strada B. È **hardening del principio ADR-019** (chiude la classe «perdita silenziosa»),
non un nuovo blocco.
