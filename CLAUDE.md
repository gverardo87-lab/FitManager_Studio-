# CLAUDE.md — FitManager AI Studio

CRM locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA.
Dati sul PC del professionista, zero cloud obbligatorio, privacy-first.

## Stack

```
Python 3.12 + FastAPI + SQLModel + SQLite (WAL)     → api/     (144 file)
Next.js 16 + React 19 + TypeScript 5 + shadcn/ui    → frontend/ (293 file)
Langchain + Ollama (moduli AI dormenti)              → core/    (27 file)
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

- **crm.db**: 26 tabelle business (clienti, contratti, workout, communication_log). Tenant-isolated via `trainer_id`. SACRO — dati del trainer, backup/restore.
- **catalog.db**: 10 tabelle catalogo scientifico (500 esercizi builtin + tassonomia muscoli/articolazioni/condizioni + relazioni + media). Read-only, shipped con installer. Zero `trainer_id`.
- **nutrition.db**: 8 tabelle catalogo alimenti (CREA 2019 + USDA). Read-only, shipped con installer. 880 alimenti attivi, 210 ricette pietanze, 12 template dieta.
- **Dual env**: prod (porta 8000/3000, crm.db) + dev (porta 8001/3001, crm_dev.db).
- **Formula porte**: `frontend_port - 3000 + 8000 = backend_port`.

## Comandi operativi

```bash
# --- Avvio sviluppo ---
./venv/Scripts/uvicorn api.main:app --port 8001 --host 0.0.0.0    # backend dev
cd frontend && npm run dev                                         # frontend dev (porta 3001)

# --- Test ---
./venv/Scripts/python -m pytest tests/ -v                          # 361 test backend
cd frontend && npm test                                            # 69 vitest (data protection)

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
- **Proxy Next.js intercetta PRIMA dei rewrite**: `/api` in `PUBLIC_ROUTES` (auth JWT gestita dal backend).
- **Seed data**: 500 esercizi + 940 relazioni + 1788 media in `data/exercises/`, seed idempotente al startup in catalog.db.
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
| `docs/technical/` | Security, License, Tailscale, Deploy, Nutrition Engine | Architettura, sicurezza, infra |
| `docs/operations/` | Release checklist, Diagnostics, Support, Upgrade | Release, troubleshooting, supporto |
| `docs/adr/` | Architecture Decision Records (9 ADR) | Decisioni architetturali |
| `docs/incidents/` | Post-mortem incidenti | Pattern sospetti, regressioni |

Indice completo con ogni file: `docs/INDEX.md`.

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
6. **Tailscale Funnel su porta FRONTEND, mai backend**: il funnel deve puntare a 3000 (Next.js), non 8000 (FastAPI). Le route `/public/*` sono pagine Next.js. Se punta al backend → `{"detail":"Not Found"}`. Dettagli in `docs/technical/TAILSCALE_FUNNEL_SETUP.md`.
7. **Cross-DB session mismatch**: funzioni dual-session (`safety_engine`, `profile_resolver`, `session_prep`) devono usare `catalog_session` per tabelle catalog.db (esercizi, muscoli, condizioni) e `session` per crm.db. Test in-memory con engine singolo NON copre questo bug. Verificare SEMPRE dopo modifiche a funzioni dual-session. Incidente: `docs/incidents/INC-2026-03-28-safety-engine-blind-spot.md`.
8. **Cache safety map non invalidata**: ogni mutation che modifica anamnesi (direttamente o indirettamente) DEVE invalidare `["exercise-safety-map", clientId]`. Include `useUpdateAnamnesi`, `useUpdateClient`, futuro polling portale pubblico.
9. **Informazioni cliniche MAI dietro toggle**: la BuilderSafetyCard e' non negoziabile quando `condition_count > 0`. Zero condizioni responsive, zero toggle, zero tab. La visibilita' dipende SOLO da `safetyMap.condition_count > 0`.
10. **Cascade FK su delete/replace sessioni**: `_delete_sessions_cascade` DEVE eliminare TUTTE le tabelle che referenziano `id_sessione` (schedule slots, logs, esercizi, blocchi) PRIMA di eliminare le sessioni. Aggiungere nuove tabelle con FK su `sessioni_scheda.id` → aggiornare SEMPRE il cascade. Test regressione: `test_workouts_crud.py::test_replace_sessions_with_schedule_no_500`. Incidente: INC-2026-03-28b.
11. **Pagine pubbliche: ZERO CSS variables del tema**: `app/public/*` (anamnesi, workout) DEVONO usare SOLO colori Tailwind espliciti (`text-gray-900`, `text-gray-500`, `bg-gray-100`). MAI `text-muted-foreground`, `text-foreground`, `bg-muted`, `border-input`. Il dispositivo del cliente ha configurazione sconosciuta (dark mode). Forzare `style={{ colorScheme: "light" }}` + `text-gray-900` sul div root. Incidente: INC-2026-03-30.
12. **Rate limiter endpoint pubblici**: calibrato per UX reale (page load = 2 req simultanee, 1 sessione = 4 req). Il frontend DEVE distinguere HTTP 429 da errori reali e mostrare UI "Riprova" dedicata, MAI "Link non valido". Incidente: INC-2026-03-30.
13. **Rebuild catalog.db = pipeline completa**: ricreare catalog.db senza rieseguire i 3 script tassonomici produce un DB con esercizi ma Safety Engine cieco. Ordine obbligatorio: `seed_taxonomy` → `populate_taxonomy` → `populate_conditions`. Il seed al startup (`api/seed_taxonomy.py`) copre solo lo sviluppo — in compiled mode catalog.db DEVE essere consegnato completo. Incidente: INC-2026-04-19.

## Credenziali sviluppo

- Dev: chiarabassani96@gmail.com / Fitness2026!
- Prod: chiarabassani96@gmail.com / chiarabassani
