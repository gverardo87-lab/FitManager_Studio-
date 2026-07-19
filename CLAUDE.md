# CLAUDE.md — FitManager AI Studio

CRM locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA.
Dati sul PC del professionista, zero cloud obbligatorio, privacy-first.

> **Contratto operativo comune:** `AGENTS.md` e' la fonte autorevole per delivery loop, guardrail,
> quality gate e lifecycle documentale. Il workflow condiviso Claude Code + Codex e'
> `docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md`. Questo file resta l'entry point e il
> contesto specifico di Claude Code; i link sono additivi e non rimuovono il comportamento esistente.

## Stack

```
Python 3.12 + FastAPI + SQLModel + SQLite (WAL)     → api/
Next.js 16 + React 19 + TypeScript 5 + shadcn/ui    → frontend/
Langchain + Ollama (moduli AI dormenti)              → core/
```

Distribuzione: Nuitka (Python→C→nativo) + Next.js standalone + Inno Setup (Windows installer).
Fallback build: PyInstaller (`fitmanager.spec` preservato per rollback).

## Modello di business (contesto per lo sviluppo)

```
Licenza software: €249 una tantum (perpetua)
FitManager Box:   €449 una tantum (Raspberry Pi + licenza)
Assistenza PRO:   €79/anno (aggiornamenti, nuovi esercizi/alimenti, template, supporto)
Inner Circle:     €249/anno (PRO + masterclass, webinar, mastermind, certificazione)
Mentorship:       €499-599/anno (futuro Anno 3+, max 15-20 membri)
```

4 livelli community: Base (gratuita) → PRO → Inner Circle → Mentorship.
PRO = solo aggiornamenti software e supporto. Masterclass e formazione = esclusivi Inner Circle.
SSoT numeri e proiezioni: `docs/business/BUSINESS_PLAN.md` (v4.3). Strategia operativa: `docs/business/STRATEGY_PLAN.md`. Modello finanziario analitico: `docs/business/FINANCIAL_MODEL.md`.

## Architettura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  frontend/  │────>│    api/      │────>│  data/*.db   │
│  Next.js 16 │     │  FastAPI     │     │  SQLite WAL  │
│  porta 3000 │     │  porta 8000  │     └──────────────┘
└─────────────┘     └──────────────┘
                          │
              ┌───────────┼───────────┐
              v           v           v
         crm.db      catalog.db  nutrition.db
        (business)  (tassonomia) (alimenti CREA)
```

- **crm.db**: 29 tabelle business (clienti, contratti, workout, communication_log, crediti_terminazione, crediti_cliente, rettifiche_contratto). Tenant-isolated via `trainer_id`. SACRO — dati del trainer, backup/restore.
- **catalog.db**: 10 tabelle catalogo scientifico (500 esercizi builtin, 466 attivi `in_subset` + tassonomia muscoli/articolazioni/condizioni + relazioni + media). Read-only, shipped con installer. Zero `trainer_id`.
- **nutrition.db**: 8 tabelle catalogo alimenti (CREA 2019 + USDA). Read-only, shipped con installer. 880 alimenti attivi, 210 ricette pietanze, 12 template dieta.
- **Porte**: formula generica `frontend_port - 3000 + 8000 = backend_port` (derivazione runtime in `api-client.ts`).
  - **Dev** (`npm run dev`): frontend **3001** → backend **8001** (`uvicorn --port 8001`). L'offset serve a far coesistere lo sviluppo con un'eventuale app installata di produzione sulla stessa macchina.
  - **Prod / funnel** (`npm run prod`, app installata): frontend **3000** → backend **8000**.
  - **UN SOLO database** (`crm.db`) in ogni caso: il dual-DB `crm_dev.db` è stato rimosso (2026-06-09). "Ambiente unico" = un solo DB, non una sola coppia di porte.

## Comandi operativi

```bash
# --- Avvio sviluppo (dev = 3001/8001, vedi nota porte) ---
./venv/Scripts/uvicorn api.main:app --port 8001 --host 0.0.0.0    # backend dev (8001)
cd frontend && npm run dev                                         # frontend dev (porta 3001)

# --- Test ---
./venv/Scripts/python -m pytest tests/ -v                          # suite backend completa (SSoT: output pytest)
cd frontend && npm test                                            # suite Vitest completa (SSoT: output runner)

# --- Quality gate (obbligatorio prima di commit) ---
bash tools/scripts/check-all.sh                                    # ruff check api/ + next build

# --- Release (ADR-004: pipeline 5 fasi) ---
# 1. Bump __version__ in api/__init__.py
# 2. Commit "release: vX.Y.Z"
# 3. bash tools/build/build-release.sh                             # preflight+build+verify+seal+tag

