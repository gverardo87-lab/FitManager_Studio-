# LEARNING_MEDIA_CLOUD_ARCHITECTURE.md

**Tipo:** materiale didattico personale (`docs/learning/`) — **non vincolante per Claude Code**.
**Scopo:** comprendere a fondo l'architettura "bundle animazioni su cloud, doppio flusso" **prima** di consolidarla nel documento tecnico (EXERCISE_LIBRARY_STRATEGY v2.2). Metodo: macro prima del micro; tre livelli di perché per ogni concetto (cos'è / perché lo voglio / perché funziona sotto); le modalità di fallimento sono parte della comprensione, non appendice.
**Stato:** a supporto di una decisione in corso di consolidamento. **Finché l'autotest (§9) non passa, la v2.2 non si consolida.**
**Cross-ref:** `EXERCISE_LIBRARY_STRATEGY.md` (§0, §1.1, §1.3, §4bis), `TUNNEL_SECURITY_BOUNDARY.md` (P2), `LEARNING_NETWORKING.md` (DNS, TLS, SNI), `BUILD_LOG.md`.

---

## 0. Il quadro macro — prima il disegno, poi i pezzi

Oggi tutto ciò che l'atleta riceve passa da un solo condotto: il tunnel FRP. La nuova architettura introduce un **secondo condotto**, e la regola che decide chi passa dove è una sola:

> **Il routing segue la classificazione del dato.**
> Dato **personale** → tunnel (TLS termina sul PC del trainer; il VPS resta cieco).
> Contenuto **generico** → diretto al media host (nessuna proprietà di privacy richiesta sul contenuto; solo disciplina sugli accessi).

```
ATLETA (smartphone)
  │
  ├─① pagina + programma + note ──► {instance}.fitmanagerstudio.com
  │     dato PERSONALE · DNS-only · SNI passthrough
  │     VPS (frps) ──tunnel──► PC trainer (frpc) ──► app
  │     TLS termina SUL PC DEL TRAINER  →  P2 intatta
  │
  └─② video animazioni ───────────► media.fitmanagerstudio.com
        contenuto GENERICO · identico per ogni atleta di ogni trainer
        TLS termina AL MEDIA HOST (nginx sul VPS, o object storage)
```

Il **trainer** usa lo stesso condotto ②: la sua UI locale punta agli stessi URL media. Una sola fonte di verità per le clip; **l'installer resta alla taglia attuale (~100 MB)** — i 6-8 GB della libreria transcodificata non vi entrano mai (erano il peso che il piano §4bis "file locali" avrebbe aggiunto, ora superseded); aggiornamenti centralizzati: **zero distribuzione media per-trainer da costruire** (una sola fonte centrale, non N copie sui PC). *Precisazione verificata dall'interno (vedi §5):* "una clip caricata = subito visibile a tutti" vale solo per URL già shippati in `catalog.db`; aggiungere o cambiare una clip viaggia col ciclo di release finché non si introduce lo strato manifest (v2).

Il punto di ricomposizione dei due flussi è **lo schermo dell'atleta**: è l'unico posto dove il contesto personale ("il TUO programma di oggi, con la nota del TUO trainer") e il contenuto generico (la clip dello squat) si incontrano. **Nessun server li vede mai insieme.**

Il perché profondo era già scritto nel §0 della strategia: contenuto generico e dato personale sono cose ontologicamente diverse. La vecchia architettura li accoppiava per inerzia ("l'app è locale, quindi tutto è locale"); la nuova li disaccoppia per principio. Il routing diventa l'espressione fisica della classificazione del dato.

---

## 1. Concetto — La pagina a due origini

**Cos'è.** Una pagina HTML servita dall'origine A i cui elementi `<video>` puntano all'origine B. Il browser carica l'HTML attraverso il tunnel e, incontrando `src="https://media.fitmanagerstudio.com/3f2a….mp4"`, apre una **seconda connessione HTTPS indipendente** verso il media host. Due origini, una pagina.

**Perché lo voglio.** Toglie i byte video dal tunnel (§2), trasforma il caso-licenza da "file ridistribuiti su PC di terzi" a "streaming dalla piattaforma" — cioè il caso che la N-EB2BL benedice testualmente (§1.1 della strategia) — e mantiene l'installer alla taglia attuale (~100 MB) anziché farlo crescere a 6-8 GB.

