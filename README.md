# FitManager AI Studio

CRM locale Windows per chinesiologi, personal trainer e professionisti fitness a P.IVA.
Dati sul PC del professionista, zero cloud obbligatorio, privacy-first.

> Versione corrente: SSoT in `api/__init__.py` (mai hardcodata qui — evita lo stale).

## Cosa copre oggi

- **Clienti**: anagrafica, anamnesi self-service, misurazioni, monitoraggio e Client Avatar (6 dimensioni)
- **Contratti & Rate**: integrita pagamenti (Contract Integrity Engine, 12 livelli), rinnovi a catena, storico incassi
- **Agenda**: sessioni, drag and drop, consumo crediti e sincronizzazione contratto
- **Cassa**: ledger, spese ricorrenti, proiezioni finanziarie, aging
- **Schede & Esercizi**: workout builder 3-tab, libreria scientifica (466 esercizi attivi), Smart Programming
- **Motori scientifici**: Training Science (~3500 LOC), Safety Engine (47 condizioni), Training Intelligence, Workout Diff
- **Comunicazioni**: sistema WhatsApp nativo (15 template, deep-link `wa.me`, auto-log, alert compleanni)
- **Portale pubblico**: anamnesi e schede self-service via share token (kiosk mobile)
- **Workspace operativi**: `Oggi`, `Rinnovi & Incassi`, Command Palette (Ctrl+K)
- **Infrastruttura**: backup/restore, setup wizard, licenza con hardware binding, tunnel FRP self-hosted

## Stack

```
Python 3.12 + FastAPI + SQLModel + SQLite (WAL)     → api/      (166 file)
Next.js 16 + React 19 + TypeScript 5 + shadcn/ui    → frontend/ (313 file src)
Langchain + Ollama (moduli AI dormenti)             → core/     (14 file)
```

Distribuzione: **Nuitka** (Python→C→nativo) + Next.js standalone + Inno Setup (Windows installer).
Fallback build: PyInstaller (`fitmanager.spec` preservato per rollback).

## Architettura — 3 database separati

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

- **crm.db** — 26 tabelle business (clienti, contratti, workout, communication_log). Tenant-isolated via `trainer_id`. SACRO: dati del trainer, backup/restore.
- **catalog.db** — 10 tabelle catalogo scientifico (500 esercizi builtin, 466 attivi + tassonomia muscoli/articolazioni/condizioni + media). Read-only, shipped con installer.
- **nutrition.db** — 8 tabelle catalogo alimenti (CREA 2019 + USDA). 880 alimenti attivi, 210 ricette, 12 template dieta. Read-only, shipped con installer.

Separazione architetturale (ADR 2026-03-19): i cataloghi scientifici sono read-only e shipped con l'installer; `crm.db` contiene SOLO dati business. Cross-DB ref via ID senza FK constraint (application-level integrity). Alembic gestisce SOLO `crm.db`.

## Snapshot del repository (verificato 2026-06-14)

| Area | Snapshot |
|---|---|
| `api/` | 166 file Python, 29 router, 25 model |
| `frontend/src/` | 313 file TS/TSX, 27 page route, 188 componenti, 32 hook |
| `tests/` | 36 file pytest |
| `core/` | 14 file Python (moduli AI/legacy fuori dal percorso critico) |
| `tools/` | 97 script, di cui 68 in `tools/admin_scripts/` |
| `data/` | `crm.db`, `catalog.db`, `nutrition.db` |

Conteggi riallineati con `rg`/`find` sul repo. Evitare di reintrodurre conteggi manuali non verificati.

## Avvio locale

Prerequisiti minimi:

- Node.js 20+ e npm
- Python 3.12 con virtualenv (`venv/`)
- SQLite in PATH (solo per check manuali DB)

### Sviluppo

```bash
# Terminale 1 — Backend (porta 8000)
./venv/Scripts/uvicorn api.main:app --port 8000 --host 0.0.0.0

# Terminale 2 — Frontend (porta 3000)
cd frontend && npm run dev
```

Apri `http://localhost:3000`.