# --- Lint singoli ---
./venv/Scripts/ruff check api/                                     # backend lint
cd frontend && npx next build                                      # frontend build (zero errori TS)

# --- Migrazioni ---
./venv/Scripts/alembic upgrade head                                # crm.db (SOLO business, esclude catalog+nutrition)
./venv/Scripts/alembic -c alembic_nutrition.ini upgrade head       # nutrition.db (SOLO alimenti)
# catalog.db NON ha Alembic — costruito da seed ORM + script popolazione

# --- Utility ---
bash tools/scripts/kill-port.sh 8001                               # kill zombie uvicorn
bash tools/scripts/restart-backend.sh                              # restart backend dev

# --- Licenza (admin) ---
python -m tools.admin_scripts.generate_license generate-keys       # genera keypair RSA
python -m tools.admin_scripts.generate_license fingerprint         # mostra fingerprint macchina
python -m tools.admin_scripts.generate_license sign \              # firma licenza per un cliente
  --client "nome-cognome" --tier pro --months 12 \
  --machine-id <SHA256_64_CHAR> --output cliente.key
python -m tools.admin_scripts.generate_license verify data/license.key  # verifica licenza
```

## 3 database — 3 session factory — separazione architetturale

```python
from api.database import get_session            # crm.db (business, tenant-isolated) — SACRO
from api.database import get_catalog_session    # catalog.db (esercizi + tassonomia, read-only)
from api.database import get_nutrition_session  # nutrition.db (alimenti + template, read-only)
```

Tutte con PRAGMA: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout=5000`.

**Principio architetturale (ADR 2026-03-19)**:
- catalog.db e nutrition.db sono cataloghi scientifici READ-ONLY, shipped con installer.
- crm.db contiene SOLO dati business del trainer. Zero tabelle catalog/nutrition duplicate.
- Cross-DB ref via ID senza FK constraint (application-level integrity, come `componenti_pasto.alimento_id`).
- Alembic gestisce SOLO crm.db (con `include_name` che esclude catalog+nutrition).
- catalog.db NON ha Alembic: costruito da ORM seed + script popolazione offline.
- `create_db_and_tables()` esclude `CATALOG_TABLE_NAMES | NUTRITION_TABLE_NAMES`.

## Regole non negoziabili

1. **Privacy-first**: dati clinici e finanziari mai esposti in viste pubbliche.
2. **Multi-tenant safety**: ogni query filtra per `trainer_id`. Mai bypassare ownership.
3. **Bouncer Pattern**: ogni endpoint verifica ownership via bouncer. Non trovato = 404, mai 403.
4. **Mass assignment prevention**: `trainer_id` e `id` mai in schema Create. `extra: "forbid"`.
5. **Atomic transactions**: operazioni multi-tabella = un singolo `session.commit()`.
6. **Determinismo**: flussi business-critical spiegabili, auditabili, prevedibili.
7. **Dati in `data/`**: DB, media, licenza, .env, log — tutto sotto `data/`. Sopravvive a upgrade.
8. **Zero path assoluti hardcoded**: usare `DATA_DIR` da `api/config.py` (gestisce `sys.frozen`).
9. **Italiano nativo**: UI, toast, placeholder in italiano. Codice in inglese.
10. **SSoT scientifica**: backend = unica fonte dati scientifici. Frontend consuma via API, mai duplica costanti.
11. **Cataloghi scientifici sacri**: catalog.db e nutrition.db contengono dati CREA 2019 costruiti incrementalmente. MAI `--reset`, `DROP`, `DELETE FROM` su questi DB senza backup preventivo (`cp file.db file.db.bak`). Il seed e' idempotente: usare SENZA `--reset`. `build_nutrition.py --reset` ha un safety gate che blocca se >200 alimenti (richiede `--force-reset` + crea backup automatico).

## Pattern critici

### Backend (dettagli in `api/CLAUDE.md`)
- **Deep Relational IDOR**: catena FK per ownership (Rate → Contract → `trainer_id`).
- **Contract Integrity Engine**: 12 livelli di protezione (residual, chiuso guard, auto-close, overpayment, cascade).
- **Invalidazione simmetrica**: operazioni inverse (pay/unpay) invalidano le stesse query.
- **Audit trail**: `log_audit()` su ogni CREATE/UPDATE/DELETE di entita' business.
- **Soft delete**: `deleted_at` su tutte le tabelle business. SELECT filtra sempre `deleted_at == None`.

### Frontend (dettagli in `frontend/CLAUDE.md`)
- **Hook per dominio**: 24 moduli, uno per dominio. Ogni mutation invalida query correlate + toast.
- **Type sync**: `types/api.ts` = contratto. `Optional[X]` Pydantic → `X | null` TypeScript.
- **toISOLocal()**: MAI `toISOString()` per payload API (perde offset fuso orario).
- **Max 300 LOC** per file di logica, 400 per dati/config.
- **AuthGuard**: MAI leggere browser API (`document`, `window`) in `useState` initializer.

