# SPEC BLOCCO G-MAC — Consegna macOS ARM64

**Stato:** 🟡 DELIVERABLE PRE-POC IMPEGNATO — C0.0 contratto target CHIUSO; prossimo gate C0.1
canary RED. G-MAC.0 codice FATTO e sigillato (T1 PASS, suite 867). Prima dell'application freeze
`v1.0.15` chiudono C0 + G-MAC.1 runtime; G-MAC.2–5 di distribuzione completano dopo il freeze
applicativo, senza ulteriori GO finché scope e policy non cambiano. Sequenza vincolante:
`SPEC_PRE_POC.md` (decisione founder 2026-07-31; Addendum ADR-026 del 2026-08-02).
**ADR di riferimento:** ADR-026 (accepted 2026-07-31) · ADR-004 (pipeline release) · ADR-007 (anti-RE) · ADR-011 (tunnel FRP)
**Ground-truth:** audit accoppiamenti Windows 2026-07-17 (workflow 6 agenti: 4 audit codebase + 2 ricerche web con fonti). Il codice reale vince sulla spec.
**Timeline:** milestone assolute e interlock in `SPEC_PRE_POC.md`; la stima tecnica di 14 giorni in
§5 resta riferimento di capacità, non autorizza packaging prima dell'application freeze.

---

## 0. Contesto e hardware target

Daniele, primo target di accettazione e consegna macOS noto, ha un **MacBook Air M1 2020 — Apple
Silicon ARM64, 8 GB RAM, macOS Tahoe 26.5.1**. La configurazione è stata confermata il 2026-08-02
da evidenza fornita dal founder. Foto e identificatori hardware grezzi non sono copiati nel
repository né nei log di verifica. L'app oggi è distribuita solo Windows (Nuitka MSVC, Inno Setup
e launcher.bat). Daniele non è un gate allo sviluppo e il potenziale percorso Virgin resta upside
commerciale non validato.

## 1. Verità fondanti (dall'audit — cosa è vero DAVVERO)