**Perché funziona sotto.** Il web è nato così: ogni risorsa di una pagina è un fetch indipendente, identificato dal suo URL; l'origine della pagina non vincola da dove arrivano le sottorisorse (le pagine caricano immagini da CDN da decenni). Per il *playback* di un video cross-origin **non serve CORS**: il browser scarica e riproduce. CORS servirà solo il giorno in cui vorremo *leggere* i pixel (canvas/WebGL — pose estimation, v2): allora serviranno header `Access-Control-Allow-Origin` sul media host e attributo `crossorigin` sul tag video. Nota per il futuro, zero impatto POC.

**L'alternativa ingenua, e perché è sbagliata.** "Faccio scaricare i video al FastAPI del trainer dal cloud, e li servo io all'atleta": così i byte rientrano nel tunnel e si perde tutto. Il proxy locale è la negazione del disaccoppiamento — vale la pena nominarlo perché è la prima soluzione che viene in mente e va riconosciuta come trappola.

---

## 2. Concetto — La fisica della banda (perché il video nel tunnel era il caso peggiore)

**Cos'è il problema.** Le linee residenziali italiane sono **asimmetriche**: una FTTC tipica fa ~100 Mbps in download ma 15-20 in upload; un'ADSL anche solo ~1 Mbps in upload. Nel modello tunnel, ogni byte che l'atleta riceve è un byte che il PC del trainer **carica**.

**Perché mi importa.** Una clip 720p pesa 1,5-2 Mbps di flusso. Tre atleti in streaming simultaneo = 4,5-6 Mbps di upload costante dal PC del trainer: su FTTC è un terzo della banda, condivisa col CRM e con tutto il resto; su ADSL è oltre il limite fisico. E la beffa è doppia: ogni byte attraversa VPS↔trainer e poi VPS↔atleta, quindi **l'egress del VPS si paga comunque** — il tunnel aggiunge solo il collo di bottiglia del trainer e doppia latenza, senza risparmiare nulla lato VPS.

**Perché funziona sotto (l'ordine di grandezza).** Il JSON di un programma è ~1-10 KB. Una clip è ~3-4 MB. Rapporto ~1:1000. Il tunnel è perfetto per il primo tipo di traffico (piccolo, personale, sensibile) e pessimo per il secondo (grosso, generico, insensibile). La separazione dei flussi è anche la corretta separazione dei *carichi*: ogni condotto porta il traffico per cui è adatto.

---

## 3. Concetto — DNS e TLS: due nomi, due regimi

**Cos'è.** `*.fitmanagerstudio.com` (le istanze) resta **DNS-only**: il TLS deve attraversare il VPS *intatto*, perché frps instrada leggendo il **SNI** nel ClientHello **senza decifrare** — è ciò che rende vera la P2 (il TLS termina su frpc, sul PC del trainer). `media.fitmanagerstudio.com` è un **nome nuovo con regime opposto**: lì il TLS **termina al media host**, che deve poter leggere le richieste per servire file, Range e cache.

**Perché lo voglio.** Senza terminazione TLS sul media host, niente nginx che serve file statici, niente Range requests, niente caching headers, niente eventuale object storage. Il regime "passthrough" è una proprietà preziosa per il dato personale e un handicap per il contenuto statico. Due regimi diversi per due classi di dato diverse: la coerenza è proprio questa.

**Perché funziona sotto.** Il SNI è il nome del server richiesto, scritto *in chiaro* nel primo pacchetto del handshake TLS: frps lo legge e smista la connessione — ancora cifrata — al tunnel giusto. Per il media host non c'è nulla da smistare verso i trainer: la connessione finisce lì, e il certificato è suo (Let's Encrypt sul VPS — si aggancia naturalmente alla Fase 2/G4 già pianificata; oppure gestito dall'object storage).

**Perché un nome nuovo e non la "promozione" del wildcard.** Il wildcard ha già un regime (passthrough verso i tunnel) e deve mantenerlo per tutte le istanze; un singolo record A esplicito con regime proprio non tocca nulla dell'esistente. È lo stesso pattern già usato per `edge.fitmanagerstudio.com`: un nome, un ruolo, un regime. (La scelta concreta nginx-su-VPS vs object storage è implementazione: la decide Code dall'interno; qui conta capire il *regime*.)

