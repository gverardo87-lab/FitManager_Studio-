# TUNNEL_MIGRATION_STRATEGY.md

**Progetto:** FitManager
**Versione:** 1.0
**Data:** 2026-06-01
**Stato:** Approvato per esecuzione
**Prerequisito:** `CRM_ACCESS_ARCHITECTURE.md` v2.0 (blueprint architetturale)
**Obiettivo:** Migrare da Tailscale Funnel a tunnel FRP self-hosted con dominio `*.fitmanagerstudio.com`

---

## 1. Contesto e motivazione

### Stato attuale (Tailscale Funnel)

```
Trainer installa FitManager
  -> Trainer installa Tailscale (software separato)
    -> Trainer configura account Tailscale
      -> Trainer abilita Funnel (porta 3000, NON 8000)
        -> URL: qualcosa.ts.net (non brandizzato)
```

**Problemi:**
- 4 step manuali con pitfall documentati (porta sbagliata = `{"detail":"Not Found"}`)
- URL non brandizzato (`*.ts.net`)
- Tailscale e' sub-processor (GDPR)
- Il tunnel espone TUTTO il frontend (nessuna separazione CRM vs pubblico)
- Non scalabile: ogni trainer ha bisogno di un account Tailscale

### Stato target (FRP self-hosted)

```
Trainer installa FitManager
  -> Tutto automatico (tunnel, DNS, certificato TLS)
    -> URL: trainer-slug.fitmanagerstudio.com (brandizzato)
      -> Solo route /public/* esposte (CRM inaccessibile da Internet)
```

---

## 2. Decisioni architetturali prese

### D1. Tecnologia tunnel: FRP

**Scelta: FRP (Fast Reverse Proxy)**

| Criterio | FRP | Rationale |
|----------|-----|-----------|
| Maturita' | 40K+ stars, Go, 8+ anni | Affidabile per produzione |
| Binario | ~15MB, cross-platform | Bundlabile in Nuitka |
| TLS e2e | TCP proxy mode (passthrough) | Preserva P2 (data-blind) |
| Brand | `*.fitmanagerstudio.com` | Dominio AVGV |
| GDPR | Nessun sub-processor per dati clinici | Solo VPS provider (Hetzner UE) |

Cloudflare Tunnel escluso: viola P2 (CF termina TLS, vede il traffico).
Rathole considerato come alternativa futura se serve binario piu' leggero (~3MB).

### D2. TLS: termina sul PC del trainer

- VPS edge fa SNI routing TCP passthrough (non apre il pacchetto TLS)
- Certificato Let's Encrypt generato e rinnovato sul PC del trainer
- Challenge: DNS-01 (unica che funziona dietro NAT)
- Credenziali DNS scoped distribuite via licenza/onboarding

### D3. Instance ID: pre-incluso nella licenza

- `instance_id` e' un nuovo claim nel JWT della licenza (es. `"instance_id": "alessio-crociani"`)
- Al primo avvio, FitManager legge l'instance_id dalla licenza
- AVGV crea il record DNS `instance_id.fitmanagerstudio.com -> IP VPS` al momento della generazione licenza
- Nessuna chiamata di rete al primo avvio per registrazione (solo per tunnel + cert)

### D4. Separazione piani di accesso

- Middleware Next.js ispeziona header custom iniettato da FRP (`X-FRP-Tunnel: true`)
- Route non `/public/*` + header tunnel presente -> 404
- Route `/public/*` accessibili da tunnel E da LAN (per testing)
- CRM (`/dashboard`, `/clienti`, ecc.) -> solo LAN

### D5. trainer_id resta

Il codebase mantiene `trainer_id` come defense-in-depth anche se l'isolamento e' fisico per istanza. Non e' un conflitto con P6 del blueprint -- e' una protezione aggiuntiva.

---

## 3. Gap analysis: codebase attuale vs target

### Gia' implementato (nessun intervento)

| Requisito | Stato |
|-----------|-------|
| Auth JWT trainer | api/routers/auth.py |
| Token opachi (share_token) per portale | api/routers/portal_*.py |
| Rate limiting auth (5/min, 20/h) | api/services/rate_limiter.py |
| Rate limiting portale (30/min, 120/h) | api/services/rate_limiter.py |
| Backend bind 127.0.0.1 in prod | api/entry_point.py |
| Swagger/Redoc disabilitati in compiled | api/main.py |
| Security headers (HSTS, X-Frame, etc) | api/main.py + frontend middleware |
| Bouncer pattern ownership | Tutti gli endpoint |
| Password bcrypt | api/routers/auth.py |
| Reset password con verifica | api/routers/auth.py |
| Audit trail (log_audit) | api/services/audit.py |
| Soft delete | Tutte le tabelle business |

