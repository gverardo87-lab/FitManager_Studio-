# EXERCISE_LIBRARY_STRATEGY.md

**Stato:** v2.1 — strategia prodotto **verificata dall'interno del codebase da Claude Code** (query dirette su `catalog.db`, seed JSON, router, installer). Recepite le decisioni founder del 2026-06-10. Changelog in coda.
**Tipo:** Prescrittivo sul *cosa deve essere vero*; descrittivo sulle opzioni di *come*.
**Ruolo di Claude Code:** architetto finale dall'interno. Questo documento fissa intento e criteri; l'implementazione (forma dello schema, punti di aggancio, integrazione con gli eseguibili di popolamento esistenti) è decisa da Code contro il codebase reale.
**Contesto a monte:** decisione POC di non esporre l'accesso tablet; FRP consolidato sui soli link esterni tokenizzati. L'energia di prodotto si sposta sull'interfaccia cliente.

---

## 0. Principio di differenziazione (il filtro per ogni decisione)

Il vantaggio competitivo di FitManager **non è la libreria di animazioni**. Le animazioni sono una commodity: chiunque può acquistare lo stesso bundle.

Il vantaggio è **l'architettura data-blind**. FitManager è l'unico prodotto noto in cui i dati dell'atleta restano sul PC del trainer, il VPS è data-blind (proprietà P2), e la conformità GDPR è semplificata per costruzione.

**Tesi di differenziazione:** ci si differenzia perché si è gli unici capaci di legare *contenuto generico* (l'animazione) a *dato sensibile e personale* (note sul corpo dell'atleta, suo video di esecuzione, sua progressione) **mantenendo quel dato protetto per architettura**. Un concorrente cloud ha animazioni più belle ma deve trasferire il corpo dell'atleta in cloud per offrire le stesse funzioni. FitManager no. Questo è l'argomento che un mercato europeo GDPR-sensibile (Italia) comprende e paga.

Ogni feature di questo documento va validata contro questo principio: *aumenta la capacità di legare contenuto generico a dato personale protetto?*

---

## 1. Decisione sul formato delle animazioni

### 1.1 Contesto verificato
- Il fornitore valutato (Exercise Animatic) consegna **MP4 H.264 4K renderizzati** (animazioni 3D appiattite in video), **non file sorgente 3D**.
- La licenza N-EB2BL del fornitore descrive esplicitamente un caso d'uso allineato al modello B2B2C di FitManager (software company che integra i video; trainer come end-user; atleti come loro clienti). Pagamento unico, perpetuo, royalty-free.
- **Clausola critica aperta:** la licenza vieta la ridistribuzione dei file grezzi o "lievemente modificati". L'architettura FitManager copia fisicamente le clip sul PC del trainer (installazione locale, decisione confermata in §4bis), il che potrebbe configurarsi come "ridistribuzione del file" anziché streaming. → Richiede chiarimento scritto col fornitore **prima dell'acquisto** (vedi §5). Nota tecnica rilevante per la domanda: a differenza di `catalog.db` (cifrato AES-256-GCM), le clip saranno file su disco; le mitigazioni realistiche sono naming UUID non semantico, watermark generico batch (§3 Strato 0) e termini di licenza — la cifratura on-the-fly di gigabyte di video non è praticabile né necessaria.

### 1.2 Implicazione tecnica MP4 vs sorgente 3D
- **MP4 (rendering finito):** consente crop, colore globale, overlay disegnati in coordinate fisse, conversione in WebM con alpha (chroma key se lo sfondo è a tinta unita). Le evidenziazioni sono **"cieche"**: si disegna in coordinate fisse, il software non "sa" dove sia un ginocchio. Funziona per parti che restano relativamente ferme (schiena in uno squat, core in un plank).
- **Sorgente 3D (glTF/GLB/FBX con rig):** consente evidenziazioni **strutturali** legate alle ossa nominate, rendering real-time in browser (three.js, già nello stack), reazione visiva al safety engine. È raro che un bundle a basso costo consegni i sorgenti.
- **Vincolo client scoperto in v2.1 (decisivo per il formato di playback):** gli atleti aprono i link su smartphone, e **iOS Safari non supporta WebM con canale alpha**. Il WebM-alpha resta una tecnica valida per gli overlay del safety engine (v2+, dove il canale di rendering è controllabile), **non** per il playback POC rivolto all'atleta.

### 1.3 Decisione
- **POC (settembre 2026): MP4.** Massimizza numero di esercizi (argomento commerciale), copertura fitness reale, licenza già allineata, zero lavoro di rendering real-time.
- **Formato di playback POC (deciso in v2.1): MP4 H.264 720p + poster JPEG.** Transcodifica ffmpeg batch dei master 4K a ~1,5-2 Mbps (~3-4 MB per loop di 15s). H.264 è l'unico baseline con decodifica hardware universale (incluso iOS Safari). Il poster di ogni clip si ricava dalle foto inizio-movimento già esistenti in `ExerciseMedia`.
- **v2: valutazione sorgente 3D** per le evidenziazioni strutturali, **solo dopo** validazione di trazione coi dieci trainer.
- **Non far dipendere la POC dalla feature 3D.** Sono livelli di rischio diversi; inseguire il 3D ora rallenta settembre per una feature simulabile con overlay semplici su MP4.

