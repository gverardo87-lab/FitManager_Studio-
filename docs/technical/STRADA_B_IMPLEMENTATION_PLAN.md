# Strada B — Piano di Implementazione

**Stato:** approvato per esecuzione
**Contesto:** Apertura del CRM all'accesso del trainer da qualunque rete via tunnel FRP
**Prerequisito:** `TUNNEL_SECURITY_BOUNDARY.md` v2.0 (acceptance criteria)
**Data:** 2026-06-08

---

## 1. Obiettivo

Permettere al trainer di accedere al CRM (login, dashboard, clienti, contratti, ecc.) da qualunque rete tramite il tunnel FRP, mantenendo:
- CRM protetto da JWT (`get_current_trainer()` su tutti gli endpoint)
- Registrazione e setup bloccati dal tunnel
- Brute force su login mitigato
- P2 data-blind preservato (invariato)

---

## 2. Analisi architetturale: propagazione IP nel tunnel

### Il problema

```
Browser --> frps (VPS, SNI passthrough TCP) --> tunnel --> frpc (TLS termination) --> localhost:3000
```

In SNI passthrough, frps **non tocca il layer HTTP** — pipe TCP puro. Quindi:
- frps **non puo' aggiungere** `X-Forwarded-For`
- frpc, ricevendo dal tunnel, vede come "client" il peer del tunnel (frps), non il browser

L'IP visto da FastAPI e' **`127.0.0.1`** per tutti gli utenti via tunnel.

### Opzioni valutate

| Opzione | Come funziona | Pro | Contro |
|---------|---------------|-----|--------|
| **Proxy Protocol v2** | frps inietta header TCP con IP reale | Standard, preserva P2 | Next.js non lo supporta nativamente |
| **Per-account lockout** | Dopo N login falliti per email, blocco temporaneo | Zero dipendenza da IP, funziona sempre | Attaccante puo' DoS l'account (lockout temporaneo) |

### Decisione: per-account lockout

FitManager e' single-tenant (1 trainer per istanza). Il rate limiting per-IP ha senso su sistemi multi-utente. Per un singolo account, il lockout progressivo per-email e' piu' efficace e non dipende dalla propagazione IP nel tunnel.

Il DoS per-account e' accettabile per il POC: il trainer puo' accedere da LAN (dove il lockout e' piu' permissivo o bypassabile) oppure aspettare il timeout.

Il rate limiter IP esistente (`auth_limiter` 5/min, 20/h) resta come layer aggiuntivo.

---

## 3. Step di implementazione

### Step 1 — Lockout progressivo su login (~1h)

**File:** `api/services/rate_limiter.py` + `api/auth/router.py`

**Cosa fare:**
- Aggiungere classe `LoginLockout`: dizionario in-memory `{email: (fail_count, locked_until)}`
- Dopo 5 fallimenti consecutivi: lockout 5 minuti
- Dopo 10 fallimenti consecutivi: lockout 30 minuti
- Login riuscito: reset contatore per quell'email
- Da LAN (IP locale): lockout piu' permissivo (soglie raddoppiate) — il trainer e' fisicamente al PC
- Integrazione in `POST /auth/login`: check lockout PRIMA della verifica password (evita timing attack)

**Vincoli:**
- Il rate limiter IP esistente (`auth_limiter`) resta invariato come layer aggiuntivo
- Lockout in-memory (reset al restart del backend) — accettabile per single-tenant
- Logging: ogni lockout loggato con `logger.warning`

**Criterio di accettazione:**
- 5 login falliti per `test@test.com` → 6° tentativo riceve 429 con messaggio "Troppi tentativi"
- Login riuscito dopo lockout scaduto → reset contatore
- Login riuscito prima del lockout → reset contatore

---

### Step 2 — Role claim nel JWT (~30min)

**File:** `api/auth/service.py` + `api/dependencies.py`

**Cosa fare:**
- `create_access_token()`: aggiungere `"role": "trainer"` al payload JWT
- `get_current_trainer()`: dopo `decode_access_token()`, verificare `payload.get("role") == "trainer"`. Se assente o diverso → 401

**Effetto collaterale:** tutti i trainer loggati vengono forzati al re-login (token vecchio senza `role` = 401). Accettabile — i token durano 8h e il re-login e' trasparente.

**Vincoli:**
- Fail-closed: token senza `role` → 401 (non "trainer per default")
- Zero impatto su portale pubblico (`ShareToken` UUID4 — meccanismo completamente separato)

**Criterio di accettazione:**
- `jwt.decode(token)` contiene `role: "trainer"`
- Token senza `role` → 401 su qualsiasi endpoint CRM
- Portale pubblico (`/api/public/*`) continua a funzionare (usa ShareToken, non JWT)

---

### Step 3 — Apertura selettiva tunnel guard (~1h)

**File:** `frontend/src/middleware.ts`

**Cosa fare:**
- Invertire la logica: da whitelist (solo `/public/*` permesso) a **blacklist** (tutto permesso tranne route bloccate)
- Definire `TUNNEL_BLOCKED_PREFIXES`:
  ```
  /register
  /setup
  /licenza
  /api/auth/register
  /api/auth/setup-status
  ```
- Richieste tunnel a route bloccate → 404
- Richieste tunnel a tutto il resto → pass-through (auth guard + backend proteggono)