### Cross-layer
- **`extra: "forbid"` su Pydantic**: un campo typo nel payload = 422 silenzioso. Dopo refactor payload, verificare sempre nomi campo vs schema.
- **Middleware Next.js intercetta PRIMA dei rewrite**: `frontend/src/middleware.ts` — tunnel guard (route separation) + auth guard. `/api` in `PUBLIC_ROUTES` (auth JWT gestita dal backend). Dal tunnel, solo `/public/*` accessibile.
- **Seed data**: 500 esercizi + 940 relazioni + 750 media nei seed JSON (`data/exercises/`), seed idempotente al startup in catalog.db. In DB dopo filtro FK orfane: 466 attivi, 894 relazioni, 750 media (seed media potato 1788→750 il 2026-06-13, §5.6.4 — niente più orfani pre-rebuild). Junction tassonomiche in catalog.db: 6.996 muscoli / 1.452 articolazioni / 5.154 condizioni (vedi `docs/operations/DB_INTEGRITY_AUDIT_2026-06-14.md`).
- **Licenza con hardware binding**: JWT RS256 con `machine_id` (SHA-256 di CPU+Board+BIOS via PowerShell). Generazione via CLI (`tools/admin_scripts/generate_license.py`). Flusso completo in `docs/technical/LICENSE_ACTIVATION.md`. `/licenza` NON e' in `AUTH_ONLY_PAGES` (il trainer loggato senza licenza deve vederla).
- **Anti-tampering (ADR-005)**: in compiled mode (Nuitka/PyInstaller) la chiave pubblica e' embedded nel codice (non da file), enforcement sempre ON (no env bypass), fingerprint fail-closed.
- **Anti-reverse engineering (ADR-007)**: 4 step layered hardening — bundle sanitization (zero Alembic/seed/pyc), DB encryption (AES-256-GCM su catalog.db + nutrition.db), Nuitka native compilation (Python→C→x86-64). TTC da 5sec/15min a giorni/settimane. Modello completo in `docs/technical/SECURITY_MODEL.md`.
- **`is_compiled()` helper** (`api/config.py`): rileva sia `sys.frozen` (PyInstaller) che `__compiled__` (Nuitka). Usato da tutti i componenti di enforcement e detection runtime.
- **DB cifrati** (`api/services/db_crypto.py`): AES-256-GCM con PBKDF2-HMAC-SHA256 e seed embedded. Build-time: `encrypt_db()`. Runtime: `decrypt_db_to_bytes()` → `sqlite3.deserialize()` → in-memory engine. Dev mode: `.db` plain invariato.
- **Network hardening (pre-Funnel)**: backend binda su `127.0.0.1` in produzione (entry_point.py), Swagger/Redoc/OpenAPI disabilitati in compiled mode, CORS supporta HTTPS, security headers (HSTS, Referrer-Policy, Permissions-Policy, X-Content-Type-Options, X-Frame-Options) su frontend e backend, version mascherata in `/health` in compiled mode.
- **Rate limiting auth** (`api/services/rate_limiter.py`): `auth_limiter` (5 req/min, 20 req/ora) su login, register, reset-password. `portal_limiter` (30 req/min, 120 req/ora) su endpoint pubblici portale. Classe `RateLimiter` riusabile, IP-based, zero dipendenze.
- **Reset password con verifica**: `POST /auth/reset-password` richiede `current_password` obbligatorio. Verifica bcrypt prima di aggiornare. Trasforma "reset" in "cambio password con verifica".

## Motori scientifici

| Motore | Path | Funzione |
|--------|------|----------|
| Training Science | `api/services/training_science/` (~3500 LOC) | Periodizzazione, EMG, volume MEV/MAV/MRV. Frontend: 6 sezioni trasparenza (reasoning, copertura, equilibrio, recupero, safety, azioni) |
| Training Intelligence | `api/routers/training_intelligence.py` | Analisi post-esecuzione: dose-response muscolo×muscolo, balance ratios, intensity zones, recovery, alert predittivi |
| Workout Diff | `api/routers/workout_diff.py` | "Git diff" allenamento: piano vs eseguito per esercizio, compliance %, punti deboli/forti |
| Safety Engine | `api/services/condition_rules.py` | 47 condizioni, 80 pattern rules |
| Nutrition Science | `api/services/nutrition_science/` (~2100 LOC) | Piano LARN 7gg, scoring 3 assi — **UI RIMOSSA** (backend preservato per futuro prodotto dedicato nutrizionisti) |
| Clinical Analysis | `frontend/src/lib/clinical-analysis.ts` | Range normativi OMS/ACSM (client-side) |
| Smart Programming | `frontend/src/lib/smart-programming/` | Scoring 14D (consumer del backend SSoT) |

