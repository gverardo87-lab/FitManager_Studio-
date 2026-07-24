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

Il runbook agent-neutral per lavorare con Claude Code e Codex e'
`docs/operations/AI_ASSISTED_DEVELOPMENT_WORKFLOW.md`: deriva da `AGENTS.md` e non ne modifica la
precedenza. I bootstrap specifici puntano al nucleo comune senza duplicarlo.

## 2) Protocollo Senior di Delivery

### Unita' operative

- **Task**: la richiesta complessiva; puo' contenere piu' gate.
- **Gate**: la minima unita' coesa, verificabile e pubblicabile che lascia il branch rilasciabile
  per il proprio scope. E' l'unita' di commit/push.
- **Microstep**: una modifica interna al gate; si verifica subito, ma non richiede un commit se da
  sola non forma un'unita' rilasciabile.
- **HOLD**: impedisce di aprire il gate successivo; non impedisce di chiudere e pubblicare il gate
  corrente gia' verificato.

### Avvio obbligatorio

Prima di modificare file:

1. controllare branch, `HEAD`, delta col remoto e working tree senza mutarli;
2. attribuire ogni modifica esistente: i file dell'utente o estranei allo scope restano intatti e
   non vengono mai inclusi per comodita';
3. leggere la SPEC attiva e le sole fonti necessarie al layer;
4. scrivere una impact map breve con obiettivo, file/layer, invarianti, verifiche ed esclusioni;
5. ottenere il GO founder se manca una decisione materiale. Il GO sul gate autorizza il suo normale
   commit e push a verifica conclusa; serve un nuovo GO se cambiano scope, branch, remoto o policy.

### State machine del gate

```
ORIENTATO -> AUTORIZZATO -> RED* -> GREEN -> VERIFICATO -> FOLD-BACK
           -> COMMITTATO -> PUSHATO -> CHECKPOINT PULITO
```

`RED*` e' obbligatorio quando e' pratico scrivere un canary/regressione prima del fix; se non lo e',
il motivo va riportato. Le altre transizioni non si saltano.

1. fare un microstep utile alla volta e verificarlo subito;
2. eseguire i quality gate proporzionati al rischio;
3. classificare i finding prima di agire:
   - **in scope e bloccante**: correggere nel gate prima di `GREEN`;
   - **fuori scope ma release-critical**: registrare HOLD/nuovo gate, senza contaminarvi il gate
     corrente;
   - **informativo**: registrare il rischio/backlog senza allargare il diff;
4. fare il fold-back documentale previsto dal §11;
5. controllare `git diff --check`, stato e lista esatta dei file; stage solo dei path attribuiti;
6. controllare diff e stat staged, poi committare con il formato del §8;
7. push immediato su `FitManager_Studio` e verifica del delta col remoto;
8. aprire il gate successivo solo al checkpoint: nessuna modifica tracked attribuibile al gate
   precedente e branch remoto allineato.

Un gate docs-first che ratifica una decisione e il relativo code gate sono due gate distinti: il
primo va committato e pushato prima di iniziare il secondo. Se il fold-back deve citare l'hash esatto
dell'implementazione, usare due commit coesi nello stesso gate (implementazione, poi consuntivo) e
pusharli insieme; non aprire altro lavoro tra i due. Un gate docs-only non genera un commit vuoto per
auto-citare il proprio hash: registra messaggio/evidenze e riporta l'hash verificato nell'handoff.

Sono ammessi file dirty estranei soltanto se attribuiti esplicitamente (per esempio un asset locale
del founder), fuori scope e mai staged. Non sono ammessi `git add .`, reset distruttivi o bypass dei
quality gate. `git add -u` e' ammesso solo quando tutte le modifiche tracked appartengono al gate.

### Stop e reporting

Fermarsi prima del gate successivo se il gate corrente non e' verificato/pushato, se restano sue
modifiche tracked, se un finding cambia autorita'/scope, se una modifica non e' attribuibile o se un
verifier critico non e' disponibile. Dopo il push riportare sempre: commit, verifiche reali, rischi o
HOLD, stato Git/remoto e prossimo gate minimo.

Non nascondere i rischi. Non usare `BUILD_LOG.md` come sostituto del checkpoint Git e non accumulare
in un unico commit un gate concluso e la remediation di un finding successivo.

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
| `main` | Release stabile | Allineato a FitManager_Studio dopo ogni release |
| `hotfix/vX.Y.Z` | Fix urgente campo | Creato dal tag, merge back, poi eliminato |

### Workflow normale

1. Lavorare sempre su `FitManager_Studio`.
2. Eseguire un gate alla volta secondo il Protocollo Senior del §2.
3. Commit e push dopo ogni gate completato; il GO founder sul gate autorizza il checkpoint normale
   di quel gate su questo branch, senza richiesta duplicata.
4. Verificare dopo il push che `origin/FitManager_Studio...FitManager_Studio` sia `0 0`.
5. Non creare feature branch senza coordinamento esplicito.

### Release