### 1.4 Sul numero di esercizi (numeri canonici verificati in v2.1)
- L'argomento commerciale del numero alto ("3000 esercizi inclusi") è una leva di vendita reale nel B2B: comunica completezza, toglie l'obiezione "manca l'esercizio che faccio fare io".
- **Numero e qualità non sono in conflitto, sono in sequenza:** il numero alto vende; la qualità dei ~50-80 esercizi più prescritti fa restare il trainer. Si parte dal bundle ampio e si cura il sottoinsieme dei fondamentali.
- **Numeri canonici (query dirette su `catalog.db`, 2026-06-10):** il catalogo conta **500 esercizi totali, di cui 466 attivi** (`in_subset=True`), **894 relazioni** progressione/regressione/variante in DB (940 nel seed, FK orfane filtrate), **750 media** validi (foto inizio/fine; il seed ne elenca 1788 ma 1038 referenziano il catalogo pre-rebuild e vengono scartate dal filtro FK). **359 esercizi attivi hanno almeno una foto; 107 sono scoperti** — un argomento *a favore* dell'acquisto del bundle: le clip colmano un gap visivo reale, non duplicano l'esistente.
- **La metrica di valutazione del bundle è la copertura sui 466 attivi** (con priorità ai fondamentali e ai 107 senza foto), non il conteggio assoluto delle clip. Nota marketing: *"500 esercizi con progressioni, controindicazioni e descrizioni biomeccaniche"* resta lecito contando il catalogo totale; è un argomento più difendibile di *"2000 clip"*. Decisione commerciale aperta tra founder e partner.
- **Attenzione semantica (verificata in v2.1):** il flag `in_subset` **non** marca i fondamentali — è il flag "database attivo" (466 `True`), usato come filtro di visibilità da dashboard, safety engine e training science. Il marcatore dei ~50-80 fondamentali **non esiste ancora**: va introdotto un campo dedicato (`is_fondamentale`) nel seed JSON — coerente col pattern esistente, zero migrazioni (catalog.db non ha Alembic). Prerequisito per AC-3 e per la metrica di copertura.

---

## 2. Sui dataset gratuiti / open source (esito ricerca)

Verificato che esistono asset in formato sorgente, ma con due trappole che li rendono inadatti al caso commerciale di FitManager nell'immediato:

- **Animazione ≠ personaggio.** La quasi totalità del materiale gratuito (es. pack FBX "no mesh", dataset BVH) è *motion data*: lo scheletro che si muove, senza il corpo visibile. Richiede una mesh 3D rigged separata da procurare e accoppiare (retargeting). Un'animazione senza mesh non mostra nulla.
- **Licenze non-commerciali.** I dataset più ampi (es. Bandai Namco 3000+ movimenti) sono Creative Commons **Non-Commercial No-Derivatives** → inutilizzabili in un prodotto commerciale e non modificabili.

**Conclusione:** "gratis su Git" non risolve il caso commerciale. Le strade sorgente realistiche per la v2 sono Mixamo (personaggi + animazioni rigged, copertura fitness però scarsa) o marketplace a pagamento con licenza commerciale (Sketchfab/TurboSquid/Unity Asset Store), da verificare per copertura fitness e costo. Il motore di rendering è già disponibile (three.js); mancherebbe solo il contenuto con licenza giusta.

---

## 2bis. Esito ricerca di mercato — bundle sorgente a pagamento

Ricerca condotta su TurboSquid e CGTrader (i due marketplace principali per asset 3D con licenza commerciale).

### 2bis.1 Risultato chiave
**Il bundle "tutto-in-uno" non esiste.** Non esiste sul mercato un singolo prodotto che combini *tante animazioni di esercizi* **+** *anatomia muscolare* **+** *licenza per ridistribuzione in app installata*. Il mercato offre invece **tre categorie distinte e mutuamente esclusive**, ciascuna con un compromesso:

| Categoria | Cosa dà | Cosa manca | Esempi reali (prezzo) |
|-----------|---------|------------|------------------------|
| **A. Pack esercizi rigged** | Sorgente editabile, leggero, alcuni esercizi | Pochi movimenti, niente anatomia (pelle, non muscoli) | "5 Exercise Animation" ($79); "Gym Exercise Animations Pack" ($49); "30 Woman Exercise Pack" ($200) |
| **B. Modelli anatomici rigged** | Muscoli come **oggetti 3D selezionabili**, scheletro nominato, subdivision (low-poly per animare / high per rendering) | **Nessuna libreria di esercizi** (solo sample animation dimostrativa) | MotionCow "Ultimate Human Anatomy - Rigged" (MAX/OBJ/FBX/C4D/MA/BLEND); "Muscles and Skeleton - Rigged" |
| **C. Volume puro** | Cataloghi enormi (CGTrader: 5.584 modelli "exercise", 2.721 "fitness" rigged) | Modelli sparsi, autori/stili diversi, **nessuna coerenza**, da comprare uno a uno | — (non è un pack unico) |

