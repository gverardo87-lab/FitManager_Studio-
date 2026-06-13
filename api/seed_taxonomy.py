# api/seed_taxonomy.py
"""
Seed tassonomia scientifica al startup — safety net per catalog.db vuoto.

Protegge lo sviluppo: se catalog.db viene ricreato durante audit/rebuild,
il startup ripopola automaticamente le 6 tabelle tassonomiche.

In compiled mode (Nuitka/PyInstaller): skip — catalog.db e' shipped
pre-costruito dall'installer e tools/ non e' nel bundle (ADR-007).
Per il prodotto installato, la protezione e' consegnare un catalog.db completo.

Ordine critico (le junction dipendono dalle tabelle base):
  1. seed_taxonomy.seed_db     → muscoli, articolazioni, condizioni_mediche
  2. populate_taxonomy.populate_db → esercizi_muscoli, esercizi_articolazioni
  3. populate_conditions.process_db → esercizi_condizioni
"""

import logging
import sqlite3
from pathlib import Path

from api.config import is_compiled


logger = logging.getLogger("fitmanager.api")

# Tabelle tassonomiche che devono essere popolate
_TAXONOMY_TABLES = (
    "muscoli", "articolazioni", "condizioni_mediche",
    "esercizi_muscoli", "esercizi_articolazioni", "esercizi_condizioni",
)


def _get_counts(db_path: str) -> dict[str, int]:
    """Conta righe per ogni tabella tassonomica. Ritorna {} se tabelle mancanti."""
    conn = sqlite3.connect(db_path)
    counts = {}
    try:
        for table in _TAXONOMY_TABLES:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608
    except sqlite3.OperationalError:
        # Tabelle non ancora create
        counts = {}
    finally:
        conn.close()
    return counts


def seed_taxonomy_all(catalog_db_path: str) -> None:
    """Seed tassonomia completa se tabelle vuote.

    Skip in compiled mode (catalog.db pre-costruito, tools/ non nel bundle).
    Attivo solo in sviluppo: invoca i 3 populate script in ordine.
    """
    if is_compiled():
        logger.info("Seed tassonomia: skip in compiled mode (catalog.db pre-costruito)")
        return

    if not catalog_db_path or not Path(catalog_db_path).exists():
        return

    counts = _get_counts(catalog_db_path)
    if not counts:
        logger.warning("Seed tassonomia: tabelle non trovate, skip")
        return

    # Se tutto gia' popolato, skip
    if all(counts[t] > 0 for t in _TAXONOMY_TABLES):
        logger.info(
            f"Seed tassonomia: gia' popolata "
            f"(muscoli={counts['muscoli']}, articolazioni={counts['articolazioni']}, "
            f"condizioni={counts['condizioni_mediche']}, "
            f"em={counts['esercizi_muscoli']}, ea={counts['esercizi_articolazioni']}, "
            f"ec={counts['esercizi_condizioni']}), skip"
        )
        return

    # Step 1: Base taxonomy (muscoli, articolazioni, condizioni_mediche)
    if counts["muscoli"] == 0 or counts["articolazioni"] == 0 or counts["condizioni_mediche"] == 0:
        logger.info("Seed tassonomia: popolo muscoli, articolazioni, condizioni_mediche...")
        from tools.admin_scripts.seed_taxonomy import seed_db
        seed_db(catalog_db_path)

    # Step 2: Junction muscoli + articolazioni
    if counts["esercizi_muscoli"] == 0 or counts["esercizi_articolazioni"] == 0:
        logger.info("Seed tassonomia: popolo esercizi_muscoli + esercizi_articolazioni...")
        from tools.admin_scripts.populate_taxonomy import populate_db
        populate_db(catalog_db_path)

    # Step 3: Junction condizioni
    if counts["esercizi_condizioni"] == 0:
        logger.info("Seed tassonomia: popolo esercizi_condizioni...")
        from tools.admin_scripts.populate_conditions import process_db
        process_db(catalog_db_path)

    # Verification
    final = _get_counts(catalog_db_path)
    empty = [t for t in _TAXONOMY_TABLES if final.get(t, 0) == 0]
    if empty:
        logger.error(f"Seed tassonomia: tabelle ancora vuote dopo seed: {empty}")
    else:
        logger.info(
            f"Seed tassonomia completata: "
            f"muscoli={final['muscoli']}, articolazioni={final['articolazioni']}, "
            f"condizioni={final['condizioni_mediche']}, "
            f"em={final['esercizi_muscoli']}, ea={final['esercizi_articolazioni']}, "
            f"ec={final['esercizi_condizioni']}"
        )
