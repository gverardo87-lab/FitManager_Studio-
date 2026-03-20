"""
Recovery script — reinserisce alimenti CREA 2019 persi con il --reset.

Legge i dati macro dai file recovery_foods_*.py (generati da CREA 2019/USDA),
inserisce gli alimenti mancanti in nutrition.db (idempotente per ID),
poi lancia import_micronutrients e populate_portions.

Uso:
  python -m tools.admin_scripts.recover_nutrition_foods
  python -m tools.admin_scripts.recover_nutrition_foods --dry-run

IMPORTANTE: NON usa --reset. Aggiunge solo alimenti mancanti.
"""

import argparse
import os
import sqlite3
import subprocess
import sys

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
CSV_DIR = os.path.join(BASE_DIR, "nutrition")

# Import food data from recovery files
from tools.admin_scripts.recovery_foods_vegetables import VEGETABLES
from tools.admin_scripts.recovery_foods_fruits import FRUITS
from tools.admin_scripts.recovery_foods_cereals_legumes import CEREALS_LEGUMES
from tools.admin_scripts.recovery_foods_meat_fish import MEAT_FISH
from tools.admin_scripts.recovery_foods_dairy import DAIRY
from tools.admin_scripts.recovery_foods_remaining import REMAINING


def recover(dry_run: bool = False) -> None:
    if not os.path.exists(DB_PATH):
        print(f"ERRORE: {DB_PATH} non trovato. Esegui prima build_nutrition.py")
        sys.exit(1)

    # Backup PRIMA di qualsiasi modifica
    if not dry_run:
        bak_path = DB_PATH + ".pre_recovery.bak"
        import shutil
        shutil.copy2(DB_PATH, bak_path)
        print(f"  Backup creato: {bak_path}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # Leggi ID esistenti
    existing_ids = {row[0] for row in c.execute("SELECT id FROM alimenti").fetchall()}
    print(f"  Alimenti esistenti: {len(existing_ids)}")

    # Assembla tutti i dati
    all_foods = VEGETABLES + FRUITS + CEREALS_LEGUMES + MEAT_FISH + DAIRY + REMAINING

    inserted = 0
    skipped = 0
    errors = []

    for entry in all_foods:
        fid, nome, cat_id, kcal, prot, carb, fat, food_type, source = entry

        if fid in existing_ids:
            skipped += 1
            continue

        if dry_run:
            inserted += 1
            continue

        try:
            c.execute("""
                INSERT INTO alimenti (id, nome, categoria_id, energia_kcal, proteine_g,
                    carboidrati_g, grassi_g, food_type, source, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (fid, nome, cat_id, kcal, prot, carb, fat, food_type, source))
            inserted += 1
        except sqlite3.IntegrityError as e:
            errors.append(f"  ID {fid} ({nome}): {e}")

    if not dry_run:
        conn.commit()
    conn.close()

    print(f"  Inseriti: {inserted}, Skippati (gia' esistenti): {skipped}")
    if errors:
        print(f"  Errori: {len(errors)}")
        for err in errors[:10]:
            print(err)

    if dry_run:
        print("\n  [DRY RUN] Nessuna modifica eseguita.")
        return

    # Verifica conteggio finale
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM alimenti WHERE is_active = 1").fetchone()[0]
    conn.close()
    print(f"\n  Alimenti attivi dopo recovery: {total}")

    # Step 2: Import micronutrienti dai CSV
    print("\n=== Step 2: Import micronutrienti ===")
    csv_files = sorted(
        f for f in os.listdir(CSV_DIR) if f.startswith("micronutrients_") and f.endswith(".csv")
    )
    for csv_file in csv_files:
        csv_path = os.path.join(CSV_DIR, csv_file)
        print(f"\n  Importing {csv_file}...")
        subprocess.run(
            [sys.executable, "-m", "tools.admin_scripts.import_micronutrients", csv_path],
            check=False,
        )

    # Step 3: Popola porzioni standard
    print("\n=== Step 3: Porzioni standard ===")
    subprocess.run(
        [sys.executable, "-m", "tools.admin_scripts.populate_portions"],
        check=False,
    )

    # Statistiche finali
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM alimenti WHERE is_active = 1").fetchone()[0]
    with_micros = conn.execute(
        "SELECT COUNT(*) FROM alimenti WHERE is_active = 1 AND calcio_mg IS NOT NULL"
    ).fetchone()[0]
    portions = conn.execute("SELECT COUNT(*) FROM porzioni_standard").fetchone()[0]
    conn.close()
    print(f"\n=== Recovery completato ===")
    print(f"  Alimenti attivi:     {total}")
    print(f"  Con micronutrienti:  {with_micros}")
    print(f"  Porzioni standard:   {portions}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recovery alimenti CREA 2019")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    recover(dry_run=args.dry_run)
