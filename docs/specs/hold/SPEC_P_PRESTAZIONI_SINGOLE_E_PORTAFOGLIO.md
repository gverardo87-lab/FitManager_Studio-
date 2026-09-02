# SPEC_P_PRESTAZIONI_SINGOLE_E_PORTAFOGLIO

**Tipo:** specifica prescrittiva. **Data:** 2026-07-08 · **Branch:** `FitManager_Studio`
**Stato:** ⏸️ **HOLD PRE-POC — P0 CHIUSO; P1–P6 NON AUTORIZZATI** (2026-07-08: P-D1..P-D6
ratificate; riga matrice depositata; birth-review FATTA). Decisione founder 2026-07-31:
il blocco P non appartiene alla `v1.0.15` e riapre solo dopo le evidenze della Wave 0 con nuovo GO.
Scheduling e criteri di riapertura: `SPEC_PRE_POC.md`.
**Governance:** ADR-025 (D-CLASSE-PRESTAZIONE, D-INSOLUTO-DERIVATO, D-WALLET-SEPARATO-COMPENSA,
D-PARZIALE-AMMESSO, D-UNPAY-FLOOR, D-PAGATORE-LEGGERO, D-REGISTRO-OPERATIVO,
D-PREZZO-LIBERO-CONSIGLIATO, D-PORTAFOGLIO, D-SCELTA-ALLA-CREAZIONE, D-SEGNALE-AZIONE) dentro la
**macchina G9** (ADR-022+Add.II penna/classify · ADR-019 ledger intoccabile · ADR-021 partizione
rate · ADR-023 fence · ADR-014 classi ricavo distinte) e la **checklist di nascita ADR-024**.
**Fondamenta:** `product/CATALOGO_SCENARI_PT.md` (96 scenari, Q1-Q23) ·
`archive/RICERCA_COMPETITOR_WALLET_SEDUTE_SINGOLE_2026-07-07.md` (W1-W11) ·
`archive/operations/AUDIT_FE_SEGNALI_E_SELETTORI_2026-07-07.md` (P1-P5, B4/B5, I1-I7).
**Mappa di verità:** `api/services/cash_categories.py` (ClasseContabile + classify) ·
`api/services/financial/ledger.py` (penna) · `invariant_gate.py` · `contract_state.py` ·
`transitions.py` · `api/models/credito_cliente.py`+`credito_terminazione.py` (pattern gemelli) ·
`tests/test_semantic_guards.py` · `tests/test_financial_state_machine.py` ·
`frontend/src/components/agenda/EventForm.tsx` · `api/routers/clients.py` (enrichment).

**Tesi falsificabile:** dopo il blocco P, (1) una seduta fuori contratto è un **fatto economico di
prima classe scelto esplicitamente** alla creazione — mai un orfano subìto né un warning-ansia;
(2) l'insoluto è un **derivato fail-loud** visibile su due viste (per-prestazione + per-cliente) e
in worklist; (3) il wallet **non va mai negativo** e la compensazione è un atto atomico suggerito;
(4) il profilo cliente ha un **Portafoglio** dove ogni segnale porta la sua azione; (5) l'asse
DENARO contrattuale esistente è **byte-identico** (blocco interamente additivo).

**Interlock G9.7 (coda aperta):** l'endpoint `assegna-contratto` resta in G9.7.2; il blocco P
aggiunge la via alternativa «diventa prestazione singola» (P2). **Guard incrociato (CP-2):
`assegna-contratto` rifiuta eventi CON prestazione, `POST /events/{id}/prestazione-singola`
rifiuta eventi CON contratto — le due vie sono mutuamente esclusive, mai doppio fatto economico.**
Il recupero degli eventi reali 640/641 = **scelta esplicita founder tra le due vie**, runbook
condiviso in P6 — MAI a mano nel DB. Il «dropdown onesto» (P1-P5 audit) si chiude in P4 (wire) +
P5 (FE).

---

## Decisioni di spec (P-D, discendenti tecniche ADR-025 — RATIFICATE 2026-07-08)

- **P-D1 — Stati contabilizzanti della singola = `{Completato}`.** L'insoluto nasce SOLO al
  Completato (D-INSOLUTO-DERIVATO). Penali su singola (No_Show/Cancellato_Tardivo) = **Q8 gated
  tributarista**: fino ad allora NON generano fatto economico — dichiarato in UI, mai silenzioso.
  Rinviato/Cancellato: nessun fatto economico (ADR-017 non si applica, niente crediti).
