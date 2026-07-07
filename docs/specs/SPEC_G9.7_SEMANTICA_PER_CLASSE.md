# SPEC_G9.7_SEMANTICA_PER_CLASSE

**Tipo:** specifica prescrittiva. **Data:** 2026-07-07 · **Branch:** `FitManager_Studio`
**Stato:** 🟡 **APERTA — DA IMPLEMENTARE** (ratifica founder 2026-07-07). Governance: `ADR-024`
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
- **AC-G97-2:** orfano assegnato via endpoint → occupa il credito; endpoint rifiuta contratto
  chiuso (400) e cliente diverso (404). **AC-G97-2b:** reopen su contratto con orfani nel periodo
  → response/preview li nomina. Fail: limbo senza uscita o riaggancio silenzioso.

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
