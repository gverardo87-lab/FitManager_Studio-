"""
Entry minimale per lo spike Nuitka (ADR-013, gate G1, cancello 3).

Domanda: l'estensione nativa di `sqlcipher3` (la .pyd con SQLCipher statico)
sopravvive a una compilazione Nuitka --standalone? Se l'exe prodotto cifra,
chiude e rilegge un DB con la chiave giusta, il binding nativo + le sue DLL
sono stati bundlati correttamente.

Stampa un sentinella ASCII; exit 0 se tutto ok, 1 altrimenti. Niente unicode
(la console Windows compilata e' cp1252).
"""

import os
import sqlite3 as stdlib_sqlite3
import sys
import tempfile

KEY = "spike-nuitka-key"


def main() -> int:
    try:
        from sqlcipher3 import dbapi2 as sql
    except Exception as e:  # noqa: BLE001
        print(f"SPIKE_NUITKA_SQLCIPHER_FAIL import: {e!r}")
        return 1

    tmp = tempfile.mkdtemp(prefix="spike_nuitka_")
    db = os.path.join(tmp, "enc.db")

    conn = sql.connect(db)
    conn.execute(f"PRAGMA key = '{KEY}'")
    ver = conn.execute("PRAGMA cipher_version").fetchone()
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("INSERT INTO t (v) VALUES (?)", ("dato-sensibile",))
    conn.commit()
    conn.close()

    # ciphertext at-rest?
    try:
        p = stdlib_sqlite3.connect(db)
        p.execute("SELECT name FROM sqlite_master").fetchall()
        p.close()
        print("SPIKE_NUITKA_SQLCIPHER_FAIL not-encrypted (stdlib read the file)")
        return 1
    except Exception:  # noqa: BLE001
        pass

    # reread with key
    conn = sql.connect(db)
    conn.execute(f"PRAGMA key = '{KEY}'")
    rows = conn.execute("SELECT v FROM t").fetchall()
    conn.close()

    if rows == [("dato-sensibile",)]:
        cv = ver[0] if ver else "?"
        print(f"SPIKE_NUITKA_SQLCIPHER_OK cipher_version={cv}")
        return 0

    print(f"SPIKE_NUITKA_SQLCIPHER_FAIL bad-data {rows}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
