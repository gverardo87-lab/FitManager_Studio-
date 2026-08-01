# SPEC BLOCCO G-MAC — Consegna macOS ARM64

**Stato:** 🟡 DELIVERABLE PRE-POC IMPEGNATO — G-MAC.0 codice FATTO e sigillato (T1 PASS, suite
867). Prima dell'application freeze `v1.0.15` apre portability canary + G-MAC.1 runtime; G-MAC.2–5
di distribuzione completano dopo il freeze applicativo, senza ulteriori GO finché scope e policy
non cambiano. Sequenza vincolante: `SPEC_PRE_POC.md` (decisione founder 2026-07-31).
**ADR di riferimento:** ADR-026 (accepted 2026-07-31) · ADR-004 (pipeline release) · ADR-007 (anti-RE) · ADR-011 (tunnel FRP)
**Ground-truth:** audit accoppiamenti Windows 2026-07-17 (workflow 6 agenti: 4 audit codebase + 2 ricerche web con fonti). Il codice reale vince sulla spec.
**Timeline:** milestone assolute e interlock in `SPEC_PRE_POC.md`; la stima tecnica di 14 giorni in
§5 resta riferimento di capacità, non autorizza packaging prima dell'application freeze.

---

## 0. Contesto e hardware target

Daniele, primo target di accettazione e consegna macOS noto, ha un **MacBook Air M1 2020 — Apple
Silicon ARM64, 8 GB RAM, macOS Tahoe 26.5.1** (foto specifiche 2026-06-28). L'app oggi è distribuita
solo Windows (Nuitka MSVC + Inno Setup + launcher.bat). Daniele non è un gate allo sviluppo e il
potenziale percorso Virgin resta upside commerciale non validato.

## 1. Verità fondanti (dall'audit — cosa è vero DAVVERO)

