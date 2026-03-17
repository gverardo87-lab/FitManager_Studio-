#!/usr/bin/env python3
"""
fix_exercises_audit.py — Script chirurgico per pulizia esercizi attivi.

Audit 2026-03-17: 391 esercizi attivi, trovati 7 duplicati, 4 classificazioni
errate, 7 bodyweight con attrezzatura, 12 nome_en mancanti, 1 near-duplicate.

Ogni fix e' tracciabile, reversibile, e annotata con motivazione.

Uso:
    python tools/scripts/fix_exercises_audit.py [--db crm|crm_dev|both] [--dry-run]

Default: --db crm_dev (sicuro per sviluppo).
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


# ═══════════════════════════════════════════════════════════
# FIX DEFINITIONS
# ═══════════════════════════════════════════════════════════

# --- 1. DUPLICATI: disattiva uno per coppia (in_subset=0) ---
# Manteniamo l'esercizio con dati piu completi o con la classificazione
# corretta. Il disattivato resta nel DB per referenza storica.

DEACTIVATE_IDS = {
    349:  "Duplicato di ID 119 'Ruota Addominale' (119 e' advanced, piu specifico)",
    389:  "Duplicato di ID 383 'Rollout con Bilanciere' (389 e' variante bench, ridondante)",
    1100: "Duplicato di ID 310 'Lateral Shuffle' (310 e' avviamento con nome_en, 1100 cardio senza)",
    1094: "Duplicato di ID 176 'Jumping Jacks' (176 e' avviamento con nome_en, 1094 cardio senza)",
    468:  "Duplicato di ID 467 'Distensioni Pettorali' (identici, 468 ha nome_en meno specifico)",
    351:  "Duplicato di ID 350 'Adduttori' stretching (identici)",
    1091: "Near-duplicato di ID 202 '90/90 Anca' (stesso esercizio, 202 ha muscoli piu completi)",
}

# --- 2. RENAME: disambiguazione nomi duplicati con esercizi diversi ---

RENAMES = {
    580: {
        "nome": "Elevazioni Frontali Gambe",
        "motivo": "Disambiguazione da ID 581 (spalle). Questo e' stretching femorali.",
    },
}

# --- 3. CLASSIFICAZIONE ERRATA: fix categoria/pattern/muscoli ---

CLASSIFICATION_FIXES = {
    415: {
        "campo": {
            "categoria": "compound",
            "pattern_movimento": "pull_v",
            "muscoli_primari": json.dumps(["lats", "back"]),
            "muscoli_secondari": json.dumps(["biceps", "core", "forearms"]),
            "nome_en": "Pull-Up",
        },
        "motivo": "Trazioni alla Sbarra: era isolation/push_h/triceps — completamente errato. "
                  "E' un compound pull_v per dorsali (errore di traduzione dal DB originale).",
    },
    557: {
        "campo": {
            "categoria": "isolation",
        },
        "motivo": "Rotazione Esterna con Banda: esercizio mono-articolare rehab (cuffia rotatori). "
                  "Era compound, corretto a isolation (coerente con ID 558 Rotazione Esterna a Cavo).",
    },
    1093: {
        "campo": {
            "categoria": "isolation",
        },
        "motivo": "Glute Bridge Bilaterale con Elastico: ponte glutei e' mono-articolare (estensione anca). "
                  "Era compound, corretto a isolation.",
    },
    1086: {
        "campo": {
            "pattern_movimento": "hip_thrust",
            "muscoli_primari": json.dumps(["glutes"]),
            "muscoli_secondari": json.dumps(["hip_flexors"]),
        },
        "motivo": "Monster Walk con Elastico: lavora gluteo medio (abduttori), non adduttori. "
                  "Pattern da adductor a hip_thrust, muscoli primari corretti.",
    },
}

# --- 4. BODYWEIGHT CON ATTREZZATURA: fix categoria ---

CATEGORY_FIXES = {
    376: {
        "campo": {"categoria": "compound"},
        "motivo": "Lancio Medicina Pallone all'indietro: usa dumbbell, non e' bodyweight. "
                  "Movimento esplosivo multi-articolare → compound.",
    },
    383: {
        "campo": {"categoria": "compound"},
        "motivo": "Rollout con Bilanciere: usa barbell, non e' bodyweight. "
                  "Movimento multi-articolare (spalla + anca) → compound.",
    },
    466: {
        "campo": {"categoria": "compound"},
        "motivo": "Push da Terra a Tre Punti: usa dumbbell, non e' bodyweight. "
                  "Movimento push multi-articolare → compound.",
    },
    467: {
        "campo": {"categoria": "isolation"},
        "motivo": "Distensioni Pettorali: usa dumbbell, non e' bodyweight. "
                  "Singolo pattern push_h → isolation (fly/press leggero).",
    },
    726: {
        "campo": {"categoria": "compound"},
        "motivo": "Twist con Palla Medica: usa dumbbell (palla medica), non e' bodyweight. "
                  "Movimento rotazionale multi-segmento → compound.",
    },
    1024: {
        "campo": {"categoria": "isolation"},
        "motivo": "Lancio Pettorale Sdraiato: usa dumbbell, non e' bodyweight. "
                  "Push orizzontale leggero → isolation.",
    },
}

# --- 5. NOME_EN MANCANTE: cardio batch ---

NOME_EN_FIXES = {
    1095: "High Knee March",
    1096: "Step Aerobics",
    1097: "Nordic Walking",
    1098: "Slow Crawl Swimming",
    1099: "Water Walking",
    1101: "Treadmill HIIT Sprint",
    1102: "Rowing Machine 500m Intervals",
    1103: "Assault Bike Tabata",
    1104: "Cardio Circuit AMRAP",
    1105: "Fartlek Run",
}
# NB: 1094 (Jumping Jacks) e 1100 (Lateral Shuffle) sono disattivati come duplicati


# ═══════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════

def apply_fixes(db_path: str, dry_run: bool = False) -> dict:
    """Applica tutti i fix al database. Ritorna contatori."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    stats = {"deactivated": 0, "renamed": 0, "classification": 0, "category": 0, "nome_en": 0, "errors": []}
    now = datetime.now(timezone.utc).isoformat()

    # Verifica che gli ID esistano e siano attivi
    def verify_active(exercise_id: int) -> bool:
        row = conn.execute(
            "SELECT id, nome, in_subset FROM esercizi WHERE id = ?", (exercise_id,)
        ).fetchone()
        if not row:
            stats["errors"].append(f"ID {exercise_id}: non trovato nel DB")
            return False
        if not row[2]:  # in_subset = 0
            stats["errors"].append(f"ID {exercise_id} '{row[1]}': gia' disattivato")
            return False
        return True

    # 1. Disattivazione duplicati
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}=== DISATTIVAZIONE DUPLICATI ===")
    for ex_id, motivo in DEACTIVATE_IDS.items():
        if not verify_active(ex_id):
            continue
        nome = conn.execute("SELECT nome FROM esercizi WHERE id = ?", (ex_id,)).fetchone()[0]
        print(f"  {'SKIP' if dry_run else 'FIX '} ID {ex_id:5d} '{nome}' → in_subset=0 | {motivo}")
        if not dry_run:
            conn.execute("UPDATE esercizi SET in_subset = 0 WHERE id = ?", (ex_id,))
        stats["deactivated"] += 1

    # 2. Rename disambiguazione
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}=== RENAME ===")
    for ex_id, fix in RENAMES.items():
        if not verify_active(ex_id):
            continue
        old_nome = conn.execute("SELECT nome FROM esercizi WHERE id = ?", (ex_id,)).fetchone()[0]
        print(f"  {'SKIP' if dry_run else 'FIX '} ID {ex_id:5d} '{old_nome}' → '{fix['nome']}' | {fix['motivo']}")
        if not dry_run:
            conn.execute("UPDATE esercizi SET nome = ? WHERE id = ?", (fix["nome"], ex_id))
        stats["renamed"] += 1

    # 3. Classificazione errata
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}=== CLASSIFICAZIONE ===")
    for ex_id, fix in CLASSIFICATION_FIXES.items():
        if not verify_active(ex_id):
            continue
        nome = conn.execute("SELECT nome FROM esercizi WHERE id = ?", (ex_id,)).fetchone()[0]
        campi = ", ".join(f"{k}={v}" for k, v in fix["campo"].items())
        print(f"  {'SKIP' if dry_run else 'FIX '} ID {ex_id:5d} '{nome}' → {campi}")
        print(f"         {fix['motivo']}")
        if not dry_run:
            sets = ", ".join(f"{k} = ?" for k in fix["campo"])
            vals = list(fix["campo"].values()) + [ex_id]
            conn.execute(f"UPDATE esercizi SET {sets} WHERE id = ?", vals)
        stats["classification"] += 1

    # 4. Categoria bodyweight errata
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}=== CATEGORIA BODYWEIGHT ===")
    for ex_id, fix in CATEGORY_FIXES.items():
        if not verify_active(ex_id):
            continue
        nome = conn.execute("SELECT nome FROM esercizi WHERE id = ?", (ex_id,)).fetchone()[0]
        new_cat = fix["campo"]["categoria"]
        print(f"  {'SKIP' if dry_run else 'FIX '} ID {ex_id:5d} '{nome}' → categoria={new_cat} | {fix['motivo']}")
        if not dry_run:
            conn.execute("UPDATE esercizi SET categoria = ? WHERE id = ?", (new_cat, ex_id))
        stats["category"] += 1

    # 5. nome_en mancanti
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}=== NOME_EN MANCANTI ===")
    for ex_id, nome_en in NOME_EN_FIXES.items():
        row = conn.execute(
            "SELECT nome, in_subset FROM esercizi WHERE id = ?", (ex_id,)
        ).fetchone()
        if not row:
            stats["errors"].append(f"ID {ex_id}: non trovato nel DB")
            continue
        print(f"  {'SKIP' if dry_run else 'FIX '} ID {ex_id:5d} '{row[0]}' → nome_en='{nome_en}'")
        if not dry_run:
            conn.execute("UPDATE esercizi SET nome_en = ? WHERE id = ?", (nome_en, ex_id))
        stats["nome_en"] += 1

    if not dry_run:
        conn.commit()

    # Conteggio finale
    active_count = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE in_subset = 1 AND deleted_at IS NULL"
    ).fetchone()[0]

    conn.close()

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}=== RIEPILOGO ({db_path}) ===")
    print(f"  Disattivati:     {stats['deactivated']}")
    print(f"  Rinominati:      {stats['renamed']}")
    print(f"  Classificazione: {stats['classification']}")
    print(f"  Categoria:       {stats['category']}")
    print(f"  Nome EN:         {stats['nome_en']}")
    print(f"  Errori:          {len(stats['errors'])}")
    print(f"  Esercizi attivi: {active_count}")
    if stats["errors"]:
        for e in stats["errors"]:
            print(f"  ⚠ {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Fix chirurgico esercizi da audit 2026-03-17")
    parser.add_argument("--db", choices=["crm", "crm_dev", "both"], default="crm_dev",
                        help="Database target (default: crm_dev)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostra le modifiche senza applicarle")
    args = parser.parse_args()

    targets = []
    if args.db in ("crm_dev", "both"):
        targets.append(str(DATA_DIR / "crm_dev.db"))
    if args.db in ("crm", "both"):
        targets.append(str(DATA_DIR / "crm.db"))

    for db_path in targets:
        if not Path(db_path).exists():
            print(f"ERRORE: {db_path} non trovato")
            sys.exit(1)

    for db_path in targets:
        print(f"\n{'='*60}")
        print(f"TARGET: {db_path}")
        print(f"{'='*60}")
        apply_fixes(db_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
