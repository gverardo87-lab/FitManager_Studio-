# Contribuire a FitManager AI Studio

Guida per sviluppatori che collaborano al progetto.

## Prerequisiti

| Requisito | Versione |
|-----------|----------|
| Python | 3.12+ |
| Node.js | 20+ |
| Git | 2.40+ |
| OS | Windows 10/11 |

## Setup ambiente

```bash
# 1. Clone e virtual environment
git clone https://github.com/gverardo87-lab/FitManager_Studio-.git
cd FitManager_Studio-
python -m venv venv
./venv/Scripts/pip install -e .

# 2. Frontend
cd frontend
npm install
cd ..

# 3. Verifica
bash tools/scripts/check-all.sh          # quality gate
./venv/Scripts/python -m pytest tests/ -v # suite backend completa
cd frontend && npm test                   # suite Vitest completa
```

## Struttura progetto

```
api/          → Backend (FastAPI + SQLModel + SQLite WAL)
frontend/     → Frontend (Next.js 16 + React 19 + shadcn/ui)
core/         → Moduli AI dormenti (Langchain + Ollama)
data/         → Database, media, licenza, log (sopravvive a upgrade)
tools/        → Script build, admin, utility
docs/         → Documentazione organizzata per dominio
tests/        → Test backend (pytest)
```

Contratto operativo: leggere prima `AGENTS.md`; il runbook condiviso è
`docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md`. Dettagli architetturali:
`CLAUDE.md` (root) → `api/CLAUDE.md` → `frontend/CLAUDE.md`.

## Avvio sviluppo

```bash
# Backend (porta 8000)
./venv/Scripts/uvicorn api.main:app --port 8000 --host 0.0.0.0

# Frontend (porta 3000, in un altro terminale)
cd frontend && npm run dev
```

Formula porte: `frontend_port - 3000 + 8000 = backend_port`.

## Branching

| Branch | Scopo |
|--------|-------|
| `main` | Backup stabile, allineato a FitManager_Studio |
| `FitManager_Studio` | Branch di sviluppo principale |

Lavorare sempre su `FitManager_Studio`. Non creare feature branch senza coordinamento.

## Commit

### Formato

```
area: descrizione concisa
```

Aree: `api:`, `frontend:`, `dashboard:`, `fix:`, `docs:`, `security:`, `build:`, `installer:`, `ux:`, `chore:`

### Regole

1. **Quality gate obbligatorio**: un pre-commit hook esegue automaticamente `ruff check api/` e (se tocchi `frontend/`) `next build`. Il commit viene bloccato se fallisce.
2. **Ogni commit lascia il branch rilasciabile** per il proprio scope.
3. **Commit atomici**: una unita' coesa e verificabile per commit.
4. **Un gate alla volta**: il gate è l'unità di commit/push; non aprire il successivo finché il
   precedente non è pushato, il delta col remoto non è `0 0` e non restano sue modifiche tracked.
5. **Stage intenzionale**: aggiungere solo i path attribuiti al gate; mai includere file locali o
   modifiche altrui per comodità.

### Esempi

```
api: aggiungi endpoint dashboard birthday alerts
fix: cascade FK su delete sessioni (INC-2026-03-28b)
frontend: tab Allenamento nel profilo cliente
docs: aggiornamento BP v4.3
security: rate limiter su endpoint auth
```

## Quality gate

Il pre-commit hook esegue automaticamente:

```bash
# Backend: lint Python
ruff check api/

# Frontend: build TypeScript (solo se file frontend/ modificati)
cd frontend && npx next build
```

Per eseguirlo manualmente: `bash tools/scripts/check-all.sh`

`git commit --no-verify` è vietato nel workflow normale. Un bypass richiede autorizzazione founder
esplicita, contesto di incidente documentato e ripetizione manuale dei gate saltati prima del push.

## Test

```bash
# Backend — tutti i test
./venv/Scripts/python -m pytest tests/ -v

# Backend — singolo file
./venv/Scripts/python -m pytest tests/test_pay_rate.py -v

# Frontend
cd frontend && npm test
```

I test backend girano prima di ogni release (fase PREFLIGHT del build pipeline).

## Release

La release segue una pipeline a 5 fasi (ADR-004):

```
PREFLIGHT → BUILD → VERIFY → SEAL → TAG
```

Solo il maintainer esegue release. Comando unico: `bash tools/build/build-release.sh`.

La versione SSoT vive in `api/__init__.py` (`__version__`). Il build script verifica che `frontend/package.json` sia allineato.

Dettagli: `docs/operations/RELEASE_CHECKLIST.md`.

## Database

3 database separati, 3 session factory:

| DB | Scopo | Mutabile | Alembic |
|----|-------|----------|---------|
| `crm.db` | Dati business (clienti, contratti, agenda) | Si | Si |
| `catalog.db` | Catalogo esercizi + tassonomia scientifica | Read-only | No |
| `nutrition.db` | Catalogo alimenti CREA 2019 | Read-only | No |

**Non toccare mai** `catalog.db` e `nutrition.db` senza coordinamento. Sono cataloghi scientifici costruiti incrementalmente.

Migrazioni:
```bash
./venv/Scripts/alembic upgrade head                           # crm.db
./venv/Scripts/alembic -c alembic_nutrition.ini upgrade head  # nutrition.db
```

## Regole non negoziabili

1. **Privacy-first**: dati clinici e finanziari mai esposti in viste pubbliche
2. **Multi-tenant safety**: ogni query filtra per `trainer_id`
3. **Bouncer Pattern**: ogni endpoint verifica ownership. Non trovato = 404, mai 403
4. **Mass assignment prevention**: `trainer_id` e `id` mai in schema Create
5. **Soft delete**: `deleted_at` su tutte le tabelle business. SELECT filtra sempre
6. **Dati in `data/`**: tutto sotto `data/`. Sopravvive a upgrade
7. **Italiano nativo**: UI in italiano, codice in inglese

Lista completa: `CLAUDE.md` sezione "Regole non negoziabili".

## Documentazione

| Cosa cerchi | Dove guardare |
|-------------|---------------|
| Architettura, regole, pitfalls | `CLAUDE.md` (root + api/ + frontend/) |
| Decisioni architetturali | `docs/adr/README.md` (10 ADR) |
| Changelog release | `CHANGELOG.md` |
| Business plan, pricing | `docs/business/BUSINESS_PLAN.md` |
| Sicurezza, threat model | `docs/technical/SECURITY_MODEL.md` |
| Procedure operative | `docs/operations/` |
| Post-mortem incidenti | `docs/incidents/` |
| Indice completo | `docs/INDEX.md` |

## Segnalazione bug

Documentare in `docs/incidents/` con formato:

```
INC-YYYY-MM-DD-titolo-breve.md
```

Contenuto: severita' (P0-P3), root cause, fix, lezione appresa.
