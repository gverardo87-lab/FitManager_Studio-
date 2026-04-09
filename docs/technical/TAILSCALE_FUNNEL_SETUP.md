# Tailscale Funnel — Setup e Guida Operativa

> **Documento di riferimento per installazione, configurazione e troubleshooting
> di Tailscale Funnel su FitManager AI Studio.**
> Destinato sia allo sviluppatore che all'installatore sui PC di clienti chinesiologi, personal trainer e professionisti fitness a P.IVA.

---

## Cos'e' Tailscale Funnel

Tailscale Funnel espone un servizio locale su internet pubblico con HTTPS automatico.
Il cliente finale (es. paziente del chinesiologo) clicca un link nel browser del telefono
e compila l'anamnesi — **senza installare nulla**, da qualsiasi rete (4G, Wi-Fi casa, ecc.).

I dati vanno direttamente dal browser al PC del trainer. Zero cloud, zero intermediari.

---

## Metodologia Operativa Definitiva

### Chi accede e come

| Chi | Come accede | URL | Richiede |
|-----|-------------|-----|----------|
| **Trainer (PC studio)** | Browser locale | `http://localhost:3000` | Nulla |
| **Trainer (tablet studio)** | Stesso Wi-Fi (LAN) | `http://192.168.x.x:3000` | Stesso Wi-Fi |
| **Trainer (fuori studio)** | Tailscale VPN | `http://100.x.x.x:3000` | App Tailscale su tablet |
| **Cliente (anamnesi)** | Link monouso WhatsApp | `https://nome.ts.net/public/anamnesi/{token}` | Solo browser |

Nota importante:
- la modalita' **Tailscale VPN / dispositivi fidati** richiede Tailscale anche sul device remoto;
- una volta raggiunto FitManager sull'indirizzo Tailscale, il trainer deve comunque fare il login applicativo FitManager su quel browser;
- il **Funnel pubblico** non espone il CRM completo: serve solo per le route pubbliche, in particolare l'anamnesi cliente.

### Flusso operativo quotidiano

1. Il trainer accende il PC → FitManager si avvia automaticamente (backend 8000 + frontend 3000)
2. Tailscale Funnel e' gia' attivo in background (`--bg`, sopravvive a riavvii)
3. Il trainer lavora da `localhost:3000` (o tablet via LAN/VPN)
4. Quando serve inviare un'anamnesi al cliente:
   - Profilo cliente → Anamnesi → "Invia Questionario"
   - Il link generato punta automaticamente a `https://nome.ts.net/...` (grazie a `PUBLIC_BASE_URL`)
   - Il trainer copia il link e lo invia su WhatsApp
5. Il cliente apre il link dal telefono → compila → dati nel DB locale del trainer

### Cosa NON serve al cliente finale
- Nessuna installazione (ne' Tailscale ne' altro)
- Nessun login o registrazione
- Nessuna app da scaricare
- Solo un link nel browser del telefono (Chrome, Safari, qualsiasi)

### Vincolo operativo
Il link funziona **SOLO** se il PC del trainer e' acceso e FitManager e' in esecuzione.
Se il PC e' spento, il cliente vedra' un errore di connessione.

---

## Prerequisiti

| Requisito | Dettaglio |
|-----------|-----------|
| Tailscale installato | v1.56+ (richiesto per `--bg` persistente) |
| Account Tailscale | Gratuito (piano Personal fino a 3 utenti) |
| MagicDNS abilitato | Admin Console → DNS → MagicDNS ON |
| HTTPS Certificates abilitato | Admin Console → DNS → HTTPS Certificates ON |
| ACL Funnel permission | Admin Console → Access Controls (vedi sotto) |
| PC acceso | Il link funziona SOLO se il PC e FitManager sono in esecuzione |

---

## Installazione Completa su PC Cliente (Runbook)

> **Checklist operativa per l'installatore.** Seguire nell'ordine esatto.
> Tempo stimato: 15-20 minuti (di cui 10 di download/installazione).

### Fase 1 — Tailscale (5 min)

- [ ] 1.1 Scaricare Tailscale da https://tailscale.com/download/windows
- [ ] 1.2 Installare e autenticarsi con l'account del trainer (email personale)
- [ ] 1.3 Verificare installazione:
  ```bash
  tailscale status
  # Deve mostrare la macchina con IP 100.x.x.x e nome (es. "pc-studio")
  ```
