"""
Import micronutrienti da CSV in nutrition.db.

Legge un CSV con struttura fissa (id, nome, 17 micro, confidence, source_detail),
valida ogni valore contro i range CREA 2019, e aggiorna nutrition.db.

Uso:
  python -m tools.admin_scripts.import_micronutrients data/nutrition/micronutrients_vegetables.csv
  python -m tools.admin_scripts.import_micronutrients data/nutrition/micronutrients_vegetables.csv --dry-run

Struttura CSV:
  id,nome,calcio_mg,ferro_mg,zinco_mg,magnesio_mg,fosforo_mg,potassio_mg,selenio_ug,
  vitamina_a_ug,vitamina_d_ug,vitamina_e_mg,vitamina_c_mg,vitamina_b1_mg,vitamina_b2_mg,
  vitamina_b3_mg,vitamina_b6_mg,vitamina_b9_ug,vitamina_b12_ug,confidence,source_detail

Regole:
  - Aggiorna SOLO campi micro (mai macro, mai nome, mai categoria)
  - Campo vuoto nel CSV = NULL (non tocca il campo)
  - Valore fuori range CREA = WARNING + campo skippato
  - Safety check: id + nome devono matchare il DB
  - Idempotente: rieseguire produce lo stesso risultato
"""

import argparse
import csv
import os
import sqlite3
import sys

# Aggiungi root al path per importare validation ranges
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from tools.admin_scripts.nutrition_validation_ranges import (
    validate_micronutrients,
)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")

MICRO_COLUMNS = [
    "calcio_mg", "ferro_mg", "zinco_mg", "magnesio_mg", "fosforo_mg",
    "potassio_mg", "selenio_ug", "vitamina_a_ug", "vitamina_d_ug",
    "vitamina_e_mg", "vitamina_c_mg", "vitamina_b1_mg", "vitamina_b2_mg",
    "vitamina_b3_mg", "vitamina_b6_mg", "vitamina_b9_ug", "vitamina_b12_ug",
]


def import_csv(csv_path: str, dry_run: bool = False) -> dict:
    """Importa micronutrienti da CSV in nutrition.db."""

    if not os.path.exists(csv_path):
        print(f"ERRORE: File non trovato: {csv_path}")
        return {"error": "file_not_found"}

    if not os.path.exists(DB_PATH):
        print(f"ERRORE: Database non trovato: {DB_PATH}")
        return {"error": "db_not_found"}

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Pre-carica nomi dal DB per safety check
    c.execute("SELECT id, nome FROM alimenti")
    db_foods = {row[0]: row[1] for row in c.fetchall()}

    stats = {
        "rows_read": 0,
        "rows_updated": 0,
        "rows_skipped": 0,
        "fields_updated": 0,
        "fields_skipped": 0,
        "warnings": [],
        "errors": [],
        "by_confidence": {"high": 0, "medium": 0, "low": 0},
    }

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stats["rows_read"] += 1

            # Parse ID
            try:
                food_id = int(row["id"])
            except (ValueError, KeyError):
                stats["errors"].append(f"Riga {stats['rows_read']}: ID invalido '{row.get('id')}'")
                stats["rows_skipped"] += 1
                continue

            csv_nome = row.get("nome", "").strip()
            confidence = row.get("confidence", "medium").strip().lower()

            # Safety check: ID esiste nel DB?
            if food_id not in db_foods:
                stats["errors"].append(f"ID {food_id} ({csv_nome}): non esiste in nutrition.db")
                stats["rows_skipped"] += 1
                continue

            # Safety check: nome corrisponde?
            db_nome = db_foods[food_id]
            if csv_nome and csv_nome != db_nome:
                # Tolleranza: confronto case-insensitive e strip
                if csv_nome.lower().strip() != db_nome.lower().strip():
                    stats["errors"].append(
                        f"ID {food_id}: nome CSV '{csv_nome}' != DB '{db_nome}'"
                    )
                    stats["rows_skipped"] += 1
                    continue

            # Parse micronutrienti
            micros = {}
            for field in MICRO_COLUMNS:
                val = row.get(field, "").strip()
                if val == "" or val.lower() == "null" or val == "-":
                    continue  # campo vuoto = non toccare
                try:
                    micros[field] = round(float(val), 2)
                except ValueError:
                    stats["warnings"].append(
                        f"ID {food_id} ({db_nome}): {field}='{val}' non numerico, skippato"
                    )

            if not micros:
                stats["rows_skipped"] += 1
                continue

            # Validazione range CREA
            range_warnings = validate_micronutrients(db_nome, micros)
            if range_warnings:
                for w in range_warnings:
                    stats["warnings"].append(w)
                    # Rimuovi il campo fuori range
                    field_name = w.split(":")[1].strip().split("=")[0]
                    if field_name in micros:
                        del micros[field_name]
                        stats["fields_skipped"] += 1

            if not micros:
                stats["rows_skipped"] += 1
                continue

            # UPDATE
            if not dry_run:
                set_clause = ", ".join(f"{k} = ?" for k in micros)
                values = list(micros.values()) + [food_id]
                c.execute(f"UPDATE alimenti SET {set_clause} WHERE id = ?", values)

            stats["rows_updated"] += 1
            stats["fields_updated"] += len(micros)
            stats["by_confidence"][confidence] = stats["by_confidence"].get(confidence, 0) + 1

    if not dry_run:
        conn.commit()

    conn.close()
    return stats


def print_report(stats: dict, csv_path: str, dry_run: bool):
    """Stampa report dell'import."""
    mode = "DRY RUN" if dry_run else "ESEGUITO"
    print(f"\n{'=' * 60}")
    print(f"  Import Micronutrienti — {mode}")
    print(f"  File: {os.path.basename(csv_path)}")
    print(f"{'=' * 60}")
    print(f"  Righe lette:      {stats['rows_read']}")
    print(f"  Righe aggiornate: {stats['rows_updated']}")
    print(f"  Righe skippate:   {stats['rows_skipped']}")
    print(f"  Campi aggiornati: {stats['fields_updated']}")
    print(f"  Campi skippati:   {stats['fields_skipped']}")
    print(f"  Confidenza: high={stats['by_confidence'].get('high', 0)}"
          f" medium={stats['by_confidence'].get('medium', 0)}"
          f" low={stats['by_confidence'].get('low', 0)}")

    if stats["errors"]:
        print(f"\n  ERRORI ({len(stats['errors'])}):")
        for e in stats["errors"][:20]:
            print(f"    {e}")
        if len(stats["errors"]) > 20:
            print(f"    ... e altri {len(stats['errors']) - 20}")

    if stats["warnings"]:
        print(f"\n  WARNING ({len(stats['warnings'])}):")
        for w in stats["warnings"][:20]:
            print(f"    {w}")
        if len(stats["warnings"]) > 20:
            print(f"    ... e altri {len(stats['warnings']) - 20}")

    if not stats["errors"] and not stats["warnings"]:
        print("\n  Zero errori, zero warning.")

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import micronutrienti da CSV in nutrition.db"
    )
    parser.add_argument("csv_file", help="Path al file CSV")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula senza scrivere")
    args = parser.parse_args()

    stats = import_csv(args.csv_file, dry_run=args.dry_run)
    if "error" not in stats:
        print_report(stats, args.csv_file, args.dry_run)
