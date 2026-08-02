# ADR-026 — Distribuzione macOS (Apple Silicon)

**Stato:** accepted (2026-07-31) + Addendum I (2026-08-02) — D1–D6 ratificate dal founder.
macOS ARM64 è un deliverable pre-POC impegnato; portability canary prima dell'application freeze,
full distribution G-MAC dopo.
Sequenza e stop condition: `docs/specs/SPEC_PRE_POC.md`.
**Contesto di nascita:** Daniele, primo target di accettazione e consegna Mac noto, ha un MacBook Air
M1 2020 (ARM64, 8 GB, macOS Tahoe 26.5.1; configurazione confermata il 2026-08-02 senza conservare
foto o identificatori hardware). La capacità di distribuzione conserva valore indipendente
dal singolo prospect; Virgin resta upside non validato. Spec operativa:
`docs/specs/SPEC_G-MAC_CONSEGNA_MACOS.md`.

---

## Decisione D1 — macOS ARM64 è la seconda piattaforma di distribuzione; il codice si biforca per branch, mai per fork

Un solo codebase, dispatch per piattaforma nei (pochissimi) punti OS-specific:
`machine_fingerprint.py` (fatto, G-MAC.0), `tunnel_config.py` per i companion `frpc` e `lego`,
launcher/installer per piattaforma. **Ogni branch macOS lascia l'output Windows bit-identico**
(oracolo: fingerprint hash, installer, launcher.bat). Niente supporto Intel x86_64: ARM64-only
(il pilota lo è).

## Decisione D2 — Layout flat, niente .app bundle

La distribuzione macOS replica il layout Windows: `FitManager/{backend/,frontend/,node/,data/,launcher.command}` in cartella utente scrivibile. Motivazione: `api/config.py` (`PROJECT_ROOT = exe.parent.parent` → `data/` sibling), risoluzione frpc e l'intera catena `data/` funzionano **invariate** — zero rischio su regola #7/#8. Il .app bundle (con DATA_DIR in `~/Library/Application Support`) è esplicitamente rimandato a post-pilota: richiede branch su config.py, notarizzazione matura e non aggiunge nulla al pilota. La sopravvivenza di `data/` all'upgrade diventa contratto dello script install/upgrade (su Windows la garantisce Inno Setup): va testata, non presunta.

## Decisione D3 — Build su GitHub Actions macOS runner; mai sul Mac del cliente

Nuitka non cross-compila: la build DEVE avvenire su macOS ARM64. Build machine: runner
GitHub-hosted `macos-15` (M1, ARM64). Il sorgente non tocca MAI la macchina del cliente (coerenza
ADR-007). Lo stesso artefatto canary viene eseguito su un runner `macos-26`; il cross-check finale
avviene sul target esatto con probe source-free. Quote/billing CI e costi/versione OS di un Mac cloud
si verificano prima dell'uso, senza cristallizzare prezzi temporali nell'ADR. La CI è anche il primo
enforcement automatico della suite (pytest su Darwin prima della build).

## Decisione D4 — Compilazione: Nuitka anche su macOS (parità ADR-007), PyInstaller come fallback dichiarato

Su Darwin Nuitka usa clang (Xcode CLT), niente `--msvc`/`--windows-console-mode`, output senza estensione. I 3 safety gates ADR-004, la cifratura build-time dei cataloghi (`db_crypto` è byte-oriented: i `.db.enc` sono identici cross-arch) e il verify/seal restano identici. Se la build arm64 incontra blocchi nei tempi del pilota: fallback PyInstaller (spec darwin dedicata) accettando un **downgrade anti-RE esplicito, temporaneo e tracciato** — mai silenzioso.

## Decisione D5 — L'artefatto consegnato richiede Developer ID e notarizzazione