### 2bis.2 Conseguenza strategica
La tensione numero-vs-qualità **non si risolve trovando un bundle migliore**: si risolve **solo stratificando fonti diverse** (già la tesi del §1.3 e del §3). La ricerca ora indica le fonti concrete per ciascuno strato:
- **Volume + argomento commerciale (2000+ esercizi):** Exercise Animatic in **MP4**. Nessun concorrente 3D si avvicina a quel numero. **Confermato.**
- **Fondamentali premium con anatomia (Strato 4):** un **modello anatomico rigged con muscoli-come-oggetti** (categoria B; MotionCow Ultimate Human Anatomy come riferimento), su cui applicare i movimenti dei ~50-80 esercizi chiave.

### 2bis.3 Candidato Strato 4: modello anatomico rigged (categoria B)
**Perché è interessante:** i muscoli sono geometria 3D separata, selezionabile e nascondibile — non texture dipinta. Questo abilita evidenziazioni **anatomiche strutturali** (isolare/colorare un muscolo specifico) che né gli MP4 né i pack low-poly con anatomia-in-texture possono fare. È esattamente la leva per un prodotto con un kinesiologo come partner scientifico. La subdivision risolve anche il rischio performance (leggero mentre anima, denso solo per il rendering); scena organizzata in layer con tutti i componenti nominati → integrabile in three.js.

**I due caveat che lo tengono in v2, non in POC:**
1. **Dà il corpo, non gli esercizi.** È un modello anatomico con una sample animation, **non** una libreria di esercizi. Per avere 50 esercizi sopra serve creazione/retargeting di animazioni (mocap commerciali o custom) sul rig. È il costo di animazione che aveva già motivato la collocazione dello Strato 4 in v2. *Comprarlo ora = comprare un motore senza benzina.*
2. **Licenza da verificare (ostacolo potenziale più del costo).** I modelli anatomici dettagliati sono asset preziosi; i venditori raramente permettono la **ridistribuzione del file sorgente** dentro un'app installata sul PC di terzi. Le licenze "royalty-free per rendering/animazione" non coprono automaticamente questo. **Da chiarire prima di qualsiasi acquisto.** Potrebbe essere il vero blocco dello Strato 4.

### 2bis.4 Nota sul pack TurboSquid valutato dal founder (categoria A)
Il pack TurboSquid esaminato (cod. 2261446) presentava specifiche **internamente contraddittorie**: descrizione "anatomia muscolare 4K" ma 5.000 poligoni / 5.000 vertici (numeri identici, sospetti di campo compilato a caso). Tre ipotesi non risolte: (a) numero riferito a un solo oggetto / errore di scheda; (b) modello low-poly con anatomia **in texture** (→ evidenziazioni solo scheletriche, non muscolari); (c) dato inaffidabile da verificare con immagini reali. **Coerente col principio: il prodotto è la fonte di verità, non la scheda di vendita.** Da chiarire col venditore (vedi §5.5) prima di considerarlo.

---

## 3. Strategia di differenziazione a quattro strati

I quattro strati **non sono alternative**: sono strati che si costruiscono uno sull'altro. I primi tre sono lo stesso flusso comunicativo che cresce (il trainer parla → l'atleta risponde → il dialogo nel tempo definisce un percorso), quindi costruire bene lo Strato 1 posa le fondamenta del 2 e del 3 senza rilavoro.

**Ranking confermato dal founder e dal partner (Alessio):**

