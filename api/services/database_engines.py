"""Primitive condivise per costruire gli engine SQLite non-business."""

import logging
import sqlite3 as sqlite3_stdlib
import tempfile
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine


logger = logging.getLogger("fitmanager.database")


def setup_sqlite_pragmas(dbapi_conn, connection_record) -> None:
    """Configura WAL, foreign key e busy timeout sulle connessioni SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def load_encrypted_db(enc_path: Path, label: str):
    """Carica un catalogo SQLite AES-GCM in memoria o su file temporaneo."""
    from api.services.db_crypto import decrypt_db_to_bytes

    db_bytes = decrypt_db_to_bytes(enc_path)
    try:
        conn = sqlite3_stdlib.connect(":memory:")
        conn.deserialize(db_bytes)
        conn.execute("PRAGMA foreign_keys=ON")
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

    tmp = Path(tempfile.mkdtemp()) / f"{label}.db"
    tmp.write_bytes(db_bytes)
    logger.info("Loaded encrypted %s (%d bytes) via temp file: %s", label, len(db_bytes), tmp)
    engine = create_engine(
        f"sqlite:///{tmp}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    event.listen(engine, "connect", setup_sqlite_pragmas)
    return engine
