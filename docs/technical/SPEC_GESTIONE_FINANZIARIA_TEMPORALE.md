# SPEC — Gestione finanziaria temporale dei contratti

**Versione:** 1.1
**Stato:** Vincolante sui criteri di accettazione — **non vincolante sull'implementazione**
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** Claude Code (architetto finale nel codebase)
**Collocazione:** `docs/technical/`
**Data:** 2026-06-19
**Spec correlata:** `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md` (stesso dominio finanziario)
**Tassonomia di riferimento:** `TASSONOMIA_FINANZIARIA.md` (vocabolario condiviso, vincolante)
**Modello di dominio (SSoT):** `FINANCIAL_DOMAIN_MODEL.md` — stati/vocabolario/worklist definiti lì.

> **Nota di versione 1.1 (2026-06-19):** incorporati i rilievi di Claude Code. (1) La base
> dell'incassato per periodo si restringe alle **categorie contrattuali** (escludendo storni e
> ENTRATA non-ricavo) — vedi §4.2 e `TASSONOMIA_FINANZIARIA.md` §2. (2) Aggiunta riga **"Altri
> incassi"** per gli incassi fuori contratto (§4.4). (3) Nota di affidabilità su `data_vendita`
> nullable/legacy per la serie competenza (§5.4). (4) Naming e nozioni rimandati alla tassonomia
> condivisa.

> **Natura del documento.** Prescrittivo su *cosa deve essere vero*, silenzioso su *come*. I criteri
> di accettazione sono vincolanti; ogni scelta implementativa (forma delle query, struttura degli
> endpoint, libreria di grafici, naming UI italiano) spetta a Claude Code, che si adatta al codebase
> reale — **fonte di verità sopra ogni assunzione qui contenuta**. Dove si cita codice esistente, è
> per ancorare i criteri a ground-truth.

---

## 0. Perché esiste questo documento

La gestione finanziaria attuale espone uno **stato istantaneo** (`kpi_fatturato`, `kpi_incassato`,
aging report, e un `monthly_revenue` scalare di un singolo mese). Risponde a *"dove sono adesso"*,
ma **non risponde alla domanda che un PT che ragiona sui soldi si fa ogni mese: "come sto andando
rispetto a prima?"**. Manca l'asse del tempo: nessuna aggregazione per periodo, nessun andamento,
nessuna composizione del fatturato. È una lacuna grave rispetto ai gestionali leader, e per un
primo cliente reale *efficienza-driven* è esattamente il tipo di assenza che erode fiducia.

Il bersaglio: trasformare il prodotto da **registratore di cassa** (fotografia) a **strumento di
gestione** (film). La differenza, per il trainer, è la sensazione di essere *in controllo* del
proprio business.

---

## 1. Le due nozioni di "fatturato nel tempo" (fondamento concettuale)

Esistono **due** risposte corrette e diverse alla domanda "quanto ha fatturato a marzo?". Non vanno
mai fuse in un unico numero: rispondono a domande diverse.

**Esempio.** Il 10 marzo il trainer vende un pacchetto da €1200: €200 di acconto subito, €1000 in
5 rate mensili (apr–ago).

| Nozione | Marzo | Su cosa si costruisce | Domanda a cui risponde |
|---|---|---|---|
| **Per cassa** (incassato) | €200 | `CashMovement.data_effettiva` | "Ho i soldi questo mese?" |
| **Per competenza** (venduto) | €1200 | `Contract.data_vendita` | "Sto vendendo bene?" |

**Decisione (2026-06-19):**
- **La vista per cassa è PRIMARIA e default.** È la realtà del conto corrente ed è l'unica coerente
  con il regime **forfettario, che è per cassa** (le tasse del trainer si calcolano sull'incassato,
  non sul venduto). Il numero che il trainer chiamerà "fatturato" deve essere quello per cassa.
- **La vista per competenza è SECONDARIA e affiancata.** Misura l'andamento commerciale.
- **Lo scarto tra le due è l'informazione di valore:** denaro venduto ma non ancora incassato — il
  credito vivo dell'attività. Renderlo visibile (es. due serie affiancate) è un obiettivo esplicito,
  perché è ciò che fa sentire il trainer in controllo.

> **Errore da evitare assolutamente:** sommare cassa e competenza in un unico totale. Sono assi
> distinti. Vanno mostrati insieme ma mai confusi.

---

## 2. Ground-truth: cosa esiste già (NON va re-implementato)

