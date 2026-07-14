# SPEC_G9.7_SEMANTICA_PER_CLASSE

**Tipo:** specifica prescrittiva. **Data:** 2026-07-07 · **Branch:** `FitManager_Studio`
**Stato:** 🟡 **APERTA — G9.7.0 ✅ · G9.7.1 ✅ (incl. -bis) · G9.7.2 ✅ CHIUSO 2026-07-09 ·
G9.7.3 ✅ CHIUSO 2026-07-11 · G9.7.4 ✅ CHIUSO 2026-07-14** (runbook §Runbook in coda, esecuzione
trainer-driven) · resta G9.7.5. Governance: `ADR-024`
(accepted). Audit fondante: `docs/operations/AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07.md` (13 finding
B1-B8/D1-D5) + `AUDIT_CENSIMENTO_ASSI_SEMANTICI_CASSA_2026-07-04.md` (assi A1-A10).
**Mappa di verità:** ADR-024 · ADR-022+Add.II · ADR-017 Add.I · ADR-019 (D-PROPONE) · ADR-023 ·
`api/services/contract_state.py` (STATI_OCCUPAZIONE_CREDITO) · `api/routers/agenda.py` ·
`api/services/financial/transitions.py` · `tests/test_semantic_guards.py` ·
`tests/test_financial_state_machine.py` · SPEC_G9.4-BIS §5 (charter auditor).

**Tesi falsificabile:** dopo G9.7, (1) nessun path di scrittura degrada in silenzio (creare un PT
senza aggancio produce warning prima e segnale dopo); (2) nessun dato resta in limbo senza via di
recupero esplicita; (3) ogni derivato-occupazione a video è spiegabile dalla vista; (4) le
transizioni dichiarano il perimetro delle entità satellite; (5) l'asse DENARO è byte-identico.

---

## Sequenza dei gate (vincolante)

### G9.7.0 — Matrice assi×regole (docs-only)
Nasce `docs/technical/MATRICE_ASSI_SEMANTICI.md` (SSoT evergreen): per ogni asse di stato
(cassa/classi contabili · occupazione crediti · stati evento · lifecycle contratto · stati
crediti/wallet · rate · slot calendario) × 4 regole (insieme chiuso · interprete unico · totalità
fail-loud · gemello esaustività) + colonna «derivati a video spiegabili» + colonna «composizione
protezioni verificata». Celle: ✅/⚠️/✗ con puntatore al presidio o al gap. Fonte: i 2 audit.
**Gate:** matrice completa, INDEX aggiornato.

### G9.7.1 — Mai-silenzio sul write-path eventi×contratto (B1, B4, B5)
- **FE pre-warning (B4):** `EventForm` con cliente selezionato e categoria PT avvisa quando il
  cliente NON ha contratti attivi agganciabili («La seduta verrà creata SENZA contratto — non
  scala crediti») — predicato dal dato già disponibile lato client o campo dedicato; il submit
  resta possibile (escape hatch legittimo) ma CONSAPEVOLE.
- **FE post-segnale (B5):** dopo il 201, se `id_contratto == null` su PT con cliente → toast
  warning dedicato (mai il success generico). La response backend già porta `id_contratto`.
- **AC-G97-1:** creare un PT per cliente con soli contratti chiusi produce warning PRIMA e toast
  dedicato DOPO. Fail: un 201 muto. *(vitest su EventForm + verifica LIVE)*
- **✅ CHIUSO 2026-07-09 con G9.7.1-bis** (verifica LIVE meticolosa → 3 gravissimi, 2 decisioni
  founder): (a) **TUTTI i toast erano muti** — doppia istanza sonner dal `dynamic()` in
  `providers.tsx`: il B5 non era MAI apparso → fix import statico (`abb0224`), riverificato LIVE
  su entrambi i rami; (b) le **ORFANE contate come «usate»** in `_calc_credits_batch`
  (`clients.py`) → dropdown a 0 → hard-block → cliente intrappolato → fix filtro
  `id_contratto != None` + gemello `test_g971bis_orfana_non_decrementa_crediti_cliente`;
  (c) l'**hard-block «Crediti esauriti» contraddiceva l'escape hatch** (B4 irraggiungibile per i
  clienti senza contratti, il caso P-D4) → declassato a warning soft calibrato, submit sempre
  permesso — la legge dura resta il credit-guard backend. AC-G97-1 presidiato da vitest
  (`event-form-warnings.test.tsx`: B4 su 3 classi di cliente + predicato `isPtOrfanoCreato`
  esportato = invariante «mai 201 muto», sopravvive a P5). P5/ADR-025 sostituirà i warning con la
  scelta a 3 vie; P4 renderà onesto il numero (`crediti_residui_attivi`).