---

## 4. Concetto — HTTP per il video: come un browser scarica davvero un MP4

**Cos'è.** Il browser non scarica un MP4 "tutto e poi lo guarda": chiede **intervalli di byte** (header `Range: bytes=0-…`) e il server risponde **`206 Partial Content`** con il pezzo richiesto. Per iniziare a riprodurre serve l'*indice* del file — l'atomo `moov` del container MP4: se sta in coda al file, il player deve arrivarci prima di partire; `ffmpeg -movflags +faststart` lo sposta in testa.

**Perché lo voglio.** Avvio immediato della clip, scrubbing fluido, e niente download di otto video interi quando l'atleta apre una scheda con otto esercizi: `preload="metadata"` sul tag video (scarica solo le intestazioni) + **poster** JPEG come anteprima — che la strategia v2.1 già ricava dalle foto inizio-movimento esistenti in `ExerciseMedia`.

**Perché funziona sotto.** nginx serve i Range nativamente da disco (header `Accept-Ranges: bytes` in risposta); il decoder hardware H.264 — unico codec baseline universale, deciso in v2.1 proprio per iOS — parte appena ha `moov` e i primi frame. Due dettagli iOS da sapere *prima* di incontrarli: l'autoplay è permesso solo con **`muted`** e **`playsinline`** (le nostre clip sono loop muti: perfetto); senza `playsinline`, iOS manda il video a tutto schermo da solo.

---

## 5. Concetto — Cache a strati e URL immutabili

**Cos'è.** Il naming UUID rende ogni URL **content-addressed**: quel nome corrisponde *per sempre* a quel contenuto. Quindi si può dichiarare `Cache-Control: public, max-age=31536000, immutable` — il browser dell'atleta scarica la clip dello squat **una volta** e non la richiede mai più.

**Perché lo voglio.** L'atleta rivede gli stessi esercizi per settimane: dalla seconda apertura della scheda, zero byte dal media host per le clip già viste. Banda risparmiata, avvio istantaneo, costi giù.

**Perché funziona sotto.** La chiave di cache è l'URL. Se un URL non cambia mai contenuto, non serve mai *invalidare*: **aggiornare una clip = pubblicare un nuovo UUID e aggiornare `ExerciseMedia.url`** (mai sovrascrivere il file vecchio). L'invalidazione della cache — notoriamente uno dei due problemi difficili dell'informatica — viene **eliminata per costruzione dal naming**. È lo stesso principio dei bundle frontend con hash nel filename. Il naming UUID del pipeline, nato per la non-semanticità, acquista qui la sua terza ragione d'essere (1: privacy degli URL; 2: argomento licenza; 3: cache immutabile).

**Vincolo verificato dall'interno — `catalog.db` read-only (Claude Code, 2026-06-13).** Il puntatore alla clip è `ExerciseMedia.url`, e quel campo vive in `catalog.db`, che a runtime è **cifrato e caricato in-memory** (`api/database.py`: `decrypt → conn.deserialize → StaticPool`): è **read-only**, il puntatore non è scrivibile a caldo. Conseguenza onesta sul "come si aggiorna una clip":
- *Pubblicare un nuovo UUID e ripuntare* **non è un'operazione runtime**: viaggia col **ciclo di release** (rebuild + re-ship di `catalog.db`), esattamente come gli aggiornamenti del contenuto scientifico (AC-3 della strategia).
- L'**immutabilità della cache resta vera** (un URL servito non si sovrascrive mai). Ciò che la POC **non** ha è l'update *live* indipendente dalla release.
- Per averlo (**R2, via v2**) serve uno strato **manifest** sul media host (`exercise_id → UUID corrente`, fetchato e cacheato con TTL corto): lì sì, *upload del file + aggiorna manifest = live per tutti, senza re-ship*, preservando l'immutabilità UUID. La promessa "una clip caricata = visibile a tutti" del §0 si realizza pienamente **solo** con il manifest. La POC adotta invece **R1** (URL coniati al build-time e shippati): più semplice, e il beneficio reale vs §4bis è *zero distribuzione media per-trainer*, non l'update live.

