# TUNNEL_ARCHITECTURE.md — Sottosistema tunnel pubblico

**Progetto:** FitManager AI Studio
**Versione:** 3.1 (consolidata)
**Stato:** Fase 0 + Fase 1 completate · R0.1.5 TLS pubblico in implementazione · resto Fase 2/3 pianificato
**Ambito:** Esposizione pubblica del portale clienti tramite tunnel FRP self-hosted, end-to-end.
**Documenti correlati:**
- `ARCHITECTURE.md` (root) — overview dell'intero sistema; i 3 attori vivono lì.
- `TUNNEL_SECURITY_BOUNDARY.md` — confine di sicurezza e acceptance criteria (apertura del CRM al tunnel).
- `SECURITY_MODEL.md` — threat model e livelli di protezione del prodotto.
- `LEGAL_REGULATORY_REPORT.md` v1.3 — compliance GDPR (P2 data-blind).

> **Cos'è questo documento.** Il riferimento unico del **sottosistema tunnel**: dal *perché esiste* (Parte I)
> al *come è progettato* (Parte II) al *come si costruisce e si opera* (Parte III). Consolida i 4 documenti
> storici (`ARCHITECTURE_OVERVIEW`, `CRM_ACCESS_ARCHITECTURE`, `TUNNEL_MIGRATION_STRATEGY`, `VPS_EDGE_SETUP`).
>
> **Cosa NON è.** Non è l'overview del sistema intero (→ `ARCHITECTURE.md` in root). Non è il confine di
> sicurezza dell'apertura del CRM (→ `TUNNEL_SECURITY_BOUNDARY.md`). Versione prodotto: vedi `api/__init__.py`.

---

# Parte I — Concetto (capire)

## 1. Il problema di partenza

FitManager non è un sito web dove i dati stanno su un server centrale. È un programma che **ogni trainer
installa sul proprio computer** (PC o mini-PC nel proprio studio/palestra). Quel computer fa due cose insieme:

1. È il **gestionale (CRM)** che il trainer usa per gestire i clienti — aperto da tablet/telefono in LAN.
2. È anche un **piccolo server** che mostra pagine (schede, questionari di anamnesi) ai **clienti finali**,
   che le aprono da casa cliccando un link.

I dati dei clienti (anche dati sanitari, Art. 9 GDPR) stanno **solo** su quel computer, mai sui server di AVGV.
Scelta deliberata: semplifica radicalmente la postura legale, perché AVGV non tocca mai quei dati.

Da qui il problema tecnico: **come fa il cliente finale, che è a casa su Internet, a raggiungere un programma
che gira sul PC del trainer dietro il router della palestra?** Quel PC non ha indirizzo pubblico, è come una
casa senza numero civico. E il vincolo di prodotto è **"zero configurazione di rete per il trainer"** — niente
port forwarding, niente IP statici, niente certificati gestiti a mano.

## 2. La soluzione: il tunnel e il "centralino"

La soluzione è un **tunnel reverse**. Invece di aspettare che qualcuno entri nel PC del trainer (difficile,
dietro NAT), è **il PC del trainer che apre da solo una connessione verso l'esterno**, verso un punto fisso
controllato da AVGV: il **VPS edge**. Una volta aperta, il traffico dei clienti finali viaggia nei due sensi.

Metafora del centralino telefonico:
- Il **VPS** è un centralino con numero pubblico noto, sempre acceso, raggiungibile da chiunque.
- Il **PC del trainer** chiama il centralino: "sono lo studio di Alessio, tieni aperta la linea con me".
- Quando un **cliente finale** vuole raggiungere lo studio di Alessio, chiama il centralino (VPS), che gira
  la chiamata sulla linea già aperta verso il PC di Alessio.

Punto cruciale dell'intero progetto — **il centralino non ascolta le telefonate**. Il traffico nel tunnel è
cifrato in modo che il VPS lo instrada **senza poterlo leggere** (principio **P2 — data-blind**). È sia una
scelta di sicurezza sia di compliance: se AVGV non può leggere i dati sanitari, dal punto di vista GDPR non
li "tratta", e una serie di obblighi pesanti decade (vedi §4).

## 3. I tre attori

I tre attori del sistema (AVGV, Trainer, Cliente finale) sono descritti nell'overview di sistema:
→ **`ARCHITECTURE.md` §2** (root). Qui basta la regola d'oro del tunnel:

> Il **CRM del trainer non è raggiungibile da Internet** allo stato attuale del prodotto — solo dalla LAN.
> Dal tunnel pubblico passano **solo** le pagine destinate ai clienti finali (`/public/*`). Sono due "piani"
> separati, applicati a livello di rete e di codice (vedi §6 e `TUNNEL_SECURITY_BOUNDARY.md`).

