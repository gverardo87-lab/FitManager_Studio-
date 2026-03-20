"""
Popola porzioni standard per tutti gli alimenti attivi in nutrition.db.

Strategia a 2 livelli:
  1. Porzioni LARN per categoria (es. "1 porzione frutta = 150g")
  2. Override specifici per alimenti con porzioni naturali (es. "1 uovo = 60g")

Idempotente: non duplica porzioni gia' esistenti (check su alimento_id + nome).
Fonte: LARN 2014 (Livelli di Assunzione di Riferimento di Nutrienti),
       SINU (Societa' Italiana di Nutrizione Umana).

Uso: python -m tools.admin_scripts.populate_portions [--dry-run]
"""

import argparse
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")

# ══════════════════════════════════════════════════════════════
# PORZIONI STANDARD LARN PER CATEGORIA
# Ogni alimento della categoria riceve queste porzioni se non ne ha gia'
# ══════════════════════════════════════════════════════════════

CATEGORY_PORTIONS: dict[int, list[tuple[str, float]]] = {
    # Cereali e derivati (cat 1) — porzioni LARN: 80g pasta/riso secco
    1: [("1 porzione", 80), ("1/2 porzione", 40)],

    # Pasta/riso/cereali cotti (cat 2) — porzione cotta ~180-200g
    2: [("1 porzione cotta", 200), ("1/2 porzione cotta", 100)],

    # Pane e prodotti da forno (cat 3) — porzione LARN: 50g pane
    3: [("1 porzione", 50), ("2 porzioni", 100)],

    # Legumi (cat 4) — porzione LARN: 150g cotti, 50g secchi
    4: [("1 porzione", 150), ("1/2 porzione", 75)],

    # Verdure e ortaggi (cat 5) — porzione LARN: 200g (80g insalata)
    5: [("1 porzione", 200), ("1/2 porzione", 100)],

    # Frutta fresca (cat 6) — porzione LARN: 150g
    6: [("1 porzione", 150), ("1/2 porzione", 75)],

    # Frutta secca e semi (cat 7) — porzione LARN: 30g
    7: [("1 manciata", 30), ("2 manciate", 60)],

    # Carne e pollame (cat 8) — porzione LARN: 100g
    8: [("1 porzione", 100), ("1 porzione grande", 150)],

    # Salumi e affettati (cat 9) — porzione LARN: 50g
    9: [("1 porzione", 50), ("2 fette", 30)],

    # Prodotti ittici (cat 10) — porzione LARN: 150g
    10: [("1 porzione", 150), ("1 filetto", 200)],

    # Uova (cat 11) — porzione LARN: 1 uovo ~60g
    11: [("1 uovo", 60), ("2 uova", 120)],

    # Latte, yogurt e formaggi (cat 12) — porzione LARN: 125ml latte, 50g formaggio
    12: [("1 porzione", 125), ("1/2 porzione", 65)],

    # Oli e condimenti (cat 13) — porzione LARN: 10ml olio
    13: [("1 cucchiaio", 10), ("2 cucchiai", 20)],

    # Dolci e zuccheri (cat 14) — porzione variabile
    14: [("1 porzione", 30), ("1 cucchiaino", 5)],

    # Bevande e integratori (cat 15) — porzione standard: 200ml
    15: [("1 bicchiere", 200), ("1 tazza", 250)],

    # Primi piatti (cat 16) — porzione: 300-350g
    16: [("1 porzione", 350), ("1/2 porzione", 175)],

    # Secondi piatti (cat 17) — porzione: 200-250g
    17: [("1 porzione", 250), ("1/2 porzione", 125)],

    # Piatti unici e bowl (cat 18) — porzione: 350-400g
    18: [("1 porzione", 400), ("1/2 porzione", 200)],

    # Zuppe e minestre (cat 19) — porzione: 300ml
    19: [("1 piatto", 300), ("1/2 piatto", 150)],

    # Contorni composti (cat 20) — porzione: 150-200g
    20: [("1 porzione", 200), ("1/2 porzione", 100)],

    # Colazioni composte (cat 21) — porzione: 250-300g
    21: [("1 porzione", 300), ("1/2 porzione", 150)],
}

# ══════════════════════════════════════════════════════════════
# OVERRIDE SPECIFICI — alimenti con porzioni naturali
# Chiave: stringa che matcha l'inizio di Food.nome
# ══════════════════════════════════════════════════════════════

