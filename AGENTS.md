# AGENTS.md - FitManager AI Studio

Questo file e' il contratto operativo unico per gli agenti che lavorano nel repository.
Obiettivo: mantenere velocita di consegna alta senza perdere affidabilita', privacy e chiarezza.

## 1) Fonti autorevoli

Quando le istruzioni confliggono, usare questo ordine:

1. system/developer/runtime constraints
2. `AGENTS.md`
3. `MANIFESTO.md`
4. `LAUNCH_SCOPE.md`
5. `api/CLAUDE.md`, `frontend/CLAUDE.md`, `core/CLAUDE.md` solo per il layer toccato
6. `POSTMORTEMS.md`
7. runbook, upgrade docs e altra documentazione solo quando servono

Le spec completate sono archiviate in `docs/archive/specs/` come riferimento storico.

Il root `CLAUDE.md` e' l'entry point letto automaticamente da Claude Code.
Per regole operative dettagliate, riferirsi a questo file e ai layer-specifici.

## 2) Delivery Loop

Per ogni task:

1. scrivere un impact map breve:
   - obiettivo
   - file/layer toccati
   - invarianti da preservare
2. fare un microstep utile alla volta
3. verificare subito il microstep
4. riportare:
   - cosa e' cambiato
   - cosa e' stato verificato
   - rischi/gap emersi
   - prossimo passo minimo

Non nascondere i rischi. Se emergono, esplicitarli presto.

## 3) Principi non negoziabili

- Privacy-first nelle viste visibili al cliente.
- Dati finanziari confinati nei contesti finance dedicati.
- Multi-tenant safety: mai bypassare ownership checks.
- Auditabilita' per operazioni critiche.
- Determinismo nei flussi business-critical.
- Nessun path assoluto hardcoded.
- Dati persistenti solo in `data/`.
- Il CRM core deve restare usabile senza dipendenza AI obbligatoria.

## 4) Guardrail ingegneristici

### Backend

- Preservare Bouncer Pattern e Deep Relational IDOR checks.
- Prevenire mass assignment.
- Tenere atomiche le operazioni multi-entita'.
- Mantenere audit log coerenti sulle transizioni critiche.

### Frontend

- Tenere il type sync con `frontend/src/types/api.ts`.
- Invalidare le query in modo simmetrico sulle operazioni inverse.
- Gestire sempre loading/error/empty state.
- Evitare dati sensibili nelle overview di default.
- Applicare le skill disponibili (`.agents/skills/`) quando il task lo richiede.

### Cross-layer

- Nessuna nuova policy di prodotto inventata nei docs o nel codice.
- I documenti storici non devono diventare regole operative.
- Preferire la soluzione piu' semplice e robusta compatibile con il launch scope.
- Evitare refactor larghi, nuove astrazioni o nuova documentazione se non richiesti dal task.

## 5) Branching Strategy

| Branch | Scopo | Regole |
|--------|-------|--------|
| `FitManager_Studio` | Sviluppo attivo | Tutti i commit vanno qui |
| `main` | Backup stabile | Allineato a FitManager_Studio dopo ogni milestone |

**Workflow**:
1. Lavorare sempre su `FitManager_Studio`.
2. Push dopo ogni step completato (commit intermedi frequenti).
3. Allineare `main` dopo ogni release o milestone significativa.
4. Non creare feature branch senza coordinamento esplicito.

## 6) Collaborazione e documentazione

Quando la task tocca codice condiviso o piu' layer, coordinare esplicitamente per evitare conflitti.
A fine task: verifiche reali e note sui rischi residui.

Per nuovi collaboratori: leggere `CONTRIBUTING.md` come entry point.

## 7) Quality Gates

### Automatici (pre-commit hook)

Il pre-commit hook blocca il commit se:
- `ruff check api/` fallisce (sempre eseguito)
- `next build` fallisce (eseguito solo se file in `frontend/` sono staged)

### Manuali (per scope specifico)

| Scope toccato | Verifica richiesta |
|---------------|-------------------|
| DB/schema | Migrazione + test backend pertinenti |
| Cash/ledger | Controlli integrita' contabile |
| Safety engine | QA clinica dedicata |
| Backup/installer | Backup → mutate → restore |
| Guide/help | Audit copertura + link integrity + responsive |
| Docs/process | Review coerenza cross-doc |

Mai dichiarare "done" senza evidenza di verifica.

### Pre-release (build-release.sh PREFLIGHT)

1. `pytest tests/ -v` — tutti i 361+ test devono passare
2. `ruff check api/` — zero warning
3. `next build` — zero errori TypeScript
4. Version sync — `api/__init__.py` == `frontend/package.json`

## 8) Commit Standard

Commit solo di unita' coese e verificabili.

### Formato

```
area: descrizione concisa
```

### Aree

| Prefisso | Quando |
|----------|--------|
| `api:` | Backend (endpoint, modelli, servizi) |
| `frontend:` | Frontend (componenti, hook, pagine) |
| `dashboard:` | Dashboard e workspace |
| `fix:` | Bug fix cross-layer |
| `docs:` | Documentazione |
| `security:` | Sicurezza, hardening |
| `build:` | Pipeline build, installer |
| `ux:` | Miglioramenti UX |
| `chore:` | Manutenzione, cleanup |
| `release:` | Release (solo per tag version) |

### Regole

- Ogni commit deve lasciare il branch rilasciabile per il proprio scope.
- Commit atomici: una unita' coesa per commit, non accumulare.
- Formato release: `release: vX.Y.Z — descrizione breve`.

## 9) Release Workflow

Pipeline 5 fasi (ADR-004):

```
1. PREFLIGHT  — git clean, version sync, pytest, ruff, next build
2. BUILD      — frontend standalone + backend exe + media staging + encryption
3. VERIFY     — smoke test su porta 9999, 5 health invariants
4. SEAL       — manifest.json con SHA-256, git info, safety gates
5. TAG        — git tag vX.Y.Z
```

**Procedura**:
1. Aggiornare `__version__` in `api/__init__.py`
2. Sync: `cd frontend && npm version X.Y.Z --no-git-tag-version`
3. Commit: `release: vX.Y.Z — descrizione`
4. Build: `bash tools/build/build-release.sh`
5. Aggiornare `CHANGELOG.md` con la nuova sezione

Dettagli: `docs/operations/RELEASE_CHECKLIST.md`.

## 10) Incident Response

Quando si scopre un bug in produzione o un problema critico:

1. **Documentare** in `docs/incidents/INC-YYYY-MM-DD-titolo.md` (severita', root cause, fix)
2. **Aggiornare** `POSTMORTEMS.md` con la lezione appresa
3. **Aggiornare** checklist/guardrail se il bug era prevenibile
4. **Hotfix**: commit diretto su `FitManager_Studio`, release patch (bump Z)

Severita': P0 (sistema inutilizzabile) → P3 (cosmetico).
