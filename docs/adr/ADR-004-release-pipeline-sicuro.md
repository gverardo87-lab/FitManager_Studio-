# ADR-004: Release Pipeline Sicuro per Distribuzione Locale

**Data**: 2026-03-21
**Stato**: Accettata
**Autori**: gvera + Claude Opus 4.6

---

## Contesto

FitManager e' un software installato localmente sul PC del cliente (chinesiologi,
personal trainer, professionisti fitness). Non c'e' cloud, non c'e' auto-update,
non c'e' CI/CD remoto. Ogni release e' un `.exe` che il cliente installa manualmente.

Fino alla v1.0.3 il processo di build era funzionante ma fragile:

| Problema emerso | Conseguenza reale |
|----------------|-------------------|
| `crm.db` con dati reali finito nell'installer | Dati di Chiara Bassani esposti al cliente |
| License enforcement disabilitato di default | App funzionava senza licenza se avviata senza launcher |
| Versione definita in 4 file separati | Drift tra backend, frontend e installer |
| Nessun check post-build | Artifact potenzialmente rotto scoperto solo dal cliente |
| Build da working tree sporco | Codice non committato nell'artifact, non riproducibile |
| Nessun manifest ne' tag | Impossibile ricostruire un artifact o sapere cosa contiene |

La v1.0.4 ha introdotto 3 safety gate nel build pipeline e il fix del license
enforcement, ma il processo resta manuale e privo di verifica end-to-end.

## Decision Drivers

1. **Il cliente non puo' fare debug** — se l'installer e' rotto, non c'e' recovery
   automatico. Il danno reputazionale e' immediato e totale.
2. **Siamo un team di 1** — nessun QA, nessun reviewer. Il pipeline deve essere
   il nostro QA automatico.
3. **Privacy sacra** — un data leak (crm.db nel bundle) e' un incidente grave,
   non un bug. Zero tolleranza.
4. **Riproducibilita'** — tra 6 mesi devi poter ricostruire esattamente lo stesso
   artifact da un tag git. Senza questo, il debugging post-deploy e' impossibile.
5. **Semplicita'** — niente CI/CD cloud, niente Docker, niente pipeline YAML.
   Tutto gira con `bash` sul PC di sviluppo. Deve restare cosi'.

---

## Decisione

### 1. Version Single Source of Truth

**`api/__init__.py`** e' l'unica fonte della versione. Tutto il resto la legge.

```
api/__init__.py                    ← UNICA definizione: __version__ = "X.Y.Z"
  ↓ letto da build-release.sh
build-installer.sh                 ← variabile, non hardcodata
  ↓ passato come parametro ISCC /D
fitmanager.iss                     ← riceve MyAppVersion via /D, non #define statico
  ↓ synced automaticamente pre-build
frontend/package.json              ← aggiornato dallo script
```

**Regola**: il version bump si fa in UN solo file. Il pipeline propaga.
Mai piu' cercare "1.0.3" in 4 posti e sperare di non dimenticarne uno.

### 2. Release Pipeline a 5 Fasi

Ogni release passa per 5 fasi sequenziali. Nessuna puo' essere saltata.

```
PREFLIGHT ──> BUILD ──> VERIFY ──> SEAL ──> TAG
```

#### Fase 1: PREFLIGHT (gate di ingresso)

Precondizioni obbligatorie prima di qualsiasi build:

| Check | Motivazione | Bloccante |
|-------|-------------|-----------|
| Git working tree pulito | Riproducibilita' — l'artifact deve corrispondere a un commit | Si |
| `pytest tests/ -v` passa | Nessuna regressione nel business logic | Si |
| `ruff check api/` pulito | Nessun warning lint nel backend | Si |
| `next build` senza errori TS | Nessun errore di tipo nel frontend | Si |
| Version bump committato | La versione nel codice corrisponde a quella che stai rilasciando | Si |

Se anche un solo check fallisce, il build non parte. Nessun `--skip-checks`
per i test — solo lint e frontend build possono essere skippati in emergenza
estrema con `--skip-lint` (e viene loggato nel manifest come warning).

#### Fase 2: BUILD (produzione artifact)

La fase build resta come oggi, con 3 sotto-step + safety gate:

