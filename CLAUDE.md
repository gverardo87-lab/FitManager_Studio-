# CLAUDE.md — FitManager AI Studio

CRM locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA.
Dati sul PC del professionista, zero cloud obbligatorio, privacy-first.

## Stack

```
Python 3.12 + FastAPI + SQLModel + SQLite (WAL)     → api/     (144 file)
Next.js 16 + React 19 + TypeScript 5 + shadcn/ui    → frontend/ (293 file)
Langchain + Ollama (moduli AI dormenti)              → core/    (27 file)
```

Distribuzione: PyInstaller + Next.js standalone + Inno Setup (Windows installer).

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
SSoT numeri e proiezioni: `docs/BUSINESS_PLAN.md` (v4.3). Strategia operativa: `docs/STRATEGY_PLAN.md`.

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

- **crm.db**: 26 tabelle business (clienti, contratti, workout, piani alimentari, communication_log). Tenant-isolated via `trainer_id`. SACRO — dati del trainer, backup/restore.
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
./venv/Scripts/python -m pytest tests/ -v                          # 326 test backend
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
- **Licenza con hardware binding**: JWT RS256 con `machine_id` (SHA-256 di CPU+Board+BIOS via PowerShell). Generazione via CLI (`tools/admin_scripts/generate_license.py`). Flusso completo in `docs/LICENSE_ACTIVATION.md`. `/licenza` NON e' in `AUTH_ONLY_PAGES` (il trainer loggato senza licenza deve vederla).
- **Anti-tampering (ADR-005)**: in frozen mode (PyInstaller) la chiave pubblica e' embedded nel codice (non da file), enforcement sempre ON (no env bypass), fingerprint fail-closed. Modello completo in `docs/SECURITY_MODEL.md`.

## Motori scientifici

| Motore | Path | Funzione |
|--------|------|----------|
| Training Science | `api/services/training_science/` (~3500 LOC) | Periodizzazione, EMG, volume MEV/MAV/MRV |
| Safety Engine | `api/services/condition_rules.py` | 47 condizioni, 80 pattern rules |
| Nutrition Science | `api/services/nutrition_science/` (~2100 LOC) | Piano LARN 7gg, scoring 3 assi |
| Clinical Analysis | `frontend/src/lib/clinical-analysis.ts` | Range normativi OMS/ACSM (client-side) |
| Smart Programming | `frontend/src/lib/smart-programming/` | Scoring 14D (consumer del backend SSoT) |

## WhatsApp Communication System

Integrazione nativa WhatsApp via deep-link `wa.me` — zero API esterne, privacy-first.
Il trainer controlla ogni messaggio prima dell'invio. Ogni click logga in `communication_log`.

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  WhatsAppButton │────>│  wa.me deep-link  │────>│  WhatsApp    │
│  (15 template)  │     │  (browser/app)    │     │  del trainer │
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
| `waNutritionPlan` | Piano alimentare pronto | Nutrizione [id], Comunicazioni |
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

