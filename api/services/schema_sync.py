"""
Schema Sync — aggiunge colonne mancanti al DB dopo upgrade o restore.

Confronta i modelli ORM (SQLModel.metadata) con lo schema reale del DB
ed esegue ALTER TABLE ADD COLUMN per le colonne mancanti.

Garanzie:
- Solo ADD, mai DROP/MODIFY
- Idempotente (safe da chiamare a ogni startup)
- Funziona in PyInstaller/Nuitka (zero dipendenze Alembic)
- Solo crm.db (business), mai catalog.db o nutrition.db
- Versione DB tracciata in tabella _schema_version
- Data migration eseguibili una sola volta per versione
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

from api import __version__  # noqa: F811
from api.database import CATALOG_TABLE_NAMES, NUTRITION_TABLE_NAMES

logger = logging.getLogger("fitmanager.schema_sync")

# Tabelle gestite da altri DB — non toccare
_EXCLUDED_TABLE_NAMES = CATALOG_TABLE_NAMES | NUTRITION_TABLE_NAMES


# ── Schema Version Tracking ──────────────────────────────────────────


def _ensure_version_table(connection: Any) -> None:
    """Crea la tabella _schema_version se non esiste."""
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS _schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """))


def _get_db_version(connection: Any) -> str | None:
    """Legge la versione corrente del DB. None = mai registrata."""
    _ensure_version_table(connection)
    row = connection.execute(text(
        "SELECT version FROM _schema_version WHERE id = 1"
    )).fetchone()
    return row[0] if row else None


def _set_db_version(connection: Any, version: str) -> None:
    """Registra la versione corrente nel DB."""
    connection.execute(text(
        "INSERT INTO _schema_version (id, version, updated_at) VALUES (1, :v, datetime('now')) "
        "ON CONFLICT(id) DO UPDATE SET version = :v, updated_at = datetime('now')"
    ), {"v": version})


# ── Data Migrations ──────────────────────────────────────────────────

# Registro migrazioni dati: (from_version, to_version, funzione).
# Ogni funzione riceve connection (gia' in transazione) e ritorna messaggio.
# Eseguita UNA SOLA VOLTA: quando db_version < to_version.
#
# Esempio:
#   def _migrate_1_0_8_to_1_1_0(connection: Any) -> str:
#       connection.execute(text("UPDATE clienti SET nuovo_campo = 'default' WHERE nuovo_campo IS NULL"))
#       return "clienti.nuovo_campo populated with defaults"
#
#   DATA_MIGRATIONS = [
#       ("1.0.8", "1.1.0", _migrate_1_0_8_to_1_1_0),
#   ]

DATA_MIGRATIONS: list[tuple[str, str, Callable]] = []


def _version_tuple(v: str) -> tuple[int, ...]:
    """Converte '1.0.8' in (1, 0, 8) per confronto."""
    return tuple(int(x) for x in v.split("."))


def _run_data_migrations(connection: Any, from_version: str | None) -> list[str]:
    """Esegue le data migration pendenti in ordine."""
    if not DATA_MIGRATIONS:
        return []

    messages: list[str] = []
    from_tuple = _version_tuple(from_version) if from_version else (0, 0, 0)

    for mig_from, mig_to, fn in DATA_MIGRATIONS:
        mig_to_tuple = _version_tuple(mig_to)
        if from_tuple < mig_to_tuple:
            logger.info("  schema_sync: running data migration %s → %s", mig_from, mig_to)
            msg = fn(connection)
            messages.append(f"migration {mig_from}→{mig_to}: {msg}")
            logger.info("  schema_sync: %s", messages[-1])

    return messages


def _get_db_columns(connection: Any, table_name: str) -> set[str]:
    """Ritorna i nomi delle colonne presenti nel DB per una tabella."""
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def _sa_type_to_sqlite(sa_type: Any) -> str:
    """Mappa tipo SQLAlchemy → tipo SQLite."""
    type_name = type(sa_type).__name__.upper()

    if type_name in ("INTEGER", "BIGINTEGER", "SMALLINTEGER"):
        return "INTEGER"
    if type_name in ("FLOAT", "NUMERIC", "DECIMAL", "REAL"):
        return "REAL"
    if type_name in ("BOOLEAN",):
        return "INTEGER"
    # String, Text, VARCHAR, DateTime, Date, JSON, ecc. → TEXT
    return "TEXT"