**Dove vive questa cache — il punto che inganna.** Non sul VPS: **nel telefono dell'atleta.** Il caching HTTP è un contratto trasportato dagli header, con due ruoli asimmetrici: il media host (nginx) si limita a *dichiarare* la politica stampando `Cache-Control` su ogni risposta; chi *esegue* il contratto è il browser, che archivia i byte sul disco del dispositivo, indicizzati per URL. Alla visita successiva il browser incontra lo stesso URL, trova la voce fresca e non manda **nessuna richiesta** — `immutable` elimina perfino la rivalidazione condizionale (`If-None-Match` → `304 Not Modified`) che un *refresh* della pagina altrimenti provocherebbe: zero pacchetti verso il VPS. Il server non tiene **alcuno stato per-atleta**: non sa chi ha scaricato cosa, non gestisce memorie — esattamente coerente coi vincoli privacy del §6 (zero cookie, zero stato utente sul dominio media). Il disegno della cache e il disegno della privacy si rinforzano a vicenda: una cache "lato server" avrebbe richiesto proprio lo stato per-utente che la P2-media vieta. Due onestà: `max-age` è un *permesso*, non una garanzia — un telefono a corto di spazio può sfrattare la voce, con l'unico effetto di un ri-download silenzioso (sistema auto-riparante); e la conservazione dei pezzi scaricati via Range (§4) è gestione interna del browser — alle nostre taglie (3-4 MB, loop visti per intero) l'effetto netto è il riuso dell'intero file.

Strato opzionale futuro: cache **locale lazy lato trainer** per l'uso offline in palestra (v2; nota di licenza: cache transitoria per uso proprio ≠ distribuzione di file).

---

## 6. Concetto — La superficie privacy e la P2 rienunciata

**Cosa vede il media host.** Per ogni fetch: IP dell'atleta, UUID della clip, orario, user-agent. Niente token, niente nome esercizio, niente identità, niente cookie.

**Perché conta comunque.** L'IP è dato personale (GDPR). E il *pattern* può sfiorare l'art. 9: una sequenza di clip di riabilitazione della spalla dallo stesso IP lascia *inferire* un infortunio. Non è un blocco — è una superficie da disciplinare consapevolmente, non da ignorare.

**I quattro vincoli (diventeranno prescrittivi nella v2.2):**
1. **URL solo-UUID:** mai token, nomi esercizio o ID atleta nel path o in query string.
2. **Split rigoroso:** pagina dal tunnel, video diretti; **zero cookie** sul dominio media.
3. **Log minimi:** IP non loggati, o retention cortissima; un paragrafo dedicato in privacy policy.
4. **Watermark burn-in** "FitManager" (già pianificato in Strato 0): deterrente anti-scraping e argomento verso la clausola N-EB2BL ("file modificati e brandizzati, non grezzi").

**La P2, rienunciata con precisione (non ammorbidita):**
- Prima: *"tutto il traffico dell'atleta attraversa il VPS cifrato; il VPS è cieco."*
- Ora: *"tutto il **dato personale** dell'atleta attraversa il VPS cifrato e termina sul PC del trainer (VPS cieco — invariato). Dal media host transitano **solo fetch anonimi di contenuto generico**, identico per chiunque, con URL non semantici e log minimi."*

Da riflettere in `TUNNEL_SECURITY_BOUNDARY.md` quando la v2.2 si consolida.

---

## 7. Modalità di fallimento — parte della comprensione, non appendice

