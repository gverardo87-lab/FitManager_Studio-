# Tunnel Security Boundary — Acceptance Criteria (Strada B)

**Stato:** binding (`docs/technical/`)
**Contesto:** Apertura del CRM all'accesso del trainer da qualunque rete, via tunnel FRP.
**Versione:** 2.0
**Convenzione errori:** in coerenza con il **Bouncer Pattern** del progetto (CLAUDE.md, regola #3: "Non trovato = 404, mai 403"), tutti i rifiuti di autorizzazione sono **404**. Un endpoint CRM colpito da chi non e' un trainer si comporta come se non esistesse.

**Percorso d'ingresso unico (FRP):** il progetto e' in transizione da Tailscale Funnel a FRP. Le due strategie NON devono coesistere a regime. FRP e' l'unico percorso target. Vedi sez. 7.

**Premessa critica:** fino all'introduzione di Strada B il tunnel serviva esclusivamente gli atleti (`/api/public/*`). Strada B espone il CRM su Internet. Il modello di minaccia passa da "rete locale fidata" a "esposto su Internet".

Questo documento specifica *cosa deve essere vero*, non *come implementarlo*.

> **Nota di revisione (v2.0 — 2026-06-08):** revisione completa basata su audit del codice sorgente (Claude Code, non Claude Chat). Principali correzioni rispetto alla v1.1:
>
> - **Sezione 0 (principio fondante):** corretto. La v1.1 affermava "un token trainer e un token atleta non sono distinguibili crittograficamente". Falso: il portale atleti usa `ShareToken` (UUID4 in query param), NON JWT. I due formati sono incompatibili — un UUID4 non puo' mai essere decodificato come JWT. Il confine trainer-vs-atleta e' gia' chiuso per costruzione di formato.
> - **AC-1 (role JWT):** riclassificato da BLOCCANTE a raccomandato (defense in depth). Il rischio "token atleta confuso con trainer" non esiste con l'architettura attuale.
> - **AC-2 (confine FastAPI):** `get_current_trainer()` e' gia' il confine su tutti gli endpoint CRM. Il gap residuo e' il claim `role`, non la dependency.
> - **Nuovo BLOCCANTE — rate limiter cieco via tunnel:** `127.0.0.1` di frpc rende `auth_limiter` inefficace. Elevato a bloccante assoluto (sez. 3).
> - **Nuovo BLOCCANTE — apertura selettiva tunnel guard:** `/auth/register` NON deve essere esposto via tunnel (sez. 4).
> - **Sezione 6 ripristinata:** scenari operativi (contenuto orfano nella v1.1).
> - La sez. P2 (data-blind) e la correzione v1.1 restano invariate.

---

## 0. Principio fondante

> **L'autorizzazione trainer-vs-anonimo e' una proprieta' del meccanismo di autenticazione verificato lato FastAPI. Non e' una proprieta' del path, dell'header `Host`, della rete di origine, ne' di alcun layer Next.js.**

Tutto cio' che precede FastAPI (middleware Next.js, Tunnel Guard, routing SNI) e' **difesa in profondita'**.

**Due assi di protezione nel codebase:**

- **Bouncer Pattern -> asse trainer-vs-trainer.** Ogni endpoint filtra per `trainer_id`. Risponde a: *"sei il proprietario di questi dati?"*
- **`get_current_trainer()` -> asse autenticato-vs-anonimo.** La dependency FastAPI (`api/dependencies.py:29-60`) verifica JWT firmato, cerca trainer in DB, controlla `is_active`. Risponde a: *"hai un JWT valido di un trainer attivo?"*

**Stato del confine oggi (verificato nel codice):**

Il JWT trainer (`api/auth/service.py:28-41`) contiene `{sub: trainer_id, email, exp}`. Il portale atleti usa un meccanismo **completamente diverso**: `ShareToken` (UUID4 in query parameter `?token=`, validato contro DB in `api/routers/public_portal.py:83-112`). I due sistemi sono **incompatibili per formato**: un UUID4 non puo' essere decodificato come JWT HS256, e un JWT non corrisponde a nessun `ShareToken.token` nel DB.

**Conseguenza:** il rischio "un atleta presenta un token che supera il check trainer" **non esiste** nell'architettura attuale. `get_current_trainer()` richiede un JWT HS256 firmato con `JWT_SECRET` -> il portale atleti non ne emette -> confine trainer-vs-atleta chiuso per costruzione di formato.

Il JWT **non** contiene un claim `role`. Questo e' un gap di defense-in-depth (sez. 1), non un gap di sicurezza attivo.

**Rapporto con la v1.1.** La v1.1 affermava: *"un token trainer e un token atleta non sono distinguibili crittograficamente"*. Questa affermazione era **errata** perche' assume che entrambi siano JWT. Il portale atleti non emette JWT: emette UUID4 opachi validati per lookup diretto. I due formati sono distinguibili alla radice (struttura, encoding, meccanismo di verifica).

---

## 1. Role nel JWT (AC-1) — raccomandato (defense in depth)

**Riclassificazione v2.0:** da BLOCCANTE a raccomandato. Motivazione: il portale atleti usa `ShareToken` (UUID4), non JWT. Il rischio "token atleta spacciato per trainer" non esiste con l'architettura attuale.

**Cosa deve essere vero:**

- Il JWT emesso da `create_access_token` DOVREBBE contenere un claim `role: "trainer"`.
- `get_current_trainer()` DOVREBBE verificare `role == "trainer"` dopo la validazione firma.
- Token senza `role` (emessi prima dell'aggiornamento) trattati come non autorizzati (fail-closed -> forza re-login pulito).

**Perche' farlo nonostante il rischio sia teorico:**

- **Future-proofing:** se in futuro il portale emettesse JWT per gli atleti (es. sessioni persistenti), il claim `role` impedirebbe confusione.
- **Costo zero:** aggiungere un campo al payload JWT e' una modifica di 1 riga.
- **Defense-in-depth:** non affidarsi a una sola proprieta' (formato token) per la separazione dei ruoli.

**Criterio di accettazione:**
Decodificando un token trainer, `role == "trainer"` e' presente. Token senza `role` -> 401.

---

## 2. Confine FastAPI — gia' implementato (AC-2)

**Stato attuale (verificato in `api/dependencies.py:29-60`):**

`get_current_trainer()` e' applicato a **tutti** gli endpoint CRM via `Depends()`. Fa gia':
1. Estrae JWT dall'header `Authorization: Bearer <token>`
2. Verifica firma HS256 con `JWT_SECRET`
3. Ottiene `trainer_id` dal claim `sub`
4. Lookup trainer nel DB + check `is_active`
5. Rifiuta con 401 se qualsiasi step fallisce

**Copertura completa:** tutti i router CRM usano questa dependency — clients, contracts, rates, movements, recurring_expenses, dashboard, agenda, todos, measurements, goals, workouts, communications, backup, workspace, training_science, training_intelligence, workout_diff.

**Gap residuo:** il check `role == "trainer"` descritto in AC-1. Non e' un buco attivo (nessun JWT "non-trainer" esiste nel sistema), ma va colmato per coerenza.

**Criterio di accettazione (test obbligatori prima del POC):**
- Richiesta CRM senza token -> 401.
- Richiesta CRM con JWT artigianale senza `role` o con `role != "trainer"` -> 401/404.
- Richiesta CRM con JWT `role: "trainer"` valido -> 200.
- Richiesta CRM con JWT manomesso nel payload -> 401 (firma fallita).
- Tutti e 4 i test via dominio pubblico del tunnel, non solo da localhost.

> Con `get_current_trainer()` gia' in vigore, il CRM e' sicuro su Internet anche **senza** AC-1. AC-1 aggiunge un layer di defense-in-depth.

---

## 3. Rate limiter IP reale — BLOCCANTE

**Problema:** `auth_limiter` (`api/services/rate_limiter.py`) e' IP-based: 5 req/min, 20 req/ora per IP. Via tunnel, frpc inoltra le richieste a `localhost:3000` -> Next.js proxya a `localhost:8000` (backend). L'IP visto da FastAPI e' **`127.0.0.1`** per TUTTI gli utenti che passano dal tunnel.

**Conseguenza:** il rate limiter conta tutti i tentativi di login via tunnel come una **sola sorgente**. Un attaccante e il trainer legittimo condividono lo stesso bucket. Un attaccante che martella `/auth/login` blocca anche il trainer dopo 5 tentativi/min. Il rate limiter e' **cieco**.

**Cosa deve essere vero:**

- Il rate limiter DEVE distinguere client IP diversi dietro il tunnel.
- Il layer di ingresso (frpc o frps) DEVE propagare l'IP reale del client via header (`X-Forwarded-For`, `X-Real-IP`, o equivalente).
- Il rate limiter DEVE estrarre l'IP reale dall'header propagato.
- L'header NON deve essere fidato ciecamente: solo la prima entry inserita dal layer di fiducia (frpc/frps) e' affidabile. Entry aggiunte a monte dal client sono spoofabili.
- **Fallback fail-closed:** se l'IP reale non e' disponibile, il rate limiter DEVE restare attivo su `127.0.0.1`. Questo significa che un attaccante potrebbe bloccare anche il trainer (DoS locale), ma e' preferibile a zero protezione.

**Criterio di accettazione:**
Due client con IP diversi che colpiscono `/auth/login` via tunnel -> conteggiati come sorgenti separate. Un client che supera 5 tentativi/min -> 429, l'altro client continua a funzionare.

**Nota implementativa (non vincolante):** FRP supporta `proxyProtocol` e header forwarding nella configurazione `https2http`. Verificare quale meccanismo propaga l'IP reale nel setup attuale. L'alternativa e' estrarlo lato frps e iniettarlo come header custom nel tunnel.

---

## 4. Apertura selettiva tunnel guard — BLOCCANTE (vincolo di sequenza)

**Cosa deve essere vero:**

`TUNNEL_ALLOWED_PREFIXES` in `middleware.ts` viene esteso per consentire l'accesso del trainer al CRM via tunnel. L'apertura e' **selettiva**, non totale.

**Route da aprire:**
- `/login` — pagina login
- `/api/auth/login` — endpoint autenticazione
- `/dashboard`, `/clienti/*`, `/contratti/*`, `/cassa/*`, `/esercizi/*`, `/schede/*`, `/agenda/*`, `/comunicazioni/*`, `/rinnovi-incassi/*`, `/oggi/*`, `/impostazioni/*`, `/guida/*` — pagine CRM
- `/api/*` (la maggior parte) — endpoint CRM (protetti da `get_current_trainer()`)
- `/_next/*`, `/favicon.ico` — asset statici (gia' aperti)

**Route da mantenere BLOCCATE dal tunnel:**
- `/register`, `/api/auth/register` — registrazione trainer solo da LAN (primo setup)
- `/setup`, `/api/auth/setup-status` — wizard primo avvio, solo LAN
- `/licenza` — pagina licenza, solo LAN

**Host header:** `isTunnelRequest()` NON deve basare decisioni di sicurezza sull'header `Host` (spoofabile — un `curl -H "Host: localhost"` potrebbe bypassare il guard). Con `get_current_trainer()` su tutti gli endpoint CRM, la distinzione LAN-vs-tunnel **non ha rilevanza di sicurezza per i dati**. Il guard resta utile per:
- Bloccare `/register` e `/setup` dal tunnel (policy, non sicurezza dati)
- Ridurre la superficie esposta (meno HTML visibile = meno info su struttura app)

**Criterio di accettazione:**
- Dal tunnel, senza token: `/login` -> 200 (pagina login). `/dashboard` -> redirect `/login`. `/api/clients` -> 401.
- Dal tunnel, con token trainer: `/dashboard` -> 200. `/api/clients` -> 200.
- Dal tunnel: `/register` -> 404. `/setup` -> 404.
- `curl -H "Host: localhost"` via dominio tunnel + senza token -> 401/404 su endpoint CRM (mai 200).

---

## 5. P2 — Data-blind (proprieta' GDPR) — DIMOSTRATO per il routing; test probatorio raccomandato

*(Invariato rispetto a v1.1 — la correzione del 2026-06-07 e' confermata.)*

**Correzione rispetto alla v1.0.** La v1.0 affermava che `type=https` + `https2http` rompesse il data-blind. Il test e2e del 2026-06-07 (BUILD_LOG, Fase 1 Step 5) ha dimostrato il contrario. Vale il principio: *il sistema e' la source of truth, non l'AI ne' il documento.*

**Cosa e' stato dimostrato (test e2e Step 5):**
`curl` dal VPS -> `frps:443` (SNI routing) -> `frpc` sul PC trainer (TLS termination) -> `localhost:3000` -> risposta. Il VPS ha instradato leggendo **solo** il campo SNI (nome dominio in chiaro nell'handshake), inoltrando il payload cifrato senza terminarlo. Con `vhostHTTPSPort = 443` + `https2http`, la terminazione TLS avviene su `frpc` lato PC, **non** sul VPS.

**Proprieta' che reggono per costruzione:**
- TLS termina su frpc (PC trainer), non sul VPS.
- VPS instrada leggendo esclusivamente l'SNI.
- VPS non possiede la chiave privata del trainer (cert generato e conservato lato PC).

**Test probatorio raccomandato (dossier GDPR, non bloccante):**
Cattura `tcpdump` sulla porta del tunnel mentre un client e' connesso. Deve risultare:
- SNI visibile in chiaro nell'handshake (atteso, e' routing).
- Payload applicativo **opaco/cifrato** dopo l'handshake.
- Nessun certificato trainer presente o richiesto sul VPS.

> **Distinzione per il legale:** "il VPS instrada senza decifrare" -> **dimostrato** (Step 5). "Un osservatore sul VPS vede solo byte opachi" -> **vero per costruzione, da mostrare** col tcpdump. La seconda e' la formulazione che sostiene la tesi "AVGV non tratta i dati".

---

## 6. Conseguenze operative del passaggio locale -> Internet

Una volta che il CRM e' raggiungibile da Internet, protezioni finora implicite vanno rese esplicite:

- **Rate limiting via tunnel (sez. 3).** Problema critico: IP tutti `127.0.0.1`. Bloccante, risolto da sez. 3.
- **Brute force login.** Constant-time compare c'e' gia' (anti-enumeration). Valutare lockout progressivo o captcha dopo N fallimenti, dato che la superficie e' pubblica.
- **CORS.** Il regex CORS ammette `localhost`/`192.168`/`100.x`. NON allargare a `*`. Se l'app e' servita dallo stesso dominio del tunnel (same origin), CORS non e' il meccanismo rilevante.
- **Registration exposure.** `/auth/register` DEVE restare bloccato dal tunnel (sez. 4). Registrazione = solo primo setup da LAN.
- **Disponibilita' dell'istanza.** L'accesso da tablet richiede il PC del trainer acceso. Vincolo di prodotto noto, da comunicare ai trainer del POC.

---

## 7. Sequenziamento — e dismissione Tailscale

**Vincolo di ordine (non negoziabile):**

> **Rate limiter IP reale (sez. 3) DEVE essere implementato PRIMA o INSIEME all'apertura selettiva (sez. 4).** Aprire il tunnel senza rate limiter funzionante = brute force illimitato su login.

Ordine consigliato:
1. Rate limiter IP reale (sez. 3) — prerequisito
2. `role: "trainer"` nel JWT (sez. 1) — facoltativo ma consigliato prima dell'apertura
3. Apertura selettiva tunnel guard (sez. 4) — l'atto di apertura
4. Test e2e attraverso dominio pubblico — i 4 test di sez. 2 + test rate limiter di sez. 3

**Dismissione Tailscale:**
- FRP e' l'unico percorso target. A transizione completata, Tailscale va **rimosso** (non lasciato dormiente).
- Finche' Tailscale e' attivo, eredita **tutti** i criteri di questo documento (entrambi terminano su Next.js:3000).
- `get_current_trainer()`, vivendo in FastAPI a valle di Next.js, protegge entrambi i percorsi automaticamente — ulteriore argomento per cui il confine sta nel JWT lato FastAPI e non nel Tunnel Guard.
- Acceptance: a transizione completata, una richiesta verso il vecchio endpoint Tailscale non deve raggiungere il CRM.

---

## 8. Scenari operativi

- **Trainer cambia PC:** rigenerare `license.key` col nuovo `machine_id` (hardware fingerprint). L'`instance_id` **resta invariato** -> l'URL del tablet non cambia.
- **Trainer cambia macchina ma vuole stesso URL:** garantito (instance_id disaccoppiato da machine_id).
- **Onboarding nuovo trainer:** genera licenza con `instance_id` -> config frpc automatica. **Zero interventi su Cloudflare** (wildcard `*.fitmanagerstudio.com` copre tutti). Nessuna registrazione DNS manuale per-trainer.

---

## 9. Riepilogo gravita' (ordine di intervento)

1. **Rate limiter IP reale (sez. 3).** Senza questo, aprire il tunnel espone login a brute force illimitato. `auth_limiter` vede tutto come `127.0.0.1`. **Bloccante assoluto per Strada B.**
2. **Apertura selettiva tunnel guard (sez. 4).** `/auth/register` NON deve essere esposto. Apertura mirata, non totale. **Bloccante per Strada B.**
3. **Sequenziamento (sez. 7).** Rate limiter prima dell'apertura. Vincolo di ordine a costo zero.
4. **AC-1 — role nel JWT (sez. 1).** Defense in depth. Il gap e' teorico (ShareToken != JWT), ma il costo e' zero e il beneficio e' future-proofing. Raccomandato prima dell'apertura.
5. **Host header (sez. 4).** Eliminare dipendenza di sicurezza dall'header `Host`. Mitigato da `get_current_trainer()`, ma il guard non deve dare falsa sicurezza.
6. **Operative (sez. 6).** Brute force lockout, registration blocking — necessari prima del POC.
7. **P2 test probatorio (sez. 5).** Cattura tcpdump per dossier GDPR — completezza, non blocco.

---

## Note di confine (cosa questo documento NON copre)

- Non specifica la struttura esatta dei claim JWT oltre `role` — la lascia all'implementazione, purche' firmati.
- Non ridiscute il routing SNI (validato, sez. 5). Fase 2 / `cert_manager.py` sostituisce solo il certificato (self-signed -> Let's Encrypt), senza cambiamenti architetturali. **Vincolo Fase 2:** ogni `frpc` mantiene il cert del *proprio* `instance_id`; nessun wildcard cert condiviso sul VPS (rimetterebbe una chiave privata sul VPS e contraddirebbe il data-blind).
- Non sostituisce la verifica con un consulente legale sulla tesi GDPR; fornisce la condizione tecnica necessaria perche' quella tesi sia difendibile.
