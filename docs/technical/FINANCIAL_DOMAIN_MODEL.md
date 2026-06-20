# FINANCIAL DOMAIN MODEL — la base unica del dominio economico-finanziario

**Versione:** 1.0
**Stato:** **SSoT del dominio finanziario — vincolante.** Ogni feature finanziaria si misura qui.
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

## 4. Vocabolario non negoziabile

Tre termini erano usati con significati diversi → d'ora in poi:

| Termine | Significato UNICO |
|---|---|
| **aperto** | `chiuso = False` (qualsiasi stato di vita tranne CHIUSO/ELIMINATO) |
| **attivo** | stato di vita **ATTIVO** (= aperto **e** vigente). **MAI** "attivo = chiuso==False" |
| **scaduto** | `data_scadenza < oggi` (asse tempo) — è una *condizione*, non uno stato di vita |
| **ingaggiato** (cliente) | ha ≥1 contratto **ATTIVO o SOSPESO** |
| **lapsed** (cliente) | non ingaggiato, ma ha contratti (solo ESAURITO/CHIUSO) |

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
| **In scadenza** | ATTIVO + `data_scadenza ≤ oggi+N` | rinnovo anticipato |
| **Contratti sospesi (sedute)** | **SOSPESO** | unità = contratto; estendi/decadi |
| **Clienti da recuperare (win-back)** | cliente **lapsed**, rappresentante non perso | unità = cliente; rappresentante = contratto più recente in assoluto |
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
- **G2 — niente worklist sovrapposte.** Classificazione = **1 stato di vita primario** + flag denaro.
  Un SOSPESO con residuo e zero rate è in "Contratti sospesi" (primario) e "Da incassare (scaduto)"
  (flag denaro) — **mai** in "Da pianificare" (riservato ad ATTIVO).
- **G3 — analytics rinnovi (renewal rate).** `rinnovo_di` cattura solo i rinnovi col bottone; un nuovo
  contratto non collegato non è linkato → il renewal-rate sottoconterebbe. **Definizione di modello:**
  un cliente è *retained* se passa da non-ingaggiato a ingaggiato (nuovo ATTIVO) entro una finestra,
  indipendentemente da `rinnovo_di`. Le metriche di churn/retention usano la **continuità cliente**,
  non solo il link. (Implementazione differita; concetto fissato qui.)
- **G4 — KPI "attivi".** `kpi_attivi` deve contare lo stato **ATTIVO** (aperto+vigente), non
  `chiuso==False`. I contratti aperti-non-attivi (SOSPESO/ESAURITO) si mostrano separati. Tutti i KPI
  derivano da `contract_state()`.
- **G5 — chiusura/terminazione con motivo.** Ogni terminazione per **decisione umana** registra un
  esito+motivo (dato strutturato): `non_rinnova` (cliente perso), `sedute_decadute` (sospeso, sessioni
  forfettate), `saldo_a_perdere` (residuo abbonato). Coerente con `esito_rinnovo_motivo` (§ SPEC).
  Niente terminazioni mute.

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
