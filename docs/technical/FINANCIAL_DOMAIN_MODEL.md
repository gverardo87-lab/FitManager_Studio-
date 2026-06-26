# FINANCIAL DOMAIN MODEL — la base unica del dominio economico-finanziario

**Versione:** 1.3
**Stato:** **SSoT del dominio finanziario — vincolante.** Ogni feature finanziaria si misura qui.

> **Nota di versione 1.3 (2026-06-21, evento di terminazione anticipata):** incorporato il **terzo modo
> di morte** del contratto — la **terminazione anticipata per decisione umana** (recesso del cliente /
> risoluzione del trainer / chiusura consensuale) avvenuta a contratto **vivo** (ATTIVO o SOSPESO), con
> **conguaglio economico bidirezionale**. Sintesi delle modifiche: (1) **§2** — introdotti
> `netto_incassato` e `totale_rimborsato` (decisione **Strada B**: il lordo non si riscrive mai). (2)
> **§3** — la frase «`chiuso` si accende SOLO su saldato+esaurito» è **superata**: vale per il
> completamento, non per la terminazione; CHIUSO è ora raggiungibile **mid-life**. (3) **§3.1 NEW** —
> l'evento di terminazione, le **due gambe del conguaglio** (rimborso in cassa / storno del dovuto),
> base di calcolo sulle **sedute** (non sul calendario). (4) **§6** — la worklist «Contratti sospesi»
> guadagna la **terza azione** (chiudi con conguaglio). (5) **§7-G7 NEW** — il conguaglio e i suoi
> invarianti; G5 esteso. (6) **§9** — **4° invariante anti-perdita** (il rimborso dovuto non sparisce)
> + **§9.5 NEW** invariante di coerenza del netto (Strada B). (7) **prerequisiti** emersi dalla
> ricognizione sul codice reale: fix Forecast (rate fantasma su CHIUSO), audit della transizione
> `chiuso`, **remediation dei 3 contratti già terminati muti** (id 4/9/13). La **policy di rimborso**
> (pro-sedute sì/no, prezzo di valorizzazione delle sedute usate, recesso del consumatore IT) è
> marcata **DECISIONE APERTA** (tributarista/legale) — il modello fissa *che* l'evento esiste e *che
> forma* ha; i numeri della policy si riempiono prima dell'implementazione. **Implementazione in coda
> a G6** (il rimborso è cassa diretta in uscita sul contratto: riusa l'infrastruttura di G6, stesso
> pattern, segno opposto).
>
> **Raffinamenti post-bridge (review Claude Code su codice vivo, 6 punti):** (a) §6/§11 — **design-scope
> ≠ build-scope** sulle 3 azioni del SOSPESO (Blocco 3 consegna worklist + *Estendi*; le gambe di
> chiusura sono di G7); (b) §3.1/§7-G5 — **`non_rinnova` è retention, NON un motivo di chiusura** (asse
> ortogonale `esito_rinnovo_motivo`); (c) §9.5 — **netto vs lordo enumerato per vista** (non più «dove
> serve»); (d) tassonomia §7.2 — **8ª query** (`get_balance`); (e) §11 — **scope schema** del blocco a
> piano; (f) §7-G7 — **remediation su dato vivo** come runbook a sé. Il meccanismo è specificabile col
> **parametro-policy pluggable**: SPEC_TERMINAZIONE non è bloccata dalla policy, solo la valorizzazione.
>
> **Assorbimenti dalla review del piano di strategia (Claude Code Opus 4.8):** (g) **campo storno
> confermato** `quota_stornata` (gemello di `totale_rimborsato`) — §2/§11 lo nominano, `residuo()` lo
> sottrae; (h) **nuovo invariante §9.5.6** `quota_stornata > 0 ⟹ chiuso = True` (load-bearing per i KPI
> residuo inline). **Resta una sola decisione di Giacomo prima della migrazione:** l'**enum di
> `motivo_chiusura`** (esito economico vs ragione — §11).

> **Nota di versione 1.2 (2026-06-20, robustezza bridge round-2):** (1) dichiarata l'**assunzione-proxy**
> del raffreddamento (§4.1: usa i contatti loggati come proxy del contatto reale). (2) **G6** (§7): manca
> il pagamento diretto del residuo → residuo non-rateizzato su scaduto non incassabile (verificato su
> dato reale); + verifica auto-close su scaduto confermata sul codice. Nessun blocco: il modello è fermo.

> **Nota di versione 1.1 (2026-06-20, rilievi bridge chat):** incorporati 3 rilievi che completano
> l'asse-tempo (lo stesso che `chiuso` ignorava): (1) **invariante transizioni indotte dal tempo** —
> ogni stato non-terminale ha una worklist, l'appartenenza è il segnale (§9.4); (2) **rollup cliente
> a natura mista** derivato/a-memoria + stato **lapsed-freddo** e **decadimento asimmetrico** (§4.1);
> (3) **costanti temporali unificate** in un punto solo, con cooling=retention=churn = una costante
> (§4.2). Debito emerso: `orphan_contracts`/`contracts-to-plan` già implementati violano G1 (§7).

**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code
**Collocazione:** `docs/technical/`
**Data:** 2026-06-21
**Decisioni:** `ADR-014` (cassa/competenza), `ADR-015` (funnel rinnovi/retention)
**Coordina (vivo):** `TASSONOMIA_FINANZIARIA.md` (asse cassa/competenza) · `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` (consumo-SSoT UI) · `IMPL_PLAN_FINANCIAL_REALIGN.md` (piano attivo).
**Ha assorbito (spec implementate, archiviate 2026-06-23 in `docs/archive/specs/`):** SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE, SPEC_GESTIONE_FINANZIARIA_TEMPORALE, SPEC_RINNOVI_SCADUTI_E_RETENTION — il loro modello vive ora qui.

> **Perché esiste.** Gli stati del contratto e la nozione di "attivo" erano definiti **per-feature**,
> con significati divergenti in endpoint diversi → logiche accavallate, difetti silenziosi (un contratto
> scaduto contato "attivo"; "da pianificare" su contratti dove non si può pianificare). Questo documento
> fissa **una volta** entità, assi, stati, vocabolario, worklist e invarianti. Le spec-feature
> contengono solo i *criteri di accettazione* e **referenziano** questo modello; non lo ridefiniscono.
> Lato codice, la derivazione vive in **un solo posto** (`contract_state()`), consumato da tutti.

---

## 1. Entità

| Entità | Tabella | Ruolo finanziario |
|---|---|---|
| **Cliente** | `clienti` | soggetto; rollup dei suoi contratti |
| **Contratto** | `contratti` | nodo centrale: prezzo, acconto, versato, crediti, date, chiuso, rinnovo_di, esito_rinnovo |
| **Rata** | `rate_programmate` | rateizzazione del denaro dovuto (importo_previsto/saldato, scadenza, stato) |
| **CashMovement** | `movimenti_cassa` | libro mastro datato (ENTRATA/USCITA, categoria, data_effettiva) — verità di cassa |
| **Evento** | `agenda` | seduta; consuma 1 credito (categoria PT, non cancellato) |

---

## 2. I tre assi del contratto (indipendenti)

Un contratto si "esaurisce" lungo **tre assi distinti**, che NON vanno confusi:

| Asse | Sorgente | Esaurito quando |
|---|---|---|
| **Tempo** | `data_inizio → data_scadenza` | `data_scadenza < oggi` (vigente se NULL o ≥ oggi) |
| **Crediti/sedute** | `crediti_totali` − `crediti_usati` | `crediti_residui = 0` |
| **Denaro** | `prezzo_totale` − `totale_versato` = `residuo` | `residuo = 0` (saldato) |