L'analisi del codice reale (`schemas/financial.py`, `routers/contracts.py`, `routers/rates.py`)
accerta che **tutta la materia prima esiste già ed è datata e categorizzata**. La spec aggiunge
l'asse temporale, non un motore finanziario.

| Materia prima | Dove vive | Uso per questa spec |
|---|---|---|
| Libro mastro datato (cassa) | `CashMovement`: `data_effettiva`, `tipo` (ENTRATA/USCITA), `categoria`, `importo` | Base di **tutta** l'aggregazione per cassa |
| Data di vendita (competenza) | `Contract.data_vendita` | Base dell'aggregazione per competenza |
| Flag rinnovo | `Contract.rinnovo_di` (null = nuovo, valorizzato = rinnovo) | Taglio **nuovi vs rinnovi** (Layer 3 primario) |
| Distinzione acconto/rata | `CashMovement.categoria` (`ACCONTO_CONTRATTO` vs `PAGAMENTO_RATA`) | Taglio **acconti vs rate** (Layer 3 secondario) |
| Collegamento movimento→contratto | `CashMovement.id_contratto`, `id_rata`, `id_cliente` | Join per i tagli di composizione |
| Fatturato mensile (scalare) | `DashboardSummary.monthly_revenue` | **Da estendere** in serie temporale (oggi è un singolo mese senza storia) |
| Aging per scadenze | `GET /rates/aging` | Già copre le scadenze; questa spec è **complementare**, non lo tocca |

**Conseguenza:** ogni layer è un `GROUP BY` (eventualmente con un join) su campi esistenti. Nessuna
migrazione dati. Nessun nuovo calcolo finanziario: solo nuove **interrogazioni** di dati già scritti.

---

## 3. Ordine di consegna (dipendenza + impatto)

I tre layer sono in dipendenza stretta: ognuno è prerequisito del successivo, e ognuno è
**consegnabile e utile da solo**. Si può fermare la consegna dopo qualsiasi layer.

```
Layer 1 (aggregazione per periodo, cassa)   ← fondamento, colma la lacuna più grave
   └─> Layer 2 (trend + competenza affiancata)   ← "wow" della demo, introduce la 2ª nozione
          └─> Layer 3 (composizione: nuovi/rinnovi, acconti/rate)   ← distingue dai leader
```

---

## 4. Layer 1 — Aggregazione per periodo (cassa)

### 4.1 Cosa deve essere vero

Il trainer deve poter sapere **quanto ha incassato in un dato periodo** (mese, trimestre, anno),
non solo il totale cumulativo o il mese corrente.

### 4.2 Criteri di accettazione

- Esiste un aggregato dell'incassato **per periodo** con granularità almeno **mensile**, e
  preferibilmente anche **trimestrale** e **annuale**.
- L'aggregazione si basa su `CashMovement.data_effettiva` (data reale dell'incasso), filtrata per
  `trainer_id`, e — **correzione v1.1** — **ristretta alle categorie contrattuali**
  (`ACCONTO_CONTRATTO` + `PAGAMENTO_RATA`), **escludendo** storni e ENTRATA non-ricavo
  (es. `STORNO_SPESA_FISSA`). Vedi `TASSONOMIA_FINANZIARIA.md` §2. *Un generico `sum(ENTRATA)`
  sovrastima il fatturato per cassa.*
- Il periodo è interrogabile: il trainer può vedere mesi/trimestri diversi, non solo quello corrente.
- **Riconciliazione (correzione v1.1):** la somma per periodo degli **incassi da contratti**
  riconcilia con la logica dei contratti. **Attenzione:** `kpi_incassato` è
  `sum(Contract.totale_versato)`, **non** una somma del libro mastro — vedi
  `TASSONOMIA_FINANZIARIA.md` §3. Il *cash flow reale totale* (che include "Altri incassi", §4.4)
  **non** riconcilia con `kpi_incassato`, ed è corretto: sono nozioni diverse.
- *(Coerente)* lo stesso schema può aggregare le **USCITE** per periodo, abilitando un saldo netto
  periodico — il libro mastro le contiene già.

### 4.3 Lasciato a Claude Code

Se è un endpoint dedicato o un'estensione del dashboard router; la forma del raggruppamento
temporale (SQL date functions vs aggregazione applicativa); il formato del periodo nella response.

### 4.4 "Altri incassi" e cash flow reale — il differenziatore (correzione v1.1)

