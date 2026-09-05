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
from typing import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, create_engine

from api.config import (
    CATALOG_DATABASE_URL,
    DATA_DIR,
    DATABASE_URL,
    NUTRITION_DATABASE_URL,
    is_compiled,
)
import api.models.share_token  # noqa: F401 — registra ShareToken nel metadata SQLModel
import api.models.nutrition  # noqa: F401 — registra modelli nutrition nel metadata SQLModel
import api.models.rettifica_contratto  # noqa: F401 — registra RettificaContratto nel metadata SQLModel (G9.2b)
from api.services.business_database import (
    BUSINESS_DATABASE_UNAVAILABLE_DETAIL,
    BusinessDatabaseController,
    BusinessDatabaseState,
    BusinessDatabaseStorageMode,
    BusinessDatabaseUnavailableError,
)
from api.services.database_engines import (
    load_encrypted_db as _load_encrypted_db,
    setup_sqlite_pragmas as _setup_sqlite_pragmas,
)

logger = logging.getLogger("fitmanager.database")

# --- Business Engine (data.db / crm.db) — late-bound ---

business_db_controller = BusinessDatabaseController(
    BusinessDatabaseState.LOCKED if is_compiled() else BusinessDatabaseState.UNINITIALIZED,
    allow_plaintext_development=not is_compiled(),
)


def _create_plaintext_business_engine(database_url: str) -> Engine:
    """Crea l'engine plaintext ammesso esclusivamente nel runtime source/dev."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    candidate = create_engine(database_url, echo=False, connect_args=connect_args)
    if database_url.startswith("sqlite"):
        event.listen(candidate, "connect", _setup_sqlite_pragmas)
    return candidate


def initialize_development_business_database() -> Engine:
    """Inizializza esplicitamente il CRM plaintext; vietato in compiled mode."""
    if is_compiled():
        raise BusinessDatabaseUnavailableError(
            BUSINESS_DATABASE_UNAVAILABLE_DETAIL
        ) from None
    return business_db_controller.initialize_plaintext_development_engine(
        lambda: _create_plaintext_business_engine(DATABASE_URL)
    )


def get_business_engine() -> Engine:
    """Accessor fail-closed dell'engine CRM pubblicato."""
    return business_db_controller.require_engine()


def get_business_database_state() -> BusinessDatabaseState:
    return business_db_controller.state


def get_business_database_storage_mode() -> BusinessDatabaseStorageMode | None:
    return business_db_controller.storage_mode

# --- Catalog Engine (catalog.db or catalog.db.enc) ---

_is_compiled = is_compiled()
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
if _is_compiled and _nutrition_enc.exists():
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


def create_db_and_tables(target_engine: Engine | None = None) -> None:
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
    selected_engine = target_engine if target_engine is not None else get_business_engine()
    SQLModel.metadata.create_all(selected_engine, tables=business_tables)


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
    with business_db_controller.session() as session:
        yield session


def get_optional_business_session() -> Generator[Session | None, None, None]:
    """Dependency health-only: non apre né sblocca il CRM quando è sigillato."""
    try:
        target_engine = get_business_engine()
    except BusinessDatabaseUnavailableError:
        yield None
        return
    with Session(target_engine) as session:
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
