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

---

## Recharts non vede le serie dentro un React Fragment — 20/06/2026
**Contesto:** grafico composizione (stacked bar con toggle Nuovi/Rinnovi vs Acconti/Rate). Le `<Bar>` condizionali erano avvolte in un Fragment `{cond ? <><Bar/><Bar/></> : <><Bar/><Bar/></>}`. A schermo: assi, griglia e label dei mesi presenti, ma **zero barre e zero legenda**. Il grafico gemello sopra (stesse `Bar` come figli diretti) funzionava.

**Livello 1 — Cosa fa:** Recharts scopre le serie (Bar, Line, Area…) **ispezionando i propri `children` con `React.Children`** al render, per costruire scale, legenda e tooltip. Un **React Fragment** (`<>…</>`) interposto **nasconde** quei figli all'introspezione → le serie non vengono registrate → niente barre, niente legenda. Assi e griglia restano perché sono componenti propri, indipendenti dalle serie.

**Livello 2 — Perché lo voglio:** rendering condizionale di serie diverse (toggle, modalità) è comunissimo. Sapere che il *contenitore* del condizionale conta evita un bug silenzioso: build verde, TypeScript contento, nessun errore runtime — solo un grafico vuoto. Il sintomo (assi sì, serie no) è la firma diagnostica.

**Livello 3 — Perché funziona così sotto:** Recharts non usa il DOM per capire cosa disegnare; legge l'albero React dei figli *dichiarativamente* (`React.Children.toArray` + type-check sul `displayName`/tipo del componente). `React.Children` **appiattisce gli array** ma **non entra nei Fragment** come se fossero trasparenti per quel matching (un Fragment è un nodo di tipo `Symbol(react.fragment)`, non un `Bar`). Quindi: passare le serie condizionali come **array da `.map()`** funziona (l'array viene appiattito e ogni `Bar` è visto), un **Fragment** no.

**Comando/config reale:** `frontend/src/components/movements/AndamentoTab.tsx`
```tsx
// ❌ niente barre: il Fragment nasconde le Bar a recharts
{cond ? <><Bar dataKey="a"/><Bar dataKey="b"/></> : <>…</>}

// ✅ array .map(): recharts appiattisce e vede ogni Bar
{(cond ? ["a","b"] : ["c","d"]).map((k,i) => (
  <Bar key={k} dataKey={k} stackId="s" fill={`var(--color-${k})`}
       radius={i===0 ? [0,0,4,4] : [4,4,0,0]} />
))}
```

**Failure mode:** avvolgo serie condizionali in `<>…</>` → grafico con assi ma vuoto, build verde, nessun errore → sembra un bug di *dati* (e infatti il primo sospetto è stato "logica/endpoint"). Me ne accorgo dal sintomo specifico: **assi/griglia presenti ma serie e legenda assenti** → guardare il *contenitore* dei children del grafico prima dei dati. Vale per qualunque libreria che introspeziona i children React (anche alcune di form/layout).