### G9.7.2 — Recupero esplicito degli orfani (B2, B3, B6 + D-RECUPERO-ESPLICITO)
- **Endpoint** `POST /events/{id}/assegna-contratto` — bouncer 404, SOLO eventi PT con
  `id_contratto == NULL`, contratto target: stesso cliente + aperto + credit-guard; audit UPDATE;
  atomico. È l'UNICA via di re-parenting (l'`EventUpdate` generico resta chiuso — il fence
  ADR-023 non si tocca).
- **Visibilità (B6):** i PT orfani in stati di occupazione diventano visibili: etichetta «senza
  contratto» + CTA «Assegna» dove l'evento appare (EventSheet/hover) e conteggio in una worklist
  (estensione ghost-events o sezione dedicata — scelta implementativa).
- **Reopen PROPONE (B2/B3):** `reopen-preview` e la response di `reopen` segnalano gli eventuali
  PT orfani del cliente creati nel periodo di chiusura (`data_creazione ≥ data_chiusura`) —
  propone il recupero, NON riaggancia da solo (D-PROPONE).
- **Recupero dato reale:** eventi 640/641 → assegna al contratto 39 via endpoint (runbook 3 righe
  in coda alla spec a implementazione fatta; MAI a mano nel DB).
- **Interlock ADR-025 (blocco P):** l'assegnazione al contratto resta QUI; la via alternativa
  «diventa prestazione singola» nasce in `SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO.md` (P2); il
  recupero 640/641 = scelta esplicita founder tra le due vie, runbook condiviso (P6). **Guard
  CP-2 (birth-review P0):** `assegna-contratto` rifiuta eventi che hanno GIÀ una prestazione
  singola — le due vie sono mutuamente esclusive, mai doppio fatto economico.
- **AC-G97-2:** orfano assegnato via endpoint → occupa il credito; endpoint rifiuta contratto
  chiuso (400) e cliente diverso (404). **AC-G97-2b:** reopen su contratto con orfani nel periodo
  → response/preview li nomina. Fail: limbo senza uscita o riaggancio silenzioso.
- **✅ CHIUSO 2026-07-09.** Endpoint `assegna-contratto` (agenda.py: guard chain 404/400 +
  credit-guard condizionato all'occupazione + auto-close via `_sync`, audit UPDATE, UN commit;
  guard CP-2 forward-dichiarato per P1) · reopen-preview e `POST /reopen`
  (`ContractReopenResponse`) NOMINANO gli orfani del periodo (`_orfani_periodo_chiusura`,
  snapshot pre-reopen) · worklist `GET /dashboard/orphan-events` col pattern `_*_candidates`
  (solo stati di occupazione; ogni riga porta i contratti APERTI del cliente = azione inline) +
  alert `orphan_events` · FE: badge hover «senza contratto», `AssegnaContrattoBanner` in
  EventSheet, `OrphanEventsSheet` con Assegna inline. **10 test** integrazione
  (`test_assegna_contratto_orfano.py`: guard chain, Rinviato esente da credit-guard,
  composizione auto-close, 2b preview+response, worklist+alert coerenti). **LIVE E2E:** orfano
  creato da UI → alert (che ha rivelato 3 orfani reali in più: 643 + 647/649) → sheet →
  assegna inline → occupa (crediti_usati+1) → alert decrementa.

### G9.7.3 — Derivato-occupazione mai nudo (D1-D5 + D-DERIVATO-MAI-NUDO)
- **D1 (hero):** riga crediti con card/valori Penali e Rinviate (dati GIÀ sul wire) — le penali
  sono un SEGNALE (amber), non dettaglio da toggle; a occupazione spiegata: totali = programmate
  + completate + penali + residui (rinviate informativo).
- **D2/D3 (liste):** sub-label che spiega la differenza usati−svolte (pattern G9.4-bis.3, es.
  «5 svolte · 2 penali»); lista: servono i conteggi sul wire di `ContractListResponse` (additivo).