### Da implementare

| # | Gap | Priorita' | Fase | Componente |
|---|-----|-----------|------|------------|
| G1 | VPS edge (FRP server + Caddy SNI + DNS) | Critica | 0 | Infrastruttura AVGV |
| G2 | FRP client bundlato nel build Nuitka | Critica | 1 | api/services/tunnel_manager.py (nuovo) |
| G3 | Instance ID nella licenza JWT | Critica | 1 | tools/admin_scripts/generate_license.py + api/services/license.py |
| G4 | Cert manager (Let's Encrypt DNS-01) | Critica | 2 | api/services/cert_manager.py (nuovo) |
| G5 | Route separation middleware | Critica | 2 | frontend/src/middleware.ts |
| G6 | Pagina "studio offline" | Media | 2 | VPS edge: pagina statica quando tunnel down |
| G7 | Inactivity timeout sessione | Media | 2 | api/routers/auth.py + frontend |
| G8 | 2FA TOTP opzionale | Bassa (POC) | 3 | api/routers/auth.py + frontend |
| G9 | UI diagnostica tunnel | Media | 3 | frontend impostazioni |
| G10 | SBOM + audit licenze | Media | 3 | tools/scripts/ |
| G11 | Export GDPR dati cliente | Media | 3 | api/routers/clients.py |
| G12 | Script provisioning AVGV-side | Media | 1 | tools/admin_scripts/provision_instance.py (nuovo) |
| G13 | Token hash (share_token hashato, non chiaro) | Media | 2 | api/models/ + api/routers/portal_*.py |

---

## 4. Piano di esecuzione: 4 fasi

### Fase 0 -- Infrastruttura AVGV (esterna al codebase)

**Obiettivo:** VPS edge funzionante, test manuale con FRP client.

**Prerequisiti:**
- Dominio `fitmanagerstudio.com` acquistato (verificare stato)
- Account Hetzner (o provider VPS equivalente UE)

**Attivita':**

| # | Task | Dettaglio | Output |
|---|------|-----------|--------|
| 0.1 | Provisioning VPS | Hetzner CX22 (2 vCPU, 4GB RAM, 40GB SSD, ~4.5 euro/mese) | IP pubblico |
| 0.2 | Hardening VPS | SSH key-only, fail2ban, ufw (443+frps port), unattended-upgrades | VPS sicuro |
| 0.3 | DNS setup | `fitmanagerstudio.com` + wildcard `*.fitmanagerstudio.com` -> IP VPS | DNS funzionante |
| 0.4 | FRP server | Deploy `frps` con config TCP passthrough su porta 443 | frps in ascolto |
| 0.5 | SNI routing | Caddy o HAProxy in TCP mode per routing SNI -> FRP | Routing funzionante |
| 0.6 | Pagina offline | Pagina statica per subdomain senza tunnel attivo | "Studio offline" |
| 0.7 | Monitoring | Uptime Kuma per frps + VPS | Alert automatici |
| 0.8 | Test manuale | FRP client da PC dev -> tunnel funzionante -> URL raggiungibile | Validazione e2e |

**Config FRP server (indicativa):**

```toml
# frps.toml
bindPort = 7000           # porta per connessioni FRP client
vhostHTTPSPort = 443      # porta per traffico HTTPS (TCP passthrough)

[webServer]
addr = "127.0.0.1"
port = 7500               # dashboard admin (solo locale)
user = "admin"
password = "<strong-password>"

[log]
to = "/var/log/frps/frps.log"
level = "info"
maxDays = 30
```

**Deliverable Fase 0:** `test.fitmanagerstudio.com` raggiungibile da Internet, traffico forwarded al PC dev via tunnel FRP.

---

### Fase 1 -- Tunnel client nel prodotto

**Obiettivo:** Trainer installa -> tunnel si apre automaticamente -> `slug.fitmanagerstudio.com` raggiungibile.

**Attivita':**

| # | Task | File | Dettaglio |
|---|------|------|-----------|
| 1.1 | Instance ID nella licenza | `tools/admin_scripts/generate_license.py` | Nuovo claim `instance_id` nel JWT. Generato da AVGV al momento della vendita. |
| 1.2 | Lettura instance_id | `api/services/license.py` | Estrarre `instance_id` dal JWT licenza. Esporre come property. |
| 1.3 | Script provisioning | `tools/admin_scripts/provision_instance.py` | Script AVGV-side: crea record DNS, genera config FRP client, prepara credenziali DNS-01. Input: instance_id. |
| 1.4 | Tunnel manager | `api/services/tunnel_manager.py` (nuovo) | Gestisce ciclo di vita FRP client: start, stop, reconnect, health check. Processo figlio di entry_point. |
| 1.5 | Config FRP client | `api/services/tunnel_manager.py` | Genera `frpc.toml` da instance_id + server address. Salva in `data/tunnel/`. |
| 1.6 | Bundle FRP binary | `tools/build/build-release.sh` | Include `frpc.exe` (Windows) nel build Nuitka come risorsa. |
| 1.7 | Auto-start tunnel | `api/entry_point.py` | Al boot, se licenza valida e instance_id presente, avvia tunnel_manager. |
| 1.8 | Health endpoint tunnel | `api/routers/settings.py` (o nuovo) | GET /tunnel/status -> { connected, url, uptime }. Solo da LAN. |
| 1.9 | Test e2e | `tests/` | Test: tunnel si connette, URL raggiungibile, reconnect dopo interruzione. |

**Config FRP client (generata automaticamente):**

```toml
# frpc.toml (generato da tunnel_manager.py)
serverAddr = "edge.fitmanagerstudio.com"
serverPort = 7000

[[proxies]]
name = "<instance_id>"
type = "https"
customDomains = ["<instance_id>.fitmanagerstudio.com"]
[proxies.plugin]
type = "https2https"
localAddr = "127.0.0.1:3000"
crtPath = "data/tunnel/cert.pem"
keyPath = "data/tunnel/key.pem"
```

**Deliverable Fase 1:** Installazione con licenza contenente instance_id -> tunnel automatico -> `slug.fitmanagerstudio.com` raggiunge il frontend.

---

### Fase 2 -- TLS e2e + route separation

**Obiettivo:** HTTPS valido con cert sul PC trainer, CRM inaccessibile da Internet.

**Attivita':**

| # | Task | File | Dettaglio |
|---|------|------|-----------|
| 2.1 | Cert manager | `api/services/cert_manager.py` (nuovo) | Genera/rinnova certificato Let's Encrypt via DNS-01. Usa libreria acme Python o shell-out a acme.sh bundlato. |
| 2.2 | Credenziali DNS scoped | `tools/admin_scripts/provision_instance.py` | Genera API token DNS con scope limitato a `_acme-challenge.<instance_id>.fitmanagerstudio.com`. |
| 2.3 | Storage credenziali | `data/tunnel/` | Credenziali DNS-01, cert, key in `data/tunnel/`. Esclusi da backup/export. |
| 2.4 | Rinnovo automatico | `api/services/cert_manager.py` | Scheduler: check scadenza ogni 12h, rinnovo 30gg prima della scadenza. |
| 2.5 | Route separation middleware | `frontend/src/middleware.ts` | Se header `X-Forwarded-For` presente (o header custom FRP) E route non e' `/public/*` -> redirect a 404. |
| 2.6 | Test isolamento | `tests/` | Richiesta a `/dashboard` via tunnel -> 404. Richiesta a `/public/workout/:token` via tunnel -> 200. |
| 2.7 | Pagina offline su VPS | Infra AVGV | Caddy/HAProxy serve pagina statica "Studio offline, riprova piu' tardi" se tunnel down per quel subdomain. |
| 2.8 | Inactivity timeout | `api/routers/auth.py` | Campo `last_activity` nella sessione. Middleware check: se > 30min -> 401. |
| 2.9 | Token hash | `api/models/` + `api/routers/portal_*.py` | Hash SHA-256 del share_token in DB. Lookup via hash. Token in chiaro solo nel link. |

**Deliverable Fase 2:** TLS e2e verificato (AVGV non vede contenuto), CRM invisibile da Internet, sessioni con timeout.

---

### Fase 3 -- Onboarding zero-touch + dismissione Tailscale

**Obiettivo:** Flusso completo dal primo avvio al link funzionante. Tailscale rimosso dal workflow.

**Attivita':**

| # | Task | File | Dettaglio |
|---|------|------|-----------|
| 3.1 | UI diagnostica tunnel | `frontend/src/app/(dashboard)/impostazioni/` | Sezione "Connessione pubblica": stato tunnel, URL, certificato, uptime, prossimo rinnovo. |
| 3.2 | 2FA TOTP opzionale | `api/routers/auth.py` + frontend | Setup TOTP con QR code. Opzionale in POC, raccomandato. |
| 3.3 | SBOM + audit licenze | `tools/scripts/generate-sbom.sh` | `pip-licenses` + `cyclonedx-py`. Output in `docs/compliance/SBOM.json` + `LICENSES.txt`. |
| 3.4 | Export GDPR | `api/routers/clients.py` | Endpoint: GET /clients/:id/export -> ZIP con tutti i dati del cliente in JSON. |
| 3.5 | Migrazione Alessio | Manuale | Generare licenza con instance_id, provisioning DNS, test, cutover da Tailscale. |
| 3.6 | Documentazione trainer | `docs/operations/` | Guida: "Il tuo studio online" (come funziona, cosa succede se il PC e' spento, troubleshooting). |
| 3.7 | Rimozione Tailscale docs | `docs/technical/TAILSCALE_FUNNEL_SETUP.md` | Archiviare in `docs/archive/`. Aggiornare CLAUDE.md e pitfalls. |
| 3.8 | Test acceptance completo | `tests/` | Verifica tutti i criteri S7 del CRM_ACCESS_ARCHITECTURE. |

**Deliverable Fase 3:** Primo avvio -> online in < 5 min. Tailscale dismesso. Criteri di accettazione S7 tutti verdi.

---

## 5. Mapping componenti codebase

| Componente blueprint | File nel codebase | Tipo |
|---------------------|-------------------|------|
| Tunnel client FRP | `api/services/tunnel_manager.py` | Nuovo |
| Gestione certificati LE | `api/services/cert_manager.py` | Nuovo |
| Instance identity | `api/services/license.py` (estensione) | Modifica |
| Instance provisioning | `tools/admin_scripts/provision_instance.py` | Nuovo |
| License con instance_id | `tools/admin_scripts/generate_license.py` | Modifica |
| Route separation | `frontend/src/middleware.ts` | Modifica |
| FRP binary bundle | `tools/build/build-release.sh` | Modifica |
| Auto-start tunnel | `api/entry_point.py` | Modifica |
| Tunnel health API | `api/routers/settings.py` o nuovo | Modifica/Nuovo |
| UI diagnostica | `frontend/src/app/(dashboard)/impostazioni/` | Modifica |
| Token hash | `api/models/` + `api/routers/portal_*.py` | Modifica |
| SBOM generator | `tools/scripts/generate-sbom.sh` | Nuovo |
| Export GDPR | `api/routers/clients.py` | Modifica |

---

## 6. Rischi e mitigazioni per l'implementazione

| Rischio | Probabilita' | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| FRP client non si connette da reti aziendali restrittive | Media | Alto | FRP supporta websocket transport (fallback su porta 443) |
| DNS propagation lenta al provisioning | Bassa | Basso | Pre-provisioning DNS 24h prima della consegna licenza |
| Let's Encrypt rate limit (50 cert/settimana per dominio) | Bassa (POC) | Medio | Wildcard cert come fallback; staging env per test |
| Nuitka bundle size cresce con FRP binary (~15MB) | Certa | Basso | Accettabile; installer gia' ~100MB+ |
| PC trainer con firewall che blocca connessioni uscenti | Bassa | Alto | FRP via HTTPS su porta 443 (raramente bloccata) |
| Cert renewal fallisce (PC spento a scadenza) | Media | Medio | Retry al riavvio; grace period 30gg; notifica trainer |

---

## 7. Metriche di successo

| Metrica | Target | Come misurarla |
|---------|--------|----------------|
| Tempo onboarding trainer | < 5 min dal primo avvio | Cronometro su test reale |
| Uptime tunnel per trainer attivo | > 99% (quando PC acceso) | Log FRP server |
| Richieste CRM da tunnel bloccate | 100% | Test automatizzato |
| Rinnovo cert automatico | 100% senza intervento | Log cert_manager |
| Step manuali per il trainer | 0 (post-installazione) | Checklist |

---

## 8. Ordine di esecuzione consigliato

```
Fase 0 (infra)         [1-2 giorni lavoro AVGV]
  |
  v
Fase 1 (tunnel client) [2-3 giorni dev]
  |
  v
Fase 2 (TLS + routing) [2-3 giorni dev]
  |
  v
Fase 3 (polish + dismiss) [1-2 giorni dev]
```

Le fasi sono sequenziali: ogni fase dipende dalla precedente.
Fase 0 e' prerequisito infrastrutturale e puo' essere fatta in parallelo con altri sviluppi.

---

## 9. Riferimenti

- `docs/technical/CRM_ACCESS_ARCHITECTURE.md` v2.0 — Blueprint architetturale
- `docs/business/LEGAL_REGULATORY_REPORT.md` v1.3 — Compliance e GDPR
- `docs/technical/SECURITY_MODEL.md` — Threat model e livelli protezione
- `docs/technical/TAILSCALE_FUNNEL_SETUP.md` — Setup attuale (da archiviare)
- FRP documentation: https://github.com/fatedier/frp
- Let's Encrypt DNS-01: https://letsencrypt.org/docs/challenge-types/#dns-01-challenge