- **P-D2 — Compensazione = due gambe di cassa pareggiate.** USCITA erogazione wallet
  (`RIMBORSO_CONTRATTO`, `id_contratto=NULL`, metodo `COMPENSAZIONE_WALLET`) + ENTRATA prestazione
  (`INCASSO_PRESTAZIONE_SINGOLA`, stesso metodo) nella STESSA transazione via penna. Cassa fisica
  invariata (+X−X), attribuzione per-classe corretta (contra-ricavo ↔ ricavo singola), àncore IP2 e
  wallet-erogato vere **per costruzione**. Alternativa scartata: registro interno senza cassa
  (romperebbe le àncore Σ e renderebbe la compensazione invisibile al mastro).
- **P-D3 — Fence temporale (ADR-023):** gli eventi sono già coperti dal fence; il **condono è
  sempre ammesso** (con audit) — è l'atto che chiude, non riscrive il passato (pattern
  `quota_stornata`, mai delete di cassa).
- **P-D4 — L'escape hatch «senza fatto economico» resta**, con label onesta e in ultima posizione:
  eliminarlo forzerebbe semantica finta (prezzi/motivi inventati che inquinano suggeritore e KPI) e
  romperebbe il flusso reale «prenota ora, firma domani, aggancia» (la via 3 è la sala d'attesa
  legittima del futuro contratto). Contenimento: ordine + toast B5 + **nag della worklist B6**
  (l'orfano è contato finché non risolto — limbo visibile con via d'uscita, mai tomba silenziosa).
  La scelta a 3 vie sostituisce il warning B4 (D-SCELTA-ALLA-CREAZIONE). Niente motivo obbligatorio
  sulla via 3 (attrito-teatro).
- **P-D5 — Naming:** tabella `prestazioni_singole` · modello `api/models/prestazione_singola.py` ·
  router `api/routers/prestazioni.py` (prefix `/prestazioni`) · FK `CashMovement.id_prestazione`.
- **P-D6 — Q9 differita INTERA, con casa dichiarata (RIVISTA in ratifica).** La bozza «metà
  veicolo» (sola gamba `CONVERSIONE_PRESTAZIONE` in P3) si biforcava in due modelli entrambi
  difettosi: (A) spostare l'incasso rende insoluta una prestazione EROGATA (il derivato P-D1 la
  punirebbe, servirebbe un condono-toppa) · (B) wallet nato senza cassa = anticipo non governato
  di G8.5 goodwill — e in entrambi il valore parcheggiato non ha destinazione finché G8.2 non
  shippa. **Decisione:** il blocco P non costruisce NESSUNA meccanica di conversione. La direzione
  resta ratificata (ADR-025: veicolo=wallet, mai sconti impliciti automatici); la meccanica nasce
  con le sue due gambe — **G8.2** (spesa wallet→contratto) + **G8.5** (nascita wallet senza cassa)
  — di cui Q9 diventa il caso d'uso unificante. Interim onesto: sconto ESPLICITO sul prezzo del
  contratto (il prezzo è libero), mai una riga di mastro che mente.

## Sequenza dei gate (vincolante)

### P0 — Nascita della classe (docs-only + ratifica) — ✅ CHIUSO 2026-07-08
- ✅ **Ratifica founder P-D1..P-D6** (una a una in sessione; P-D6 rivista — la sezione P-D è la
  legge del blocco).
- ✅ **Riga in matrice** (`docs/technical/MATRICE_ASSI_SEMANTICI.md`): asse «prestazione singola &
  insoluto», celle ✗ coi puntatori ai gate P1..P6. Prima riga nata col protocollo completo
  (matrice + review PRIMA del codice).
