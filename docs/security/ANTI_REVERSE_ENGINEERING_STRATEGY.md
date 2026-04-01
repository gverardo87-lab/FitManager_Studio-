# Strategia Anti-Reverse Engineering — FitManager AI Studio

**Versione**: 1.0
**Data**: 2026-04-01
**Autore**: Giacomo Verardo + Claude (Security Audit)
**Stato**: Approvato per implementazione
**Branch**: FitManager_Studio

---

## 1. Contesto e Motivazione

Alessio Crociani (partner commerciale) ricevera' il software installato per il POC con 10 Fondatori. Il software contiene proprieta' intellettuale significativa costruita in mesi di lavoro:

- **Training Science Engine**: ~9.000 LOC di algoritmi proprietari (periodizzazione, EMG, MEV/MAV/MRV, plan builder)
- **Nutrition Science Engine**: ~2.500 LOC (piano LARN 7gg, 14 slot proteici, porzioni)
- **Safety Engine**: 47 condizioni mediche, 80 pattern rules
- **Catalogo Esercizi**: 500 esercizi x 43 colonne (biomeccanica, demand vector 10D, coaching cues)
- **Catalogo Alimenti**: 880 alimenti CREA 2019 + 12 template dieta LARN
- **Contract Integrity Engine**: 12 livelli di protezione finanziaria

**Rischio**: un programmatore esperto (L2) puo' estrarre tutto il codice sorgente e i dati scientifici dal software installato in meno di 1 giorno.

---

## 2. Principio Guida

> **La protezione software non e' un prodotto, e' un processo ciclico.**
> L'obiettivo non e' l'invulnerabilita' — e' alzare il costo dell'attacco oltre il valore del bottino.

**Formula chiave**: `Protezione sufficiente = costo attacco > valore di cio' che si ottiene`

Per FitManager (licenza EUR 249, nicchia italiana): protezione L2 (sviluppatore esperto) e' business-sufficiente.

---

## 3. Threat Model

### 3.1 Tassonomia Attaccanti (5 livelli)

| Livello | Profilo | Tool | Tempo Budget | Motivazione |
|---------|---------|------|-------------|-------------|
| **L0** | Utente curioso | Google, YouTube | 10 min | "Vediamo cosa c'e' dentro" |
| **L1** | Tecnico base | pyinstxtractor, DB Browser | 1-2 ore | Copiare il DB esercizi |
| **L2** | Sviluppatore esperto | decompyle3, Ghidra, Frida | 1-3 giorni | Clonare il prodotto |
| **L3** | RE professionale | angr, symbolic execution, IDA Pro | 1-2 settimane | Craccare DRM commerciale |
| **L4** | Nation-state | Custom tool, 0-day | Illimitato | Fuori scope |

### 3.2 Attaccante Target

**Profilo**: Alessio Crociani o sviluppatore da lui ingaggiato.
**Livello stimato**: L1-L2 (competenze Python, accesso al software installato).
**Motivazione worst-case**: Clonare il prodotto, bypassare licenza, estrarre patrimonio scientifico.
**Accesso**: Software installato su PC del partner (accesso completo ai file locali).

### 3.3 Crown Jewels (asset da proteggere)

| Tier | Asset | LOC/Righe | Valore | Priorita' |
|------|-------|-----------|--------|-----------|
| **Crown Jewels** | Training Science Engine | ~9.000 LOC | Differenziale competitivo | MASSIMA |
| **Crown Jewels** | Nutrition Science Engine | ~2.500 LOC | Differenziale competitivo | MASSIMA |
| **Crown Jewels** | Safety Engine | ~250 LOC | 47 condizioni, 80 rules | ALTA |
| **Crown Jewels** | Catalogo 500 esercizi | 500 x 43 colonne | Mesi di lavoro scientifico | MASSIMA |
| **Crown Jewels** | 880 alimenti CREA + template | 3.000+ righe DB | Patrimonio nutrizionale | ALTA |
| **Business Logic** | Contract Integrity Engine | ~500 LOC | Replicabile con effort | MEDIA |
| **Business Logic** | Dashboard KPI, WhatsApp templates | ~2.000 LOC | Pattern standard | BASSA |
| **Commodity** | CRUD, auth JWT, componenti UI | ~10.000 LOC | Chiunque la riscrive | MINIMA |