## WhatsApp Communication System

Integrazione nativa WhatsApp via deep-link `wa.me` — zero API esterne, privacy-first.
Il trainer controlla ogni messaggio prima dell'invio. Ogni click logga in `communication_log`.

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  WhatsAppButton │────>│  wa.me deep-link  │────>│  WhatsApp    │
│  (14 template)  │     │  (browser/app)    │     │  del trainer │
└────────┬────────┘     └──────────────────┘     └──────────────┘
         │ fire-and-forget
         v
┌──────────────────┐     ┌──────────────────┐
│ POST /communi-   │────>│ communication_log│
│ cations          │     │ (crm.db)         │
└──────────────────┘     └──────────────────┘
```

### Stack comunicazioni

| Layer | File | Funzione |
|-------|------|----------|
| Template engine | `frontend/src/lib/whatsapp-templates.ts` | 15 template pre-compilati (italiano, firma trainer) |
| UI component | `frontend/src/components/ui/whatsapp-button.tsx` | 3 varianti (icon/compact/full) + auto-log via `clientId` prop |
| Centro Comunicazioni | `frontend/src/app/(dashboard)/comunicazioni/page.tsx` | 2 tab: Invia (rubrica + invio multiplo) + Registro (timeline) |
| Registry component | `frontend/src/components/communications/CommunicationRegistry.tsx` | Timeline raggruppata per data, filtro per cliente |
| Frontend hooks | `frontend/src/hooks/useCommunications.ts` | `useAllCommunications`, `useClientCommunications`, `useLogCommunication` |
| Backend router | `api/routers/communications.py` | POST log + GET registro (all/per-cliente) |
| Backend model | `api/models/communication_log.py` | `CommunicationLog` (canale, template_usato, anteprima, trainer_id, id_cliente) |
| Dashboard alerts | `api/routers/dashboard.py` | Alert "birthdays" (oggi + 7gg) + endpoint `/birthday-clients` |
| Birthday sheet | `frontend/src/components/dashboard/BirthdayClientsSheet.tsx` | Sheet auguri con WhatsApp pre-compilato |
| Birthday banner | `frontend/src/app/(dashboard)/page.tsx` | Banner dedicato sopra AlertHub (sempre visibile) |

### 15 template WhatsApp

| Template | Funzione | Contesto d'uso |
|----------|----------|----------------|
| `waRateReminder` | Sollecito rata scaduta | OverdueRatesSheet, Rinnovi & Incassi |
| `waAppointmentReminder` | Conferma appuntamento 24h | AgendaLive, Oggi timeline |
| `waWorkoutShare` | Scheda allenamento pronta | ExportButtons (builder), Comunicazioni |
| `waWelcome` | Benvenuto + link anamnesi | ClientSheet (creazione) |
| `waRenewalReminder` | Rinnovo in scadenza (urgenza calibrata) | ExpiringContractsSheet, Comunicazioni |
| `waContractConfirm` | Conferma contratto attivato | Contratto dettaglio |
| `waCheckIn` | Re-engagement inattivo (zero pressione) | InactiveClientsSheet, Comunicazioni |
| `waEventConfirm` | Conferma sessione appena creata | EventSheet |
| `waBirthday` | Auguri compleanno | BirthdayClientsSheet, Comunicazioni |
| `waMilestone` | Traguardo N sedute | Comunicazioni |
| `waClassReminder` | Reminder lezione di gruppo | Comunicazioni |
| `waClassCancelled` | Classe annullata | Comunicazioni |
| `waProgressUpdate` | Check mensile progressi | Comunicazioni |
| `waFreeMessage` | Messaggio libero (solo firma) | Comunicazioni |

### Pattern architetturali

- **Auto-log trasparente**: `WhatsAppButton` accetta props `clientId` + `templateKey`. Al click, apre wa.me E logga in `communication_log` (fire-and-forget, non blocca l'utente).
- **Invio multiplo sequenziale**: pagina `/comunicazioni` seleziona N clienti → apre wa.me uno alla volta con stepper dots + contatore. Ogni invio logga.
- **Filtri 2 assi**: Stato (Attivi/Inattivi) AND Situazione (Con crediti/Rate scadute). Pattern identico a pagina Clienti.
- **Profilo cliente pulito**: PanoramicaTab mostra solo link compatto "N comunicazioni → Vedi registro". Deep-link a `/comunicazioni?tab=registro&cliente=X`.
- **Birthday alert separato**: banner dedicato sopra AlertHub (non soggetto a `MAX_VISIBLE_ALERTS`). Click apre BirthdayClientsSheet.
- **Phone sanitization**: `sanitizePhone()` in `format.ts` auto-prefissa `+39` per numeri italiani 10 cifre.

## FRP Tunnel System

Tunnel self-hosted per esporre il portale pubblico su Internet. Sostituisce Tailscale Funnel.
Zero configurazione per il trainer. Privacy-first: il VPS non vede il contenuto (P2 data-blind).

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Browser cliente │────>│  VPS edge        │────>│  PC trainer      │
│  (smartphone)    │     │  frps :443       │     │  frpc → :3000    │
│                  │     │  SNI passthrough  │     │  (Next.js)       │
└──────────────────┘     └──────────────────┘     └──────────────────┘
   HTTPS request          instrada per hostname     termina TLS locale
                          NON apre il pacchetto     risponde in chiaro
```

