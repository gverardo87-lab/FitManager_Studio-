# FINANCIAL DOMAIN MODEL — la base unica del dominio economico-finanziario

**Versione:** 1.2
**Stato:** **SSoT del dominio finanziario — vincolante.** Ogni feature finanziaria si misura qui.

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
**Data:** 2026-06-20
**Decisioni:** `ADR-014` (cassa/competenza), `ADR-015` (funnel rinnovi/retention)
**Assorbe / coordina:** `TASSONOMIA_FINANZIARIA.md` (asse cassa/competenza), `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md`, `SPEC_GESTIONE_FINANZIARIA_TEMPORALE.md`, `SPEC_RINNOVI_SCADUTI_E_RETENTION.md`

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

- **`crediti_usati` è computed-on-read**: `COUNT(eventi PT non cancellati, non eliminati)` sul contratto.
  `crediti_residui = max(crediti_totali − crediti_usati, 0)`.
- **`residuo = max(prezzo_totale − totale_versato, 0)`**. `totale_versato` riconciliabile col mastro
  (`ReconciliationResponse`).

---

## 3. Stato di vita del contratto (canonico) — `contract_state()`

`chiuso` (flag stored) si accende SOLO su **denaro saldato + crediti esauriti** (auto-close su pay/event,
o manuale) — **ignora il tempo**. Quindi lo stato di vita reale è una **funzione derivata** di
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
| **SOSPESO** | tempo scaduto, **sedute prepagate residue** = gliele DEVI | estendi / pianifica sedute / decadi |
| **ESAURITO** | pacchetto consumato, **deve ancora denaro** | incassa il residuo / rinnova |
| **CHIUSO** | terminato (entrambi gli assi, o chiuso a mano) | — |

> **Regola d'oro:** lo stato di vita lo calcola SOLO `contract_state()`. Nessun endpoint/KPI ricalcola
> "attivo" per conto suo.

---

## 4. Vocabolario non negoziabile (contratto)

Tre termini erano usati con significati diversi → d'ora in poi:

| Termine | Significato UNICO |
|---|---|
| **aperto** | `chiuso = False` (qualsiasi stato di vita tranne CHIUSO/ELIMINATO) |
| **attivo** | stato di vita **ATTIVO** (= aperto **e** vigente). **MAI** "attivo = chiuso==False" |
| **scaduto** | `data_scadenza < oggi` (asse tempo) — è una *condizione*, non uno stato di vita |

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
  automatica; l'aging **aumenta** l'urgenza (segno invertito). Esce solo per decisione (estendi/decadi).

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
| **saldato** | `residuo = 0` |
| **da pianificare** | `residuo > 0` e nessuna Rata (zero rate non eliminate) |
| **parzialmente pianificato** | rate presenti ma `Σ residui rate non-saldate < residuo` |
| **pianificato** | `Σ residui rate non-saldate ≈ residuo` |
| **rate scadute** | ≥1 rata non-saldata con `data_scadenza < oggi` |

