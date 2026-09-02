# ADR-016 — Asse EROGATO canonico per il recesso, forfeiture delle prenotate, riconciliazione display↔rimborso

- Date: 2026-06-26
- Status: accepted
- Deciders: Giacomo Verardo (AVGV Technologies); analisi e proposta di Claude Code (audit senior crediti/contratti/rimborso)
- Related upgrade ID: G7.7 (remediation audit)
- Audit di provenienza: `docs/archive/operations/AUDIT_CREDITI_RIMBORSO_2026-06-26.md`
- Correlati: `ADR-014` (gestione finanziaria), `ADR-015` (funnel rinnovi/retention); modello vivo: `docs/technical/FINANCIAL_DOMAIN_MODEL.md` (v1.3), `docs/technical/TASSONOMIA_FINANZIARIA.md` (v1.2); catena G7.0→G7.6 (`SPEC_G7.0_SCHEMA_TERMINAZIONE.md`)

## Context

La catena di terminazione anticipata (G7.0→G7.6) calcola **ogni** importo di recesso — rimborso e
storno — sulla base del **servizio reso**, cioè le sole sedute `Completato` (asse **EROGATO**):
`_count_sedute_erogate` → `valore_servizio_reso` → `compute_settlement`. La firma di `compute_settlement`
rende l'asse OCCUPAZIONE (sedute Event PT che impegnano il monte-crediti — **definizione precisata da
`ADR-017`**: `Programmato + Completato`, con `Rinviato` **escluso** perché libera il credito)
**strutturalmente irraggiungibile** dal calcolo monetario.

L'audit senior del 2026-06-26 (trigger: segnalazione del trainer reale Chiara su un presunto "errore
logico" nei crediti residui usati per il rimborso) ha verificato su `crm.db` reale (35 contratti, 2
terminazioni) che **il calcolo è corretto**: zero violazioni di non-negatività, tetto e conservazione
del ledger. La divergenza percepita — "crediti residui 4, ma rimborso su 2 sedute" — è **by-design**:
una seduta solo *prenotata* (Programmato) occupa uno slot ma non è servizio reso, quindi non aumenta il
rimborso (forfeiture).

**Il problema non è la matematica, è che la decisione vive solo implicitamente** nel codice e nella
microcopy del dialog di terminazione (G7.5c). Conseguenze:
- nessun documento la congela → un refactor della formula potrebbe spostarla su OCCUPAZIONE senza che
  un test/guardia lo intercetti (over-rimborso del prenotato-non-erogato);
- lista contratti, scheda dettaglio e profilo cliente mostrano l'asse OCCUPAZIONE (`crediti_residui`)
  **senza affiancare** l'EROGATO → il trainer si forma un modello mentale errato *prima* di aprire la
  terminazione (radice della percezione di Chiara, finding L1);
- consumatori secondari **ricalcolano** lo stato off-SSoT (`ContrattiTab` collassa Sospeso→Attivo,
  finding M3) — esattamente ciò che SPEC_VOCABOLARIO Giro 2 vuole eliminare.

## Decision Drivers

