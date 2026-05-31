"""
Test Upgrade End-to-End — verifica che schema_sync gestisca upgrade DB correttamente.

Simula il percorso di un partner (es. Alessio v1.0.7) che aggiorna alla versione corrente.
Non richiede server avviato — lavora direttamente sul DB.

Uso:
    python -m tools.admin_scripts.test_upgrade
    python -m tools.admin_scripts.test_upgrade --from-version 1.0.7
    python -m tools.admin_scripts.test_upgrade --db-path data/crm.db
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def _get_tables_and_columns(db_path: str) -> dict[str, list[str]]:
    """Ritorna {table_name: [col1, col2, ...]} per tutte le tabelle."""
    conn = sqlite3.connect(db_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    result = {}
    for t in tables:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info([{t}])").fetchall()]
        result[t] = cols
    conn.close()
    return result


def _get_version(db_path: str) -> str | None:
    """Legge la versione dal DB. None se tabella non esiste."""
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT version FROM _schema_version WHERE id = 1").fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def _get_row_counts(db_path: str) -> dict[str, int]:
    """Ritorna {table_name: row_count} per tabelle business."""
    conn = sqlite3.connect(db_path)
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '\\_%' ESCAPE '\\' ORDER BY name"
    ).fetchall()]
    result = {}
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        result[t] = count
    conn.close()
    return result


def _downgrade_db(db_path: str, to_version: str) -> None:
    """Degrada il DB rimuovendo _schema_version (simula DB pre-tracking)."""
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS _schema_version")
    conn.commit()
    conn.close()


def _run_sync(db_path: str) -> list[str]:
    """Esegue sync_schema sul DB e ritorna i messaggi."""
    from sqlalchemy import create_engine

    from api.services.schema_sync import sync_schema

    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    messages = sync_schema(engine)
    engine.dispose()
    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description="Test upgrade end-to-end")
    parser.add_argument(
        "--db-path", default=str(ROOT / "data" / "crm.db"),
        help="Path al DB sorgente da usare come base (default: data/crm.db)",
    )
    parser.add_argument(
        "--from-version", default="1.0.7",
        help="Versione da simulare come partenza (default: 1.0.7)",
    )
    args = parser.parse_args()

    source_db = Path(args.db_path)
    if not source_db.exists():
        print(f"FAIL: DB sorgente non trovato: {source_db}")
        sys.exit(1)

    from api import __version__ as app_version

    print(f"=== Test Upgrade: v{args.from_version} -> v{app_version} ===")
    print(f"DB sorgente: {source_db} ({source_db.stat().st_size:,} bytes)")
    print()

    # ── 1. Copia DB in temp ──
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "crm_upgrade_test.db"
        shutil.copy2(source_db, test_db)
        print(f"[1/6] Copia DB in {test_db}")

        # ── 2. Snapshot pre-upgrade ──
        pre_tables = _get_tables_and_columns(str(test_db))
        pre_counts = _get_row_counts(str(test_db))
        pre_version = _get_version(str(test_db))
        print(f"[2/6] Snapshot pre-upgrade: {len(pre_tables)} tabelle, versione={pre_version}")

        # ── 3. Downgrade (simula DB vecchio) ──
        _downgrade_db(str(test_db), args.from_version)
        downgraded_version = _get_version(str(test_db))
        print(f"[3/6] Downgrade a v{args.from_version}: _schema_version={downgraded_version}")

        # ── 4. Esegui sync_schema ──
        print(f"[4/6] Esecuzione sync_schema...")
        messages = _run_sync(str(test_db))
        if messages:
            for msg in messages:
                print(f"       {msg}")
        else:
            print("       (nessuna modifica schema)")

        # ── 5. Verifica post-upgrade ──
        print(f"[5/6] Verifica post-upgrade:")
        errors = []

        # 5a. Versione registrata
        post_version = _get_version(str(test_db))
        if post_version == app_version:
            print(f"       OK  versione DB = {post_version}")
        else:
            errors.append(f"versione DB = {post_version}, atteso {app_version}")
            print(f"       FAIL  versione DB = {post_version}, atteso {app_version}")

        # 5b. Tabelle e colonne
        post_tables = _get_tables_and_columns(str(test_db))
        for table_name, expected_cols in post_tables.items():
            if table_name.startswith("_"):
                continue
            pre_cols = pre_tables.get(table_name, [])
            new_cols = set(expected_cols) - set(pre_cols)
            if new_cols:
                print(f"       INFO  {table_name}: +{len(new_cols)} colonne ({', '.join(sorted(new_cols))})")

        # 5c. Dati preservati
        post_counts = _get_row_counts(str(test_db))
        data_ok = True
        for table_name, pre_count in pre_counts.items():
            post_count = post_counts.get(table_name, 0)
            if post_count != pre_count:
                errors.append(f"{table_name}: {pre_count} righe -> {post_count} (dati persi!)")
                print(f"       FAIL  {table_name}: {pre_count} -> {post_count} righe")
                data_ok = False
        if data_ok:
            total_rows = sum(pre_counts.values())
            print(f"       OK  dati preservati ({total_rows} righe totali, {len(pre_counts)} tabelle)")

        # 5d. Integrity check
        conn = sqlite3.connect(str(test_db))
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        if integrity == "ok":
            print(f"       OK  PRAGMA integrity_check = ok")
        else:
            errors.append(f"integrity_check = {integrity}")
            print(f"       FAIL  integrity_check = {integrity}")

        # ── 6. Risultato ──
        print()
        if errors:
            print(f"[6/6] FAIL — {len(errors)} errori:")
            for e in errors:
                print(f"       - {e}")
            sys.exit(1)
        else:
            print(f"[6/6] PASS — upgrade v{args.from_version} -> v{app_version} completato con successo")


if __name__ == "__main__":
    main()
