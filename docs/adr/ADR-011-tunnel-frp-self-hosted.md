# ADR-011 — Migrazione a Tunnel FRP self-hosted

**Data**: 2026-06-09
**Stato**: Accettata
**Autore**: Giacomo Verardo + Claude
**Decisione approvata**: 2026-06-01 (`TUNNEL_MIGRATION_STRATEGY.md` v1.0) — Fase 1 core completata e shippata in v1.0.10, testata su 2 PC il 2026-06-09.

## Contesto

L'accesso pubblico al portale dell'atleta (link anamnesi/scheda tokenizzati) era erogato via **Tailscale Funnel**. Il modello presentava cinque problemi strutturali:

- **Onboarding manuale a 4 step** con pitfall documentati (porta 3000 vs 8000 → `{"detail":"Not Found"}`): il trainer installa Tailscale separatamente, configura l'account, abilita Funnel sulla porta giusta.
- **URL non brandizzato** (`*.ts.net`).
- **Tailscale come sub-processor GDPR** sul percorso del dato.
- **Nessuna separazione dei piani**: il Funnel esponeva l'intero frontend, CRM incluso.
- **Non scalabile**: ogni trainer richiede un account Tailscale.

Lo stato target: il trainer installa FitManager, e tunnel + DNS + (futuro) certificato TLS si configurano automaticamente, su URL brandizzato `slug.fitmanagerstudio.com`, con il CRM invisibile da Internet.

## Decision Drivers

- **Privacy-first / P2 data-blind**: il dato personale dell'atleta non deve essere leggibile da alcun intermediario sul percorso.
- **Zero-touch onboarding**: zero step manuali per il trainer dopo l'installazione (vincolo per uno sviluppatore solo con 10 Fondatori al POC).
- **Brand**: dominio proprietario AVGV.
- **GDPR**: minimizzare i sub-processor sul dato clinico.
- **Bundlabilità**: il client tunnel deve poter entrare nel build Nuitka.

## Alternative considerate

| Alternativa | Pro | Contro | Decisione |
|-------------|-----|--------|-----------|
| **Tailscale Funnel** (status quo) | Già funzionante | 4 step manuali, URL non brand, sub-processor GDPR, espone tutto il frontend, non scalabile | Scartata (dismissione pianificata Fase 3) |
| **Cloudflare Tunnel** | Maturo, gratuito | CF **termina il TLS** → vede il traffico → **viola P2** | Scartata (incompatibile con data-blind) |
| **FRP (Fast Reverse Proxy)** | 40K★, Go, 8+ anni, binario ~15MB cross-platform, TCP/SNI passthrough preserva P2, self-hosted su VPS UE | Richiede VPS proprio (Hetzner) | **Scelta** |
| **Rathole** | Binario più leggero (~3MB) | Meno maturo | Riserva futura se serve ridurre il bundle |

## Decisione

Migrare a **tunnel FRP self-hosted** con dominio `*.fitmanagerstudio.com`. Cinque decisioni architetturali:

- **D1 — Tecnologia: FRP.** `frps` sul VPS edge Hetzner (`edge.fitmanagerstudio.com`, CPX22), `frpc` bundlato nel prodotto.
- **D2 — TLS termina sul PC del trainer.** Il VPS fa **SNI routing in passthrough** (legge il nome dominio in chiaro nel ClientHello, non apre il pacchetto cifrato). `frpc` termina il TLS lato PC e inoltra a `localhost:3000` (plugin `https2http`). Il VPS non possiede la chiave privata del trainer → **P2 data-blind preservata** (dimostrato e2e il 2026-06-07). Fase 1: cert self-signed; Fase 2: Let's Encrypt via DNS-01.
- **D3 — Instance ID nella licenza.** Nuovo claim `instance_id` nel JWT della licenza determina il sottodominio. Il **wildcard DNS** `*.fitmanagerstudio.com → IP VPS` copre tutti i trainer: **zero provisioning DNS per-istanza** (gap G12 eliminato).
- **D4 — Separazione dei piani di accesso.** Il middleware Next.js rileva le richieste dal tunnel via hostname: route non `/public/*` → **404** (non 403, non rivela esistenza). Il CRM è accessibile solo da LAN.
- **D5 — `trainer_id` resta** come defense-in-depth anche se l'isolamento è fisico per-istanza.

