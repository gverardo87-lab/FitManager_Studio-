# EXERCISE_LIBRARY_STRATEGY.md

**Stato:** v2.2 — recepita la decisione di **hosting centrale dei media** (§4ter, supersede §4bis), maturata in chat il 2026-06-12 su proposta founder e fondata didatticamente in `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md`. Verifica codebase v2.1 (Claude Code) invariata e tuttora valida. Changelog in coda.
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
- **Clausola di ridistribuzione — ribaltata di segno in v2.2:** la licenza vieta la ridistribuzione dei file grezzi o "lievemente modificati". Con l'hosting centrale (§4ter) le clip **non vengono più copiate sul PC del trainer**: risiedono sul media host AVGV e sono erogate in **streaming HTTPS** agli utenti della piattaforma (trainer e atleti, questi ultimi via pagina tokenizzata). È il modello che la N-EB2BL descrive testualmente come caso d'uso consentito (software company che integra i video nella propria piattaforma offerta a coach e professionisti). La domanda al fornitore (§5.1) passa **da blocker potenziale a conferma di routine** — resta obbligatoria per iscritto prima dell'acquisto. Mitigazioni anti-scraping confermate: watermark generico burn-in (§3 Strato 0) e naming UUID non semantico, ora a **tripla funzione**: privacy degli URL, argomento licenza, cache immutabile (§4ter).

### 1.2 Implicazione tecnica MP4 vs sorgente 3D
- **MP4 (rendering finito):** consente crop, colore globale, overlay disegnati in coordinate fisse, conversione in WebM con alpha (chroma key se lo sfondo è a tinta unita). Le evidenziazioni sono **"cieche"**: si disegna in coordinate fisse, il software non "sa" dove sia un ginocchio. Funziona per parti che restano relativamente ferme (schiena in uno squat, core in un plank).
- **Sorgente 3D (glTF/GLB/FBX con rig):** consente evidenziazioni **strutturali** legate alle ossa nominate, rendering real-time in browser (three.js, già nello stack), reazione visiva al safety engine. È raro che un bundle a basso costo consegni i sorgenti.
- **Vincolo client scoperto in v2.1 (decisivo per il formato di playback):** gli atleti aprono i link su smartphone, e **iOS Safari non supporta WebM con canale alpha**. Il WebM-alpha resta una tecnica valida per gli overlay del safety engine (v2+, dove il canale di rendering è controllabile), **non** per il playback POC rivolto all'atleta.

### 1.3 Decisione
- **POC (settembre 2026): MP4.** Massimizza numero di esercizi (argomento commerciale), copertura fitness reale, licenza già allineata, zero lavoro di rendering real-time.
- **Formato di playback POC (deciso in v2.1): MP4 H.264 720p + poster JPEG.** Transcodifica ffmpeg batch dei master 4K a ~1,5-2 Mbps (~3-4 MB per loop di 15s). H.264 è l'unico baseline con decodifica hardware universale (incluso iOS Safari). Il poster di ogni clip si ricava dalle foto inizio-movimento già esistenti in `ExerciseMedia`.
- **Hosting dei media (deciso in v2.2): centrale, su `media.fitmanagerstudio.com`.** Le clip e i poster **non entrano nell'installer** (che resta ~100 MB) **né transitano dal tunnel FRP**: trainer e atleti li caricano in HTTPS diretto dal media host. Razionale, vincoli e proprietà in §4ter; fondamento didattico in `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md`. La scelta di serving (nginx sul VPS vs object storage a egress zero) è implementativa: la decide Code dall'interno.
- **v2: valutazione sorgente 3D** per le evidenziazioni strutturali, **solo dopo** validazione di trazione coi dieci trainer.
- **Non far dipendere la POC dalla feature 3D.** Sono livelli di rischio diversi; inseguire il 3D ora rallenta settembre per una feature simulabile con overlay semplici su MP4.