- [ ] 1.4 Annotare i dati della macchina:
  - **Nome macchina**: _________________ (es. `pc-studio`)
  - **Tailnet**: _________________ (es. `tail1234ab.ts.net`)
  - **DNS name completo**: _________________ (es. `pc-studio.tail1234ab.ts.net`)
  - **IP Tailscale**: _________________ (es. `100.x.x.x`)

### Fase 2 — Admin Console Tailscale (3 min)

Accedere a https://admin.tailscale.com con l'account del trainer.

- [ ] 2.1 **DNS** → verificare che **MagicDNS** sia ON (di solito attivo di default)
- [ ] 2.2 **DNS** → abilitare **HTTPS Certificates** se non attivo
- [ ] 2.3 **Access Controls** → nell'editor visuale, sezione **Capabilities**:
  - **Target**: selezionare l'email dell'account Tailscale del trainer
  - **Attribute**: `funnel`
  - **IP Pools**: lasciare vuoto
  - **Salvare** la policy
- [ ] 2.4 Verificare permesso Funnel:
  ```bash
  tailscale funnel status
  # OK: qualsiasi risposta che NON sia "Funnel not available"
  # (anche "No serve config" va bene — il permesso c'e')
  ```

### Fase 3 — FitManager (5 min)

- [ ] 3.1 Eseguire l'ultima build `FitManager_Setup_1.0.4.exe`
- [ ] 3.2 Primo avvio: completare il Setup Wizard (credenziali trainer)
- [ ] 3.3 Attivare licenza (se richiesta)
- [ ] 3.4 Verificare che il CRM funzioni: `http://localhost:3000` → login → navigazione OK

### Fase 4 — Configurazione Portale Pubblico (2 min)

- [ ] 4.1 Aprire FitManager → `Impostazioni -> Connettivita`
- [ ] 4.2 Nel wizard guidato:
  - scegliere `Portale pubblico`
  - usare `Usa DNS rilevato` se il DNS Tailscale e' stato rilevato
  - in alternativa inserire manualmente `https://<nome-macchina>.<tailnet>.ts.net`
- [ ] 4.3 Applicare la configurazione dal prodotto
- [ ] 4.4 Verificare che il profilo risultante sia `public_portal`

Fallback tecnico solo se il wizard non e' disponibile o fallisce:
```env
PUBLIC_PORTAL_ENABLED=true
PUBLIC_BASE_URL=https://<nome-macchina>.<tailnet>.ts.net
```
In quel caso riavviare FitManager dopo la modifica manuale del file `data/.env`.

### Fase 5 — Funnel (automatico dal launcher)

Il launcher attiva automaticamente il funnel se `PUBLIC_PORTAL_ENABLED=true` nel `.env`.
Non serve aprire terminali — basta avviare FitManager normalmente.

- [ ] 5.1 Verificare che nel log del launcher compaia: `[+] Attivazione Tailscale Funnel su porta 3000...`
- [ ] 5.2 Verificare stato:
  ```bash
  tailscale funnel status
  # Deve mostrare:
  # https://<nome>.<tailnet>.ts.net (Funnel on)
  # |-- / proxy http://127.0.0.1:3000
  ```

**Se serve attivare manualmente** (debug o terminale):
```bash
tailscale funnel --bg 3000
```

### Fase 6 — Test End-to-End (3 min)

- [ ] 6.0 **Test CRM su dispositivo fidato**: da tablet/telefono del trainer con Tailscale attivo
  - installare e aprire Tailscale sul device remoto
  - fare login nello stesso tailnet del PC studio
  - aprire `http://<IP-Tailscale-PC>:3000` oppure `http://<dns-ts>.ts.net:3000`
  - verificare che FitManager risponda
  - fare login con le credenziali FitManager del trainer
  - verificare che la sessione remota sia indipendente da `localhost`
- [ ] 6.1 **Test login via Funnel**: da un telefono (4G, Tailscale DISABILITATO):
  - Aprire `https://<nome>.ts.net/login` → deve apparire la pagina login
  - Fare login con le credenziali → deve funzionare
- [ ] 6.2 **Verifica guidata in-app**: dal PC aprire `Impostazioni -> Connettivita`
  - scegliere un cliente attivo di prova
  - generare un link anamnesi monouso
  - eseguire la validazione guidata
  - il verdetto deve risultare `ready`