## File impattati

| File | Tipo | Ruolo |
|------|------|-------|
| `api/services/tunnel_manager.py` | NUOVO | Babysitter frpc: subprocess, backoff+jitter, drain output, atexit cleanup |
| `api/services/tunnel_config.py` | NUOVO | TunnelConfig, risoluzione path frpc, cert self-signed auto-generato |
| `api/services/license.py` | Modifica | Estrazione claim `instance_id` dal JWT |
| `api/main.py` | Modifica | Lifespan step 6: auto-start tunnel + auto-set `PUBLIC_BASE_URL` |
| `frontend/src/middleware.ts` | Modifica | Tunnel guard (hostname) + auth guard → CRM 404 dal tunnel |
| `tools/admin_scripts/generate_license.py` | Modifica | Flag `--instance-id <slug>` nel comando `sign` |
| `tools/build/build-installer.sh` | Modifica | Staging di `frpc.exe` + safety gate |

## Conseguenze

### Positive
- **Onboarding zero-touch**: installazione identica per tutti; tunnel + URL automatici dalla licenza.
- **URL brandizzato** `slug.fitmanagerstudio.com`.
- **P2 data-blind preservata**: il VPS instrada senza decifrare (dimostrato e2e).
- **CRM invisibile da Internet**: route separation a 404.
- **GDPR**: nessun sub-processor sul dato clinico (solo VPS provider UE).
- **Aggiornamenti centrali del routing**: una clip caricata = visibile a tutti (rilevante per la futura media cloud, vedi ADR-012 riservato).

### Negative
- **Dipendenza dal PC acceso**: l'accesso dal tablet richiede il PC del trainer online (vincolo di prodotto noto, da comunicare ai trainer POC).
- **Cert renewal** (Fase 2): la gestione Let's Encrypt DNS-01 introduce complessità (mitigata da grace period + retry al riavvio).
- **Bundle +~15MB** per il binario frpc (accettabile su installer ~100MB).
- **VPS da mantenere** (hardening, monitoring, costo ~4.5€/mese).

### Follow-up (stato fasi)
- **Fase 0** (VPS, frps, DNS wildcard): COMPLETATA.
- **Fase 1 core** (instance_id, tunnel_manager, auto-start, route separation, test e2e, bundle frpc): COMPLETATA (v1.0.10).
- **Fase 2** (TLS e2e Let's Encrypt DNS-01, pagina offline, token hash, inactivity timeout): DA FARE.
- **Fase 3** (onboarding zero-touch completo, UI diagnostica, **dismissione Tailscale**): DA FARE.

## Rollback / Exit Strategy

FRP è **additivo**: finché la Fase 3 non dismette Tailscale, entrambi i percorsi terminano su Next.js:3000 e `get_current_trainer()` protegge entrambi. In caso di problema sul tunnel FRP, il portale resta erogabile via Tailscale Funnel fino alla dismissione pianificata. Il binario frpc e il lifespan step 6 sono disattivabili senza toccare il resto del prodotto.

## Supersedes / Superseded By

- **Supersedes**: l'approccio Tailscale Funnel (`docs/technical/TAILSCALE_FUNNEL_SETUP.md`, da archiviare in Fase 3).
- **Superseded by**: —

## Riferimenti

- `docs/technical/TUNNEL_MIGRATION_STRATEGY.md` — strategia completa (4 fasi, gap analysis G1-G13)
- `docs/technical/TUNNEL_SECURITY_BOUNDARY.md` — confine di sicurezza, P2 data-blind (dimostrato e2e)
- `docs/technical/CRM_ACCESS_ARCHITECTURE.md` — blueprint architetturale v2.0
- `docs/learning/BUILD_LOG.md` — diario cronologico (Fase 0 → Fase 1 Step 1-8)
- `docs/adr/ADR-007-anti-reverse-engineering.md` — hardening bundle (frpc bundlato in Nuitka)