- **Determinismo** (regola #6): un importo che muove cassa deve avere una base esplicita, auditabile e
  non ambigua. "Servizio reso" è verificabile; "capacità occupata" non è un valore economico.
- **Nessuna perdita silenziosa / nessun guadagno silenzioso**: né il cliente paga il non-erogato, né
  incassa il prenotato. La forfeiture va dichiarata, non subìta.
- **SSoT unico** (`contract_state.py`): un solo punto deriva stato e residuo; i consumatori **leggono**.
- **Coerenza display↔denaro (I6)**: due viste dello stesso contratto non devono divergere.

## Considered Options

### Option A — Lasciare la decisione implicita (status quo)
- Pro: zero lavoro.
- Contro: nessuna barriera contro un refactor che sposta la valorizzazione su OCCUPAZIONE; l'off-SSoT
  recompute continua a proliferare; la percezione di Chiara resta irrisolta.

### Option B — Valorizzare (in tutto o in parte) sull'asse OCCUPAZIONE
- Pro: il numero a schermo (`crediti_residui`) coinciderebbe col rimborso → nessuna "sorpresa".
- Contro: il cliente verrebbe rimborsato per sedute **mai erogate** ma solo prenotate → over-rimborso
  strutturale; premia il no-show; rompe il nesso rimborso = servizio non goduto. Inaccettabile.

### Option C — Ratificare EROGATO canonico + forfeiture + riconciliazione obbligatoria (scelta)
- Pro: congela la decisione corretta; abilita una guardia automatica anti-regressione; chiude la
  divergenza display risolvendo la radice della percezione (riconciliazione ovunque, non solo nel dialog).
- Contro: introduce una guardia di tetto su `unpay`/`reopen`/`update_rate` e un piccolo costo UI di
  riconciliazione da mantenere.

## Decision

**Option C.** Si ratificano tre decisioni vincolanti, finora solo implicite:

1. **Asse canonico EROGATO.** Il valore del servizio reso — e quindi **ogni** rimborso/conguaglio da
   recesso — si calcola **esclusivamente** sulle sedute `Completato`. L'asse OCCUPAZIONE pilota *solo*
   occupazione, auto-close, credit/delete guard e display crediti — **mai** un importo in euro. La
   *definizione* dell'asse OCCUPAZIONE (quali stati Event lo compongono) è precisata da `ADR-017`, che
   emenda questo punto: `Programmato + Completato`, con `Rinviato` **escluso** (il rinvio libera il
   credito spendibile). L'asse EROGATO e la barriera strutturale **non** cambiano.
   `compute_settlement` mantiene una firma che non accetta grandezze di occupazione (**barriera
   strutturale**, non solo convenzione).

2. **Forfeiture delle prenotate.** Le sedute solo prenotate (Programmato) **non riducono** il rimborso:
   sono capacità impegnata, non servizio reso. È disegno intenzionale, non un difetto.

3. **Riconciliazione obbligatoria (I6).** Ovunque sia mostrato l'asse OCCUPAZIONE (`crediti_residui`),
   l'UI deve rendere **riconciliabile** l'asse EROGATO (sedute completate) come base del rimborso — non
   solo nel dialog di terminazione. È **vietato** il recompute off-SSoT degli stati lifecycle/money nei
   consumatori secondari: si **legge** da `evaluate_contract`/`contract_state`, non si ricalcola.

### Corollari operativi ratificati (audit §4, decisioni founder 2026-06-26)

- **Tetto del recesso come invariante enforced, non solo emergente.** `unpay_rate`, `reopen`,
  `update_rate` diventano soggetti all'invariante `totale_rimborsato ≤ totale_versato` e alla simmetria
  dell'inverso. In particolare: **`unpay_rate` su un contratto terminato (con storno/rimborso) è
  rifiutato (409)** — il path canonico è `POST /reopen` (riallinea atomicamente), poi la revoca.
  *Reject*, non *reroute*: un solo inverso esplicito, zero magia nascosta.
- **`reopen` inverso esatto.** Il ripristino delle rate soft-eliminate dal terminate avviene tramite un
  **marker** (`rate.chiusa_da_terminazione`), non con un select aperto su `deleted_at != None` (che
  resusciterebbe rate eliminate per altre ragioni).
- **Indicatore leggero per il COMPLETAMENTO-prenotato.** Sui contratti chiusi `COMPLETAMENTO` con
  erogato < crediti, l'UI espone un campo **derivato additivo** ("N sedute prenotate non erogate alla
  chiusura" + hint "rimborso via Riapri→Termina"), **senza** introdurre un nuovo sotto-stato nell'enum
  (espansione di vocabolario differita a Giro 2).
- **Grep-guard "euro-da-crediti"** in `tools/scripts/check-all.sh`: blocca l'uso di `crediti_residui`/
  occupazione come addendo monetario fuori da `contract_settlement.py` (con allowlist), a difesa della
  barriera strutturale del punto 1.

## Consequences

- **Positive**: la decisione corretta è congelata e difesa da una guardia automatica; `unpay`/`reopen`/
  `update_rate` rientrano sotto l'invariante di tetto (chiude il money-bug H1 e i debiti-SSoT M1/M2); la
  radice della percezione di Chiara è risolta (riconciliazione display↔erogato ovunque, non solo nel
  dialog); fine del recompute off-SSoT nei consumatori secondari (M3).
- **Negative**: un marker nullable su `rate` (migrazione + schema_sync auto-add) per la precisione del
  reopen; una componente UI di riconciliazione da mantenere; una voce in più in `check-all.sh`.
- **Follow-up actions** (blocco G7.7, `IMPL_PLAN_FINANCIAL_REALIGN.md`):
  - R1 guardia `unpay_rate` + sentinella tetto · R2 guard `chiuso` + cap su `update_rate` · R3 marker
    `reopen` · R4/R5 riconciliazione display (backend + frontend, ContrattiTab ai badge SSoT) · R6
    igiene (L2 vocabolario CONSUNZIONE, L3 test, grep-guard).
  - A implementazione completata: aggiornare `api/CLAUDE.md`, `FINANCIAL_DOMAIN_MODEL.md`, `BUILD_LOG.md`.

## Rollback / Exit Strategy

Le viste di riconciliazione sono letture aggregate: rimuoverle non tocca i dati. L'unico stato
persistente nuovo è il marker `rate.chiusa_da_terminazione` (nullable, default-safe) — in caso di
rollback resta un dato inerte ignorato; il reopen tornerebbe al comportamento G7.4 (over-restore
accettato). Le guardie di tetto (`unpay`/`update_rate`) sono rifiuti a monte: rimuoverle ripristina il
comportamento pre-G7.7 (nessuna migrazione da invertire). Nessuna alterazione dei contratti esistenti.

## Supersedes / Superseded By

- Supersedes: — (estende `ADR-014` sul dominio recesso/valorizzazione; ratifica le invarianti della
  catena G7.0→G7.6)
- Superseded by: — · **§1 emendato da `ADR-017`** (2026-06-26): la *definizione* dell'asse OCCUPAZIONE
  esclude `Rinviato` (il rinvio libera il credito). L'asse EROGATO, la forfeiture delle prenotate e la
  barriera strutturale di `compute_settlement` restano invariati.
