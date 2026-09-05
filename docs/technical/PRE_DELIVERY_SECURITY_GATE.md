# PRE_DELIVERY_SECURITY_GATE.md

**Versione:** 1.2
**Stato:** Vincolante sui criteri di accettazione — non vincolante sull'implementazione
**Owner:** Giacomo Verardo (AVGV Technologies)
**Destinatario:** agenti e sviluppatori che implementano o verificano la consegna
**Collocazione:** `docs/technical/`

> **Nota di versione 1.1 (2026-06-16):** documento annotato contro il codice reale (bridge rule §6).
> Ogni gate Tier 1–2 porta ora una riga **`Stato nel codice (verificato 2026-06-16)`** che fotografa
> lo stato effettivo. Tre correzioni ground-truth rispetto alla v1.0: **G4 è già ~60% implementato**
> (lifecycle token presente nel modello), **G7 ha già lo strato edge** (tunnel guard nel middleware
> Next), e il report legale Tier 3 vive in `docs/business/LEGAL_REGULATORY_REPORT.md`
> (non in `docs/technical/`). Il design del gate più pesante (G1) è in
> `docs/adr/ADR-013-crm-db-encryption-at-rest.md` (accepted 2026-06-17).

> **Nota di versione 1.2 (2026-09-04):** S1.0 docs-first ratifica owner unico per installazione
> compilata e chiarisce il boundary auth/DB in ADR-013 Addendum I. Il contratto esecutivo G1+G5 è
> `docs/specs/SPEC_S1_G1_G5_CIFRATURA_CRM.md`. Lo stato nel codice resta gap fino ai code gate.

---

## 0. Perché esiste questo documento

Un possibile lighthouse pilot macOS, segnalato tramite Alessio, ha reso concreta la prima consegna a
un trainer che potrebbe usare FitManager con **atleti reali e dati personali reali**. Il target di
accettazione non modifica il criterio: qualunque primo deployment data-bearing fissa lo standard che
ogni trainer successivo eredita — POC incluso. Daniele è il primo target Mac noto, non una deroga né
il fondamento unico della strategia.

Questo cambia il modello di rischio in modo radicale. Finora la modalità di fallimento operativa era *"il software ha un bug"* — recuperabile con una patch. Dal momento in cui i dati di un atleta reale entrano nel sistema, la modalità di fallimento operativa diventa *"i dati personali di persone identificabili sono esposti, persi, o accessibili a chi non dovrebbe averli"* — un data breach, con obbligo di notifica al Garante entro 72 ore ai sensi dell'art. 33 GDPR, e potenzialmente verso gli interessati stessi ai sensi dell'art. 34.

Questo documento definisce il **gate di sicurezza** che il software deve superare prima di toccare i dati di un singolo atleta reale. È prescrittivo su *cosa deve essere vero e perché* — i criteri di accettazione sono vincolanti. È deliberatamente silenzioso su *come*: ogni decisione implementativa spetta a Claude Code, che si adatta alla struttura reale del codebase, la quale è la fonte di verità sopra qualsiasi assunzione contenuta in questo documento.

**Decisione founder (2026-06-16):** la solidità e la sicurezza sono il fondamento; il fattore tempo è una conseguenza, non un rischio da scambiare con scorciatoie. G1 si fa **full, password-bound** (nessuna postura interim). Niente "bruciarsi in partenza" per guadagnare pochi giorni su una consegna che fissa la barra per tutti.

**Il gate è una precondizione vincolante alla consegna, non una backlog.** Le voci del Tier 1 (Bloccanti) devono essere soddisfatte prima che il trainer riceva il software. Le voci del Tier 2 (Fortemente raccomandate) dovrebbero essere soddisfatte prima della consegna oppure portare un'eccezione esplicita, documentata e con scadenza temporale accettata da Giacomo. Il Tier 3 (GDPR / Processo) è un binario parallelo che deve essere completo prima che il trainer faccia l'onboarding del primo atleta, ma non è tutto codice.

---

## 1. La premessa architetturale che rende tutto trattabile

