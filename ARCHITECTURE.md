# ARCHITECTURE.md — FitManager AI Studio

> **Cos'è questo documento.** La mappa d'insieme del sistema: *come è fatto* e *perché ha questa forma*.
> È il punto di partenza per chi deve orientarsi prima di toccare un singolo pezzo — la bussola macro.
>
> **Cosa NON è.** Non è un runbook operativo (→ `CLAUDE.md`), non è una guida di un singolo sottosistema
> (→ `docs/technical/`, `docs/scientific/`), non è il registro delle decisioni (→ `docs/adr/`).
> Quando una sezione qui sotto diventa "come si fa nel dettaglio", il dettaglio vive altrove e questo
> documento ci punta. Tieni questo file **piccolo e stabile**: descrive la struttura, non l'implementazione.
>
> **Numeri volatili** (conteggi file, esercizi, versione) non vivono qui: hanno una sola casa
> (versione → `api/__init__.py`; conteggi DB → `docs/operations/DB_INTEGRITY_AUDIT_*.md`).
> Questo evita che l'overview diventi l'ennesimo posto da aggiornare e contraddire.

---

## 1. Cos'è FitManager, in una frase

Un **CRM locale per professionisti del fitness a P.IVA** (chinesiologi, personal trainer), che gira
**sul computer del trainer** — non su un server centrale. I dati clinici e finanziari dei clienti restano
su quella macchina; il cloud non è mai obbligatorio.

Questa singola scelta — **local-first, privacy-first** — determina quasi tutta l'architettura che segue.
Da essa discendono: la distribuzione come applicazione nativa installabile, la sicurezza incentrata sulla
licenza con hardware binding invece che sull'auth di un backend cloud, e il tunnel data-blind necessario
per esporre il portale pubblico senza che nessuno (nemmeno il produttore) tocchi i dati sanitari.

## 2. I tre attori del sistema

Capire l'architettura significa capire chi la usa e da dove:

```
┌────────────────────┐         ┌────────────────────┐         ┌────────────────────┐
│   TRAINER          │         │  CLIENTE FINALE    │         │  AVGV (produttore) │
│  usa il CRM da     │         │  apre link pubblici│         │  firma licenze,    │
│  tablet/PC in LAN  │         │  da casa, su       │         │  gestisce VPS edge,│
│  (rete locale)     │         │  Internet          │         │  NON vede i dati   │
└─────────┬──────────┘         └─────────┬──────────┘         └─────────┬──────────┘
          │ LAN                          │ Internet (tunnel)            │ amministrazione
          v                              v                              v
   ┌───────────────────────────────────────────────┐          firma JWT licenza
   │           PC del trainer (la "macchina")        │          provisioning DNS
   │   frontend :3000  ──>  api :8000  ──>  *.db     │          VPS edge (SNI passthrough)
   └───────────────────────────────────────────────┘
```

- Il **trainer** è l'unico utente autenticato del CRM. Accede in LAN; il CRM è invisibile da Internet.
- Il **cliente finale** non ha account: riceve link monouso (anamnesi, scheda) che raggiungono la macchina
  del trainer **solo** attraverso il tunnel, e **solo** sulle route `/public/*`.
- **AVGV** non è un attore runtime sui dati: firma le licenze offline e gestisce l'infrastruttura edge che
  instrada il traffico senza poterlo leggere (principio **P2 data-blind**).

## 3. Topologia runtime