- ✅ **Birth-review** (D-BIRTH-AUDITOR, charter SPEC_G9.4-BIS §5, lente applicata inline). Esito:
  - **S1-S5 charter:** insiemi chiusi previsti come SSoT (P-D1 → `STATI_CONTABILIZZANTI_PRESTAZIONE`;
    **la prestazione NON ha colonna `stato`: derivato-only per decisione**, chi volesse aggiungerla
    deve passare da qui) · interprete unico pianificato (modulo puro, IP3) · totalità sul diff = il
    censimento call-site di P1 · niente netto nudo (W7 due viste) · rito di nascita rispettato
    (ADR-025 + spec + BUILD_LOG).
  - **CP composizione protezioni — 4 finding foldati nei gate:** **CP-1** `delete_client` RESTRICT
    va esteso alle prestazioni con posizione aperta (→ P2) · **CP-2** `assegna-contratto` (G9.7.2)
    deve rifiutare eventi CON prestazione — doppio fatto economico (→ interlock) · **CP-3** il
    blocco prestazione sopprime l'auto-assign; singola su cliente CON contratto attivo = legittima
    (→ P2) · **CP-4** delete evento con prestazione senza denaro = cascade soft-delete dichiarato
    (→ P2).
  - **CP verificate OK (nessun cambio):** **CP-5** reopen del contratto origine-wallet con
    compensazioni a valle → R2-bis riassorbe l'erogato, gambe di cassa restano (ADR-019), zero
    double-count (contra-ricavo lato contratto ↔ ricavo lato prestazione) · **CP-6**
    Rinviato/Cancellato su prepagata → vie d'uscita esistenti (transizioni evento libere per
    riprogrammare, o unpay per rimborsare), nessun deadlock.