| File | Scopo | Quando leggerlo |
|------|-------|-----------------|
| `CLAUDE.md` (questo) | Entry point, regole cross-layer | Sempre — e' il primo file da leggere |
| `api/CLAUDE.md` | Pattern backend, schema, endpoint, test | Quando tocchi `api/` |
| `frontend/CLAUDE.md` | Pattern frontend, componenti, pitfalls | Quando tocchi `frontend/` |
| `core/CLAUDE.md` | Moduli AI dormenti, stato legacy | Quando tocchi `core/` |
| `docs/BUSINESS_PLAN.md` | **SSoT** numeri, pricing, proiezioni, modello community 4 livelli | Quando tocchi pricing, community, partner, proiezioni — BP v4.3 e' la fonte di verita' |
| `docs/STRATEGY_PLAN.md` | Piano operativo lancio, category creation, ruolo partner | Quando pianifichi azioni di go-to-market o partnership |
| `MANIFESTO.md` | Missione prodotto, visual identity, principi UX | Quando serve contesto di prodotto |
| `LAUNCH_SCOPE.md` | Cosa e' in scope per il lancio | Quando prioritizzi feature |
| `POSTMORTEMS.md` | Lezioni da errori passati | Quando incontri un pattern sospetto |
| `AGENTS.md` | Delivery loop, quality gates, commit standard | Quando serve contesto operativo agenti |
| `docs/SECURITY_MODEL.md` | Threat model, 5 livelli protezione, roadmap sicurezza | Quando tocchi licenza, auth, anti-tampering |
| `docs/LICENSE_ACTIVATION.md` | Attivazione licenza, hardware binding, CLI admin | Quando tocchi licenza, fingerprint, setup |
| `docs/adr/ADR-004-release-pipeline-sicuro.md` | Pipeline release 5 fasi, version SSoT, safety gate, smoke test | Quando fai una release o tocchi il build pipeline |
| `docs/adr/ADR-005-license-hardening-anti-tampering.md` | Hardening licenza: embedded key, env bypass block, fail-closed | Quando tocchi sistema licenza o anti-tampering |
| `docs/VIDEO_PRODUCTION.md` | Pipeline video blindata: manifest SSoT, flusso continuo, selettori verificati, errori critici | Quando crei o modifichi video — leggere §5.1 + §8 SEMPRE prima di scriptare |
| `docs/VIDEO_GUIDE_STRATEGY.md` | Sistema video-guide contestuali: 4 livelli (hub, header, bussola, palette), regole, mapping | Quando integri video nell'interfaccia |
| `docs/adr/ADR-006-fitmanager-box-multi-platform.md` | FitManager Box: strategia multi-platform, modello hardware+software, BOM, pricing | Quando tocchi deploy, licensing cross-platform, o strategia prodotto |
| `docs/POST_LAUNCH_ROADMAP_90D.md` | Roadmap 90 giorni post-lancio: PWA, mobile UX, Box, science nudges, GTM | Quando pianifichi lavoro post-lancio |
| `docs/adr/ADR-007-fitscan-computer-vision-biomechanics.md` | FitScan: architettura a strati (pose commodity + engine proprietario), 3 livelli, integrazione motori | Quando tocchi FitScan, CV, misurazioni automatiche |
| `docs/FITSCAN_ARCHITECTURE.md` | Spec tecnica FitScan: DB schema, Biomechanical Engine, Pose Provider, exercise profiles, privacy | Quando implementi FitScan — leggere SEMPRE prima di scrivere codice |
| `docs/adr/ADR-008-builder-fullscreen-science-panel.md` | Builder full-screen: sidebar nascosta, Science Panel 320px con Safety+Score+Coverage+Balance live | Quando tocchi il builder, il layout, o la sidebar |
| `docs/TAILSCALE_FUNNEL_SETUP.md` | Setup Tailscale Funnel, auto-start launcher, architettura proxy, troubleshooting, roadmap accesso remoto | Quando tocchi portale pubblico, anamnesi self-service, accesso remoto clienti |

## Commit

Formato: `area: descrizione` — es. `api: ...`, `nutrizione: ...`, `dashboard: ...`, `fix: ...`

Quality gate obbligatorio: `bash tools/scripts/check-all.sh` (ruff + next build).
Ogni commit deve lasciare il branch rilasciabile per il proprio scope.

## Pitfalls ricorrenti (top 6)

1. **`toISOString()` perde timezone**: usare `toISOLocal()` da `lib/format.ts` per ogni payload API con date.
2. **`extra: "forbid"` + campo typo = 422**: verificare nomi campo con curl vs schema Pydantic dopo ogni refactor.
3. **PyInstaller `Path(__file__)`**: non funziona in bundle → usare `DATA_DIR` da `config.py`.
4. **Radix: no `<label>` + Checkbox**: causa double-toggle. Usare `<div onClick>` + `stopPropagation`.
5. **`useState(() => browserAPI())`**: hydration mismatch. Usare `useState(false)` + `useEffect`.
6. **Tailscale Funnel su porta FRONTEND, mai backend**: il funnel deve puntare a 3000 (Next.js), non 8000 (FastAPI). Le route `/public/*` sono pagine Next.js. Se punta al backend → `{"detail":"Not Found"}`. Dettagli in `docs/TAILSCALE_FUNNEL_SETUP.md`.

## Credenziali sviluppo

- Dev: chiarabassani96@gmail.com / Fitness2026!
- Prod: chiarabassani96@gmail.com / chiarabassani
