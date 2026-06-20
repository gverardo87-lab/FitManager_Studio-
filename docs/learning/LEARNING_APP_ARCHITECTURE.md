# LEARNING_APP_ARCHITECTURE.md

**Progetto:** FitManager
**Ambito:** Modellazione del dominio nel codebase — contratti, rinnovi, semantica delle date, convenzioni di settore
**Origine:** Sessione 2026-06-19 — implementazione SPEC_RINNOVO Criterio A (flusso di rinnovo)

---

## Rinnovo sequenziale vs parallelo, e la convenzione delle date nei CRM — 19/06/2026
**Contesto:** implementando il pre-fill del contratto di rinnovo avevo messo `data_inizio = oggi`. Il founder ha fermato: un rinnovo non parte "oggi", parte quando finisce il contratto precedente. Da lì l'analisi della semantica corretta e di cosa fanno i CRM leader.

**Livello 1 — Cosa fa:** un *rinnovo* (`Contract.rinnovo_di` valorizzato) è la **continuazione** di un rapporto, non un secondo contratto in parallelo. Il pacchetto nuovo deve iniziare quando finisce il vecchio. Default corretto delle date del figlio:
- `data_inizio = max(data_scadenza padre + 1 giorno, oggi)`
- `data_scadenza = data_inizio + durata del padre` (stesso numero di giorni)

Entrambe restano modificabili: il ~10% di casi paralleli (es. due pacchetti concorrenti) li aggiusta il trainer a mano.

**Livello 2 — Perché lo voglio:** mettere `data_inizio = oggi` su un rinnovo crea un **buco temporale** (se rinnovi prima della scadenza, il figlio si sovrappone al padre) o un'incoerenza di copertura. Il modello mentale del trainer è sequenziale: "questo cliente continua". Il default deve riflettere il caso dominante, altrimenti ogni rinnovo richiede una correzione manuale — frizione esattamente dove SPEC_RINNOVO promette fluidità. La guardia `max(…, oggi)` evita il caso assurdo del contratto "nuovo" che parte ieri (padre già scaduto, rinnovo tardivo).

**Livello 3 — Perché funziona così sotto / cosa fanno i leader:** la regola "inizio = fine precedente" è uno standard di settore, ma **si biforca per tipo di dato**:
- **Sistemi a date intere** (`date`, giorno come unità, scadenza = ultimo giorno *inclusivo*): il rinnovo parte a **`scadenza + 1 giorno`**. È la convenzione di **Salesforce CPQ** (il renewal term inizia il giorno dopo la fine del contratto). FitManager è qui: `data_scadenza` è un `date`, non un timestamp.
- **Sistemi a timestamp** (`current_period_end` come istante, confine *esclusivo*): il periodo successivo inizia **esattamente** a `period_end`, **senza +1**, perché l'istante di fine di uno è l'istante di inizio del successivo (contiguità senza gap né doppio conteggio). È il modello di **Stripe Billing, Chargebee, Recurly**.
- Il "+1" non è arbitrario: dipende da se la fine è *inclusiva* (ultimo giorno valido → il prossimo è +1) o *esclusiva* (istante-confine → coincide). Confondere i due modelli genera o un giorno di gap o un giorno di overlap.
- **Software palestre/PT** (Mindbody, Glofox), il dominio più vicino: rinnovo **anticipato** → estende dalla scadenza (il cliente non perde giorni); contratto **già scaduto/lapsed** → riparte da oggi. È esattamente la guardia `max(scadenza+1, oggi)`.

La nostra scelta combina i due: continuità Salesforce (date intere, +1) + restart-smart delle palestre sul contratto scaduto.

**Comando/config reale:** `frontend/src/components/contracts/ContractForm.tsx`
```ts
// Rinnovo = continuazione sequenziale del padre (derivata, modificabile)
const today = startOfDay(new Date());
const parentEnd = renewalDefaults?.data_scadenza ? parseISO(renewalDefaults.data_scadenza) : undefined;
const dayAfterParent = parentEnd ? addDays(parentEnd, 1) : undefined;
renewalStart = dayAfterParent && dayAfterParent > today ? dayAfterParent : today;  // max(scadenza+1, oggi)
// data_scadenza = renewalStart + (parentEnd - parentStart)  → stessa durata
```
Spec vincolante: `SPEC_RINNOVO_E_CONTRATTI_DA_PIANIFICARE.md` §A.2 (v1.3) + §5 decisione #6.

