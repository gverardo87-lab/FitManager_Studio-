# ADR-007 — Anti-Reverse Engineering (Layered Hardening)

**Data**: 2026-04-09
**Stato**: Accettata
**Autore**: Giacomo Verardo + Claude (Security Audit)

## Contesto

Il Red Team audit baseline (2026-04-01) ha rivelato che un attaccante L2 (sviluppatore esperto) poteva estrarre l'intero patrimonio IP dal software installato in meno di 1 giorno:

- **catalog.db + nutrition.db**: apribili in 5 secondi con qualsiasi client SQLite
- **30 migration Alembic**: schema completo 26 tabelle business in chiaro nel bundle
- **4 seed JSON** (4 MB): 500 esercizi completi in chiaro nel bundle
- **Bytecode Python**: estraibile in 30 sec (pyinstxtractor) e decompilabile in 15 min (decompyle3)

Audit completo: `docs/technical/SECURITY_AUDIT_BASELINE.md`

Il software sara' installato sulla macchina del partner commerciale per il POC con 10 Fondatori. La protezione deve essere proporzionata: bloccare L2 (sviluppatore esperto), non L3+ (RE professionale).

## Decisione

Implementare un hardening a 4 step stratificati, ciascuno indipendente e rilasciabile singolarmente:

| Step | Cosa | Impatto |
|------|------|---------|
| **1** | Rimuovere Alembic migrations dal bundle | Schema DB nascosto |
| **2** | Rimuovere seed JSON dal bundle | Dati esercizi non in chiaro |
| **3** | Cifrare catalog.db + nutrition.db (AES-256-GCM) | Patrimonio scientifico protetto |
| **4** | Compilazione nativa Nuitka (Python → C → x86-64) | Codice sorgente non decompilabile |

### Step 1 — Bundle Sanitization (Alembic)

Rimossi da `fitmanager.spec` le entry `datas[]` per `alembic/` e `alembic.ini`, e i 4 `hiddenimports` Alembic. Alembic non e' mai importato a runtime — `schema_sync.py` usa ALTER TABLE raw.

### Step 2 — Bundle Sanitization (Seed JSON)

Rimossi i 4 file seed_*.json da `fitmanager.spec` e `fitmanager.iss`. In `seed_exercises.py` aggiunto guard: se in compiled mode e file assente, log info e return 0. catalog.db pre-built contiene gia' tutti i dati.

### Step 3 — Database Encryption (AES-256-GCM)

Nuovo modulo `api/services/db_crypto.py`: encrypt/decrypt con AES-256-GCM e chiave derivata via PBKDF2-HMAC-SHA256 da seed embedded nel codice.

Build-time: `encrypt_db()` produce `catalog.db.enc` e `nutrition.db.enc` (salt 16B + nonce 12B + ciphertext). Runtime: `decrypt_db_to_bytes()` → `sqlite3.deserialize()` → in-memory SQLAlchemy engine.

Dev mode: usa `.db` plain (zero cambiamenti al workflow sviluppo).

Scelta AES-256-GCM vs SQLCipher:
- SQLCipher richiede build da sorgente Windows (Visual Studio + OpenSSL)
- Cambia dialect SQLAlchemy (`sqlite+pysqlcipher`)
- I DB sono piccoli (3.5 MB) → in-memory approach piu' semplice

### Step 4 — Native Compilation (Nuitka)

Nuovo script `tools/build/build-backend-nuitka.sh`: compila Python → C → x86-64 nativo. Zero `.pyc` decompilabile nel bundle.

Nuovo helper `is_compiled()` in `api/config.py`: rileva sia `sys.frozen` (PyInstaller) che `__compiled__` (Nuitka). Usato in:
- `api/config.py` (PROJECT_ROOT detection)
- `api/services/license.py` (key resolution)
- `api/services/system_runtime.py` (enforcement toggle)
- `api/database.py` (encrypted DB loading)
- `api/seed_exercises.py` (frozen guard)

`fitmanager.spec` preservato come backup per rollback a PyInstaller.

## Alternative considerate

| Alternativa | Pro | Contro | Decisione |
|-------------|-----|--------|-----------|
| **SQLCipher** | Standard industria | Build complessa su Windows, cambia dialect SQLAlchemy | Scartata (AES-256-GCM piu' pragmatica) |
| **PyArmor** | Veloce da integrare | Licenza commerciale, bytecode comunque patchabile | Scartata (Nuitka superiore) |
| **Full obfuscation** (pyarmor + PyInstaller) | Compatibile | Non nativo, crackabile con effort L2 | Scartata |
| **VMProtect / Themida** | Protezione estrema | Windows-only, costo alto, over-engineering per L2 | Scartata (sproporzionata) |

## File impattati

| File | Tipo modifica |
|------|--------------|
| `api/config.py` | `is_compiled()` helper, `CATALOG_DB_ENC`, `NUTRITION_DB_ENC` |
| `api/database.py` | `_load_encrypted_db()`, engine condizionale per `.db.enc` |
| `api/services/db_crypto.py` | **NUOVO** — AES-256-GCM encrypt/decrypt |
| `api/services/license.py` | `is_compiled()` al posto di `_is_frozen()` |
| `api/services/system_runtime.py` | `is_compiled()` per enforcement |
| `api/seed_exercises.py` | Guard compiled mode per file assenti |
| `api/main.py` | Skip WAL purge per DB in-memory |
| `tools/build/fitmanager.spec` | Rimossi Alembic + seed JSON |
| `tools/build/build-backend-nuitka.sh` | **NUOVO** — build script Nuitka |
| `tools/build/build-installer.sh` | Cifratura DB pre-packaging |
| `tools/build/build-release.sh` | Conteggi nutrition pre-cifratura |
| `installer/fitmanager.iss` | `.db.enc` al posto di `.db`, rimossi seed JSON |

## Conseguenze

### Positive
- **TTC dati scientifici**: da 5 secondi a > 1 giorno (Step 3) / > 1 settimana (Step 4)
- **TTC codice sorgente**: da 15 minuti a > 1 settimana (Step 4)
- **TTC license bypass**: da 1-2 ore a > 3 giorni (Step 4)
- **Schema DB**: non piu' esposto nel bundle (Step 1)
- **Seed JSON**: eliminati dal bundle distribuito (Step 2)

### Negative
- Build time: 10-30 minuti (Nuitka) vs 1-2 minuti (PyInstaller)
- Primo build Nuitka puo' richiedere trial-and-error per hidden imports
- RAM runtime: +3.5 MB per DB in-memory (negligibile)

### Rollback
- `fitmanager.spec` preservato — `pyinstaller fitmanager.spec` per tornare a PyInstaller
- DB plain sempre disponibili in dev mode
- Ogni step e' indipendente — si possono disabilitare singolarmente

## Riferimenti

- `docs/security/ANTI_REVERSE_ENGINEERING_STRATEGY.md` — strategia completa
- `docs/technical/SECURITY_MODEL.md` — modello 6 livelli
- `docs/technical/SECURITY_AUDIT_BASELINE.md` — audit pre-hardening
- `docs/technical/SECURITY_AUDIT_POST_HARDENING.md` — audit post-hardening
- `docs/adr/ADR-005-license-hardening-anti-tampering.md` — hardening licenza (complementare)