*(L'apertura selettiva del CRM al tunnel — "Strada B" — è progettata ma non ancora implementata: vedi
`TUNNEL_SECURITY_BOUNDARY.md`.)*

## 4. Vincoli di progetto e implicazioni GDPR

### 4.1 Vincoli (definiti dal committente)

1. **Software locale, non SaaS centralizzato**: l'istanza gira sull'hardware del trainer. Nessuna replica centrale dei dati.
2. **Zero configurazione di rete lato trainer**: niente DNS, port forwarding, IP statico, firewall, certificati a mano.
3. **Zero installazioni/credenziali lato cliente finale**: apre il link e accede senza registrazione.
4. **Database SQLite locale per trainer**: nessun database centralizzato lato AVGV.
5. **Disponibilità legata al PC del trainer**: PC spento = sistema offline. Comportamento atteso e accettato.
6. **Infrastruttura AVGV minima**: l'unico elemento server-side è il tunnel edge che instrada il traffico. Nessun database, nessuna logica applicativa, nessun dato clinico.
7. **Costi sostenibili per la POC**: dominio (~10 €/anno) + VPS edge (~4-6 €/mese). Il trainer non sostiene costi infrastrutturali.

### 4.2 Conseguenze sulla compliance GDPR

Il modello distribuito è strutturalmente favorevole alla compliance:
- **AVGV è fornitore di software**, non Data Processor dei dati clinici. I dati sanitari non transitano né risiedono sui server AVGV.
- **Ogni trainer è autonomo Titolare del trattamento** dei dati dei propri clienti.
- **Non serve DPA tra trainer e AVGV** per i dati clinici (il software non li accede). Resta consigliabile un EULA che espliciti la separazione.
- **Il tunnel deve essere "data-blind"** (P2): il traffico cifrato attraversa l'edge AVGV senza che AVGV possa leggerlo. È un requisito **di compliance**, non solo di sicurezza.

Riferimento incrociato: `LEGAL_REGULATORY_REPORT.md` v1.3 — AVGV è Titolare solo per dati propri (account, fatturazione, licenze, metadata di routing), mai per dati clinici.

---

# Parte II — Architettura (come è progettato)

## 5. Principi architetturali (P1–P10)

Vincolanti; le scelte implementative sono libere purché li rispettino.

