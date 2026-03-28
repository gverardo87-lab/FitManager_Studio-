#!/usr/bin/env python3
"""
Seed diretto via SQLite per le parti che falliscono via API.
Inserisce misurazioni, obiettivi, movimenti manuali.
"""
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import sqlite3
from datetime import date, timedelta, datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "crm_dev.db")
DB_PATH = os.path.abspath(DB_PATH)
TODAY = date.today()
NOW = datetime.now(timezone.utc).isoformat()

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
# FK OFF: valori_misurazione e obiettivi hanno FK cross-DB (metriche in catalog.db)
conn.execute("PRAGMA foreign_keys=OFF")

# Get trainer_id
trainer_id = conn.execute("SELECT id FROM trainers LIMIT 1").fetchone()[0]
print(f"Trainer ID: {trainer_id}")

# Get client IDs ordered
clients = conn.execute("SELECT id, nome, cognome FROM clienti WHERE deleted_at IS NULL ORDER BY id").fetchall()
cids = [c[0] for c in clients]
print(f"Clienti: {len(cids)}")

# == Misurazioni ==
print("\n--- Misurazioni ---")
profiles = {
    0: [(1, [92.0, 89.5, 87.8, 86.2]), (3, [24.0, 22.8, 21.5, 20.5])],   # Peso + Massa Grassa
    1: [(1, [58.0, 57.5, 57.2, 57.0]), (3, [22.0, 21.5, 21.0, 20.5])],
    2: [(1, [85.0, 85.5, 86.2, 86.8]), (3, [18.0, 17.5, 17.0, 16.5])],
    3: [(1, [68.0, 67.0, 66.0, 65.5])],
    7: [(1, [73.0, 72.0, 71.0, 70.2]), (3, [28.0, 27.0, 26.5, 25.8])],
    10: [(1, [98.0, 96.5, 95.0, 93.8]), (3, [32.0, 31.0, 30.2, 29.5])],
}

for ci, metrics in profiles.items():
    if ci >= len(cids):
        continue
    cid = cids[ci]
    n = len(metrics[0][1])
    for si in range(n):
        d = (TODAY + timedelta(days=-(n - si) * 21)).isoformat()
        # Insert measurement session
        conn.execute(
            "INSERT INTO misurazioni_cliente (id_cliente, trainer_id, data_misurazione, note) VALUES (?, ?, ?, ?)",
            (cid, trainer_id, d, f"Misurazione #{si + 1}"),
        )
        mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        # Insert values
        for metric_id, vals in metrics:
            conn.execute(
                "INSERT INTO valori_misurazione (id_misurazione, id_metrica, valore) VALUES (?, ?, ?)",
                (mid, metric_id, vals[si]),
            )
    nome = clients[ci][1]
    print(f"  {nome}: {n} sessioni")

conn.commit()

# == Obiettivi ==
print("\n--- Obiettivi ---")
goals = [
    (0, 1, "diminuire", 82.0, 92.0, "2026-01-01", "2026-01-01", "2026-06-30", 1, "Peso forma estate"),
    (0, 3, "diminuire", 18.0, 24.0, "2026-01-01", "2026-01-01", "2026-06-30", 2, "Body fat target"),
    (1, 1, "mantenere", None, 58.0, "2026-02-01", "2026-02-01", None, 3, "Mantenere peso"),
    (2, 1, "aumentare", 90.0, 85.0, "2025-12-01", "2025-12-01", "2026-12-01", 1, "Massa target"),
    (7, 1, "diminuire", 65.0, 73.0, "2026-02-01", "2026-02-01", "2026-07-31", 1, "-8kg"),
    (10, 1, "diminuire", 88.0, 98.0, "2026-02-20", "2026-02-20", "2026-08-31", 1, "Peso target medico"),
]

for ci, metric_id, dire, target, baseline, data_base, ini, sca, pri, note in goals:
    if ci >= len(cids):
        continue
    cid = cids[ci]
    conn.execute(
        """INSERT INTO obiettivi_cliente
        (id_cliente, trainer_id, id_metrica, direzione, valore_target, valore_baseline,
         data_baseline, data_inizio, data_scadenza, tipo_obiettivo, priorita, stato,
         completato_automaticamente, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cid, trainer_id, metric_id, dire, target, baseline, data_base, ini, sca,
         "corporeo", pri, "attivo", False, note),
    )
    nome = clients[ci][1]
    print(f"  {nome}: {dire} metrica #{metric_id}")

conn.commit()

# == Movimenti manuali ==
print("\n--- Movimenti manuali ---")
movs = [
    ("USCITA", "2026-02-15", 89.0, "POS", "Attrezzatura", "Elastici resistenza TheraBand"),
    ("USCITA", "2026-01-10", 45.0, "CONTANTI", "Materiale", "Tappetini yoga x3"),
    ("ENTRATA", "2026-03-01", 50.0, "CONTANTI", "Consulenza", "Consulenza nutrizionale una tantum"),
    ("USCITA", "2026-03-05", 29.0, "POS", "Software", "Abbonamento Canva Pro"),
    ("USCITA", "2026-03-15", 150.0, "BONIFICO", "Formazione", "Corso aggiornamento NSCA"),
    ("ENTRATA", "2026-02-20", 30.0, "CONTANTI", "Altro", "Vendita magliette palestra"),
]

for tipo, data, imp, met, cat, note in movs:
    conn.execute(
        """INSERT INTO movimenti_cassa
        (trainer_id, data_movimento, data_effettiva, tipo, categoria, importo, metodo, note, operatore)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trainer_id, data, data, tipo, cat, imp, met, note, "API"),
    )
    print(f"  {tipo} EUR {imp} - {note[:40]}")

conn.commit()

# == Riepilogo finale ==
print("\n--- Riepilogo DB ---")
tables = [
    "trainers", "clienti", "contratti", "rate_programmate", "agenda",
    "movimenti_cassa", "misurazioni_cliente", "valori_misurazione",
    "obiettivi_cliente", "spese_ricorrenti", "communication_log",
    "schede_allenamento", "sessioni_scheda", "esercizi_sessione",
    "todos", "audit_log",
]
for t in tables:
    try:
        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {c}")
    except Exception as e:
        print(f"  {t}: ERROR {e}")

conn.close()
print("\n=== SEED DIRETTO COMPLETATO ===")
