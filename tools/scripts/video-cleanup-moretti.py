"""Pre-run cleanup: rimuove tutti i dati test di Luca Moretti da crm_dev.db."""
import sqlite3

conn = sqlite3.connect("data/crm_dev.db")
ids = [r[0] for r in conn.execute(
    "SELECT id FROM clienti WHERE cognome='Moretti' AND nome='Luca'"
).fetchall()]

if ids:
    ph = ",".join("?" * len(ids))
    cids = [r[0] for r in conn.execute(
        f"SELECT id FROM contratti WHERE id_cliente IN ({ph})", ids
    ).fetchall()]
    if cids:
        cp = ",".join("?" * len(cids))
        conn.execute(f"DELETE FROM rate_programmate WHERE id_contratto IN ({cp})", cids)
        conn.execute(f"DELETE FROM movimenti_cassa WHERE id_contratto IN ({cp})", cids)
        conn.execute(f"DELETE FROM contratti WHERE id IN ({cp})", cids)
    conn.execute(f"DELETE FROM misurazioni_cliente WHERE id_cliente IN ({ph})", ids)
    conn.execute(f"DELETE FROM obiettivi_cliente WHERE id_cliente IN ({ph})", ids)
    conn.execute(f"DELETE FROM clienti WHERE id IN ({ph})", ids)
    conn.commit()
    print(f"  Rimossi {len(ids)} clienti, {len(cids)} contratti")
else:
    print("  Nessun Luca Moretti trovato")
conn.close()