**Host header:**
- Valutare sostituzione della detection basata su `Host` con header custom iniettato da frpc
- frpc supporta `requestHeaders.set.X-FRP-Tunnel = "true"` nella config `https2http`
- Piu' affidabile: l'header viene dal processo frpc locale, non dal client browser
- Se non fattibile in tempi brevi: documentare il rischio spoofing come accettato (mitigato da `get_current_trainer()`)

**Aggiornamento frpc.toml** (in `tunnel_manager.py` → `generate_frpc_toml()`):
```toml
[proxies.plugin]
type = "https2http"
localAddr = "127.0.0.1:3000"
requestHeaders.set.X-FRP-Tunnel = "true"
```

**Vincoli:**
- `/public/*` resta accessibile dal tunnel (atleti)
- CRM accessibile dal tunnel solo con JWT valido
- Auth guard (Layer 2) resta per redirect UX su richieste LAN senza cookie

**Criterio di accettazione:**
- Dal tunnel, senza token: `/login` → 200. `/dashboard` → redirect `/login`. `/api/clients` → 401.
- Dal tunnel, con JWT trainer: `/dashboard` → 200. `/api/clients` → 200.
- Dal tunnel: `/register` → 404. `/setup` → 404.

---

### Step 4 — Test e2e via dominio pubblico (~30min)

**Esecuzione:** manuale dal VPS o da device esterno alla LAN.

```bash
# 1. Senza token → 401
curl -sk https://gvera-dev.fitmanagerstudio.com/api/clients
# Atteso: 401 (o 403 da HTTPBearer)

# 2. JWT artigianale senza role → 401
curl -sk -H "Authorization: Bearer <jwt_senza_role>" \
  https://gvera-dev.fitmanagerstudio.com/api/clients
# Atteso: 401

# 3. JWT trainer valido (role: trainer) → 200
curl -sk -H "Authorization: Bearer <jwt_con_role>" \
  https://gvera-dev.fitmanagerstudio.com/api/clients
# Atteso: 200

# 4. JWT manomesso → 401
curl -sk -H "Authorization: Bearer <jwt_payload_alterato>" \
  https://gvera-dev.fitmanagerstudio.com/api/clients
# Atteso: 401

# 5. Register bloccato dal tunnel → 404
curl -sk https://gvera-dev.fitmanagerstudio.com/register
# Atteso: 404

# 6. Host spoofing → non 200
curl -sk -H "Host: localhost" \
  https://gvera-dev.fitmanagerstudio.com/api/clients
# Atteso: 401 (mai 200)

# 7. Login brute force → lockout
for i in $(seq 1 6); do
  curl -sk -X POST -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    https://gvera-dev.fitmanagerstudio.com/api/auth/login
done
# Atteso: primi 5 → 401, 6° → 429 (locked)

# 8. Portale pubblico funziona ancora
curl -sk "https://gvera-dev.fitmanagerstudio.com/api/public/anamnesi/validate?token=<token_valido>"
# Atteso: 200 (se PUBLIC_PORTAL_ENABLED=true e token valido)
```

---

## 4. Ordine di esecuzione

```
Step 1 (lockout login)         BLOCCANTE — prerequisito
  |
  v
Step 2 (role JWT)              raccomandato prima dell'apertura
  |
  v
Step 3 (apertura guard)        l'atto di apertura — dopo Step 1
  |
  v
Step 4 (test e2e)              validazione finale
```

Tempo stimato: ~3h di sviluppo + testing.

---

## 5. Cosa NON cambia

| Componente | Stato |
|------------|-------|
| `get_current_trainer()` su tutti gli endpoint CRM | Gia' in vigore, invariato |
| Bouncer pattern (trainer_id filtering) | Gia' in vigore, invariato |
| Rate limiter IP (`auth_limiter` 5/min, 20/h) | Resta come layer aggiuntivo |
| Rate limiter portale (`portal_limiter` 30/min, 120/h) | Invariato |
| P2 data-blind (SNI passthrough, TLS termina su frpc) | Invariato |
| Portale pubblico (ShareToken UUID4) | Invariato |
| Cert self-signed Fase 1 | Invariato (Fase 2 = Let's Encrypt) |

---

## 6. Rischi residui post-implementazione

| Rischio | Probabilita' | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| DoS per-account (attaccante triggera lockout del trainer) | Bassa | Medio | Trainer accede da LAN (lockout piu' permissivo), timeout scade in 5-30 min |
| Frontend HTML visibile da tunnel (struttura app) | Certa | Basso | Nessun dato senza JWT, solo shell React |
| Host header spoofing bypassa tunnel guard | Bassa | Basso | Mitigato da `get_current_trainer()`, valutare header custom frpc |
| IP reale non disponibile nel rate limiter IP | Certa | Basso | Compensato da per-account lockout, rate limiter IP resta come layer extra |

---

## 7. Riferimenti

- `docs/technical/TUNNEL_SECURITY_BOUNDARY.md` v2.0 — acceptance criteria
- `docs/technical/TUNNEL_MIGRATION_STRATEGY.md` v1.0 — strategia migrazione completa
- `api/dependencies.py:29-60` — `get_current_trainer()` (confine esistente)
- `api/services/rate_limiter.py` — rate limiter IP attuale
- `api/auth/service.py:28-41` — `create_access_token()` (JWT senza role)
- `frontend/src/middleware.ts` — tunnel guard + auth guard attuali
