"""
Video 02 — Setup DB: elimina contratto €550, crea contratto scaduto con rate pagate.

Scenario:
  - Luca Moretti esiste (creato dal video 01 o da test precedenti)
  - Elimina il contratto da €550 (cascade: rate + movimenti)
  - Crea contratto "Mensile 4 Sedute": 01/03-31/03, €300, zero acconto
  - Crea 2 rate SALDATE: €150 il 15/03 + €150 il 22/03 (BONIFICO)
  - Il contratto appare in /rinnovi-incassi (chiuso=0, scadenza entro 30gg, crediti>0)

Eseguire PRIMA di ogni sessione di registrazione video 02.
"""
import sqlite3
import sys
from datetime import datetime

DB = "data/crm_dev.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# ──────────────────────────────────────────
# 1. Trova Luca Moretti
# ──────────────────────────────────────────
rows = cur.execute(
    "SELECT id, trainer_id FROM clienti WHERE cognome='Moretti' AND nome='Luca' AND deleted_at IS NULL"
).fetchall()

if not rows:
    print("ERRORE: Luca Moretti non trovato in crm_dev.db")
    print("  Esegui prima il video 01 per creare il cliente, oppure crealo manualmente.")
    conn.close()
    sys.exit(1)

client_id, trainer_id = rows[0]
print(f"[setup] Luca Moretti trovato: client_id={client_id}, trainer_id={trainer_id}")

# ──────────────────────────────────────────
# 2. Elimina TUTTI i contratti esistenti di Moretti (cascade)
# ──────────────────────────────────────────
existing = cur.execute(
    "SELECT id, prezzo_totale FROM contratti WHERE id_cliente=? AND deleted_at IS NULL",
    (client_id,)
).fetchall()

if existing:
    cids = [r[0] for r in existing]
    cp = ",".join("?" * len(cids))
    # Spezza catena rinnovi PRIMA di eliminare (evita FK constraint su rinnovo_di)
    cur.execute(f"UPDATE contratti SET rinnovo_di = NULL WHERE rinnovo_di IN ({cp})", cids)
    cur.execute(f"UPDATE contratti SET rinnovo_di = NULL WHERE id IN ({cp})", cids)
    for cid, prezzo in existing:
        # Cascade: movimenti (hanno FK a rate) → rate → contratto
        cur.execute("DELETE FROM movimenti_cassa WHERE id_contratto=?", (cid,))
        cur.execute("DELETE FROM rate_programmate WHERE id_contratto=?", (cid,))
        cur.execute("DELETE FROM contratti WHERE id=?", (cid,))
        print(f"  Eliminato contratto #{cid} (€{prezzo})")

# Pulisci anche movimenti orfani legati al cliente
cur.execute("DELETE FROM movimenti_cassa WHERE id_cliente=? AND id_contratto IS NULL", (client_id,))

# ──────────────────────────────────────────
# 3. Crea contratto "Mensile 4 Sedute"
# ──────────────────────────────────────────
now_iso = datetime.now().isoformat()
cur.execute("""
    INSERT INTO contratti (
        trainer_id, id_cliente, tipo_pacchetto,
        data_vendita, data_inizio, data_scadenza,
        crediti_totali, crediti_usati, prezzo_totale,
        acconto, totale_versato, stato_pagamento,
        chiuso, note, rinnovo_di, deleted_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    trainer_id, client_id, "Mensile 4 Sedute",
    "2026-03-01",  # data_vendita
    "2026-03-01",  # data_inizio
    "2026-03-31",  # data_scadenza — scade entro 30gg → visibile in rinnovi
    4,              # crediti_totali
    0,              # crediti_usati (computed, ma colonna presente)
    300.00,         # prezzo_totale
    0,              # acconto
    300.00,         # totale_versato (2 rate da 150 pagate)
    "SALDATO",      # stato_pagamento
    0,              # chiuso = False (crediti non esauriti → appare in rinnovi)
    None,           # note
    None,           # rinnovo_di
    None,           # deleted_at
))
contract_id = cur.lastrowid
print(f"[setup] Contratto creato: #{contract_id} — Mensile 4 Sedute, €300, 01/03-31/03")

# ──────────────────────────────────────────
# 4. Crea 2 rate SALDATE
# ──────────────────────────────────────────
for i, (scadenza, desc) in enumerate([
    ("2026-03-15", "Rata 1/2"),
    ("2026-03-22", "Rata 2/2"),
], start=1):
    cur.execute("""
        INSERT INTO rate_programmate (
            id_contratto, data_scadenza, importo_previsto,
            descrizione, stato, importo_saldato, deleted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (contract_id, scadenza, 150.00, desc, "SALDATA", 150.00, None))
    rate_id = cur.lastrowid
    print(f"  Rata #{rate_id}: €150 scadenza {scadenza} — SALDATA")

    # Movimento cassa corrispondente
    cur.execute("""
        INSERT INTO movimenti_cassa (
            trainer_id, data_movimento, data_effettiva,
            tipo, categoria, importo, metodo,
            id_cliente, id_contratto, id_rata,
            note, operatore, deleted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trainer_id,
        f"2026-03-{15 if i == 1 else 22}T10:00:00",  # data_movimento
        f"2026-03-{15 if i == 1 else 22}",             # data_effettiva
        "ENTRATA",
        "PAGAMENTO_RATA",
        150.00,
        "BONIFICO",
        client_id,
        contract_id,
        rate_id,
        f"Pagamento {desc} — Moretti Luca",
        "API",
        None,
    ))

# ──────────────────────────────────────────
# 5. Commit + Verify
# ──────────────────────────────────────────
conn.commit()

# Verifica
print("\n[verify] Stato finale:")
c = cur.execute(
    "SELECT id, tipo_pacchetto, prezzo_totale, totale_versato, stato_pagamento, chiuso, data_scadenza "
    "FROM contratti WHERE id=?", (contract_id,)
).fetchone()
print(f"  Contratto #{c[0]}: {c[1]}, €{c[2]}, versato=€{c[3]}, stato={c[4]}, chiuso={c[5]}, scadenza={c[6]}")

rates = cur.execute(
    "SELECT id, importo_previsto, importo_saldato, stato, data_scadenza "
    "FROM rate_programmate WHERE id_contratto=? AND deleted_at IS NULL", (contract_id,)
).fetchall()
for r in rates:
    print(f"  Rata #{r[0]}: €{r[1]}, saldato=€{r[2]}, stato={r[3]}, scadenza={r[4]}")

movs = cur.execute(
    "SELECT COUNT(*) FROM movimenti_cassa WHERE id_contratto=? AND deleted_at IS NULL", (contract_id,)
).fetchone()
print(f"  Movimenti cassa: {movs[0]}")

print(f"\n[output] client_id={client_id}")
print(f"[output] contract_id={contract_id}")
print(f"[output] trainer_id={trainer_id}")

conn.close()
print("\n[done] Setup video 02 completato.")