- [ ] 6.3 **Test anamnesi**: dal PC (localhost:3000):
  - Navigare su un profilo cliente → Anamnesi → "Invia Questionario"
  - Il link generato deve iniziare con `https://<nome>.ts.net/public/anamnesi/...`
  - Copiare il link → aprirlo dal telefono (4G) → deve apparire il form
  - Compilare e inviare → verificare che i dati compaiano nel profilo cliente
- [ ] 6.4 **Test monouso**: riaprire lo stesso link → deve mostrare "Link gia' utilizzato"

### Post-installazione — Comunicazione al Trainer

- [ ] Comunicare il link Funnel: `https://<nome>.ts.net`
- [ ] Spiegare: **"Il link per i clienti funziona solo quando FitManager e' aperto sul PC"**
- [ ] Spiegare: **"Tu lavori normalmente da localhost:3000, i link per i clienti li genera il sistema"**
- [ ] Spiegare: **"Dal tablet o da un altro dispositivo fuori studio devi prima accedere a Tailscale e poi fare anche il login FitManager su quel browser"**
- [ ] Spiegare: **"Dal tablet puoi accedere tramite lo stesso Wi-Fi usando l'IP del PC"**
- [ ] Annotare l'IP LAN del PC per accesso tablet: _________________ (es. `192.168.1.10`)
- [ ] Test tablet: aprire `http://<IP-LAN>:3000` dal tablet del trainer → login → OK

---

## Architettura Tecnica — Come Funziona

```
Cliente (smartphone 4G, qualsiasi rete)
  |
  | HTTPS (certificato Let's Encrypt gestito da Tailscale)
  v
Tailscale Funnel (cloud Tailscale — solo routing, zero dati persistiti)
  |
  | TCP tunnel crittografato
  v
PC Trainer (Tailscale daemon locale)
  |
  | proxy http://127.0.0.1:3000
  v
Next.js Frontend (porta 3000)
  |
  | rewrite /api/* → http://localhost:8000/api/*
  | rewrite /media/* → http://localhost:8000/media/*
  v
FastAPI Backend (porta 8000) → SQLite locale
```

### Perche' funziona senza esporre la porta 8000

Il frontend Next.js funge da **reverse proxy**:
- Il browser chiama URL relativi (`/api/auth/login`)
- Next.js rewrite li proxya internamente a `http://localhost:8000/api/auth/login`
- Il backend non e' mai esposto direttamente su internet

Configurazione in `frontend/next.config.ts`:
```typescript
rewrites: async () => ({
  source: "/api/:path*",
  destination: `http://localhost:${backendPort}/api/:path*`,
})
```

### API URL Detection (`frontend/src/lib/api-client.ts`)

```typescript
// HTTPS o nessuna porta → siamo dietro Funnel/reverse proxy → URL relativi
if (protocol === "https:" || !port) return "/api";
// Altrimenti → mapping diretto porta (LAN, localhost, VPN)
return `http://${hostname}:${apiPort}/api`;
```

### PUBLIC_BASE_URL — Link Generation

```
Trainer lavora da localhost:3000
  → genera link anamnesi
  → backend legge PUBLIC_BASE_URL da data/.env
  → ritorna URL assoluto: https://nome.ts.net/public/anamnesi/{token}
  → frontend mostra URL completo (non prepende localhost)
  → il link funziona dal telefono del cliente
```

Senza `PUBLIC_BASE_URL`, il link userebbe `window.location.origin` (es. `http://localhost:3000/...`)
che non sarebbe raggiungibile dal telefono del cliente.

### Proxy Next.js (`frontend/src/proxy.ts`)

`/api` e' nelle `PUBLIC_ROUTES` — il proxy non interferisce con le chiamate API
proxiate. L'autenticazione JWT e' gestita dal backend FastAPI.

---

## Gestione Funnel

### Attivare (persistente — raccomandato)
```bash
tailscale funnel --bg 3000
```
Sopravvive a chiusura terminale e riavvii del PC (richiede Tailscale v1.56+).

### Disattivare
```bash
tailscale funnel --bg off
```

### Verificare stato
```bash
tailscale funnel status
```

### Attivare (temporaneo — solo per test)
```bash
tailscale funnel 3000
# Ctrl+C per fermare
```

---

## Feature Flag e Configurazione