Il differenziatore centrale di FitManager — **local-first, data-blind by design** — è anche ciò che fa convergere questa analisi di sicurezza invece di farla esplodere. Vale la pena dichiarare la premessa in modo esplicito, perché ogni voce qui sotto ne è una conseguenza.

- **I dati personali del trainer (le schede degli atleti) vivono sul PC del trainer stesso**, in un database SQLite per-trainer (`crm.db`), distribuito come app desktop (Nuitka; PyInstaller fallback).
- **Il VPS è data-blind.** Il tunnel FRP fa routing SNI (`vhostHTTPSPort=443` + `https2http`) senza terminare il TLS; la terminazione avviene su `frpc` sul PC del trainer. Proprietà confermata da test end-to-end reale. Il VPS strutturalmente non può leggere il traffico di trainer o atleti. **Questa proprietà (P2) è portante per l'intero assetto GDPR e non deve regredire.**
- **Gli atleti accedono tramite link pubblico tokenizzato a installazione zero** (`ShareToken`, parametro query UUID4, lookup su DB) — strutturalmente incompatibile con le credenziali del trainer.

La conseguenza: la superficie di attacco non è "un cloud che contiene i dati di tutti". Sono due superfici strette e ben definite:

1. **Il PC del trainer** — dove i dati risiedono fisicamente (riservatezza a riposo, disponibilità/backup).
2. **Il portale pubblico** — l'unica cosa esposta a internet (sicurezza dei token, resistenza all'abuso, sicurezza del trasporto).

Tutto ciò che è in Tier 1 e Tier 2 è un criterio di accettazione su una di queste due superfici. Nient'altro necessita di hardening per questa consegna, perché nient'altro contiene i dati.

---

## 2. Tier 1 — BLOCCANTI (nessuna consegna senza questi)

### G1. Cifratura a riposo del database SQLite del trainer

**Cosa deve essere vero:** Il database SQLite per-trainer che contiene i dati personali degli atleti deve essere cifrato a riposo. Se il portatile del trainer viene perso, rubato o comunque acceduto fisicamente, il file `.db` non deve essere leggibile in chiaro con strumenti standard.

**Perché:** È la conseguenza più importante del modello local-first. La stessa architettura che dà a FitManager il suo vantaggio GDPR (i dati non sono mai su un cloud) colloca i dati su un dispositivo consumer portatile fuori dal controllo fisico di Giacomo. Le schede degli atleti includono dati che qualificano come **categoria particolare ai sensi dell'art. 9 GDPR** (relativi alla salute: infortuni, peso, parametri fisici, limitazioni all'allenamento). Lo storage in chiaro di dati ex art. 9 su un dispositivo rubabile è il vettore di breach a più alta probabilità e più alto impatto dell'intero sistema.

**Criteri di accettazione:**
- I dati personali e sanitari degli atleti non sono recuperabili dal file del database senza il segreto di decifratura.
- Il segreto di decifratura non è memorizzato accanto al database in modo da vanificare la cifratura (cioè non in chiaro nella stessa cartella, non hardcoded nel binario distribuito).
- Il flusso di derivazione/sblocco della chiave è legato all'autenticazione del trainer, così che il solo possesso del file sia insufficiente.
- L'approccio è documentato in una voce di `BUILD_LOG.md`, incluso dove vive la chiave e da quale minaccia difende e da quale no.

**Stato nel codice (riverificato 2026-09-05):** ❌ **Gap G1 ancora reale, boundary pre-login
corretto in S1.2.** `crm.db` esistente è ancora plaintext sul disco e non esiste ancora l'opener
SQLCipher password-bound: i criteri G1/G5 non sono quindi soddisfatti. Il commit `d197467` ha però
rimosso l'engine business import-time e gli accessi anticipati: in compiled mode il lifespan resta
`LOCKED` e non apre, crea, sincronizza, verifica o copia `crm.db`; health resta disponibile senza
sessione business. Il modello `catalog.db`/`nutrition.db` (`decrypt_db_to_bytes` →
`sqlite3.deserialize`) resta invariato e non è riutilizzabile per il CRM read-write/password-bound.
Restano da collegare envelope/login e SQLCipher (S1.3), migrazione legacy (S1.4) e backup bundle
cifrato (S1.5). Decisione in **ADR-013 + Addendum I**; contratto code-gate in
**`docs/specs/SPEC_S1_G1_G5_CIFRATURA_CRM.md`**.