SPECIFIC_PORTIONS: dict[str, list[tuple[str, float]]] = {
    # === FRUTTA (unita' naturali) ===
    "Mela": [("1 mela media", 180), ("1 mela piccola", 130)],
    "Banana": [("1 banana media", 120), ("1 banana grande", 150)],
    "Arancia": [("1 arancia media", 200), ("1 arancia piccola", 130)],
    "Pera": [("1 pera media", 180)],
    "Pesca": [("1 pesca media", 170)],
    "Kiwi": [("1 kiwi", 80)],
    "Mandarino": [("1 mandarino", 80)],
    "Clementina": [("1 clementina", 60)],
    "Fico,": [("1 fico", 40), ("3 fichi", 120)],
    "Albicocca": [("1 albicocca", 40), ("3 albicocche", 120)],
    "Susina": [("1 susina", 50), ("3 susine", 150)],
    "Ciliegia": [("10 ciliegie", 80)],
    "Fragol": [("5-6 fragole", 100)],
    "Lamponi": [("1 coppetta", 125)],
    "More": [("1 coppetta", 125)],
    "Mirtilli": [("1 coppetta", 125)],
    "Anguria": [("1 fetta", 300)],
    "Cocomero": [("1 fetta", 300)],
    "Melone": [("1 fetta", 200)],
    "Ananas": [("1 fetta", 100), ("2 fette", 200)],
    "Avocado": [("1/2 avocado", 70), ("1 avocado", 140)],
    "Melograno": [("1/2 melograno", 90)],
    "Mango": [("1/2 mango", 100)],
    "Papaya": [("1 fetta", 140)],
    "Cocco": [("1 pezzo", 45)],

    # === FRUTTA SECCA (porzioni specifiche) ===
    "Mandorle": [("10 mandorle", 15), ("20 mandorle", 30)],
    "Noci,": [("3 noci", 15), ("6 noci", 30)],
    "Nocciole": [("10 nocciole", 15), ("20 nocciole", 30)],
    "Anacardi": [("10 anacardi", 15), ("1 manciata", 30)],
    "Pistacchi": [("20 pistacchi", 15), ("1 manciata", 30)],
    "Arachidi": [("20 arachidi", 20), ("1 manciata", 30)],
    "Datteri": [("1 dattero", 8), ("3 datteri", 24)],
    "Uvetta": [("1 cucchiaio", 15), ("1 manciata", 30)],
    "Prugne secche": [("3 prugne", 25)],
    "Fichi secchi": [("2 fichi", 30)],
    "Semi di chia": [("1 cucchiaio", 10)],
    "Semi di lino": [("1 cucchiaio", 10)],
    "Semi di zucca": [("1 cucchiaio", 10), ("1 manciata", 20)],
    "Semi di girasole": [("1 cucchiaio", 10), ("1 manciata", 20)],
    "Semi di sesamo": [("1 cucchiaino", 5), ("1 cucchiaio", 10)],

    # === PANE ===
    "Pane integrale": [("1 fetta", 30), ("2 fette", 60)],
    "Pane di segale": [("1 fetta", 30), ("2 fette", 60)],
    "Pane ciabatta": [("1 fetta", 40), ("1 panino", 80)],
    "Gallette": [("1 galletta", 8), ("3 gallette", 24)],
    "Fette biscottate": [("1 fetta", 10), ("3 fette", 30)],
    "Cracker": [("3 cracker", 25)],
    "Grissini": [("3 grissini", 20)],
    "Piadina": [("1 piadina", 100)],
    "Tortilla": [("1 tortilla", 40)],
    "Cornetto": [("1 cornetto", 50)],

    # === LATTICINI ===
    "Latte": [("1 bicchiere", 200), ("1 tazza", 250)],
    "Yogurt": [("1 vasetto", 125), ("1 vasetto grande", 170)],
    "Mozzarella": [("1 mozzarella", 125), ("1/2 mozzarella", 65)],
    "Ricotta": [("1 porzione", 100)],
    "Parmigiano": [("1 cucchiaio grattugiato", 10), ("1 scaglia", 20)],
    "Grana": [("1 cucchiaio grattugiato", 10), ("1 scaglia", 20)],
    "Burrata": [("1 burrata", 125)],
    "Stracchino": [("1 porzione", 50)],
    "Crescenza": [("1 porzione", 50)],
    "Mascarpone": [("1 cucchiaio", 30)],
    "Philadelphia": [("1 porzione", 25)],
    "Fiocchi di latte": [("1 porzione", 100)],
    "Burro": [("1 noce", 10), ("1 cucchiaino", 5)],
    "Panna": [("1 cucchiaio", 15)],

    # === UOVA ===
    "Uovo": [("1 uovo", 60), ("2 uova", 120)],
    "Albume": [("1 albume", 35), ("2 albumi", 70)],
    "Tuorlo": [("1 tuorlo", 18), ("2 tuorli", 36)],
    "Frittata": [("1 porzione", 150)],

    # === CARNE ===
    "Petto di pollo": [("1 petto", 200), ("1/2 petto", 100)],
    "Hamburger": [("1 hamburger", 100), ("1 hamburger grande", 150)],
    "Fegato": [("1 porzione", 100)],
    "Polpett": [("2 polpette", 100), ("3 polpette", 150)],
    "Scaloppin": [("1 porzione", 120)],
    "Salsiccia": [("1 salsiccia", 80), ("2 salsicce", 160)],

    # === SALUMI ===
    "Bresaola": [("4 fette", 30), ("6 fette", 50)],
    "Prosciutto crudo": [("3 fette", 30), ("5 fette", 50)],
    "Prosciutto cotto": [("2 fette", 40), ("3 fette", 60)],
    "Mortadella": [("2 fette", 40)],
    "Salame": [("4 fette", 30)],
    "Pancetta": [("2 fette", 20), ("3 fette", 30)],
    "Wurstel": [("1 wurstel", 40), ("2 wurstel", 80)],
    "Speck": [("3 fette", 30), ("5 fette", 50)],

    # === OLI ===
    "Olio": [("1 cucchiaio", 10), ("1 cucchiaino", 5)],
    "Aceto": [("1 cucchiaio", 10)],
    "Salsa di soia": [("1 cucchiaio", 15)],
    "Maionese": [("1 cucchiaio", 15)],
    "Ketchup": [("1 cucchiaio", 15)],
    "Senape": [("1 cucchiaino", 5)],
    "Miele": [("1 cucchiaino", 7), ("1 cucchiaio", 21)],
    "Zucchero": [("1 cucchiaino", 5), ("1 bustina", 7)],
    "Marmellata": [("1 cucchiaio", 20)],
    "Cioccolato": [("1 quadratino", 10), ("2 quadratini", 20)],
    "Cacao": [("1 cucchiaino", 5)],

    # === BEVANDE ===
    "Caffe": [("1 tazzina", 30)],
    "Caffè": [("1 tazzina", 30)],
    "Te ": [("1 tazza", 200)],
    "Tè ": [("1 tazza", 200)],
    "Succo": [("1 bicchiere", 200)],
    "Vino": [("1 calice", 125)],
    "Birra": [("1 bicchiere", 250), ("1 lattina", 330)],
    "Acqua": [("1 bicchiere", 200)],

    # === INTEGRATORI ===
    "Creatina": [("1 dose", 5)],
    "BCAA": [("1 dose", 5)],
    "Whey": [("1 misurino", 30)],
    "Proteine": [("1 misurino", 30)],
    "Maltodestrine": [("1 misurino", 30)],
}