- **D4:** `DeleteContractDialog` legge `contract.crediti_residui` dal wire (delega SSoT).
- **D5:** sheet/rinnovi — breakdown minimo dove il conteggio è mostrato.
- **AC-G97-3:** sul caso reale (12 totali · 5 svolte · 2 penali) ogni superficie che mostra i
  residui li rende spiegabili dalla vista. Fail: un credito «sparito» a video.
- **✅ CHIUSO 2026-07-11.** Fetta D1-D4 (`e533f9d`, 2026-07-09): hero a 6 card + banner-SEGNALE
  always-visible con l'equazione (totali = programmate + svolte + penali + residui), sub-label
  «N svolte · M penali» su ContractRow+ContrattiTab, DeleteContractDialog dal wire, wire additivo
  lista (`sedute_penali`+`crediti_residui`, batch fuso in UNA query group-by dal SSoT). Fetta D5
  (2026-07-11): `_occupazione_breakdown_map` in `dashboard.py` = UNICO interprete batch
  (group-by `(id_contratto, stato)`, derivazione `STATI_OCCUPAZIONE_CREDITO`/`STATI_PENALE`;
  `_crediti_usati_map` delega; la raw-SQL COUNT dell'expiring RITIRATA); `suspended-contracts` +
  `expiring-contracts` espongono `sedute_completate`+`sedute_penali`; sub-label sulle card
  rinnovi/sospesi (`rinnovi-incassi/page.tsx`) e su `ExpiringContractsSheet`. Gemelli: 2 pytest
  D5 (worklist == dettaglio, un solo interprete — `test_late_cancel_no_show.py`) + 2 vitest sheet
  (svolte+penali dal wire · zero penali = zero rumore). LIVE (read-only, dev 3001/8001): caso
  founder a video — card contratto 39 «12 PT · 3/12 crediti · 7 svolte · 2 penali»; card senza
  penali mostrano solo «N svolte». Matrice: celle DV occupazione-credito + R2/DV crediti-residui → ✅.

### G9.7.4 — Guard di classe (D4 + D-LEGGI-PER-CLASSE)
- Il gemello FE «no-recalc» (`test_semantic_guards.py`) si estende dall'asse denaro all'asse
  crediti: vietati i ricalcoli inline (`crediti_totali - crediti_usati`, somme su stati evento)
  con allowlist esplicita motivata; anti-vacuità: le superfici consumano i campi wire.
- **Test di perimetro transizioni (D-PERIMETRO-TRANSIZIONI):** un test semantico asserisce che
  `execute_terminate`/`execute_reopen` dichiarano il perimetro delle entità satellite (rate,
  cassa, receivable, wallet, eventi) — enumerazione esplicita nel modulo (marker/costante
  `PERIMETRO_TRANSIZIONE`) + il test fallisce se nasce una entità satellite nuova (FK/tabella che
  referenzia il contratto) non elencata. Gemello di esaustività della classe «5 produttori».
- **AC-G97-4:** aggiungere una tabella satellite finta al perimetro del test → rosso finché non
  dichiarata. Fail: guard vacuo.
- **✅ CHIUSO 2026-07-14.** Cinque gemelli in `test_semantic_guards.py`:
  *(a)* `test_g974_fe_no_credit_math` — vietati `totali−usati`, `totali−residui` e i conteggi di
  stati evento client-side; allowlist motivata SOLO per gli aggregati-di-vista (dashboard-helpers,
  RangeStatsBar agenda — stessa dottrina Σ-di-vista del money-guard). **Provato ROSSO sul codice
  pre-fix**: 2 siti reali fixati (progress bar RenewalCard `totali−residui` → `crediti_usati` dal
  wire; dropdown AssegnaContrattoBanner `totali−usati` → `crediti_residui` dal wire).
  *(b)* anti-vacuità consumo wire: hero/ContractRow/DeleteContractDialog/banner/rinnovi LEGGONO i
  campi occupazione; autorità = `ContractListResponse.model_fields`.
  *(c)* `test_g974_stati_credito_no_reinline` — chiude il flag LOW G9.4-bis della matrice:
  classificazioni wallet/receivable solo via `STATO_CREDITO_*` (SALDATO escluso dalla rete:
  collide con l'asse `stato_pagamento`).
  *(d)* **`PERIMETRO_TRANSIZIONE`** in `transitions.py`: 7 satellite dichiarate con dottrina
  terminate/reopen (rate M1/reconcile · cassa IMMUTABILE R1 · rettifiche storno/reversal ·
  receivable →ANNULLATO · wallet →ANNULLATO+fold · agenda SOLO-lettura · self `rinnovo_di` mai
  mutato) + `test_g974_perimetro_transizioni_esaustivo` = set-equality bidirezionale col metadata
  ORM (satellite nuova non dichiarata O voce fantasma = rosso; la rete per-nome
  `id_contratto`/`id_contratto_origine` copre il cross-DB senza FK, pitfall #15).
  *(e)* AC-G97-4: `test_g974_perimetro_becca_satellite_nuova` prova la scoperta su tabella FINTA
  `prestazioni_finte` in MetaData separato (zero inquinamento) — la futura `prestazioni_singole`
  (P1) NON può nascere senza dichiarare il suo destino nelle transizioni (CP-4 by-construction).
  Suite full **858** pytest (+5) · **103** vitest · check-all verde. Asse DENARO invariato
  (costante+test, zero logica toccata).

### G9.7.5 — Anticipo (D-BIRTH-AUDITOR + D-GENERATIVO-PER-ASSE)
- Agente `.claude/agents/semantic-birth-auditor.md` dal charter SPEC_G9.4-BIS §5, esteso con la
  lente «composizione protezioni» (il deadlock B1×no-re-parenting è il caso canonico).
- Hypothesis: rule nuove sull'asse occupazione in `test_financial_state_machine.py` (crea PT su
  contratto vivo/chiuso · completa · termina · riapri · assegna orfano) + invariante
  **I-EVENTI**: ogni PT in stato di occupazione ha `id_contratto` valido OPPURE è segnalato come
  orfano (mai occupazione fantasma, mai orfano invisibile).
- **AC-G97-5:** liveness provata (le rule nuove vengono esercitate — sonda come G9.5); il canary
  «crea-su-chiuso poi riapri» riproduce B1/B2 e verifica il comportamento nuovo.

---

## Fuori scope (dichiarato)
Riaggancio AUTOMATICO al reopen (violerebbe D-PROPONE) · modifica del fence ADR-023 · asse DENARO
(byte-identico per costruzione: nessun CashMovement/colonna toccata) · G8.5 goodwill (in coda,
apertura pendente per DoD G8.4) · B7/B8 (auto-protezioni: documentate in matrice, zero codice).

## Definizione di fatto
(1) matrice viva in docs/technical; (2) zero 201 muti sul write-path eventi; (3) orfani visibili +
recuperabili via endpoint auditato + 640/641 recuperati; (4) occupazione spiegabile su ogni
superficie; (5) guard crediti + perimetro transizioni nel gate; (6) auditor attivo + Hypothesis
estesa con liveness provata; (7) suite verde, asse DENARO invariato, check-all verde.

**Quality gate per ogni gate di codice:** pytest (full su diff api/ money-adjacent; fascia su
FE/test-only) + vitest + next build + check-all; commit specifici `feat: G9.7.N — …`; fold-back
docs a chiusura gate (metodo §7).

---

## Runbook recupero orfani reali (G9.7.2 — esecuzione trainer-driven, MAI a mano nel DB)

Stato al 2026-07-09 (worklist live): **5 orfani** — 640/641/**643** (Giacomo Verardo, il 643 è
nato DOPO l'audit; il suo contratto 39 è CHIUSO → oggi «nessun contratto aperto») + **647/649**
(eventi `test` del founder su Sara Di Grumo e Dalila Floris).

1. **647/649 (test):** eliminarli dall'agenda (erano prove del founder) — o assegnarli se erano
   sedute vere.
2. **640/641/643 (Giacomo):** scelta esplicita founder per ciascuno (ADR-025):
   *(a)* riapri il contratto 39 (`reopen-preview` ora li NOMINA) → assegna dal
   dettaglio evento o dalla worklist → gestisci il contratto (ri-termina/completa); oppure
   *(b)* attendi P2 (blocco P) e promuovili a **prestazioni singole**.
3. Verifica: alert `orphan_events` a zero (o al solo residuo scelto), crediti del contratto
   coerenti a video.