### P1 — Schema + classe contabile + penna (backend puro, zero superfici)
- **Tabella `prestazioni_singole`** (pattern gemello `crediti_terminazione`/`crediti_cliente`):
  `id` · `trainer_id` (FK idx) · `id_cliente` (FK idx) · `id_evento` (FK idx **UNIQUE** — 1:1 con
  l'evento agenda, che resta puro scheduling: zero campi economici su `agenda`) · `importo ≥ 0` ·
  `motivo_prezzo_zero` (nullable; obbligatorio se `importo == 0`, Q7) · `importo_incassato`
  (default 0) · `importo_condonato` (default 0) · `motivo_condono`/`data_condono` (nullable) ·
  `data_creazione` · `deleted_at`. Migrazione Alembic formale + `create_db_and_tables` (pattern
  G7.10). **Pitfall #15:** FK solo verso tabelle crm.db — nessun cross-DB.
- **`CashMovement`:** colonne nuove `id_prestazione` (FK nullable idx) + `pagatore` (TEXT nullable,
  D-PAGATORE-LEGGERO — vale per OGNI movimento: ricevute/solleciti intestati al pagatore quando
  presente; Payer entity fuori scope dichiarato).
- **`cash_categories.py`:** `CATEGORIA_INCASSO_PRESTAZIONE = "INCASSO_PRESTAZIONE_SINGOLA"` +
  frozenset `PRESTAZIONE_CASH_IN` · **`ClasseContabile.RICAVO_PRESTAZIONE_SINGOLA`** (7ª classe) ·
  `classify_cash_movement` estesa col parametro `id_prestazione`: ENTRATA+`id_prestazione` →
  guard categoria ∈ `PRESTAZIONE_CASH_IN` fail-loud → classe nuova. **Nello STESSO gate:** censire
  via grep e aggiornare TUTTI i call-site di `classify` e ogni consumatore esaustivo dell'enum —
  la classe non nasce monca (il fail-loud non deve MAI scattare in prod per un ramo dimenticato).
  KPI: la classe entra nei cumulativi con commento «cumulativo» (Q11/pitfall #14), MAI fusa con
  `RICAVO_CONTRATTUALE` (ADR-014).
- **Penna:** `post_prestazione_inflow(session, prestazione, importo, categoria, metodo,
  data_effettiva, trainer_id, *, pagatore=None, note=None)` in `ledger.py` — crea il CashMovement
  **E** incrementa `importo_incassato` nello stesso atto → àncora IP2 per costruzione. Fail-loud su
  categoria fuori asse (gemello delle guard esistenti).
- **Invarianti (gemelli I1-I6), funzioni pure** (modulo `prestazione_state.py` o sezione dedicata):
  **IP1** `importo ≥ 0 ∧ incassato ≥ 0 ∧ condonato ≥ 0 ∧ incassato+condonato ≤ importo` ·
  **IP2** àncora ledger `importo_incassato == Σ ENTRATA[id_prestazione] non-deleted` ·
  **IP3** derivati: `da_incassare = importo − incassato − condonato`; `insoluto = da_incassare` se
  evento Completato, altrimenti `0` (nasce al Completato) · **IP4** `importo == 0 ⟹
  motivo_prezzo_zero` (Q7). Wiring in `invariant_gate` (stesso regime log/raise di I5/I6).
- **Gemelli semantici** in `test_semantic_guards.py`: categoria in `PRESTAZIONE_CASH_IN` e MAI in
  `CONTRACT_CASH_IN`; `classify` totale sulle 7 classi (partizione per costruzione).
- **Gemello di totalità READ-MODEL (da AUDIT_PRE_RELEASE_2026-07-16, M3-sem):** il presidio delle
  7 classi copre ANCHE gli interpreti di lettura, non solo `classify` — oggi `get_movement_stats`
  ha `entrate_lorde` a whitelist di 2 classi + un `else` che somma **alle uscite del grafico**, e
  `get_financial_trend` ha l'`else` bucket-altri: una classe nuova compilerebbe verde finendo
  classificata male. Shape: pin di cardinalità `set(ClasseContabile) == {…7…}` con messaggio che
  ELENCA gli interpreti da aggiornare, oppure bucketing su mapping totale
  `dict[ClasseContabile, bucket]` ad accesso diretto (KeyError = fail-loud). La 7ª classe non
  nasce finché stats/trend non la gestiscono esplicitamente.
- **AC-P1:** suite verde; classificazione di ogni movimento ESISTENTE invariata (zero movimenti con
  `id_prestazione` → asse DENARO byte-identico); `financial-invariant-verifier` PASS.

### P2 — Write-path: nascita, incasso, unpay, suggeritore
- **Nascita atomica (D-SCELTA-ALLA-CREAZIONE):** `EventCreate` accetta blocco opzionale
  `prestazione_singola {importo, motivo_prezzo_zero?, incasso_immediato?{importo, metodo,
  pagatore?}}` — UN commit crea Event (PT, `id_contratto=NULL`) + PrestazioneSingola (+ eventuale
  incasso via penna). **Vietato** il blocco su evento con `id_contratto` (400: o contratto o
  singola, mai entrambi). **Il blocco prestazione SOPPRIME l'auto-assign del contratto (CP-3): la
  scelta esplicita vince** — la singola su cliente CON contratto attivo è legittima (seduta fuori
  pacchetto, non scala crediti). Audit CREATE dedicato.
- **`POST /events/{id}/prestazione-singola`:** promuove un PT orfano esistente (bouncer 404, solo
  PT `id_contratto==NULL` senza prestazione) — la via alternativa di G9.7.2.
- **`POST /prestazioni/{id}/incassa`** (schema RatePayment-like + `pagatore?`): parziale ammesso
  (D-PARZIALE-AMMESSO), cap `importo ≤ da_incassare` (422), penna, audit, UN commit. L'incasso è
  ammesso in QUALSIASI momento (prepagata legittima, W2): l'insoluto resta derivato post-Completato.
- **`POST /prestazioni/{id}/unpay`** (gemello `unpay_rate`): soft-delete movimento + decremento
  `importo_incassato`; se il movimento è gamba di compensazione → floor wallet (P3, D-UNPAY-FLOOR).
- **Suggeritore Q6** (`GET /clients/{id}/prestazioni/prezzo-suggerito`, deterministico+spiegabile):
  (1) prezzo implicito dell'ultimo contratto del cliente `prezzo_totale/crediti_totali` (se
  `crediti_totali > 0`); fallback (2) ultima prestazione singola a prezzo > 0; fallback (3)
  `importo=null` con spiegazione dichiarata. Response `{importo, spiegazione}` («consigliato
  perché…»). MAI un gate: prezzo libero (D-PREZZO-LIBERO-CONSIGLIATO, W9 = unicità). Il prezzo-zero
  è escluso da (2) per costruzione (Q7).
- **Ciclo evento:** Rinviato/Cancellato → nessun fatto economico nuovo; se prepagata, la
  prestazione resta col suo incassato e le vie d'uscita sono dichiarate (CP-6): riprogrammare
  (transizioni evento libere) o rimborsare (unpay). **Delete evento → RESTRICT (409)** se
  prestazione con incassi/condoni (pattern delete-contratto): mai orfanare denaro; **senza denaro
  → cascade soft-delete della prestazione nella STESSA transazione (CP-4)** — satellite enumerato,
  D-PERIMETRO-TRANSIZIONI.
- **`delete_client` RESTRICT esteso (CP-1):** il RESTRICT su posizione aperta (oggi contratti
  attivi + wallet/receivable APERTI) copre anche le prestazioni con `da_incassare > 0` — mai
  cancellare un cliente orfanando un insoluto vivo. Gemello nell'harness.
- **Feature flag `PRESTAZIONI_SINGOLE_ENABLED`** (default ON; OFF → 403 sulla creazione, pattern
  `PUBLIC_PORTAL_ENABLED`) — rollback ADR-025.
- **Hypothesis:** rule nuove (crea singola · incassa parziale · completa · rinvia · unpay ·
  condona) con IP1-IP4 negli `@invariant`; rifiuti legittimi = no-op, 5xx = bug.
- **AC-P2:** PT senza contratto col blocco singola → 201 con prestazione; insoluto compare SOLO
  post-Completato; unpay oltre il floor → 409 **con l'azione**; prezzo-zero senza motivo → 422.

### P3 — Compensazione wallet + condono (Q9, Q10)
- **`POST /prestazioni/{id}/compensa-wallet {id_credito, importo}`** — atto atomico a due gambe
  (P-D2): cap `importo ≤ min(residuo wallet, da_incassare)` → wallet MAI negativo. Il wallet la
  registra come erogazione (`importo_erogato +=`) → il reopen del contratto d'origine la riassorbe
  già per costruzione (R2-bis, ADR-019 Add.II). Suggerita dal Portafoglio quando
  `wallet > 0 ∧ insoluto > 0` («Compensa €X», D-SEGNALE-AZIONE), MAI automatica.
- **Unpay della compensazione:** ripristino di ENTRAMBE le gambe nella stessa transazione; wallet
  già speso a valle → **409 esplicito con l'azione** (D-UNPAY-FLOOR). Vietato l'insoluto sintetico.
- **Condono (Q10):** `POST /prestazioni/{id}/condona {importo, motivo}` — rettifica dedicata:
  `importo_condonato +=` (cap `≤ da_incassare`), audit dedicato, MAI delete di cassa (ADR-019).
  Il write-off è un atto, mai un'omissione (W8). **Definitivo** nel blocco P (niente
  annullo-condono, P-D3): a differenza dell'incasso non ha cassa da ripristinare.