- **P1. Doppio piano di accesso.** Piano trainer (locale, LAN-only): il CRM gira su `localhost:<porta>` ed è raggiungibile dalla LAN, **mai** esposto al tunnel. Piano cliente finale (pubblico via tunnel): solo gli endpoint necessari (`/public/*`). Isolamento applicato a livello di rete **e** applicativo (middleware che rifiuta route CRM dal tunnel).
- **P2. Tunnel reverse data-blind.** Tunnel iniziato dal PC del trainer verso l'edge AVGV. Trasporta TLS end-to-end: il certificato di terminazione TLS è **sul PC del trainer**, non sull'edge. L'edge vede solo SNI/hostname (routing), IP sorgente, byte cifrati. Non decifra body né response, non logga contenuto applicativo.
- **P3. Autenticazione trainer.** Anche se il CRM è in LAN, l'accesso richiede autenticazione locale (lo studio non è sempre presidiato, il WiFi può essere accessibile a terzi). Baseline: password (bcrypt) + 2FA TOTP opzionale.
- **P4. Accesso cliente finale via token opaco.** Ogni link è un token con entropia ≥128 bit, scadenza configurabile, revocabile dal CRM, che non codifica dati personali, associato server-side a identità e risorsa. Implementazione: `ShareToken` (UUID4) in tabella SQLite locale.
- **P5. Authorization server-side su ogni route.** Ogni endpoint verifica identità, diritto alla risorsa e coerenza con il piano d'accesso. Nessuna authz su obscurity dell'URL o controlli client-side.
- **P6. Isolamento per istanza, non per riga.** Ogni trainer ha la propria istanza con SQLite isolato → l'isolamento è **fisico**, non row-level. Il codebase mantiene comunque `trainer_id` come defense-in-depth (non un conflitto: protezione aggiuntiva).
- **P7. Sessioni limitate.** Durata sessione trainer 4-12h (8h raccomandato); logout per inattività 20-60 min; re-auth per operazioni sensibili. Il token cliente finale ha vita propria.
- **P8. HTTPS ovunque, end-to-end.** Trainer↔CRM in LAN: HTTPS locale o HTTP su `localhost`. Cliente finale↔PC trainer: TLS end-to-end con certificato pubblico (Let's Encrypt) emesso e rinnovato **sul PC del trainer**. Nessuna terminazione TLS sul VPS (violerebbe P2).
- **P9. Identità di istanza e onboarding zero-touch.** Ogni istanza ha un `instance_id` univoco **pre-incluso nella licenza** (claim JWT). Determina il subdomain `<instance_id>.fitmanagerstudio.com`, l'identità del tunnel client e il certificato. Il trainer non configura nulla.
- **P10. Logging e audit.** Sul PC trainer: ogni auth/uso/revoca token/accesso ad anamnesi è loggato localmente. Sull'edge AVGV: **solo** metadata di routing (timestamp, instance_id, IP sorgente, codice risposta), mai contenuto. Retention edge limitata e documentata (~30 giorni).

## 6. Architettura logica di riferimento

```
        +--------------------------------------------------+
        |                  INTERNET PUBBLICA                |
        +---------+------------------------------+---------+
                  | HTTPS (TLS end-to-end)        |
                  v                               v
        +-----------------+              +-----------------+
        |  Cliente finale |              |  Cliente finale |
        |  di trainer A   |              |  di trainer B   |
        +--------+--------+              +--------+--------+
                 | trainerA.fitmanagerstudio.com | trainerB.fitmanagerstudio.com
                 +--------------+----------------+
                                v
              +-------------------------------+
              |     VPS EDGE (AVGV)           |
              |  - DNS wildcard *.fitmanagerstudio.com
              |  - FRP server (frps)          |
              |  - Routing SNI -> instance_id |
              |  - NO TLS termination         |
              |  - Solo metadata routing      |
              +-------+---------------+-------+
                      | tunnel cifrato | tunnel cifrato
                      v                v
        +-------------------+  +-------------------+
        |   PC Trainer A    |  |   PC Trainer B    |
        |  FitManager:      |  |  FitManager:      |
        |  - Next.js :3000  |  |  - Next.js :3000  |
        |  - frpc client    |  |  - frpc client    |
        |  - TLS termination|  |  - TLS termination|
        |  - SQLite         |  |  - SQLite         |
        |  - cert (L.E.)    |  |  - cert (L.E.)    |
        +--------+----------+  +--------+----------+
                 | LAN palestra          | LAN palestra
                 v                       v
        +------------------+    +------------------+
        | Trainer A su     |    | Trainer B su     |
        | tablet (CRM LAN) |    | tablet (CRM LAN) |
        +------------------+    +------------------+
```

**Invarianti critici:**
1. Le route CRM (`/dashboard`, `/clienti`, …) arrivate via tunnel sono **rifiutate con 404** (non 401/403: non rivelano esistenza). Solo `/public/*` passa dal tunnel.
2. Le route `/public/:token` accettano richieste dal tunnel; senza token valido sono rifiutate.
3. Il certificato TLS del subdomain è generato, conservato e usato **esclusivamente sul PC del trainer**. AVGV non possiede né custodisce chiavi private dei trainer.
4. Il VPS edge instrada per SNI hostname **senza** ispezione né decifratura del traffico applicativo.

## 7. Decisioni architetturali e opzioni tecniche

### 7.1 Decisioni prese (D1–D5)

- **D1. Tecnologia tunnel: FRP** (Fast Reverse Proxy). Maturo (40K+ stars, Go, 8+ anni), binario ~15MB bundlabile, TLS e2e via passthrough (preserva P2), brand `*.fitmanagerstudio.com`, nessun sub-processor per dati clinici (solo Hetzner UE). **Cloudflare Tunnel escluso**: termina TLS, vede il traffico, viola P2. Rathole resta alternativa futura se serve binario più leggero (~3MB).
- **D2. TLS termina sul PC del trainer.** Il VPS fa SNI routing TCP passthrough (non apre il pacchetto TLS). Certificato Let's Encrypt sul PC trainer. **ADR-011 Addendum I:** challenge HTTP-01 attraverso un proxy FRP dedicato alla sola `/.well-known/acme-challenge/`; nessuna credenziale DNS sul trainer.
- **D3. Instance ID pre-incluso nella licenza.** `instance_id` è un claim del JWT licenza (es. `"instance_id": "alessio-crociani"`). Il wildcard DNS copre tutti i trainer → **zero provisioning DNS per-istanza**.
- **D4. Separazione piani di accesso.** Middleware Next.js rileva richieste dal tunnel via hostname; route non-`/public/*` dal tunnel → 404. `/public/*` accessibili da tunnel e LAN.
- **D5. `trainer_id` resta** come defense-in-depth anche con isolamento fisico (non in conflitto con P6).

### 7.2 Confronto opzioni tunnel (storico decisionale)

| Opzione | Modello | P2 data-blind | Frizione trainer | Costo AVGV | Esito |
|---------|---------|---------------|------------------|------------|-------|
| **FRP self-hosted** | `frps` su VPS + client nell'installer | ✅ (passthrough) | Zero | ~4.5 €/mese | **SCELTO** |
| Cloudflare Tunnel | `cloudflared` + CF edge | ❌ (CF termina TLS) | Zero | Free | Escluso (viola P2) |
| Tailscale Funnel | client Tailscale + Funnel | ⚠️ sub-processor | Bassa (account TS) | Free fino a limiti | **Da dismettere** |
| ngrok | tunnel SaaS | ⚠️ | Zero | A pagamento | Escluso |
| WireGuard + proxy | VPN site-to-site | ✅ | Zero | ~4.5 €/mese | Più complesso da automatizzare |

### 7.3 Certificati Let's Encrypt dietro NAT — ADR-011 Addendum I

Il PC trainer non è raggiungibile direttamente sulla porta 80, ma FRP rende pubblicamente
raggiungibile **solo** il webroot ACME: `frps:80` instrada per host e per location
`/.well-known/acme-challenge/` a un plugin `static_file` di `frpc`. Il webroot vive sotto
`data/tunnel/`, non contiene dati applicativi e non ha Next.js/API come upstream. Ogni altro path HTTP
riceve 404 all'edge.

Questa è la soluzione R0.1.5: HTTP-01 funziona dietro NAT grazie al tunnel già stabilito, mentre
certificato e chiave privata nascono e restano sul PC trainer. DNS-01 con token Cloudflare distribuito
è respinto: `DNS Write` è restringibile alla zona, non al singolo record challenge. Wildcard cert
centralizzato gestito da AVGV resta **NON ACCETTABILE** (chiave privata sull'edge, violazione P2).

---

# Parte III — Build & Operations (come si costruisce e si opera)

## 8. Migrazione Tailscale → FRP: stato e piano a 4 fasi

### 8.1 Stato attuale (consolidato 2026-06-14)

| Fase | Stato | Sintesi |
|------|-------|---------|
| **Fase 0** — Infrastruttura AVGV | ✅ **COMPLETATA** (2026-06-02) | VPS Hetzner, hardening, frps v0.61.1, DNS wildcard, test e2e tunnel |
| **Fase 1** — Tunnel client nel prodotto | ✅ **COMPLETATA** (core 2026-06-07, frpc bundle 2026-06-09) | instance_id, tunnel_manager, tunnel_config, auto-start, route separation, health endpoint, frpc.exe nell'installer |
| **Fase 2** — TLS e2e + route hardening | 🟠 **R0.1.5 TLS IN IMPLEMENTAZIONE** · resto pianificato | cert manager Let's Encrypt HTTP-01 ristretto via FRP; token hash, inactivity timeout e pagina offline restano separati |
| **Fase 3** — Onboarding zero-touch + dismissione Tailscale | ⬜ **PIANIFICATA** | UI diagnostica, 2FA TOTP, SBOM, export GDPR, rimozione Tailscale |

> **Nota:** l'**apertura del CRM al tunnel** ("Strada B") è un workstream a sé, **approvato ma non implementato**.
> Vedi `TUNNEL_SECURITY_BOUNDARY.md`. Allo stato attuale il middleware espone **solo** `/public/*` (whitelist).

### 8.2 Gap analysis (codebase vs target)

**Già implementato:** auth JWT trainer, ShareToken portale, rate limiting auth/portale, backend bind 127.0.0.1,
Swagger gating in compiled, security headers, Bouncer pattern, bcrypt, reset password con verifica, audit trail,
soft delete.

**Stato dei gap del piano di migrazione:**

| # | Gap | Fase | Componente | Stato |
|---|-----|------|------------|-------|
| G1 | VPS edge (frps + SNI + DNS) | 0 | Infra AVGV | ✅ Fatto |
| G2 | FRP client bundlato | 1 | `api/services/tunnel_manager.py` | ✅ Fatto |
| G3 | Instance ID nella licenza JWT | 1 | `generate_license.py` + `license.py` | ✅ Fatto |
| G4 | Cert manager (Let's Encrypt HTTP-01 via FRP) | 2 / R0.1.5 | `api/services/cert_manager.py` | 🟠 Core + packaging fail-closed ✅ · edge/live ⏳ |
| G5 | Route separation middleware | 1/2 | `frontend/src/middleware.ts` | ✅ Base (whitelist) · ⬜ blacklist Strada B |
| G6 | Pagina "studio offline" sul VPS | 2 | VPS edge | ⬜ Da fare |
| G7 | Inactivity timeout sessione | 2 | `api/auth/router.py` + frontend | ⬜ Da fare |
| G8 | 2FA TOTP opzionale | 3 | `api/auth/` + frontend | ⬜ Da fare |
| G9 | Health endpoint tunnel | 1 | `api/routers/system.py` → `GET /system/tunnel-status` | ✅ Fatto |
| G10 | SBOM + audit licenze | 3 | `tools/scripts/` | ⬜ Da fare |
| G11 | Export GDPR dati cliente | 3 | `api/routers/clients.py` | ⬜ Da fare |
| ~~G12~~ | ~~Script provisioning DNS per-istanza~~ | — | — | NON NECESSARIO (wildcard DNS) |
| G13 | Token hash (ShareToken hashato) | 2 | `api/models/` + `public_portal.py` | ⬜ Da fare |

### 8.3 Fase 1 — Tunnel client nel prodotto (dettaglio componenti, COMPLETATA)

| # | Componente | File | Esito |
|---|------------|------|-------|
| 1.1 | Instance ID nella licenza | `tools/admin_scripts/generate_license.py` | claim `instance_id` nel JWT |
| 1.2 | Lettura instance_id | `api/services/license.py` | estrazione dal JWT licenza |
| 1.3 | Tunnel manager | `api/services/tunnel_manager.py` | babysitter frpc: subprocess, backoff+jitter, drain, cleanup |
| 1.4 | Config tunnel + cert | `api/services/tunnel_config.py` | TunnelConfig, frpc path, cert self-signed auto |
| 1.5 | Bundle FRP binary | `tools/build/build-installer.sh` | frpc.exe staged + safety gate (2026-06-09) |
| 1.6 | Auto-start tunnel | `api/main.py` lifespan step 6 | startup/shutdown + auto `PUBLIC_BASE_URL` |
| 1.7 | Route separation | `frontend/src/middleware.ts` | tunnel guard (hostname) + auth guard, CRM 404 dal tunnel |
| 1.8 | Health endpoint | `api/routers/system.py` | `GET /system/tunnel-status` → state/instance_id/public_url/pid (solo LAN) |
| 1.9 | Test e2e | manuale (2026-06-07) | SNI routing + P2 data-blind dimostrato via curl dal VPS |

**Config FRP client (generata automaticamente da `tunnel_manager.py`):**
```toml
serverAddr = "edge.fitmanagerstudio.com"
serverPort = 7000

[[proxies]]
name = "<instance_id>"
type = "https"
customDomains = ["<instance_id>.fitmanagerstudio.com"]
[proxies.plugin]
type = "https2http"
localAddr = "127.0.0.1:3000"
crtPath = "data/tunnel/cert.pem"
keyPath = "data/tunnel/key.pem"

[[proxies]]
name = "<instance_id>-acme-http"
type = "http"
customDomains = ["<instance_id>.fitmanagerstudio.com"]
locations = ["/.well-known/acme-challenge/"]
[proxies.plugin]
type = "static_file"
localPath = "data/tunnel/acme-webroot"
```

### 8.4 Fase 2 — TLS e2e + route hardening (R0.1.5 IN IMPLEMENTAZIONE; resto pianificato)

- **2.1 Cert manager — R0.1.5**: ✅ core locale (`api/services/cert_manager.py`) con preflight HTTP prima dell'ordine, client ACME hash/version pin, validazione SAN/tempo/key/chain, installazione con rollback, restart frpc e stop esplicito del processo ACME; ✅ packaging riproducibile tramite `fetch-lego.ps1` esplicito e `stage-acme-client.sh` fail-closed (binario + licenza); ⏳ edge/live.
- **2.2 Trasporto challenge — R0.1.5**: ✅ lato client (`frpc type=http`, `locations=["/.well-known/acme-challenge/"]`, plugin `static_file`, testato con v0.61.1); ⏳ lato edge (`frps vhostHTTPPort=80` + UFW/probe) pendente per accesso SSH interattivo. Nessun token DNS e nessun upstream applicativo su HTTP.
- **2.3 Storage — R0.1.5**: `data/tunnel/` (account ACME, webroot, cert, key), escluso da backup/export; installazione cert/key atomica dopo verifica.
- **2.4 Rinnovo automatico — R0.1.5**: ✅ scheduler opportunistico al boot + check ogni 12h, rinnovo 30gg prima della scadenza, retry 15min e ultimo certificato valido preservato; prova live resta pendente.
- **2.7 Pagina offline su VPS**: il VPS serve pagina statica "Studio offline" se il tunnel di quel subdomain è down.
- **2.9 Token hash**: SHA-256 del `ShareToken` in DB, lookup via hash, token in chiaro solo nel link.

*(Le route-separation/sessione/lockout di Fase 2 si intrecciano con Strada B → `TUNNEL_SECURITY_BOUNDARY.md`.)*

### 8.5 Fase 3 — Onboarding zero-touch + dismissione Tailscale (PIANIFICATA)

- **3.1** UI diagnostica tunnel in Impostazioni (stato, URL, certificato, uptime, prossimo rinnovo).
- **3.2** 2FA TOTP opzionale. **3.3** SBOM + audit licenze. **3.4** Export GDPR. **3.6** Guida trainer "Il tuo studio online".
- **3.7** Dismissione Tailscale: `TAILSCALE_FUNNEL_SETUP.md` archiviato in `docs/archive/` (2026-06-14). Aggiornare CLAUDE.md/pitfalls. Acceptance: una richiesta al vecchio endpoint Tailscale non deve raggiungere il CRM.

### 8.6 Metriche di successo

| Metrica | Target |
|---------|--------|
| Tempo onboarding trainer | < 5 min dal primo avvio |
| Uptime tunnel (PC acceso) | > 99% |
| Richieste CRM da tunnel bloccate | 100% |
| Rinnovo cert automatico | 100% senza intervento |
| Step manuali per il trainer | 0 (post-installazione) |

## 9. Setup VPS edge (infrastruttura AVGV — Fase 0 completata)

### 9.1 Dominio

| Proprietà | Valore |
|-----------|--------|
| Dominio | `fitmanagerstudio.com` |
| Registrar / DNS | Cloudflare (registrato 2026-06-02, ~$10.46/anno, auto-rinnovo) |
| Account | G.verardo87@gmail.com (WHOIS privacy attiva) |

**Record DNS:** `A  *  → 128.140.91.39`, **DNS only (nuvola grigia)**. Critico: se fosse Proxied (arancione),
Cloudflare intercetterebbe il TLS violando P2. Un singolo wildcard copre tutti i trainer presenti e futuri;
il routing per-trainer è gestito da FRP via `customDomains`.

```bash
$ dig qualsiasi-slug.fitmanagerstudio.com +short   # → 128.140.91.39 (wildcard)
```

### 9.2 VPS

| Proprietà | Valore |
|-----------|--------|
| Provider | Hetzner Cloud (azienda UE → GDPR) |
| Server | `fitmanagerstudio-edge`, CPX22 (2 vCPU AMD, 4 GB RAM, 80 GB SSD) |
| Location | Falkenstein, Germania (eu-central) |
| IPv4 / IPv6 | `128.140.91.39` / `2a01:4f8:c013:2f66::1` |
| OS | Ubuntu 26.04 LTS |
| Costo | ~4.50 €/mese (IVA inclusa) |

**Accesso SSH:** chiave Ed25519 (`~/.ssh/id_ed25519`, con passphrase), utente `root`.
`ssh -i ~/.ssh/id_ed25519 root@128.140.91.39`. Fingerprint salvato in `known_hosts` (protezione MITM).

### 9.3 Hardening

```bash
apt update && apt upgrade -y                         # 5.1 aggiornamenti
apt install -y ufw                                   # 5.2 firewall
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'ACME HTTP-01 via FRP'
ufw allow 443/tcp comment 'HTTPS tunnel'
ufw allow 7000/tcp comment 'FRP bind'
ufw --force enable
apt install -y fail2ban                              # 5.3 ban SSH brute force (5 tentativi/10min)
```

| Porta | Scopo | Accessibile da |
|-------|-------|----------------|
| 22/tcp | SSH admin | Qualsiasi IP (protetto da chiave) |
| 80/tcp | Solo `/.well-known/acme-challenge/` → webroot FRP per-istanza | Internet |
| 443/tcp | Traffico clienti finali → tunnel | Internet |
| 7000/tcp | Connessioni FRP client (PC trainer → VPS) | Internet |

Tutto il resto bloccato (IPv4 + IPv6). *Sicurezza futura:* restringere la 22 ai soli IP AVGV quando stabili.

### 9.4 FRP server

Installazione FRP v0.61.1 in `/opt/frp/`. Configurazione `/opt/frp/frps.toml`:

```toml
bindPort = 7000           # connessioni FRP client (PC trainer)
vhostHTTPPort = 80        # solo challenge ACME HTTP-01, path ristretto dal proxy client
vhostHTTPSPort = 443      # traffico HTTPS clienti finali — SNI routing (no TLS termination)

[webServer]
addr = "127.0.0.1"        # dashboard admin solo locale (via SSH tunnel)
port = 7500
user = "admin"
password = "<password manager AVGV>"

[log]
to = "/var/log/frps/frps.log"
level = "info"
maxDays = 30              # retention log 30gg
```

Servizio systemd `frps.service` (`Restart=always`, `RestartSec=5`, `After=network.target`, `enabled`).
Gestione: `systemctl status|restart|stop frps`, `journalctl -u frps -f`.
Dashboard admin via SSH tunnel: `ssh -L 7500:127.0.0.1:7500 -i ~/.ssh/id_ed25519 root@128.140.91.39`.

### 9.5 Test e2e Fase 0 (2026-06-02)

FRP client di test (`tcp`, porta 8080) dal PC dev Windows → frps sul VPS → `localhost:3001`. `curl` dal VPS
su `127.0.0.1:8080` → **HTTP 307** (redirect al login FitManager). Il traffico ha percorso VPS (DE) → PC (IT)
attraverso il tunnel, in modo trasparente. *(Test connettività di base; il test TLS e2e — `https`, porta 443,
cert Let's Encrypt — è rimandato a Fase 2.)* Porta 8080 rimossa dal firewall a fine test.

## 10. Flusso di una richiesta (end-to-end)

1. Il cliente apre `https://alessio-crociani.fitmanagerstudio.com/public/workout/abc123`.
2. Il browser risolve via DNS → `128.140.91.39` (wildcard).
3. Handshake TLS verso `128.140.91.39:443`.
4. `frps` legge l'**SNI hostname** dall'handshake: `alessio-crociani.fitmanagerstudio.com`.
5. `frps` trova il client con `customDomains = [...]` corrispondente.
6. `frps` inoltra i byte TLS cifrati (**senza decifrare**) attraverso il tunnel al PC del trainer.
7. `frpc` sul PC riceve, termina TLS e passa al Next.js locale (porta 3000).
8. Next.js risponde; la risposta torna indietro, sempre cifrata.

**In nessun punto AVGV legge il contenuto.** Il VPS vede solo: SNI hostname (in chiaro nell'handshake), IP del
cliente, quantità di byte. Nient'altro. → Dimostrazione e test probatorio: `TUNNEL_SECURITY_BOUNDARY.md` §P2.

## 11. Operations AVGV (post-vendita)

### 11.1 Ruolo permanente
Il VPS edge è il centralino che smista le richieste verso i PC dei trainer. Deve restare acceso 24/7 finché
esiste almeno un trainer attivo. VPS down = **tutti** i link pubblici di **tutti** i trainer offline.

### 11.2 Attività ricorrenti

| Attività | Frequenza | Sforzo |
|----------|-----------|--------|
| Pagamento VPS / dominio | Mensile / annuale | Zero (addebito/rinnovo automatico) |
| `apt update && apt upgrade -y` (riavvio se kernel) | Mensile | ~5 min (FRP riparte da systemd) |
| Aggiornamento FRP (se critico) | Raro | ~10 min |
| Monitoraggio uptime | Continuo | Zero (automatizzabile, Uptime Kuma) |

**Per-trainer (solo alla vendita):** generare licenza con `instance_id` (`generate_license.py sign --instance-id <slug>`)
+ annotare in `docs/operations/DEPLOYMENTS.md`. **Nessun** record DNS, **nessuna** config FRP per nuovo trainer.

### 11.3 Costi (fissi, non scalano con i trainer)

| Trainer attivi | Costo VPS | Per trainer |
|----------------|-----------|-------------|
| 1 | 4.50 €/mese | 4.50 € |
| 10 | 4.50 €/mese | 0.45 € |
| 50 | 4.50 €/mese | 0.09 € |
| 100+ | ~9 €/mese (upgrade CX32) | ~0.09 € |

Totale annuo ~63.50 € (dominio + VPS), coperto già dal primo abbonamento PRO (79 €/anno). Upgrade a CX32
solo oltre ~100 trainer simultanei (FRP gestisce connessioni TCP leggere).

### 11.4 Manutenzione e verifica rapida

```bash
systemctl status frps        # FRP attivo?
ufw status                   # Firewall attivo?
fail2ban-client status       # Fail2ban attivo?
df -h / ; du -sh /var/log/frps/   # Spazio disco / log
```

Aggiornamento FRP: `systemctl stop frps` → scarica nuova release in `/opt/frp/` → sostituisci `frps`/`frpc` →
`systemctl start frps`. Log: rotazione automatica (`maxDays = 30`).

### 11.5 Disaster recovery

- **Server irrecuperabile:** nuovo VPS (stesse specifiche) → ripeti §9.3-9.4 → aggiorna il record DNS wildcard. I FRP client si riconnettono automaticamente (se configurati con hostname `edge.fitmanagerstudio.com`, non IP). Ripristino stimato 30-60 min.
- **Dominio:** registrato su Cloudflare con auto-rinnovo. Mantenere credenziali account nel password manager.

### 11.6 Credenziali (registro AVGV)

| Servizio | Host | Username |
|----------|------|----------|
| Cloudflare | dash.cloudflare.com | G.verardo87@gmail.com |
| Hetzner Cloud | console.hetzner.cloud | G.verardo87@gmail.com |
| VPS SSH | 128.140.91.39:22 | root (chiave Ed25519 + passphrase) |
| FRP Dashboard | 127.0.0.1:7500 (via SSH tunnel) | admin |

> **IMPORTANTE:** le password operative (dashboard FRP) **non** sono archiviate in alcun file
> versionato. R0.1.5 non usa credenziali DNS; account ACME e chiavi private restano nel solo
> `data/tunnel/` locale, escluso da Git e da export/backup.

## 12. Rischi residui e aree aperte

| Rischio | Mitigazione | Stato |
|---------|-------------|-------|
| Internet palestra instabile | Documentare requisito minimo; cache offline form anamnesi | Da valutare |
| Trainer chiude il PC durante compilazione | Pagina "studio offline" (Fase 2.7) | Pianificato |
| VPS edge SPOF per tutti i trainer | Edge ridondato multi-region + failover DNS | Fase 2+ |
| FRP bloccato da reti aziendali restrittive | FRP via HTTPS porta 443 (raramente bloccata); websocket transport | Mitigato |
| Cert non rinnovato (PC spento a scadenza) | Check opportunistico al boot + ogni 12h; rinnovo entro 30gg; ultimo cert valido preservato | R0.1.5 |
| Porta 80 usata per raggiungere il CRM | FRP `locations` solo challenge + webroot statico dedicato; nessun upstream Next/API; probe 404 fuori path | R0.1.5 |
| Compromissione PC trainer (malware) | Fuori scope diretto; best practice in onboarding | Documentare |
| Conformità Art. 9 su transito via edge | P2 data-blind + audit + dossier tcpdump | Dimostrato (routing) |

## 13. Riferimenti

- `ARCHITECTURE.md` (root) — overview di sistema, 3 attori
- `TUNNEL_SECURITY_BOUNDARY.md` — confine di sicurezza, apertura CRM (Strada B), acceptance criteria
- `SECURITY_MODEL.md` — threat model e livelli di protezione
- `LEGAL_REGULATORY_REPORT.md` v1.3 — compliance GDPR
- `docs/archive/TAILSCALE_FUNNEL_SETUP.md` — setup legacy (sostituito da FRP)
- FRP: https://github.com/fatedier/frp · Let's Encrypt HTTP-01: https://letsencrypt.org/docs/challenge-types/#http-01-challenge · lego webroot: https://go-acme.github.io/lego/obtain/http01/
- Cloudflare API token permissions (DNS Write = Zone): https://developers.cloudflare.com/fundamentals/api/reference/permissions/
- GDPR Reg. UE 2016/679 — Art. 5, 9, 28, 32 · ACME RFC 8555

## 14. Changelog (consolidato)

| Versione | Data | Modifiche |
|----------|------|-----------|
| 1.0 (ARCHITECTURE_OVERVIEW) | 2026-06-02 | Mappa narrata: problema, tunnel/centralino, VPS, 3 attori, fasi |
| 2.0 (CRM_ACCESS_ARCHITECTURE) | 2026-04-23 | Blueprint: modello distribuito, P1-P10, threat model, criteri accettazione |
| 1.0 (TUNNEL_MIGRATION_STRATEGY) | 2026-06-01 | Strategia Tailscale→FRP: D1-D5, gap analysis, 4 fasi |
| 1.0 (VPS_EDGE_SETUP) | 2026-06-02 | Fase 0: dominio, VPS, hardening, frps, DNS wildcard, test e2e |
| **3.0** | **2026-06-14** | **Consolidamento dei 4 documenti in uno (design + build + ops). Stati di fase allineati alla realtà del codice: Fase 1 completata (incl. frpc bundle + health endpoint `GET /system/tunnel-status`), Fase 2/3 pianificate. Threat model delegato a SECURITY_MODEL; 3 attori delegati ad ARCHITECTURE.md root; acceptance/Strada B delegati a TUNNEL_SECURITY_BOUNDARY.** |
| **3.1** | **2026-07-24** | **ADR-011 Addendum I/R0.1.5: DNS-01 distribuito sostituito da HTTP-01 ristretto via FRP; zero credenziali DNS sui trainer, webroot ACME dedicato, porta 80 non applicativa, P2 e terminazione TLS locale invariati. Corretto anche l'esempio runtime reale `https2http`.** |
