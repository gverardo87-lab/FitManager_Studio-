# ADR-023 — Temporal fence: la storia CONTABILIZZATA di una liquidazione è immutabile; il varco è `reopen`

**Stato: accepted** (ratifica founder 2026-07-03, Opzione C) · **Blocco: G7.8-ter** ·
Spec: `docs/specs/SPEC_TEMPORAL_FENCE_EVENTI_LIQUIDATI.md`

## Context

Il lato DENARO del dominio è già completamente protetto nel tempo (H1 `unpay`→409 su terminato, M2
`update_rate`, cap B-ter, cassa append-only ADR-019). Il lato EVENTI no: `update_event` (cambio `stato`,
con la sola eccezione del Bouncer 4 `Completato→Rinviato`) e `delete_event` non guardano
`contract.chiuso`. Su un contratto TERMINATO — il cui conguaglio (rimborso/storno/receivable/wallet) è
stato calcolato sulla base delle sedute contabilizzate (Completato + penali G7.8-bis) — la storia può
mutare in silenzio: la reopen-allowlist (G7.2) tiene il contratto chiuso, quindi nessun errore visibile;
il mismatch resta latente ed esplode alla riapertura (reconcile/settlement su una storia diversa da
quella liquidata) o nel confronto col denaro già mosso. Con G7.8-bis il rischio si è allargato: anche
`No_Show→Cancellato` sposta euro di conguaglio, non solo crediti.

**Ricerca competitor (2026-07-03, fonti ufficiali: Mindbody, WellnessLiving, Zen Planner/Daxko,
Glofox/ABC, Vagaro)** — cinque prodotti indipendenti convergono sulle stesse leggi:
L1 presenze riscrivibili / denaro no (confine = settlement); L2 i due assi non si ricalcolano mai a
vicenda automaticamente; **L3 la liquidazione congela, non ricalcola** (Mindbody blocca il void con
visite associate; Booker vieta il revert dello stato post-fee); L4 correzione forward-only
(QuickBooks closing-date + password + Exceptions-report; Xero lock-dates role-gated; Stripe: Charge
immutabile nei campi finanziari, Refund = oggetto NUOVO che referenzia l'originale; Trainerize: crediti
"non-refundable and non-revocable", correzione = consumazione compensativa; PushPress: credito assegnato
"cannot be removed directly — cancel the appointment"); L5 la finestra di correzione sta PRIMA del
denaro. Il pattern del varco maturo è ovunque **esplicito, role-gated e AUDITATO** (QBO logga ogni
eccezione al fence) — il nostro `reopen` ha già tutte e tre le proprietà. Dettaglio + citazioni:
`docs/archive/RICERCA_COMPETITOR_TEMPORAL_FENCE_2026-07-03.md`.

## Decision

- **D-TF-BASE — Ciò che è entrato nel conguaglio non si riscrive.** Nuovo asse SSoT
  `contract_state.STATI_SERVIZIO_CONTABILIZZATO = {"Completato"} ∪ STATI_PENALE` (la base di
  `compute_settlement`, G7.9 + G7.8-bis). Su un contratto **chiuso e non auto-riapribile**
  (`chiuso ∧ NOT puo_auto_riaprire`, cioè motivo `TERMINAZIONE_*`/`CONSUNZIONE`/`NULL` legacy — riuso
  della FSM G9.3): (a) un cambio di `stato` evento è **vietato (409)** se lo stato di partenza O di
  arrivo è contabilizzato; (b) il **delete** di un evento contabilizzato è **vietato (409)**.
- **D-TF-PULIZIA — Il fence protegge la base, non la agenda.** Le mutazioni che NON toccano la base
  restano libere sul contratto terminato: `Programmato → Cancellato/Rinviato` (pulizia delle
  prenotazioni orfane sopravvissute al terminate) e il delete di eventi non-contabilizzati. Anche
  date/titolo/note restano liberi (non alterano la base; L1 dei competitor).
- **D-TF-VARCO — `POST /reopen` è l'unico varco.** Riaperto il contratto (non-distruttivo, ricalcola —
  ADR-019), la storia torna pienamente editabile; alla ri-terminazione il conguaglio si ricalcola sulla
  storia corretta. Il 409 indirizza esplicitamente lì (microcopy). È il pattern "reversibilità =
  ricostruzione esplicita" (Zen Planner Undo-Drop), che il dominio già possiede.
- **D-TF-LEGACY — I chiusi `motivo NULL` sono dentro il fence.** Nessuna liquidazione da proteggere, ma
  stessa deliberatezza: una chiusura manuale/legacy non si erode da un edit-evento; si riapre e si
  corregge. (Coerente con la reopen-allowlist: NULL non si auto-riapre.)
- **D-TF-COMPLETAMENTO — I chiusi `COMPLETAMENTO` restano fuori dal fence.** Lì l'auto-reopen
  simmetrico payment/credit-driven è il comportamento corretto già esistente e non c'è conguaglio.

## Consequences

Chiude l'ultima porta temporale del dominio: denaro (già fenced) + storia contabilizzata (questo ADR) +
varco unico (`reopen`). `create_event` su chiuso era già 400. Asse DENARO invariato (solo guard, zero
calcoli nuovi). FE: il 409 arriva ai toast via `extractErrorMessage`; disabilitazioni proattive in UI =
opzionali, non bloccanti (G8.4+). Estende ADR-017/ADR-019; nessun supersede.

## Rollback / Exit Strategy

Due guard puri in `agenda.py` + una costante SSoT: rollback = rimozione dei guard. Nessuno schema,
nessuna migrazione, nessun dato alterato.
