# MATRICE ASSI SEMANTICI — le 4 regole su ogni asse di stato

**SSoT evergreen** (ADR-024 D-LEGGI-PER-CLASSE) · nata 2026-07-07 (G9.7.0) dai censimenti
`AUDIT_CENSIMENTO_ASSI_SEMANTICI_CASSA_2026-07-04.md` + `AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07.md`.
**Regola di manutenzione:** un asse di stato senza riga qui è un asse NON governato — il
`semantic-birth-auditor` (G9.7.5) verifica questa matrice a ogni nascita di asse/stato/derivato.

Le 4 regole (LEARNING_PROGRAMMAZIONE §Concetti dal campo, generalizzate da ADR-024):
**R1** insieme chiuso (enum/frozenset, mai literal sparsi) · **R2** interprete unico (un solo
classificatore/derivatore) · **R3** totalità fail-loud (il caso fuori-insieme o il fallback
SEGNALA, mai silenzio) · **R4** gemello di esaustività (test che diventa rosso alla nascita di un
valore nuovo non classificato). Colonne extra: **DV** derivati a video spiegabili
(D-DERIVATO-MAI-NUDO) · **CP** composizione protezioni verificata (il deadlock B1×no-re-parenting
insegna: le protezioni si esaminano anche COMBINATE).

| Asse | R1 insieme chiuso | R2 interprete unico | R3 fail-loud | R4 gemello | DV derivati a video | CP composizione |
|---|---|---|---|---|---|---|
| **Cassa: categoria→classe** | ✅ `ClasseContabile` 6 classi (`cash_categories.py`) | ✅ `classify_cash_movement` | ✅ fail-loud su celle vincolate + write-guard 422 | ✅ AC-RM-2/3 (`test_read_model_cassa`) | ✅ D-NESSUN-NETTO-NUDO (bucket /stats, sub-label card) | ✅ verifier + gate I1-I6 |
| **Denaro contratto (versato/rimborsato/storno)** | ✅ penne unica `ledger.py` | ✅ `contract_state` (residuo/netto) | ✅ invariant gate (409/log) | ✅ ancore sensore + `test_semantic_guards` | ✅ G8.4: netto mai nudo, «Saldo» ledger (ADR-019 Add.IV) | ✅ G9 FSM + Hypothesis |
| **Stati evento (6)** | ✅ `VALID_STATUSES` + FE `EVENT_STATUSES` | ✅ SSoT label FE (`EVENT_STATUS_LABELS`) | ⚠️ transizioni libere (fence solo su contabilizzato) | ✅ `test_occupazione_ssot` anti-literal | ✅ label mai-underscore (task #14 + EventsTable) | ⚠️ da esaminare in G9.7.4 |
| **Occupazione-credito** | ✅ `STATI_OCCUPAZIONE_CREDITO` | ✅ conteggi da SSoT (contracts/agenda/dashboard) | ✅ credit-guard 400 | ✅ `test_occupazione_ssot` | ✗ **D1-D3/D5: penali/rinviate invisibili → residui non spiegabili** (G9.7.3) | ⚠️ |
| **Occupazione-slot / contabilizzato** | ✅ `STATI_OCCUPAZIONE_SLOT`, `STATI_SERVIZIO_CONTABILIZZATO` | ✅ | ✅ fence 409 (ADR-023) | ✅ partizione runtime test | n/a (assi interni) | ✅ (G7.8-ter verifier) |
| **Aggancio eventi×contratto** | ⚠️ implicito (`id_contratto` nullable) | ⚠️ `_auto_assign_contract` unico MA esito non tipizzato | ✗ **B1/B5: orfano fail-silent (201 muto)** (G9.7.1) | ✗ nessun gemello (I-EVENTI in G9.7.5) | ✗ **B6: orfani invisibili** (G9.7.2) | ✗ **deadlock B1×no-re-parenting** (G9.7.2: recupero esplicito) |
| **Lifecycle contratto + money_substate** | ✅ enum SSoT `contract_state` | ✅ `evaluate_contract` | ✅ allowlist riapertura, guard update | ✅ suite vocabolario + FSM G9.3 | ✅ badge 2 assi (SPEC_VOCABOLARIO Giro 1) — ⏳ Giro 2 (rinnovi/workspace off-SSoT) | ⚠️ perimetro transizioni NON enumerato (B2/B3 → G9.7.4) |
| **Stati crediti/wallet (APERTO/SALDATO/ANNULLATO)** | ✅ costanti `STATO_CREDITO_*` (G9.4-bis.0) | ✅ `residuo_credito` SSoT | ⚠️ | ✗ **flag LOW noto: nessun gemello anti-re-inline** (G9.7.4) | ⚠️ worklist ok, breakdown minimale | ⚠️ |
| **Stati rate (PENDENTE/PARZIALE/SALDATA)** | ✅ | ✅ `recompute_stato_pagamento` (G9.1c, 4 copie→1) | ✅ INV-RATE I6 | ✅ harness + Hypothesis | ✅ badge rate + riconciliazione | ✅ (ADR-021) |
| **Crediti residui (derivato FE)** | n/a | ⚠️ **D4: `DeleteContractDialog` ricalcola inline** (G9.7.3/4) | n/a | ✗ guard FE copre solo denaro (G9.7.4) | ✗ vedi occupazione | n/a |

**Legenda gap aperti (tutti → gate G9.7):** ✗ = AC del blocco (B/D dall'audit 2026-07-07) ·
⚠️ = presidio parziale, verifica nel gate indicato. A blocco G9.7 chiuso questa matrice deve
essere tutta ✅/n/a oppure dichiarare il rischio residuo accettato.

**Storia:** le righe cassa/denaro sono ✅ perché OGNI cella è costata un incidente o un audit
(INC-2026-06-08, INC-2026-07-03, G7-G9). ADR-024 esiste per pagare le celle degli altri assi
PRIMA dell'incidente. Ultimo aggiornamento: 2026-07-07 (G9.7.0).