Tre processi, una macchina:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────────────┐
│  frontend/  │────>│    api/      │────>│  data/*.db (SQLite WAL)   │
│  Next.js 16 │     │  FastAPI     │     │  crm · catalog · nutrition│
│  :3000      │     │  :8000       │     └──────────────────────────┘
└─────────────┘     └──────────────┘
```

- **Frontend** (Next.js 16 / React 19 / TS): unica origine che l'utente apre. Proxa `/api/*` e `/media/*`
  al backend same-origin. In produzione fa anche da terminatore TLS per il tunnel.
- **Backend** (FastAPI / SQLModel): unica fonte di verità per dati e logica. Espone REST + JWT.
  In produzione binda **`127.0.0.1`** (mai esposto direttamente).
- **Porte**: frontend 3000, backend 8000. Formula generica: `backend = frontend - 3000 + 8000`.
  Il frontend deduce la base URL API da `window.location` a runtime — zero config.

Layer dormiente: **`core/`** (Langchain + Ollama) ospita moduli AI non sul percorso critico di lancio.
Non è importato dal backend di produzione.

## 4. La decisione portante: tre database separati

È la scelta architetturale più importante del sistema (ADR-003). I dati hanno tre nature diverse e
**non vanno mescolati**:

| Database | Natura | Contenuto | Mutabilità | `trainer_id` |
|----------|--------|-----------|------------|--------------|
| **`crm.db`** | Business del trainer — **SACRO** | 26 tabelle: clienti, contratti, rate, agenda, cassa, schede, anamnesi, comunicazioni, audit | Read/write, backup/restore | Sì — tenant-isolated |
| **`catalog.db`** | Catalogo scientifico | 10 tabelle: esercizi builtin + tassonomia (muscoli/articolazioni/condizioni) + media | **Read-only**, shipped con l'installer | No |
| **`nutrition.db`** | Catalogo alimentare | 8 tabelle: alimenti CREA 2019/USDA, ricette, porzioni LARN, template dieta | **Read-only**, shipped con l'installer | No |

**Perché separati e non un unico DB:**
- I cataloghi scientifici sono **dati del prodotto**, costruiti incrementalmente e cifrati nel bundle; il
  business è **dato del trainer**, che vive solo sulla sua macchina e va salvato/ripristinato.
  Naturalezza di backup diversa, ciclo di vita diverso, proprietà diversa.
- `crm.db` non duplica mai tabelle di catalogo. I riferimenti cross-DB sono **per ID, senza FK constraint**
  (integrità a livello applicativo, es. `componenti_pasto.alimento_id`).
- **Alembic gestisce SOLO `crm.db`** (`include_name` esclude catalog+nutrition). I cataloghi non hanno
  migrazioni: sono costruiti da seed ORM + script di popolazione offline.

**Tre session factory, una per DB** (`api/database.py`):

```python
from api.database import get_session            # crm.db      (business, tenant-isolated)
from api.database import get_catalog_session    # catalog.db  (esercizi + tassonomia, read-only)
from api.database import get_nutrition_session   # nutrition.db (alimenti + template, read-only)
```

⚠️ **Pitfall strutturale.** Le funzioni dual-session (safety engine, profile resolver, session prep)
DEVONO usare `catalog_session` per le tabelle di `catalog.db` e `session` per `crm.db`. Confonderle
produce un crash 500 silenzioso che i test in-memory a engine singolo non catturano.
Incidente: `docs/incidents/INC-2026-03-28-safety-engine-blind-spot.md`.

## 5. Ciclo di vita di una richiesta

Come una richiesta del trainer attraversa il sistema, dall'alto in basso:

```
1. Browser (trainer in LAN)
      │  fetch('/api/contratti/42')  con cookie JWT
      v
2. Next.js proxy (frontend/src/proxy.ts)
      │  auth boundary: route protette richiedono cookie; /api/public/* è pubblico
      v
3. FastAPI router (api/routers/contracts.py)
      │  get_current_trainer()  → valida JWT → trainer_id
      │  BOUNCER: la risorsa appartiene a questo trainer_id? No → 404 (mai 403)
      v
4. Business logic + SQLModel (catena ownership via FK: Rate → Contract → trainer_id)
      │  transazione atomica: operazioni multi-tabella = un solo commit()
      v
5. crm.db (SQLite WAL) — SELECT filtra sempre deleted_at IS NULL (soft delete)
```

Quattro invarianti non negoziabili visibili in questo flusso (dettaglio in `api/CLAUDE.md`):
- **Multi-tenant safety**: ogni query filtra per `trainer_id`. Mai bypassare l'ownership.
- **Bouncer Pattern**: non trovato = **404**, mai 403 (non rivelare l'esistenza di dati altrui).
- **Mass assignment prevention**: `trainer_id` e `id` mai negli schema Create; Pydantic `extra: "forbid"`.
- **Atomic transactions + soft delete**: un commit per operazione; `deleted_at` invece di hard delete.

## 6. Architettura a strati

### Backend (`api/`) — dettaglio in `api/CLAUDE.md`
```
routers/    REST + Bouncer Pattern (un modulo per dominio)
schemas/    Pydantic v2 — il contratto verso il frontend (extra: "forbid")
services/   business logic: contract integrity, safety engine, training science, tunnel, rate limiter
models/     SQLModel ORM (table=True) — mappato sui 3 DB
database.py tri-engine + 3 session factory + PRAGMA (WAL, foreign_keys, busy_timeout)
```
Il backend è la **SSoT scientifica**: ogni costante/parametro dei motori vive qui. Il frontend non
duplica mai una costante scientifica — la consuma via API.

### Frontend (`frontend/src/`) — dettaglio in `frontend/CLAUDE.md`
```
app/         App Router — route group (dashboard) + login/setup/licenza + public portal
components/  organizzati per dominio (clients, contracts, workouts, dashboard, ...)
hooks/       un modulo React Query per dominio; ogni mutation invalida le query correlate + toast
lib/         api-client (axios + JWT interceptor), format (toISOLocal!), smart-programming, ...
types/api.ts il contratto TypeScript ↔ Pydantic (Optional[X] → X | null)
```
Regole strutturali: max 300 LOC per file di logica, auth a 3 layer (proxy → AuthGuard → interceptor),
mai `toISOString()` nei payload (perde il fuso → `toISOLocal()`).

## 7. Preoccupazioni trasversali

| Concern | Forma | Approfondimento |
|---------|-------|-----------------|
| **Multi-tenancy** | `trainer_id` su ogni riga di `crm.db` + Bouncer + Deep Relational IDOR | `api/CLAUDE.md` |
| **Integrità contratti** | Contract Integrity Engine: 12 livelli (residual, auto-close simmetrico, overpayment, cascade) | `api/CLAUDE.md` |
| **Sicurezza prodotto** | Licenza JWT RS256 + hardware binding; bundle sanitization; DB encryption AES-256-GCM; Nuitka | `docs/technical/SECURITY_MODEL.md` · ADR-005 · ADR-007 |
| **Portale pubblico** | Share token monouso → route `/public/*` → tunnel FRP; rate limiter dedicato | `docs/technical/TUNNEL_SECURITY_BOUNDARY.md` · ADR-009 · ADR-011 |
| **Tunnel data-blind** | VPS edge fa SNI passthrough; TLS terminato sulla macchina del trainer (P2) | `docs/technical/TUNNEL_ARCHITECTURE.md` (design + build + operations) |
| **Motori scientifici** | Deterministici, spiegabili, auditabili; backend = unica fonte | `docs/scientific/*_CERTIFICATION.md` |
| **Comunicazioni** | WhatsApp via deep-link `wa.me` (zero API esterne); ogni invio loggato | `CLAUDE.md` §WhatsApp |

### Motori scientifici (vista d'insieme)
Sei motori deterministici trasformano FitManager da gestionale a strumento professionale. Sono **spiegabili
e riproducibili** — nessuna black box. La SSoT dei loro ~717 parametri è `docs/scientific/PARAMETER_REGISTRY.md`.

| Motore | Funzione |
|--------|----------|
| Training Science | Periodizzazione, EMG, volume MEV/MAV/MRV |
| Training Intelligence | Analisi post-esecuzione: dose-response, balance, recovery, alert |
| Workout Diff | Piano vs eseguito, compliance % |
| Safety Engine | 47 condizioni × 80 pattern rules su anamnesi cliente |
| Nutrition Science | Piano LARN, scoring 3 assi (UI rimossa, backend preservato) |
| Smart Programming | Scoring 14D (frontend, consumer del backend SSoT) |

## 8. Distribuzione e packaging

L'app è un **installer Windows nativo**, non un servizio cloud:

```
Python  ──Nuitka──>  C ──>  eseguibile x86-64 nativo  ┐
Next.js ──standalone build──>  bundle Node              ├──> Inno Setup ──> installer .exe
catalog.db + nutrition.db  ──cifrati AES-256-GCM──>     ┘
```

- **Nuitka** compila il Python in C nativo (zero bytecode decompilabile). Fallback: PyInstaller
  (`fitmanager.spec` preservato per rollback).
- In **compiled mode** (`is_compiled()` rileva Nuitka/PyInstaller): chiave pubblica licenza embedded,
  enforcement sempre ON, Swagger/Redoc disabilitati, DB cifrati deserializzati in-memory a runtime.
- **`data/` sopravvive agli upgrade**: DB, media, licenza, `.env`, log vivono tutti lì. Zero path assoluti
  hardcoded — si usa `DATA_DIR` da `api/config.py` (gestisce `sys.frozen`).
- **Release**: pipeline 5 fasi (ADR-004) — preflight → build → verify → seal → tag. Versione SSoT in
  `api/__init__.py`. Entry point unico: `tools/build/build-release.sh`.

## 9. Dove andare più a fondo

Questo documento è l'hub. Per il dettaglio, segui il puntatore:

| Vuoi capire… | Leggi |
|--------------|-------|
| Regole operative, comandi, pitfall cross-layer | `CLAUDE.md` (+ `api/`, `frontend/`, `core/` per dominio) |
| Pattern e invarianti del backend | `api/CLAUDE.md` |
| Pattern e pitfall del frontend | `frontend/CLAUDE.md` |
| Perché una scelta è stata fatta | `docs/adr/` (11 ADR, indice in `adr/README.md`) |
| Modello di sicurezza completo | `docs/technical/SECURITY_MODEL.md` |
| Come funziona il tunnel (design, build, ops) | `docs/technical/TUNNEL_ARCHITECTURE.md` |
| Certificazione dei motori scientifici | `docs/scientific/` |
| Stato fisico dei DB (conteggi reali) | `docs/operations/DB_INTEGRITY_AUDIT_*.md` |
| Indice di tutta la documentazione | `docs/INDEX.md` |
| Modello di business e numeri | `docs/business/BUSINESS_PLAN.md` |

---

**Mantenuto da**: G. Verardo · **Ruolo del file**: Layer 3 governance (Tier-1 normativo) · **Versione prodotto**: vedi `api/__init__.py`
