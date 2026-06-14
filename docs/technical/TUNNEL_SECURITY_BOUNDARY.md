# Tunnel Security Boundary — Confine di sicurezza & Piano "Strada B"

**Stato:** binding (`docs/technical/`) · **Versione:** 3.0 (consolidata)
**Contesto:** Apertura del CRM all'accesso del trainer da qualunque rete, via tunnel FRP.
**Implementazione:** ⬜ **APPROVATA, NON ANCORA IMPLEMENTATA** (verificato nel codice 2026-06-14 — vedi §0bis).
**Documento padre:** `TUNNEL_ARCHITECTURE.md` (design + build + operations del sottosistema tunnel).

**Convenzione errori:** in coerenza con il **Bouncer Pattern** (CLAUDE.md regola #3: "Non trovato = 404, mai 403"),
tutti i rifiuti di autorizzazione sono **404**. Un endpoint CRM colpito da chi non è un trainer si comporta come
se non esistesse.

**Percorso d'ingresso unico (FRP):** il progetto è in transizione da Tailscale Funnel a FRP. Le due strategie
NON devono coesistere a regime. FRP è l'unico percorso target (vedi §7).

**Premessa critica:** finora il tunnel serve esclusivamente gli atleti (`/public/*`). Strada B esporrà il CRM
su Internet: il modello di minaccia passa da "rete locale fidata" a "esposto su Internet".

Questo documento specifica **cosa deve essere vero** (§0–§7, acceptance criteria) e **come implementarlo**
(§8–§11, piano operativo Strada B, ex `STRADA_B_IMPLEMENTATION_PLAN.md`).

> **Nota di revisione (v2.0 — 2026-06-08):** revisione basata su audit del codice sorgente. Correzioni vs v1.1:
> - **§0:** corretto. La v1.1 affermava "token trainer e atleta non distinguibili crittograficamente". Falso: il portale atleti usa `ShareToken` (UUID4 in query param), NON JWT. Confine trainer-vs-atleta già chiuso per costruzione di formato.
> - **AC-1 (role JWT):** da BLOCCANTE a raccomandato (defense in depth).
> - **AC-2 (confine FastAPI):** `get_current_trainer()` è già il confine su tutti gli endpoint CRM.
> - **Nuovi BLOCCANTI:** rate limiter cieco via tunnel (§3), apertura selettiva tunnel guard (§4).
>
> **Nota di consolidamento (v3.0 — 2026-06-14):** assorbito `STRADA_B_IMPLEMENTATION_PLAN.md` (→ §8–§11).
> Aggiunto §0bis con lo stato reale dell'implementazione verificato nel codice.

---

## 0. Principio fondante

> **L'autorizzazione trainer-vs-anonimo è una proprietà del meccanismo di autenticazione verificato lato
> FastAPI. Non è una proprietà del path, dell'header `Host`, della rete di origine, né di alcun layer Next.js.**

Tutto ciò che precede FastAPI (middleware Next.js, Tunnel Guard, routing SNI) è **difesa in profondità**.

**Due assi di protezione nel codebase:**
- **Bouncer Pattern → asse trainer-vs-trainer.** Ogni endpoint filtra per `trainer_id`. *"Sei il proprietario di questi dati?"*
- **`get_current_trainer()` → asse autenticato-vs-anonimo.** La dependency FastAPI (`api/dependencies.py`) verifica JWT firmato, cerca il trainer in DB, controlla `is_active`. *"Hai un JWT valido di un trainer attivo?"*

**Stato del confine (verificato nel codice):** il JWT trainer (`api/auth/service.py`) contiene `{sub, email, exp}`.
Il portale atleti usa `ShareToken` (UUID4 in query `?token=`, validato contro DB in `api/routers/public_portal.py`).
I due sistemi sono **incompatibili per formato**: un UUID4 non è decodificabile come JWT, e un JWT non corrisponde
a nessun `ShareToken` nel DB.

**Conseguenza:** il rischio "un atleta presenta un token che supera il check trainer" **non esiste**
nell'architettura attuale. Confine trainer-vs-atleta chiuso per costruzione di formato. Il JWT **non** contiene
ancora un claim `role`: è un gap di defense-in-depth (§1), non un buco di sicurezza attivo.

---

## 0bis. Stato dell'implementazione (verificato 2026-06-14)

Audit del codice sorgente. **Strada B è progettata e approvata, ma NON ancora implementata.**

| Elemento | Atteso da Strada B | Stato nel codice |
|----------|--------------------|------------------|
| Claim `role: "trainer"` nel JWT | `create_access_token` lo aggiunge; `get_current_trainer` lo verifica | ⬜ **Assente** |
| `LoginLockout` per-account | classe in `rate_limiter.py` + check in `/auth/login` | ⬜ **Assente** |
| Apertura selettiva tunnel guard | `middleware.ts` passa da whitelist a blacklist | ⬜ **Non fatto** — ancora `TUNNEL_ALLOWED_PREFIXES = ["/public", "/api/public", "/health", "/media", "/_next", "/favicon.ico"]` (whitelist) |
| Rate limiter IP reale via tunnel | propagazione IP dietro frpc | ⬜ **Non risolto** (compensato da per-account lockout, §9) |

**Conseguenza operativa:** allo stato attuale il **CRM NON è accessibile dal tunnel** — solo `/public/*` lo è.
Il confine descritto qui sotto è il *target* da raggiungere prima di aprire il CRM su Internet. Finché Strada B
non è implementata, l'esposizione del CRM resta chiusa per costruzione del middleware.

---

## 1. Role nel JWT (AC-1) — raccomandato (defense in depth)

**Cosa deve essere vero:**
- Il JWT emesso da `create_access_token` DOVREBBE contenere `role: "trainer"`.
- `get_current_trainer()` DOVREBBE verificare `role == "trainer"` dopo la validazione firma.
- Token senza `role` trattati come non autorizzati (fail-closed → forza re-login pulito).

**Perché farlo nonostante il rischio sia teorico:** future-proofing (se un domani il portale emettesse JWT per
gli atleti), costo zero (1 riga nel payload), defense-in-depth (non affidarsi a una sola proprietà — il formato
token — per separare i ruoli).

**Criterio di accettazione:** decodificando un token trainer, `role == "trainer"` è presente. Token senza `role` → 401.

---

## 2. Confine FastAPI — già implementato (AC-2)

**Stato attuale (`api/dependencies.py`):** `get_current_trainer()` è applicato a **tutti** gli endpoint CRM via
`Depends()`. Fa già: (1) estrae JWT da `Authorization: Bearer`, (2) verifica firma HS256 con `JWT_SECRET`,
(3) ottiene `trainer_id` da `sub`, (4) lookup trainer + check `is_active`, (5) 401 se qualsiasi step fallisce.

**Copertura completa:** clients, contracts, rates, movements, recurring_expenses, dashboard, agenda, todos,
measurements, goals, workouts, communications, backup, workspace, training_science, training_intelligence, workout_diff.

**Gap residuo:** il check `role == "trainer"` (§1). Non è un buco attivo, va colmato per coerenza.

**Criterio di accettazione (test obbligatori prima del POC):**
- Richiesta CRM senza token → 401.
- JWT artigianale senza `role` o `role != "trainer"` → 401/404.
- JWT `role: "trainer"` valido → 200.
- JWT manomesso nel payload → 401 (firma fallita).
- Tutti e 4 via dominio pubblico del tunnel, non solo da localhost.

> Con `get_current_trainer()` già in vigore, il CRM è sicuro su Internet anche **senza** AC-1. AC-1 aggiunge un layer.

---

## 3. Rate limiter IP reale — BLOCCANTE

**Problema:** `auth_limiter` (`api/services/rate_limiter.py`) è IP-based (5/min, 20/h per IP). Via tunnel, frpc
inoltra a `localhost:3000` → l'IP visto da FastAPI è **`127.0.0.1`** per TUTTI gli utenti del tunnel.

**Conseguenza:** il rate limiter conta tutti i tentativi come **una sola sorgente**. Attaccante e trainer
condividono lo stesso bucket → un attaccante che martella `/auth/login` blocca anche il trainer. Il limiter è **cieco**.

**Cosa deve essere vero:** il rate limiter DEVE distinguere client IP diversi dietro il tunnel. Il layer di
ingresso (frpc/frps) DEVE propagare l'IP reale via header; il limiter DEVE estrarlo. L'header NON va fidato
ciecamente (solo la prima entry inserita dal layer di fiducia è affidabile). **Fallback fail-closed:** se l'IP
reale non è disponibile, il limiter resta attivo su `127.0.0.1` (DoS locale possibile, ma preferibile a zero protezione).

> **Orientamento implementativo (da confermare in fase di sviluppo — vedi §9):** in SNI passthrough frps
> **non può** iniettare `X-Forwarded-For` (pipe TCP puro, non tocca il layer HTTP). L'opzione candidata è il
> **per-account lockout** (§8 Step 1), indipendente dall'IP, che soddisfa l'intento di sez. 3 senza richiedere
> la propagazione IP. La scelta finale (lockout per-account vs Proxy Protocol v2) sarà valutata al momento
> dell'implementazione di Strada B.

**Criterio di accettazione:** un client che supera la soglia di tentativi → bloccato; il trainer legittimo
mantiene un percorso d'accesso (LAN, soglie più permissive).

---

## 4. Apertura selettiva tunnel guard — BLOCCANTE (vincolo di sequenza)

**Cosa deve essere vero:** l'apertura del CRM al tunnel è **selettiva**, non totale.

**Route da aprire:** `/login`, `/api/auth/login`; pagine CRM (`/dashboard`, `/clienti/*`, `/contratti/*`,
`/cassa/*`, `/esercizi/*`, `/schede/*`, `/agenda/*`, `/comunicazioni/*`, `/rinnovi-incassi/*`, `/oggi/*`,
`/impostazioni/*`, `/guida/*`); `/api/*` (protetti da `get_current_trainer()`); asset statici (`/_next/*`, `/favicon.ico`).

**Route da mantenere BLOCCATE dal tunnel:** `/register`, `/api/auth/register` (registrazione solo LAN);
`/setup`, `/api/auth/setup-status` (wizard primo avvio); `/licenza` (solo LAN).

**Host header:** `isTunnelRequest()` NON deve basare decisioni di sicurezza sull'header `Host` (spoofabile).
Con `get_current_trainer()` su tutti gli endpoint CRM, la distinzione LAN-vs-tunnel **non ha rilevanza di
sicurezza per i dati**. Il guard resta utile per bloccare `/register`/`/setup` (policy) e ridurre la superficie esposta.

**Criterio di accettazione:**
- Dal tunnel, senza token: `/login` → 200; `/dashboard` → redirect `/login`; `/api/clients` → 401.
- Dal tunnel, con token trainer: `/dashboard` → 200; `/api/clients` → 200.
- Dal tunnel: `/register` → 404; `/setup` → 404.
- `curl -H "Host: localhost"` via dominio tunnel + senza token → 401/404 su endpoint CRM (mai 200).

---

## 5. P2 — Data-blind (proprietà GDPR) — DIMOSTRATO per il routing

*(Invariato — correzione del 2026-06-07 confermata.)*

**Cosa è stato dimostrato (test e2e Fase 1 Step 5):** `curl` dal VPS → `frps:443` (SNI routing) → `frpc` sul PC
trainer (TLS termination) → `localhost:3000` → risposta. Il VPS ha instradato leggendo **solo** l'SNI (in chiaro
nell'handshake), inoltrando il payload cifrato senza terminarlo. Con `vhostHTTPSPort = 443` + `https2http`, la
terminazione TLS avviene su `frpc` lato PC, **non** sul VPS.

**Proprietà che reggono per costruzione:** TLS termina su frpc (PC trainer), non sul VPS; il VPS instrada solo
sull'SNI; il VPS non possiede la chiave privata del trainer.

**Test probatorio raccomandato (dossier GDPR, non bloccante):** cattura `tcpdump` sulla porta del tunnel con un
client connesso → SNI in chiaro (atteso, è routing), payload **opaco/cifrato**, nessun certificato trainer sul VPS.

> **Distinzione per il legale:** "il VPS instrada senza decifrare" → **dimostrato** (Step 5). "Un osservatore sul
> VPS vede solo byte opachi" → vero per costruzione, da mostrare col tcpdump. La seconda sostiene la tesi "AVGV non tratta i dati".

---

## 6. Conseguenze operative del passaggio locale → Internet

- **Rate limiting via tunnel (§3).** Critico: IP tutti `127.0.0.1`. Risolto da per-account lockout (§8/§9).
- **Brute force login.** Constant-time compare già presente. Aggiungere lockout progressivo (§8 Step 1).
- **CORS.** Il regex ammette `localhost`/`192.168`/`100.x`. NON allargare a `*`. Same-origin → CORS non rilevante.
- **Registration exposure.** `/auth/register` DEVE restare bloccato dal tunnel (§4). Solo primo setup da LAN.
- **Disponibilità.** L'accesso da tablet richiede il PC acceso. Vincolo di prodotto, da comunicare ai trainer POC.

---

## 7. Sequenziamento — e dismissione Tailscale

**Vincolo di ordine (non negoziabile):**
> **Il lockout/rate limiter (§3, §8 Step 1) DEVE essere implementato PRIMA o INSIEME all'apertura selettiva
> (§4, §8 Step 3).** Aprire il tunnel senza protezione brute force = login martellabile illimitatamente.

Ordine consigliato: (1) lockout login → (2) `role` JWT (consigliato) → (3) apertura selettiva → (4) test e2e.

**Dismissione Tailscale:**
- FRP è l'unico percorso target. A transizione completata, Tailscale va **rimosso** (non lasciato dormiente).
- Finché Tailscale è attivo, eredita **tutti** i criteri di questo documento (entrambi terminano su Next.js:3000).
- `get_current_trainer()`, vivendo in FastAPI a valle di Next.js, protegge entrambi i percorsi — ulteriore prova che il confine sta nel JWT, non nel Tunnel Guard.
- Acceptance: a transizione completata, una richiesta al vecchio endpoint Tailscale non deve raggiungere il CRM.
- Setup legacy archiviato: `docs/archive/TAILSCALE_FUNNEL_SETUP.md`.

---

## 8. Piano di implementazione Strada B (ex STRADA_B_IMPLEMENTATION_PLAN)

**Obiettivo:** permettere al trainer di accedere al CRM da qualunque rete via tunnel FRP, mantenendo: CRM
protetto da JWT, registrazione/setup bloccati dal tunnel, brute force mitigato, P2 data-blind invariato.

> *Piano proposto, non ancora eseguito (vedi §0bis). In particolare la mitigazione brute-force dello Step 1
> (per-account lockout) è l'orientamento corrente, da confermare al momento dell'implementazione (§9).*

### Step 1 — Lockout progressivo su login (~1h) — BLOCCANTE
**File:** `api/services/rate_limiter.py` + `api/auth/router.py`.
- Classe `LoginLockout`: dizionario in-memory `{email: (fail_count, locked_until)}`.
- 5 fallimenti consecutivi → lockout 5 min; 10 → 30 min. Login riuscito → reset.
- Da LAN (IP locale): soglie raddoppiate (il trainer è fisicamente al PC).
- Check lockout **PRIMA** della verifica password (evita timing attack).
- Il rate limiter IP esistente resta come layer aggiuntivo. Lockout in-memory (reset al restart — ok per single-tenant). Ogni lockout loggato (`logger.warning`).

**AC:** 5 login falliti per `test@test.com` → 6° = 429 "Troppi tentativi"; login riuscito dopo scadenza → reset.

### Step 2 — Role claim nel JWT (~30min) — raccomandato
**File:** `api/auth/service.py` + `api/dependencies.py`.
- `create_access_token()`: aggiungere `"role": "trainer"` al payload.
- `get_current_trainer()`: dopo `decode_access_token()`, verificare `role == "trainer"`; assente/diverso → 401.
- **Effetto collaterale:** tutti i trainer loggati forzati al re-login (token vecchio = 401). Accettabile (token 8h, re-login trasparente).
- Fail-closed: token senza `role` → 401. Zero impatto sul portale (`ShareToken` UUID4, meccanismo separato).

**AC:** `jwt.decode(token)` contiene `role: "trainer"`; token senza `role` → 401; portale pubblico continua a funzionare.

### Step 3 — Apertura selettiva tunnel guard (~1h) — l'atto di apertura
**File:** `frontend/src/middleware.ts`.
- Invertire la logica: da **whitelist** (`TUNNEL_ALLOWED_PREFIXES`, solo `/public/*`) a **blacklist** (`TUNNEL_BLOCKED_PREFIXES`).
  ```
  TUNNEL_BLOCKED_PREFIXES = [ /register, /setup, /licenza, /api/auth/register, /api/auth/setup-status ]
  ```
- Richieste tunnel a route bloccate → 404; tutto il resto → pass-through (auth guard + backend proteggono).
- **Host header:** sostituire la detection basata su `Host` con header custom iniettato da frpc, in `tunnel_manager.py → generate_frpc_toml()`:
  ```toml
  [proxies.plugin]
  type = "https2http"
  localAddr = "127.0.0.1:3000"
  requestHeaders.set.X-FRP-Tunnel = "true"
  ```
  Più affidabile (l'header viene dal processo frpc locale, non dal browser). Se non fattibile a breve: documentare il rischio spoofing come accettato (mitigato da `get_current_trainer()`).
- `/public/*` resta accessibile (atleti); CRM dal tunnel solo con JWT valido; auth guard (Layer 2) resta per redirect UX in LAN.

**AC:** identici a §4.

### Step 4 — Test e2e via dominio pubblico (~30min)
Esecuzione manuale dal VPS o da device esterno alla LAN: → vedi §10.

### Ordine e tempi
Step 1 (BLOCCANTE) → Step 2 (consigliato) → Step 3 (apertura, dopo Step 1) → Step 4 (validazione). ~3h dev + testing.

---

## 9. Analisi architetturale: propagazione IP nel tunnel

```
Browser → frps (VPS, SNI passthrough TCP) → tunnel → frpc (TLS termination) → localhost:3000
```

In SNI passthrough, frps **non tocca il layer HTTP** (pipe TCP puro): non può aggiungere `X-Forwarded-For`, e
frpc vede come "client" il peer del tunnel (frps), non il browser. L'IP visto da FastAPI è **`127.0.0.1`** per tutti.

| Opzione | Come funziona | Pro | Contro |
|---------|---------------|-----|--------|
| Proxy Protocol v2 | frps inietta header TCP con IP reale | Standard, preserva P2 | Next.js non lo supporta nativamente |
| **Per-account lockout** | dopo N login falliti per email, blocco temporaneo | Zero dipendenza da IP, funziona sempre | Attaccante può DoS l'account (lockout temporaneo) |

**Orientamento proposto: per-account lockout** *(da confermare al momento dell'implementazione di Strada B).*
FitManager è single-tenant (1 trainer per istanza): il rate limiting per-IP ha senso su sistemi multi-utente,
ma per un singolo account il lockout per-email sarebbe più efficace e indipendente dalla propagazione IP. Il DoS
per-account è accettabile per il POC (il trainer accede da LAN o attende il timeout). Il rate limiter IP esistente
resta come layer aggiuntivo. La valutazione definitiva (incluso se introdurre Proxy Protocol v2) è rimandata.

---

## 10. Test e2e via dominio pubblico (8 casi)

```bash
# 1. Senza token → 401
curl -sk https://gvera-dev.fitmanagerstudio.com/api/clients

# 2. JWT artigianale senza role → 401
curl -sk -H "Authorization: Bearer <jwt_senza_role>" https://gvera-dev.fitmanagerstudio.com/api/clients

# 3. JWT trainer valido (role: trainer) → 200
curl -sk -H "Authorization: Bearer <jwt_con_role>" https://gvera-dev.fitmanagerstudio.com/api/clients

# 4. JWT manomesso → 401
curl -sk -H "Authorization: Bearer <jwt_payload_alterato>" https://gvera-dev.fitmanagerstudio.com/api/clients

# 5. Register bloccato dal tunnel → 404
curl -sk https://gvera-dev.fitmanagerstudio.com/register

# 6. Host spoofing → non 200
curl -sk -H "Host: localhost" https://gvera-dev.fitmanagerstudio.com/api/clients   # atteso: 401 (mai 200)

# 7. Login brute force → lockout
for i in $(seq 1 6); do
  curl -sk -X POST -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    https://gvera-dev.fitmanagerstudio.com/api/auth/login
done                                                       # atteso: primi 5 → 401, 6° → 429

# 8. Portale pubblico funziona ancora
curl -sk "https://gvera-dev.fitmanagerstudio.com/api/public/anamnesi/validate?token=<token_valido>"   # atteso: 200
```

---

## 11. Riepilogo gravità, cosa non cambia, rischi residui

### 11.1 Ordine di intervento (gravità)
1. **Lockout / rate limiter (§3, §8 Step 1).** Bloccante assoluto per Strada B.
2. **Apertura selettiva tunnel guard (§4, §8 Step 3).** `/register` non esposto. Bloccante.
3. **Sequenziamento (§7).** Lockout prima dell'apertura. Costo zero.
4. **AC-1 — role nel JWT (§1, §8 Step 2).** Defense in depth, future-proofing. Raccomandato.
5. **Host header (§4).** Eliminare dipendenza di sicurezza dall'`Host`. Mitigato da `get_current_trainer()`.
6. **Operative (§6).** Brute force lockout, registration blocking — prima del POC.
7. **P2 test probatorio (§5).** tcpdump per dossier GDPR — completezza, non blocco.

### 11.2 Cosa NON cambia

| Componente | Stato |
|------------|-------|
| `get_current_trainer()` su tutti gli endpoint CRM | Già in vigore, invariato |
| Bouncer pattern (`trainer_id` filtering) | Già in vigore, invariato |
| Rate limiter IP (`auth_limiter` 5/min, 20/h) | Resta come layer aggiuntivo |
| Rate limiter portale (`portal_limiter` 30/min, 120/h) | Invariato |
| P2 data-blind (SNI passthrough, TLS su frpc) | Invariato |
| Portale pubblico (`ShareToken` UUID4) | Invariato |
| Cert self-signed Fase 1 | Invariato (Fase 2 = Let's Encrypt) |

### 11.3 Rischi residui post-implementazione

| Rischio | Prob. | Impatto | Mitigazione |
|---------|-------|---------|-------------|
| DoS per-account (attaccante triggera lockout del trainer) | Bassa | Medio | Accesso da LAN (lockout permissivo), timeout 5-30 min |
| Frontend HTML visibile da tunnel | Certa | Basso | Nessun dato senza JWT, solo shell React |
| Host header spoofing bypassa il guard | Bassa | Basso | Mitigato da `get_current_trainer()`; header custom frpc |
| IP reale non disponibile nel rate limiter IP | Certa | Basso | Compensato da per-account lockout |

### 11.4 Scenari operativi
- **Trainer cambia PC:** rigenerare `license.key` col nuovo `machine_id`. L'`instance_id` resta invariato → l'URL del tablet non cambia.
- **Onboarding nuovo trainer:** licenza con `instance_id` → config frpc automatica. Zero interventi su Cloudflare (wildcard copre tutti).

---

## Note di confine (cosa questo documento NON copre)

- Non specifica la struttura esatta dei claim JWT oltre `role` (lasciata all'implementazione, purché firmati).
- Non ridiscute il routing SNI (validato, §5). Fase 2 / `cert_manager.py` sostituisce solo il certificato (self-signed → Let's Encrypt), senza cambiamenti architetturali. **Vincolo Fase 2:** ogni `frpc` mantiene il cert del *proprio* `instance_id`; nessun wildcard cert condiviso sul VPS (rimetterebbe una chiave privata sul VPS, contraddice il data-blind).
- Non sostituisce la verifica con un consulente legale sulla tesi GDPR; fornisce la condizione tecnica necessaria perché quella tesi sia difendibile.
- Setup, decisioni architetturali e operations del tunnel: → `TUNNEL_ARCHITECTURE.md`.

---

## Riferimenti

- `TUNNEL_ARCHITECTURE.md` — design, build, operations del sottosistema tunnel
- `ARCHITECTURE.md` (root) — overview di sistema, 3 attori
- `SECURITY_MODEL.md` — threat model e livelli di protezione
- `api/dependencies.py` — `get_current_trainer()` (confine esistente)
- `api/services/rate_limiter.py` — rate limiter IP attuale
- `api/auth/service.py` — `create_access_token()` (JWT, oggi senza `role`)
- `frontend/src/middleware.ts` — tunnel guard + auth guard (oggi whitelist `/public/*`)
- `docs/archive/TAILSCALE_FUNNEL_SETUP.md` — setup legacy

## Changelog

| Versione | Data | Modifiche |
|----------|------|-----------|
| 1.1 | 2026-06 | Prima stesura acceptance criteria (con errore §0 su distinguibilità token) |
| 2.0 | 2026-06-08 | Revisione su audit codice: §0 corretto (ShareToken≠JWT), AC-1 declassato, nuovi bloccanti §3/§4 |
| **3.0** | **2026-06-14** | **Assorbito `STRADA_B_IMPLEMENTATION_PLAN.md` (→ §8–§11). Aggiunto §0bis: stato reale verificato nel codice (Strada B NON implementata — middleware ancora whitelist, nessun `role`, nessun `LoginLockout`). Riferimenti riallineati a `TUNNEL_ARCHITECTURE.md`.** |