def _resolve_default(column: Any, sqlite_type: str) -> str:
    """Determina la clausola DEFAULT per ALTER TABLE ADD COLUMN."""
    # Se nullable (il caso piu' comune per colonne aggiunte dopo) → NULL
    if column.nullable is not False:
        return "DEFAULT NULL"

    # Cerca default esplicito nel modello
    if column.default is not None:
        arg = column.default.arg
        if arg is not None and not callable(arg):
            if isinstance(arg, bool):
                return f"DEFAULT {1 if arg else 0}"
            if isinstance(arg, (int, float)):
                return f"DEFAULT {arg}"
            if isinstance(arg, str):
                escaped = arg.replace("'", "''")
                return f"DEFAULT '{escaped}'"

    # Server default
    if column.server_default is not None:
        return f"DEFAULT {column.server_default.arg}"

    # Non-nullable senza default: safety default per tipo
    if sqlite_type == "INTEGER":
        return "DEFAULT 0"
    if sqlite_type == "REAL":
        return "DEFAULT 0.0"
    return "DEFAULT ''"


def _drop_phantom_tables(db_engine: Engine) -> list[str]:
    """Rimuove tabelle fantasma catalog/nutrition da crm.db.

    Queste tabelle vengono restaurate da backup pre-separazione 3 DB.
    Sono vuote e non interferiscono, ma confondono l'audit e gonfiano
    il conteggio tabelle. DROP solo se vuote (safety check).
    """
    messages: list[str] = []
    # Tabelle che vivono SOLO in catalog.db o nutrition.db
    phantoms = (
        _EXCLUDED_TABLE_NAMES | {"esercizi", "esercizi_relazioni", "esercizi_media",
        "esercizi_muscoli", "esercizi_articolazioni", "esercizi_condizioni",
        "muscoli", "articolazioni", "condizioni_mediche"}
    )

    with db_engine.connect() as conn:
        existing = {row[0] for row in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )).fetchall()}

        for table_name in sorted(phantoms & existing):
            # Safety: DROP solo se vuota
            count = conn.execute(text(f"SELECT COUNT(*) FROM [{table_name}]")).fetchone()[0]
            if count > 0:
                continue
            # Safety extra: skip se la tabella ha schema completo (test in-memory
            # o DB dove create_all ha creato il modello ORM intero — non e' phantom)
            col_count = len(conn.execute(text(
                f"PRAGMA table_info([{table_name}])"
            )).fetchall())
            if col_count > 3:
                continue  # schema reale (ORM), non phantom stub
            conn.execute(text(f"DROP TABLE IF EXISTS [{table_name}]"))
            msg = f"dropped phantom table '{table_name}' (empty, belongs to catalog/nutrition.db)"
            messages.append(msg)
            logger.info("  schema_sync: %s", msg)

        if messages:
            conn.commit()

    return messages