1. Bump `__version__` in `api/__init__.py`.
2. Sync: `cd frontend && npm version X.Y.Z --no-git-tag-version`.
3. Commit: `release: vX.Y.Z — descrizione`.
4. Build: `bash tools/build/build-release.sh` (preflight+build+verify+seal+tag).
5. Aggiornare `CHANGELOG.md` con sezione nuova release (inclusa sezione `### Upgrade`).
6. Allineare main:
   ```bash
   git checkout main && git merge FitManager_Studio --ff-only && git push origin main
   git checkout FitManager_Studio
   ```

### Hotfix (bug critico da partner/campo)

Scenario: Alessio segnala un bug bloccante, ma su `FitManager_Studio` c'e' lavoro in corso non rilasciabile.

```bash
# 1. Creare branch dal tag dell'ultima release consegnata
git checkout -b hotfix/v1.0.9 v1.0.8

# 2. Fix + test
# ... applicare fix minimale ...
pytest tests/ -v

# 3. Bump version + release
# ... bump __version__, npm version ...
git commit -m "release: v1.0.9 — hotfix descrizione"
bash tools/build/build-release.sh

# 4. Merge back in FitManager_Studio
git checkout FitManager_Studio
git merge hotfix/v1.0.9

# 5. Allineare main + cleanup
git checkout main && git merge FitManager_Studio --ff-only && git push origin main
git checkout FitManager_Studio
git branch -d hotfix/v1.0.9
```

**Regole hotfix**:
- Solo fix minimale — nessuna feature, nessun refactor.
- Deve passare tutti i quality gate (pytest + ruff + next build).
- Merge back in `FitManager_Studio` OBBLIGATORIO (evita divergenza).
- Branch hotfix eliminato dopo merge (non resta nel repo).

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

1. `pytest tests/ -v` — l'intera suite raccolta dal runner deve passare
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

Pipeline 5 fasi (ADR-004). Procedura completa nella sezione 5 "Branching Strategy → Release".

```
1. PREFLIGHT  — git clean, version sync, pytest, ruff, next build
2. BUILD      — frontend standalone + backend exe + media staging + encryption
3. VERIFY     — smoke test su porta 9999, 5 health invariants
4. SEAL       — manifest.json con SHA-256, git info, safety gates
5. TAG        — git tag vX.Y.Z
```

Dettagli tecnici: `docs/operations/RELEASE_CHECKLIST.md`.

## 10) Incident Response

Quando si scopre un bug in produzione o un problema critico:

1. **Documentare** in `docs/incidents/INC-YYYY-MM-DD-titolo.md` (severita', root cause, fix)
2. **Aggiornare** `POSTMORTEMS.md` con la lezione appresa
3. **Aggiornare** checklist/guardrail se il bug era prevenibile
4. **Hotfix**: seguire procedura in sezione 5 "Branching Strategy → Hotfix"

Severita': P0 (sistema inutilizzabile) → P3 (cosmetico).

## 11) Ciclo di vita dei documenti (IL metodo — ratificato 2026-07-03)

**Principio: la POSIZIONE è lo STATO.** Un agente (o un umano) decide cosa caricare dal path, senza
dover leggere gli header. Contratto di contesto sintetico anche in `CLAUDE.md`.

| Specie | Casa | Ciclo di vita |
|--------|------|---------------|
| **ADR** (`docs/adr/`) | La LEGGE | Nasce quando cambia una regola del dominio. Immortale: mai archiviato, evolve per **Addendum**. Indice in `adr/README.md` |
| **SPEC** (`docs/specs/`) | Il lavoro APERTO | Nasce da/with un ADR, prescrive UN blocco. Riga `Stato:` obbligatoria in testa. **A chiusura blocco: consuntivo (commit, suite, esiti) + spostamento in `docs/archive/specs/` nello STESSO commit docs del gate** |
| **SSoT evergreen** (`docs/technical/`) | Com'è FATTO il sistema | FDM, TASSONOMIA, SECURITY_MODEL, TUNNEL, ecc. Aggiornati dal fold-back di ogni gate che li tocca. **Zero SPEC_*/IMPL_PLAN_* qui** (guard in `check-all.sh`) |
| **AUDIT/ROADMAP** | Fotografie | Foldate nelle decisioni che generano (ADR/SPEC), poi → `docs/archive/` con header di esito. Mai riferimento vivo |
| **LOG** | `docs/learning/BUILD_LOG.md` | UNICO log di sviluppo, append-only, mai riscritto. (`docs/upgrades/` dismesso 2026-07-03) |

**Definition of Done di un gate** (estende il Protocollo Senior §2):

```
implementazione + test → full suite verde → verifier adversariale (financial-invariant-verifier
sui money-path; docs-code-drift-auditor su richiesta) → FOLD-BACK DOCS (Stato spec consuntivato ·
INDEX · BUILD_LOG · ADR/Addendum se è cambiata una regola · archiviazione se il blocco è chiuso)
→ commit atomico → push → verifica allineamento remoto (GO del gate secondo §2)
```

Regole falsificabili (presidiate da guard, non da disciplina):
- nessuna `SPEC_*`/`IMPL_PLAN_*` vive in `docs/technical/`;
- nessuna spec con `Stato: ✅ IMPLEMENTATA` resta in `docs/specs/`;
- `docs/archive/` non è MAI contesto di lavoro.