**Domande aperte:**
- [ ] Verificare se le versioni recenti di recharts hanno reso i Fragment trasparenti (in tal caso resta comunque buona pratica l'array per chiarezza). Per ora: mai Fragment attorno a serie di grafici.

---

## Entrata-fantasma: una query che fa JOIN al padre deve filtrare lo stato terminale del padre — 21/06/2026
**Contesto:** il Forecast (`get_forecast`, `movements.py`) proietta come "entrate certe" le rate PENDENTI/PARZIALI future. La query faceva `JOIN Contract` e filtrava `Rate.deleted_at == None` + `Contract.deleted_at == None`, ma **non** `Contract.chiuso == False`. Una rata PENDENTE su un contratto CHIUSO (chiuso a metà, terminato, o legacy) restava proiettata come incasso futuro che non arriverà mai.

**Livello 1 — Cosa fa:** quando un record-figlio (Rate) è valido di per sé ma la sua "esigibilità" dipende dallo **stato del padre** (Contract chiuso/terminato), filtrare solo il figlio non basta. Una rata può essere PENDENTE (figlio "vivo") mentre il contratto è CHIUSO (padre "morto") → il debito non esiste più, ma la query lo vede ancora. Fix: aggiungere il predicato di stato del padre (`Contract.chiuso == False`).

**Livello 2 — Perché lo voglio:** una proiezione finanziaria che gonfia le entrate con denaro che non arriverà induce a decisioni sbagliate (spendere contando su un incasso fantasma). È lo speculare del "debito nascosto": qui è un **credito inventato**. Per un cruscotto che promette controllo, è un errore di fiducia.

**Livello 3 — Perché funziona così sotto:** è una **dipendenza di validità transitiva**. La validità di un fatto figlio (rata dovuta) è condizionata da un fatto padre (contratto attivo). SQL non la impone: un JOIN unisce righe, non propaga lo stato. Regola trasferibile: **ogni aggregazione su figli che attraversa un JOIN al padre deve includere i predicati di stato del padre** (soft-delete *e* flag terminali tipo `chiuso`). Controprova sistematica: per ogni `JOIN Parent` in una query di lettura, chiedersi "quali stati del padre rendono il figlio non più rilevante?" e filtrarli. L'aging report lo faceva già (`Contract.chiuso == False`, `rates.py`), il Forecast no → asimmetria = il bug.

**Comando/config reale:** `api/routers/movements.py` `get_forecast`
```python
select(Rate).join(Contract, Rate.id_contratto == Contract.id).where(
    Contract.trainer_id == trainer.id,
    Rate.stato.in_(["PENDENTE", "PARZIALE"]),
    Rate.data_scadenza > today,
    Rate.deleted_at == None,
    Contract.deleted_at == None,
    Contract.chiuso == False,   # ← senza questo: entrata-fantasma da rate su contratti chiusi
)
```

**Failure mode:** filtro solo il figlio (soft-delete della rata) e dimentico lo stato del padre → numeri verdi, build verde, nessun errore, ma la proiezione mente. Me ne accorgo solo confrontando due query gemelle (aging vs forecast) e notando che una filtra `chiuso` e l'altra no. Test di regressione dedicato: rata PENDENTE futura su contratto CHIUSO → NON in proiezione.

**Domande aperte:**
- [ ] Audit sistematico: esistono altre query con `JOIN Contract` che dimenticano `chiuso`? (Le worklist nuove derivano da `contract_state`, quindi sono coperte; il rischio è nelle query raw-SQL storiche.)

---

## Difese inerti vs codice testabile: non landare esclusioni per dati che non esistono ancora — 21/06/2026
**Contesto:** il piano (Prereq P) prevedeva di "cablare in difesa" l'esclusione del futuro `RIMBORSO_CONTRATTO` da 4 query di cassa (burn/stats/forecast/get_balance) **prima** che la categoria fosse mai scritta (la scrittura arriva col blocco G7). Avrei aggiunto `NOT categoria == RIMBORSO_CONTRATTO` a query che oggi non vedono nessun rimborso.

**Livello 1 — Cosa fa:** un'esclusione di una categoria che **non esiste ancora nei dati** è codice **inerte**: non cambia nessun risultato finché G7 non scrive il primo rimborso. È de-facto non testabile end-to-end *adesso* (nessun caso reale la esercita; un test potrebbe solo verificare che è no-op). Scelta: spostare quelle esclusioni **dentro G7**, dove un `RIMBORSO` reale le esercita e il test ha significato.

**Livello 2 — Perché lo voglio:** "massima pulizia" significa anche **niente codice che non puoi dimostrare funzioni**. Codice difensivo per un futuro non ancora arrivato sembra prudente ma è debito: chi legge non sa se è attivo o morto, e un test no-op dà falsa sicurezza. Tenere il blocco corrente (Prereq P) fatto **solo** di pezzi con effetto reale e testabile (predicato SSoT, fix Forecast, audit transizione) lo rende verificabile al 100%.

**Livello 3 — Perché funziona così sotto:** principio di **co-locazione tra codice e sua prova**. Una modifica vale quando esiste un caso che la esercita; landarla lontano da quel caso separa il "cosa" dal "perché", e il "perché" (il rimborso) non c'è ancora. Distinzione operativa: il **predicato SSoT** (`cash_categories.py`) si lascia ora — è la *fonte* condivisa, consumata già dalla consolidazione costanti — ma i suoi **consumatori inerti** (le esclusioni) si scrivono col consumatore reale. SSoT = fondazione (ok in anticipo); difese = comportamento (con il caso che le attiva). Eccezione legittima al "cablare in difesa": un **fix con effetto reale subito** (P1 Forecast `chiuso`) si fa ora anche se "prepara" G7, perché protegge un caso **già esistente** (contratti chiusi legacy con rate pendenti).

**Failure mode:** riempio un blocco "fondativo" di esclusioni/guard per scenari futuri → diff grande, test no-op, e al momento di G7 nessuno ricorda se quelle difese erano complete o giuste (non sono mai state esercitate). Me ne accorgo quando un test può solo asserire "non cambia nulla": segnale che il codice è nel posto sbagliato nel tempo.

**Domande aperte:**
- [ ] In G7, ri-verificare che le 8 query siano allineate **insieme** all'introduzione del rimborso (un solo blocco coerente, ognuna con un test che la esercita con un `RIMBORSO` vero).