1. **Il runtime backend è quasi tutto già portabile.** `api/` ha solo 3 file che spawnano processi (fingerprint, tunnel_manager, connectivity_runtime); zero winreg/windll/os.startfile/shell=True. `backup.py`, `db_crypto.py`, `logging_config.py`, `entry_point.py`, seed, schema_sync: puri Python/pathlib. `is_compiled()` funziona identico su macOS.
2. **La montagna è la pipeline di distribuzione, non il codice**: launcher.bat, Inno Setup, node.exe, Nuitka `--msvc` sono 4 sostituzioni obbligate.
3. **Nuitka NON cross-compila**: la build backend DEVE girare su hardware macOS ARM64 (conferma ufficiale, issue #43/#2149). Cross-arch x86→arm64 sconsigliata (bug #2724): build nativa arm64.
4. **Il bundle Next standalone è platform-specific** (`@img/sharp-win32-x64`, swc/oxide/lightningcss win32 nel lock): `npm ci && next build` va rieseguito su macOS. Le varianti darwin-arm64 esistono già come optionalDependencies.
5. **`tunnel_config.py:35` hardcoda `frpc.exe`** → su macOS il tunnel si spegne **in silenzio** (log "frpc assente"). Il binario ufficiale `frp_0.61.1_darwin_arm64.tar.gz` esiste (verificato via GitHub API) — stessa versione del frps sul VPS.
6. **Il Job Object non ha equivalente macOS.** Il pitfall #16 cambia natura: niente lock del file immagine (upgrade non fallisce), ma un frpc orfano tiene il proxy-name su frps → il nuovo frpc fallisce la registrazione e cicla in backoff ("tunnel rotto/stantio").
7. **Layout flat = zero modifiche a `config.py`**: `PROJECT_ROOT = exe.parent.parent` funziona invariato con `FitManager/{backend,frontend,node,data,launcher.command}` in una cartella scrivibile dall'utente (MAI /Applications con .app bundle, per ora).
8. **Gatekeeper è il rischio di consegna n.1.** Su ARM64 la firma (almeno ad-hoc) è obbligatoria per eseguire. Il bypass right-click→Apri NON esiste più (rimosso in Sequoia). Su Tahoe, app ad-hoc in quarantena → "app danneggiata", e "Open Anyway" a volte non compare. La candidate esterna richiede Developer ID + notarizzazione; la firma ad-hoc è ammessa soltanto nel canary/debug interno e non sostituisce il gate di consegna.
9. **GitHub Actions macOS**: label `macos-15`/`macos-26` = ARM64 (M1, 3 vCPU, 7 GB). Repo privato piano Free: 2.000 min/mese consumati ~10x su macOS → **~200 minuti-orologio/mese**, poi $0.062/min. Alternativa spot: Scaleway Mac mini M4 €0,22/h (minimo 24h ≈ €5,3) per validazione manuale.
10. **Dipendenze: nessun blocker.** Il perimetro runtime reale è ~13 pacchetti (la lista `--include-package` di build-backend-nuitka.sh è il manifest attendibile, NON pyproject.toml che trascina lo stack AI dormiente con `chroma-hnswlib` senza wheel cp312). Tutte le native shipped hanno wheel macosx-arm64 cp312. I `.db.enc` cifrati su Windows si decifrano byte-identici su arm64 (formato byte-oriented, nessuna dipendenza da architettura).
11. **Anomalia da chiarire pre-build**: `--include-package=email_validator` in build-backend-nuitka.sh:80 ma il pacchetto non risulta nella venv → verificare prima di replicare la build.
12. **Local Network prompt / firewall macOS: non ci toccano** (bind 127.0.0.1 loopback; firewall spento di default; il prompt Local Network non scatta per localhost).

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

### G-MAC.1 — Portabilità runtime tunnel (unico codice `api/` rimasto)
- `tunnel_config.py`: `_FRPC_FILENAME` platform-conditional (`"frpc.exe"` su win, `"frpc"` altrove) + testo warning aggiornato; dev-path `tools/bin/` per il binario darwin.
- `tunnel_manager.py`: `start_new_session` — **decisione**: NON usarlo (finding audit): frpc resta nel process-group del backend così il `trap` del launcher e il SIGHUP di sessione uccidono l'intero gruppo (equivalente pragmatico del Job Object). In compenso: messaggio del ramo `PermissionError` esteso (Gatekeeper/quarantine su darwin).
- Windows resta **bit-identico** (branch, mai modifica del ramo esistente). Test gemelli per la risoluzione filename.
- Opzionale se il tempo regge (rischio residuo dichiarato altrimenti): PID-file + sweep al boot (~20 LOC) contro l'orfano da SIGKILL.

### G-MAC.2 — Pipeline build macOS (CI GitHub Actions)
- `requirements-api-macos.txt` lean derivato dalla lista `--include-package` (13 pacchetti + dev: pytest/httpx/hypothesis/ruff/alembic). MAI installare pyproject completo su mac.
- Primo workflow GH Actions del repo: runner `macos-15` (pin esplicito), step: venv → pytest suite completa su darwin → `next build` → Nuitka build (clang, no `--msvc`, no `--windows-console-mode`, output `fitmanager` senza estensione, ccache per le run successive) → staging node darwin-arm64 (tarball ufficiale, versione pinnata) + frpc darwin_arm64 v0.61.1 → cifratura cataloghi + 3 safety gates ADR-004 (mantenuti identici; Gate 2 ri-puntato a install.sh) → bundle `FitManager-macos-arm64.tar.gz` come artifact.
- Patch portabilità bash (non rompono Windows): `resolve_python` prova `venv/bin` prima di `venv/Scripts`; `shasum -a 256` fallback di `sha256sum`; `grep -oE` al posto di `-oP`; port-check con `lsof`.
- Budget minuti: prima build fredda 20-60 min; con ~200 min/mese free → poche run intere/mese: sviluppare lo script in locale-bash il più possibile, CI solo per build vere.
- Chiarire anomalia `email_validator` (§1.11) prima della prima build.

### G-MAC.3 — Packaging, launcher, firma
- `launcher.command` (~30 righe): `cd "$(dirname "$0")"`, `LICENSE_ENFORCEMENT_ENABLED=true`, `./backend/fitmanager --port 8000 &`, health-wait curl, `PORT=3000 HOSTNAME=0.0.0.0 ./node/bin/node frontend/server.js &`, `open http://localhost:3000`, `trap 'kill -- -$$' EXIT` + `wait` (chiudi finestra Terminal = spegni tutto, frpc incluso). Niente blocco Tailscale.
- `install.sh` + `upgrade`: i 3 contratti §2, `pkill -f frpc.toml` + kill backend PRIMA di sovrascrivere, sostituzione **per rename mai in-place** (Mach-O in esecuzione sovrascritto in-place = SIGKILL per firma invalida), verifica della notarizzazione e dei permessi eseguibili.
- Firma: Developer ID + hardened runtime + notarizzazione sono criteri della candidate consegnabile. `codesign -s -` resta solo nel canary/debug interno.

### G-MAC.4 — Validazione end-to-end su hardware macOS reale
- Ambiente: Scaleway Mac mini M4 24h (≈€5,3) oppure direttamente il Mac di Daniele in call guidata (decisione D-MAC-3).
- Checklist: boot launcher → /health → login → **T2 fingerprint (stabile tra riavvii) + cross-check binding licenza** (chiude G-MAC.0) → tunnel FRP attivo (proxy registrato, portale pubblico raggiungibile da smartphone) → log DB cifrati "via deserialize" (se "via temp file": annotare degrado ADR-007) → upgrade simulato (install.sh sopra installazione esistente, `data/` intatto) → chiusura finestra = zero processi orfani (`pgrep`).

### G-MAC.5 — Consegna
- Licenza: `fingerprint` sul Mac di Daniele (via pagina /licenza dell'app installata, stesso flusso Windows) → `sign --tier pro --instance-id daniele-<slug> --machine-id <FP_MAC>` → record DNS sottodominio.
- Runbook consegna scritto in `docs/operations/` (gemello del flusso Alessio/Chiara v1.0.13) + registrazione in `DEPLOYMENTS.md`.

## 4. Decisioni ratificate (founder 2026-07-31, → ADR-026)

- **D-MAC-1 — Firma/canale**: avviare l'enrollment Apple Developer prima del gate di distribuzione. Developer ID + hardened runtime + notarizzazione sono obbligatori sull'artefatto consegnato; ad-hoc è solo una tecnica interna di canary/debug. Nessun workaround USB/scp viene presentato al cliente. Se il gate Apple ritarda, slitta G-MAC.5.
- **D-MAC-2 — Build machine**: (RACCOMANDATO) GitHub Actions `macos-15` come build machine unica + Scaleway 24h per la validazione G-MAC.4. MAI buildare sul Mac del cliente (source exposure, viola ADR-007), MAI riusare la venv/l'output Windows.
- **D-MAC-3 — Dove validare G-MAC.4**: Scaleway 24h prima della consegna (pulito, ripetibile) vs direttamente call con Daniele (zero costi, ma prima esperienza = debugging). Raccomandato: Scaleway.
- **D-MAC-4 — Compilatore**: Nuitka anche su mac (parità ADR-007). Fallback dichiarato se la build arm64 dà problemi nei tempi: PyInstaller (`fitmanager.spec` da duplicare per darwin) accettando downgrade anti-RE **esplicito e temporaneo** per il solo pilota.
- **D-MAC-5 — Interplay G1 (cifratura crm.db)**: nessuna consegna data-bearing con `crm.db`
  plaintext. Portability canary e G-MAC.1 precedono l'application freeze; verificano SQLCipher,
  boot e runtime su Darwin. G-MAC.2–5 consumano poi la baseline G1 congelata. Un'incompatibilità
  sposta il milestone o entra nello scope v1.0.15, mai in una deroga sicurezza.

## 5. Timeline proposta (14 giorni)

| Giorni | Cosa |
|--------|------|
| pre-freeze | Portability canary + G-MAC.1 (tunnel filename, dipendenze, SQLCipher/boot e test runtime) |
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
| Budget minuti CI (200/mese) | Script sviluppati fuori CI; ccache; run intere contate |
| Tahoe stringe ancora Gatekeeper (26.2+ segnalazioni) | Developer ID + notarizzazione della candidate e test su Scaleway con la STESSA versione OS di Daniele (26.5) |
| frpc orfano su SIGKILL (no Job Object) | trap process-group nel launcher + pkill nell'upgrade; PID-file sweep se il tempo regge; rischio residuo dichiarato |
| 8 GB RAM sul Mac target | Run-time OK (~1 GB per lo stack); MAI buildare sul suo Mac |