| # | Guasto | Sintomo per l'atleta | Degradazione | Perché è accettabile / mitigazione |
|---|--------|----------------------|--------------|-------------------------------------|
| 1 | Media host giù | Pagina, programma e note OK; i video non partono | **Graceful** | I due flussi sono indipendenti. Fallback naturale: poster + testi `setup`/`esecuzione` del catalogo (già ricchi). Il catalogo testuale È il piano B |
| 2 | PC trainer spento | Non carica niente (come oggi) | Totale | Il media host attivo non aiuta: la *pagina* nasce dal tunnel. **Dipendenza asimmetrica:** il media dipende dalla pagina, mai il contrario |
| 3 | Trainer offline in palestra | (lato trainer) CRM locale OK, clip no | Parziale | **La regressione vera** della nuova architettura → cache lazy locale (v2) |
| 4 | URL di una clip trapela | Chiunque può scaricare quella clip | Nessuna sul personale | Sicurezza-per-non-indovinabilità (UUID4 ≈ 2¹²² combinazioni): **lecita solo perché il contenuto è generico** — sarebbe inaccettabile per dato personale. Watermark come deterrente alla ripubblicazione |
| 5 | Server senza `Accept-Ranges` | Scrubbing rotto, avvio lento | UX degradata | Configurazione nginx; test esplicito in checklist di deploy |
| 6 | Autoplay bloccato (iOS) | Clip ferma finché non si tocca | UX | `muted` + `playsinline` (clip già mute per natura) |
| 7 | (futuro v2) lettura frame in canvas fallisce | Overlay pose estimation rotto | Solo feature v2 | Richiede CORS + `crossorigin` (§1); zero impatto POC, annotato per non riscoprirlo |

La riga 4 merita un'enfasi metodologica: è lo stesso meccanismo (URL non indovinabile) usato con due giudizi opposti a seconda della classe di dato. Capire *perché* è lecito qui e non lo sarebbe per il dato personale significa aver capito tutta l'architettura.

---

## 8. Cosa NON cambia (ancoraggio)

Tunnel FRP, ShareToken per l'atleta, JWT per il trainer, `crm.db` sul PC del trainer, `catalog.db` cifrato nell'installer, P2 sul dato personale: **tutto invariato**. La nuova architettura *aggiunge* un condotto per il contenuto generico; non tocca un byte del percorso del dato personale. Se domani il media host sparisse, il prodotto tornerebbe esattamente a oggi (più un gap visivo).

---

## 9. Autotest — "Posso spiegarlo o non l'ho capito"

Senza rileggere, a voce alta:

1. Qual è la regola unica che decide quale flusso usa un dato? (§0)
2. Perché il browser può caricare video da un dominio diverso da quello della pagina senza che nessuno glielo "permetta"? E quando invece servirà CORS? (§1)
3. Perché tre atleti in streaming attraverso il tunnel mettono in difficoltà la linea del trainer, e perché il VPS pagava l'egress *comunque* nel vecchio modello? (§2)
4. Perché il wildcard deve restare DNS-only mentre `media.` può terminare TLS al VPS? Cosa legge frps per instradare senza decifrare? (§3)
5. Cosa fa `+faststart`, e cosa succederebbe senza? Cosa risponde il server a una richiesta Range? (§4)
6. Dove vive *fisicamente* la cache che evita il ri-download, e qual è l'unico ruolo del VPS nel contratto di caching? Perché possiamo dire "per sempre", e come si aggiorna una clip senza invalidare niente — e perché nella POC quell'aggiornamento viaggia col ciclo di release anziché essere live (vincolo `catalog.db` read-only), mentre l'update live richiede il manifest (v2)? (§5)
7. Cosa vede esattamente il media host di un atleta? Qual è il rischio di inferenza art. 9 da pattern? Quali sono i quattro vincoli? (§6)
8. Se il media host è giù, cosa vede l'atleta? E se è giù il PC del trainer, a cosa serve il media host attivo? (§7, righe 1-2)
9. Perché la sicurezza-per-non-indovinabilità è lecita per le clip e sarebbe inaccettabile per il dato personale? (§7, riga 4)
10. Enuncia la P2 nella formulazione nuova, a memoria. (§6)

Se una risposta zoppica: la sezione indicata, poi di nuovo la domanda. **Il gate è questo: autotest passato → si scrive la v2.2 e la mail al fornitore.**

---

## Riferimenti
- `EXERCISE_LIBRARY_STRATEGY.md` — §0 (tesi di differenziazione), §1.1 (clausola licenza), §1.3 (formato 720p + poster), §4bis (decisione file-locali, **superseded** dalla v2.2 in arrivo)
- `TUNNEL_SECURITY_BOUNDARY.md` — proprietà P2 (da aggiornare con la riformulazione del §6)
- `LEARNING_NETWORKING.md` — DNS, handshake TLS, SNI
- `BUILD_LOG.md` — voce da aggiungere quando la decisione si consolida

---

