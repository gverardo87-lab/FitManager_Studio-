"""
Spike funzionale SQLCipher (ADR-013, gate G1).

Verifica, contro il driver reale `sqlcipher3` (wheel Windows nativo):
  1. crea un DB cifrato, scrive, chiude;
  2. il file e' ciphertext (lo sqlite3 stdlib NON lo legge);
  3. riapertura con chiave corretta -> dati leggibili;
  4. riapertura con chiave SBAGLIATA -> fallisce;
  5. integrazione SQLAlchemy (path che userebbe l'app: SQLModel/SQLAlchemy
     con PRAGMA key su connect) -> insert/select OK;
  6. stampa cipher_version.

Esce 0 se tutti i check passano, 1 altrimenti. Non tocca crm.db ne' la venv di progetto.
"""

import os
import sqlite3 as stdlib_sqlite3
import sys
import tempfile

KEY = "correct horse battery staple — spike key"
WRONG_KEY = "wrong key"


def _ok(label):
    print(f"  [OK]   {label}")


def _fail(label, detail=""):
    print(f"  [FAIL] {label} {detail}")


def main() -> int:
    failures = 0
    print("=== Spike SQLCipher — test funzionale ===")

    try:
        import sqlcipher3
        from sqlcipher3 import dbapi2 as sqlcipher_dbapi
    except Exception as e:  # noqa: BLE001
        _fail("import sqlcipher3", repr(e))
        return 1
    _ok(f"import sqlcipher3 (lib {getattr(sqlcipher3, '__version__', '?')})")

    tmpdir = tempfile.mkdtemp(prefix="sqlcipher_spike_")
    db_path = os.path.join(tmpdir, "encrypted.db")

    # --- 1. crea DB cifrato + scrive ---
    try:
        conn = sqlcipher_dbapi.connect(db_path)
        conn.execute(f"PRAGMA key = '{KEY}'")
        ver = conn.execute("PRAGMA cipher_version").fetchone()
        conn.execute("CREATE TABLE atleti (id INTEGER PRIMARY KEY, nome TEXT, peso REAL)")
        conn.execute("INSERT INTO atleti (nome, peso) VALUES (?, ?)", ("Mario Rossi", 78.5))
        conn.commit()
        conn.close()
        _ok(f"crea DB cifrato + scrive (cipher_version={ver[0] if ver else '?'})")
    except Exception as e:  # noqa: BLE001
        _fail("crea DB cifrato", repr(e))
        return 1

    # --- 2. il file e' ciphertext: sqlite3 stdlib NON deve leggerlo ---
    try:
        plain = stdlib_sqlite3.connect(db_path)
        plain.execute("SELECT name FROM sqlite_master").fetchall()
        plain.close()
        _fail("ciphertext at-rest", "sqlite3 stdlib ha letto il DB cifrato (NON cifrato!)")
        failures += 1
    except stdlib_sqlite3.DatabaseError:
        _ok("ciphertext at-rest (sqlite3 stdlib rifiuta: 'file is not a database')")
    except Exception as e:  # noqa: BLE001
        _ok(f"ciphertext at-rest (sqlite3 stdlib fallisce: {type(e).__name__})")

    # bonus: i primi byte non sono l'header 'SQLite format 3'
    with open(db_path, "rb") as fh:
        header = fh.read(16)
    if header.startswith(b"SQLite format 3"):
        _fail("header check", "il file inizia con header SQLite in chiaro")
        failures += 1
    else:
        _ok(f"header check (primi byte non-SQLite: {header[:6]!r}...)")

    # --- 3. riapertura con chiave corretta ---
    try:
        conn = sqlcipher_dbapi.connect(db_path)
        conn.execute(f"PRAGMA key = '{KEY}'")
        rows = conn.execute("SELECT nome, peso FROM atleti").fetchall()
        conn.close()
        if rows == [("Mario Rossi", 78.5)]:
            _ok("riapertura con chiave corretta -> dati integri")
        else:
            _fail("riapertura chiave corretta", f"dati inattesi: {rows}")
            failures += 1
    except Exception as e:  # noqa: BLE001
        _fail("riapertura chiave corretta", repr(e))
        failures += 1

    # --- 4. riapertura con chiave SBAGLIATA deve fallire ---
    try:
        conn = sqlcipher_dbapi.connect(db_path)
        conn.execute(f"PRAGMA key = '{WRONG_KEY}'")
        conn.execute("SELECT nome FROM atleti").fetchall()
        conn.close()
        _fail("chiave sbagliata", "lettura riuscita con chiave errata!")
        failures += 1
    except Exception as e:  # noqa: BLE001
        _ok(f"chiave sbagliata respinta ({type(e).__name__})")

    # --- 5. integrazione SQLAlchemy (path app) ---
    try:
        from sqlalchemy import create_engine, event, text

        sa_db = os.path.join(tmpdir, "sa_encrypted.db")
        # module= inietta il DBAPI di sqlcipher3 al posto di sqlite3 stdlib
        engine = create_engine(f"sqlite:///{sa_db}", module=sqlcipher_dbapi)

        @event.listens_for(engine, "connect")
        def _set_key(dbapi_conn, _rec):  # noqa: ANN001
            dbapi_conn.execute(f"PRAGMA key = '{KEY}'")

        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE clienti (id INTEGER PRIMARY KEY, nome TEXT)"))
            conn.execute(text("INSERT INTO clienti (nome) VALUES (:n)"), {"n": "Giulia Bianchi"})
        with engine.connect() as conn:
            got = conn.execute(text("SELECT nome FROM clienti")).fetchall()
        engine.dispose()

        # verifica che anche il DB SQLAlchemy sia ciphertext
        try:
            p = stdlib_sqlite3.connect(sa_db)
            p.execute("SELECT name FROM sqlite_master").fetchall()
            p.close()
            sa_encrypted = False
        except Exception:  # noqa: BLE001
            sa_encrypted = True

        if got == [("Giulia Bianchi",)] and sa_encrypted:
            _ok("SQLAlchemy + PRAGMA key su connect -> insert/select OK, file cifrato")
        else:
            _fail("SQLAlchemy", f"rows={got} encrypted={sa_encrypted}")
            failures += 1
    except Exception as e:  # noqa: BLE001
        _fail("SQLAlchemy integrazione", repr(e))
        failures += 1

    print("")
    if failures == 0:
        print("RISULTATO: TUTTI I CHECK PASSATI [OK]")
        return 0
    print(f"RISULTATO: {failures} CHECK FALLITI [FAIL]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
