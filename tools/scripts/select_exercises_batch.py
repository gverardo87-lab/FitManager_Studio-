#!/usr/bin/env python3
"""
select_exercises_batch.py — Seleziona N esercizi dall'archivio per attivazione.

Regole ferree:
  1. Solo esercizi archiviati (in_subset=0, deleted_at IS NULL)
  2. CON FOTO obbligatoria (esercizi_media count > 0), TRANNE categorie photo-optional
  3. Nome non duplicato con esercizi gia attivi
  4. Solo beginner/intermediate (no advanced)
  5. Output: lista IDs pronta per activate_batch.py

Categorie photo-optional: avviamento, stretching, mobilita, cardio
(esercizi dinamici/posizionali che non hanno start/end position fotografabile)

Target: Chiara — chinesiologa nutrizionista, clienti donne 18-70,
focus tonificazione/dimagrimento/benessere/postura.

Uso:
    python tools/scripts/select_exercises_batch.py [--db crm_dev|crm] [--count 50]

Output: lista IDs + comando activate_batch.py pronto da copiare.
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

PHOTO_OPTIONAL_CATEGORIES = {"avviamento", "stretching", "mobilita", "cardio"}


def get_pool(conn: sqlite3.Connection) -> list[dict]:
    """Ritorna il pool di esercizi attivabili: archiviati, con foto, nome unico."""

    # Nomi attivi per esclusione duplicati
    active_names: set[str] = set()
    for r in conn.execute(
        "SELECT nome FROM esercizi WHERE in_subset=1 AND deleted_at IS NULL"
    ):
        active_names.add(r[0].lower().strip())

    rows = conn.execute("""
        SELECT e.id, e.nome, e.categoria, e.pattern_movimento, e.attrezzatura,
               e.difficolta, e.muscoli_primari,
               (SELECT COUNT(*) FROM esercizi_media em WHERE em.exercise_id = e.id) as media_count
        FROM esercizi e
        WHERE e.in_subset = 0
          AND e.deleted_at IS NULL
          AND e.difficolta IN ('beginner', 'intermediate')
        ORDER BY e.categoria, e.pattern_movimento, e.nome
    """).fetchall()

    pool: list[dict] = []
    for r in rows:
        eid, nome, cat, pat, equip, diff, muscles_json, media_count = r
        # Esclude nomi duplicati
        if nome.lower().strip() in active_names:
            continue
        # Esclude senza foto (tranne photo-optional)
        has_media = media_count > 0
        is_photo_optional = cat in PHOTO_OPTIONAL_CATEGORIES
        if not has_media and not is_photo_optional:
            continue

        try:
            muscles = json.loads(muscles_json) if muscles_json else []
        except (json.JSONDecodeError, TypeError):
            muscles = []

        pool.append({
            "id": eid, "nome": nome, "cat": cat, "pattern": pat,
            "equip": equip, "diff": diff, "muscles": muscles,
            "media": media_count,
        })

    return pool


# ═══════════════════════════════════════════════════════════
# SELEZIONE CURATA PER CHIARA
# ═══════════════════════════════════════════════════════════
#
# Criteri di selezione per target donne 18-70, tonificazione/dimagrimento/benessere:
#
# GLUTEI & GAMBE (12): priorita #1 per clientela femminile
#   - Hinge con manubri/elastico (accessibili, non solo bilanciere)
#   - Squat varianti (sumo, affondi laterali/indietro)
#   - Step-up funzionale per over-50
#   - Kickback glutei, calf raise
#
# CORE & POSTURA (8): correzione posturale
#   - Crunch base/obliqui/palla (mancanti nel catalogo attivo)
#   - Rotazione funzionale (woodchop, russian twist)
#   - Vuoto addominale (TVA, zero equipment)
#
# UPPER BODY TONING (8): richieste comuni donne
#   - Spalle/tricipiti con elastico e cavo (accessibili)
#   - Croci cavi bassi, curl inclinato
#   - Piegamenti diamante/pike (bodyweight progressions)
#
# STRETCHING (12): wellness/aging population
#   - Stretch base mancanti (quad, femorali, polpacci, pettorali, spalle, tricipiti, collo)
#   - IT band, quadrato lombi, gran dorsale, femorali con fascia
#   - Tilt bacino in piedi (postura pelvica)
#
# AVVIAMENTO (5): warmup essenziali
#   - Corsa leggera, cerchi braccia, rotazioni tronco, skip, calci indietro
#
# CARDIO + GAP (5): completamento
#   - Ciclismo (low-impact over-50), battle rope
#   - Leg extension unilaterale, squat elastico, calf raise band


CURATED_IDS = [
    # ── GLUTEI & GAMBE (12) ──
    1014,  # Stacco Rumeno con Manubri — hinge base manubri, beginner, mc=2
    525,   # Affondi con Manubri — squat base con peso, beginner, mc=2
    535,   # Affondo Indietro con Manubri — meno stress ginocchio, inter, mc=2
    798,   # Plie Squat con Manubrio — adduttori+glutei, beginner, mc=2
    542,   # Step Up con Manubri — progressione, intermediate, mc=2
    1011,  # Step-up con Sollevamento Ginocchio — funzionale over-50, beg, mc=2
    588,   # Kickback Glutei — isolamento glutei bodyweight, beginner, mc=2
    610,   # Iperestensioni o Estensioni lombari — postura+glutei, beg, mc=2
    567,   # Calci Flutter — glutei bodyweight, beginner, mc=2
    419,   # Affondo Camminato — squat funzionale, beginner, mc=2
    867,   # Sollevamento Polpaccio Seduto — soleo macchina, beginner, mc=2
    915,   # Estensione Gambe Unilaterale — leg_ext gap, beginner, mc=2

    # ── CORE & POSTURA (8) ──
    493,   # Crunch — base mancante, beginner, mc=2
    740,   # Crunch Obliqui — obliqui essenziale, beginner, mc=2
    553,   # Crunch su Palla — stability ball, propriocezione, beg, mc=2
    504,   # Crunch Declinato Obliquo — variante declinata, beg, mc=2
    441,   # Crunch Inversi a Cavo — core cavo, beginner, mc=2
    659,   # Sollevamento Ginocchia/Fianchi Parallele — core bw, beg, mc=2
    435,   # Rotazione Interna al Cavo — rotazione cavo, beginner, mc=2
    955,   # Rematore a Un Braccio (rotation) — anti-rotation, beg, mc=2

    # ── UPPER BODY TONING (8) ──
    675,   # Elevazioni Laterali con Band — spalle elastico, beg, mc=2
    952,   # Estensione Tricipiti Banda — tricipiti casa, beginner, mc=2
    696,   # Estensione Tricipiti Cavo Basso — variante cavo, beg, mc=2
    695,   # Croci Cavi Bassi — petto isolation cavo, beginner, mc=2
    621,   # Curl Bicipiti Inclinato — bicipiti manubri, beginner, mc=2
    851,   # Trazioni alla Cavo a Braccio Dritto — lats cavo, beg, mc=2
    836,   # Croci posteriori — spalle posteriori, beginner, mc=2
    524,   # Alzate Frontali Inclinati — spalle variante, beginner, mc=2

    # ── STRETCHING (12) — photo-optional ──
    186,   # Stretching Quadricipiti — base mancante
    187,   # Stretching Femorali — base mancante
    188,   # Stretching Polpacci — base mancante
    189,   # Stretching Pettorali alla Porta — anti-cifosi
    191,   # Stretching Spalle Cross-Body — sedentarieta
    192,   # Stretching Tricipiti — complemento upper
    197,   # Stretching Collo Laterale — cervicale
    321,   # Stretching IT Band (Fascia Lata) — camminatrici
    326,   # Stretching Quadrato Lombi — lombalgia
    329,   # Stretching Femorali con Fascia — variante profonda
    324,   # Stretching Gran Dorsale Laterale — mobilita
    1004,  # Tilt del Bacino in Piedi — postura pelvica

    # ── AVVIAMENTO (5) — photo-optional ──
    175,   # Corsa Leggera — warmup cardio base
    179,   # Cerchi Braccia — warmup spalle
    180,   # Rotazioni del Tronco — warmup core
    177,   # Skip Sul Posto — warmup cardio
    178,   # Calci Indietro — warmup femorali

    # ── CARDIO + GAP (5) ──
    160,   # Ciclismo — low-impact over-50 (photo-optional)
    281,   # Battle Rope — spalle+core (photo-optional)
    967,   # Squat con Elastici — squat casa, beginner, mc=2
    451,   # Sollevamenti Plantari con Banda — calf band, beg, mc=2
    604,   # Estensione Ipocondriaca con Elastici — glutei band, beg, mc=2
]


def validate_selection(conn: sqlite3.Connection, ids: list[int]) -> tuple[list[int], list[str]]:
    """Valida la selezione contro il pool. Ritorna (valid_ids, errors)."""
    pool = get_pool(conn)
    pool_ids = {ex["id"] for ex in pool}

    active_names: set[str] = set()
    for r in conn.execute(
        "SELECT nome FROM esercizi WHERE in_subset=1 AND deleted_at IS NULL"
    ):
        active_names.add(r[0].lower().strip())

    valid: list[int] = []
    errors: list[str] = []

    seen_ids: set[int] = set()
    for eid in ids:
        if eid in seen_ids:
            errors.append(f"ID {eid}: DUPLICATO nella lista")
            continue
        seen_ids.add(eid)

        row = conn.execute(
            "SELECT nome, categoria, in_subset, deleted_at FROM esercizi WHERE id = ?",
            (eid,),
        ).fetchone()

        if not row:
            errors.append(f"ID {eid}: NON ESISTE nel DB")
            continue
        nome, cat, in_subset, deleted = row

        if deleted:
            errors.append(f"ID {eid} '{nome}': SOFT-DELETED")
            continue
        if in_subset == 1:
            errors.append(f"ID {eid} '{nome}': GIA ATTIVO")
            continue
        if nome.lower().strip() in active_names:
            errors.append(f"ID {eid} '{nome}': NOME DUPLICATO con esercizio attivo")
            continue
        if eid not in pool_ids:
            # Non nel pool = manca foto e non e' photo-optional
            media = conn.execute(
                "SELECT COUNT(*) FROM esercizi_media WHERE exercise_id = ?", (eid,)
            ).fetchone()[0]
            if media == 0 and cat not in PHOTO_OPTIONAL_CATEGORIES:
                errors.append(f"ID {eid} '{nome}': SENZA FOTO (cat={cat})")
                continue

        valid.append(eid)

    return valid, errors


def main():
    parser = argparse.ArgumentParser(
        description="Seleziona esercizi dall'archivio per attivazione"
    )
    parser.add_argument(
        "--db", choices=["crm", "crm_dev"], default="crm_dev",
        help="Database target (default: crm_dev)",
    )
    parser.add_argument(
        "--count", type=int, default=50,
        help="Numero esercizi da selezionare (default: 50)",
    )
    parser.add_argument(
        "--pool-only", action="store_true",
        help="Mostra solo il pool disponibile, senza selezionare",
    )
    args = parser.parse_args()

    db_path = str(DATA_DIR / f"{args.db}.db")
    if not Path(db_path).exists():
        print(f"ERRORE: {db_path} non trovato")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    pool = get_pool(conn)
    print(f"Pool disponibile: {len(pool)} esercizi (archiviati, con foto, nome unico)")
    print()

    # Distribuzione pool
    cat_counts = Counter(ex["cat"] for ex in pool)
    print("Distribuzione pool:")
    for cat, cnt in cat_counts.most_common():
        print(f"  {cat:<14s} {cnt:3d}")

    if args.pool_only:
        print()
        for ex in pool:
            print(
                f"  {ex['id']:5d} | {ex['nome']:<45s} | {ex['cat']:<12s} | "
                f"{ex['pattern']:<15s} | {ex['equip']:<12s} | {ex['diff']}"
            )
        conn.close()
        return

    # Validazione selezione curata
    print()
    print(f"=== VALIDAZIONE SELEZIONE ({len(CURATED_IDS)} IDs) ===")
    valid_ids, errors = validate_selection(conn, CURATED_IDS)

    if errors:
        print(f"\nERRORI ({len(errors)}):")
        for e in errors:
            print(f"  {e}")

    print(f"\nValidi: {len(valid_ids)}/{len(CURATED_IDS)}")

    if len(valid_ids) < args.count:
        print(f"\n ATTENZIONE: solo {len(valid_ids)} validi, richiesti {args.count}")

    # Output: lista IDs
    ids_str = ",".join(str(i) for i in valid_ids)
    print(f"\n=== IDS PRONTI ({len(valid_ids)}) ===")
    print(ids_str)

    # Distribuzione selezione
    print(f"\n=== DISTRIBUZIONE SELEZIONE ===")
    sel_cats: Counter[str] = Counter()
    sel_diffs: Counter[str] = Counter()
    for eid in valid_ids:
        row = conn.execute(
            "SELECT categoria, difficolta FROM esercizi WHERE id = ?", (eid,)
        ).fetchone()
        if row:
            sel_cats[row[0]] += 1
            sel_diffs[row[1]] += 1

    print("Per categoria:")
    for cat, cnt in sel_cats.most_common():
        print(f"  {cat:<14s} {cnt:3d}")
    print("Per difficolta:")
    for diff, cnt in sel_diffs.most_common():
        print(f"  {diff:<14s} {cnt:3d}")

    active_count = conn.execute(
        "SELECT COUNT(*) FROM esercizi WHERE in_subset=1 AND deleted_at IS NULL"
    ).fetchone()[0]
    print(f"\nAttivi attuali: {active_count}")
    print(f"Dopo attivazione: {active_count + len(valid_ids)}")

    # Comando activate_batch
    print(f"\n=== COMANDO ATTIVAZIONE ===")
    print(
        f'./venv/Scripts/python tools/scripts/activate_batch.py '
        f'--db both --ids "{ids_str}"'
    )

    conn.close()


if __name__ == "__main__":
    main()