- **AC-P3:** compensazione → saldo cassa invariato, wallet e insoluto scendono insieme; condono
  estingue senza toccare il mastro; unpay post-spesa-a-valle → 409 con azione.

### P4 — Read-model: Portafoglio + wire onesto (D-PORTAFOGLIO, W7, Q11, Q23)
- **`GET /clients/{id}/portafoglio`** — UN interprete backend: `{crediti_sedute_attivi {residui,
  breakdown per contratto}, wallet {residuo, items}, receivable {residuo, items}, prestazioni
  {da_incassare, insoluto, items}, azioni_suggerite}` — ogni blocco porta l'azione che lo risolve.
- **Fix root-cause audit:** `crediti_residui_attivi` su `ClientResponse` (residui dei SOLI
  contratti attivi); il campo storico `crediti_residui` resta, documentato «cumulativo».
  **Evidenza LIVE 2026-07-20 (audit FE §5):** la variante «attivo esaurito + chiuso residuale»
  elude ENTRAMBI i warning EventForm (B4 vede 1 attivo; «esauriti» legge il cumulativo = 2 dal
  CHIUSO) e il toast B5 promette un'assegnazione che `OrphanEventsSheet` non può offrire (unico
  aperto a 0 residui). Il campo onesto serve anche a rendere COERENTE il predicato dei warning:
  entrambe le gambe sullo stesso perimetro.
- **Due viste di UN derivato (W7):** insoluto per-prestazione (riconciliabile) + aggregato
  per-cliente (Portafoglio) + **worklist globale `GET /dashboard/insoluti`** (aging, gemella
  `crediti-da-incassare`, pattern `_*_candidates()` → count == len(items)).
- **Q23:** campo informativo `data_bonifico_dichiarato` (nullable) sulla prestazione — stato
  informativo sul sollecito («dichiarato il …»), display-only: NON tocca il derivato, mai una
  terza semantica.