---

## 4. Layered Defense — I 6 Anelli di Protezione

```
+================================================================+
|  ANELLO 6: Environmental Checks (runtime watchdog)             |
|  +----------------------------------------------------------+  |
|  |  ANELLO 5: Code Virtualization / Native Compilation       |  |
|  |  +----------------------------------------------------+  |  |
|  |  |  ANELLO 4: Obfuscation (illeggibilita')            |  |  |
|  |  |  +----------------------------------------------+  |  |  |
|  |  |  |  ANELLO 3: Integrity Verification             |  |  |  |
|  |  |  |  +----------------------------------------+  |  |  |  |
|  |  |  |  |  ANELLO 2: Licensing + HW Binding       |  |  |  |  |
|  |  |  |  |  +----------------------------------+  |  |  |  |  |
|  |  |  |  |  |  ANELLO 1: Legal                  |  |  |  |  |  |
|  |  |  |  |  +----------------------------------+  |  |  |  |  |
|  |  |  |  +----------------------------------------+  |  |  |  |
|  |  |  +----------------------------------------------+  |  |  |
|  |  +----------------------------------------------------+  |  |
|  +----------------------------------------------------------+  |
+================================================================+
```

### 4.1 Stato Attuale (pre-hardening, v1.0.6)

| Anello | Descrizione | Stato | Gap |
|--------|-------------|-------|-----|
| 1. Legal | NDA + non-compete + penale | **NON FIRMATO** | Bloccante per consegna |
| 2. Licensing | JWT RS256 + HW binding (ADR-005) | **Buono** | OK se bytecode protetto |
| 3. Integrity | Hash chiave pubblica embedded | **Minimale** | Serve CRC/self-hash |
| 4. Obfuscation | Codice offuscato/cifrato | **ASSENTE** | Zero protezione |
| 5. Virtualization | Compilazione nativa | **ASSENTE** | Zero protezione |
| 6. Environmental | Anti-debug runtime | **ASSENTE** | Bassa priorita' per L2 |

### 4.2 Stato Target (post-hardening)