**Decisione implementativa ora ratificata:** ADR-013 sceglie SQLCipher + envelope DEK–KEK + boot a
due fasi; l'Addendum I e la SPEC S1 fissano owner unico, candidate engine, KDF/recovery, migrazione e
backup. Il criterio di questo gate resta la proprietà verificabile, non il solo uso della libreria.

**Fondazione S1.1 (2026-09-04):** ✅ commit `efda1fe` implementa e verifica le primitive pure
dell'envelope v1 (scrypt/HKDF/AES-GCM, doppio slot e atomic write). Non cambia ancora engine, boot,
auth, migrazione o backup e `crm.db` resta plaintext: **G1 non è GREEN** e la tensione G5 resta
aperta.

**Boundary S1.2 (2026-09-05):** ✅ commit `d197467` rende l'engine business late-bound, verifica e
prepara un candidate engine prima della pubblicazione atomica, serializza gli unlock concorrenti e
fa fallire chiusi CRM/backup/portale/JWT mentre il DB non è disponibile. Il boot compilato non tocca
più `crm.db`; un initializer plaintext esplicito resta solo per lo sviluppo. **G1/G5 non sono ancora
GREEN** perché storage reale, setup/recovery, migrazione e backup cifrato sono i gate successivi.
Prossimo gate tecnico: S1.3 setup owner e recovery UX.

---

### G2. La cecità del rate limiter deve essere risolta per il portale pubblico

**Cosa deve essere vero:** Il portale pubblico rivolto agli atleti deve poter applicare controlli anti-abuso (rate limiting / throttling) su base **per-client-reale**, non per-`localhost`.

**Perché:** È già un blocker noto e aperto, e l'arrivo di atleti reali lo promuove da "robustezza" a "sicurezza". `frpc` inoltra tutto il traffico a `localhost`, quindi FastAPI vede attualmente `127.0.0.1` come indirizzo sorgente di ogni richiesta. Due conseguenze, entrambe inaccettabili con utenti reali su un link pubblico:
1. **Nessun controllo anti-abuso efficace.** Uno `ShareToken` è un UUID4 in un parametro query. Senza rate limiting per-client, non c'è mitigazione contro l'enumerazione automatizzata di token o l'abuso del portale.
2. **Denial of service auto-inflitto.** Qualsiasi limiter ingenuo basato su IP vede solo `127.0.0.1` e finirebbe per throttlare *il trainer legittimo* — facendo DoS al cliente pagante.

**Criteri di accettazione:**
- L'identità reale del client (IP di origine, o un equivalente affidabile) è propagata attraverso il tunnel fino al livello applicativo.
- I controlli anti-abuso sugli endpoint del portale pubblico si basano sull'identità reale del client, mai su `127.0.0.1`.
- L'identità propagata è fidata **solo** sul percorso interno al tunnel e non può essere falsificata da un client che imposta un header direttamente (cioè l'header viene rimosso/sovrascritto al confine di fiducia, non creduto ciecamente).
- Il traffico legittimo del trainer non subisce mai danni collaterali da un controllo destinato a un abusatore pubblico.

**Stato nel codice (verificato 2026-06-16):** ❌ **Gap reale, confermato.** `RateLimiter.check()` usa `request.client.host` (`api/services/rate_limiter.py:30`) → dietro `frpc → localhost` vede sempre `127.0.0.1`. `portal_limiter` (30/min, 120/h) è cablato sugli endpoint pubblici (`public_portal.py:78`) ma è **cieco**. Nessuna gestione di `X-Forwarded-For`/`proxyProtocol`/`forwarded-allow-ips` in tutto `api/`. Soluzione plausibile: header fidato iniettato da `frpc` (proxyProtocol o header custom) + uvicorn `--forwarded-allow-ips=127.0.0.1` + `ProxyHeadersMiddleware`, con strip dell'header in ingresso al confine di fiducia. Scope dell'ordine di giorni.