| Frontend | Backend | Database |
|---|---|---|
| `3000` | `8000` | `data/crm.db` |

Il frontend deduce la base URL API da `window.location` (formula: `frontend_port - 3000 + 8000`).

### Credenziali sviluppo

- `chiarabassani96@gmail.com` / `Fitness2026!`

## Quality gate

Gate obbligatorio prima di ogni commit:

```bash
bash tools/scripts/check-all.sh        # ruff check api/ + next build
```

Test e lint singoli:

```bash
./venv/Scripts/python -m pytest tests/ -v      # test backend (tests/)
cd frontend && npm test                        # vitest (data protection)
./venv/Scripts/ruff check api/                 # backend lint
cd frontend && npx next build                  # frontend build (zero errori TS)
```

Ogni commit deve lasciare il branch rilasciabile per il proprio scope.
Formato commit: `area: descrizione` (es. `api: ...`, `dashboard: ...`, `fix: ...`).

## Sicurezza

Hardening completato (post-audit Red Team, rischio da CRITICO ad ACCETTABILE):

- **License hardening (ADR-005)**: JWT RS256 con `machine_id` (hardware binding), chiave pubblica embedded in compiled mode, enforcement sempre ON, fingerprint fail-closed.
- **Anti-reverse engineering (ADR-007)**: bundle sanitization (zero Alembic/seed/pyc) + DB encryption AES-256-GCM su catalog.db/nutrition.db + Nuitka native compilation.
- **Network hardening**: bind `127.0.0.1` in produzione, Swagger/Redoc disabilitati in compiled mode, rate limiting auth (5/min, 20/h), security headers (HSTS, Referrer-Policy, Permissions-Policy), CORS HTTPS, version masking.
- **Tunnel FRP (route separation)**: il portale pubblico è esposto via VPS edge (SNI passthrough, P2 data-blind); il CRM resta invisibile da Internet (tutto fuori da `/public/*` → 404).

Modello completo: `docs/technical/SECURITY_MODEL.md`.

## Rilascio

Pipeline 5 fasi (ADR-004): preflight → build → verify → seal → tag.

```bash
# 1. Bump __version__ in api/__init__.py
# 2. Commit "release: vX.Y.Z"
# 3. bash tools/build/build-release.sh
```

## Struttura del progetto

```text
frontend/      Next.js 16 + React 19 + TypeScript
  src/app/     App Router: dashboard, setup, licenza, public portal
  src/components/ + src/hooks/ + src/types/api.ts
api/           FastAPI + SQLModel + Pydantic
  routers/     domini REST, auth, backup, workspace, training science, comunicazioni, tunnel
  models/      ORM business + licenza + public portal
  schemas/     contratti API e DTO
  services/    workspace engine, training science, safety, tunnel, rate limiter, db crypto
core/          moduli AI/legacy non obbligatori per il CRM core
tools/         seed, build, migration, admin script, licenza
data/          database SQLite, media, licenza, log (sopravvive agli upgrade)
docs/          governance organizzata per dominio (vedi docs/INDEX.md)
installer/     launcher e packaging Windows (Inno Setup)
```

## Documentazione

| File | Scopo |
|---|---|
| `ARCHITECTURE.md` | Overview di sistema: forma dell'architettura, 3 attori, 3 DB, ciclo richiesta, decisioni portanti — **punto di partenza** |
| `CLAUDE.md` | Manifesto architetturale: regole, runbook, pattern cross-layer (+ `api/CLAUDE.md`, `frontend/CLAUDE.md`, `core/CLAUDE.md`) |
| `docs/INDEX.md` | Dispatcher unico di tutta la documentazione (business, product, technical, operations, adr, incidents, security) |
| `AGENTS.md` | Delivery loop, quality gate, commit standard |
| `MANIFESTO.md` | Missione, visual identity, principi UX |
| `LAUNCH_SCOPE.md` | Scope di lancio |
| `CHANGELOG.md` | Storico versioni |
| `POSTMORTEMS.md` | Lezioni da incidenti passati |

**Maintained by**: G. Verardo