def populate(db_path: str, dry_run: bool) -> dict:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Load all active foods
    c.execute("SELECT id, nome, categoria_id FROM alimenti WHERE is_active = 1 ORDER BY id")
    foods = c.fetchall()

    # Load existing portions to avoid duplicates
    c.execute("SELECT alimento_id, nome FROM porzioni_standard")
    existing = {(r[0], r[1]) for r in c.fetchall()}

    stats = {"inserted": 0, "skipped_dup": 0, "foods_covered": set()}

    for food_id, food_nome, cat_id in foods:
        portions_to_add: list[tuple[str, float]] = []

        # 1. Check specific overrides first
        matched_specific = False
        for pattern, portions in SPECIFIC_PORTIONS.items():
            if food_nome.startswith(pattern) or pattern.lower() in food_nome.lower():
                portions_to_add.extend(portions)
                matched_specific = True
                break

        # 2. Category defaults (only if no specific match)
        if not matched_specific:
            cat_portions = CATEGORY_PORTIONS.get(cat_id, [])
            portions_to_add.extend(cat_portions)

        # Insert non-duplicate portions
        for p_nome, p_grammi in portions_to_add:
            if (food_id, p_nome) in existing:
                stats["skipped_dup"] += 1
                continue

            if not dry_run:
                c.execute(
                    "INSERT INTO porzioni_standard (alimento_id, nome, grammi) VALUES (?, ?, ?)",
                    (food_id, p_nome, p_grammi),
                )
            stats["inserted"] += 1
            stats["foods_covered"].add(food_id)
            existing.add((food_id, p_nome))

    if not dry_run:
        conn.commit()

    # Count total coverage
    c.execute("SELECT COUNT(DISTINCT alimento_id) FROM porzioni_standard")
    stats["total_covered"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM porzioni_standard")
    stats["total_portions"] = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM alimenti WHERE is_active = 1")
    stats["total_foods"] = c.fetchone()[0]

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Popola porzioni standard LARN")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "ESEGUITO"
    stats = populate(DB_PATH, args.dry_run)

    print(f"\n{'=' * 60}")
    print(f"  Porzioni Standard LARN — {mode}")
    print(f"{'=' * 60}")
    print(f"  Porzioni inserite: {stats['inserted']}")
    print(f"  Duplicati skippati: {stats['skipped_dup']}")
    print(f"  Alimenti nuovi coperti: {len(stats['foods_covered'])}")
    print(f"  Totale porzioni DB: {stats['total_portions']}")
    print(f"  Copertura: {stats['total_covered']}/{stats['total_foods']} alimenti")
    print()


if __name__ == "__main__":
    main()