## Appendice A — La superficie di implementazione nel codice esistente (verifica Claude Code, 2026-06-13)

Questa appendice è il *ponte* tra l'architettura (il disegno) e il codice che già esiste (la realtà). L'ho verificata dall'interno del codebase: serve a non scoprire le frizioni al momento di implementare.

### A.1 — `media.ts` oggi vieta esattamente ciò che la v2.2 richiede

**Cosa fa.** `frontend/src/lib/media.ts` espone `getMediaUrl()`, che ritorna il **path relativo** così com'è e, nel commento, **vieta esplicitamente** gli URL assoluti: *"NON costruire URL assoluti: falliscono via Tailscale Funnel… e su qualsiasi configurazione dove il browser non raggiunge direttamente la porta del backend."*

**Perché è così.** Oggi i media sono **same-origin**: Next fa da rewrite `/media/* → backend`, quindi un path relativo basta e funziona da LAN, da tunnel, da ovunque. L'URL assoluto romperebbe perché punterebbe a una porta/origine che il browser dell'atleta non raggiunge.

**Perché è il vero blocco della v2.2.** La v2.2 vuole l'**opposto**, ma *solo per il contenuto generico*: la clip deve puntare ad `https://media.fitmanagerstudio.com/…` (cross-origin, assoluto), mentre il dato personale resta relativo/same-origin via tunnel. Quindi `media.ts` non va "sbloccato" a permettere assoluti — va reso **consapevole della classificazione**: generico → host assoluto; personale → relativo. È la traduzione in codice del principio del §0.

**Failure mode.** Se si "sblocca" ingenuamente `getMediaUrl` a ritornare assoluti per tutto, si rischia di mandare cross-origin anche dato personale (regressione P2) o di rompere i media same-origin esistenti. La distinzione non è opzionale: è il cuore del routing-per-classificazione.

### A.2 — Non c'è un solo chokepoint: due percorsi di risoluzione

**Cosa ho trovato.** La risoluzione media è **eterogenea**, su due strade indipendenti:
- **Dashboard/trainer** → usa `getMediaUrl()` (in `esercizi/[id]`, `ExercisesTable` thumbnail, `ExerciseDetailPanel`).
- **Pagina pubblica atleta** (`public/scheda/[token]`, ~830 LOC) → **NON** usa `getMediaUrl`: consuma `ex.foto_start` / `ex.foto_end` come `<img src>` diretti, **emessi dall'endpoint pubblico del backend**, e oggi viaggiano **attraverso il tunnel**.

In più gli URL nascono da fonti diverse: `ExerciseMedia.url` (stored, relativo), `thumbnail_url` (calcolato nel router a query-time), path-by-convention (`ExerciseDetailPanel` costruisce `/media/exercises/{id}/exec_start.jpg`), `foto_start/end` (emessi dall'endpoint pubblico).

**Conseguenza per l'implementazione.** Evolvere la risoluzione media tocca **due punti, non uno**: il resolver frontend *e* l'endpoint pubblico del backend che emette gli URL all'atleta. Quest'ultimo è dove il cross-origin conta di più, perché è il flusso che oggi carica il tunnel.

### A.3 — Il puntatore vive in un DB read-only (richiamo al §5)

Riepilogo del vincolo dimostrato in §5: `ExerciseMedia.url` sta in `catalog.db`, a runtime **cifrato e in-memory** (`api/database.py`: `decrypt → conn.deserialize → StaticPool`) → read-only. Aggiornare un URL = **build-time + release** (R1, POC). L'update *live* indipendente dalla release richiede lo strato **manifest** (R2, v2). Vedi §5 per il dettaglio.

### A.4 — Il marcatore `is_fondamentale` (stato e dipendenza)

Il campo `is_fondamentale` (marcatore dei ~50-80 fondamentali, che guida la **metrica di copertura del bundle**) è oggi **cablato ma vuoto**: presente in modello/schema/type/seed-reader, ma **zero esercizi marcati** nel seed JSON e zero UI. È prerequisito della metrica di copertura, ma il suo collo di bottiglia è una **decisione di dominio** (quali fondamentali), non codice. Lezione di data-modeling trasferibile in `LEARNING_PROGRAMMAZIONE.md` ("Concetti dal campo").