> Questa sezione mette a terra il posizionamento di `TASSONOMIA_FINANZIARIA.md` §0: la liquidità
> reale come funzione di prodotto che i competitor non hanno, **neutra e difendibile**.

Il trainer deve poter vedere, accanto agli incassi da contratti, gli **incassi fuori contratto**
(sessioni singole, extra), come **riga/categoria separata** — e la somma delle due come
**cash flow reale** del periodo.

**Criteri di accettazione:**
- Esiste una voce **"Altri incassi"** per periodo: `CashMovement` ENTRATA con `id_contratto IS NULL`,
  **al netto degli storni** e delle ENTRATA non-ricavo (vedi `TASSONOMIA_FINANZIARIA.md` §2).
- "Altri incassi" è **separato** dagli incassi da contratti, mai fuso (la parte contrattuale resta
  riconciliabile).
- Esiste la nozione di **cash flow reale** del periodo = incassi da contratti + altri incassi: il
  *quanto è davvero entrato*.
- **Confine di posizionamento (vincolante):** il software espone **cash management neutro**
  (visibilità sulla liquidità). NON nomina, struttura o agevola alcuna nozione di reddito "non
  dichiarato". La nozione fiscale resta distinta. Coerente con l'impianto di compliance di AVGV
  (`TASSONOMIA_FINANZIARIA.md` §0). *Non è un parere fiscale: l'asse va validato con un
  professionista tributarista.*

---

## 5. Layer 2 — Andamento nel tempo (trend) + competenza affiancata

### 5.1 Cosa deve essere vero

Il trainer deve **vedere l'andamento** dell'incassato come serie temporale (la curva che sale o
scende), e accanto ad essa l'andamento del **venduto** (per competenza), così da percepire sia la
crescita sia lo scarto tra venduto e incassato.

### 5.2 Criteri di accettazione

- Esiste una **serie temporale** dell'incassato (per cassa) su N periodi consecutivi, adatta a una
  visualizzazione a grafico.
- Accanto, una **seconda serie** del venduto (per competenza), costruita su `Contract.data_vendita`.
- Le due serie sono **distinte e affiancate** (es. due linee), **mai sommate**. Lo scarto tra le
  due — denaro venduto non ancora incassato — deve essere leggibile.
- L'intervallo temporale è ragionevolmente configurabile (es. ultimi N mesi).

### 5.3 Lasciato a Claude Code

La libreria/forma del grafico; quanti periodi di default; se le due serie stanno nello stesso
endpoint; il naming UI italiano delle due nozioni (vedi `TASSONOMIA_FINANZIARIA.md` §5).

### 5.4 Nota di affidabilità sui dati storici (correzione v1.1)

`Contract.data_vendita` è **nullable** e ha **default `date.today`**. I contratti **legacy/migrati**
(es. i 7 record storici) possono avere `data_vendita` assente o schiacciata sulla data di import →
la serie **competenza** si distorce sul passato. **Decisione (2026-06-19):** la serie competenza è
dichiarata **best-effort sui dati storici**, non sanata — perché (a) riguarda pochi record, e
(b) la vista **primaria (cassa)** non ne soffre, poggiando su `data_effettiva` reale. Se in futuro
si vuole precisione storica anche sul venduto, è un'attività di data cleanup separata.

---

## 6. Layer 3 — Composizione del fatturato

### 6.1 Cosa deve essere vero

Il trainer deve sapere **da dove viene** il fatturato di un periodo, lungo due assi che il codice
rende affidabili (flag strutturati, non testo libero).

### 6.2 Assi di composizione (decisione 2026-06-19)

**Primario — Nuovi vs Rinnovi** (via `Contract.rinnovo_di`):
- Risponde alla domanda strategica *"cresco acquisendo o fidelizzando?"*.
- `rinnovo_di == None` → nuovo; valorizzato → rinnovo.

**Secondario — Acconti vs Rate** (via `CashMovement.categoria`):
- Risponde a *"il mese è fatto di denaro fresco o di code di contratti pregressi?"*.
- `ACCONTO_CONTRATTO` vs `PAGAMENTO_RATA`.

> **Perché questi due e non altri.** Sono i tagli che il codice rende **solidi**: flag strutturati,
> non soggetti a errori di digitazione. Insieme raccontano una storia coerente: *acconti su contratti
> nuovi* = crescita per acquisizione; *rate su rinnovi* = attività matura che incassa la propria base.

### 6.3 Criteri di accettazione