**Failure mode:** se sbaglio e metto `data_inizio = oggi` → su un rinnovo anticipato il figlio si sovrappone al padre (due contratti "attivi" sullo stesso periodo) → i KPI di stato (contratti attivi, crediti) contano doppio e il trainer vede un contratto che "parte oggi" quando il precedente è ancora in corso. Me ne accorgo perché le date pre-compilate non hanno senso rispetto al contratto che sto rinnovando (inizio prima della fine del padre). Caso speculare: `scadenza+1` puro senza la guardia → su padre già scaduto il figlio nasce con `data_inizio` nel passato → contratto "nuovo" già iniziato, sorprendente e potenzialmente con rate retrodatate.

**Domande aperte:**
- [ ] La "durata" è preservata come numero di giorni esatto. Per pacchetti definiti in mesi/sedute potrebbe essere più naturale preservare i *mesi di calendario* (es. sempre 2 mesi) invece dei giorni. Valutare se serve, oppure se l'editabilità del campo basta.
- [ ] Se in futuro si introducono pacchetti a timestamp (orari, non solo date), rivedere la convenzione +1 → period-end esclusivo.

---

## KPI affiancati: la disposizione comunica una relazione matematica — 20/06/2026
**Contesto:** cruscotto contratti con 3 KPI in fila (Venduto / A rate / Da pianificare). Confondeva anche chi (founder + io) l'aveva pensato. Capire *perché* ha dato una regola di presentazione dati.

**Livello 1 — Cosa fa:** N numeri in celle uguali, affiancate, vengono letti dal cervello come **parti di un insieme che somma**. Se i numeri NON sommano (o sommano a qualcosa che non è mostrato), il layout *mente* sulla loro relazione. Nel caso reale: `Venduto` (prezzo, 15.177) non c'entra con `A rate + Da pianificare` (= residuo, 5.441) — affiancarli implicava una somma inesistente. Fix: separare per **scope/storia** e rendere **esplicita l'equazione** che torna (`Residuo = A scadenza + Da pianificare`), con l'ancora (Residuo) mostrata.

**Livello 2 — Perché lo voglio:** un cruscotto finanziario vale solo se l'utente **si fida** dei numeri. Numeri che non riconciliano a vista generano dubbio — l'opposto del "sentirsi in controllo" che il prodotto promette. Per un utente efficienza-driven con poco tempo, il dubbio = abbandono della feature.

**Livello 3 — Perché funziona così sotto:** è percezione (Gestalt: prossimità + similarità → raggruppamento) + il "modello mentale" che l'utente costruisce. Due principi trasferibili: (a) **affianca solo ciò che somma**; se non somma, separa o mostra l'operatore (`=`, `+`); (b) **una vista = uno scope**: non mischiare cumulativo-storico (include chiusi) e stato-corrente (solo aperti) nella stessa griglia senza segnalarlo — sono domande diverse ("quanto ho fatto in totale" vs "quanto devo ancora incassare"). Lo stesso vale per qualunque dashboard: KPI di flusso vs di stato, lifetime vs corrente, lordo vs netto.

**Failure mode:** se metto in fila numeri di scope/grandezza diversi → l'utente tenta una somma mentale che non torna → non si fida → o ignora il cruscotto o (peggio) prende decisioni su una lettura sbagliata. Me ne accorgo quando *io stesso* non so spiegare in una frase come si legano due numeri adiacenti (Principio 1 del metodo: "se non lo spiego, non l'ho capito" — vale anche per la UI).

**Domande aperte:**
- [ ] Serve un'icona/tooltip che mostri l'equazione anche a chi non la coglie dal layout? Per ora l'operatore `=`/`+` inline dovrebbe bastare — da validare con l'utente reale.
