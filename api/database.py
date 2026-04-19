# api/database.py
"""
Database layer con SQLModel (SQLAlchemy + Pydantic).

Architettura tri-database:
  - business engine (data.db / crm.db): dati trainer, clienti, contratti, workout
  - catalog engine (catalog.db): tassonomia scientifica (muscoli, articolazioni, condizioni, metriche)
  - nutrition engine (nutrition.db): catalogo alimenti CREA/USDA

In frozen mode (compiled binary), catalog e nutrition vengono decifrati da .db.enc
e caricati in memoria (AES-256-GCM). In dev mode, usano i file .db plain.
"""

import logging
import sqlite3 as sqlite3_stdlib
import sys
from pathlib import Path
from typing import Generator

from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from api.config import CATALOG_DATABASE_URL, DATA_DIR, DATABASE_URL, NUTRITION_DATABASE_URL
import api.models.share_token  # noqa: F401 — registra ShareToken nel metadata SQLModel
import api.models.nutrition  # noqa: F401 — registra modelli nutrition nel metadata SQLModel

logger = logging.getLogger("fitmanager.database")

# --- SQLite PRAGMA setup ---


def _setup_sqlite_pragmas(dbapi_conn, connection_record):
    """
    Configura PRAGMA SQLite per sicurezza e performance.

    - WAL: crash resistance, letture concorrenti
    - foreign_keys: integrita' referenziale enforced
    - busy_timeout: evita "database is locked" su accessi concorrenti
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def _load_encrypted_db(enc_path: Path, label: str):
    """Load an AES-256-GCM encrypted SQLite DB.

    Strategy 1: deserialize into in-memory DB (fastest, zero I/O).
    Strategy 2: write to temp file (fallback if bundled sqlite3 lacks deserialize).
    """
    from api.services.db_crypto import decrypt_db_to_bytes

    db_bytes = decrypt_db_to_bytes(enc_path)

    # Strategy 1: in-memory deserialize
    try:
        conn = sqlite3_stdlib.connect(":memory:")
        conn.deserialize(db_bytes)
        conn.execute("PRAGMA foreign_keys=ON")
        # Verify it actually works (deserialize can silently fail)
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1").fetchone()
        logger.info("Loaded encrypted %s (%d bytes) via deserialize", label, len(db_bytes))
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            creator=lambda: conn,
        )
    except Exception:
        pass

    # Strategy 2: temp file (bundled sqlite3 without SQLITE_ENABLE_DESERIALIZE)
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / f"{label}.db"
    tmp.write_bytes(db_bytes)
    db_url = f"sqlite:///{tmp}"
    logger.info("Loaded encrypted %s (%d bytes) via temp file: %s", label, len(db_bytes), tmp)
    eng = create_engine(
        db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    event.listen(eng, "connect", _setup_sqlite_pragmas)
    return eng


# --- Business Engine (data.db / crm.db) ---

_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=_connect_args,
)

if DATABASE_URL.startswith("sqlite"):
    event.listen(engine, "connect", _setup_sqlite_pragmas)

# --- Catalog Engine (catalog.db or catalog.db.enc) ---

_is_compiled = getattr(sys, "frozen", False) or "__compiled__" in dir()
_catalog_enc = DATA_DIR / "catalog.db.enc"
logger.info("Catalog DB init: compiled=%s, enc_exists=%s", _is_compiled, _catalog_enc.exists())

if _is_compiled and _catalog_enc.exists():
    catalog_engine = _load_encrypted_db(_catalog_enc, "catalog")
    _catalog_encrypted = True
else:
    _catalog_connect_args = {}
    if CATALOG_DATABASE_URL.startswith("sqlite"):
        _catalog_connect_args = {"check_same_thread": False}

    catalog_engine = create_engine(
        CATALOG_DATABASE_URL,
        echo=False,
        connect_args=_catalog_connect_args,
    )

    if CATALOG_DATABASE_URL.startswith("sqlite"):
        event.listen(catalog_engine, "connect", _setup_sqlite_pragmas)
    _catalog_encrypted = False
    logger.info("Catalog DB: file-based at %s", CATALOG_DATABASE_URL)

# --- Nutrition Engine (nutrition.db or nutrition.db.enc) ---

_nutrition_enc = DATA_DIR / "nutrition.db.enc"
if (getattr(sys, "frozen", False) or "__compiled__" in dir()) and _nutrition_enc.exists():
    nutrition_engine = _load_encrypted_db(_nutrition_enc, "nutrition")
    _nutrition_encrypted = True
else:
    _nutrition_connect_args = {}
    if NUTRITION_DATABASE_URL.startswith("sqlite"):
        _nutrition_connect_args = {"check_same_thread": False}

    nutrition_engine = create_engine(
        NUTRITION_DATABASE_URL,
        echo=False,
        connect_args=_nutrition_connect_args,
    )

    if NUTRITION_DATABASE_URL.startswith("sqlite"):
        event.listen(nutrition_engine, "connect", _setup_sqlite_pragmas)
    _nutrition_encrypted = False


def is_catalog_encrypted() -> bool:
    return _catalog_encrypted


def is_nutrition_encrypted() -> bool:
    return _nutrition_encrypted


# --- Table creation ---

# Tabelle catalog (catalogo scientifico esercizi + tassonomia)
# Queste tabelle vivono in catalog.db (read-only, shipped con installer).
# Pattern identico a nutrition.db: catalogo separato, cross-DB ref da crm.db.
CATALOG_TABLE_NAMES = frozenset({
    # Esercizi builtin + relazioni
    "esercizi",
    "esercizi_relazioni",
    "esercizi_media",
    # Tassonomia scientifica
    "muscoli",
    "esercizi_muscoli",
    "articolazioni",
    "esercizi_articolazioni",
    "condizioni_mediche",
    "esercizi_condizioni",
    "metriche",
})

# Tabelle nutrition (catalogo alimenti CREA/USDA)
NUTRITION_TABLE_NAMES = frozenset({
    "categorie_alimenti",
    "alimenti",
    "porzioni_standard",
    "ricette_pietanze",
    "plan_templates",
    "template_plan_meals",
    "template_plan_components",
})


def create_db_and_tables() -> None:
    """
    Crea le tabelle BUSINESS nel database principale (crm.db).

    ESCLUDE tabelle catalog e nutrition (vivono nei rispettivi DB).
    Usa CREATE TABLE IF NOT EXISTS: sicuro da chiamare piu' volte.
    NON sovrascrive tabelle esistenti, NON aggiunge colonne mancanti
    (per quello servono migrazioni esplicite).
    """
    _excluded = CATALOG_TABLE_NAMES | NUTRITION_TABLE_NAMES
    business_tables = [
        t for t in SQLModel.metadata.sorted_tables
        if t.name not in _excluded
    ]
    SQLModel.metadata.create_all(engine, tables=business_tables)


def create_catalog_tables() -> None:
    """
    Crea le tabelle CATALOG nel database tassonomico (catalog.db).

    Usato da build_catalog.py per creare catalog.db da zero.
    In produzione, catalog.db viene shippato pre-costruito.
    Skipped if loaded from encrypted in-memory DB (tables already present).
    """
    if _catalog_encrypted:
        return
    tables = [
        t for t in SQLModel.metadata.sorted_tables
        if t.name in CATALOG_TABLE_NAMES
    ]
    SQLModel.metadata.create_all(catalog_engine, tables=tables)


def create_nutrition_tables() -> None:
    """
    Crea le tabelle NUTRITION nel database alimenti (nutrition.db).

    Usato da build_nutrition.py per creare nutrition.db da zero.
    In produzione, nutrition.db viene shippato pre-costruito con dati CREA 2019.
    Skipped if loaded from encrypted in-memory DB (tables already present).
    """
    if _nutrition_encrypted:
        return
    tables = [
        t for t in SQLModel.metadata.sorted_tables
        if t.name in NUTRITION_TABLE_NAMES
    ]
    SQLModel.metadata.create_all(nutrition_engine, tables=tables)


# --- Session factories ---


def get_session() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI: session BUSINESS (data.db).

    Usata dalla maggior parte degli endpoint (clienti, contratti, agenda, etc.).
    """
    with Session(engine) as session:
        yield session


def get_catalog_session() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI: session CATALOG (catalog.db).

    Usata dagli endpoint che leggono tassonomia scientifica:
    - Dettaglio esercizio (muscoli, articolazioni)
    - Safety map (condizioni mediche)
    - Metriche (misurazioni, obiettivi)
    """
    with Session(catalog_engine) as session:
        yield session


def get_nutrition_session() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI: session NUTRITION (nutrition.db).

    Usata dagli endpoint che leggono il catalogo alimenti:
    - Ricerca alimenti (nome, categoria)
    - Dettaglio alimento con macro per 100g
    - Porzioni standard
    - Calcolo macro componenti pasto (cross-DB lookup)
    """
    with Session(nutrition_engine) as session:
        yield session
