# DELTA_v2.2 — EXERCISE_LIBRARY_STRATEGY.md

**Tipo:** artefatto di lavoro per **Claude Code** — istruzioni di integrazione del delta v2.1 → v2.2 su `docs/technical/EXERCISE_LIBRARY_STRATEGY.md`. Da eliminare (o archiviare) dopo l'integrazione.
**Fonte:** sessione chat 2026-06-12. La v2.1 è stata letta in chat da un render GitHub (markdown spogliato, coda troncata da metà §4.3): **gli ancoraggi sotto sono semantici, non stringhe esatte** — Code localizza le sezioni per titolo/contenuto nel file reale. Il sistema è la fonte di verità.
**Gate di consolidamento:** la decisione è presa; **commit della v2.2 e invio della mail al fornitore avvengono dopo l'autotest** (`docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` §9, previsto stasera). Correzioni emerse dall'autotest riplasmano questo delta prima del commit.

---

## Operazioni di integrazione (in ordine)

### OP-1 — Header: riga "Stato" — SOSTITUIRE
Sostituire la riga **Stato** con:

> **Stato:** v2.2 — recepita la decisione di **hosting centrale dei media** (§4ter, supersede §4bis), maturata in chat il 2026-06-12 su proposta founder e fondata didatticamente in `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md`. Verifica codebase v2.1 (Claude Code) invariata e tuttora valida. Changelog in coda.

Il resto dell'header (Tipo, Ruolo di Claude Code, Contesto a monte) resta invariato.

---

### OP-2 — §1.1, bullet "Clausola critica aperta" — SOSTITUIRE per intero
Il bullet attuale (clausola critica + nota tecnica su clip su disco, cifratura non praticabile, ecc.) è superato: descriveva il mondo §4bis. Sostituire con:

> - **Clausola di ridistribuzione — ribaltata di segno in v2.2:** la licenza vieta la ridistribuzione dei file grezzi o "lievemente modificati". Con l'hosting centrale (§4ter) le clip **non vengono più copiate sul PC del trainer**: risiedono sul media host AVGV e sono erogate in **streaming HTTPS** agli utenti della piattaforma (trainer e atleti, questi ultimi via pagina tokenizzata). È il modello che la N-EB2BL descrive testualmente come caso d'uso consentito (software company che integra i video nella propria piattaforma offerta a coach e professionisti). La domanda al fornitore (§5.1) passa **da blocker potenziale a conferma di routine** — resta obbligatoria per iscritto prima dell'acquisto. Mitigazioni anti-scraping confermate: watermark generico burn-in (§3 Strato 0) e naming UUID non semantico, ora a **tripla funzione**: privacy degli URL, argomento licenza, cache immutabile (§4ter).

---

### OP-3 — §1.3 — AGGIUNGERE bullet dopo "Formato di playback POC"

> - **Hosting dei media (deciso in v2.2): centrale, su `media.fitmanagerstudio.com`.** Le clip e i poster **non entrano nell'installer** (che resta ~100 MB) **né transitano dal tunnel FRP**: trainer e atleti li caricano in HTTPS diretto dal media host. Razionale, vincoli e proprietà in §4ter; fondamento didattico in `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md`. La scelta di serving (nginx sul VPS vs object storage a egress zero) è implementativa: la decide Code dall'interno.

---

### OP-4 — §4bis — MARCARE SUPERSEDED (non cancellare)
Anteporre alla sezione §4bis questo banner, lasciando il corpo invariato:

> ⚠️ **SUPERSEDED in v2.2** — la decisione attiva è l'**hosting centrale dei media: vedi §4ter**. Sezione conservata per tracciabilità decisionale: il razionale qui esposto era corretto rispetto al vincolo allora assunto ("app locale ⇒ contenuto locale"), vincolo sciolto in v2.2 dal principio *il routing segue la classificazione del dato*.

---

### OP-5 — INSERIRE nuova sezione §4ter (subito dopo §4bis)

