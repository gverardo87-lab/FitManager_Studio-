"""
Schema Sync — aggiunge colonne mancanti al DB dopo upgrade o restore.

Confronta i modelli ORM (SQLModel.metadata) con lo schema reale del DB
ed esegue ALTER TABLE ADD COLUMN per le colonne mancanti.

Garanzie:
- Solo ADD, mai DROP/MODIFY
- Idempotente (safe da chiamare a ogni startup)
- Funziona in PyInstaller (zero dipendenze Alembic)
- Solo crm.db (business), mai catalog.db o nutrition.db
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

from api.database import CATALOG_TABLE_NAMES, NUTRITION_TABLE_NAMES

logger = logging.getLogger("fitmanager.schema_sync")

# Tabelle gestite da altri DB — non toccare
_EXCLUDED_TABLE_NAMES = CATALOG_TABLE_NAMES | NUTRITION_TABLE_NAMES


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

    Ritorna lista di messaggi con le modifiche effettuate.
    Solo crm.db (business tables), mai catalog/nutrition.
    """
    messages: list[str] = []

    # Fix legacy cross-DB FK constraints (idempotente)
    messages.extend(_fix_cross_db_fk(db_engine))

    tables_checked = 0
    columns_added = 0

    with db_engine.connect() as connection:
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
