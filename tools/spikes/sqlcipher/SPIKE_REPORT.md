# Spike SQLCipher — Report

- **Data:** 2026-06-16
- **Contesto:** ADR-013 (cifratura crm.db a riposo, gate G1 di `PRE_DELIVERY_SECURITY_GATE.md`)
- **Domanda:** l'asse A di ADR-013 (SQLCipher per la cifratura full-DB read-write) è realizzabile su questo stack — Windows + Python 3.12 + SQLAlchemy/SQLModel + **bundle Nuitka standalone**?
- **Verdetto:** ✅ **VALIDATO end-to-end.** SQLCipher è installabile come wheel nativo, cifra realmente, si integra con SQLAlchemy, e **sopravvive a Nuitka standalone** (binding + DLL crypto bundlati, l'exe gira e decifra).
- **Caveat (toolchain, non SQLCipher):** la validazione Nuitka è passata con **MSVC**; il path **MinGW** usato oggi dalla build reale (`build-backend-nuitka.sh --mingw64`) è attualmente **rotto** su questa macchina per un mismatch Nuitka 4.1.2 + gcc 15.2.0 (`windows.h not found`). Vedi §4.

---

## 1. Cancelli e risultati

| # | Cancello | Domanda | Esito |
|---|----------|---------|-------|
| 1 | Wheel Windows | Esiste un driver SQLCipher prebuilt per cp312/win_amd64? | ✅ `sqlcipher3-0.6.2-cp312-cp312-win_amd64.whl` (2.4 MB, amalgamation + crypto statica nel wheel) |
| 2 | Funzionale | Cifra davvero + si integra con SQLAlchemy? | ✅ 7/7 check (`test_sqlcipher_functional.py`) |
| 3 | Nuitka standalone | Il binding nativo sopravvive alla compilazione? | ✅ exe standalone gira: `SPIKE_NUITKA_SQLCIPHER_OK cipher_version=4.12.0 community` |

### Cancello 1 — wheel
`pip download --only-binary=:all:` ha trovato un wheel **nativo** `cp312-cp312-win_amd64`. Driver: **`sqlcipher3` 0.6.2** (binding stile pysqlite con SQLCipher statico). Niente DLL di sistema da procurare, niente build da sorgente. Gli altri candidati (`sqlcipher3-binary`, `pysqlcipher3`, `sqlcipher-binary`) **non** hanno wheel Windows.

### Cancello 2 — funzionale (`test_sqlcipher_functional.py`)
Tutti i check verdi:
- `import sqlcipher3` → **cipher_version 4.12.0 community**;
- crea DB cifrato + scrive;
- **ciphertext at-rest**: `sqlite3` stdlib rifiuta il file (`file is not a database`); header non-`SQLite format 3`;
- riapertura con chiave corretta → dati integri;
- **chiave sbagliata → respinta** (`DatabaseError`, con il rumore atteso `hmac check failed`);
- **integrazione SQLAlchemy**: `create_engine(..., module=sqlcipher3.dbapi2)` + `PRAGMA key` su evento `connect` → insert/select OK, file cifrato. *(È esattamente il pattern che userebbe l'engine business di FitManager.)*

### Cancello 3 — Nuitka standalone (`spike_entry.py`)
Build `--standalone --msvc=latest --include-package=sqlcipher3`. L'exe prodotto (5.4 MB, bundle 26 MB) **gira e decifra**:
```
SPIKE_NUITKA_SQLCIPHER_OK cipher_version=4.12.0 community   (exit 0)
```
Nuitka ha bundlato correttamente:
- `_sqlite3.pyd` (126 KB) — il binding nativo di sqlcipher3;
- **`libcrypto-3.dll` (5.2 MB)** — OpenSSL usato da SQLCipher per la crypto;
- `sqlite3.dll` (1.6 MB).

---

## 2. Implicazioni per ADR-013

- **Asse A (SQLCipher) confermato fattibile.** Cifratura full-DB trasparente, read-write, zero cambi ai modelli/query — solo `PRAGMA key` su connect via event listener SQLAlchemy.
- **Costo bundle:** +~7 MB (`libcrypto-3.dll` 5.2 + `sqlite3.dll` 1.6 + binding). Trascurabile su un installer ~117 MB.
- **Nota OpenSSL duplicato:** l'app porta già `cryptography` (che usa il proprio OpenSSL via `_rust.pyd`). SQLCipher aggiunge un `libcrypto-3.dll` separato. Coesistono (namespace diversi), ma sono ~5 MB di OpenSSL ridondante — accettabile, da annotare.
- **Driver scelto:** `sqlcipher3` (Charles Leifer), wheel cp312 nativo. Da aggiungere a `pyproject.toml` quando si implementa.

---

## 3. Verifiche residue (prima dell'implementazione di produzione)

- **`PRAGMA rekey`** (cambio password = ri-wrap DEK nell'envelope, §ADR-013 asse E) — non testato qui, ma supportato nativamente da SQLCipher.
- **`VACUUM INTO` con chiave** per il backup cifrato (G5) — da validare nel design backup.
- **WAL + SQLCipher**: il progetto usa `journal_mode=WAL`. Verificare che WAL su DB cifrato si comporti (il file `-wal` è anch'esso cifrato in SQLCipher 4). Da testare in implementazione.
- **Migrazione plaintext → cifrato** dei crm.db già deployati (Chiara) al primo boot post-upgrade, con backup preventivo.

---

## 4. Finding collaterale — toolchain di build (da risolvere a parte)

Due fatti emersi, **indipendenti da SQLCipher**, ma rilevanti per le release:

1. **La venv di progetto (`venv/`) non ha Nuitka installato** (`python -m nuitka` → "No module named nuitka"; nessuno script `nuitka` in `Scripts/`). L'ambiente che ha prodotto v1.0.12 (oggi) **non è catturato** nella venv → rischio per build riproducibili.
2. **Il path MinGW della build reale è attualmente rotto.** `build-backend-nuitka.sh` usa `--mingw64`. Con Nuitka **4.1.2** (ultima) + il MinGW auto-scaricato **gcc 15.2.0** (winlibs r6), la compilazione C fallisce con `fatal error: windows.h: No such file or directory` su **tutti** i moduli (non solo sqlcipher). `windows.h` **esiste** nel MinGW (`x86_64-w64-mingw32/include/`) → è Nuitka che non passa quel sysroot include al gcc nuovo. La build MSVC (VS 2022, `cl 14.3`) invece funziona.

**Implicazione:** prima della prossima release con SQLCipher servirà una decisione toolchain — o passare la build a `--msvc=latest`, o pinnare un gcc/winlibs compatibile, o pinnare la versione di Nuitka. **Non blocca la decisione su SQLCipher**, ma va sistemato. (Possibile che il gcc 15.2.0 sia stato tirato in cache proprio da questo spike; la build di v1.0.12 potrebbe aver usato un gcc precedente ora sovrascritto — da verificare.)

---

## 5. Artefatti

- `test_sqlcipher_functional.py` — test funzionale (cancello 2).
- `spike_entry.py` — entry per il build Nuitka (cancello 3).
- `nuitka_build.log` / `nuitka_msvc.log` — log build (MinGW fallito / MSVC ok).
- `dist_spike/`, `.venv/`, `_probe/`, `*.whl` — artefatti pesanti, **git-ignored** (vedi `.gitignore`). Riproducibili dai due script.