| Priorità | Strato | Orizzonte |
|----------|--------|-----------|
| 1 | Personalizzazione coaching del trainer (cue, note, assegnazioni sull'esercizio) | **POC** |
| 2 | Dialogo e feedback dell'atleta (risposte, video di sé che esegue) | v2 |
| 3 | Progressioni legate al percorso dell'atleta | v2 |
| 4 | Safety engine sul movimento reale (analisi locale, privacy-first) | Visione |

Il ranking riflette una logica da prodotto reale, non da demo: prima ciò che serve al trainer ogni giorno, ultimo ciò che suona avanzato ma è più lontano.

### Strato 0 — Branding (valore percepito immediato, quasi-zero costo) — *corretto in v2.1*
Ogni animazione porta il logo/identità del trainer. L'atleta vede "lo studio del mio trainer", non un video anonimo. **Forma corretta (vincolo architetturale: installer identico per tutti, personalizzazione via licenza):**
- **Branding del trainer = overlay CSS/HTML a runtime** sopra il `<video>` (logo dal profilo trainer). Zero re-encode, zero costo per cliente, branding dinamico. Bruciare il logo nei file richiederebbe ri-encodare l'intera libreria per ogni cliente — insostenibile.
- **Watermark generico "FitManager" = burn-in ffmpeg batch, una sola volta** durante la transcodifica (§1.3). Anti-ridistribuzione, e argomento utile verso la clausola N-EB2BL ("file modificati e brandizzati, non grezzi").
Incluso nella POC.

### Strato 1 — Personalizzazione coaching del trainer (POC) → vedi §4 per la specifica

### Strato 2 — Dialogo e feedback dell'atleta (v2)
L'atleta risponde sull'esercizio ("fatto", "fastidio al ginocchio", video di sé che esegue). L'animazione diventa il fulcro di un dialogo asincrono. **Legame con l'architettura:** il video del corpo dell'atleta è dato intimo che resta sul PC del trainer, non in cloud. Argomento di privacy non replicabile da un'app cloud.

### Strato 3 — Progressioni (v2) — *grafo GIÀ ESISTENTE*
Le animazioni si legano in catene di progressione: la scheda mostra "il tuo squat questa settimana", e avanza quando il trainer fa progredire l'atleta. Trasforma una libreria statica in un percorso → fidelizzazione. **Verificato sul DB reale:** il grafo esiste già — **894 relazioni** progressione/regressione/variante in `ExerciseRelation` (940 nel seed, FK orfane filtrate). Il costo dello strato collassa da "modellazione dati + UI" a **"solo UI"**. Resta v2 per priorità, ma è molto più vicino di quanto stimato in v1.0.

### Strato 4 — Safety engine sul movimento reale (Visione)
**Riformulazione chiave:** il safety engine *"in entrata"* (atleta → sistema) è più potente di quello "in uscita". L'atleta si registra mentre esegue; il sistema (o il trainer guidato dal sistema) confronta con l'animazione di riferimento e segnala scostamenti via pose estimation (tecnologia matura, **non** richiede il 3D rigged del bundle).
**Convergenza perfetta con l'architettura:** l'analisi del corpo è il dato più sensibile che esista. Eseguita localmente sul PC del trainer, consente la frase che nessun concorrente cloud può dire: *"la tua forma viene analizzata e non lascia mai il computer del tuo trainer"*. Il vincolo architetturale diventa l'argomento di vendita sulla feature più preziosa. È la roadmap che giustifica la scelta data-blind agli investitori.
**Verificato sul codice — il substrato dati esiste già:** demand vector 10D per esercizio (skill, coordinazione, stabilità, balistico, impatto, carico assiale, complesso di spalla, carico lombare, grip, metabolico — DB-backed con fallback a registry), junction `esercizi_condizioni` (4.168 righe) e campo `controindicazioni`. Distinzione importante: il safety engine **dati-driven** (matching demand/controindicazioni ↔ condizioni dell'atleta) ha già la base computazionale ed è cosa diversa dalla **pose estimation sul movimento reale**, che resta Visione. Il primo può maturare prima del secondo.

### Mappa muscolare 2D — *promossa da "candidata" a CONFERMATA in v2.1 (AC-6)*
La verifica dall'interno ha sciolto la riserva: la junction `esercizi_muscoli` ha **6.996 righe e copre il 100% dei 466 esercizi attivi** (zero esclusi), con ruoli `primary`/`secondary`/`stabilizer` e valore di attivazione — **più ricca** dei campi JSON `muscoli_primari`/`muscoli_secondari`, che vanno trattati come rappresentazione legacy di display. **La junction è la fonte autorevole.** In più, il campo `muscle_map_url` esiste già sul modello `Exercise` (oggi vuoto su tutti i record): il punto di atterraggio c'è. "Mostrare quali muscoli lavorano" non richiede né il 3D anatomico né il bundle: SVG corpo umano fronte/retro con muscoli come path nominati, colorati via data-binding (primari pieni, secondari attenuati, stabilizzatori opzionali). Costo minimo, credibilità scientifica alta. Il 3D con muscoli-oggetti (§2bis.3) resta la versione premium futura. **Entra in POC accanto ad AC-5.**

---

## 4. Specifica prescrittiva — Strato 1 (POC)

### 4.1 Contesto del codebase — VERIFICATO dall'interno (query dirette su catalog.db)
Architettura a **doppio database**, pattern consolidato (identico a `nutrition.db`):
- **`catalog.db`** — read-only, shipped con l'installer (ADR-007: pre-costruito in compiled mode, `tools/` fuori dal bundle). Contiene gli esercizi builtin: **500 esercizi totali, 466 attivi** (ID preservati), **894 relazioni** progressione/regressione/variante (`ExerciseRelation`), **750 media** foto inizio/fine movimento (`ExerciseMedia`; 359 esercizi attivi coperti, 107 scoperti), **6 tabelle tassonomiche** (`muscoli`, `articolazioni`, `condizioni_mediche` + junction `esercizi_muscoli` 6.996 righe, `esercizi_articolazioni`, `esercizi_condizioni` 4.168 righe). Seed idempotente al startup con filtraggio FK orfane.
- **`crm.db`** — il database business del trainer. È qui che vive ogni personalizzazione.
- **Esercizi custom del trainer: non esistono ancora.** Tutti gli endpoint write del catalogo (`POST/PUT /exercises`, relazioni) ritornano `501 Not Implemented`. L'overlay AC-1 è greenfield, **ma con un vincolo di design**: se in futuro gli esercizi custom vivranno in una tabella separata su crm.db con il proprio spazio ID, l'overlay agganciato per `exercise_id` intero rischia collisioni. Prevedere da subito un namespacing (es. `source` + `id`): costa zero ora, costa una migrazione dopo.

**Conseguenza prescrittiva:** il trainer **non può modificare le righe del catalogo**. La personalizzazione dello Strato 1 è per costruzione un **overlay in `crm.db` agganciato per `exercise_id`** al catalogo immutabile — non campi aggiunti all'oggetto esercizio. Le animazioni del bundle si mappano sul pattern `ExerciseMedia` esistente (AC-2).

### 4.2 Assunzione — VERIFICATA (con precisazione)
L'identificatore stabile **esiste**: sono **ID interi preservati nel seed** per integrità delle FK (relazioni e media vi si agganciano; il seed filtra le FK orfane). **Non** sono UUID: l'UUID appartiene al **naming dei file media** prodotti dal pipeline ffmpeg, e il ponte tra i due mondi è `ExerciseMedia.url`. Il documento v1.0 era corretto nella sostanza, impreciso nella lettera. *Il sistema è la fonte di verità: verifica avvenuta sui file reali, non per assunzione.*

### 4.3 Cosa deve diventare vero (acceptance criteria)

**AC-1 — Personalizzazione a TRE livelli** *(raffinato in v2.0: il vincolo catalogo-immutabile impone tre piani, non due — ed è un design migliore)*:
- **Livello builtin (`catalog.db`):** il contenuto scientifico del catalogo (`coaching_cues`, `note_sicurezza`, `errori_comuni`, `setup`, `esecuzione`, `respirazione`, …) vive nel catalogo e **viaggia con le release** — gli aggiornamenti scientifici raggiungono tutti i trainer senza toccare le loro personalizzazioni.
- **Livello trainer (`crm.db`, overlay per `exercise_id`):** integrazioni/override del trainer sull'esercizio, validi per tutti i suoi atleti — la sua firma metodologica.
- **Livello assegnazione (`crm.db`):** nota individuale + parametri (serie, ripetizioni, carico) per il singolo atleta.
- L'atleta vede la **composizione dei tre**: base scientifica + metodo del trainer + consiglio personale. La semantica di composizione (additiva vs override per campo) la decide Code.
- *Razionale v2.0:* la separazione su due DB rende il design **più robusto** del due-livelli originale: il catalogo è aggiornabile senza schiacciare le personalizzazioni, e le personalizzazioni sopravvivono agli update. L'architettura esistente lo rende naturale, non un costo aggiuntivo.

**AC-2 — Mappatura animazioni: pattern GIÀ ESISTENTE.** `ExerciseMedia` (`exercise_id`, `tipo`, `url`, `ordine`, `descrizione`) esiste e contiene già **750 media** validi (foto inizio/fine movimento, tutte `tipo='image'`). Le animazioni del bundle sono **nuovi record con un nuovo `tipo`** (es. `animation`), URL verso l'MP4 prodotto dal pipeline (§1.3). Nessuna struttura da creare; il meccanismo è dimostrato da centinaia di righe reali. **Nota strategica aggiornata:** il layer visivo esiste al 77% (359/466) — il bundle lo *potenzia* dove c'è e lo *crea* sui 107 esercizi scoperti. Pressione d'acquisto moderata ma reale; resta valido il front-loading pre-agosto.

**AC-3 — Contenuto scientifico: ESISTE GIÀ AL 100% — il lavoro è tuning interno** *(riscritto in v2.1)*. Verifica sul DB reale: **tutti i 10 campi di contenuto ricco sono popolati su 466/466 esercizi attivi** (`coaching_cues`, `note_sicurezza`, `errori_comuni`, `setup`, `esecuzione`, `respirazione`, `descrizione_anatomica`, `descrizione_biomeccanica`, `controindicazioni`, `tempo_consigliato`). Il lavoro non è di creazione né di struttura: è **revisione qualitativa interna (founder/team) in fase di tuning di catalog.db**, prioritizzata sui fondamentali. Decisione founder 2026-06-10: **Alessio è fuori dall'equazione tecnica del contenuto** (eventuale ruolo di validatore/endorsement, non di produttore); decade la dipendenza esterna e la scadenza agosto. Il posizionamento si fonda su "catalogo scientifico proprietario con fonti citate" (il demand vector referenzia NSCA 2016, Sahrmann 2002, Alentorn-Geli 2009). **Prerequisito:** il marcatore `is_fondamentale` (§1.4), che definisce *dove* concentrare il tuning e la metrica di copertura del bundle. Resta il punto di differenziazione più immediato e difendibile: contenuto proprietario AVGV dentro il catalogo, non copiabile riacquistando il bundle.

**AC-4 — Estensibilità verso Strato 2.** La struttura dati dello Strato 1 deve poter accogliere lo Strato 2 (campo risposta dell'atleta) come **ulteriore campo sullo stesso oggetto-assegnazione**, senza rilavoro. Costruire una volta, estendere due volte.

**AC-5 — UI atleta minima, con vincolo di banda** *(esteso in v2.1)*. La vista atleta mostra: animazione + cue di base + nota personale + parametri (serie/reps/carico). Nulla di più per la POC. **Vincolo di banda tunnel:** le clip vivono sul PC del trainer ed escono dal suo uplink residenziale via FRP (in Italia spesso 10-20 Mbps); una scheda con 8 esercizi × 4 MB = 32 MB per page view se precaricata. Prescrizioni: `preload="none"` sui video, poster JPEG (dalle foto esistenti), caricamento della clip **solo all'apertura del singolo esercizio** (tap/viewport). Mai precaricare l'intera scheda.

**AC-6 — Mappa muscolare 2D: CONFERMATA in POC** *(promossa in v2.1)*. SVG corpo umano fronte/retro con muscoli come path nominati, colorati via data-binding dalla junction `esercizi_muscoli` (fonte autorevole: 6.996 righe, copertura 100% degli attivi, ruoli primary/secondary/stabilizer + attivazione). Primari pieni, secondari attenuati. I campi JSON `muscoli_primari`/`muscoli_secondari` sono rappresentazione legacy di display, non fonte. Punto di atterraggio già esistente: `Exercise.muscle_map_url`. Non richiede 3D né bundle; costo minimo, credibilità scientifica alta. Entra in POC accanto ad AC-5.

### 4.4 Vincolo di adozione (il vero rischio, non il codice)
Il rischio dello Strato 1 **non è tecnico, è di adozione.** Se inserire cue e note è macchinoso, i trainer non lo faranno e il differenziatore muore. Il vincolo di design **non è "quante cose si possono personalizzare" ma "quanto è veloce farlo"**:
- I cue di base sono già popolati (AC-3) così il trainer modifica anziché scrivere da zero.
- Rendere l'assegnazione a un atleta un'operazione di pochi secondi.
- *La pigrizia del trainer è il nemico, non la complessità del codice.*

### 4.5 Confine di responsabilità
- **Questo documento (chat + verifiche interne):** intento, struttura a tre livelli, ruolo del contenuto proprietario, acceptance criteria, vincolo di adozione, decisioni di distribuzione (§4bis).
- **Claude Code (dall'interno):** forma dell'overlay in `crm.db`, semantica di composizione dei tre livelli, integrazione col seed esistente, pipeline transcodifica/staging, e le azioni tecniche residue elencate in §5.6.

---

## 4bis. Distribuzione — tutto nell'installer (DECISO, 2026-06-10)

**Decisione founder:** le clip vivono nell'installer. Il software deve essere **funzionante senza download o configurazioni oltre alla licenza** — coerente col posizionamento "CRM professionale locale, zero cloud obbligatorio". La distribuzione raffinata (update incrementali, content pack) si affronta dopo; per la POC è trascurabile.

### 4bis.1 Dimensionamento
- **Ceiling di crescita (calcolo founder):** 1000 esercizi × 2,5-5 MB ≈ **max ~4,9 GB** — accettabile per un CRM professionale locale.
- **Payload POC realistico:** la logica di copertura (§1.4) impone di spedire **solo le clip mappate sul catalogo** → max 466 oggi, verosimilmente meno (copertura parziale del bundle). A 2,5-5 MB/clip (H.264 720p, §1.3): **~1,2-2,3 GB**.
- Lo staging segue il pattern già esistente: `build-media.sh` filtra i media degli esercizi attivi in `dist/media/` → riga `[Files]` in `fitmanager.iss` (oggi `installer/fitmanager.iss:73` per le foto).

### 4bis.2 Vincoli tecnici della pipeline (verificati su `fitmanager.iss`)
1. **Soglia Inno Setup ~2,1 GB:** sopra, serve `DiskSpanning=yes` → output `setup.exe` + file `.bin` affiancati (si distribuisce una cartella/zip, non un singolo exe). Sotto soglia (probabile per la POC) resta il singolo `.exe`. Da monitorare al crescere della copertura.
2. **Compressione: video esclusi.** L'attuale `Compression=lzma2/ultra + SolidCompression=yes` su gigabyte di MP4 già compressi produce guadagno ~zero e tempi di build/install enormi. Le clip vanno marcate **`nocompression`** nella riga `[Files]` dedicata. Il codice resta lzma2.
3. **Canale di distribuzione:** GitHub Releases ha un limite di **2 GB per asset**. Quando l'installer lo supera, il canale naturale è il **VPS Hetzner già attivo** (CPX22, 20 TB/mese inclusi). Da formalizzare quando serve; non blocca la POC (10 fondatori, consegna diretta).
4. **Update path (decisione rimandata esplicita):** ogni release re-spedisce l'intero payload media. Accettato per la POC. Futuro: componente media separata (flag `onlyifdoesntexist` / installer di update leggero senza media).

---

## 5. Azioni aperte

### 5.1 Domande scritte al fornitore (prima dell'acquisto, in ordine di importanza)
1. **Formato di consegna:** solo MP4 renderizzati, o anche file sorgente 3D (glTF/GLB/FBX con rig)? *(Decide se le evidenziazioni strutturali dello Strato 4 sono "ora" o "dopo".)*
2. **Clausola installazione locale:** "la mia app si installa localmente sul PC del trainer e le clip risiedono sul suo disco (transcodificate, con watermark del mio prodotto), accessibili ai suoi atleti via link privato tokenizzato; questo rientra nella N-EB2BL o configura ridistribuzione vietata?" *(La risposta scritta è la protezione legale. La modalità di distribuzione è ora decisa — §4bis — quindi la domanda è formulabile con precisione.)*
3. **Solo se forniscono i sorgenti:** la licenza permette il rendering real-time dei modelli 3D dentro l'applicazione?
4. **Lista degli esercizi inclusi nel bundle** → per calcolare la **copertura del catalogo** (sui **466 attivi**; priorità ai fondamentali `is_fondamentale` e ai **107 esercizi senza foto**). *(La copertura, non il conteggio assoluto delle clip, è la metrica di valutazione — vedi §1.4.)*

### 5.2 Verifica campioni (test condizionante, ridimensionato in v2.1)
Per la POC il chroma-key **non è più necessario** (playback MP4 diretto, §1.3): la verifica campioni serve a validare **qualità di transcodifica a 720p** (leggibilità del movimento, dimensione file reale per clip) e, in prospettiva v2+, la pulizia dello sfondo per gli overlay (testare sui movimenti difficili: attrezzi, bilanciere sopra la testa, capelli sciolti). Richiedere campioni prima dell'acquisto resta condizionante.

### 5.3 Verifica sorgente per Strato 4 v2 (esito ricerca + azione residua)
Ricerca di mercato **già condotta** (vedi §2bis): il bundle tutto-in-uno non esiste; il candidato Strato 4 è la categoria B (modello anatomico rigged con muscoli-come-oggetti, riferimento MotionCow Ultimate Human Anatomy). **Azione residua:** quando si affronterà lo Strato 4, decidere tra (a) acquistare un modello anatomico categoria B + procurare/animare i ~50-80 esercizi sopra, oppure (b) commissioning custom. Entrambi subordinati alla verifica licenza-ridistribuzione (§2bis.3 caveat 2). Non blocca settembre.

### 5.4 Tuning contenuto catalogo (interno) *(riscritto in v2.1 — sostituisce "Asset Alessio")*
Revisione qualitativa dei campi di contenuto ricco (già popolati al 100%, AC-3) sui ~50-80 fondamentali, condotta internamente (founder/team) in fase di tuning di catalog.db. Nessuna dipendenza esterna, nessuna scadenza agosto. Prerequisito: introduzione del marcatore `is_fondamentale` (§5.6.1).

### 5.5 Domande al venditore pack TurboSquid (se lo si vuole valutare — in ordine, sconto per ultimo)
1. **Numero di esercizi/animazioni distinti** contenuti nel pack? *(Decisivo per l'argomento volume; la scheda non lo dichiara.)*
2. **L'anatomia muscolare è geometria 3D separata o texture dipinta** sul modello? *(Decide se le evidenziazioni possono essere muscolari o solo scheletriche.)*
3. **La licenza permette la ridistribuzione del modello dentro un'app installata sul PC di clienti terzi, in un prodotto commerciale a pagamento?** *(Punto critico assoluto, come per Exercise Animatic.)*
4. **Screenshot/render reali del modello + lista esercizi inclusi** (per validare contro le specifiche contraddittorie, §2bis.4).
5. Solo dopo le risposte sopra: lo sconto offerto.

### 5.6 Azioni tecniche per Code *(verifiche v2.0 risolte — restano le azioni)*
Esiti delle verifiche dall'interno (2026-06-10) e azioni residue:
1. **Marcatore fondamentali (NUOVA, prioritaria):** `in_subset` è il flag "database attivo" (466 `True`), non i fondamentali. Introdurre campo `is_fondamentale` nel seed JSON + modello (zero Alembic: catalog.db è seed-driven). Sblocca AC-3, §5.1.4, §5.4.
2. **`is_compiled()` / `dir()` (CONFERMATO, esteso):** il check `"__compiled__" in dir()` dentro una funzione non rileva mai Nuitka (`dir()` ritorna lo scope locale). Presente in `seed_exercises.py:39` **e in `config.py:63` dentro `is_compiled()`** — quest'ultimo usato da license enforcement e Swagger gating; oggi regge solo perché Nuitka standalone setta anche `sys.frozen` (confermato dai test di produzione). Normalizzare in un unico helper corretto.
3. **Naming seed (CONFERMATO, peggio del previsto):** `seed_exercise_relations.json` esiste ma contiene le **junction tassonomiche** (6.009 muscoli + 1.234 articolazioni + 4.168 condizioni); le progressioni vivono in `seed_exercise_progressions.json`. Allineare docstring di `seed_exercises.py` e valutare rinomina per eliminare la trappola.
4. **Pruning seed media (NUOVA):** `seed_exercise_media.json` referenzia 894 exercise_id del catalogo pre-rebuild; 1.038 entry su 1.788 sono orfane (filtrate dal FK guard — i 750 in DB sono corretti). Pruning del seed + pulizia file orfani in `data/media` locale (lo staging installer già filtra gli attivi).
5. **Muscoli — fonte autorevole (RISOLTO):** la junction `esercizi_muscoli` è autorevole (copertura 100%, ruoli + attivazione); i campi JSON su `Exercise` sono display legacy. AC-6 sbloccata.
6. **Esercizi custom (RISOLTO):** non esistono (endpoint 501). Overlay AC-1 greenfield con vincolo namespacing (§4.1).
7. **Nuitka nei docstring (RISOLTO):** migrazione PyInstaller→Nuitka già avvenuta e documentata (ADR-007); PyInstaller resta fallback (`fitmanager.spec`). Nessuna azione.
8. **Cross-reference ADR-007** (catalog.db pre-costruito, `tools/` fuori bundle): questo documento vi si appoggia (§4.1); mantenerlo coerente con l'ADR.

---

## 6. Sintesi in una frase

> Non ci si differenzia sulle animazioni (commodity). Ci si differenzia perché si è gli unici a legare contenuto generico a dato personale protetto per architettura, con un **catalogo proprietario di 500 esercizi (466 attivi)** già completo di tassonomia, progressioni, controindicazioni e **contenuto scientifico popolato al 100%**. La POC realizza lo Strato 1 (clip MP4 H.264 nell'installer mappate su `ExerciseMedia` + personalizzazione a tre livelli + tuning interno del contenuto + mappa muscolare 2D); la visione (safety engine locale) è ciò che rende la scelta data-blind un argomento di vendita, non un vincolo.

---

## Changelog
- **v2.1** — Verifica **dall'interno** (Claude Code: query dirette su catalog.db, seed JSON, router, installer) + decisioni founder 2026-06-10. **Numeri canonici:** 466 attivi / 894 relazioni / 750 media / 107 esercizi senza foto; copertura calcolata su 466. **`in_subset` ≠ fondamentali** → nuovo marcatore `is_fondamentale` (§5.6.1). **AC-3 riscritto:** contenuto ricco già popolato al 100% su 466/466 → lavoro = tuning interno; **Alessio fuori dall'equazione tecnica** (decisione founder), decade la scadenza agosto. **Nuovo §4bis Distribuzione (DECISO):** tutto nell'installer, payload POC 1,2-2,3 GB, `nocompression` sui video, soglia DiskSpanning 2,1 GB, canale VPS oltre i 2 GB, update path rimandato esplicito. **Formato POC:** MP4 H.264 720p + poster (vincolo iOS Safari: niente WebM-alpha verso l'atleta); chroma-key retrocesso a tecnica v2+ per overlay (§5.2 ridimensionato). **Strato 0 corretto:** branding trainer = overlay runtime UI; ffmpeg solo per watermark generico batch. **AC-5 esteso:** vincolo banda tunnel (preload none, poster, lazy per esercizio). **AC-6 promossa da candidata a confermata** (junction 100%, `muscle_map_url` già sul modello). **Gap media spiegato:** seed stale pre-rebuild (894 ID referenziati vs 500 in catalogo). §5.6 convertito da "verifiche da fare" a "esiti + azioni residue" (incluso bug `dir()` anche in `config.py:63`).
- **v2.0** — Verifica contro il codebase reale (`api/seed_exercises.py`, `api/seed_taxonomy.py`, condivisi in chat dal founder). Assunzione §4.2 **verificata** (ID interi preservati; ponte UUID via `ExerciseMedia.url`). AC-1 raffinato a **tre livelli** (vincolo catalogo-immutabile: `catalog.db` read-only + overlay in `crm.db`). AC-2 riclassificato come **pattern esistente** (`ExerciseMedia`). AC-3 ridotto a **lavoro di contenuto** (campi già presenti). Strato 3 **riprezzato** (grafo esistente → solo UI). Strato 4 distinto in **dati-driven** vs **pose estimation** (Visione). Aggiunta **AC-6 candidata** (mappa muscolare 2D da `esercizi_muscoli`). Metrica bundle spostata da conteggio a **copertura del catalogo**. Aggiunte note tecniche per Code (§5.6).
- **v1.0** — Strategia iniziale: principio di differenziazione, decisione MP4/sorgente, quattro strati con ranking, specifica Strato 1, ricerca di mercato (§2 e §2bis).