> ## 4ter. Hosting centrale dei media (decisione v2.2 — supersede §4bis)
>
> **La regola che governa il routing (prescrittiva):**
> > Il routing segue la classificazione del dato.
> > Dato **personale** → tunnel FRP: TLS termina sul PC del trainer, VPS cieco — **P2 invariata**.
> > Contenuto **generico** → HTTPS **diretto** a `media.fitmanagerstudio.com`, bypassando il tunnel.
>
> **Cosa cambia.** Le clip (MP4 720p) e i poster JPEG risiedono su un media host gestito da AVGV. Trainer e atleti li caricano in HTTPS diretto: i tag `<video>` puntano al media host, mentre pagina e JSON personali continuano a viaggiare nel tunnel. L'installer resta alla taglia attuale (~100 MB): i ~6-8 GB di libreria transcodificata non vi entrano mai. Gli aggiornamenti della libreria diventano centrali (una clip caricata = visibile a tutti i trainer, zero sync da costruire). Il punto di ricomposizione dei due flussi è **lo schermo dell'utente**: nessun server vede mai insieme contesto personale e contenuto generico.
>
> **Cosa NON cambia.** Tunnel FRP, ShareToken, JWT, `crm.db`, `catalog.db` cifrato nell'installer, P2 sul dato personale: **invariati**. Dipendenza asimmetrica: il media dipende dalla pagina (che nasce dal tunnel), mai il contrario. Strato 0 invariato: l'overlay di branding a runtime funziona identico su sorgente remota; il watermark burn-in avviene in transcodifica batch, **prima** dell'upload.
>
> **Razionale (tre forze convergenti):**
> 1. **Licenza:** il caso passa da "file ridistribuiti su PC di terzi" (zona grigia della clausola anti-ridistribuzione) a "streaming dalla piattaforma" — il caso d'uso che la N-EB2BL descrive testualmente come consentito (§1.1).
> 2. **Banda:** l'upload residenziale del trainer non regge streaming multiplo (1,5-2 Mbps per atleta contro i 15-20 Mbps di upload di una FTTC, ~1 di una ADSL), e nel modello tunnel il VPS pagava comunque l'egress (doppio transito) con doppia latenza. Il tunnel resta per il traffico per cui è perfetto (JSON personale, ~KB) e viene sollevato dal traffico per cui è pessimo (video, ~MB: rapporto ~1:1000).
> 3. **Operatività:** installer invariato, distribuzione e aggiornamento centrali della libreria — decisivo per uno sviluppatore solo.
>
> **Vincoli prescrittivi P2-media (violarne uno = regressione):**
> 1. **URL solo-UUID:** mai token, nomi esercizio o ID atleta in path o query string.
> 2. **Split rigoroso:** pagina dal tunnel, media diretti; **zero cookie** sul dominio media; **nessuno stato per-utente** sul media host.
> 3. **Log minimi:** IP non loggati o retention cortissima; paragrafo dedicato in privacy policy (l'IP è dato personale; il *pattern* delle clip può sfiorare inferenze art. 9).
> 4. **Watermark burn-in** generico in transcodifica (già Strato 0).
>
> **P2 rienunciata (da riflettere in `TUNNEL_SECURITY_BOUNDARY.md`):**
> - Prima: *"tutto il traffico dell'atleta attraversa il VPS cifrato; il VPS è cieco."*
> - Ora: *"tutto il **dato personale** dell'atleta attraversa il VPS cifrato e termina sul PC del trainer (VPS cieco — invariato). Dal media host transitano **solo fetch anonimi di contenuto generico**, identico per chiunque, con URL non semantici e log minimi."*
>
> **Regime DNS/TLS.** `media.fitmanagerstudio.com` = nuovo record A esplicito; il TLS **termina al media host** (Let's Encrypt — aggancio naturale alla Fase 2/G4). Il wildcard `*.fitmanagerstudio.com` resta DNS-only / SNI-passthrough, **intoccato**. Stesso pattern già usato per `edge.`: un nome, un ruolo, un regime.
>
> **Caching (prescrittivo).** Clip e poster serviti con `Cache-Control: public, max-age=31536000, immutable`. **Aggiornare un asset = pubblicare un nuovo UUID e aggiornare `ExerciseMedia.url`** — mai sovrascrivere un file esistente: l'invalidazione è eliminata per costruzione dal naming. La cache che evita i ri-download vive **nel browser del client**; il media host si limita a dichiarare la politica e non tiene stato per-utente — coerente coi vincoli 2-3.
>
> **Perimetro del media host.** Serve **tutti gli asset generici**: clip MP4, poster JPEG e, in prospettiva, le mappe muscolari SVG (`muscle_map_url`, AC-6) e ogni asset generico futuro. Per asset di pochi KB (SVG) la scelta bundling-locale vs media host è implementativa: decide Code.
>
> **Serving (decisione a Code, dall'interno).** Opzioni: **nginx sul VPS** con Range nativi e caching headers (CPX22: 20 TB/mese inclusi — alla scala POC margine di un ordine di grandezza), oppure **object storage a egress zero**. Il proxy CDN gratuito classico ha vincoli di ToS sul video puro: non è la prima opzione. Requisiti non negoziabili qualunque sia la scelta: HTTPS, `Accept-Ranges: bytes`, header di cache come sopra, log IP disattivabili/minimi.
>
> **Requisito di degradazione (UI atleta).** Se il media host non risponde, la vista atleta DEVE degradare con grazia: poster (se in cache) + testi `setup`/`esecuzione` del catalogo come fallback. Pagina e programma — che nascono dal tunnel — restano pienamente funzionanti.
>
> **Regressione accettata.** Il trainer offline in palestra perde i video (il CRM locale resta pieno: catalogo, testi, foto bundled invariati). Mitigazione pianificata in v2: **cache lazy locale lato trainer**. Nota licenza differita: cache transitoria per uso proprio ≠ distribuzione di file; conferma da chiedere al fornitore quando la feature si attiverà (§5.1).
>
> **Fondamento didattico:** `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md` — quadro macro, tre livelli di perché, tabella completa delle modalità di fallimento, autotest (§9) il cui superamento è il gate di questo consolidamento.

---

### OP-6 — §5.1, domanda 2 — SOSTITUIRE
La domanda "clausola installazione locale" descrive il mondo §4bis. Sostituire con:

> 2. **Conferma streaming centrale (esito atteso: positivo).** Ottenere conferma scritta che il deployment scelto rientra nella N-EB2BL. Testo pronto da inviare:
>    > *"Our application is a B2B platform for fitness trainers. We host your video clips on our own central media server (transcoded to 720p, with a generic watermark burned in). Trainers and their athletes stream the clips over HTTPS from our platform; the files are never bundled into our installer and never copied to end users' machines. Athletes access their training pages through private tokenized links. Can you confirm that this central-streaming deployment is covered by the N-EB2BL license?"*
>    Domanda differita (v2, quando si attiverà la cache lazy del trainer): conferma che il caching locale transitorio per uso proprio del trainer non costituisce ridistribuzione.

Le altre domande di §5.1 (formato di consegna; lista esercizi per copertura sui 466) restano invariate.

---

### OP-7 — Changelog — AGGIUNGERE voce in testa

> - **v2.2** — **Hosting centrale dei media** (§4ter, supersede §4bis). Routing per classificazione del dato: personale → tunnel (P2 invariata), generico → HTTPS diretto a `media.fitmanagerstudio.com`. Clausola licenza ribaltata di segno: da "ridistribuzione su PC di terzi" a "streaming dalla piattaforma" (§1.1); domanda fornitore riformulata con testo EN pronto (§5.1). Quattro vincoli P2-media prescrittivi (URL solo-UUID; split senza cookie né stato per-utente; log minimi; watermark). P2 rienunciata (da riflettere in `TUNNEL_SECURITY_BOUNDARY.md`). Caching immutabile per naming UUID (terza funzione del naming). Installer invariato (~100 MB). Regressione accettata: trainer offline → mitigazione v2 con cache lazy. Requisito di degradazione graceful della UI atleta. Serving (nginx vs object storage): decisione a Code. Fondamento didattico: `docs/learning/LEARNING_MEDIA_CLOUD_ARCHITECTURE.md`. Consolidamento subordinato al gate autotest (LEARNING §9).

---

### OP-8 — Verifiche incrociate per Code (dall'interno)
1. **Riferimenti residui a §4bis** nel file (oltre a quello sistemato da OP-2): dove indicano la *decisione attiva*, puntare a §4ter; dove sono storici, lasciare.
2. **`ExerciseMedia.url`:** confermare che il campo regge URL assoluti `https://` (tipo, lunghezza, eventuali validazioni); individuare il punto del pipeline che lo popolerà.
3. **Pipeline ffmpeg:** aggiungere lo step di upload al media host dopo transcodifica + watermark (collocazione negli script: a Code).
4. **UI atleta/trainer:** scovare eventuali assunzioni di media serviti in locale o con path relativi → URL assoluti.
5. **CORS:** non necessario per il playback `<video>` cross-origin; annotare che servirà (header + attributo `crossorigin`) solo per la lettura frame in canvas (pose estimation, v2).

---

## Azioni a valle (fuori da questo documento)
- **`BUILD_LOG.md`** — voce: decisione hosting centrale media (data, razionale in una riga, link a §4ter e al learning doc).
- **`TUNNEL_SECURITY_BOUNDARY.md`** — recepire la P2 rienunciata (formulazione in §4ter).
- **Mail al fornitore** — invio **dopo** il gate autotest; testo EN già in §5.1/OP-6.
- **DNS** — record A `media.fitmanagerstudio.com` (fase implementativa, insieme alla scelta di serving).
- **Privacy policy** — paragrafo sul dominio media (vincolo 3), quando si redige la policy.
