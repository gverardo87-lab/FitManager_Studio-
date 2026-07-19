# ADR-026 — Distribuzione macOS (Apple Silicon)

**Stato:** proposed (2026-07-17) — decisioni D1-D6 raccomandate, da ratificare una a una col founder **all'apertura del blocco G-MAC** (⏸️ coda #3, sequenza founder 2026-07-19: prima release v1.0.14, poi blocco P). Anticipabile solo l'enrollment Apple Developer (D5): coda in tempo di calendario
**Contesto di nascita:** primo cliente reale (Daniele, PT pilota) ha un MacBook Air M1 2020 (ARM64, 8 GB, macOS Tahoe 26.5). Consegna richiesta entro 2 settimane. Spec operativa: `docs/specs/SPEC_G-MAC_CONSEGNA_MACOS.md`. Ground-truth: audit accoppiamenti Windows 2026-07-17 (4 agenti codebase + 2 ricerche web con fonti).

---

## Decisione D1 — macOS ARM64 è la seconda piattaforma di distribuzione; il codice si biforca per branch, mai per fork

Un solo codebase, dispatch per piattaforma nei (pochissimi) punti OS-specific: `machine_fingerprint.py` (fatto, G-MAC.0), `tunnel_config.py` filename frpc, launcher/installer per piattaforma. **Ogni branch macOS lascia l'output Windows bit-identico** (oracolo: fingerprint hash, installer, launcher.bat). Niente supporto Intel x86_64: ARM64-only (il parco Mac 2026 e il pilota lo sono).

## Decisione D2 — Layout flat, niente .app bundle

La distribuzione macOS replica il layout Windows: `FitManager/{backend/,frontend/,node/,data/,launcher.command}` in cartella utente scrivibile. Motivazione: `api/config.py` (`PROJECT_ROOT = exe.parent.parent` → `data/` sibling), risoluzione frpc e l'intera catena `data/` funzionano **invariate** — zero rischio su regola #7/#8. Il .app bundle (con DATA_DIR in `~/Library/Application Support`) è esplicitamente rimandato a post-pilota: richiede branch su config.py, notarizzazione matura e non aggiunge nulla al pilota. La sopravvivenza di `data/` all'upgrade diventa contratto dello script install/upgrade (su Windows la garantisce Inno Setup): va testata, non presunta.

## Decisione D3 — Build su GitHub Actions macOS runner; mai sul Mac del cliente

Nuitka non cross-compila (conferma ufficiale): la build DEVE avvenire su macOS ARM64. Build machine: runner GitHub-hosted `macos-15` (M1, ARM64; repo privato = ~200 min-orologio/mese inclusi, poi $0.062/min). Il sorgente non tocca MAI la macchina del cliente (coerenza ADR-007). Validazione manuale pre-consegna: Mac cloud spot (Scaleway M4, €0,22/h, minimo 24h) o call guidata. La CI è anche il primo enforcement automatico della suite (pytest su darwin prima della build).

## Decisione D4 — Compilazione: Nuitka anche su macOS (parità ADR-007), PyInstaller come fallback dichiarato

Su Darwin Nuitka usa clang (Xcode CLT), niente `--msvc`/`--windows-console-mode`, output senza estensione. I 3 safety gates ADR-004, la cifratura build-time dei cataloghi (`db_crypto` è byte-oriented: i `.db.enc` sono identici cross-arch) e il verify/seal restano identici. Se la build arm64 incontra blocchi nei tempi del pilota: fallback PyInstaller (spec darwin dedicata) accettando un **downgrade anti-RE esplicito, temporaneo e tracciato** — mai silenzioso.

## Decisione D5 — Firma: Developer ID + notarizzazione come traguardo; ponte ad-hoc SOLO per il pilota e SOLO via canale senza quarantena

Fatti (ricerca 2026, fonti nella spec): su ARM64 la firma almeno ad-hoc è obbligatoria; il bypass right-click→Apri è stato rimosso (Sequoia); su Tahoe un bundle ad-hoc in quarantena produce "app danneggiata" e "Open Anyway" è inaffidabile. Quindi: (a) enrollment Apple Developer ($99/anno) da avviare subito → codesign Developer ID + hardened runtime + notarytool in CI (automatizzabile, minuti); (b) finché (a) non è pronto, il pilota riceve il bundle via **scp o zip su USB** (canale che non applica `com.apple.quarantine`; MAI AirDrop/download browser) con `install.sh` che fa `xattr -dr` + `codesign -s -`. Il percorso (b) è dichiarato ponte: inaccettabile come esperienza di prodotto oltre il pilota.

## Decisione D6 — Kill-on-close di frpc su macOS: process-group + trap nel launcher, pkill nell'upgrade

Su macOS non esistono Job Object né PDEATHSIG. Equivalente a 2 livelli (specchio del modello Windows di pitfall #16): (1) frpc resta nel process-group/sessione del backend e `launcher.command` fa `trap 'kill -- -$$' EXIT` → chiusura finestra Terminal = morte dell'intero albero; (2) install/upgrade esegue `pkill -f frpc.toml` + kill backend prima di sostituire i file, sostituzione per rename mai in-place (un Mach-O in esecuzione sovrascritto in-place viene SIGKILLato per firma invalida). Rischio residuo dichiarato: orfano da SIGKILL diretto del backend (mitigabile con PID-file sweep al boot, opzionale nel pilota). Nota: su macOS l'orfano non locka il file immagine (l'upgrade non fallisce con codice 5) ma tiene il proxy-name su frps → tunnel rotto fino al kill.

## Questione aperta (fuori da questo ADR, decisione founder): interplay con G1

La consegna al primo cliente reale era gated sul Pre-Delivery Security Gate (ADR-013 accepted, zero codice: crm.db oggi plaintext). Su macOS SQLCipher è più oneroso (nessun wheel: brew + build da sorgente; spike Nuitka da ripetere su darwin). Le opzioni — consegnare il pilota con crm.db plaintext (accettazione esplicita, G1 dopo) o spostare la deadline — sono D-MAC-5 nella spec. Qualunque scelta, il vincolo cross-platform entra nel design di dettaglio G1 da subito.

## Conseguenze

- Nasce la prima CI del repo (GH Actions macOS): pytest su darwin + build + safety gates ADR-004 su ogni release macOS.
- `SPEC_FINGERPRINT_CROSSPLATFORM` (G-MAC.0) è il cancello di fattibilità: codice fatto e T1 verificato (hash Windows invariato); T2 chiude su hardware reale.
- Il registro deployment (`DEPLOYMENTS.md`) traccia la piattaforma per cliente; il runbook di consegna macOS nasce in `docs/operations/`.
- Ogni futuro binario long-lived aggiunto al bundle deve dichiarare il proprio destino su ENTRAMBE le piattaforme (Job Object su win, process-group/trap su mac) — estensione del pitfall #16.
