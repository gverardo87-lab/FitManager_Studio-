# api/config.py
"""
Configurazione API — tutti i valori sensibili da variabili d'ambiente.

Per sviluppo locale basta il .env. In produzione, usa secrets management.
DATABASE_URL e' l'unica riga da cambiare per passare a PostgreSQL.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Paths (prima di load_dotenv per poter caricare data/.env)
# PyInstaller frozen: exe e' in {app}/backend/fitmanager.exe → parent.parent = {app}/
# Nuitka compiled: __compiled__ iniettato nel namespace del modulo, stesso layout di PyInstaller
# Source tree: config.py e' in {project}/api/config.py → parents[1] = {project}/
# NOTA: il check usa globals(), MAI dir() — dentro una funzione dir() ritorna lo scope
# locale e non vede __compiled__ (bug storico, vedi EXERCISE_LIBRARY_STRATEGY.md §5.6).
_is_bundled = getattr(sys, "frozen", False) or "__compiled__" in globals()
if _is_bundled:
    PROJECT_ROOT = Path(sys.executable).resolve().parent.parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

# Carica .env dal progetto (sviluppo) + data/.env (produzione/bootstrap)
load_dotenv()  # .env nella root del progetto
load_dotenv(DATA_DIR / ".env", override=False)  # data/.env come fallback

# Database — Phase 1: SQLite. Phase 2: cambia solo questa riga.
# SQLite:     "sqlite:///data/crm.db"
# PostgreSQL: "postgresql://user:pass@localhost:5432/fitmanager"
def _resolve_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    return f"sqlite:///{DATA_DIR / 'crm.db'}"

DATABASE_URL: str = _resolve_database_url()

# Catalog Database — tassonomia scientifica (muscoli, articolazioni, condizioni, metriche)
# Shared tra prod e dev (stessi dati di riferimento), sempre in data/catalog.db.
# Se CATALOG_DATABASE_URL e' settato esplicitamente, ha priorita'.
CATALOG_DATABASE_URL: str = os.getenv(
    "CATALOG_DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'catalog.db'}",
)

# Nutrition Database — catalogo alimenti (CREA 2019 + USDA + custom)
# Shared tra prod e dev (stessa banca dati alimenti), sempre in data/nutrition.db.
# Se NUTRITION_DATABASE_URL e' settato esplicitamente, ha priorita'.
NUTRITION_DATABASE_URL: str = os.getenv(
    "NUTRITION_DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'nutrition.db'}",
)

# Encrypted catalog paths (used by database.py for frozen mode)
CATALOG_DB_ENC: Path = DATA_DIR / "catalog.db.enc"
NUTRITION_DB_ENC: Path = DATA_DIR / "nutrition.db.enc"


def is_compiled() -> bool:
    """Detect compiled binary (PyInstaller frozen OR Nuitka compiled).

    Unico helper autorevole: valuta il check una volta a livello di modulo
    (dove globals() vede __compiled__ di Nuitka). Tutti i componenti di
    enforcement e detection runtime DEVONO usare questa funzione, mai
    ripetere il check inline.
    """
    return _is_bundled


# Logging locale applicativo
LOG_DIR: Path = DATA_DIR / "logs"
APP_LOG_LEVEL: str = os.getenv("APP_LOG_LEVEL", "INFO").upper()
APP_LOG_MAX_BYTES: int = int(os.getenv("APP_LOG_MAX_BYTES", "1000000"))
APP_LOG_BACKUP_COUNT: int = int(os.getenv("APP_LOG_BACKUP_COUNT", "5"))

# JWT Authentication — bootstrap automatico al primo avvio
def _resolve_jwt_secret() -> str:
    """Risolve JWT_SECRET: env > data/.env > auto-genera e persiste."""
    import logging
    import secrets
    _logger = logging.getLogger("fitmanager.config")

    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        return secret

    # Auto-genera e persiste in data/.env
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    env_file = DATA_DIR / ".env"
    secret = secrets.token_hex(32)

    # Appendi senza sovrascrivere altre variabili gia' presenti
    with open(env_file, "a", encoding="utf-8") as f:
        f.write(f"\nJWT_SECRET={secret}\n")

    _logger.info(
        "JWT_SECRET generato automaticamente e salvato in %s", env_file
    )
    return secret


JWT_SECRET: str = _resolve_jwt_secret()
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))  # 8 ore

# API
API_PREFIX: str = "/api"
API_VERSION: str = "v1"