| Anello | Stato Target | Implementazione |
|--------|-------------|-----------------|
| 1. Legal | NDA + non-compete firmati | Accordo legale (fuori scope tecnico) |
| 2. Licensing | Invariato (gia' buono) | ADR-005 gia' implementato |
| 3. Integrity | DB cifrati + hash chiave | AES-256-GCM su cataloghi |
| 4. Obfuscation | Nessun .pyc leggibile, nessun JSON/SQL in chiaro | Rimozione Alembic + seed + cifratura DB |
| 5. Virtualization | Python compilato a codice nativo | Nuitka (Python → C → x86-64) |
| 6. Environmental | Fuori scope Phase 1 | Da valutare se emerge piracy |

---

## 5. Red Team Audit Baseline (v1.0.6)

Audit completo: `docs/technical/SECURITY_AUDIT_BASELINE.md`

### 5.1 Risultati Sintetici

| # | Test | Target | TTC Attuale | TTC Target | Verdetto |
|---|------|--------|-------------|------------|----------|
| 1 | PyInstaller bundle | Bytecode Python | **30 sec** | > 4 ore | **FAIL** |
| 2 | Database cataloghi | Patrimonio scientifico | **5 sec** | > 1 ora | **FAIL CRITICO** |
| 3 | Seed + Migrations | Schema + dati esercizi | **0 sec** | > 1 ora | **FAIL** |
| 4 | String extraction | Stringhe sensibili | N/A (post-PYZ) | N/A | PASS parziale |
| 5 | Frontend build | Codice TypeScript | 1-2 giorni | 1-2 giorni | **PASS** |
| 6 | License bypass | Sistema licenza | **1-2 ore** | > 8 ore | PASS condizionato |
| 7 | Decompilation | Codice proprietario | **< 15 min** | > 1 giorno | **FAIL** |

### 5.2 Scoperte Critiche

1. **catalog.db + nutrition.db**: patrimonio scientifico apribile in 5 secondi con qualsiasi SQLite client
2. **30 migration Alembic**: file .py plaintext nel bundle, espongono schema completo 26 tabelle business
3. **4 seed JSON** (4 MB): 500 esercizi completi + relazioni in chiaro nel bundle
4. **Bytecode Python**: estraibile in 30 sec (pyinstxtractor) e decompilabile in 15 min (decompyle3)
5. **Frontend**: PASS — source map vuote (stub 53 bytes), TypeScript non recuperabile

---

## 6. Piano di Implementazione — 4 Step

### 6.1 Panoramica

| Step | Cosa | Tempo | Rischio | Impatto TTC |
|------|------|-------|---------|-------------|
| **1** | Rimuovere Alembic dal bundle | 30 min | Zero | Schema nascosto |
| **2** | Rimuovere seed JSON dal bundle | 45 min | Basso | Dati esercizi non in chiaro |
| **3** | Cifrare catalog.db + nutrition.db (AES-256-GCM) | 3-4 ore | Medio | Da 5 sec a impossibile |
| **4** | Nuitka compilation (Python → C → nativo) | 4-8 ore | Alto | Da 15 min a impossibile |

**Totale stimato**: 1-2 giorni.
**Ogni step e' indipendente**: committabile e testabile singolarmente.
**Rollback**: PyInstaller `.spec.bak` per tornare al build precedente.

---

### 6.2 STEP 1 — Rimuovere Alembic dal Bundle

**Razionale**: 31 file migration .py in plaintext espongono l'intero schema delle 26 tabelle business. Alembic non e' MAI importato a runtime — `schema_sync.py` usa `ALTER TABLE` raw con zero dipendenza Alembic.

**File da modificare**:
- `tools/build/fitmanager.spec` — rimuovere 2 entry da `datas[]` (alembic dir + alembic.ini) e 4 entry da `hiddenimports[]` (alembic.*)

**Cosa rimuovere da `datas[]`**:
```python
# RIMUOVERE:
(str(ROOT / 'alembic'), 'alembic'),
(str(ROOT / 'alembic.ini'), '.'),
```

**Cosa rimuovere da `hiddenimports[]`**:
```python
# RIMUOVERE:
'alembic',
'alembic.migration',
'alembic.operations',
'alembic.script',
```

**Verifica**:
- [ ] `dist/fitmanager/_internal/alembic/` non esiste piu'
- [ ] Smoke test: `/health` OK, esercizi funzionano
- [ ] pytest passa

**Rischio**: ZERO. Alembic e' un tool dev-only.

---

### 6.3 STEP 2 — Rimuovere Seed JSON dal Bundle

**Razionale**: 4 file JSON (4 MB) espongono tutti i 500 esercizi in chiaro con 43 colonne. catalog.db e' pre-costruito e shipped con l'installer — i JSON sono un safety net ridondante.

**File da modificare**:
- `tools/build/fitmanager.spec` — rimuovere 4 entry seed_*.json da `datas[]`
- `installer/fitmanager.iss` — rimuovere 4 righe Source seed_*.json dalla sezione `[Files]`
- `api/seed_exercises.py` — aggiungere guard frozen: se `sys.frozen` e file assente, log info (non warning) e return 0

**Modifica `api/seed_exercises.py`**:

Aggiungere `import sys` in testa. In `seed_builtin_exercises()`, `seed_exercise_relations()`, `seed_exercise_media()`, dopo il check `if not SEED_FILE.exists()`:

```python
if not SEED_FILE.exists():
    if getattr(sys, "frozen", False):
        logger.info("Seed esercizi: file non presente in bundle (atteso in frozen mode)")
    else:
        logger.warning(f"Seed esercizi: file non trovato {SEED_FILE}")
    return 0
```

**Verifica**:
- [ ] `dist/fitmanager/_internal/data/exercises/` non esiste
- [ ] Installer non contiene seed_*.json
- [ ] `/api/exercises` ritorna 500 esercizi (da catalog.db pre-built)
- [ ] Log mostra "gia' presenti 500 builtin, skip" (catalog.db ha i dati)

**Rischio**: BASSO. catalog.db e' sempre presente e pre-popolato.

---

### 6.4 STEP 3 — Cifrare catalog.db + nutrition.db (AES-256-GCM)

**Razionale**: I 2 cataloghi scientifici (3.5 MB totali) sono il patrimonio IP piu' esposto. Apribili con qualsiasi SQLite client in 5 secondi. Li cifriamo con AES-256-GCM e li decifriamo in memoria a runtime.

**Perche' AES-256-GCM e non SQLCipher**:
- SQLCipher richiede build da sorgente su Windows (Visual Studio + OpenSSL + amalgamation)
- Cambia il dialect SQLAlchemy da `sqlite` a `sqlite+pysqlcipher` (rompe tutti i check)
- Dependency hell con Nuitka/PyInstaller
- I DB sono piccoli (3.5 MB) → in-memory approach e' piu' semplice e veloce

**Architettura**:
```
BUILD TIME:  catalog.db  --encrypt_db()--> catalog.db.enc  (shipped nell'installer)
RUNTIME:     catalog.db.enc --decrypt()--> sqlite3.deserialize() --> in-memory SQLAlchemy engine
DEV MODE:    catalog.db (plain) --> engine normale (zero cambiamenti)
```

`sqlite3.Connection.deserialize()` e' disponibile in Python 3.11+ (progetto usa 3.12).

**File da creare**:

#### `api/services/db_crypto.py` (NUOVO)

```python
"""
AES-256-GCM encrypt/decrypt per cataloghi scientifici.

Build time: encrypt catalog.db → catalog.db.enc (via build-installer.sh)
Runtime: decrypt .enc → in-memory SQLite (zero temp file su disco)

Chiave derivata con PBKDF2-HMAC-SHA256 da seed embedded nel codice.
Il .enc e' inutile senza il binario compilato che contiene il seed.
"""
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Seed embedded (32 bytes hex). Generato una volta con secrets.token_hex(32).
# Questo e' il "something you have" (il binario).
_EMBEDDED_KEY_SEED = "<64 hex chars — generare con secrets.token_hex(32)>"
_EMBEDDED_KEY_HASH = "<sha256 del seed per integrity check>"

def _verify_seed_integrity() -> bool:
    actual = hashlib.sha256(_EMBEDDED_KEY_SEED.encode()).hexdigest()
    return actual == _EMBEDDED_KEY_HASH

def _derive_key(salt: bytes) -> bytes:
    """Deriva chiave AES-256 da seed embedded + salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(bytes.fromhex(_EMBEDDED_KEY_SEED))

def encrypt_db(db_path: Path, output_path: Path) -> None:
    """Build-time: cifra un file SQLite.

    Formato output: salt(16 bytes) + nonce(12 bytes) + ciphertext(N bytes)
    """
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(salt)
    plaintext = db_path.read_bytes()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    output_path.write_bytes(salt + nonce + ciphertext)

def decrypt_db_to_bytes(enc_path: Path) -> bytes:
    """Runtime: decifra .enc e ritorna bytes SQLite raw."""
    data = enc_path.read_bytes()
    salt, nonce, ciphertext = data[:16], data[16:28], data[28:]
    key = _derive_key(salt)
    return AESGCM(key).decrypt(nonce, ciphertext, None)
```

**File da modificare**:

#### `api/config.py`

Aggiungere dopo le definizioni DATABASE_URL:
```python
# Path cifrati per frozen mode (distribuiti dall'installer)
CATALOG_DB_ENC: Path = DATA_DIR / "catalog.db.enc"
NUTRITION_DB_ENC: Path = DATA_DIR / "nutrition.db.enc"
```

#### `api/database.py`

Aggiungere funzione `_load_encrypted_db()` e logica condizionale per engine creation:

```python
import sys
from pathlib import Path
from api.config import DATA_DIR

def _load_encrypted_db(enc_path: Path, label: str) -> Engine:
    """Decripta .enc → in-memory SQLite via deserialize()."""
    import sqlite3 as sqlite3_stdlib
    from sqlalchemy.pool import StaticPool
    from api.services.db_crypto import decrypt_db_to_bytes

    db_bytes = decrypt_db_to_bytes(enc_path)
    conn = sqlite3_stdlib.connect(":memory:")
    conn.deserialize(db_bytes)
    conn.execute("PRAGMA foreign_keys=ON")
    logger.info(f"Loaded encrypted {label} ({len(db_bytes):,} bytes) into memory")

    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        creator=lambda: conn,
    )

# Catalog engine — cifrato in frozen mode, plain in dev
_catalog_enc = DATA_DIR / "catalog.db.enc"
if getattr(sys, "frozen", False) and _catalog_enc.exists():
    catalog_engine = _load_encrypted_db(_catalog_enc, "catalog")
else:
    # ... engine creation esistente (invariata)

# Nutrition engine — stesso pattern
_nutrition_enc = DATA_DIR / "nutrition.db.enc"
if getattr(sys, "frozen", False) and _nutrition_enc.exists():
    nutrition_engine = _load_encrypted_db(_nutrition_enc, "nutrition")
else:
    # ... engine creation esistente (invariata)
```

#### `tools/build/build-installer.sh`

Dopo staging dei DB, aggiungere cifratura:
```bash
echo "Encrypting catalog databases..."
"$PYTHON_BIN" -c "
from pathlib import Path; import sys; sys.path.insert(0, '$ROOT')
from api.services.db_crypto import encrypt_db
encrypt_db(Path('$RELEASE_DATA_DIR/catalog.db'), Path('$RELEASE_DATA_DIR/catalog.db.enc'))
encrypt_db(Path('$RELEASE_DATA_DIR/nutrition.db'), Path('$RELEASE_DATA_DIR/nutrition.db.enc'))
"
rm "$RELEASE_DATA_DIR/catalog.db" "$RELEASE_DATA_DIR/nutrition.db"
```

#### `installer/fitmanager.iss`

Cambiare source:
```ini
; DA:
Source: "..\dist\release-data\catalog.db"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\dist\release-data\nutrition.db"; DestDir: "{app}\data"; Flags: ignoreversion
; A:
Source: "..\dist\release-data\catalog.db.enc"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\dist\release-data\nutrition.db.enc"; DestDir: "{app}\data"; Flags: ignoreversion
```

#### `api/main.py`

Skip `_purge_stale_wal()` per DB cifrati (no WAL per in-memory):
```python
# In lifespan, prima del WAL purge:
if not (DATA_DIR / "catalog.db.enc").exists():
    _purge_stale_wal(DATA_DIR / "catalog.db")
if not (DATA_DIR / "nutrition.db.enc").exists():
    _purge_stale_wal(DATA_DIR / "nutrition.db")
```

#### `tools/build/build-release.sh`

Fase SEAL: estrarre conteggi nutrition PRIMA della cifratura, dal source `data/nutrition.db` anziche' dallo staging.

**Verifica**:
- [ ] `dist/release-data/` contiene `.enc`, nessun `.db` plain
- [ ] `sqlite3 catalog.db.enc` → "not a database"
- [ ] Smoke test: `/health` con `catalog: connected`
- [ ] `/api/exercises` ritorna 500 esercizi
- [ ] Dev mode (`--port 8001`) usa `.db` plain (invariato)
- [ ] pytest tutti pass (usano in-memory, non toccati)

**Rischi e mitigazioni**:
- `deserialize()` richiede Python 3.12+ → confermato
- RAM +3.5MB → negligibile
- Se `.enc` corrotto → crash startup con log CRITICAL (aggiungere try/except)
- WAL purge → skip per DB in-memory

---

### 6.5 STEP 4 — Nuitka Compilation (Python → C → Nativo)

**Razionale**: PyInstaller impacchetta `.pyc` bytecode estraibile (pyinstxtractor) e decompilabile (decompyle3). Nuitka compila Python in C, poi in codice macchina x86-64 nativo. Il risultato non e' decompilabile — un attaccante vede solo assembly.

**Prerequisiti**:
- `pip install nuitka` nel venv
- Nuitka scarica automaticamente MinGW64 al primo build (`--assume-yes-for-downloads`)
- Build time: 10-30 minuti (vs 1-2 min PyInstaller) — accettabile per release

**Fattibilita' verificata**:
- Zero import dinamici in `api/` (confermato con grep)
- Tutte le C extension gia' precompilate (.pyd per Windows)
- pyproject.toml standard (setuptools)
- Nuitka compatibilita' stimata: 95%

**File da modificare**:

#### `api/config.py` — helper condiviso

```python
def is_compiled() -> bool:
    """Detect compiled binary (PyInstaller frozen OR Nuitka compiled)."""
    return getattr(sys, "frozen", False) or "__compiled__" in dir()
```

Poi sostituire tutti i `getattr(sys, "frozen", False)` con `is_compiled()` in:
- `api/config.py` (line 17: PROJECT_ROOT detection)
- `api/services/license.py` (`_is_frozen()`)
- `api/services/system_runtime.py` (`get_distribution_mode()`, `is_license_enforcement_enabled()`)
- `api/database.py` (engine creation condizionale — Step 3)
- `api/seed_exercises.py` (frozen guard — Step 2)

#### `tools/build/build-backend.sh` — rimpiazzare PyInstaller

Comando Nuitka:
```bash
"$PYTHON_BIN" -m nuitka \
    --standalone \
    --mingw64 \
    --output-dir="$ROOT/dist" \
    --output-filename=fitmanager.exe \
    --include-package=api \
    --include-package=uvicorn \
    --include-package=fastapi \
    --include-package=starlette \
    --include-package=sqlmodel \
    --include-package=sqlalchemy \
    --include-package=pydantic \
    --include-package=pydantic_core \
    --include-package=jose \
    --include-package=bcrypt \
    --include-package=dotenv \
    --include-package=email_validator \
    --include-package=multipart \
    --include-package=openpyxl \
    --include-package=cryptography \
    --include-package=dateutil \
    --nofollow-import-to=torch \
    --nofollow-import-to=transformers \
    --nofollow-import-to=langchain \
    --nofollow-import-to=chromadb \
    --nofollow-import-to=sklearn \
    --nofollow-import-to=streamlit \
    --nofollow-import-to=plotly \
    --nofollow-import-to=matplotlib \
    --nofollow-import-to=pytest \
    --nofollow-import-to=IPython \
    --nofollow-import-to=core \
    --nofollow-import-to=alembic \
    --enable-plugin=anti-bloat \
    --remove-output \
    --assume-yes-for-downloads \
    --windows-console-mode=force \
    "$ROOT/tools/build/entry_point.py"

# Rinomina output per matchare struttura Inno Setup
mv "$ROOT/dist/entry_point.dist" "$ROOT/dist/fitmanager"
```

#### `tools/build/fitmanager.spec`

Rinominare a `fitmanager.spec.bak` (backup per rollback di emergenza).

#### `installer/fitmanager.iss`

Verificare che il path `dist\fitmanager\*` per il backend sia ancora corretto dopo il rename output.

**Verifica**:
- [ ] Build Nuitka completa senza errori
- [ ] `pyinstxtractor fitmanager.exe` → FALLISCE (non e' PyInstaller)
- [ ] `decompyle3` → nulla da decompilare (zero .pyc)
- [ ] `strings fitmanager.exe | grep "def seed_builtin"` → nulla (codice nativo)
- [ ] Smoke test: `/health` con 5 invarianti OK
- [ ] `/api/exercises` → 500 esercizi
- [ ] License enforcement funziona (`is_compiled()` rileva Nuitka)

**Rischi e mitigazioni**:
- **Build time 10-30 min**: accettabile per release, dev mode non toccato
- **Hidden imports mancanti**: primo build potrebbe richiedere trial-and-error. Budget 1-2 ore
- **Nuitka `__compiled__` vs `sys.frozen`**: gestito da `is_compiled()` helper
- **Rollback**: `fitmanager.spec.bak` per tornare a PyInstaller se bloccante

---

## 7. Ordine di Esecuzione e Commit

```
Step 1 → build + test → commit "hardening: remove Alembic migrations from distribution bundle"
   |
Step 2 → build + test → commit "hardening: remove seed JSONs from bundle (catalog.db self-sufficient)"
   |
Step 3 → build + test → commit "hardening: AES-256-GCM encryption for catalog.db + nutrition.db"
   |
Step 4 → build + test → commit "hardening: replace PyInstaller with Nuitka native compilation (ADR-007)"
```

**Ogni step e' indipendente e rilasciabile.** Se Step 4 ha problemi, gli Step 1-3 proteggono gia' i dati scientifici.

---

## 8. Impatto TTC Post-Hardening (stimato)

| Asset | TTC Pre | TTC Post (Step 1-3) | TTC Post (Step 1-4) |
|-------|---------|---------------------|----------------------|
| Schema 26 tabelle | **0 sec** | > 1 giorno | > 1 settimana |
| Catalogo 500 esercizi | **5 sec** | > 1 giorno | > 1 settimana |
| 880 alimenti CREA | **5 sec** | > 1 giorno | > 1 settimana |
| Training Science (9K LOC) | **15 min** | 15 min (invariato) | **> 1 settimana** |
| Nutrition Science (2.5K LOC) | **15 min** | 15 min (invariato) | **> 1 settimana** |
| License bypass | **1-2 ore** | 1-2 ore (invariato) | **> 3 giorni** |
| Seed esercizi JSON | **0 sec** | **impossibile** (rimosso) | **impossibile** |

---

## 9. Checklist Finale Post-Implementazione

### Test Red Team (da ripetere dopo tutti gli step)

- [ ] `pyinstxtractor fitmanager.exe` → fallisce
- [ ] `decompyle3` → nulla da decompilare
- [ ] `sqlite3 catalog.db.enc` → "not a database"
- [ ] `strings exe | grep EMBEDDED_PUBLIC_KEY` → nulla
- [ ] Zero `alembic/` nel bundle installato
- [ ] Zero `seed_*.json` nel bundle installato
- [ ] Zero `.db` plain (solo `.enc`) per cataloghi

### Test Funzionali (invarianza)

- [ ] `/health` → 5 invarianti OK
- [ ] `/api/exercises` → 500 esercizi
- [ ] Dev mode (`--port 8001`) → funziona invariato
- [ ] pytest 349 test → tutti passano
- [ ] Bundle size comparabile (~50-120 MB)
- [ ] `build-release.sh` completa tutte le 5 fasi

### Documentazione

- [ ] `docs/adr/ADR-007-anti-reverse-engineering.md`
- [ ] `docs/technical/SECURITY_MODEL.md` aggiornato
- [ ] `docs/technical/SECURITY_AUDIT_POST_HARDENING.md`
- [ ] `CLAUDE.md` root aggiornato (nota build Nuitka)

---

## 10. Protezioni Future (Trigger-Based)

Non implementare in anticipo. Investire solo quando c'e' evidenza.

| Trigger | Azione | Costo | Impatto |
|---------|--------|-------|---------|
| **50+ clienti** | Code signing Authenticode | Basso | Tamper detection OS-level |
| **Evidenza piracy** | Analisi crack + patch vettore specifico | Medio | Chiude vettore specifico |
| **Distribuzione internazionale** | License revocation list | Basso | Blocca licenze compromesse |
| **Scale significativa** | License server (phone-home periodico) | Alto | Revoca + analytics |
| **Regolamentazione** | SQLCipher su crm.db (dati clinici) | Medio | HIPAA/GDPR compliance |
| **Clone sul mercato** | Anti-debug runtime (Frida detection) | Medio | Anello 6 completo |

---

## 11. Skill Installate per Security Testing

| Skill | Source | Installs | Uso |
|-------|--------|----------|-----|
| `anti-reversing-techniques` | wshobson/agents | 3.5K | Framework protezione: anti-debug, obfuscation, code virtualization |
| `ctf-reverse` | ljagiello/ctf-skills | 1.1K | Red team testing: decompilazione, analisi binari, bypass detection |

Installate globalmente in `~/.agents/skills/`. Disponibili per audit e re-test futuri.

---

## 12. Riferimenti

| Documento | Path | Contenuto |
|-----------|------|-----------|
| Red Team Audit Baseline | `docs/technical/SECURITY_AUDIT_BASELINE.md` | 7 test, TTC per Crown Jewel |
| Security Model esistente | `docs/technical/SECURITY_MODEL.md` | 5 livelli protezione pre-hardening |
| ADR-005 License Hardening | `docs/adr/ADR-005-license-hardening-anti-tampering.md` | 4 layer anti-tamper licenza |
| Skill anti-reversing | `~/.agents/skills/anti-reversing-techniques/SKILL.md` | Anti-debug, obfuscation, bypass |
| Skill ctf-reverse | `~/.agents/skills/ctf-reverse/SKILL.md` | RE tools, decompilazione, analisi |
| Standard OWASP MASVS-R | Esterno | Resilience requirements (adattato da mobile) |