### 1.4 Sul numero di esercizi (numeri canonici verificati in v2.1)
- L'argomento commerciale del numero alto ("3000 esercizi inclusi") è una leva di vendita reale nel B2B: comunica completezza, toglie l'obiezione "manca l'esercizio che faccio fare io".
- **Numero e qualità non sono in conflitto, sono in sequenza:** il numero alto vende; la qualità dei ~50-80 esercizi più prescritti fa restare il trainer. Si parte dal bundle ampio e si cura il sottoinsieme dei fondamentali.
- **Numeri canonici (verificati su `catalog.db` — audit 2026-06-14, `docs/operations/DB_INTEGRITY_AUDIT_2026-06-14.md`):** **522 esercizi totali, 466 attivi** (`in_subset=True`), **894 relazioni** progressione/regressione/variante (940 nel seed, FK orfane filtrate), **750 media** validi (seed potato a 750 il 2026-06-13, §5.6.4), e le junction tassonomiche **6.996 muscoli + 1.452 articolazioni + 5.154 condizioni** (copertura 100% dei 466 attivi). **359 esercizi attivi hanno almeno una foto; 107 sono scoperti** — un argomento *a favore* dell'acquisto del bundle: le clip colmano un gap visivo reale, non duplicano l'esistente. ⚠️ Le stesure precedenti riportavano **4.168 condizioni / 1.234 articolazioni**: erano i numeri della copia **stale** del catalogo in `crm.db` (pre-rebuild), non di `catalog.db`. Vedi audit.
- **La metrica di valutazione del bundle è la copertura sui 466 attivi** (con priorità ai fondamentali e ai 107 senza foto), non il conteggio assoluto delle clip. Nota marketing: *"522 esercizi con progressioni, controindicazioni e descrizioni biomeccaniche"* resta lecito contando il catalogo totale; è un argomento più difendibile di *"2000 clip"*. Decisione commerciale aperta tra founder e partner.
- **Attenzione semantica (verificata in v2.1):** il flag `in_subset` **non** marca i fondamentali — è il flag "database attivo" (466 `True`), usato come filtro di visibilità da dashboard, safety engine e training science. Il marcatore dei ~50-80 fondamentali **esiste già end-to-end ma è ancora vuoto** (*wired-but-empty*): il campo dedicato `is_fondamentale` c'è sul modello (`api/models/exercise.py`), nello schema (`api/schemas/exercise.py`) e nel seed (`api/seed_exercises.py`, default `False`), ma **0 righe sono marcate** in `catalog.db` (verificato 2026-06-23). Il lavoro residuo non è introdurre il campo: è **popolarlo** marcando i ~50-80 fondamentali nel seed JSON — zero migrazioni (catalog.db non ha Alembic). Prerequisito per AC-3 e per la metrica di copertura.

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
**Verificato sul codice — il substrato dati esiste già:** demand vector 10D per esercizio (skill, coordinazione, stabilità, balistico, impatto, carico assiale, complesso di spalla, carico lombare, grip, metabolico — DB-backed con fallback a registry), junction `esercizi_condizioni` (5.154 righe) e campo `controindicazioni`. Distinzione importante: il safety engine **dati-driven** (matching demand/controindicazioni ↔ condizioni dell'atleta) ha già la base computazionale ed è cosa diversa dalla **pose estimation sul movimento reale**, che resta Visione. Il primo può maturare prima del secondo.

### Mappa muscolare 2D — *promossa da "candidata" a CONFERMATA in v2.1 (AC-6)*
La verifica dall'interno ha sciolto la riserva: la junction `esercizi_muscoli` ha **6.996 righe e copre il 100% dei 466 esercizi attivi** (zero esclusi), con ruoli `primary`/`secondary`/`stabilizer` e valore di attivazione — **più ricca** dei campi JSON `muscoli_primari`/`muscoli_secondari`, che vanno trattati come rappresentazione legacy di display. **La junction è la fonte autorevole.** In più, il campo `muscle_map_url` esiste già sul modello `Exercise` (oggi popolato su **29 record**, vuoto sui restanti — verificato 2026-06-23): il punto di atterraggio c'è ed è già parzialmente in uso. "Mostrare quali muscoli lavorano" non richiede né il 3D anatomico né il bundle: SVG corpo umano fronte/retro con muscoli come path nominati, colorati via data-binding (primari pieni, secondari attenuati, stabilizzatori opzionali). Costo minimo, credibilità scientifica alta. Il 3D con muscoli-oggetti (§2bis.3) resta la versione premium futura. **Entra in POC accanto ad AC-5.**

---

## 4. Specifica prescrittiva — Strato 1 (POC)

### 4.1 Contesto del codebase — VERIFICATO dall'interno (query dirette su catalog.db)
Architettura a **doppio database**, pattern consolidato (identico a `nutrition.db`):
- **`catalog.db`** — read-only, shipped con l'installer (ADR-007: pre-costruito in compiled mode, `tools/` fuori dal bundle). Contiene gli esercizi builtin: **522 esercizi totali, 466 attivi** (ID preservati), **894 relazioni** progressione/regressione/variante (`ExerciseRelation`), **750 media** foto inizio/fine movimento (`ExerciseMedia`; 359 esercizi attivi coperti, 107 scoperti), **6 tabelle tassonomiche** (`muscoli`, `articolazioni`, `condizioni_mediche` + junction `esercizi_muscoli` 6.996 righe, `esercizi_articolazioni` 1.452 righe, `esercizi_condizioni` 5.154 righe). Seed idempotente al startup con filtraggio FK orfane.
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

**AC-3 — Contenuto scientifico: ESISTE GIÀ AL 100% — il lavoro è tuning interno** *(riscritto in v2.1)*. Verifica sul DB reale: **tutti i 10 campi di contenuto ricco sono popolati su 466/466 esercizi attivi** (`coaching_cues`, `note_sicurezza`, `errori_comuni`, `setup`, `esecuzione`, `respirazione`, `descrizione_anatomica`, `descrizione_biomeccanica`, `controindicazioni`, `tempo_consigliato`). Il lavoro non è di creazione né di struttura: è **revisione qualitativa interna (founder/team) in fase di tuning di catalog.db**, prioritizzata sui fondamentali. Decisione founder 2026-06-10: **Alessio è fuori dall'equazione tecnica del contenuto** (eventuale ruolo di validatore/endorsement, non di produttore); decade la dipendenza esterna e la scadenza agosto. Il posizionamento si fonda su "catalogo scientifico proprietario con fonti citate" (il demand vector referenzia NSCA 2016, Sahrmann 2002, Alentorn-Geli 2009). **Prerequisito:** il marcatore `is_fondamentale` (§1.4) — campo **già esistente end-to-end ma ancora vuoto** (0 righe marcate), da **popolare** sui ~50-80 fondamentali; definisce *dove* concentrare il tuning e la metrica di copertura del bundle. Resta il punto di differenziazione più immediato e difendibile: contenuto proprietario AVGV dentro il catalogo, non copiabile riacquistando il bundle.

**AC-4 — Estensibilità verso Strato 2.** La struttura dati dello Strato 1 deve poter accogliere lo Strato 2 (campo risposta dell'atleta) come **ulteriore campo sullo stesso oggetto-assegnazione**, senza rilavoro. Costruire una volta, estendere due volte.

**AC-5 — UI atleta minima, con vincolo di banda** *(esteso in v2.1)*. La vista atleta mostra: animazione + cue di base + nota personale + parametri (serie/reps/carico). Nulla di più per la POC. **Vincolo di banda tunnel:** le clip vivono sul PC del trainer ed escono dal suo uplink residenziale via FRP (in Italia spesso 10-20 Mbps); una scheda con 8 esercizi × 4 MB = 32 MB per page view se precaricata. Prescrizioni: `preload="none"` sui video, poster JPEG (dalle foto esistenti), caricamento della clip **solo all'apertura del singolo esercizio** (tap/viewport). Mai precaricare l'intera scheda.

**AC-6 — Mappa muscolare 2D: CONFERMATA in POC** *(promossa in v2.1)*. SVG corpo umano fronte/retro con muscoli come path nominati, colorati via data-binding dalla junction `esercizi_muscoli` (fonte autorevole: 6.996 righe, copertura 100% degli attivi, ruoli primary/secondary/stabilizer + attivazione). Primari pieni, secondari attenuati. I campi JSON `muscoli_primari`/`muscoli_secondari` sono rappresentazione legacy di display, non fonte. Punto di atterraggio già esistente: `Exercise.muscle_map_url` (oggi popolato su **29 record**, vuoto sui restanti). Non richiede 3D né bundle; costo minimo, credibilità scientifica alta. Entra in POC accanto ad AC-5.

### 4.4 Vincolo di adozione (il vero rischio, non il codice)
Il rischio dello Strato 1 **non è tecnico, è di adozione.** Se inserire cue e note è macchinoso, i trainer non lo faranno e il differenziatore muore. Il vincolo di design **non è "quante cose si possono personalizzare" ma "quanto è veloce farlo"**:
- I cue di base sono già popolati (AC-3) così il trainer modifica anziché scrivere da zero.
- Rendere l'assegnazione a un atleta un'operazione di pochi secondi.
- *La pigrizia del trainer è il nemico, non la complessità del codice.*

### 4.5 Confine di responsabilità
- **Questo documento (chat + verifiche interne):** intento, struttura a tre livelli, ruolo del contenuto proprietario, acceptance criteria, vincolo di adozione, decisioni di distribuzione e hosting dei media (§4ter, supersede §4bis).
- **Claude Code (dall'interno):** forma dell'overlay in `crm.db`, semantica di composizione dei tre livelli, integrazione col seed esistente, pipeline transcodifica/staging, e le azioni tecniche residue elencate in §5.6.

---

## 4bis. Distribuzione — tutto nell'installer (DECISO, 2026-06-10)

> ⚠️ **SUPERSEDED in v2.2** — la decisione attiva è l'**hosting centrale dei media: vedi §4ter**. Sezione conservata per tracciabilità decisionale: il razionale qui esposto era corretto rispetto al vincolo allora assunto ("app locale ⇒ contenuto locale"), vincolo sciolto in v2.2 dal principio *il routing segue la classificazione del dato*.

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

## 4ter. Hosting centrale dei media (decisione v2.2 — supersede §4bis)

**La regola che governa il routing (prescrittiva):**
> Il routing segue la classificazione del dato.
> Dato **personale** → tunnel FRP: TLS termina sul PC del trainer, VPS cieco — **P2 invariata**.
> Contenuto **generico** → HTTPS **diretto** a `media.fitmanagerstudio.com`, bypassando il tunnel.

**Cosa cambia.** Le clip (MP4 720p) e i poster JPEG risiedono su un media host gestito da AVGV. Trainer e atleti li caricano in HTTPS diretto: i tag `<video>` puntano al media host, mentre pagina e JSON personali continuano a viaggiare nel tunnel. L'installer resta alla taglia attuale (~100 MB): i ~6-8 GB di libreria transcodificata non vi entrano mai. La distribuzione dei media diventa centrale: **zero copie per-trainer da costruire** (una sola fonte, non N PC). *Precisazione (vedi "Caching" sotto):* aggiungere o cambiare una clip viaggia col ciclo di release perché il puntatore `ExerciseMedia.url` è in `catalog.db` read-only; l'update live indipendente dalla release è una via v2 (manifest). Il punto di ricomposizione dei due flussi è **lo schermo dell'utente**: nessun server vede mai insieme contesto personale e contenuto generico.

**Cosa NON cambia.** Tunnel FRP, ShareToken, JWT, `crm.db`, `catalog.db` cifrato nell'installer, P2 sul dato personale: **invariati**. Dipendenza asimmetrica: il media dipende dalla pagina (che nasce dal tunnel), mai il contrario. Strato 0 invariato: l'overlay di branding a runtime funziona identico su sorgente remota; il watermark burn-in avviene in transcodifica batch, **prima** dell'upload.

**Razionale (tre forze convergenti):**
1. **Licenza:** il caso passa da "file ridistribuiti su PC di terzi" (zona grigia della clausola anti-ridistribuzione) a "streaming dalla piattaforma" — il caso d'uso che la N-EB2BL descrive testualmente come consentito (§1.1).
2. **Banda:** l'upload residenziale del trainer non regge streaming multiplo (1,5-2 Mbps per atleta contro i 15-20 Mbps di upload di una FTTC, ~1 di una ADSL), e nel modello tunnel il VPS pagava comunque l'egress (doppio transito) con doppia latenza. Il tunnel resta per il traffico per cui è perfetto (JSON personale, ~KB) e viene sollevato dal traffico per cui è pessimo (video, ~MB: rapporto ~1:1000).
3. **Operatività:** installer invariato, distribuzione e aggiornamento centrali della libreria — decisivo per uno sviluppatore solo.

**Vincoli prescrittivi P2-media (violarne uno = regressione):**
1. **URL solo-UUID:** mai token, nomi esercizio o ID atleta in path o query string.
2. **Split rigoroso:** pagina dal tunnel, media diretti; **zero cookie** sul dominio media; **nessuno stato per-utente** sul media host.
3. **Log minimi:** IP non loggati o retention cortissima; paragrafo dedicato in privacy policy (l'IP è dato personale; il *pattern* delle clip può sfiorare inferenze art. 9).
4. **Watermark burn-in** generico in transcodifica (già Strato 0).

**P2 rienunciata (da riflettere in `TUNNEL_SECURITY_BOUNDARY.md`):**
- Prima: *"tutto il traffico dell'atleta attraversa il VPS cifrato; il VPS è cieco."*
- Ora: *"tutto il **dato personale** dell'atleta attraversa il VPS cifrato e termina sul PC del trainer (VPS cieco — invariato). Dal media host transitano **solo fetch anonimi di contenuto generico**, identico per chiunque, con URL non semantici e log minimi."*

**Regime DNS/TLS.** `media.fitmanagerstudio.com` = nuovo record A esplicito; il TLS **termina al media host** (Let's Encrypt — aggancio naturale alla Fase 2/G4). Il wildcard `*.fitmanagerstudio.com` resta DNS-only / SNI-passthrough, **intoccato**. Stesso pattern già usato per `edge.`: un nome, un ruolo, un regime.

**Caching (prescrittivo).** Clip e poster serviti con `Cache-Control: public, max-age=31536000, immutable`. **Mai sovrascrivere un file esistente** — l'invalidazione è eliminata per costruzione dal naming. La cache che evita i ri-download vive **nel browser del client**; il media host si limita a dichiarare la politica e non tiene stato per-utente — coerente coi vincoli 2-3.

**Aggiornamento del puntatore — vincolo verificato dall'interno (Claude Code, 2026-06-13).** `ExerciseMedia.url` vive in `catalog.db`, che a runtime è **read-only, cifrato, caricato in-memory** (`api/database.py`: `decrypt → conn.deserialize → StaticPool`): il puntatore **non è scrivibile a caldo**. Conseguenza:
- **POC (R1, decisione attiva):** gli URL dei media sono coniati nel seed e **shippati** in `catalog.db`; aggiungere/cambiare clip viaggia col **ciclo di release** (rebuild + re-ship), esattamente come il tuning del contenuto scientifico (AC-3). Il beneficio reale vs §4bis è *zero distribuzione media per-trainer*, non l'update live.
- **v2 (R2):** per l'update **live** indipendente dalla release, introdurre uno strato **manifest** sul media host (`exercise_id → UUID corrente`, fetch cacheato a TTL corto): upload + aggiorna manifest = visibile a tutti senza re-ship, preservando l'immutabilità UUID. È ciò che realizza pienamente "una clip caricata = visibile a tutti".

**Perimetro del media host.** Serve **tutti gli asset generici**: clip MP4, poster JPEG e, in prospettiva, le mappe muscolari SVG (`muscle_map_url`, AC-6) e ogni asset generico futuro. Per asset di pochi KB (SVG) la scelta bundling-locale vs media host è implementativa: decide Code.

**Serving (decisione a Code, dall'interno).** Opzioni: **nginx sul VPS** con Range nativi e caching headers (CPX22: 20 TB/mese inclusi — alla scala POC margine di un ordine di grandezza), oppure **object storage a egress zero**. Il proxy CDN gratuito classico ha vincoli di ToS sul video puro: non è la prima opzione. Requisiti non negoziabili qualunque sia la scelta: HTTPS, `Accept-Ranges: bytes`, header di cache come sopra, log IP disattivabili/minimi.

**Requisito di degradazione (UI atleta).** Se il media host non risponde, la vista atleta DEVE degradare con grazia: poster (se in cache) + testi `setup`/`esecuzione` del catalogo come fallback. Pagina e programma — che nascono dal tunnel — restano pienamente funzionanti.

**Regressione accettata.** Il trainer offline in palestra perde i video (il CRM locale resta pieno: catalogo, testi, foto bundled invariati). Mitigazione pianificata in v2: **cache lazy locale lato trainer**. Nota licenza differita: cache transitoria per uso proprio ≠ distribuzione di file; conferma da chiedere al fornitore quando la feature si attiverà (§5.1).

**Fondamento didattico:** `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` — quadro macro, tre livelli di perché, tabella completa delle modalità di fallimento, autotest (§9) il cui superamento è il gate di questo consolidamento.

---

## 5. Azioni aperte

### 5.1 Domande scritte al fornitore (prima dell'acquisto, in ordine di importanza)
1. **Formato di consegna:** solo MP4 renderizzati, o anche file sorgente 3D (glTF/GLB/FBX con rig)? *(Decide se le evidenziazioni strutturali dello Strato 4 sono "ora" o "dopo".)*
2. **Conferma streaming centrale (esito atteso: positivo).** Ottenere conferma scritta che il deployment scelto rientra nella N-EB2BL. Testo pronto da inviare:
   > *"Our application is a B2B platform for fitness trainers. We host your video clips on our own central media server (transcoded to 720p, with a generic watermark burned in). Trainers and their athletes stream the clips over HTTPS from our platform; the files are never bundled into our installer and never copied to end users' machines. Athletes access their training pages through private tokenized links. Can you confirm that this central-streaming deployment is covered by the N-EB2BL license?"*

   Domanda differita (v2, quando si attiverà la cache lazy del trainer): conferma che il caching locale transitorio per uso proprio del trainer non costituisce ridistribuzione.
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
1. **Marcatore fondamentali (✅ CABLATO — da popolare):** `in_subset` è il flag "database attivo" (466 `True`), non i fondamentali. Il campo `is_fondamentale` **esiste già end-to-end** — modello (`api/models/exercise.py`), schema (`api/schemas/exercise.py`), seed (`api/seed_exercises.py`, default `False`) — ma è **wired-but-empty: 0 righe marcate** in `catalog.db` (verificato 2026-06-23). Azione residua: **popolarlo** marcando i ~50-80 fondamentali nel seed JSON (zero Alembic: catalog.db è seed-driven). Sblocca AC-3, §5.1.4, §5.4.
2. **`is_compiled()` / `dir()` (✅ RISOLTO — verificato 2026-06-23):** il vecchio check `"__compiled__" in dir()` dentro una funzione non rilevava mai Nuitka (`dir()` ritorna lo scope locale). Ora la rilevazione bundle è centralizzata in **un unico helper corretto**: `config.py` valuta `_is_bundled = getattr(sys, "frozen", False) or "__compiled__" in globals()` **a livello di modulo** (dove `globals()` vede `__compiled__` di Nuitka) e `is_compiled()` lo ritorna (`api/config.py`, con commento esplicito "il check usa globals(), MAI dir()"). `seed_exercises.py` usa `is_compiled()` (via `_frozen_guard`), non più il check inline. License enforcement e Swagger gating consumano lo stesso helper. Bug storico chiuso.
3. **Naming seed (✅ RISOLTO 2026-06-13):** il file (ex `seed_exercise_relations.json`) contiene le **junction tassonomiche** come **export stale pre-rebuild** (6.009 muscoli + 1.234 articolazioni + 4.168 condizioni) — **≠ dai conteggi live di `catalog.db`** (6.996 / 1.452 / 5.154), che le ricalcola via `populate_taxonomy`/`populate_conditions`. Le progressioni vivono in `seed_exercise_progressions.json`. Rinominato in `seed_taxonomy_junctions.json` + docstring allineata; verificato che **nessun codice runtime/build lo legge** (le junction sono calcolate, non caricate). ⚠️ Questo export stale è la fonte dell'errore numerico nelle stesure ≤ v2.1 (vedi §1.4 e `DB_INTEGRITY_AUDIT_2026-06-14.md`).
4. **Pruning seed media (✅ ESEGUITO 2026-06-13):** `seed_exercise_media.json` referenziava 1.788 entry, 1.038 orfane vs il catalogo rebuild (i 750 in DB erano corretti). **Seed potato da 1.788 → 750 entry**; 1.639 file fisici orfani spostati in quarantena `data/_media_orphans_pre_rebuild/` (ignorata da git, mai cancellati senza backup). Seed e DB ora coincidono (750).
5. **Muscoli — fonte autorevole (RISOLTO):** la junction `esercizi_muscoli` è autorevole (copertura 100%, ruoli + attivazione); i campi JSON su `Exercise` sono display legacy. AC-6 sbloccata.
6. **Esercizi custom (RISOLTO):** non esistono (endpoint 501). Overlay AC-1 greenfield con vincolo namespacing (§4.1).
7. **Nuitka nei docstring (RISOLTO):** migrazione PyInstaller→Nuitka già avvenuta e documentata (ADR-007); PyInstaller resta fallback (`fitmanager.spec`). Nessuna azione.
8. **Cross-reference ADR-007** (catalog.db pre-costruito, `tools/` fuori bundle): questo documento vi si appoggia (§4.1); mantenerlo coerente con l'ADR.

---

## 6. Sintesi in una frase

> Non ci si differenzia sulle animazioni (commodity). Ci si differenzia perché si è gli unici a legare contenuto generico a dato personale protetto per architettura, con un **catalogo proprietario di 522 esercizi (466 attivi)** già completo di tassonomia, progressioni, controindicazioni e **contenuto scientifico popolato al 100%**. La POC realizza lo Strato 1 (clip MP4 H.264 nell'installer mappate su `ExerciseMedia` + personalizzazione a tre livelli + tuning interno del contenuto + mappa muscolare 2D); la visione (safety engine locale) è ciò che rende la scelta data-blind un argomento di vendita, non un vincolo.

---

## Changelog
- **v2.2** — **Hosting centrale dei media** (§4ter, supersede §4bis). Routing per classificazione del dato: personale → tunnel (P2 invariata), generico → HTTPS diretto a `media.fitmanagerstudio.com`. Clausola licenza ribaltata di segno: da "ridistribuzione su PC di terzi" a "streaming dalla piattaforma" (§1.1); domanda fornitore riformulata con testo EN pronto (§5.1). Quattro vincoli P2-media prescrittivi (URL solo-UUID; split senza cookie né stato per-utente; log minimi; watermark). P2 rienunciata (da riflettere in `TUNNEL_SECURITY_BOUNDARY.md`). Caching immutabile per naming UUID (terza funzione del naming). Installer invariato (~100 MB). Regressione accettata: trainer offline → mitigazione v2 con cache lazy. Requisito di degradazione graceful della UI atleta. Serving (nginx vs object storage): decisione a Code. Fondamento didattico: `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md`. Consolidamento subordinato al gate autotest (LEARNING §9). **Vincolo `catalog.db` read-only (verifica Code 2026-06-13):** il puntatore `ExerciseMedia.url` si aggiorna al build-time/release (**R1**, POC); update live via **manifest** rimandato a v2 (**R2**). "Zero sync" precisato in "zero distribuzione per-trainer". `media.ts` da evolvere per URL cross-origin (OP-8.4 riformulato).
- **v2.1.1** (2026-06-14) — **Correzione numeri canonici post-audit** (`docs/operations/DB_INTEGRITY_AUDIT_2026-06-14.md`). Le junction `esercizi_condizioni` (**5.154**, non 4.168) ed `esercizi_articolazioni` (**1.452**, non 1.234) erano state misurate sulla copia **stale** del catalogo in `crm.db` (pre-rebuild), non su `catalog.db`. Corretti §1.4, §3 (Strato 4), §4.1. §5.6.3 (rinomina seed) e §5.6.4 (pruning media a 750) marcate eseguite. Catalog.db verificato pristino (0 FK orfane, copertura junction 100%, contenuto 100%).
- **v2.1** — Verifica **dall'interno** (Claude Code: query dirette su catalog.db, seed JSON, router, installer) + decisioni founder 2026-06-10. **Numeri canonici:** 466 attivi / 894 relazioni / 750 media / 107 esercizi senza foto; copertura calcolata su 466. **`in_subset` ≠ fondamentali** → nuovo marcatore `is_fondamentale` (§5.6.1). **AC-3 riscritto:** contenuto ricco già popolato al 100% su 466/466 → lavoro = tuning interno; **Alessio fuori dall'equazione tecnica** (decisione founder), decade la scadenza agosto. **Nuovo §4bis Distribuzione (DECISO):** tutto nell'installer, payload POC 1,2-2,3 GB, `nocompression` sui video, soglia DiskSpanning 2,1 GB, canale VPS oltre i 2 GB, update path rimandato esplicito. **Formato POC:** MP4 H.264 720p + poster (vincolo iOS Safari: niente WebM-alpha verso l'atleta); chroma-key retrocesso a tecnica v2+ per overlay (§5.2 ridimensionato). **Strato 0 corretto:** branding trainer = overlay runtime UI; ffmpeg solo per watermark generico batch. **AC-5 esteso:** vincolo banda tunnel (preload none, poster, lazy per esercizio). **AC-6 promossa da candidata a confermata** (junction 100%, `muscle_map_url` già sul modello). **Gap media spiegato:** seed stale pre-rebuild (894 ID referenziati vs 500 in catalogo). §5.6 convertito da "verifiche da fare" a "esiti + azioni residue" (incluso bug `dir()` anche in `config.py:63`).
- **v2.0** — Verifica contro il codebase reale (`api/seed_exercises.py`, `api/seed_taxonomy.py`, condivisi in chat dal founder). Assunzione §4.2 **verificata** (ID interi preservati; ponte UUID via `ExerciseMedia.url`). AC-1 raffinato a **tre livelli** (vincolo catalogo-immutabile: `catalog.db` read-only + overlay in `crm.db`). AC-2 riclassificato come **pattern esistente** (`ExerciseMedia`). AC-3 ridotto a **lavoro di contenuto** (campi già presenti). Strato 3 **riprezzato** (grafo esistente → solo UI). Strato 4 distinto in **dati-driven** vs **pose estimation** (Visione). Aggiunta **AC-6 candidata** (mappa muscolare 2D da `esercizi_muscoli`). Metrica bundle spostata da conteggio a **copertura del catalogo**. Aggiunte note tecniche per Code (§5.6).
- **v1.0** — Strategia iniziale: principio di differenziazione, decisione MP4/sorgente, quattro strati con ranking, specifica Strato 1, ricerca di mercato (§2 e §2bis).