- L'incassato di un periodo è scomponibile in **nuovi vs rinnovi** (join `CashMovement.id_contratto`
  → `Contract.rinnovo_di`).
- L'incassato di un periodo è scomponibile in **acconti vs rate** (`CashMovement.categoria`).
- Le somme delle componenti riconciliano con il totale del periodo (Layer 1): nessun ammanco.
- La composizione si innesta sull'aggregazione temporale già costruita (Layer 1/2), non la duplica.

### 6.4 Esplicitamente FUORI perimetro (per scelta)

- **Taglio per tipo di pacchetto** (`Contract.tipo_pacchetto`): tecnicamente possibile ma `tipo_pacchetto`
  è **testo libero** (`max_length=100`) — "PT individuale" / "Personal 1:1" / "PT" sarebbero
  categorie diverse se il trainer non è disciplinato. **Meno affidabile come asse**, rimandato a
  un'iterazione successiva (eventualmente previa normalizzazione della nomenclatura).
- **Top clienti per valore** (`CashMovement.id_cliente`): è una vista **relazionale** ("chi"), non
  **temporale** ("come sto andando"). Utile, ma è un'altra vista — non parte del trend. Fuori da
  questa spec.

### 6.5 Lasciato a Claude Code

Forma della scomposizione (stacked bar, tabella, breakdown nell'endpoint del trend); naming UI
italiano degli assi.

---

## 7. Nota di conformità — regime forfettario

Le due nozioni (cassa / competenza) e i tagli di composizione sono **strumenti gestionali**, non
*revenue recognition* GAAP. AVGV opera in **forfettario per cassa**: non si applica il trattamento
per competenza contabile (no *deferred revenue* di bilancio). La vista per competenza qui è un
indicatore **commerciale** (quanto vendo), non una posta contabile. Il numero esposto come
"fatturato"/"incassato" deve restare coerente con il **principio di cassa** del forfettario.

---

## 8. Confini con le spec e i sottosistemi esistenti

- **Aging report** (`/rates/aging`): copre le **scadenze future/passate** delle rate. Questa spec
  copre l'**andamento storico dell'incassato/venduto**. Sono complementari e **separati** — non
  unificare.
- **Spec "Contratti da pianificare"**: copre i contratti **senza piano rate**. Indipendente da
  questa, ma stesso dominio: coerenza di naming e di UI è auspicabile.
- **Riconciliazione** (`ReconciliationResponse`): l'integrità `totale_versato` ↔ libro mastro è già
  auditata altrove. Questa spec **assume** quel libro mastro corretto come fonte per la cassa.

---

## 9. Checklist di accettazione (sintesi verificabile)

**Layer 1 — Aggregazione per periodo:**
- [ ] Incassato per mese (min.), idealmente trimestre/anno, su `data_effettiva` + trainer, **ristretto alle categorie contrattuali** (escludendo storni — v1.1).
- [ ] Periodo interrogabile (non solo il corrente).
- [ ] "Incassi da contratti" riconcilia con la logica contratti; cash flow reale NON riconcilia con `kpi_incassato` (atteso — v1.1).
- [ ] Voce **"Altri incassi"** separata (ENTRATA fuori contratto, al netto storni) + nozione **cash flow reale** (v1.1).

**Layer 2 — Trend + competenza:**
- [ ] Serie temporale incassato (cassa) su N periodi.
- [ ] Serie affiancata venduto (competenza, `data_vendita`).
- [ ] Due serie distinte, mai sommate; scarto leggibile.
- [ ] Serie competenza dichiarata best-effort sui dati legacy (v1.1).

**Layer 3 — Composizione:**
- [ ] Scomposizione nuovi vs rinnovi (`rinnovo_di`).
- [ ] Scomposizione acconti vs rate (`categoria`).
- [ ] Componenti riconciliano col totale del periodo.

**Perimetro e conformità:**
- [ ] Taglio per pacchetto e top-clienti NON in questa iterazione (documentati).
- [ ] Cassa primaria/default; competenza secondaria; mai fuse.
- [ ] Coerenza forfettario per cassa; nessuna pretesa GAAP.

---

## 10. Bridge rule

Output non banale di Claude Code derivato da questa spec (scelte su endpoint temporali, forma delle
serie, scomposizione) va ricondotto a una *learning capture* digerita in chat, e — se introduce o
modifica decisioni vincolanti — riflesso in `BUILD_LOG.md` con i consueti cross-reference.