- **`crediti_usati` è computed-on-read** = **occupazione-credito**: `COUNT(eventi PT in stato
  `Programmato` o `Completato`, non eliminati)` sul contratto. **`Rinviato` e `Cancellato` NON occupano**
  — il rinvio libera il credito spendibile (ADR-017/G7.8; `Rinviato` resta display via `sedute_rinviate`).
  `crediti_residui = max(crediti_totali − crediti_usati, 0)`.
- **`residuo = max(prezzo_totale − totale_versato, 0)`**. `totale_versato` riconciliabile col mastro
  (`ReconciliationResponse`).

> **`data_scadenza = NULL` = "pacchetto senza termine" è un caso di prodotto REALE (decisione audit 2026-06-23).**
> Il SSoT tratta già NULL come *contratto perpetuo* (`is_vigente` NULL→True, `contract_lifecycle` NULL→ATTIVO
> permanente; tutti i guard rate/KPI/aging sono già null-safe). La contraddizione cross-layer — il boundary
> `ContractCreate` **vieta** NULL mentre modello e SSoT lo **ammettono** — si risolve **aprendo il boundary**:
> `ContractCreate` + form `data_scadenza` **opzionale** (**implementato 2026-06-23**; zero migrazione DB,
> colonna già nullable: `ContractCreate.data_scadenza: Optional[date]`, validator condizionale, checkbox
> "Senza scadenza" nel `ContractForm`, label "Senza scadenza" in lista/dettaglio; test
> `test_contract_no_expiry.py`). NULL **non è "legacy"**: è first-class. *(Altre decisioni audit Contract 2026-06-23 — non
> model-level: `chiuso`-via-update → rimozione rimandata a G7; type-honesty NOT NULL/ORM → rimandato, resta
> boundary-only [§9.5.7]. Dettaglio e razionale in `BUILD_LOG.md`.)*

> **Asse denaro — il netto (v1.3, decisione Strada B).** `totale_versato` è e resta **LORDO cumulativo**
> (somma di tutto ciò che è entrato, invariante `totale_versato == Σ ENTRATA` del mastro per il
> contratto). Su questo **non si scrive mai a ritroso**: ridurre il lordo = riscrivere il passato e far
> riapparire un dovuto inesistente via `residuo = prezzo − versato`. Quando del denaro **esce** verso il
> cliente (rimborso, §3.1), il netto si introduce **ex-novo** con un campo dedicato:
>
> | Quantità | Definizione | Natura |
> |---|---|---|
> | `totale_versato` | Σ di ciò che è entrato (LORDO) | stored, immutabile a ritroso, `== Σ ENTRATA` |
> | `totale_rimborsato` | Σ di ciò che è uscito verso il cliente come restituzione | stored, parte da 0, **cresce solo** (immutable-forward) |
> | `quota_stornata` | Σ del dovuto **abbonato** (write-off, gamba storno §3.1) — azzera il `residuo` senza riscrivere `prezzo_totale` | stored, parte da 0, **cresce solo** (immutable-forward) — gemello di `totale_rimborsato` |
> | **`netto_incassato`** | `totale_versato − totale_rimborsato` | **derivato** — cassa effettivamente trattenuta |
>
> `residuo = max(prezzo_totale − totale_versato − quota_stornata, 0)` è la forma **canonica** (confermata
> in ricognizione: il campo `quota_stornata` è necessario perché `residuo()` è letto anche nel **dettaglio**,
> non solo nelle worklist gated dal lifecycle). Per i contratti non terminati `quota_stornata = 0` e la
> formula collassa su `prezzo − versato`; per i terminati vale l'invariante §9.5 (`residuo ≡ 0`, settled).

---

## 3. Stato di vita del contratto (canonico) — `contract_state()`

`chiuso` (flag stored) è il **flag terminale**: quando è acceso, lo stato di vita è CHIUSO,
**indipendentemente da tempo e crediti**. Lo stato di vita reale è una **funzione derivata** di
(tempo × crediti × chiuso), in **4 stati mutuamente esclusivi**:

```
contract_state(c):
  if c.deleted_at:           -> ELIMINATO        (fuori da ogni vista)
  if c.chiuso:               -> CHIUSO
  if scaduto(c):             # data_scadenza < oggi
      if crediti_residui > 0 -> SOSPESO          # sedute prepagate da erogare
      else                   -> ESAURITO         # sedute finite (⇒ residuo denaro > 0, sennò sarebbe CHIUSO)
  else:                      -> ATTIVO           # vigente (scadenza NULL o ≥ oggi)
```

| Stato | Significato operativo | Azione tipica |
|---|---|---|
| **ATTIVO** | copertura in corso | usare/pianificare |
| **SOSPESO** | tempo scaduto, **sedute prepagate residue** = gliele DEVI | estendi / pianifica sedute / **chiudi con conguaglio** / decadi |
| **ESAURITO** | pacchetto consumato, **deve ancora denaro** | incassa il residuo / rinnova |
| **CHIUSO** | terminato — **qualificato dal motivo** (completamento o terminazione, §3.1) | — |

> **⚠️ Come si accende `chiuso` (corretto in v1.3).** Fino alla v1.2 si affermava che `chiuso` si
> accende **SOLO** su denaro saldato + crediti esauriti (auto-close). Quella frase descriveva **un solo
> percorso** — il *completamento*. La v1.3 riconosce un **secondo percorso**: la **terminazione
> anticipata esplicita** (§3.1), che accende `chiuso` su un contratto ancora **vivo** (ATTIVO o
> SOSPESO), *non* saldato/esaurito, previo **conguaglio**. Quindi `chiuso` si accende per **due vie**:
> (a) **auto-close** su saldato+esaurito = *completamento*; (b) **terminazione** per decisione umana =
> *recesso / risoluzione / chiusura consensuale*. CHIUSO **non è più indistinto**: porta sempre il
> **motivo** che dice da quale via è arrivato (§3.1). I 3 contratti `chiuso=1` con scadenza futura e
> crediti tutti da erogare trovati sul dato reale (id 4/9/13) sono esattamente terminazioni avvenute
> per la via (b) **senza** motivo né conguaglio — la patologia che la v1.3 chiude (§7-G7, remediation).

> **Regola d'oro:** lo stato di vita lo calcola SOLO `contract_state()`. Nessun endpoint/KPI ricalcola
> "attivo" per conto suo.

### 3.1 Terminazione anticipata — il terzo modo di morte (v1.3)

Nel modello, un contratto muore oggi in **due** modi:

- **Completamento** — denaro saldato **e** sedute esaurite → `chiuso` auto → **CHIUSO**. Morte
  *fisiologica*: il contratto ha dato tutto ciò che doveva.
- **Consunzione** — scade il tempo lasciando un asse aperto → **SOSPESO** (sedute residue) o
  **ESAURITO** (denaro residuo), poi una decisione umana lo regola (§7-G5). Morte *per esaurimento del
  tempo*.

La v1.3 aggiunge il **terzo** modo:

- **Terminazione anticipata** — una delle parti chiude il contratto **mentre è ancora vivo** (ATTIVO,
  oppure SOSPESO sul versante crediti), **prima del suo corso naturale**, con un **conguaglio
  economico**. Morte *per decisione attiva a metà corsa*.

È l'evento **più trasversale** del dominio: attraversa **tutti e tre gli assi insieme** — interrompe
il **tempo** (prima della scadenza), congela i **crediti** (sedute non erogate), muove il **denaro**
(conguaglio). Per questo non è un sottocaso di `delete` (che porta a ELIMINATO, fuori da ogni vista,
senza storia) né del `chiuso` di completamento (che presuppone i due assi esauriti). È un percorso
proprio, e va rappresentato come tale.

**Cosa registra la terminazione (dato strutturato):** *(colonna "Stato" aggiornata 2026-06-24: G7.0 ha aggiunto le 4 colonne)*