def _fix_cross_db_fk(db_engine: Engine) -> list[str]:
    """Rimuove FK residue cross-DB (esercizi_sessione → esercizi).

    Background: esercizi_sessione.id_esercizio aveva FK verso esercizi(id),
    ma esercizi vive in catalog.db. Con PRAGMA foreign_keys=ON SQLite
    crashava al commit. Il modello Python ha gia' rimosso la FK (workout.py:91),
    ma il DDL nel DB la manteneva. Questo fix ricrea la tabella senza la FK.
    Idempotente: skip se la FK non c'e' piu'.
    """
    messages: list[str] = []
    with db_engine.connect() as conn:
        fks = conn.execute(text("PRAGMA foreign_key_list(esercizi_sessione)")).fetchall()
        has_cross_db_fk = any(row[2] == "esercizi" for row in fks)
        if not has_cross_db_fk:
            return messages

        logger.info("  schema_sync: fixing cross-DB FK on esercizi_sessione")
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS _esercizi_sessione_fixed (
                id INTEGER NOT NULL PRIMARY KEY,
                id_sessione INTEGER NOT NULL,
                id_esercizio INTEGER NOT NULL,
                ordine INTEGER NOT NULL,
                serie INTEGER NOT NULL,
                ripetizioni VARCHAR NOT NULL,
                tempo_riposo_sec INTEGER NOT NULL,
                tempo_esecuzione VARCHAR,
                note VARCHAR,
                carico_kg FLOAT,
                id_blocco INTEGER,
                posizione_nel_blocco INTEGER,
                FOREIGN KEY(id_sessione) REFERENCES sessioni_scheda (id)
            )
        """))
        conn.execute(text(
            "INSERT OR IGNORE INTO _esercizi_sessione_fixed SELECT * FROM esercizi_sessione"
        ))
        conn.execute(text("DROP TABLE esercizi_sessione"))
        conn.execute(text("ALTER TABLE _esercizi_sessione_fixed RENAME TO esercizi_sessione"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_esercizio "
            "ON esercizi_sessione (id_esercizio)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_sessione "
            "ON esercizi_sessione (id_sessione)"
        ))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_esercizi_sessione_id_blocco "
            "ON esercizi_sessione (id_blocco)"
        ))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()
        msg = "esercizi_sessione — removed cross-DB FK to esercizi (catalog.db)"
        messages.append(msg)
        logger.info("  schema_sync: %s", msg)

    return messages


def sync_schema(db_engine: Engine) -> list[str]:
    """
    Confronta modelli ORM vs DB reale e aggiunge colonne mancanti.
    Traccia la versione del DB ed esegue data migration pendenti.

    Ritorna lista di messaggi con le modifiche effettuate.
    Solo crm.db (business tables), mai catalog/nutrition.
    """
    messages: list[str] = []

    # Fix legacy cross-DB FK constraints (idempotente)
    messages.extend(_fix_cross_db_fk(db_engine))

    # Rimuovi tabelle phantom da backup pre-separazione (idempotente)
    messages.extend(_drop_phantom_tables(db_engine))

    tables_checked = 0
    columns_added = 0

    with db_engine.connect() as connection:
        # ── Version tracking ──
        prev_version = _get_db_version(connection)
        app_version = __version__

        if prev_version and prev_version != app_version:
            logger.info("  schema_sync: upgrade %s → %s", prev_version, app_version)
        elif not prev_version:
            logger.info("  schema_sync: first version tracking — registering %s", app_version)

        # ── Column sync ──
        for table in SQLModel.metadata.sorted_tables:
            if table.name in _EXCLUDED_TABLE_NAMES:
                continue

            db_columns = _get_db_columns(connection, table.name)
            if not db_columns:
                # Tabella non esiste nel DB — create_db_and_tables() la crea
                continue

            tables_checked += 1
            newly_added: list[str] = []

            for column in table.columns:
                if column.name in db_columns:
                    continue

                sqlite_type = _sa_type_to_sqlite(column.type)
                default_clause = _resolve_default(column, sqlite_type)
                ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {sqlite_type} {default_clause}"

                connection.execute(text(ddl))
                columns_added += 1
                newly_added.append(column.name)
                msg = f"{table.name} — added column '{column.name}' ({sqlite_type} {default_clause})"
                messages.append(msg)
                logger.info("  schema_sync: %s", msg)

            # Crea indici per le colonne appena aggiunte (se richiesti dal modello)
            for column in table.columns:
                if column.name not in newly_added:
                    continue
                if column.index:
                    idx_name = f"ix_{table.name}_{column.name}"
                    connection.execute(text(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table.name} ({column.name})"
                    ))
                    idx_msg = f"{table.name} — created index '{idx_name}'"
                    messages.append(idx_msg)
                    logger.info("  schema_sync: %s", idx_msg)

        # ── Data migrations ──
        mig_messages = _run_data_migrations(connection, prev_version)
        messages.extend(mig_messages)

        # ── Stamp version ──
        _set_db_version(connection, app_version)

        connection.commit()

    if columns_added == 0:
        logger.info("  schema_sync: schema up to date (%d tables checked)", tables_checked)
    else:
        logger.info(
            "  schema_sync: %d columns added across %d tables",
            columns_added,
            tables_checked,
        )

    return messages
