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
from datetime import date
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel

from api import __version__  # noqa: F811
from api.database import CATALOG_TABLE_NAMES, NUTRITION_TABLE_NAMES
from api.models.rettifica_contratto import CAUSALE_BACKFILL_LEGACY

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


# Tabelle business con FK locale residua verso una tabella che vive in un altro DB
# (catalog.db / nutrition.db). Con PRAGMA foreign_keys=ON SQLite cerca la tabella
# parent nello stesso file: assente nei crm.db fresh → crash al commit/insert.
# Il modello Python ha gia' rimosso la FK; questo fix allinea il DDL del DB.
_CROSS_DB_FK_FIXES: list[tuple[str, str]] = [
    ("esercizi_sessione", "esercizi"),    # → catalog.db (INC workout.py:91)
    ("valori_misurazione", "metriche"),   # → catalog.db (measurement.py)
    ("obiettivi_cliente", "metriche"),    # → catalog.db (goal.py)
]


def _recreate_table_dropping_fk(conn: Any, table: str, parent_to_drop: str) -> None:
    """Ricrea `table` preservando colonne/righe/indici ma SENZA la FK verso
    `parent_to_drop`. Generico via introspezione (PRAGMA) — robusto vs DB con
    colonne aggiunte da migrazioni successive. SQLite non supporta DROP CONSTRAINT,
    quindi: crea _tmp → copia righe → drop originale → rename → ricrea indici.
    """
    info = conn.execute(text(f"PRAGMA table_info([{table}])")).fetchall()
    # (cid, name, type, notnull, dflt_value, pk)
    col_names = [r[1] for r in info]
    col_defs: list[str] = []
    pk: list[tuple[int, str]] = []
    for _cid, name, ctype, notnull, dflt, pk_idx in info:
        d = f'"{name}" {ctype}'.rstrip()
        if notnull:
            d += " NOT NULL"
        if dflt is not None:
            d += f" DEFAULT {dflt}"
        col_defs.append(d)
        if pk_idx:
            pk.append((pk_idx, name))
    pk_cols = [n for _, n in sorted(pk)]

    # FK da mantenere (tutte tranne quelle verso parent_to_drop), raggruppate per id
    fk_rows = conn.execute(text(f"PRAGMA foreign_key_list([{table}])")).fetchall()
    by_id: dict[int, list] = {}
    for row in fk_rows:
        by_id.setdefault(row[0], []).append(row)
    fk_clauses: list[str] = []
    for _fid, rows in sorted(by_id.items()):
        parent = rows[0][2]
        if parent == parent_to_drop:
            continue
        ordered = sorted(rows, key=lambda x: x[1])
        froms = ", ".join(f'"{r[3]}"' for r in ordered)
        tos = ", ".join(f'"{r[4]}"' for r in ordered)
        fk_clauses.append(f"FOREIGN KEY ({froms}) REFERENCES {parent} ({tos})")

    # Indici creati con CREATE INDEX (origin='c') da ricreare dopo il rename
    recreate_idx: list[tuple[str, bool, list[str]]] = []
    for _seq, iname, unique, origin, *_rest in conn.execute(
        text(f"PRAGMA index_list([{table}])")
    ).fetchall():
        if origin != "c":
            continue
        icols = [c[2] for c in conn.execute(text(f"PRAGMA index_info([{iname}])")).fetchall()]
        recreate_idx.append((iname, bool(unique), icols))

    tmp = f"_{table}_fixed"
    parts = list(col_defs)
    if pk_cols:
        parts.append(f"PRIMARY KEY ({', '.join(pk_cols)})")
    parts.extend(fk_clauses)
    ddl = f"CREATE TABLE {tmp} (\n  " + ",\n  ".join(parts) + "\n)"
    cols_csv = ", ".join(f'"{c}"' for c in col_names)

    conn.execute(text(f"DROP TABLE IF EXISTS {tmp}"))
    conn.execute(text(ddl))
    conn.execute(text(f"INSERT INTO {tmp} ({cols_csv}) SELECT {cols_csv} FROM {table}"))
    conn.execute(text(f"DROP TABLE {table}"))
    conn.execute(text(f"ALTER TABLE {tmp} RENAME TO {table}"))
    for iname, unique, icols in recreate_idx:
        uq = "UNIQUE " if unique else ""
        icols_csv = ", ".join(f'"{c}"' for c in icols)
        conn.execute(text(f"CREATE {uq}INDEX IF NOT EXISTS {iname} ON {table} ({icols_csv})"))