| Campo | Ruolo | Stato |
|---|---|---|
| `data_chiusura` | **quando** la terminazione ha effetto | ✅ **esiste** (`contract.py`, G7.0; scritto da `terminate`/`reopen`) |
| `motivo_chiusura` / `motivo_terminazione` | **perché/come** è chiuso: distingue *completamento* dalle terminazioni | ✅ **esiste** (`contract.py`, enum 4 valori, G7.0; **DERIVATO dall'esito** in `terminate`, mai COMPLETAMENTO) |

**Tassonomia dei motivi** (CHIUSO è sempre qualificato):

| Famiglia | Motivo | Quando | Cassa |
|---|---|---|---|
| *Completamento* | `completamento` (implicito/default dell'auto-close) | saldato + esaurito | — |
| *Post-scadenza* (§7-G5) | `sedute_decadute` · `saldo_a_perdere` | contratto **già scaduto** (SOSPESO/ESAURITO), si regola il residuo | nessuna, o storno |
| *Terminazione anticipata* (**v1.3**) | `recesso_cliente` · `risoluzione_trainer` · `chiusura_consensuale` | contratto **vivo** (ATTIVO/SOSPESO), tagliato a metà | **conguaglio** (rimborso e/o storno) |

> **Distinguibilità obbligatoria.** *Completamento* e *terminazione* possono avere assi identici a
> chiusura avvenuta (entrambi CHIUSO, entrambi a residuo zero dopo conguaglio). La differenza è **a
> memoria** (il *perché*), esattamente come ATTIVO è derivato ma «perso» è a memoria (§4.1). Perciò
> CHIUSO **non** ottiene un quinto stato di vita derivato: resta CHIUSO, **qualificato** dal motivo.
> Appiattire terminazione e completamento nello stesso CHIUSO indistinto è la perdita-di-informazione
> che il consolidamento esiste per evitare (ed è ciò che rende i 3 contratti muti irriconoscibili oggi).

> **`esito_rinnovo` ≠ `motivo_chiusura` (ortogonali — chiarito post-bridge).** `non_rinnova` **NON** è
> un motivo di chiusura: è un marker di **retention a livello cliente** (campo **esistente**
> `esito_rinnovo_motivo`) che dice «niente nuovo contratto» e fa **uscire il cliente dal win-back** —
> **non chiude** il contratto corrente, che resta nel suo stato di vita (tipicamente SOSPESO/ESAURITO)
> finché le sue assi aperte non sono regolate. Verificato sul codice: l'esito di rinnovo scrive
> `esito_rinnovo_motivo` e **lascia il contratto aperto** (`test_clients_to_recover`: il contratto
> resta, è solo escluso dal win-back). `motivo_chiusura` è invece il motivo per cui **IL CONTRATTO**
> diventa CHIUSO. I due **coesistono** a tempi e per ragioni diverse: un cliente può prima dichiarare
> `non_rinnova` (retention) e **poi** il suo contratto SOSPESO chiudersi per `sedute_decadute`
> (chiusura). **Sono due campi distinti, da non fondere.** Quando esiste già un esito di rinnovo,
> chiudere il contratto è un atto separato che valorizza `motivo_chiusura`.

#### Il conguaglio — funzione pura, su base SEDUTE

Al momento della terminazione una **funzione pura** (famiglia `contract_state.py`, niente DB) calcola
il **conguaglio**. La particolarità del dominio PT rispetto al SaaS è la **base di calcolo**: il SaaS
prora sul **tempo** (giorni usati / giorni totali); un pacchetto PT prora sulle **sedute**. Il valore
da regolare non è "i giorni che mancano alla scadenza" ma "le **sedute** pagate e non erogate". È
l'asse crediti che torna protagonista.

```
valore_servizio_reso = f(sedute_erogate, policy_prezzo_seduta)   # policy = DECISIONE APERTA
conguaglio           = valore_servizio_reso − totale_versato      # cassa sul servizio reso
```

| `conguaglio` | Significato | Gamba |
|---|---|---|
| **< 0** | il cliente ha **versato più** del servizio reso | **RIMBORSO** (il trainer restituisce `−conguaglio`) |
| **> 0** | il cliente ha **ricevuto più** di quanto versato | **da incassare** (G6) **oppure STORNO** (`saldo_a_perdere`) |
| **= 0** | pari e patta | solo chiusura |

In parallelo, la **quota non erogata** del contratto (`prezzo − valore_servizio_reso`) è **annullata**
(non sarà mai erogata): è lo **storno** che porta `residuo` a **zero** (§9.5). Le due gambe sono
simmetriche e corrispondono alla distinzione contabile **rimborso ≠ nota di credito**:

- **Gamba RIMBORSO (cassa esce).** `conguaglio < 0` → movimento **USCITA** datato di categoria
  **`RIMBORSO_CONTRATTO`** (con `id_contratto`) + `totale_rimborsato += −conguaglio`. È un **rimborso**:
  contante che torna al cliente. `totale_versato` **non si tocca**; il netto emerge da
  `netto_incassato = versato − rimborsato`.
- **Gamba STORNO (cassa non si muove).** la quota non erogata e/o il dovuto a cui il trainer rinuncia
  (`saldo_a_perdere`) si **stornano**: si **riduce il dovuto** senza movimento di cassa e **senza
  riscrivere `prezzo_totale`** (che resta la verità della *competenza/venduto*, §8). È una **nota di
  credito**: riduce un debito, non restituisce contante. Porta `residuo` a 0. Inoltre: le **rate future
  PENDENTI** del contratto si **soft-deletano** (non più dovute) — §7-G7, prerequisito Forecast.

> **Esempio compatto.** Pacchetto da 20 sedute, prezzo 1000, prepagato `versato = 700`. Il cliente fa 4
> sedute, poi recede. Con policy "pro-sedute a prezzo di pacchetto" → `valore_servizio_reso = 200`.
> `conguaglio = 200 − 700 = −500` → **rimborso 500** (USCITA `RIMBORSO_CONTRATTO`, `totale_rimborsato =
> 500`). La quota mai erogata e mai incassata (`prezzo − versato = 300`) si **storna**. Esito:
> `netto_incassato = 700 − 500 = 200` (= valore reso ✓), `residuo = 0` ✓. `totale_versato` resta 700,
> `prezzo_totale` resta 1000 (il *venduto* storico non cambia).

> **`residuo` e il debito-fantasma — la trappola da evitare.** NON calcolare mai `residuo = prezzo −
> (versato − rimborsato)`: nell'esempio darebbe `1000 − 200 = 800`, cioè il sistema affermerebbe che il
> cliente **deve ancora 800** dopo che gli hai **restituito** denaro. È il debito *inventato*, speculare
> al debito *nascosto* dei 3 contratti muti. La verità è che la terminazione **regola** tutto: dopo di
> essa `residuo ≡ 0` (§9.5). Il `residuo` formula `prezzo − versato` vale per i contratti **non**
> terminati; per i terminati è zero per costruzione (rimborso) o via storno (write-off).

#### Decisione Strada B (vincolante)

Tra le due architetture possibili per la verità del "netto incassato" dopo un rimborso, è scelta la
**Strada B**:

- **Movimento di denaro sacro** (disciplina della Strada A dove conta): il rimborso è una **USCITA
  datata immutabile** nel mastro, **mai** una cancellazione né una modifica dell'ENTRATA originale —
  stesso principio dello `STORNO_SPESA_FISSA` (compensa, non cancella).
- **Proiezione KPI pragmatica** (niente refactoring totale): i KPI contrattuali continuano a leggere i
  **campi del Contract** (`totale_versato`, `residuo`, e ora `totale_rimborsato`/`netto_incassato`),
  **non** si riscrivono per derivare dal mastro. `totale_rimborsato` è il **ponte** che rende il
  rimborso visibile ai KPI senza migrare ogni query al ledger.
- **Contropartita non negoziabile (§9.5):** il rimborso scrive in **due posti in una sola transazione
  atomica** — USCITA nel mastro **e** `totale_rimborsato` sul Contract — *o entrambi o nessuno*, così
  mastro e Contract **non divergono mai**. Questo è l'invariante che tiene in piedi la scelta.

#### Policy di rimborso — DECISIONE APERTA (non blocca il modello)

Il modello fissa *che* l'evento esiste e *che forma* ha. I **numeri** della policy restano da chiudere
con **tributarista/legale** prima dell'implementazione del blocco:

1. **Rimborso pro-sedute come default sì/no.** I pacchetti PA prepagati assomigliano più
   all'abbonamento annuale (importo significativo, prepagato → rimborso atteso) che al mensile (servizio
   fino a fine periodo, nessun rimborso). Default plausibile: **pro-sedute**, ma è scelta contrattuale.
2. **Prezzo di valorizzazione delle sedute usate.** Listino pieno o prezzo scontato del pacchetto? Un
   cliente che recede dopo le prime sedute di un pacchetto scontato deve indietro **meno** se le sedute
   usate si valorizzano a prezzo pieno. Cambia il numero del conguaglio.
3. **Recesso del consumatore (legge IT).** Il recesso ha tutele specifiche; va verificato l'inquadramento.

Finché la policy non è chiusa, la **funzione di conguaglio** ha **forma** definita (input: contratto,
data di efficacia, policy; output: numero con segno; base: sedute) ma il **parametro policy** è aperto.

---

## 4. Vocabolario non negoziabile (contratto)

Tre termini erano usati con significati diversi → d'ora in poi:

| Termine | Significato UNICO |
|---|---|
| **aperto** | `chiuso = False` (qualsiasi stato di vita tranne CHIUSO/ELIMINATO) |
| **attivo** | stato di vita **ATTIVO** (= aperto **e** vigente). **MAI** "attivo = chiuso==False" |
| **scaduto** | `data_scadenza < oggi` (asse tempo) — è una *condizione*, non uno stato di vita |
| **terminazione** (v1.3) | chiusura **per decisione umana di un contratto vivo** (recesso/risoluzione/consensuale), con conguaglio — **distinta** dal *completamento* (auto-close) e dalla *consunzione* (scadenza). CHIUSO è sempre qualificato dal `motivo_chiusura` |
| **conguaglio** (v1.3) | regolamento economico della terminazione, calcolato **sulle sedute**; segno: `<0` rimborso al cliente, `>0` dovuto dal cliente, `=0` pari |
| **insolvente** (consumo UI) | **flag derivato cross-asse**, NON uno stato: `lifecycle ∈ {SOSPESO, ESAURITO}` **AND** `rate scadute`. Il modello resta a **4 stati + ELIMINATO** (§3); nessun badge-asse proprio; **mutuamente esclusivo con `in_scadenza`** per costruzione (uno scaduto, l'altro ATTIVO). È il sotto-caso *scaduto* del segnale "denaro arretrato" (`rate_scadute`), che su un ATTIVO si chiama "in ritardo". Definizione e resa UI vincolanti: `SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` |

> **"insolvente" è solo *consumo* del modello, non un'estensione.** Vive come predicato puro
> (`is_insolvente(state)`) nel SSoT `contract_state.py`, gemello di `is_rate_planificabile`/
> `is_residuo_incassabile_diretto`, e non aggiunge stati di vita né colonne. Registrato qui perché aveva
> **tre definizioni divergenti** nel frontend: il consolidamento del vocabolario lo riporta a una sola.

### 4.1 Rollup cliente — natura MISTA: derivato + a memoria

Lo stato cliente ha **due nature diverse** (come il contratto: ATTIVO è derivato, esito-non-rinnova è
a memoria). Non confonderle:

| Stato cliente | Natura | Derivazione / fonte |
|---|---|---|
| **ingaggiato** | **derivato** | ha ≥1 contratto **ATTIVO o SOSPESO** |
| **lapsed (caldo)** | **derivato** | non ingaggiato, ha contratti, entro la soglia churn (§4.2) → worklist win-back |
| **lapsed-freddo** | **derivato** (da `communication_log` + tempo) | lapsed **oltre** la soglia churn, *e* ultimo richiamo loggato oltre soglia (o nessun richiamo) → **esce** dalla worklist calda |
| **perso** | **a memoria** | il trainer ha registrato "non rinnova" (`esito_rinnovo_motivo`) |

> Il **"freddo" è derivato**, non un nuovo campo: riusa `communication_log` (il richiamo WhatsApp è già
> loggato). `freddo = lapsed AND giorni_lapse > SOGLIA_CHURN AND (nessun richiamo o ultimo richiamo > SOGLIA_CHURN)`.
>
> **Assunzione esplicita (proxy del richiamo):** il raffreddamento usa i **contatti loggati** in
> `communication_log` come *proxy* del contatto reale. Un richiamo **non loggato** (telefono, di persona)
> NON sposta lo stato → un cliente realmente ricontattato può restare "caldo" oltre soglia. È una
> semplificazione accettata (loggare ogni contatto = frizione che il PT efficienza-driven non vuole);
> dichiarata qui perché non diventi un mistero futuro ("perché è ancora caldo se l'ho chiamato?").

**Decadimento asimmetrico (vincolante):**
- **lapsed → si raffredda**: è un'*opportunità*; dopo la soglia churn + ultimo richiamo, esce dalla
  worklist calda (diventa freddo). La worklist win-back non cresce all'infinito.
- **SOSPESO → si scalda, non decade mai**: è un'*obbligazione* (gli devi sedute). Nessuna uscita
  automatica; l'aging **aumenta** l'urgenza (segno invertito). Esce solo per decisione (estendi /
  **chiudi con conguaglio** / decadi).

### 4.2 Costanti temporali (dichiarate UNA volta)

Tutte le finestre-tempo vivono qui, isolate, per non sdoppiarsi (no numeri magici sparsi):

| Costante | Valore | Uso |
|---|---|---|
| `SOGLIA_IN_SCADENZA_GG` | 30 | ATTIVO entra in "in scadenza" |
| `SOGLIA_CHURN_GG` | 90 | **unica**: confine churn = raffreddamento lapsed = finestra retention (G3). Un cliente che torna ingaggiato entro 90gg dal lapse = *retained*; oltre = *churned/freddo* |

> Cooling, retention-window (G3) e definizione-di-churn sono **lo stesso concetto** → una costante sola.

---

## 5. Sotto-stato denaro (ortogonale allo stato di vita)

Su un contratto aperto, indipendente dallo stato di vita:

| Sotto-stato | Derivazione |
|---|---|
| **saldato** | `residuo = 0` — **sempre e solo** "pagato" grazie all'invariante `prezzo > 0` (§9.5.7): mai "prezzo mancante" |
| **da pianificare** | `residuo > 0` e nessuna Rata (zero rate non eliminate) |
| **parzialmente pianificato** | rate presenti ma `Σ residui rate non-saldate < residuo` |
| **pianificato** | `Σ residui rate non-saldate ≈ residuo` |
| **rate scadute** | ≥1 rata non-saldata con `data_scadenza < oggi` |

"Rate non-saldate" = `stato ∈ {PENDENTE, PARZIALE}` (allineato all'aging).

> **"rate scadute" ha UNA sola fonte.** Il SSoT `rate_scadute` (`evaluate_contract`) alimenta sia questo
> sotto-stato, sia il flag-riga "denaro arretrato", sia il filtro Situazione, sia `is_insolvente` (§4). La
> formula-riga "larga" preesistente (`ha_rate_scadute`, `contracts.py`) va derivata da qui o documentata come
> suo alias — niente seconda formula viva (`SPEC_VOCABOLARIO_E_CLASSIFICAZIONE_CONTRATTI.md` §2.1/AC-1b).

> **Contratti terminati (v1.3).** Un contratto CHIUSO per terminazione è **regolato** (settled): il
> conguaglio ha portato `residuo` a 0 e le rate future sono soft-deleted. Non compare quindi in alcun
> sotto-stato denaro "da pianificare / da incassare / rate scadute". Se compare, è un bug (§9.5).

---

## 6. Mappa worklist → derivazione (univoca, senza sovrapposizioni)

Ogni contratto/cliente ha **uno stato di vita primario** + **flag denaro secondari**. Le worklist
derivano da qui, senza doppi conteggi:

| Worklist | Deriva da | Note |
|---|---|---|
| **In scadenza** | ATTIVO + `data_scadenza ≤ oggi+SOGLIA_IN_SCADENZA_GG` | rinnovo anticipato |
| **Contratti sospesi (sedute)** | **SOSPESO** | unità = contratto; **estendi / chiudi-con-conguaglio / decadi**; **non decade, urgenza ↑** |
| **Clienti da recuperare (win-back)** | cliente **lapsed CALDO** (non freddo, non perso) | unità = cliente; rappresentante = contratto più recente in assoluto; esce quando freddo (§4.1) |
| **Da pianificare (rate)** | **ATTIVO** + `da pianificare` | **solo ATTIVO** (vedi §7 G1) |
| **Da incassare (scaduto)** | (SOSPESO o ESAURITO) + `residuo > 0` | incasso diretto, non pianificabile a rate |
| **Rate scadute / aging** | Rate non-saldate oltre scadenza | rate-first |
| **Andamento (cassa/competenza)** | libro mastro datato | ortogonale (vedi §8) |

> **Le tre azioni su un SOSPESO (v1.3).** Chiudere un SOSPESO non è binario. Sono **tre** esiti distinti,
> e la UX del Blocco 3 va disegnata per accoglierli tutti e tre fin dall'inizio:
> 1. **Estendi** — sposta `data_scadenza` avanti: il SOSPESO torna ATTIVO, le sedute restano erogabili.
> 2. **Chiudi con conguaglio** (`recesso_cliente` / `chiusura_consensuale`) — il cliente non userà le
>    sedute residue e **vuole indietro** il prepagato → terminazione con **gamba rimborso** (§3.1).
> 3. **Decadi** (`sedute_decadute`) — le sedute residue sono **forfettate**, nessun rimborso → chiusura
>    con **gamba storno** a saldo zero di cassa.
> «Estendi vs decadi» (v1.2) era una falsa dicotomia: mancava la terza via, il rimborso.
>
> **⚠️ Design-scope ≠ build-scope (precisato post-bridge).** La UX del Blocco 3 si **disegna** per
> accogliere tutte e tre fin dall'inizio (i tre bottoni esistono), ma solo **Estendi** è
> **costruibile** nel Blocco 3 (`update_contract` su `data_scadenza`: niente cassa, niente schema
> nuovo). Le **due gambe di chiusura** — *Chiudi con conguaglio* (rimborso, infra G7) e *Decadi*
> (storno del residuo, G7 / G5-mai-implementato) — atterrano **col blocco terminazione**, dove vivono
> i campi schema (`data_chiusura`, `motivo_chiusura`) e la macchina del conguaglio. **Anche «Decadi a
> `residuo` zero»** (pura chiusura+motivo, senza cassa) resta lì: spezzare la migrazione dello
> schema-di-chiusura per anticipare un solo sotto-caso frammenta una superficie che va costruita **come
> unità coerente**. Quindi: **Blocco 3 = worklist + Estendi**; ogni *chiusura* (qualsiasi gamba,
> qualsiasi `residuo`) = **blocco terminazione**. Nel Blocco 3 i due bottoni di chiusura erano disabilitati
> «disponibile a breve» → **[✅ G7.3/G7.4: cablati]** ora attivi: un **"Termina"** (copre conguaglio e
> decadenza, esito DERIVATO) + **"Riapri"** sui contratti chiusi.

---

## 7. Lacune risolte a livello di modello (G1–G7)

- **G1 — residuo su contratto scaduto NON è "da pianificare".** La guardia rate vieta rate oltre
  `data_scadenza` (passata) → su SOSPESO/ESAURITO non si può creare una rata. Quindi **"da pianificare"
  è ristretto ad ATTIVO**; il residuo su contratti scaduti vive in **"da incassare (scaduto)"** (incasso
  diretto o previa estensione del contratto). Niente azioni impossibili.
  - **⚠️ DEBITO già in codice**: `orphan_contracts`/`contracts-to-plan` (SPEC_RINNOVO, già implementati)
    filtrano `chiuso=False + residuo>0 + zero rate` **senza** restrizione di vigenza → includono i
    SOSPESO/ESAURITO e offrono l'azione impossibile. **Da correggere** (restringere ad ATTIVO) — primo
    fix che il modello fa emergere nel codice esistente. *(Stato: chiuso nel Blocco 1.)*
- **G2 — niente worklist sovrapposte.** Classificazione = **1 stato di vita primario** + flag denaro.
  Un SOSPESO con residuo e zero rate è in "Contratti sospesi" (primario) e "Da incassare (scaduto)"
  (flag denaro) — **mai** in "Da pianificare" (riservato ad ATTIVO).
- **G3 — analytics rinnovi (renewal rate).** `rinnovo_di` cattura solo i rinnovi col bottone; un nuovo
  contratto non collegato non è linkato → il renewal-rate sottoconterebbe. **Definizione di modello:**
  un cliente è *retained* se torna ingaggiato entro **`SOGLIA_CHURN_GG`** (§4.2, la **stessa** costante
  del raffreddamento lapsed), indipendentemente da `rinnovo_di`. Churn/retention usano la **continuità
  cliente**, non solo il link. (Implementazione differita; concetto + costante fissati qui.)
- **G4 — KPI "attivi".** `kpi_attivi` deve contare lo stato **ATTIVO** (aperto+vigente), non
  `chiuso==False`. I contratti aperti-non-attivi (SOSPESO/ESAURITO) si mostrano separati. Tutti i KPI
  derivano da `contract_state()`. *(Stato: chiuso nel Blocco 2.)*
- **G5 — chiusura/terminazione con motivo.** Ogni chiusura per **decisione umana** registra un
  `motivo_chiusura` (dato strutturato): `sedute_decadute` (sospeso, sessioni forfettate),
  `saldo_a_perdere` (residuo abbonato), più i tre di **terminazione anticipata** (§3.1). Niente
  terminazioni mute.
  - **⚠️ `non_rinnova` NON è un motivo di chiusura (corretto post-bridge).** È un marker di **retention
    a livello cliente** (`esito_rinnovo_motivo`, campo **esistente**), su un asse **ortogonale** al
    `motivo_chiusura`: **non chiude** il contratto (verificato: `test_clients_to_recover` — il
    contratto resta aperto, è solo escluso dal win-back). I due campi coesistono per ragioni diverse
    (§3.1). La v1.2 li elencava insieme; qui sono separati.
  - **⚠️ Esteso in v1.3 (G7).** I motivi G5 coprono le decisioni **post-scadenza** (contratto già
    SOSPESO/ESAURITO). La v1.3 aggiunge i motivi di **terminazione anticipata** (contratto **vivo**) e,
    soprattutto, la **macchina del conguaglio** (rimborso in cassa) che G5 non aveva — G5 prevedeva solo
    storni/forfait, **mai un'uscita di cassa verso il cliente**. G5 non era mai stato implementato → il
    meccanismo di storno della gamba write-off (§3.1) e G5 si sono **unificati nel blocco terminazione**
    (**✅ G7.1/G7.3:** `quota_stornata` azzera il residuo, scritto da `terminate`; rimborso = `RIMBORSO_CONTRATTO`).
- **G6 — manca il pagamento DIRETTO del residuo (v1.2).** Oggi si incassa **solo via Rata** e su uno
  **scaduto** non si può creare una rata (guardia G1). Quindi un residuo **non rateizzato** su contratto
  scaduto è **non incassabile** (verificato: Dalila c25, 20€). **Fix:** azione "incassa residuo" diretta
  (CashMovement legato al contratto + `totale_versato` += importo + auto-close).
  - **Verifica auto-close su scaduto: ✓ confermata.** `pay_rate` auto-close è **date-independent**
    (`rates.py:559-570`): incassare l'ultimo residuo di un ESAURITO lo porta a CHIUSO anche se scaduto →
    nessun ESAURITO-fantasma a residuo zero.
  - **Dipendenza con G7.** Il rimborso (G7) è cassa **diretta in uscita** sul contratto; G6 costruisce
    la prima cassa **diretta in entrata** sul contratto. **Stesso pattern, segno opposto** → G7 riusa
    l'infrastruttura di G6. **Sequenza vincolata: G6 prima, terminazione dopo.**

- **G7 — terminazione anticipata con conguaglio (v1.3, NEW).** Il contratto non ha un percorso per
  essere **chiuso a metà corsa con regolamento economico bidirezionale**. Conseguenze sul codice reale,
  verificate in ricognizione:
  - **Sta già succedendo muto.** 3 contratti (id **4, 9, 13**) sono `chiuso=1` con scadenza **futura**,
    saldati, **tutti i crediti da erogare**, zero `rinnovo_di`/`esito`. Terminazione anticipata avvenuta
    via `update_contract chiuso=true` (setattr generico, `contracts.py:646-648`) **senza** conguaglio né
    traccia: il residuo/le sedute spariscono da "da incassare" mentre prezzo/versato/crediti restano →
    **debito non cancellato, nascosto**. → **Remediation dati** (sotto).
  - **Il rimborso è infrastruttura nuova.** Lo schema mastro regge una **USCITA con `id_contratto`**
    senza migrazione (`movement.py:42-47`), ma **0 casi** esistono nel DB e `MovementManualCreate`
    **vieta** `id_contratto` (`financial.py:327`). Va costruita: categoria `RIMBORSO_CONTRATTO`,
    endpoint transazionale, registrazione del rimborso, storno del residuo, calcolo conguaglio.
  - **I due sottosistemi finanziari non convergono — la terminazione li costringe a incontrarsi.**
    Contratti/rate **cancellano** (soft-delete dell'ENTRATA: `contracts.py:754`, `rates.py:680`); le
    spese **compensano** (storno immutabile: `recurring_expenses.py:588`). La terminazione corretta è
    **ibrida**: **rimborso = nuovo movimento USCITA** (compensa, preserva la traccia fiscale); **rate
    future = soft-delete** (cancella, già esistente). `delete_contract` (force+keep_payments) porta a
    **ELIMINATO, non a CHIUSO-con-storia**: semantica sbagliata per una terminazione **visibile**.
  - **La categoria deve essere classificata da un predicato esplicito.** La "whitelist cassa
    contrattuale" **✅ ora esiste** (`cash_categories.py`, `CONTRACT_CASH_IN/OUT`, Prereq P0); ante-P0 non
    c'era e le query partizionavano per `id_contratto IS NOT NULL`, non per categoria — una USCITA
    contrattuale cadeva **automaticamente** in 3 aggregati di uscite-variabili (misclassificata come **costo
    operativo**). **L'allineamento delle ~7 query residue al predicato resta G7.5.** → Il predicato "movimento contrattuale"
    va reso **esplicito e bidirezionale** (entrata: ACCONTO/RATA; uscita: RIMBORSO) — dettaglio in
    `TASSONOMIA_FINANZIARIA.md` §2/§7 (v1.2). **9 query** da allineare (mappate nella tassonomia; la 9ª,
    `get_dashboard_summary.monthly_revenue`, emersa dalla review bridge sul codice vivo).
  - **Prerequisito Forecast.** Le rate **PENDENTI** su un contratto CHIUSO-non-eliminato sono proiettate
    dal Forecast come **entrata certa fantasma** (filtra solo `deleted_at`, `movements.py:1432-1441`) →
    la terminazione **deve soft-deletare le rate future**.
  - **Prerequisito auditabilità.** La transizione `chiuso` oggi è auditata in modo **inaffidabile**
    (`pay_rate` non logga `chiuso`, `rates.py:598-601`; l'agenda audita l'evento non il contratto). La
    terminazione — l'evento **più importante da tracciare** legalmente — non può ereditare un audit
    bucato. → **Auditabilità della transizione `chiuso` è prerequisito del blocco.**
  - **Fork risolto (Strada B).** Verità del netto: campo `totale_rimborsato` immutabile sul Contract, KPI
    sui campi, sync atomico mastro+Contract (§3.1, §9.5).
  - **Remediation dati (id 4/9/13) — su DATO VIVO.** Una volta che il modello esiste e l'evento è
    rappresentabile, i 3 contratti muti vanno regolarizzati: riconosciuti come terminazioni col loro
    conguaglio **ricostruito**, oppure riaperti se la chiusura fu un errore. **Non si toccano** finché
    il blocco non esiste. **Sono contratti reali di Chiara (dato di produzione):** la regolarizzazione è
    una **procedura a sé** — **per-contratto, auditata, reversibile, mai uno script bulk** — da scrivere
    come **runbook separato**, non come parte dell'implementazione del meccanismo.

---

## 8. Asse cassa / competenza (da `TASSONOMIA_FINANZIARIA.md`)

Ortogonale agli stati: misura il **flusso nel tempo**, non lo stato del contratto.
- **Cassa** (primaria, forfettario): incassato su `CashMovement.data_effettiva`, ristretto alle categorie
  contrattuali, **storni esclusi**; "Altri incassi" (fuori contratto) separati; "cash flow reale" = somma.
  - **v1.3:** la cassa contrattuale diventa **bidirezionale** — gli **incassi da contratti** sono ora al
    **netto dei rimborsi** (`RIMBORSO_CONTRATTO`). Il "cash flow reale dei contratti" passa da `Σ incassi`
    a **`Σ incassi − Σ rimborsi`**. Dettaglio e formule: `TASSONOMIA_FINANZIARIA.md` §1/§2/§7 (v1.2).
- **Competenza** (secondaria, commerciale): venduto su `Contract.data_vendita`. **Mai sommata alla cassa.**
  - **v1.3:** la terminazione **non riscrive `prezzo_totale`** → il *venduto* storico resta integro
    (un'altra ragione per cui lo storno usa un campo dedicato e non la riscrittura del prezzo, §3.1).
- Confine §0 TASSONOMIA: cash management **neutro**, nessun campo/label codifica lo stato fiscale.

Dettaglio completo e formule: `TASSONOMIA_FINANZIARIA.md` (resta valido; questo §8 è il puntatore).

---

## 9. Invarianti (anti-perdita silenziosa)

Nessuno di questi può sparire da una worklist o da un conto senza **decisione umana esplicita**:
1. **Denaro dovuto** (residuo > 0): da pianificare (ATTIVO) o da incassare (scaduto) o aging.
2. **Sedute prepagate** (SOSPESO): estendi / chiudi-con-conguaglio / decadi.
3. **Cliente lapsed**: recupera o "non rinnova".
4. **Rimborso dovuto al cliente (v1.3)**: quando la terminazione produce un conguaglio a favore del
   cliente (sedute prepagate non erogate), quel rimborso **non sparisce senza essere registrato**. È lo
   **speculare** del SOSPESO: lì è il **cliente che deve al trainer** (gli devi le sedute), qui è il
   **trainer che deve al cliente** (gli devi indietro il denaro). Un rimborso dovuto e non tracciato è
   una **passività occulta** ed espone legalmente — la protezione che distingue il prodotto vale **anche
   e di più** sul lato uscita.

### 9.4 Invariante delle transizioni indotte dal tempo (v1.1 — la lezione del SOSPESO)

`contract_state()` è corretto ma **inerte**: risponde solo se interrogato. Il difetto SOSPESO non fu
un dato sparito ma una **transizione muta** — ATTIVO→SOSPESO / ATTIVO→ESAURITO avvengono per pura
aritmetica della data, senza che nessun evento le segnali. (Le transizioni *event-induced*, es. usare
l'ultima seduta → ESAURITO, fanno già rumore; il rischio è solo sulle **time-induced**.)

**Invariante:** *ogni stato non-terminale deve avere una worklist/alert che lo accoglie — nessuno
stato "homeless".* Così la transizione indotta dal tempo **fa rumore** alla prossima apertura: la
**membership nella worklist È il segnale** (modello pull). Verifica di copertura: ATTIVO→in-scadenza,
SOSPESO→contratti-sospesi, ESAURITO→da-incassare + (cliente) clienti-da-recuperare. Se aggiungi uno
stato e non gli dai casa, hai ricreato la perdita silenziosa.

> **Push (futuro):** rilevamento attivo delle transizioni anche ad app chiusa (notifica) richiede un
> always-on (FitManager Box / tunnel). Ora il pull-coverage è sufficiente per un'app locale.

### 9.5 Invariante di coerenza del netto — Strada B (v1.3)

La scelta Strada B (§3.1) mantiene **due rappresentazioni** del denaro effettivamente trattenuto: il
**mastro** (somma firmata dei movimenti) e i **campi del Contract** (`totale_versato`,
`totale_rimborsato`). Se divergono, il sistema **mente in silenzio**. Invarianti che lo impediscono:

1. **`totale_versato` è LORDO e immutabile a ritroso**: `totale_versato == Σ ENTRATA(contratto)`. Un
   rimborso **non lo riduce**.
2. **Scrittura atomica del rimborso**: ogni rimborso scrive **in una sola transazione** sia la **USCITA
   `RIMBORSO_CONTRATTO`** nel mastro sia l'incremento di **`totale_rimborsato`** sul Contract — *o
   entrambi o nessuno*. Mastro e Contract non divergono mai.
3. **Netto derivato**: `netto_incassato = totale_versato − totale_rimborsato`. È l'unica nozione di
   "cassa trattenuta" sul contratto.
4. **`residuo ≡ 0` dopo terminazione**: un contratto CHIUSO per terminazione è **regolato**. Il
   conguaglio porta il residuo a zero — per costruzione nella gamba rimborso (versato già ≥ valore
   reso), via **storno** nella gamba write-off (riduzione del dovuto **senza** riscrivere
   `prezzo_totale`). **Mai** un residuo aperto né un debito **inventato** su un contratto terminato
   (`residuo = prezzo − versato − storni`, non `prezzo − (versato − rimborsato)`). Le **rate future**
   sono soft-deleted (no fantasmi nel Forecast).
5. **Atomicità delle due gambe**: rimborso (cassa) e storno (dovuto) sono **due facce dello stesso
   evento contabile** → **transazione unica, tutto-o-niente**. Mai denaro restituito con residuo ancora
   dovuto, né viceversa.
6. **`quota_stornata > 0 ⟹ chiuso = True`** (coupling reso esplicito, dal piano di strategia). Lo storno
   avviene **solo** terminando (gamba write-off / decadenza), che accende `chiuso`; `reopen`/`unterminate`
   lo azzerano. L'invariante è **load-bearing**: alcuni KPI calcolano il residuo **inline senza**
   sottrarre `quota_stornata` e sono corretti **solo** perché filtrano i contratti aperti (`if not
   chiuso`). Va **asserito/documentato** — oppure quelle formule migrano a `contract_state.residuo()`.
   Un `quota_stornata > 0` su un contratto **aperto** è uno stato impossibile: se compare, è un bug.

   > **Semantica di riapertura — guard ALLOWLIST (delta v1.3, review bridge + addendum §6).** L'auto-riapertura
   > credit-driven (`agenda._sync_contract_chiuso`: `chiuso` da `True` a `False` quando i crediti non sono più
   > esauriti) scatta **SOLO se `motivo_chiusura == COMPLETAMENTO`**. Ogni altro valore — `TERMINAZIONE_*`,
   > **e `NULL` (chiusura manuale o legacy)** — **non si riapre automaticamente**; solo `reopen`/`unterminate`
   > espliciti la riaprono. ⚠️ **Allowlist, NON denylist**: una denylist (`non riaprire se motivo ∈ TERMINAZIONE_*
   > o quota_stornata>0`) **manca il caso reale** della chiusura *manuale* (`motivo=NULL`, nessuno storno) —
   > che è proprio quella già latente oggi e quella esercitata dal test. Riaprire una terminazione produrrebbe
   > lo **stato zombie** `chiuso=False ∧ quota_stornata>0`, che questo invariante dichiara impossibile.
   >
   > **Due prerequisiti non negoziabili (load-bearing in entrambe le direzioni):**
   > 1. **Il completamento DEVE marcarsi.** I percorsi di auto-close per completamento (`pay_rate`; ramo di
   >    chiusura di `_sync_contract_chiuso`) devono **scrivere `motivo_chiusura = COMPLETAMENTO`** quando chiudono.
   >    Senza, la allowlist congela **anche** le riaperture legittime (es. completato → si cancella per errore una
   >    seduta → deve tornare a dover una seduta → deve riaprirsi): preservato **solo** se il completamento porta `COMPLETAMENTO`.
   > 2. **Doppio significato del `NULL`, dichiarato.** La guard tratta `NULL` in modo **conservativo (non-riaprire)**;
   >    il runbook (§3.1/§11) legge il `NULL` legacy come **`COMPLETAMENTO` implicito** (solo classificazione/analytics).
   >    Conseguenza **accettata**: un completamento **legacy** (`motivo=NULL`, pre-G7) non si auto-riapre più su modifica
   >    d'agenda — direzione **sicura** (non resuscita uno stato a debito nascosto); se serve, il trainer riapre a mano.
   >
   > **Già latente oggi** (non solo post-G7): una chiusura *manuale* di un contratto non-completato viene riaperta
   > alla prima mutazione d'agenda su un suo evento PT. Fix **vincolante in G7** (allowlist + marcatura completamento;
   > la colonna `motivo_chiusura` esiste solo lì). Tracciato da
   > `test_lifecycle_audit.test_manual_close_not_reopened_by_agenda_edit` (**xfail strict** → xpass **solo** quando
   > atterrano **entrambi** i prerequisiti). Mitigante presente: la transizione è già auditata.
   >
   > **Alternativa più pulita (decisione di Giacomo, scope G7):** **togliere `chiuso` da `update_contract`** →
   > le chiusure passano solo da `terminate`/`close` (che scrivono il motivo), `reopen` resta. Così la
   > «chiusura-manuale-senza-motivo» **non esiste più**, la collisione del `NULL` sparisce, e il test va riscritto
   > su una terminazione vera. Elimina la categoria di stati ambigui alla radice (costo: schema-input + call-site).
7. **`prezzo_totale > 0` per ogni contratto creato** (invariante di creazione — PREREQ-prezzo di G6).
   Un contratto **esiste** solo con un prezzo strettamente positivo: è l'atto che attiva le coperture
   (assicurative/fiscali) e abilita gli incassi. Conseguenza: l'equivalenza `residuo = 0 ⟺ saldato` (§5) è
   vera **senza asterischi** — `residuo = 0` significa **sempre e solo** "saldato", **mai** "prezzo mai posto".
   Un `prezzo_totale` nullo/zero su un contratto **non eliminato** è uno stato **impossibile**: se compare è
   un bug (o un legacy pre-invariante da bonificare). Enforce **al boundary** (`ContractCreate` **e**
   `ContractUpdate`, `api/schemas/financial.py`, messaggio IT didattico); il tipo ORM resta `Optional` (legacy
   ammesso) ⇒ le due guardie di consumo del frontend (Giro 1, `prezzo != null`) restano come
   **difesa-in-profondità a costo zero** — annotate, non da rimuovere.

   > **Simmetria credito-/debito-fantasma — `residuo` ha UN solo significato.** Ai due estremi dell'asse denaro
   > la stessa disciplina: il **debito-fantasma** (residuo che afferma un dovuto inesistente dopo un rimborso) si
   > chiude con un **campo dedicato** (§9.5.6, `quota_stornata`) perché quello stato *deve* esistere; il
   > **credito-fantasma** (residuo 0 che afferma "pagato" senza prezzo) si chiude con un **invariante a monte**
   > (questo §9.5.7, `prezzo > 0`) perché quello stato **non deve** esistere. La decisione di design che separa le
   > due strade: *stato di processo* (legittimamente incompleto → sotto-stato + worklist) vs *vincolo di integrità*
   > (non deve mai esistere → validazione a monte). Qui il dominio («niente prezzo = niente contratto/coperture»)
   > qualifica il caso come integrità ⇒ invariante, non un sesto sotto-stato.

E: `kpi_incassato = Σ totale_versato` (NON somma del mastro); il cash flow reale (con Altri incassi)
non riconcilia con `kpi_incassato` — è atteso (TASSONOMIA §3).

> **Netto vs lordo per vista — enumerato, non «dove serve» (precisato post-bridge).** Appena esistono
> rimborsi, una card «Incassato» che mostra `Σ totale_versato` (lordo) **sovrastima**. Quale vista usa
> cosa è **decisione fissata qui**, non lasciata all'implementazione:
>
> | Vista | Base | Perché |
> |---|---|---|
> | Card «Incassato» / KPI incassato visualizzato | **netto** (`Σ netto_incassato`) | il trainer vuole sapere cosa ha **trattenuto** |
> | Andamento cassa — serie contratti | **netto** per periodo (incassi − rimborsi) | TASSONOMIA §7 q#5 |
> | Saldo / cash reale | **già netto** (l'USCITA sottrae da sé) | TASSONOMIA §7 q#1 |
> | Venduto (competenza) | **`prezzo_totale`** (invariato) | i rimborsi non toccano la competenza |
> | Reconciliation (interna) | `totale_versato` **LORDO** `== Σ ENTRATA` **+** `totale_rimborsato == Σ USCITA RIMBORSO` | è l'**àncora di consistenza**, non una vista «incassato»: resta sul lordo per definizione |
>
> Regola: ogni numero che il trainer legge come «quanto è entrato» dai contratti è **netto**; il
> **lordo** sopravvive solo come **sorgente del netto** e **àncora della reconciliation**.

---

## 10. SSoT lato codice

- **Un modulo `contract_state()`** (es. `api/services/contract_state.py` o helper condiviso): data un
  contratto (+ crediti_usati), ritorna lo stato di vita + sotto-stato denaro. **Unica fonte** della
  derivazione; KPI, worklist, alert lo consumano. Vietato ricalcolare "attivo/scaduto" altrove.
  - **v1.3:** stessa famiglia (funzioni pure, niente DB) ospita il **calcolo del conguaglio** (input:
    contratto, data di efficacia, policy; output: numero con segno; base: sedute). Il **parametro
    policy** è aperto finché non chiuso col tributarista.
- Le viste/endpoint diventano *query + presentazione* sopra `contract_state()`.

---

## 11. Rapporto con le spec-feature

| Doc | Ruolo dopo questo modello |
|---|---|
| `FINANCIAL_DOMAIN_MODEL.md` (questo) | **SSoT**: entità, assi, stati, vocabolario, worklist, invarianti |
| `TASSONOMIA_FINANZIARIA.md` | dettaglio asse cassa/competenza (referenziato §8) — **v1.2** include `RIMBORSO_CONTRATTO` e il predicato contrattuale bidirezionale |
| `SPEC_RINNOVO_*`, `SPEC_*_TEMPORALE`, `SPEC_RINNOVI_SCADUTI_*` | solo *criteri di accettazione* della feature; **referenziano** stati/vocabolario di qui |
| `SPEC_G7.0` + `SPEC_G7.3` (✅ scritte, IMPLEMENTATE) | criteri di accettazione della terminazione anticipata (schema G7.0 + endpoint/conguaglio G7.3); referenziano §3.1/§7-G7/§9.5. La policy `pro_sedute` è default **PROVISIONAL** (valorizzazione numerica gated dal tributarista, ma NON ha bloccato la struttura) |
| `IMPL_PLAN_*` | effimeri; in `docs/archive/` a implementazione conclusa |
| `ADR-014`, `ADR-015` | decisioni (immutabili) |

> **Sequenza di implementazione (v1.3, precisata post-bridge).** Blocco 3 = **worklist sospesi +
> Estendi** (la UX *disegna* le 3 azioni, §6; ma le due gambe di chiusura sono di G7) → Blocco 4
> (**G6**, incasso diretto) → **Blocco terminazione** (**G7**, rimborso diretto + storno + **tutte** le
> chiusure-con-motivo, riusa G6) → **remediation** dei 3 contratti muti (runbook a sé, §7-G7) → infine
> **G1 — cifratura `crm.db`**, il **vero prossimo grande blocco**: l'unico con una scadenza che non
> dipende da noi (dato sanitario, art. 9). Il finanziario rende il prodotto convincente, la cifratura
> lo rende lecito.
>
> **Scope schema del blocco terminazione — ✅ IMPLEMENTATO (G7.0).** **4 colonne plain** su `contratti` (nessuna FK
> cross-DB, gemelle di `esito_rinnovo_motivo`): `totale_rimborsato`, **`quota_stornata`** (azzera il `residuo` nella
> gamba write-off senza riscrivere `prezzo_totale`; `residuo()` lo sottrae — letto anche nel dettaglio, §2/§3.1),
> `data_chiusura`, `motivo_chiusura` (**enum a 4 valori, DECISO** — vedi nota sotto) + la categoria movimento
> `RIMBORSO_CONTRATTO`. Fatti: migrazione Alembic `d83abb993ea8` **e** `schema_sync` ADD-column per i DB **già
> deployati** (Chiara/Alessio) + `ContractResponse` + il tipo frontend. (Dettaglio: `SPEC_G7.0`.)
>
> **⚠️ Decisione aperta — enum di `motivo_chiusura` (prima della migrazione).** Il piano di strategia lo
> organizza per **esito economico** (`COMPLETAMENTO`/`CONSUNZIONE`/`TERMINAZIONE_RIMBORSO`/`TERMINAZIONE_DECADENZA`),
> guida-gamba; §3.1 lo organizzava per **ragione** (`recesso`/`risoluzione`/`consensuale`). Sono **due assi
> ortogonali** in un campo solo: andava scelto **quale** vive in `motivo_chiusura`. **✅ DECISO (G7.0/G7.3):**
> vince l'**esito economico** (4 valori, guida-gamba), **DERIVATO server-side** dal conguaglio (mai scelto dal
> trainer, mai `COMPLETAMENTO` da `terminate`); la *ragione* umana (recesso/risoluzione) NON vive qui (campo
> separato futuro, se servirà). Modello ed enum del codice coincidono (`contract_settlement.MotivoChiusura`).

## 12. Bridge rule

Modifiche al modello (nuovo stato, nuova worklist, nuovo invariante, nuovo evento di dominio) → qui
prima, poi le spec/codice. Output non banale → learning capture + `BUILD_LOG.md`.