Fatti (ricerca 2026, fonti nella spec): su ARM64 la firma almeno ad-hoc è obbligatoria; il bypass
right-click→Apri è stato rimosso (Sequoia); su Tahoe un bundle ad-hoc in quarantena produce "app
danneggiata" e "Open Anyway" è inaffidabile. L'enrollment Apple Developer va quindi avviato prima
del gate di distribuzione e la candidate consegnabile deve passare Developer ID, hardened runtime
e notarizzazione. La firma ad-hoc resta ammessa solo su artefatti interni del portability canary o
di debug: non è un canale di consegna e non genera workaround USB/scp al cliente. Se credenziali o
notarizzazione non sono disponibili, G-MAC.5 resta chiuso e si sposta il milestone.

## Decisione D6 — Kill-on-close di frpc su macOS: process-group + trap nel launcher, pkill nell'upgrade

Su macOS non esistono Job Object né PDEATHSIG. Equivalente a 2 livelli (specchio del modello Windows di pitfall #16): (1) frpc resta nel process-group/sessione del backend e `launcher.command` fa `trap 'kill -- -$$' EXIT` → chiusura finestra Terminal = morte dell'intero albero; (2) install/upgrade esegue `pkill -f frpc.toml` + kill backend prima di sostituire i file, sostituzione per rename mai in-place (un Mach-O in esecuzione sovrascritto in-place viene SIGKILLato per firma invalida). Rischio residuo dichiarato: orfano da SIGKILL diretto del backend (mitigabile con PID-file sweep al boot, opzionale nel pilota). Nota: su macOS l'orfano non locka il file immagine (l'upgrade non fallisce con codice 5) ma tiene il proxy-name su frps → tunnel rotto fino al kill.

## Interplay con G1 — chiuso dalla decisione founder 2026-07-31

La consegna data-bearing resta gated sul Pre-Delivery Security Gate. Il portability canary verifica
SQLCipher/Nuitka su Darwin prima che G1 venga congelato; il packaging finale segue l'application
freeze. Non esiste un'opzione di consegna operativa con `crm.db` plaintext. Se la compatibilità Mac
richiede lavoro aggiuntivo, il finding entra nello scope della v1.0.15 o sposta il milestone: non
genera una deroga di sicurezza.

## Addendum I — 2026-08-02: build evidence ≠ target compatibility

L'evidenza hardware del primo target ratifica **MacBook Air M1 2020, ARM64, 8 GB, macOS Tahoe
26.5.1**. Ne consegue un contratto di prova a tre livelli:

1. C0.0 fissa matrice, soglie e privacy prima del codice;
2. C0.1 costruisce su `macos-15` ed esegue il medesimo artefatto su `macos-26`;
3. C0.2 esegue quel canary compilato e source-free sul target esatto.

La label `macos-26` non garantisce la patch `26.5.1`: un PASS solo runner è evidenza di portabilità,
non certificazione del target. C0.2 non riceve sorgenti, toolchain, dati reali o chiavi private e non
emette seriale, `IOPlatformUUID`, output `ioreg` o fingerprint nei log/report. La prova di binding
licenza resta nel gate G-MAC.4/G-MAC.5 e nel canale amministrativo dedicato.

Un finding C0 diventa requisito della `v1.0.15` o sposta il milestone. Non può essere convertito in
waiver di sicurezza, in packaging anticipato o in un PASS condizionale presentato come compatibilità
confermata. Soglie e matrice falsificabile vivono in
`docs/specs/SPEC_G-MAC_CONSEGNA_MACOS.md` §3 C0.

## Conseguenze

- Nasce la prima CI del repo (GH Actions macOS): pytest su Darwin, build `macos-15`, smoke dello
  stesso artefatto su `macos-26` e safety gates ADR-004 su ogni release macOS.
- `SPEC_FINGERPRINT_CROSSPLATFORM` (G-MAC.0) è il cancello di fattibilità: codice fatto e T1 verificato (hash Windows invariato); T2 chiude su hardware reale.
- Il registro deployment (`DEPLOYMENTS.md`) traccia la piattaforma per cliente; il runbook di consegna macOS nasce in `docs/operations/`.
- Ogni futuro binario long-lived aggiunto al bundle deve dichiarare il proprio destino su ENTRAMBE le piattaforme (Job Object su win, process-group/trap su mac) — estensione del pitfall #16.