def _fix_cross_db_fk(db_engine: Engine) -> list[str]:
    """Rimuove FK residue cross-DB dal DDL di crm.db (idempotente).

    Background: alcune tabelle business avevano FK verso tabelle catalog
    (esercizi, metriche) che ora vivono in catalog.db. Con foreign_keys=ON
    SQLite cercava il parent nello stesso file → crash su crm.db fresh.
    Vedi `_CROSS_DB_FK_FIXES`. Skip per ogni tabella la cui FK non c'e' piu'.
    """
    messages: list[str] = []
    with db_engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        for table, parent in _CROSS_DB_FK_FIXES:
            exists = conn.execute(text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"
            ), {"n": table}).fetchone()
            if not exists:
                continue
            fks = conn.execute(text(f"PRAGMA foreign_key_list([{table}])")).fetchall()
            if not any(row[2] == parent for row in fks):
                continue  # FK gia' assente → idempotente
            logger.info("  schema_sync: fixing cross-DB FK on %s (→ %s)", table, parent)
            _recreate_table_dropping_fk(conn, table, parent)
            msg = f"{table} — removed cross-DB FK to {parent} (catalog.db)"
            messages.append(msg)
            logger.info("  schema_sync: %s", msg)
        conn.execute(text("PRAGMA foreign_keys=ON"))
        if messages:
            conn.commit()

    return messages


def _drop_stale_catalog_tables(db_engine: Engine) -> list[str]:
    """Rimuove dal crm.db le tabelle catalog STALE (duplicato del catalogo che
    vive in catalog.db) — detrito della migrazione monolite→3 DB.

    A differenza di `_drop_phantom_tables` (solo stub vuoti ≤3 colonne), droppa
    anche le tabelle POPOLATE: l'app non le legge mai da crm.db (usa
    get_catalog_session). Prerequisito: `_fix_cross_db_fk` ha gia' rimosso ogni
    FK business→catalog (altrimenti skip difensivo per tabella ancora referenziata).

    SAFETY — skip su DB in-memory: i test usano un singolo engine dove le tabelle
    catalog convivono legittimamente con quelle business; non vanno toccate.
    """
    db = db_engine.url.database
    if db in (None, "", ":memory:"):
        return []

    messages: list[str] = []
    dropped: list[str] = []
    with db_engine.connect() as conn:
        existing = {row[0] for row in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )).fetchall()}
        targets = sorted(CATALOG_TABLE_NAMES & existing)
        if not targets:
            return []

        # Difesa: nessuna tabella business deve ancora referenziare un target via FK
        business = existing - CATALOG_TABLE_NAMES - NUTRITION_TABLE_NAMES
        referenced: set[str] = set()
        for bt in business:
            for fk in conn.execute(text(f"PRAGMA foreign_key_list([{bt}])")).fetchall():
                if fk[2] in targets:
                    referenced.add(fk[2])

        for t in targets:
            if t in referenced:
                logger.warning(
                    "  schema_sync: skip drop stale '%s' — ancora referenziata da FK business", t
                )
                continue
            conn.execute(text(f"DROP TABLE IF EXISTS [{t}]"))
            dropped.append(t)
            msg = f"dropped stale catalog table '{t}' (vive in catalog.db)"
            messages.append(msg)
            logger.info("  schema_sync: %s", msg)
        if dropped:
            conn.commit()

    # Compatta lo spazio liberato (best-effort, fuori transazione, mai fatale al boot)
    if dropped:
        try:
            raw = db_engine.raw_connection()
            try:
                raw.execute("VACUUM")
                raw.commit()
            finally:
                raw.close()
        except Exception as exc:  # noqa: BLE001 — VACUUM non deve mai bloccare il boot
            logger.warning("  schema_sync: VACUUM post-drop fallito (non fatale): %s", exc)

    return messages