**Lasciato a Claude Code:** `proxyProtocol` vs. un header custom fidato iniettato da `frps`/`frpc` vs. altro meccanismo; dove si impone il confine di fiducia; l'algoritmo e le soglie del limiter. Il criterio è *controllo basato sul client reale, senza falsificabilità e senza danni collaterali al trainer.*

> **Riferimento incrociato:** è il blocker attivo già tracciato in `TUNNEL_SECURITY_BOUNDARY.md`. Tunnel Guard non deve essere aperto alle route CRM finché questo non è chiuso; questo gate eredita quel vincolo.

---

### G3. TLS valido sul portale pubblico (niente self-signed davanti agli atleti)

**Cosa deve essere vero:** Un atleta che apre il link del portale su telefono o laptop deve raggiungerlo su un TLS che il browser considera fidato, senza alcun avviso sul certificato.

**Perché:** Prima di R0.1.5 il sistema usava un certificato self-signed per la validazione SNI. Era accettabile per la validazione interna, non davanti a un atleta reale. Un avviso di sicurezza del browser al primo contatto (a) distrugge la fiducia in un prodotto B2B2C il cui intero pitch è la privacy, (b) abitua gli utenti a cliccare oltre gli avvisi di sicurezza, che è di per sé un danno, e (c) rende il portale legittimo indistinguibile da un'intercettazione malevola per chiunque presti attenzione.