```env
# data/.env — configurazione completa per portale pubblico
PUBLIC_PORTAL_ENABLED=true
PUBLIC_BASE_URL=https://<nome-macchina>.<tailnet>.ts.net
```

### PUBLIC_PORTAL_ENABLED
Default: `false`. Se disabilitato, tutti gli endpoint `/api/public/*` ritornano 404.
Il Funnel continuera' a funzionare per il login trainer (utile per accesso remoto),
ma i link anamnesi per i clienti non saranno generabili.

### PUBLIC_BASE_URL
Default: vuoto (URL relativo). Se configurato, i link anamnesi generati usano questo
dominio come base — il trainer puo' lavorare da `localhost:3000` normalmente e i link
generati saranno comunque accessibili dal cliente via Funnel.

**Senza** `PUBLIC_BASE_URL`: il link usa `window.location.origin` — se il trainer
accede da localhost, il link sara' `http://localhost:3000/public/anamnesi/{token}`
(non raggiungibile dal cliente).

**Con** `PUBLIC_BASE_URL`: il link sara' sempre
`https://<nome>.ts.net/public/anamnesi/{token}` indipendentemente da come il trainer
accede al CRM.

**Importante**: dopo aver modificato `data/.env`, riavviare FitManager (il backend
legge le variabili d'ambiente solo all'avvio).

---

## Regola critica: il Funnel punta al FRONTEND, mai al backend

```
CORRETTO:    tailscale funnel --bg 3000    → proxy http://127.0.0.1:3000 (Next.js)
SBAGLIATO:   tailscale funnel --bg 8000    → proxy http://127.0.0.1:8000 (FastAPI)
```

**Perche'**: la pagina `/public/anamnesi/{token}` e' una route Next.js. Se il funnel
punta al backend (8000), il client riceve `404 Not Found` perche' FastAPI non serve
pagine HTML. Il frontend Next.js fa proxy delle chiamate `/api/*` al backend internamente.

Il launcher usa automaticamente `%FRONTEND_PORT%` (3000 in prod, variabile con `--port`).

**Sintomo se la porta e' sbagliata**: il link anamnesi apre una pagina con `{"detail":"Not Found"}`
invece del questionario. Il backend risponde, ma non sa servire la route frontend.

---

## Auto-start nel Launcher

Dal v1.0.6, `launcher.bat` avvia automaticamente il Funnel dopo backend + frontend:

```
[1/3] Avvio backend API...
[2/3] Attesa backend...
[3/3] Avvio frontend...
[+] Attivazione Tailscale Funnel su porta 3000...
```