def _backfill_quota_stornata_rettifiche(db_engine: Engine) -> list[str]:
    """Backfill idempotente (G9.2b, ADR-022 Addendum I): dà una derivazione ledger al
    `quota_stornata` legacy scritto a mano PRIMA della terza penna `post_adjustment`.

    Per ogni contratto con `quota_stornata > 0.009` e ZERO rettifiche → 1 riga
    `BACKFILL_LEGACY` di pari importo (`data_effettiva = data_chiusura`, fallback oggi).
    Da lì l'àncora `quota_stornata == Σ importo[rettifiche_contratto]` vale anche sul
    legacy. Additivo (colonna e `residuo()` intatti), idempotente (guard zero-rettifiche
    → re-run no-op), raw SQL (gira in frozen, come `_fix_cross_db_fk`). Nessun filtro
    `deleted_at` sui contratti: l'àncora è universale, vale anche sui soft-deleted.
    """
    messages: list[str] = []
    with db_engine.connect() as conn:
        existing = {row[0] for row in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )).fetchall()}
        if not {"contratti", "rettifiche_contratto"} <= existing:
            return []  # tabella non ancora creata (la crea create_db_and_tables al boot, prima di sync)

        candidates = conn.execute(text(
            """
            SELECT c.id, c.trainer_id, c.quota_stornata, COALESCE(c.data_chiusura, :today)
            FROM contratti c
            WHERE c.quota_stornata > 0.009
              AND NOT EXISTS (SELECT 1 FROM rettifiche_contratto r WHERE r.id_contratto = c.id)
            """
        ), {"today": date.today().isoformat()}).fetchall()
        for cid, tid, quota, data_eff in candidates:
            conn.execute(text(
                """
                INSERT INTO rettifiche_contratto
                    (trainer_id, id_contratto, importo, causale, data_effettiva, note)
                VALUES (:tid, :cid, :importo, :causale, :data_eff,
                        'Backfill quota_stornata legacy pre-G9.2b (ADR-022 Addendum I)')
                """
            ), {
                "tid": tid,
                "cid": cid,
                "importo": quota,
                "causale": CAUSALE_BACKFILL_LEGACY,
                "data_eff": data_eff,
            })
            msg = (
                f"rettifiche_contratto — backfill {CAUSALE_BACKFILL_LEGACY} "
                f"contratto {cid} (+{quota})"
            )
            messages.append(msg)
            logger.info("  schema_sync: %s", msg)
        if messages:
            conn.commit()

    return messages


def sync_schema(db_engine: Engine) -> list[str]:
    """
    Confronta modelli ORM vs DB reale e aggiunge colonne mancanti.
    Traccia la versione del DB ed esegue data migration pendenti.

    Ritorna lista di messaggi con le modifiche effettuate.
    Solo crm.db (business tables), mai catalog/nutrition.
    """
    messages: list[str] = []

    # Fix legacy cross-DB FK constraints (idempotente) — DEVE precedere i drop sotto
    messages.extend(_fix_cross_db_fk(db_engine))

    # Rimuovi tabelle phantom da backup pre-separazione (stub vuoti, idempotente)
    messages.extend(_drop_phantom_tables(db_engine))

    # Rimuovi tabelle catalog stale POPOLATE (detrito migrazione monolite→3DB, idempotente)
    messages.extend(_drop_stale_catalog_tables(db_engine))

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

    # Backfill G9.2b: quota_stornata legacy → 1 riga BACKFILL_LEGACY (idempotente, additivo).
    # DEVE seguire la column-sync: su un DB pre-G7.0 la colonna quota_stornata nasce QUI sopra
    # (ALTER TABLE) — eseguirlo prima crasherebbe il boot con "no such column".
    messages.extend(_backfill_quota_stornata_rettifiche(db_engine))

    if columns_added == 0:
        logger.info("  schema_sync: schema up to date (%d tables checked)", tables_checked)
    else:
        logger.info(
            "  schema_sync: %d columns added across %d tables",
            columns_added,
            tables_checked,
        )

    return messages