1. `build-frontend.sh` → Next.js standalone
2. `build-backend.sh` → PyInstaller exe
3. `build-media.sh` → staging media esercizi
4. Staging `release-data/` (catalog.db, nutrition.db, license_public.pem)
5. **Safety Gate 1**: CRM data leak prevention (crm.db assente da dist/)
6. **Safety Gate 2**: ISS reference check (fitmanager.iss non referenzia crm.db)
7. **Safety Gate 3**: Nutrition DB integrity (soglie minime template/alimenti)
8. ISCC → produce `FitManager_Setup_{version}.exe`

#### Fase 3: VERIFY (smoke test automatico)

Dopo la produzione dell'installer, il pipeline avvia l'exe buildato e verifica
che il software funzioni realmente:

```
1. Avvia dist/fitmanager/fitmanager.exe su porta effimera (es. 9999)
2. Attendi /health (max 30 secondi)
3. Verifica 5 invarianti:
   - version == versione attesa
   - db == "connected"
   - catalog == "connected"
   - license_enforcement_enabled == true
   - distribution_mode == "installer"
4. Shutdown
```

Se anche un solo invariante fallisce, il build e' dichiarato FAIL.
L'installer prodotto non va distribuito.

**Perche' questo check e' critico**: PyInstaller puo' produrre un exe che si
compila senza errori ma crasha al runtime (import mancante, path rotto,
dipendenza non inclusa). Questo e' l'unico modo per scoprirlo prima del cliente.

#### Fase 4: SEAL (manifest + hash)

Il pipeline produce un file `manifest.json` accanto all'installer:

```json
{
  "version": "1.0.4",
  "build_date": "2026-03-21T18:30:00+01:00",
  "git_commit": "00b7a4e",
  "git_branch": "fit_launch_01",
  "artifact": "FitManager_Setup_1.0.4.exe",
  "artifact_sha256": "A1B2C3...",
  "artifact_size_bytes": 104857600,
  "preflight": {
    "pytest": "pass (326/326)",
    "ruff": "pass",
    "next_build": "pass",
    "git_clean": true
  },
  "safety_gates": {
    "crm_leak_check": "pass",
    "iss_reference_check": "pass",
    "nutrition_integrity": "pass"
  },
  "smoke_test": {
    "health_endpoint": "pass",
    "version_match": true,
    "enforcement_enabled": true
  },
  "contents": {
    "catalog_exercises": 500,
    "nutrition_templates": 12,
    "nutrition_alimenti": 880
  }
}
```

Il manifest e' la **carta d'identita'** dell'artifact. Viene archiviato insieme
all'installer. Tra 6 mesi, apri il manifest e sai esattamente:
- quale commit lo ha prodotto
- quali test sono passati
- cosa contiene (quanti esercizi, template, alimenti)
- l'hash per verificare integrita'

#### Fase 5: TAG (sigillo git)

```bash
git tag -a "v1.0.4" -m "Release 1.0.4 — license enforcement + safety gates"
```

Il tag e' il sigillo finale. Significa:
- `git checkout v1.0.4` → ricostruisci lo stesso artifact
- `git log v1.0.3..v1.0.4` → vedi cosa e' cambiato tra release
- `git diff v1.0.3 v1.0.4` → diff preciso

Il tag si crea SOLO dopo che le fasi 1-4 sono passate.
Mai taggare un commit il cui build non e' stato verificato.

### 3. Struttura File

```
tools/build/
  build-release.sh          ← ENTRY POINT UNICO per release
  build-installer.sh        ← sub-step: build puro (chiamato da build-release.sh)
  build-frontend.sh         ← sub-step: Next.js standalone
  build-backend.sh          ← sub-step: PyInstaller
  build-media.sh            ← sub-step: staging media
  fitmanager.spec            ← spec PyInstaller

dist/
  FitManager_Setup_1.0.4.exe   ← artifact
  manifest.json                 ← carta d'identita' dell'artifact
  release-data/                 ← snapshot immutabili per packaging
```

### 4. Comandi Operativi

```bash
# ── SVILUPPO (quotidiano) ──
bash tools/scripts/check-all.sh                    # lint + build check rapido

# ── RELEASE (quando pronto per il cliente) ──
# 1. Bump versione in api/__init__.py
# 2. Commit: "release: v1.0.X — descrizione"
# 3. Build completo:
bash tools/build/build-release.sh                  # 5 fasi automatiche
# 4. Se tutto verde: artifact pronto in dist/
```