### Stack tunnel

| Layer | File | Funzione |
|-------|------|----------|
| Config | `api/services/tunnel_config.py` | TunnelConfig dataclass, risoluzione frpc path, cert self-signed auto-generato |
| Manager | `api/services/tunnel_manager.py` | Babysitter frpc: subprocess, backoff+jitter, drain output, atexit cleanup |
| Identity | `api/services/license.py` | Claim `instance_id` nel JWT licenza (determina sottodominio) |
| CLI | `tools/admin_scripts/generate_license.py` | `--instance-id <slug>` nel comando `sign` |
| Boot | `api/main.py` lifespan step 6 | Auto-start tunnel + auto-set `PUBLIC_BASE_URL` |
| Route guard | `frontend/src/middleware.ts` | Tunnel guard: solo `/public/*` accessibile, CRM → 404 |
| VPS | `edge.fitmanagerstudio.com` | frps v0.61.1, Hetzner CPX22, `vhostHTTPSPort=443` |

### Flusso zero-touch

1. AVGV genera licenza con `--instance-id gvera-dev` + crea record DNS
2. Trainer installa FitManager (identico per tutti) + inserisce licenza
3. Al boot: backend legge `instance_id` → genera cert self-signed → avvia frpc → tunnel attivo
4. `PUBLIC_BASE_URL` settato automaticamente → link pubblici usano `https://slug.fitmanagerstudio.com`
5. Link anamnesi/schede funzionano via tunnel, CRM accessibile solo da LAN (localhost)

### Route separation (sicurezza)

`frontend/src/middleware.ts` — due layer indipendenti:
- **Layer 1 — Tunnel Guard**: hostname non locale (non localhost/127.0.0.1/LAN) → solo `/public/*`, `/api/public/*`, `/health`, `/media` permessi. Tutto il resto → **404** (non 403, non rivela esistenza).
- **Layer 2 — Auth Guard**: richieste LAN senza cookie JWT → redirect `/login`.

Il CRM (login, dashboard, clienti) e' **completamente invisibile** da Internet.

### Pattern architetturali

- **Separazione config/esecuzione**: `tunnel_config.py` assembla il config, `tunnel_manager.py` gestisce il processo. Il manager non sa nulla di licenze o path.
- **Backoff esponenziale + jitter**: restart frpc con attesa crescente (1s→2s→4s→...60s) + ritardo casuale. Evita retry storm e thundering herd.
- **Cert self-signed (Fase 1)**: RSA 2048, SAN con subdomain + wildcard, 365gg, rigenerato se scaduto. In Fase 2 sostituito da Let's Encrypt (stessi path, zero cambio codice).
- **Proxy type HTTPS + plugin `https2http`**: frpc termina TLS e inoltra HTTP a localhost:3000. Il VPS fa SNI passthrough (non apre il pacchetto TLS). P2 data-blind dimostrato.
- **`PUBLIC_BASE_URL` auto**: se `instance_id` presente, il lifespan setta `PUBLIC_BASE_URL=https://slug.fitmanagerstudio.com` e `PUBLIC_PORTAL_ENABLED=true`. I link generati dal trainer usano l'URL tunnel, non `localhost`.

### Fase di sviluppo

- Fase 0: COMPLETATA (VPS, frps, DNS wildcard)
- Fase 1: CORE COMPLETATA (instance_id, tunnel_manager, auto-start, route separation, test e2e)
  - Rimangono: bundle frpc in Nuitka, script provisioning DNS, health endpoint