1. **Il runtime backend è quasi tutto già portabile.** `api/` ha solo 3 file che spawnano processi (fingerprint, tunnel_manager, connectivity_runtime); zero winreg/windll/os.startfile/shell=True. `backup.py`, `db_crypto.py`, `logging_config.py`, `entry_point.py`, seed, schema_sync: puri Python/pathlib. `is_compiled()` funziona identico su macOS.
2. **La montagna è la pipeline di distribuzione, non il codice**: launcher.bat, Inno Setup, node.exe, Nuitka `--msvc` sono 4 sostituzioni obbligate.
3. **Nuitka NON cross-compila**: la build backend DEVE girare su hardware macOS ARM64 (conferma ufficiale, issue #43/#2149). Cross-arch x86→arm64 sconsigliata (bug #2724): build nativa arm64.
4. **Il bundle Next standalone è platform-specific** (`@img/sharp-win32-x64`, swc/oxide/lightningcss win32 nel lock): `npm ci && next build` va rieseguito su macOS. Le varianti darwin-arm64 esistono già come optionalDependencies.
5. **Il runtime tunnel/ACME hardcoda due companion Windows:** `frpc.exe` e `lego.exe` in
   `api/services/tunnel_config.py`. Su macOS FRP si spegne in silenzio e il rinnovo ACME non trova
   il client. G-MAC.1 deve rendere platform-conditional **entrambi** i nomi, con regressione Windows
   e test Darwin. Il binario ufficiale `frp_0.61.1_darwin_arm64.tar.gz` esiste — stessa versione del
   frps sul VPS; versione, licenza e SHA-256 di ogni companion vanno bloccati prima dello staging.
6. **Il Job Object non ha equivalente macOS.** Il pitfall #16 cambia natura: niente lock del file immagine (upgrade non fallisce), ma un frpc orfano tiene il proxy-name su frps → il nuovo frpc fallisce la registrazione e cicla in backoff ("tunnel rotto/stantio").
7. **Layout flat = zero modifiche a `config.py`**: `PROJECT_ROOT = exe.parent.parent` funziona invariato con `FitManager/{backend,frontend,node,data,launcher.command}` in una cartella scrivibile dall'utente (MAI /Applications con .app bundle, per ora).
8. **Gatekeeper è il rischio di consegna n.1.** Su ARM64 la firma (almeno ad-hoc) è obbligatoria per eseguire. Il bypass right-click→Apri NON esiste più (rimosso in Sequoia). Su Tahoe, app ad-hoc in quarantena → "app danneggiata", e "Open Anyway" a volte non compare. La candidate esterna richiede Developer ID + notarizzazione; la firma ad-hoc è ammessa soltanto nel canary/debug interno e non sostituisce il gate di consegna.
9. **Build CI e target non sono equivalenti.** I runner standard privati GitHub `macos-15` e
   `macos-26` sono Apple M1 con 3 CPU, 7 GB RAM e 14 GB SSD, ma la label non garantisce la patch
   esatta `26.5.1`. `macos-15` resta la build machine; lo stesso artefatto canary deve girare su
   `macos-26` e poi sul target esatto. Minuti e billing si verificano subito prima dell'esecuzione,
   senza assumere prezzi o quote storiche.
10. **Le dipendenze hanno un percorso ARM64 verificabile, non ancora un PASS.** Il perimetro runtime
    reale deriva dalla build lean, non dallo stack AI dormiente. PyPI pubblica per `sqlcipher3 0.6.2`
    una wheel CPython 3.12 `macosx_11_0_arm64`; il lock frontend contiene varianti darwin-arm64 di
    Sharp e SWC. C0 deve comunque fissare versione e hash, installare solo wheel ARM64, eseguire il
    round-trip SQLCipher e provare il binario Nuitka: la disponibilità nominale non certifica il
    runtime.
11. **Anomalia da chiarire pre-build**: `--include-package=email_validator` in build-backend-nuitka.sh:80 ma il pacchetto non risulta nella venv → verificare prima di replicare la build.
12. **Local Network prompt / firewall macOS: non ci toccano** (bind 127.0.0.1 loopback; firewall spento di default; il prompt Local Network non scatta per localhost).
13. **Il target ha 8 GB, non un margine teorico illimitato.** La compatibilità richiede una misura
    del processo backend + Node dopo warm-up e smoke core; non è lecito trasformare una stima di
    memoria in PASS.

## 2. Decisione architetturale portante (→ ADR-026)

**Layout flat, parità di contratti con Windows.** La distribuzione macOS replica il layout `FitManager/{backend/,frontend/,node/,data/,launcher.command}` in `~/Applications/FitManager` (o `~/FitManager`). Conseguenze:
- `api/config.py`, risoluzione frpc compiled, catena `data/` (crm.db, licenza, .env, logs, backups, media, tunnel): **INVARIATI**.
- I 3 contratti dell'installer Windows diventano contratti dello script `install.sh`: (1) kill processi prima di sovrascrivere; (2) sovrascrivere solo backend/frontend/node/launcher, MAI `data/`; (3) i cataloghi `.db.enc` + `license_public.pem` + media si copiano SOLO in `data/`, crm.db non si spedisce mai.
- Su macOS la sopravvivenza di `data/` all'upgrade è una **convenzione di script, non un enforcement di piattaforma**: va testata esplicitamente (G-MAC.4).

## 3. Gate

### G-MAC.0 — Fingerprint cross-platform ✅ codice FATTO (2026-07-17) · chiusura su Mac reale
Spec di dettaglio: `SPEC_FINGERPRINT_CROSSPLATFORM.md` (bozza 25/06, decisione primitive §4 confermata).
- **T1 (Windows, output-invariante): PASS** — hash pre/post refactor identico carattere per carattere (`695ad621…4315`) sulla macchina di sviluppo. Estratta `_fingerprint_windows()` (puro spostamento).
- **T2 (macOS)**: `_fingerprint_macos()` implementata — singola invocazione `ioreg -rd1 -c IOPlatformExpertDevice`, entrambi i campi `IOPlatformUUID|IOPlatformSerialNumber` (ordine fissato), disciplina tutto-o-niente INC-2026-06-18 (retry sui vuoti, no-retry sui timeout, mai hash parziale, mai cache di `unavailable`). Dispatch su `platform.system()` (Windows/Darwin/altro→unavailable).
- Test: `tests/test_machine_fingerprint.py` 18/18 (7 nuovi: hash+ordine, singola invocazione §4.1, tutto-o-niente, retry, timeout, self-heal, dispatch). Il fixture forza il ramo Windows → suite valida anche su host darwin.
- **Il gate CHIUDE solo con T2 + cross-check binding su hardware macOS reale** (G-MAC.4).

### C0 — Portability canary mirato al target M1/8 GB/Tahoe 26.5.1

C0 è un gate di evidenza pre-freeze, non packaging cliente. È composto da tre checkpoint distinti:

- **C0.0 — contratto target (questo gate docs): CHIUSO.** Configurazione supportata, matrice di
  prova, limiti privacy e soglie sono fissati prima del codice.
- **C0.1 — canary CI RED→GREEN.** Un workflow minimo costruisce l'artefatto canary ARM64 su `macos-15`
  ARM64 e lo esegue, senza ricompilarlo, su `macos-26`. Il primo risultato reale è RED finché tutte
  le prove sotto non producono evidenza; ogni incompatibilità apre un requisito v1.0.15, non una
  deroga.
- **C0.2 — conferma target source-free.** Lo stesso canary compilato viene eseguito in call guidata
  sul Mac di Daniele. Sul target non arrivano repository, sorgenti, venv, chiavi private, dati reali
  o strumenti di build. Un PASS solo CI è **condizionale**, non certifica il target esatto.

Matrice minima e falsificabile:

| Area | Evidenza C0.1 CI | Evidenza C0.2 target esatto |
|------|------------------|-----------------------------|
| Identità ambiente | `arm64`; build `macos-15`; esecuzione dello stesso artefatto su `macos-26` | `arm64`; macOS `26.5.1`; modello M1/2020 e RAM 8 GB già confermati, senza esportare identificatori |
| Supply chain | versioni + SHA-256; solo wheel/tag ARM64; `file` e `otool` senza slice x86 o dylib irrisolte | nessuna dipendenza installata e nessuna richiesta Rosetta |
| SQLCipher/G1 | create→write→close→reopen, wrong-key fail, plaintext assente, smoke dal binario Nuitka standalone | medesimo smoke con DB sintetico temporaneo, poi rimozione |
| Frontend | `npm ci` + `next build` su ARM64; moduli nativi darwin-arm64 | boot standalone e navigazione core sintetica |
| Stabilità | `/health`, login sintetico e smoke core; nessun crash | 30 minuti dopo warm-up senza crash, memory pressure o terminazione |
| Memoria | RSS combinata backend + Node registrata dopo warm-up e smoke | warning oltre 1,5 GB; FAIL oltre 2 GB, memory pressure o terminazione |
| Display | smoke browser alle viewport 1440×900 e 1024×640 | nessun blocco del flusso core alla risoluzione usata dal target |
| Storage | dimensione artefatto e spazio libero registrati | spazio libero registrato; la soglia installer finale viene fissata in G-MAC.3 sul bundle reale |
| Fingerprint | test automatici Darwin già presenti | probe compilato: stabilità booleana tra due letture; nessun valore grezzo o fingerprint nei log |

Privacy del probe C0.2:

- output ammesso: architettura, versione OS, RAM/spazio in classi tecniche, esiti booleani,
  misure di memoria e codici errore sanitizzati;
- output vietato: seriale, `IOPlatformUUID`, output `ioreg`, fingerprint completo, foto, username,
  path home, contenuto DB o token/licenze;
- il report committato contiene solo esiti e misure non identificanti. La prova di binding licenza
  resta G-MAC.4/G-MAC.5 nel canale amministrativo dedicato.

**Definition of Done C0:** C0.1 e C0.2 entrambi PASS sullo stesso artefatto. Ogni finding viene
classificato; se richiede G-MAC.1, la remediation avviene in un gate codice separato e C0.1 viene
rieseguito prima di C0.2. C0 non produce un installer consegnabile e non autorizza dati reali.

### G-MAC.1 — Portabilità runtime tunnel (unico codice `api/` rimasto)
- `tunnel_config.py`: `_FRPC_FILENAME` e `_ACME_CLIENT_FILENAME` platform-conditional
  (`frpc.exe`/`lego.exe` su Windows, `frpc`/`lego` su Darwin) + warning aggiornati; dev-path
  `tools/bin/` per i binari Darwin.
- `tunnel_manager.py`: `start_new_session` — **decisione**: NON usarlo (finding audit): frpc resta nel process-group del backend così il `trap` del launcher e il SIGHUP di sessione uccidono l'intero gruppo (equivalente pragmatico del Job Object). In compenso: messaggio del ramo `PermissionError` esteso (Gatekeeper/quarantine su darwin).
- Windows resta **bit-identico** (branch, mai modifica del ramo esistente). Test gemelli per la
  risoluzione di entrambi i filename e canary Darwin aggiornato. G-MAC.1 è un gate codice separato:
  si apre soltanto dopo l'evidenza C0.1 RED o per i due accoppiamenti già dimostrati dal codice.
- Opzionale se il tempo regge (rischio residuo dichiarato altrimenti): PID-file + sweep al boot (~20 LOC) contro l'orfano da SIGKILL.

### G-MAC.2 — Pipeline build macOS di release (CI GitHub Actions)
- `requirements-api-macos.txt` lean derivato dalla lista `--include-package` (13 pacchetti + dev: pytest/httpx/hypothesis/ruff/alembic). MAI installare pyproject completo su mac.
- Promuovere il workflow minimo C0 a pipeline di release: build su runner `macos-15` ARM64 (pin
  esplicito), poi smoke dello **stesso artefatto** su runner `macos-26`; step: venv → pytest suite
  completa su Darwin →
  `next build` → Nuitka build (clang, no `--msvc`, no `--windows-console-mode`, output `fitmanager`
  senza estensione, ccache per le run successive) → staging Node darwin-arm64 + `frpc` + `lego`
  Darwin con versioni/hash/licenze pinnati → cifratura cataloghi + 3 safety gates ADR-004
  (mantenuti identici; Gate 2 ri-puntato a install.sh) → bundle
  `FitManager-macos-arm64.tar.gz` come artifact.
- Patch portabilità bash (non rompono Windows): `resolve_python` prova `venv/bin` prima di `venv/Scripts`; `shasum -a 256` fallback di `sha256sum`; `grep -oE` al posto di `-oP`; port-check con `lsof`.
- Budget: quote e billing GitHub vengono letti e registrati prima della prima run; CI solo per build
  vere, ccache e artifact reuse tra build `macos-15` e smoke `macos-26`.
- Chiarire anomalia `email_validator` (§1.11) prima della prima build.

### G-MAC.3 — Packaging, launcher, firma
- `launcher.command` (~30 righe): `cd "$(dirname "$0")"`, `LICENSE_ENFORCEMENT_ENABLED=true`, `./backend/fitmanager --port 8000 &`, health-wait curl, `PORT=3000 HOSTNAME=0.0.0.0 ./node/bin/node frontend/server.js &`, `open http://localhost:3000`, `trap 'kill -- -$$' EXIT` + `wait` (chiudi finestra Terminal = spegni tutto, frpc incluso). Niente blocco Tailscale.
- `install.sh` + `upgrade`: i 3 contratti §2, `pkill -f frpc.toml` + kill backend PRIMA di sovrascrivere, sostituzione **per rename mai in-place** (Mach-O in esecuzione sovrascritto in-place = SIGKILL per firma invalida), verifica della notarizzazione e dei permessi eseguibili.
- Firma: Developer ID + hardened runtime + notarizzazione sono criteri della candidate consegnabile. `codesign -s -` resta solo nel canary/debug interno.

### G-MAC.4 — Validazione end-to-end su hardware macOS reale
- Ambiente: Mac cloud ARM64 pulito per rehearsal ripetibile, con costo verificato prima dell'ordine,
  più cross-check conclusivo sul MacBook Air M1/8 GB/Tahoe 26.5.1 di Daniele in call guidata.
- Checklist: boot launcher → /health → login → **T2 fingerprint (stabile tra riavvii) + cross-check binding licenza** (chiude G-MAC.0) → tunnel FRP e rinnovo ACME attivi → portale pubblico raggiungibile da smartphone → log DB cifrati "via deserialize" (se "via temp file": annotare degrado ADR-007) → upgrade simulato (install.sh sopra installazione esistente, `data/` intatto) → chiusura finestra = zero processi orfani (`pgrep`). Sul target arriva solo l'artefatto firmato/source-free.

### G-MAC.5 — Consegna
- Licenza: `fingerprint` sul Mac di Daniele (via pagina /licenza dell'app installata, stesso flusso Windows) → `sign --tier pro --instance-id daniele-<slug> --machine-id <FP_MAC>` → record DNS sottodominio.
- Runbook consegna scritto in `docs/operations/` (gemello del flusso Alessio/Chiara v1.0.13) + registrazione in `DEPLOYMENTS.md`.

## 4. Decisioni ratificate (founder 2026-07-31, → ADR-026)

- **D-MAC-1 — Firma/canale**: avviare l'enrollment Apple Developer prima del gate di distribuzione. Developer ID + hardened runtime + notarizzazione sono obbligatori sull'artefatto consegnato; ad-hoc è solo una tecnica interna di canary/debug. Nessun workaround USB/scp viene presentato al cliente. Se il gate Apple ritarda, slitta G-MAC.5.
- **D-MAC-2 — Build machine ed evidenza target**: GitHub Actions `macos-15` è la build machine;
  lo stesso artefatto viene eseguito su `macos-26`, poi sul target esatto. Il Mac del cliente non è
  mai una build machine (source exposure, viola ADR-007) e non riusa venv/output Windows.
- **D-MAC-3 — Dove validare G-MAC.4**: rehearsal su Mac cloud ARM64 pulito e ripetibile; cross-check
  conclusivo obbligatorio in call sul target M1/8 GB/Tahoe 26.5.1. Costo e versione OS del provider
  si verificano prima dell'ordine: un host cloud diverso non sostituisce il target.
- **D-MAC-4 — Compilatore**: Nuitka anche su mac (parità ADR-007). Fallback dichiarato se la build arm64 dà problemi nei tempi: PyInstaller (`fitmanager.spec` da duplicare per darwin) accettando downgrade anti-RE **esplicito e temporaneo** per il solo pilota.
- **D-MAC-5 — Interplay G1 (cifratura crm.db)**: nessuna consegna data-bearing con `crm.db`
  plaintext. Portability canary e G-MAC.1 precedono l'application freeze; verificano SQLCipher,
  boot e runtime su Darwin. G-MAC.2–5 consumano poi la baseline G1 congelata. Un'incompatibilità
  sposta il milestone o entra nello scope v1.0.15, mai in una deroga sicurezza.

## 5. Timeline proposta (14 giorni)

| Giorni | Cosa |
|--------|------|
| pre-freeze | C0.0 contratto target → C0.1 canary RED → G-MAC.1 remediation (`frpc` + `lego`) + re-run C0.1 GREEN → C0.2 probe source-free target |
| 1-3 post-freeze | G-MAC.2: requirements lean, patch bash, workflow CI, prima build verde |
| 4-7 post-freeze | G-MAC.3: launcher.command, install.sh, firma/notarizzazione; bundle installabile |
| 8-11 post-freeze | G-MAC.4 su Mac pulito: checklist completa, fix emersi, candidate e2e |
| 12-14 post-freeze | G-MAC.5: licenza+DNS, runbook, consegna assistita Daniele + buffer |

## 6. Does NOT touch (blinda lo scope)

- ❌ Nessun refactor del ramo Windows: ogni modifica è un **branch** per piattaforma; output Windows bit-identico (installer, launcher.bat, .iss, Job Object, build MSVC invariati).
- ❌ Niente .app bundle / DMG drag-to-Applications in questo blocco (post-pilota, con notarizzazione matura).
- ❌ G-MAC non implementa G1 dopo il freeze: consuma la baseline security già verde. Prima del
  freeze il canary verifica la compatibilità Darwin e impedisce un design G1 Windows-only.
- ❌ Niente Intel/x86_64 macOS: ARM64-only.
- ❌ Niente modifiche a `license.py`/`generate_license.py` (il fingerprint resta stringa opaca).
- ❌ Il tooling dev Windows (kill-port.sh, restart-backend.sh, pipeline video) resta com'è.

## 7. Rischi principali

| Rischio | Mitigazione |
|---------|-------------|
| Enrollment Apple in coda lunga (settimane) | Avviare prima del gate distribution; se non è pronto, G-MAC.5 resta chiuso e il milestone slitta |
| Prima build Nuitka arm64 con sorprese (FastAPI+pydantic-core compilati) | Smoke /health nel workflow CI; fallback PyInstaller dichiarato (D-MAC-4) |
| Budget minuti CI | Preflight su quota/billing corrente; ccache; artifact reuse; run intere contate |
| Runner `macos-26` con patch diversa da 26.5.1 | Build su `macos-15`, smoke medesimo artefatto su `macos-26`, conferma source-free obbligatoria sul target esatto |
| Tahoe stringe Gatekeeper | Developer ID + hardened runtime + notarizzazione della candidate; ad-hoc soltanto nel canary interno |
| frpc orfano su SIGKILL (no Job Object) | trap process-group nel launcher + pkill nell'upgrade; PID-file sweep se il tempo regge; rischio residuo dichiarato |
| 8 GB RAM sul Mac target | Misura combinata backend+Node: warning >1,5 GB, FAIL >2 GB/memory pressure; MAI buildare sul target |
| Identificatori hardware nei log | Probe source-free con soli esiti booleani e misure non identificanti; seriale/UUID/fingerprint vietati nei report |

## 8. Fonti verificate per C0.0 (2026-08-02)

- Apple, modelli compatibili con macOS Tahoe 26:
  <https://support.apple.com/en-gb/122867>
- Apple, specifiche MacBook Air M1 2020 e risoluzioni supportate:
  <https://support.apple.com/it-it/111883>
- GitHub, specifiche correnti dei runner macOS hosted:
  <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>
- PyPI, wheel ARM64 CPython 3.12 di `sqlcipher3 0.6.2`:
  <https://pypi.org/project/sqlcipher3/>
- Nuitka, compilazione nativa e supporto macOS/Apple Silicon:
  <https://nuitka.net/user-documentation/user-manual.html>
- Apple, Developer ID e notarizzazione:
  <https://developer.apple.com/developer-id/> e
  <https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution>