### 5. Regole Non Negoziabili

1. **Mai distribuire un artifact senza manifest** — se non c'e' il manifest,
   il build non e' stato verificato. Non shipparlo.

2. **Mai buildare da working tree sporco** — se hai modifiche non committate,
   committa o stash prima. Il build deve corrispondere a un commit preciso.

3. **Mai skippare lo smoke test** — il fatto che PyInstaller compili senza
   errori non significa che l'exe funzioni. Il smoke test e' la prova.

4. **Mai modificare la versione a mano in piu' di un file** — tocchi solo
   `api/__init__.py`. Se devi toccare altro, il pipeline e' rotto.

5. **Mai rilasciare senza tag git** — il tag e' il contratto. Senza tag,
   non puoi ricostruire l'artifact ne' debuggare un problema del cliente.

6. **Mai rilasciare crm.db nel bundle** — i safety gate lo impediscono,
   ma la regola vale anche se i gate vengono momentaneamente disabilitati
   per debugging. Il crm.db contiene dati del trainer. Punto.

---

## Ciclo di Vita Completo della Release

```
FASE              CHI            COSA                                   OUTPUT
─────────────────────────────────────────────────────────────────────────────────
Sviluppo          Dev            Codice, test, commit funzionali        Branch aggiornato
Quality gate      Dev            check-all.sh                           Lint + TS clean
Version bump      Dev            Modifica api/__init__.py               Commit "release: vX.Y.Z"
Build             Script         build-release.sh (5 fasi)              Installer + manifest
Archiviazione     Dev            Copia installer + manifest in archivio Backup release
Deploy            Dev + Cliente  Installer al cliente                   Software installato
Post-install      Cliente        Setup wizard + license key             Sistema funzionante
Verifica          Dev            /health + checklist                    Release chiusa
Tag               Dev            git tag vX.Y.Z                         Sigillo
```

---

## Consequences

### Positive
- Ogni artifact e' riproducibile da un tag git
- Il smoke test impedisce di shippare exe rotti
- Il manifest documenta cosa c'e' nell'artifact senza doverlo aprire
- La version SSoT elimina il drift tra componenti
- Il preflight impedisce build da stato sporco

### Negative
- Il build richiede ~2 minuti in piu' (smoke test)
- Il version bump richiede un commit dedicato prima del build
- Rigidita': non puoi "fare in fretta" saltando step

### Follow-up
- Implementare `build-release.sh` con le 5 fasi
- Refactorare `build-installer.sh` per leggere versione da SSoT
- Refactorare `fitmanager.iss` per accettare versione via `/D`
- Aggiornare `CLAUDE.md` sezione "Comandi operativi"
- Valutare code signing Windows (futuro, quando il volume clienti lo giustifica)

---

## Supersedes / Superseded By

- **Supersedes**: processo build ad-hoc pre-v1.0.4 (build-installer.sh senza gate)
- **Superseded by**: nessuno (questa e' la baseline)

---

## Appendice: Checklist Pre-Deploy (uso manuale)

Da verificare prima di consegnare l'installer al cliente:

- [ ] `manifest.json` presente accanto all'installer
- [ ] `manifest.json` → tutti i gate "pass"
- [ ] `manifest.json` → smoke_test "pass"
- [ ] `manifest.json` → version corrisponde a quella attesa
- [ ] Tag git `vX.Y.Z` creato
- [ ] Installer testato su macchina diversa da quella di sviluppo (se possibile)
- [ ] `license_public.pem` verificato presente nel bundle
- [ ] Chiave privata RSA in backup sicuro (separata dal repo)

## Appendice: Verifica Post-Install (sul PC cliente)

Da verificare dopo l'installazione sul PC del cliente:

- [ ] FitManager si avvia correttamente
- [ ] `/health` → `license_enforcement_enabled: true`
- [ ] `/health` → `version: "X.Y.Z"` corretta
- [ ] `/health` → `db: "connected"`, `catalog: "connected"`
- [ ] Pagina `/licenza` mostra codice macchina copiabile
- [ ] Dopo collocamento `license.key` → app funziona
- [ ] `GET /api/nutrition/plan-templates` → template presenti
- [ ] Esercizi visibili con foto nel catalogo