- **KPI:** ricavo da singole nei cumulativi con classe propria; ogni KPI nuovo col commento
  «stato vs cumulativo» inline (Q11/pitfall #14).
- **AC-P4:** sul caso founder («(2 crediti)» da contratto CHIUSO accanto a «nessun contratto
  attivo») il Portafoglio spiega ogni numero dalla vista; aggregato == Σ items (test).

### P5 — FE: scelta alla creazione + Portafoglio + dropdown onesto (Q20, Q22)
- **EventForm — la scelta a 3 vie sostituisce il warning-ansia B4/G9.7.1:** cliente + PT + zero
  contratti agganciabili → radio: «**Prestazione singola** (€X consigliato — perché…)» ·
  «Aggancia contratto…» (se esiste aperto) · «Senza fatto economico» (ultima, label onesta, P-D4).
  **Q22:** microcopy guida contratto-vs-singole. **Q20:** freshness warning se cliente fermo
  ≥ `SOGLIA_CHURN_GG` con anamnesi stantia — segnale CON azione (link anamnesi), mai blocco.
- **Dropdown clienti:** consuma `crediti_residui_attivi` con label onesta (chiude P1-P5 audit).
  Il toast B5 si aggiorna: singola creata → conferma della scelta, non warning.
- **Pannello «Portafoglio»** nel profilo cliente (tab o card in Panoramica — scelta
  implementativa): 4 blocchi, ogni riga con azione (Incassa / Compensa €X / Eroga / worklist).
  Zero ricalcoli FE: consuma SOLO il wire (guard).
- **Guard FE-no-money-math esteso** all'asse prestazione (allowlist motivata) + vitest sulla
  scelta a 3 vie + **QUARTA fixture warning** `{contratti_attivi: 1, crediti_residui: 2 (dal
  chiuso), crediti_residui_attivi: 0}` — la variante 2026-07-20 che oggi non ha alcun segnale
  pre-submit (audit FE §5).
- **AC-P5:** caso founder rigiocato LIVE (Playwright): seduta flash per cliente storico → scelta
  esplicita → prestazione nasce → Portafoglio la mostra con azione. Zero panico, zero 201 muti.
  Include la variante «attivo esaurito + chiuso residuale»: segnale PRIMA del submit, mai
  sorpresa post-creazione.

### P6 — Presidio, recupero, chiusura
- Matrice: celle asse prestazione → ✅ coi puntatori ai presidi REALI (anti-vacuità).
- Hypothesis liveness provata (sonda G9.5) sulle rule nuove; harness invariante×transizione esteso.
- **Runbook 640/641** (con G9.7.2): scelta esplicita founder per ciascun evento — assegna al
  contratto 39 (endpoint G9.7.2) o promuovi a singola (P2). MAI a mano nel DB.
- Consuntivo + fold-back: FDM (entità nuova) · TASSONOMIA (vocabolario prestazione/insoluto/
  compensazione) · `api/CLAUDE.md` · matrice · archiviazione spec (metodo §7).

---

## Fuori scope (dichiarato)
Q8 penale monetaria su singola (**gated tributarista** — con `pro_sedute` e confine fiscale, call
unica D-REGISTRO-OPERATIVO) · Q12 listino versionato (post-lancio) · **Q14 linea esatta: il
Portafoglio è CRM-only — sul portale pubblico MAI saldi €/wallet/insoluti; i crediti-sedute
restano l'unica estensione ammissibile futura, fuori blocco P** · Q15 GDPR conservazione (Tier-3)
· Q16 riclassificazione retroattiva (OD-1 invariato) · Q19 upsell nudge (le singole nascono
interrogabili come serie: basta l'indice per-cliente) · Q21 abbonamento flat (ADR dedicato futuro)
· Payer entity (D-PAGATORE-LEGGERO basta) · **Q9 conversione singole→pacchetto INTERA → casa
G8.2+G8.5** (P-D6: direzione wallet ratificata, interim = sconto esplicito sul prezzo contratto)
· G8.5 goodwill (in coda) · vocabolario UI mai fiscale (mai «fattura» — D-REGISTRO-OPERATIVO).

## Definizione di fatto
(1) classe nata col protocollo ADR-024 (riga matrice, gemelli, Hypothesis, birth-review); (2) la
seduta fuori contratto è una scelta esplicita con prezzo consigliato spiegabile; (3) insoluto
derivato su 2 viste + worklist; (4) compensazione atomica + condono auditato; (5) Portafoglio nel
profilo con azione per riga; (6) dropdown/label oneste (P1-P5 audit chiusi); (7) 640/641
recuperati via endpoint; (8) asse DENARO contrattuale byte-identico (`financial-invariant-verifier`
PASS a ogni push); (9) suite + vitest + build + check-all verdi; (10) fold-back docs completo.

**Quality gate per ogni gate di codice:** pytest full su diff api/ money-adjacent (+ verifier
read-only pre-push) · vitest · next build · check-all; commit `feat: P.N — …`; fold-back docs a
chiusura gate (metodo §7).