**Criteri di accettazione:**
- Il portale pubblico presenta un certificato fidato dai browser mobile e desktop mainstream attuali.
- Il provisioning e il rinnovo del certificato sono automatizzati (nessuna scadenza silenziosa che il giorno del rinnovo rompa l'accesso di ogni atleta).
- La proprietà data-blind (P2) è preservata: la gestione del certificato non deve spostare la terminazione TLS sul VPS in modo da consentire al VPS di leggere il traffico di trainer/atleti. **Se l'approccio TLS scelto terminasse sul VPS, è una regressione di P2 e deve essere segnalata a Giacomo prima di procedere, non adottata silenziosamente.**

**Stato nel codice e live (riesaminato 2026-07-28):** ✅ **G3 / R0.1.5 core+live verde.** ADR-011 Addendum I usa **Let's Encrypt HTTP-01 attraverso FRP**: il cert vive su `frpc` (PC trainer), la porta 80 instrada soltanto il webroot challenge e non raggiunge il CRM. Nessuna credenziale DNS viene distribuita. Rinnovo: opportunistico al boot + check ogni 12h, finestra 30 giorni, ultimo cert valido preservato. Apply edge e rollback sono stati esercitati; la chain dev Let's Encrypt è trusted dallo store di sistema e il probe strict ha verificato SAN, `/health` e `/public/` 200, HTTP non-challenge e CRM 404, senza bypass di trust. P2 resta intatta.

**Vincolo operativo:** restano vincolanti gli esiti *fidato dai browser, auto-rinnovante,
P2-preserving*. R0.4 ha riportato questi controlli nelle procedure vive di release/supporto il
2026-07-28; la candidate deve ripeterli sul proprio artefatto.

---

### G4. Ciclo di vita dello ShareToken: scadenza e revoca

**Cosa deve essere vero:** Il token di accesso di un atleta deve essere **revocabile** e deve avere un **ciclo di vita** definito (non deve essere una chiave eterna e incondizionata ai dati di quell'atleta).

**Perché:** Uno `ShareToken` è una credenziale bearer — chi possiede l'URL possiede l'accesso. Due modalità di fallimento se il ciclo di vita non è definito:
- **Nessuna revoca:** quando un atleta smette di lavorare con il trainer, o un link trapela (messaggio inoltrato, dispositivo condiviso, cronologia del browser, header referer), non c'è modo di tagliare l'accesso. Il link è una porta permanente.
- **Nessuna scadenza:** un link trapelato resta valido per sempre, massimizzando la finestra di esposizione.

**Criteri di accettazione:**
- Un trainer può revocare l'accesso di un singolo atleta, e la revoca ha effetto alla richiesta successiva.
- I token hanno un ciclo di vita definito appropriato a una credenziale bearer (scadenza, rotazione, o ri-emissione — scelta di design di Claude Code), così che un link trapelato non conceda accesso indefinito.
- La gestione del token minimizza la fuga incidentale: valutare se il pattern UUID4-in-query-param espone il token via cronologia del browser, log del server, o header `Referer`, e mitigare dove lo fa. (Questo può richiedere o meno di spostare il token fuori dalla query string — è un giudizio implementativo, ma *l'esposizione alla fuga deve essere valutata e registrata*, non assunta innocua.)
- I token revocati o scaduti falliscono in modo chiuso e non rivelano nulla sul fatto che il token sia mai esistito (nessun oracolo che distingua "mai valido" da "scaduto/revocato").

**Stato nel codice (verificato 2026-06-16):** 🟡 **~60% già implementato** — la v1.0 di questo doc sottostimava. Il modello `ShareToken` (`api/models/share_token.py`) ha già: `expires_at` (48h anamnesi / `data_fine`+7gg workout) → **scadenza ✅**; `used_at` (monouso per scope anamnesi) → **single-use parziale ✅**; revoca via eliminazione del record → **revoca ✅**; `scope` estendibile. **Restano da chiudere (il 40%):** (a) **assessment esplicito della fuga UUID-in-query** (cronologia browser, header `Referer` verso terze parti, log) e mitigazione — oggi non valutato/registrato; (b) verifica **fail-closed / no-oracle** sull'endpoint `validate` (token scaduto/revocato/mai-esistito → stesso fallimento generico) — da auditare in `public_portal.py`; (c) una **UX di revoca esplicita** lato trainer (oggi solo delete del record, nessun controllo dedicato). Il lifecycle non va costruito da zero: va completato e auditato.

**Lasciato a Claude Code:** il meccanismo di trasporto del token, la strategia di scadenza, lo storage della revoca. Il criterio è *revocabile + con ciclo di vita + fuga-valutata + fallimento chiuso*.

---

## 3. Tier 2 — FORTEMENTE RACCOMANDATI (soddisfare prima della consegna, oppure documentare un'eccezione con scadenza)

### G5. Strategia di backup / recovery per i dati del trainer

**Cosa deve essere vero:** Deve esistere un modo definito e seguibile dal trainer per recuperare i dati degli atleti se il PC del trainer si guasta, viene perso, o viene resettato.

**Perché:** È l'*altro* taglio della lama del local-first. Senza copia cloud, un singolo disco morto distrugge il 100% dei dati degli atleti di un trainer senza alcun rimedio. La prima volta che capita a un trainer reale, chiude la relazione ed espone Giacomo a una contestazione credibile (il trainer ha affidato i dati al prodotto e li ha persi). Nota la tensione con G1: qualsiasi backup deve essere a sua volta **cifrato**, o reintroduce esattamente l'esposizione in chiaro a riposo che G1 chiude.

**Criteri di accettazione:**
- Esiste un percorso di recovery (export cifrato, o un meccanismo equivalente progettato da Claude Code).
- Qualsiasi artefatto di backup è cifrato allo stesso standard di G1 — nessun dato in chiaro degli atleti lascia mai il database cifrato, neppure verso un file di backup.
- Il percorso è realisticamente seguibile da un trainer non tecnico (la frizione qui è un rischio di prodotto, per il principio fermo di Giacomo di non aggiungere frizione ai trainer clienti).
- Documentato, così che il trainer sappia che esiste e come usarlo.

**Stato nel codice (riverificato 2026-09-05):** 🟠 L'infrastruttura legacy backup/restore
(`api/routers/backup.py`, 7 endpoint WAL-safe) resta disponibile soltanto sul percorso esplicito
`PLAINTEXT_DEVELOPMENT`. S1.2 ha rimosso l'auto-backup CRM dal boot e blocca il router sia in
compiled mode sia davanti a un engine classificato `ENCRYPTED`, impedendo che il vecchio
`sqlite3.backup()` produca una copia plaintext nel nuovo boundary. Non esiste ancora il backup
bundle cifrato né il percorso trainer-facing di recovery/restore: **G5 non è GREEN**. Il contratto
resta nello stesso blocco G1, ADR-013 Addendum I + `SPEC_S1_G1_G5_CIFRATURA_CRM.md`; implementazione
prevista in S1.5 dopo setup/recovery e migrazione.

> **Perché Tier 2 e non Tier 1:** a differenza di G1–G4, un backup mancante non causa di per sé un *breach* (la riservatezza è intatta). Causa una *perdita di disponibilità*. È un grave rischio di prodotto e di fiducia, e una preoccupazione GDPR borderline su integrità e disponibilità (art. 32), ma non espone dati a un attaccante. Se la consegna deve procedere prima che questo sia costruito, richiede un'eccezione esplicita documentata e un'istruzione manuale temporanea al trainer.

---

### G6. Hardening dell'autenticazione ai confini di fiducia

**Cosa deve essere vero:** Entrambe le superfici autenticate — login del trainer (JWT) e portale atleti (ShareToken) — dovrebbero resistere al brute force delle credenziali e all'abuso di sessione.

**Perché:** Una volta che G2 rende possibile il rate limiting basato sul client reale, andrebbe effettivamente applicato ai percorsi che portano autenticazione, non solo agli endpoint generici. Le credenziali del trainer custodiscono l'intero dataset degli atleti; lo ShareToken custodisce la scheda di un singolo atleta. Entrambi meritano resistenza al brute force.

**Criteri di accettazione:**
- L'autenticazione del trainer resiste al guessing automatizzato delle credenziali (lockout/backoff basato sull'identità reale del client da G2).
- La gestione JWT segue le buone pratiche attuali per scadenza e (dove applicabile) invalidazione; verificare che durata del token e comportamento di refresh siano appropriati per un'app desktop che contiene dati sensibili.
- Il portale atleti applica i controlli anti-abuso di G2 specificamente alla sottomissione del token.

**Stato nel codice (verificato 2026-06-16):** 🟡 `auth_limiter` (5/min, 20/h) già applicato a login/register/reset-password — ma **cieco come G2** (per-`localhost`). JWT HS256, expiry 8h (`JWT_EXPIRE_MINUTES`), nessun refresh/invalidazione esplicita (`api/auth/service.py`). **Dipende interamente da G2**: senza identità reale del client, lockout e backoff non sono applicabili. Da rivisitare appena G2 è chiuso.

---

### G7. Audit della superficie del portale pubblico

**Cosa deve essere vero:** Una conferma positiva ed esplicita che **nessun endpoint CRM / autenticato-trainer sia raggiungibile via il percorso pubblico**, e che la superficie pubblica non riveli nulla che non dovrebbe.

**Perché:** La memoria e la revisione precedente indicano che `get_current_trainer()` già protegge tutti i router CRM — bene. Ma "crediamo sia coperto" non è la stessa cosa di "abbiamo verificato, endpoint per endpoint, che il percorso pubblico espone solo il portale atleti". L'unica superficie esposta a internet merita un audit esplicito, non un'assunzione ereditata. È anche il punto dove il principio *il-sistema-è-la-fonte-di-verità* si applica più duramente: confermare contro la tabella reale dei router, non contro la descrizione che ne dà questo documento.

**Criteri di accettazione:**
- Enumerare ogni endpoint raggiungibile attraverso il percorso pubblico del tunnel e confermare che ciascuno sia (a) il portale atleti previsto, oppure (b) correttamente richieda autenticazione trainer e rifiuti l'accesso non autenticato.
- Le risposte di errore sulla superficie pubblica non fanno trapelare informazione di esistenza (token malformato/assente → fallimento generico, nessuna distinzione che aiuti l'enumerazione).
- Il risultato dell'audit è registrato (una breve sezione in `TUNNEL_SECURITY_BOUNDARY.md` o una nota dedicata), così che la prossima consegna erediti una baseline verificata invece di una ri-assunta.

**Stato nel codice (verificato 2026-06-16):** 🟡 **Lo strato edge esiste già.** Il middleware Next (`frontend/src/middleware.ts`) applica il Tunnel Guard: da hostname non-locale, solo `/public`, `/api/public`, `/health`, `/media`, `/_next`, `/favicon.ico` passano; tutto il resto → **404** (non 403, non rivela esistenza). Il tunnel punta alla porta 3000 (Next), che proxya `/api/*` al backend → un client dal tunnel raggiunge il backend solo via `/api/public/*`. **Ma è difesa a uno strato solo** (edge): il pitfall #6 di `CLAUDE.md` avverte esplicitamente che se il middleware regredisce, il CRM è esposto. **G7 resta da fare come audit esplicito a due strati:** (1) enumerare i router e confermare che il backend stesso (`get_current_trainer`) rifiuti, non solo l'edge; (2) verificare che `/_next` via tunnel non serva payload RSC di pagine CRM; (3) registrare la baseline in `TUNNEL_SECURITY_BOUNDARY.md`.

---

### G8. Disciplina di logging (non lasciare che il sistema data-blind crei un log data-leaky)

**Cosa deve essere vero:** I log applicativi sul PC del trainer non devono diventare una copia ombra in chiaro dei dati degli atleti che G1 ha appena finito di cifrare.

**Perché:** È un classico autogol: il database è cifrato, e poi dati sanitari, nomi degli atleti, o token finiscono scritti in chiaro in un file di log che sta lì accanto. I log sono anche utili per la rilevazione di abusi che G2/G6 abilitano, quindi l'obiettivo è *log utili senza payload sensibili.*

**Criteri di accettazione:**
- I log non contengono dati di categoria particolare degli atleti (parametri sanitari/fisici) né ShareToken completi in chiaro.
- I log sufficienti a rilevare e investigare abusi (timestamp, identità reale del client, endpoint, esito) sono conservati.
- Qualsiasi retention dei log rispetta la minimizzazione dei dati — i log non sono un secondo store indefinito di dati personali.

**Stato nel codice (verificato 2026-06-16):** ⏳ Da auditare. Logging bootstrap in `api/logging_config.py` (`data/logs/fitmanager.log`, rotazione). Serve un pass mirato sui punti di log per assicurare zero parametri sanitari/nomi atleti/token completi. Dipende in parte da G2 (l'identità reale del client da loggare arriva da lì).

---

## 4. Tier 3 — GDPR & PROCESSO (deve essere completo prima dell'onboarding del primo atleta; binario parallelo, non tutto codice)

Questi non sono ticket implementativi per Claude Code nello stesso senso del Tier 1–2, ma fanno parte dello stesso gate e sono elencati perché nulla cada tra il binario tecnico e quello legale. Riferimento incrociato a **`docs/business/LEGAL_REGULATORY_REPORT.md`** (v1.3) e coordinamento con i consulenti legali/del lavoro già previsti nel piano. *(Correzione v1.1: il report vive in `docs/business/`, non in `docs/technical/`.)*

### G9. Ruoli fissati per iscritto: il trainer è Titolare, AVGV è Responsabile
Il trainer decide finalità e mezzi del trattamento dei dati dei suoi atleti → **titolare del trattamento**. AVGV fornisce lo strumento e l'infrastruttura di routing → **responsabile del trattamento**. Questa relazione richiede un **accordo sul trattamento (DPA) / nomina a responsabile ex art. 28 GDPR** tra AVGV e il trainer. È distinto e aggiuntivo rispetto agli accordi commerciali/di partnership. Deve essere in essere prima che il trainer tratti dati reali di atleti attraverso il prodotto.

### G10. Informativa rivolta agli atleti (artt. 13–14)
L'atleta deve ricevere l'informativa privacy quando usa il portale per la prima volta: chi è il titolare (il trainer), che AVGV è il responsabile, quali dati sono trattati, la base giuridica, la conservazione, e i suoi diritti. L'architettura data-blind è una *storia forte* da raccontare qui — AVGV non vede mai i dati — e va riflessa accuratamente.

### G11. Procedura di risposta al data breach (artt. 33–34)
Prima che i dati reali siano in produzione, deve esistere una procedura scritta e minima su cosa accade se un breach è sospettato: come il trainer (titolare) notifica al Garante entro 72 ore, gli obblighi di AVGV come responsabile di informare il titolare senza ingiustificato ritardo, e il percorso decisionale per notificare gli atleti interessati. Un runbook di una pagina basta per iniziare; il punto è che esista *prima* di servire, non improvvisato sotto un orologio di 72 ore.

### G12. Registro delle attività di trattamento (art. 30)
Un registro leggero del trattamento che AVGV svolge come responsabile. Il design data-blind lo mantiene breve, il che è di per sé un punto di forza.

---

## 5. La decisione di consegna

Mettendo il gate in termini operativi semplici, così che la risposta a *"quando posso consegnarlo?"* sia meccanica invece che ansiosa:

**Consegna il software al trainer solo quando:** G1, G2, G3, G4 sono soddisfatti (Tier 1, tutti e quattro).

**Lascia che il trainer faccia l'onboarding del primo atleta reale solo quando:** il Tier 1 è soddisfatto **e** ci sono G9, G10, G11 (la relazione titolare/responsabile, l'informativa agli atleti, e il runbook breach).

**Mira a soddisfare prima della consegna, oppure rinvia consapevolmente con un'eccezione documentata e con scadenza:** G5, G6, G7, G8.

Questa sequenza permette al trainer di ricevere ed esplorare il prodotto (Tier 1 fatto) leggermente in anticipo rispetto all'impalcatura legale completa, garantendo al contempo che nessun dato reale di atleta entri finché non esistono i pezzi su titolare/responsabile e notifica breach. Mette in testa le voci a rischio irreversibile (tutto ciò che tocca la riservatezza di dati reali) e concede alle voci di disponibilità/processo una breve pista esplicita.

### 5.1 Sequenza di lavoro tecnica (Claude Code, 2026-06-16)

Ordine per rischio strutturale e dipendenze, non per ordine di elenco:

| Ordine | Traccia | Razionale |
|--------|---------|-----------|
| **1** | **Design G1 + G5** (palo lungo) → ADR-013 | Boot a due fasi + scelta cifratura + backup cifrato. Decisione strutturale da cui dipende il resto. Zero codice finché l'ADR non è accettato. |
| **2** | **G2** (real client IP) | Indipendente da G1, sblocca G6. Già blocker tracciato. |
| **3** | **G4 + G7** | G4: chiudere il 40% mancante. G7: audit a due strati + registrazione. Verifiche mirate, basso rischio. |
| **4** | **G3** (Let's Encrypt HTTP-01 ristretto via FRP) | P2-preserving, zero credenziali DNS sui trainer; rinnovo su PC spegnibile coperto da boot + scheduler. |
| **5** | **G6 + G8** | Dipendono da G2 (identità reale del client). |
| **parallelo** | **Tier 3** (G9–G12) | Binario legale, non blocca il codice, gestito da Giacomo con i consulenti. Serve prima dell'onboarding del primo atleta. |

---

## 6. Principi fermi che questo gate eredita

- **Il sistema e il codebase reale sono la fonte di verità.** Dove la descrizione dell'architettura in questo documento (copertura dei router, gestione dei token, comportamento del tunnel) differisce da ciò che Claude Code trova nel codice, il codice vince, e questo documento viene corretto per allinearsi — immediatamente, in loco, secondo la convenzione stabilita. *(Applicato nella v1.1: vedi le righe "Stato nel codice" per gate.)*
- **Prescrittivo su *cosa deve essere vero*, libero su *come*.** Ogni criterio di accettazione qui sopra è una proprietà da raggiungere. Nessuna libreria, algoritmo o struttura è imposta. Claude Code è l'architetto finale nel codebase.
- **Non regredire P2 (data-blindness).** È la fondazione dell'assetto GDPR e del vantaggio difendibile del prodotto. Qualsiasi modifica che sposterebbe la terminazione TLS o il traffico leggibile sul VPS è una regressione da segnalare, non da assorbire.
- **Niente frizione per i trainer clienti.** Dove un controllo può essere reso invisibile o a basso sforzo per il trainer (e soprattutto per l'atleta) senza indebolire la proprietà, dovrebbe esserlo.
- **Bridge rule:** qualsiasi implementazione non banale che Claude Code produce contro questi criteri diventa una learning capture da digerire in chat, così che la comprensione macro resti allineata alla ground truth.