**Condizioni per l'auto-start:**
1. `PUBLIC_PORTAL_ENABLED=true` presente in `data/.env`
2. Tailscale installato (trovato in PATH o in `C:\Program Files\Tailscale\`)

Se una delle condizioni manca, il launcher prosegue senza Funnel (nessun errore bloccante).
Il comando `tailscale funnel --bg` e' idempotente: se il funnel e' gia' attivo, non fa nulla.

---

## Troubleshooting

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `{"detail":"Not Found"}` sulla pagina anamnesi | **Funnel punta al backend (8000) invece che al frontend (3000)** | `tailscale funnel off` poi `tailscale funnel --bg 3000` |
| "Funnel not available" | ACL non configurato | Admin Console → Access Controls → aggiungere funnel attr |
| Login gira e da errore | Proxy blocca `/api/*` | Verificare `PUBLIC_ROUTES` include `/api` in `src/proxy.ts` |
| Link anamnesi con "localhost" | `PUBLIC_BASE_URL` non configurato | Aggiungere `PUBLIC_BASE_URL=https://...` in `data/.env` e riavviare |
| Link anamnesi non funziona da telefono | PC spento o FitManager non in esecuzione | Avviare FitManager + verificare `tailscale funnel status` |
| "ERR_CONNECTION_REFUSED" da telefono | Funnel non attivo | `tailscale funnel --bg 3000` |
| 502 Bad Gateway | Funnel attivo ma FitManager spento | Avviare FitManager |
| Certificato non valido | HTTPS Certificates non abilitato | Admin Console → DNS → abilitare HTTPS Certificates |
| Pagina bianca dopo login | Backend non raggiungibile | Verificare backend su porta 8000: `curl localhost:8000/health` |
| Immagini esercizi non caricate | Rewrite `/media/*` mancante | Verificare `next.config.ts` ha rewrite per `/media/:path*` |
| Tablet non raggiunge il CRM | IP LAN errato o firewall | Verificare IP con `ipconfig`, controllare firewall Windows porta 3000 |
| Funnel --bg fallisce con "foreground listener" | Funnel temporaneo gia' attivo | Chiudere il terminale con Funnel foreground, poi `tailscale funnel --bg 3000` |
| Launcher non avvia il funnel | `PUBLIC_PORTAL_ENABLED` non nel `.env` o Tailscale non installato | Verificare `data/.env` e `tailscale status` |

---

## Sicurezza

| Aspetto | Implementazione |
|---------|----------------|
| Trasporto | HTTPS (Let's Encrypt via Tailscale) |
| Dati in transito | Solo routing via Tailscale cloud, zero persistenza |
| Dati a riposo | SQLite locale sul PC del trainer |
| Token anamnesi | UUID4 monouso, scadenza 48h, invalidato dopo uso |
| Rate limiting | 10 req/min, 30 req/h per IP (in-process) |
| Mascheramento | Nome cliente mascherato nella pagina pubblica ("Marco R.") |
| Feature flag | Disattivabile con `PUBLIC_PORTAL_ENABLED=false` |
| Backend | Non esposto direttamente — solo via Next.js proxy |
| Zero PII nel token | UUID opaco, nessun dato personale nell'URL |
| Soft-delete check | Token per client cancellato → 404 |

---

## Costi

- **Tailscale Personal**: gratuito (fino a 3 utenti, 100 dispositivi)
- **Funnel**: incluso nel piano gratuito
- **Dominio**: fornito da Tailscale (`*.ts.net`), zero costi DNS
- **Certificato HTTPS**: Let's Encrypt automatico, zero costi

---

## Setup Attuale (Sviluppo — gvera)

```
Tailscale:     v1.94.2
Macchina:      giacomo
Tailnet:       tail8a3bc3.ts.net
DNS name:      giacomo.tail8a3bc3.ts.net
IP Tailscale:  100.127.28.16
IP LAN:        192.168.1.23
Funnel:        https://giacomo.tail8a3bc3.ts.net/ → proxy http://127.0.0.1:3000
data/.env:     PUBLIC_PORTAL_ENABLED=true, PUBLIC_BASE_URL=https://giacomo.tail8a3bc3.ts.net
```

Dispositivi Tailscale:
- `giacomo` (PC dev, Windows) — 100.127.28.16
- `ipad-10th-gen-wifi` (iPad Chiara) — 100.77.229.76
- `iphone183` (iPhone) — 100.116.68.114

---

## Sviluppo con Funnel

### Problema: HMR reload loop via Funnel

Accedendo a `https://giacomo.tail8a3bc3.ts.net` con `npm run dev`, la pagina si ricarica
ogni pochi secondi. Il WebSocket HMR (`_next/webpack-hmr`) fallisce per due motivi combinati:

1. **Tailscale Funnel non proxya WebSocket upgrade** — il tunnel e' HTTP-only, la richiesta
   `wss://giacomo.ts.net/_next/webpack-hmr` ritorna 502.
2. **Next.js 16 blocca Origin cross-site** — anche redirectando il WebSocket a
   `ws://localhost:3001`, la funzione `blockCrossSite()` in `router-server.js` rifiuta
   il handshake perche' l'header `Origin: https://giacomo.tail8a3bc3.ts.net` non matcha
   localhost → risposta HTTP 403 → browser interpreta come `ERR_INVALID_HTTP_RESPONSE`.

Dopo N retry falliti, Next.js esegue full page reload → loop infinito.

### Soluzione: mock WebSocket (dev-only)

`layout.tsx` inietta un `<script>` che intercetta la creazione di WebSocket HMR.
Quando l'hostname non e' `localhost` ne' `127.0.0.1` e l'URL contiene `_next/webpack-hmr`,
invece di aprire una connessione reale, restituisce un **oggetto mock** che:

- Simula `readyState: OPEN` (1) e fire `onopen` dopo un tick
- Non invia ne' riceve messaggi (`send()` = no-op)
- Non chiude ne' genera errori (`onclose`/`onerror` mai invocati)
- Implementa l'interfaccia WebSocket completa (inclusi `addEventListener`/`removeEventListener`)

Next.js HMR crede di essere connesso ma non riceve update → **zero reload, zero retry,
pagina stabile**. Lo sviluppatore usa `localhost:3001` per HMR attivo e il Funnel
esclusivamente per verificare flussi client-facing (anamnesi, scheda allenamento, etc.).

Lo script viene incluso SOLO con `NODE_ENV === "development"` (tree-shaken in prod build).
Su `localhost`/`127.0.0.1` non ha effetto — il WebSocket reale viene creato normalmente.

### Font locali (eliminano 403 su `/__nextjs_font/`)

I font (Inter, Caveat) sono serviti da file locali in `frontend/src/fonts/` invece che da
Google Fonts CDN. Questo elimina l'endpoint `/__nextjs_font/` che Funnel bloccava con 403.

Vantaggi collaterali: zero richieste a Google, funziona offline, coerente con privacy-first.

**Nota**: dopo un cambio di font o pulizia della cache, eseguire `rm -rf .next .next-dev`
e hard refresh nel browser (Ctrl+Shift+R) per eliminare riferimenti stale a file `.woff2`
ormai inesistenti.

### Script `dev:funnel`

```bash
npm run dev:funnel   # next build && next start -p 3000 -H 0.0.0.0
```

Per testare esattamente cio' che vede il cliente (prod build, zero HMR) via Funnel su porta 3000.

### Troubleshooting sviluppo con Funnel

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| Pagina si ricarica ogni 3-5 sec via Funnel | Mock WebSocket non attivo (script mancante in `<head>`) | Verificare in DevTools → Elements che lo script mock sia presente. Se manca: `NODE_ENV` non e' `development` |
| Console mostra `ERR_INVALID_HTTP_RESPONSE` | Mock non intercetta il WebSocket (hostname check fallito) | Verificare che l'URL del Funnel non sia `localhost`. DevTools → Console: il mock logga zero errori se attivo |
| Font 403 via Funnel (`geist-latin.woff2` o simili) | Cache stale con riferimenti a font rimossi | `rm -rf .next .next-dev` + Ctrl+Shift+R (hard refresh browser) |
| Font 403 via Funnel (`/__nextjs_font/`) | Font serviti da Google Fonts CDN | Verificare che `layout.tsx` usi `next/font/local`, non `next/font/google` |
| HMR non funziona via Funnel | **Comportamento atteso**: il mock disabilita HMR via Funnel by design | Usare `localhost:3001` per sviluppo con HMR. Il Funnel serve solo per test flussi client-facing |
| `dev:funnel` non parte | Build fallisce | Risolvere errori TypeScript con `npx next build` |

## Note per Sviluppo Futuro

- **Custom domain**: Tailscale supporta custom domain su Funnel (piano a pagamento).
  Es. `https://studio-chiara.fitmanager.it` invece di `*.ts.net`
- **Auto-start FitManager**: configurare launcher.bat in Startup di Windows
  per avvio automatico al login del trainer
- **Monitoring uptime**: potenziale feature futura — notifica push se il PC e' offline
  quando un cliente tenta di accedere

### Roadmap accesso remoto clienti (oltre l'anamnesi)

Il funnel su porta frontend e' la base per tutte le feature client-facing future.
Lo stesso pattern (token monouso + pagina pubblica + proxy API) si applica a:

1. **Anamnesi self-service** (attivo) — questionario 6 step
2. **Visualizzazione scheda allenamento** — il cliente vede la scheda dal telefono
3. **Visualizzazione piano alimentare** — il cliente vede il piano LARN
4. **Progress report** — il cliente vede i propri progressi (misurazioni, grafici)
5. **Booking self-service** — il cliente prenota la prossima sessione
6. **Pagamento online** — integrazione Stripe/PayPal con link monouso

Tutti passano per lo stesso tunnel: frontend porta 3000 → proxy API → SQLite locale.
Nessun dato esce dal PC del trainer. Zero cloud. Zero abbonamenti.

Architettura target:
```
/public/anamnesi/{token}     → questionario (attivo)
/public/scheda/{token}       → scheda allenamento (futuro)
/public/nutrizione/{token}   → piano alimentare (futuro)
/public/progressi/{token}    → report progressi (futuro)
/public/booking/{token}      → prenotazione sessione (futuro)
```

Ogni route pubblica segue lo stesso pattern:
- Token UUID4 monouso, scadenza configurabile
- Rate limiting IP-based
- Mascheramento PII nella pagina pubblica
- Fire-and-forget: il client invia, il trainer controlla dopo