"Rate non-saldate" = `stato ∈ {PENDENTE, PARZIALE}` (allineato all'aging).

---

## 6. Mappa worklist → derivazione (univoca, senza sovrapposizioni)

Ogni contratto/cliente ha **uno stato di vita primario** + **flag denaro secondari**. Le worklist
derivano da qui, senza doppi conteggi:

| Worklist | Deriva da | Note |
|---|---|---|
| **In scadenza** | ATTIVO + `data_scadenza ≤ oggi+SOGLIA_IN_SCADENZA_GG` | rinnovo anticipato |
| **Contratti sospesi (sedute)** | **SOSPESO** | unità = contratto; estendi/decadi; **non decade, urgenza ↑** |
| **Clienti da recuperare (win-back)** | cliente **lapsed CALDO** (non freddo, non perso) | unità = cliente; rappresentante = contratto più recente in assoluto; esce quando freddo (§4.1) |
| **Da pianificare (rate)** | **ATTIVO** + `da pianificare` | **solo ATTIVO** (vedi §7 G1) |
| **Da incassare (scaduto)** | (SOSPESO o ESAURITO) + `residuo > 0` | incasso diretto, non pianificabile a rate |
| **Rate scadute / aging** | Rate non-saldate oltre scadenza | rate-first |
| **Andamento (cassa/competenza)** | libro mastro datato | ortogonale (vedi §8) |

---

## 7. Lacune risolte a livello di modello (G1–G5)

- **G1 — residuo su contratto scaduto NON è "da pianificare".** La guardia rate vieta rate oltre
  `data_scadenza` (passata) → su SOSPESO/ESAURITO non si può creare una rata. Quindi **"da pianificare"
  è ristretto ad ATTIVO**; il residuo su contratti scaduti vive in **"da incassare (scaduto)"** (incasso
  diretto o previa estensione del contratto). Niente azioni impossibili.
  - **⚠️ DEBITO già in codice**: `orphan_contracts`/`contracts-to-plan` (SPEC_RINNOVO, già implementati)
    filtrano `chiuso=False + residuo>0 + zero rate` **senza** restrizione di vigenza → includono i
    SOSPESO/ESAURITO e offrono l'azione impossibile. **Da correggere** (restringere ad ATTIVO) — primo
    fix che il modello fa emergere nel codice esistente.
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
  derivano da `contract_state()`.
- **G5 — chiusura/terminazione con motivo.** Ogni terminazione per **decisione umana** registra un
  esito+motivo (dato strutturato): `non_rinnova` (cliente perso), `sedute_decadute` (sospeso, sessioni
  forfettate), `saldo_a_perdere` (residuo abbonato). Coerente con `esito_rinnovo_motivo` (§ SPEC).
  Niente terminazioni mute.
- **G6 — manca il pagamento DIRETTO del residuo (v1.2, da Obs bridge).** Oggi si incassa **solo via
  Rata** (nessun endpoint di pagamento diretto sul contratto) e su uno **scaduto** non si può creare
  una rata (guardia G1). Quindi un residuo **non rateizzato** su contratto scaduto è **non incassabile**
  (verificato sul dato reale: Dalila c25, 20€ residuo non su rata) → "da incassare (scaduto)" lo
  mostrerebbe **senza azione** (fantasma in worklist). **Fix:** azione "incassa residuo" diretta
  (CashMovement legato al contratto + `totale_versato` += importo + auto-close), che rende azionabile
  "da incassare (scaduto)".
- **Verifica auto-close su scaduto (Obs bridge): ✓ confermata.** `pay_rate` auto-close è
  **date-independent** (`rates.py:559-570`): incassare l'ultimo residuo di un ESAURITO (saldato +
  crediti esauriti) lo porta a CHIUSO anche se scaduto → nessun ESAURITO-fantasma a residuo zero.
  (Test di confine da aggiungere, come "scade oggi".)

---

## 8. Asse cassa / competenza (da `TASSONOMIA_FINANZIARIA.md`)

Ortogonale agli stati: misura il **flusso nel tempo**, non lo stato del contratto.
- **Cassa** (primaria, forfettario): incassato su `CashMovement.data_effettiva`, ristretto alle categorie
  contrattuali (`ACCONTO_CONTRATTO`+`PAGAMENTO_RATA`), **storni esclusi**; "Altri incassi" (fuori
  contratto) separati; "cash flow reale" = somma.
- **Competenza** (secondaria, commerciale): venduto su `Contract.data_vendita`. **Mai sommata alla cassa.**
- Confine §0 TASSONOMIA: cash management **neutro**, nessun campo/label codifica lo stato fiscale.

Dettaglio completo e formule: `TASSONOMIA_FINANZIARIA.md` (resta valido; questo §8 è il puntatore).

---

## 9. Invarianti (anti-perdita silenziosa)

Nessuno di questi può sparire da una worklist senza **decisione umana esplicita**:
1. **Denaro dovuto** (residuo > 0): da pianificare (ATTIVO) o da incassare (scaduto) o aging.
2. **Sedute prepagate** (SOSPESO): estendi o decadi.
3. **Cliente lapsed**: recupera o "non rinnova".

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

E: `kpi_incassato = Σ totale_versato` (NON somma del mastro); il cash flow reale (con Altri incassi)
non riconcilia con `kpi_incassato` — è atteso (TASSONOMIA §3).

---

## 10. SSoT lato codice

- **Un modulo `contract_state()`** (es. `api/services/contract_state.py` o helper condiviso): data un
  contratto (+ crediti_usati), ritorna lo stato di vita + sotto-stato denaro. **Unica fonte** della
  derivazione; KPI, worklist, alert lo consumano. Vietato ricalcolare "attivo/scaduto" altrove.
- Le viste/endpoint diventano *query + presentazione* sopra `contract_state()`.

---

## 11. Rapporto con le spec-feature

| Doc | Ruolo dopo questo modello |
|---|---|
| `FINANCIAL_DOMAIN_MODEL.md` (questo) | **SSoT**: entità, assi, stati, vocabolario, worklist, invarianti |
| `TASSONOMIA_FINANZIARIA.md` | dettaglio asse cassa/competenza (referenziato §8) |
| `SPEC_RINNOVO_*`, `SPEC_*_TEMPORALE`, `SPEC_RINNOVI_SCADUTI_*` | solo *criteri di accettazione* della feature; **referenziano** stati/vocabolario di qui |
| `IMPL_PLAN_*` | effimeri; in `docs/archive/` a implementazione conclusa |
| `ADR-014`, `ADR-015` | decisioni (immutabili) |

## 12. Bridge rule

Modifiche al modello (nuovo stato, nuova worklist, nuovo invariante) → qui prima, poi le spec/codice.
Output non banale → learning capture + `BUILD_LOG.md`.
