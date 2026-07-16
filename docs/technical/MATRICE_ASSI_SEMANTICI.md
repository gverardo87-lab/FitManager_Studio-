# MATRICE ASSI SEMANTICI — le 4 regole su ogni asse di stato

**SSoT evergreen** (ADR-024 D-LEGGI-PER-CLASSE) · nata 2026-07-07 (G9.7.0) dai censimenti
`AUDIT_CENSIMENTO_ASSI_SEMANTICI_CASSA_2026-07-04.md` + `AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07.md`.
**Regola di manutenzione:** un asse di stato senza riga qui è un asse NON governato — il
`semantic-birth-auditor` (`.claude/agents/`, attivo da G9.7.5) verifica questa matrice a ogni
nascita di asse/stato/derivato.

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
| **Stati evento (6)** | ✅ `VALID_STATUSES` + FE `EVENT_STATUSES` | ✅ SSoT label FE (`EVENT_STATUS_LABELS`) | ⚠️ transizioni libere (fence solo su contabilizzato) | ✅ `test_occupazione_ssot` anti-literal | ✅ label mai-underscore (task #14 + EventsTable) | ✅ G9.7.4: destino eventi×transizioni DICHIARATO (`agenda` SOLO-lettura in `PERIMETRO_TRANSIZIONE`; reopen NOMINA gli orfani) + canary crea-su-chiuso→riapri FATTO (G9.7.5) |
| **Occupazione-credito** | ✅ `STATI_OCCUPAZIONE_CREDITO` | ✅ conteggi da SSoT — `_occupazione_breakdown_map` fonde anche le worklist dashboard (G9.7.3/D5) | ✅ credit-guard 400 | ✅ `test_occupazione_ssot` | ✅ **G9.7.3 D1-D5 (2026-07-11)**: hero 6 card + banner-equazione, sub-label «N svolte · M penali» su liste, worklist rinnovi/sospesi e sheet dashboard | ⚠️ credit-guard×escape-hatch: warning soft (G9.7.1-bis), scelta esplicita a 3 vie in P5 |
| **Occupazione-slot / contabilizzato** | ✅ `STATI_OCCUPAZIONE_SLOT`, `STATI_SERVIZIO_CONTABILIZZATO` | ✅ | ✅ fence 409 (ADR-023) | ✅ partizione runtime test | n/a (assi interni) | ✅ (G7.8-ter verifier) |
| **Aggancio eventi×contratto** | ⚠️ accettato: il `NULL` È lo stato orfano, governato da segnali (G9.7.1/2) + I-EVENTI; tipizzazione esplicita = scelta 3 vie P5 | ⚠️ accettato: `_auto_assign_contract` unico, esito ora SEGNALATO (B5 legge `id_contratto` della response); scelta esplicita in P5 | ✅ G9.7.1(-bis): pre-warning B4 + toast dedicato B5 (mai 201 muto; predicato `isPtOrfanoCreato` + vitest `event-form-warnings`) | ✅ G9.7.5: invariante **I-EVENTI** nella macchina Hypothesis dopo OGNI mossa (mai occupazione fantasma, mai orfano invisibile) + `test_i_eventi_non_vacuo` su ENTRAMBI i rami | ✅ G9.7.2: worklist `orphan-events` + alert (count==items) + badge «senza contratto» + sheet con Assegna inline | ✅ G9.7.2 recupero esplicito (`assegna-contratto` UNICA via) + G9.7.5 canary composizione (`test_canary_crea_su_chiuso_poi_riapri`: B1→segnale→B2 propone→recupero) + lente CP nell'auditor |
| **Lifecycle contratto + money_substate** | ✅ enum SSoT `contract_state` | ✅ `evaluate_contract` | ✅ allowlist riapertura, guard update | ✅ suite vocabolario + FSM G9.3 | ✅ badge 2 assi (SPEC_VOCABOLARIO Giro 1) — ⏳ Giro 2 (rinnovi/workspace off-SSoT) | ✅ G9.7.4: `PERIMETRO_TRANSIZIONE` (7 satellite con dottrina, `transitions.py`) + gemello esaustività dal metadata ORM (`test_g974_perimetro_transizioni_esaustivo`: satellite nuova/fantasma = rosso) |
| **Stati crediti/wallet (APERTO/SALDATO/ANNULLATO)** | ✅ costanti `STATO_CREDITO_*` (G9.4-bis.0) | ✅ `residuo_credito` SSoT | ⚠️ | ✅ G9.7.4: `test_g974_stati_credito_no_reinline` (classificazioni solo via `STATO_CREDITO_*`) | ⚠️ worklist ok, breakdown minimale | ⚠️ |
| **Stati rate (PENDENTE/PARZIALE/SALDATA)** | ✅ | ✅ `recompute_stato_pagamento` (G9.1c, 4 copie→1) | ✅ INV-RATE I6 | ✅ harness + Hypothesis | ✅ badge rate + riconciliazione | ✅ (ADR-021) |
| **Crediti residui (derivato FE)** | n/a | ✅ D4: `crediti_residui` sul wire, i dialog LEGGONO (G9.7.3) | n/a | ✅ G9.7.4: `test_g974_fe_no_credit_math` (totali−usati / totali−residui / conteggi stati evento vietati; allowlist aggregati-di-vista) + anti-vacuità consumo wire | ✅ vedi occupazione (G9.7.3) | n/a |
| **Prestazione singola & insoluto (nasce col blocco P, ADR-025)** | ✗ `STATI_CONTABILIZZANTI_PRESTAZIONE = {Completato}` (P-D1) + 7ª `ClasseContabile` + `PRESTAZIONE_CASH_IN` — **niente colonna stato: derivato-only per decisione** (P1) | ✗ modulo puro derivati `da_incassare`/`insoluto` (IP3) + suggeritore Q6 spiegabile (P1/P2) | ✗ penna `post_prestazione_inflow` fail-loud + IP1-IP4 in invariant gate (P1) | ✗ gemelli semantici 7 classi + Hypothesis rule asse prestazione (P1/P2/P6) | ✗ due viste W7 (per-prestazione + Portafoglio) + worklist insoluti, mai nudo (P4/P5) | ✅ **birth-review P0 FATTA 2026-07-08**: CP-1..CP-4 foldati in spec (delete_client RESTRICT · guard assegna-contratto · soppressione auto-assign · cascade delete-evento); CP-5/CP-6 verificate OK (reopen×compensazione via R2-bis; Rinviato-prepagata ha uscite) |

**Legenda gap aperti (→ gate G9.7 o blocco P):** ✗ = AC del blocco indicato (B/D dall'audit
2026-07-07; P1..P6 da `SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md`) · ⚠️ = presidio parziale,
verifica nel gate indicato. A blocco chiuso le sue celle devono essere ✅/n/a oppure dichiarare il
rischio residuo accettato.

**Storia:** le righe cassa/denaro sono ✅ perché OGNI cella è costata un incidente o un audit
(INC-2026-06-08, INC-2026-07-03, G7-G9). ADR-024 esiste per pagare le celle degli altri assi
PRIMA dell'incidente. La riga «prestazione singola» è la PRIMA nata col protocollo completo
(riga in matrice + birth-review PRIMA del codice, ADR-024 D-BIRTH-AUDITOR).
Ultimo aggiornamento: 2026-07-16 (G9.7.5 chiuso: riga «aggancio eventi×contratto» R3/R4/DV/CP → ✅,
R1/R2 = rischio residuo ACCETTATO con puntatore P5; canary stati-evento FATTO; auditor attivo).