- Fase 2: TLS e2e (cert Let's Encrypt DNS-01, pagina offline, token hash)
- Fase 3: Onboarding zero-touch + dismissione Tailscale

Architettura completa (design + build + operations): `docs/technical/TUNNEL_ARCHITECTURE.md`. Security boundary + Strada B: `docs/technical/TUNNEL_SECURITY_BOUNDARY.md`.

## Agent Skills (quality automation)

Skills installate in `.agents/skills/` — knowledge base attive per audit e code generation.

| Skill | Source | Quando si attiva |
|-------|--------|-----------------|
| `vercel-react-best-practices` | Vercel Labs | 62 regole in 8 categorie. Regole CRITICAL/HIGH codificate in `frontend/CLAUDE.md` sezione "React Performance Rules". |
| `web-design-guidelines` | Vercel Labs | Audit WCAG + UX on-demand (`/web-design-guidelines <file>`). Usare prima di merge su componenti UI nuovi. |
| `code-review` | Built-in | Review PR (`/code-review`). Multi-agent: 2 CLAUDE.md compliance + 2 bug detection. High-signal only. |
| `frontend-design` | Built-in | Creazione UI production-grade (`/frontend-design`). Design system coerente, no estetica AI generica. |

**Integrazione nel workflow**:
- Regole Vercel CRITICAL/HIGH codificate in frontend/CLAUDE.md (non servono invocazioni esplicite).
- `/web-design-guidelines <file>` prima di merge su componenti UI nuovi o modificati.
- `/code-review` su ogni PR verso main.
- `/frontend-design` quando si crea una nuova pagina o componente complesso.

## Struttura file governance

### Layer 1 — Codice (CLAUDE.md per dominio)

| File | Dominio | Quando leggerlo |
|------|---------|-----------------|
| `CLAUDE.md` (questo) | Entry point, regole cross-layer | Sempre |
| `api/CLAUDE.md` | Backend: pattern, schema, endpoint, test | Quando tocchi `api/` |
| `frontend/CLAUDE.md` | Frontend: componenti, hook, pitfalls | Quando tocchi `frontend/` |
| `core/CLAUDE.md` | Moduli AI dormenti | Quando tocchi `core/` |

### Layer 2 — Documentazione (organizzata per dominio in `docs/`)

| Directory | Contenuto | Quando leggerlo |
|-----------|-----------|-----------------|
| `docs/business/` | BP, Strategy Plan, Financial Model, Partner, Legal, Competitive | Pricing, proiezioni, partner, fondi, NASpI |
| `docs/product/` | Roadmap post-lancio, FitScan, Video production/strategy | Pianificazione feature, video, post-lancio |
| `docs/specs/` | **SOLO spec APERTE** (il fronte di lavoro: `ls docs/specs/` = work-queue) | Quando implementi un blocco |
| `docs/technical/` | SOLO SSoT evergreen (FDM, Tassonomia, Security, Tunnel, License, Deploy) | Architettura, sicurezza, infra |
| `docs/operations/` | Release checklist, Diagnostics, Support, Upgrade | Release, troubleshooting, supporto |
| `docs/adr/` | Architecture Decision Records (13 ADR attivi + ADR-012 riservato) | Decisioni architetturali |
| `docs/incidents/` | Post-mortem incidenti | Pattern sospetti, regressioni |
| `docs/learning/` | Apprendimento founder-developer (concetti, metodo, build log) | Mai — materiale didattico, non spec |

Indice completo con ogni file: `docs/INDEX.md`.

### Contratto di contesto (riordino 2026-07-03 — la POSIZIONE è lo STATO)

- `docs/adr/` = la LEGGE (decisioni immortali, evolvono per Addendum, mai archiviate).
- `docs/technical/` = com'è FATTO il sistema (solo SSoT evergreen; **zero SPEC_*/IMPL_PLAN_*** — guard in check-all).
- `docs/specs/` = cosa stiamo COSTRUENDO ORA (solo spec aperte, riga `Stato:` obbligatoria in testa; a chiusura blocco → consuntivo + `docs/archive/specs/` nello stesso commit docs del gate).
- `docs/archive/` = storia: **MAI caricare come contesto di lavoro**.
- Log di sviluppo UNICO = `docs/learning/BUILD_LOG.md` (UPGRADE_LOG dismesso 2026-07-03). Ciclo di vita completo: `AGENTS.md`.

### Regola di cattura learning (automatica)

Quando durante una sessione di lavoro emergono concetti tecnici nuovi o approfondimenti non banali (casi edge, pattern architetturali, failure mode, meccanismi sotto la superficie), Claude Code cattura il materiale nel file `docs/learning/LEARNING_*.md` appropriato per dominio, seguendo il template a 3 livelli definito in `docs/learning/LEARNING_METHOD.md` sez. 4. Il trigger e' intrinseco alla conversazione: la cattura avviene anche se non richiesta esplicitamente. Non scatta per dettagli di implementazione pura, informazioni gia' presenti, o sessioni di puro bugfix senza concetti nuovi.

### Layer 3 — Governance di progetto (root)

| File | Scopo |
|------|-------|
| `MANIFESTO.md` | Missione, visual identity, principi UX |
| `LAUNCH_SCOPE.md` | Cosa e' in scope per il lancio |
| `POSTMORTEMS.md` | Lezioni da errori passati |
| `AGENTS.md` | Delivery loop, quality gates, commit standard |

## Commit

Formato: `area: descrizione` — es. `api: ...`, `nutrizione: ...`, `dashboard: ...`, `fix: ...`

Quality gate obbligatorio: `bash tools/scripts/check-all.sh` (ruff + next build).
Ogni commit deve lasciare il branch rilasciabile per il proprio scope.

## Pitfalls ricorrenti (top 10)

1. **`toISOString()` perde timezone**: usare `toISOLocal()` da `lib/format.ts` per ogni payload API con date.
2. **`extra: "forbid"` + campo typo = 422**: verificare nomi campo con curl vs schema Pydantic dopo ogni refactor.
3. **PyInstaller `Path(__file__)`**: non funziona in bundle → usare `DATA_DIR` da `config.py`.
4. **Radix: no `<label>` + Checkbox**: causa double-toggle. Usare `<div onClick>` + `stopPropagation`.
5. **`useState(() => browserAPI())`**: hydration mismatch. Usare `useState(false)` + `useEffect`.
6. **Tunnel FRP inoltra a porta 3000 (frontend), mai 8000**: il tunnel punta a Next.js (porta 3000) che proxya `/api/*` al backend. Le route `/public/*` sono pagine Next.js. **Route separation**: `frontend/src/middleware.ts` blocca tutto tranne `/public/*` dal tunnel (404). Se il middleware manca o e' bypassato → CRM esposto su Internet.
7. **Cross-DB session mismatch**: funzioni dual-session (`safety_engine`, `profile_resolver`, `session_prep`) devono usare `catalog_session` per tabelle catalog.db (esercizi, muscoli, condizioni) e `session` per crm.db. Test in-memory con engine singolo NON copre questo bug. Verificare SEMPRE dopo modifiche a funzioni dual-session. Incidente: `docs/incidents/INC-2026-03-28-safety-engine-blind-spot.md`.
8. **Cache safety map non invalidata**: ogni mutation che modifica anamnesi (direttamente o indirettamente) DEVE invalidare `["exercise-safety-map", clientId]`. Include `useUpdateAnamnesi`, `useUpdateClient`, futuro polling portale pubblico.
9. **Informazioni cliniche MAI dietro toggle**: la BuilderSafetyCard e' non negoziabile quando `condition_count > 0`. Zero condizioni responsive, zero toggle, zero tab. La visibilita' dipende SOLO da `safetyMap.condition_count > 0`.
10. **Cascade FK su delete/replace sessioni**: `_delete_sessions_cascade` DEVE eliminare TUTTE le tabelle che referenziano `id_sessione` (schedule slots, logs, esercizi, blocchi) PRIMA di eliminare le sessioni. Aggiungere nuove tabelle con FK su `sessioni_scheda.id` → aggiornare SEMPRE il cascade. Test regressione: `test_workouts_crud.py::test_replace_sessions_with_schedule_no_500`. Incidente: INC-2026-03-28b.
11. **Pagine pubbliche: ZERO CSS variables del tema**: `app/public/*` (anamnesi, workout) DEVONO usare SOLO colori Tailwind espliciti (`text-gray-900`, `text-gray-500`, `bg-gray-100`). MAI `text-muted-foreground`, `text-foreground`, `bg-muted`, `border-input`. Il dispositivo del cliente ha configurazione sconosciuta (dark mode). Forzare `style={{ colorScheme: "light" }}` + `text-gray-900` sul div root. Incidente: INC-2026-03-30.
12. **Rate limiter endpoint pubblici**: calibrato per UX reale (page load = 2 req simultanee, 1 sessione = 4 req). Il frontend DEVE distinguere HTTP 429 da errori reali e mostrare UI "Riprova" dedicata, MAI "Link non valido". Incidente: INC-2026-03-30.
13. **Rebuild catalog.db = pipeline completa**: ricreare catalog.db senza rieseguire i 3 script tassonomici produce un DB con esercizi ma Safety Engine cieco. Ordine obbligatorio: `seed_taxonomy` → `populate_taxonomy` → `populate_conditions`. Il seed al startup (`api/seed_taxonomy.py`) copre solo lo sviluppo — in compiled mode catalog.db DEVE essere consegnato completo. Incidente: INC-2026-04-19.
14. **KPI cumulativi vs KPI di stato: filtri diversi**: KPI cumulativi (fatturato, incassato, crediti totali) DEVONO includere i contratti chiusi — sono metriche storiche. KPI operativi (rate scadute, contratti attivi, crediti residui) filtrano `chiuso=False`. MAI applicare `if not c.chiuso` a somme di `prezzo_totale` o `totale_versato`. Ogni KPI aggregato deve avere commento inline: "stato" (filtra attivi) o "cumulativo" (include tutto). Test regressione: `test_contract_integrity.py::test_kpi_fatturato_includes_closed_contracts`. Incidente: INC-2026-06-08.
15. **FK locale verso tabelle catalog = bomba a orologeria sui crm.db fresh**: quando una tabella business (`crm.db`) referenzia per ID una tabella che vive in catalog.db/nutrition.db (`metriche`, `esercizi`, `alimenti`), il modello SQLModel **NON deve** dichiarare `foreign_key=`. Una FK locale finisce nel DDL di `crm.db`, ma il parent è escluso da `create_db_and_tables()` (è in `CATALOG_TABLE_NAMES`/`NUTRITION_TABLE_NAMES`). Sui crm.db **fresh** (installer, che non spedisce crm.db) con `foreign_keys=ON`, il primo INSERT crasha `no such table: metriche`. I DB **monolite** (Alessio/Chiara, via Alembic) hanno la tabella → mascherano il bug ("works on my machine"). Pattern corretto: `id_metrica: int = Field(index=True)` cross-DB, come `componenti_pasto.alimento_id`. Letture sempre via `get_catalog_session`. Il self-heal dei DB già deployati è in `schema_sync._fix_cross_db_fk` (`_CROSS_DB_FK_FIXES`): ricrea la tabella senza la FK al boot, idempotente, no Alembic (gira in frozen). Precedente: `esercizi_sessione→esercizi`. Test: `test_schema_sync.py::test_fix_cross_db_fk_removes_metriche_fk`.
16. **Processo spawnato dal backend = deve morire col backend (Job Object), e l'installer deve chiuderlo prima di sovrascriverlo**: ogni processo a vita lunga lanciato dal backend (oggi `frpc` via `tunnel_manager.py`) è un **nipote detached** (`launcher.bat → fitmanager.exe → Popen frpc.exe`, `CREATE_NO_WINDOW`). Il cleanup via `atexit` + lifespan `stop()` copre SOLO la chiusura gentile; su chiusura brusca (l'utente chiude la finestra del launcher) NON scatta e il processo resta **orfano**. Un `.exe` in esecuzione **locka il proprio file immagine** → al primo upgrade che deve rimpiazzarlo, l'installer fallisce con `ERROR_ACCESS_DENIED` (codice 5). Fix obbligatorio a 2 livelli: (a) agganciare il processo a un **Windows Job Object** `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` (`_create_kill_on_close_job` + `_assign_process_to_job` in `tunnel_manager.py`) → il SO lo uccide quando il backend termina, comunque termini; (b) l'installer (`fitmanager.iss`) chiude i processi prima di scrivere — `CloseApplications=yes` + `taskkill /F /T` in `PrepareToInstall` per i nomi app-specifici. Regola per il futuro: QUALSIASI nuovo binario a vita lunga aggiunto al bundle richiede entrambi. Incidente: `docs/incidents/INC-2026-06-15-installer-frpc-lock.md`.
17. **Fingerprint hardware: mai hashare un set parziale, mai cachare un fallimento**: il `machine_id` della licenza è `sha256("cpu|board|bios")` letto via 3 query PowerShell/WMI (`machine_fingerprint.py`). Su alcune macchine le query falliscono a intermittenza (carico, antivirus, risveglio da sleep) ritornando vuoto. Hashare un set parziale (`sha256("cpu||bios")`) produce un fingerprint **diverso** dal `machine_id` firmato → `wrong_machine` → 403 → blocco CRM. Regole ferree: (a) se **anche un solo** identificatore manca → `"unavailable"` (fail-closed), MAI un hash parziale; (b) `get_machine_fingerprint` cacha **solo** un fingerprint completo 3/3 — un `"unavailable"` NON va congelato, così la richiesta dopo ritenta e si auto-guarisce invece di bloccare l'intera sessione; (c) retry sui vuoti transitori. L'hash 3/3 resta `sha256("cpu\|board\|bios")` → licenze esistenti invariate. Vale per QUALSIASI identificatore usato per autorizzazione: set completo e deterministico o fallimento esplicito recuperabile, mai degradazione parziale. Test: `test_machine_fingerprint.py` (capovolto il test che certificava il bug). Incidente: `docs/incidents/INC-2026-06-18-fingerprint-partial-license-lockout.md`.

## Credenziali sviluppo

- Login: **chiarabassani96@gmail.com / chiarabassani**
- UN SOLO database (`crm.db`) → un solo set di credenziali. La vecchia coppia
  "Dev: …/Fitness2026!" era legata al rimosso `crm_dev.db` e **non funziona più**
  (verificato 2026-06-20: ritorna 401). Vedi sezione Porte per dev=3001/8001 vs prod=3000/8000.
