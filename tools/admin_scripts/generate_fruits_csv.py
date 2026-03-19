"""
Genera CSV micronutrienti per frutta fresca (categoria 6).

Fonte: CREA 2019 IV ed. + USDA FoodData Central.
Valori per 100g di prodotto edibile.

Uso: python -m tools.admin_scripts.generate_fruits_csv
Output: data/nutrition/micronutrients_fruits.csv
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
OUT_PATH = os.path.join(BASE_DIR, "nutrition", "micronutrients_fruits.csv")


def _v(ca, fe, zn, mg, p, k, se, va, vd, ve, vc, b1, b2, b3, b6, b9, b12, conf, src):
    return {
        "calcio_mg": ca, "ferro_mg": fe, "zinco_mg": zn, "magnesio_mg": mg,
        "fosforo_mg": p, "potassio_mg": k, "selenio_ug": se,
        "vitamina_a_ug": va, "vitamina_d_ug": vd, "vitamina_e_mg": ve,
        "vitamina_c_mg": vc, "vitamina_b1_mg": b1, "vitamina_b2_mg": b2,
        "vitamina_b3_mg": b3, "vitamina_b6_mg": b6, "vitamina_b9_ug": b9,
        "vitamina_b12_ug": b12, "confidence": conf, "source_detail": src,
    }


CREA = {
    # === AGRUMI ===
    "Cedro":          _v(34, 0.4, 0.1, 8, 16, 123, 0.4, 1, 0, 0.15, 38, 0.04, 0.02, 0.2, 0.06, 11, 0, "high", "CREA 2019"),
    "Clementina":     _v(30, 0.1, 0.1, 11, 21, 130, 0.1, 12, 0, 0.2, 48.8, 0.09, 0.03, 0.4, 0.06, 24, 0, "high", "CREA 2019"),
    "Lime":           _v(33, 0.6, 0.1, 6, 18, 102, 0.4, 2, 0, 0.22, 29.1, 0.03, 0.02, 0.2, 0.04, 8, 0, "high", "USDA FDC"),
    "Pompelmo rosa":  _v(22, 0.1, 0.1, 9, 18, 135, 0.1, 46, 0, 0.13, 31.2, 0.04, 0.02, 0.2, 0.04, 13, 0, "high", "USDA FDC"),

    # === FRUTTI ROSSI / BACCHE ===
    "Ciliegia":       _v(13, 0.4, 0.1, 11, 21, 222, 0, 3, 0, 0.07, 7, 0.03, 0.03, 0.2, 0.05, 4, 0, "high", "CREA 2019"),
    "Fragoline di bosco": _v(26, 0.7, 0.2, 13, 24, 160, 0.4, 1, 0, 0.29, 58, 0.02, 0.02, 0.4, 0.05, 24, 0, "medium", "CREA 2019 fragola"),
    "Lamponi":        _v(25, 0.7, 0.4, 22, 29, 151, 0.2, 2, 0, 0.87, 26.2, 0.03, 0.04, 0.6, 0.06, 21, 0, "high", "USDA FDC"),
    "Mirtilli rossi": _v(8, 0.3, 0.1, 6, 13, 85, 0.1, 3, 0, 1.2, 13.3, 0.01, 0.02, 0.1, 0.06, 1, 0, "high", "USDA FDC cranberries"),
    "Mora di gelso":  _v(39, 1.9, 0.1, 18, 38, 194, 0.6, 1, 0, 0.87, 36.4, 0.03, 0.1, 0.6, 0.05, 6, 0, "high", "USDA FDC mulberry"),
    "More":           _v(29, 0.6, 0.5, 20, 22, 162, 0.4, 11, 0, 1.17, 21, 0.02, 0.03, 0.6, 0.03, 25, 0, "high", "USDA FDC blackberry"),
    "Ribes nero":     _v(55, 1.5, 0.3, 24, 59, 322, 0, 12, 0, 1.0, 181, 0.05, 0.05, 0.3, 0.07, 0, 0, "high", "CREA 2019"),
    "Ribes rosso":    _v(33, 1.0, 0.2, 13, 44, 275, 0.6, 2, 0, 0.1, 41, 0.04, 0.03, 0.1, 0.07, 8, 0, "high", "CREA 2019"),
    "Ribes nero (succo)": _v(30, 0.8, 0.2, 15, 35, 200, 0, 8, 0, 0.7, 80, 0.03, 0.04, 0.2, 0.05, 0, 0, "medium", "CREA 2019 ribes nero"),
    "Uva spina":      _v(25, 0.3, 0.1, 10, 27, 198, 0.6, 15, 0, 0.37, 27.7, 0.04, 0.03, 0.3, 0.08, 6, 0, "high", "CREA 2019"),
    "Bacche di aronia": _v(30, 0.6, 0.5, 16, 23, 162, 0.4, 6, 0, 1.2, 21, 0.02, 0.02, 0.3, 0.03, 25, 0, "medium", "USDA FDC chokeberry"),
    "Bacche di acai":  _v(260, 4.4, 0.7, 174, 124, 535, 0, 6, 0, 0, 0, 0.11, 0.14, 0.4, 0.09, 0, 0, "medium", "USDA FDC acai powder"),
    "Bacche di goji":  _v(190, 6.8, 2.0, 112, 203, 1132, 50, 1341, 0, 0, 48.4, 0.15, 1.3, 4.3, 0.75, 0, 0, "high", "USDA FDC goji dried"),

    # === POMACEE E DRUPACEE ===
    "Fico":           _v(35, 0.4, 0.2, 17, 14, 232, 0.2, 7, 0, 0.11, 2, 0.06, 0.05, 0.4, 0.11, 6, 0, "high", "CREA 2019"),
    "Fico d'India":   _v(56, 0.3, 0.1, 85, 24, 220, 0.6, 2, 0, 0.01, 14, 0.01, 0.06, 0.5, 0.06, 6, 0, "high", "CREA 2019"),
    "Kaki":           _v(8, 0.2, 0.1, 9, 17, 161, 0.6, 81, 0, 0.73, 7.5, 0.03, 0.02, 0.1, 0.1, 8, 0, "high", "CREA 2019"),
    "Mela cotogna":   _v(11, 0.7, 0.04, 8, 17, 197, 0.6, 2, 0, 0.55, 15, 0.02, 0.03, 0.2, 0.04, 3, 0, "high", "CREA 2019"),
    "Mela rossa (Fuji)": _v(6, 0.1, 0.04, 5, 11, 107, 0, 3, 0, 0.18, 4.6, 0.02, 0.03, 0.1, 0.04, 3, 0, "high", "USDA FDC apple"),
    "Mela verde (Granny Smith)": _v(6, 0.1, 0.04, 5, 11, 107, 0, 3, 0, 0.18, 4.6, 0.02, 0.03, 0.1, 0.04, 3, 0, "high", "USDA FDC apple"),
    "Nespola":        _v(16, 0.3, 0.1, 13, 27, 266, 0.6, 76, 0, 0.89, 1, 0.02, 0.02, 0.2, 0.1, 14, 0, "high", "CREA 2019"),
    "Nettarina":      _v(6, 0.3, 0.2, 9, 26, 201, 0, 17, 0, 0.77, 5.4, 0.03, 0.03, 1.1, 0.03, 5, 0, "high", "CREA 2019"),
    "Pera Williams":  _v(9, 0.2, 0.1, 7, 12, 116, 0.1, 1, 0, 0.12, 4.3, 0.01, 0.03, 0.2, 0.03, 7, 0, "high", "CREA 2019 pera"),
    "Pera abate":     _v(9, 0.2, 0.1, 7, 12, 116, 0.1, 1, 0, 0.12, 4.3, 0.01, 0.03, 0.2, 0.03, 7, 0, "medium", "CREA 2019 pera"),
    "Pesca bianca":   _v(6, 0.3, 0.2, 9, 20, 190, 0.1, 16, 0, 0.73, 6.6, 0.02, 0.03, 0.8, 0.03, 4, 0, "high", "CREA 2019 pesca"),
    "Pesca tabacchiera": _v(6, 0.3, 0.2, 9, 20, 190, 0.1, 16, 0, 0.73, 6.6, 0.02, 0.03, 0.8, 0.03, 4, 0, "medium", "CREA 2019 pesca"),
    "Susina (prugna)": _v(6, 0.2, 0.1, 7, 16, 157, 0, 17, 0, 0.26, 9.5, 0.03, 0.03, 0.4, 0.03, 5, 0, "high", "CREA 2019"),
    "Corbezzolo":     _v(30, 0.5, 0.1, 10, 20, 180, 0.3, 5, 0, 0.3, 15, 0.03, 0.03, 0.3, 0.05, 10, 0, "medium", "CREA 2019 stima"),
    "Melograno, semi": _v(10, 0.3, 0.4, 12, 36, 236, 0.5, 0, 0, 0.6, 10.2, 0.07, 0.05, 0.3, 0.08, 38, 0, "high", "USDA FDC pomegranate"),
    "Melograno, succo": _v(11, 0.1, 0.1, 7, 11, 214, 0.3, 0, 0, 0.38, 0.1, 0.02, 0.01, 0.2, 0.04, 24, 0, "high", "USDA FDC pomegranate juice"),

    # === TROPICALI ===
    "Cocco, polpa":   _v(14, 2.4, 1.1, 32, 113, 356, 10.1, 0, 0, 0.24, 3.3, 0.07, 0.02, 0.5, 0.05, 26, 0, "high", "USDA FDC coconut"),
    "Guava":          _v(18, 0.3, 0.2, 22, 40, 417, 0.6, 31, 0, 0.73, 228, 0.07, 0.04, 1.1, 0.11, 49, 0, "high", "USDA FDC"),
    "Lychee":         _v(5, 0.3, 0.1, 10, 31, 171, 0.6, 0, 0, 0.07, 71.5, 0.01, 0.07, 0.6, 0.1, 14, 0, "high", "USDA FDC"),
    "Mango":          _v(11, 0.2, 0.1, 10, 14, 168, 0.6, 54, 0, 0.9, 36.4, 0.03, 0.04, 0.7, 0.12, 43, 0, "high", "USDA FDC"),
    "Maracuja":       _v(12, 1.6, 0.1, 29, 68, 348, 0.6, 64, 0, 0.02, 30, 0, 0.13, 1.5, 0.1, 14, 0, "high", "USDA FDC passion fruit"),
    "Papaya":         _v(20, 0.3, 0.1, 21, 10, 182, 0.6, 47, 0, 0.3, 60.9, 0.02, 0.03, 0.4, 0.04, 37, 0, "high", "USDA FDC"),
    "Carambola":      _v(3, 0.1, 0.1, 10, 12, 133, 0.6, 1, 0, 0.15, 34.4, 0.01, 0.02, 0.4, 0.02, 12, 0, "high", "USDA FDC starfruit"),
    "Banana plantano": _v(3, 0.6, 0.1, 37, 34, 499, 1.5, 56, 0, 0.14, 18.4, 0.05, 0.05, 0.7, 0.3, 22, 0, "high", "USDA FDC plantain cooked"),
    "Cocomero (anguria)": _v(7, 0.2, 0.1, 10, 11, 112, 0.4, 28, 0, 0.05, 8.1, 0.03, 0.02, 0.2, 0.05, 3, 0, "high", "CREA 2019"),
    "Melone cantalupo": _v(9, 0.2, 0.2, 12, 15, 267, 0.4, 169, 0, 0.05, 36.7, 0.04, 0.02, 0.7, 0.07, 21, 0, "high", "CREA 2019"),
    "Giuggiola":      _v(21, 0.5, 0.1, 10, 23, 250, 0, 2, 0, 0, 69, 0.02, 0.04, 0.9, 0.08, 0, 0, "high", "CREA 2019"),
    "Giuggiola fresca tipo cinese": _v(21, 0.5, 0.1, 10, 23, 250, 0, 2, 0, 0, 69, 0.02, 0.04, 0.9, 0.08, 0, 0, "medium", "CREA 2019 giuggiola"),

    # === FRUTTA SECCA / ESSICCATA ===
    "Albicocche secche": _v(55, 2.7, 0.4, 32, 71, 1162, 2.2, 180, 0, 4.33, 1, 0.02, 0.07, 2.6, 0.14, 10, 0, "high", "USDA FDC"),
    "Banana, essiccata": _v(22, 1.2, 0.5, 108, 74, 1491, 3.9, 4, 0, 0.3, 7, 0.18, 0.24, 2.8, 0.44, 14, 0, "high", "USDA FDC banana chips"),
    "Datteri secchi":  _v(64, 0.9, 0.4, 54, 62, 696, 3, 7, 0, 0.05, 0, 0.05, 0.07, 1.6, 0.25, 15, 0, "high", "USDA FDC"),
    "Fichi secchi":    _v(162, 2.0, 0.5, 68, 67, 680, 0.6, 0, 0, 0.35, 1.2, 0.09, 0.08, 0.6, 0.11, 9, 0, "high", "CREA 2019"),
    "Prugne secche":   _v(43, 0.9, 0.4, 41, 69, 732, 0.3, 39, 0, 0.43, 0.6, 0.05, 0.19, 1.9, 0.21, 4, 0, "high", "USDA FDC"),
    "Uvetta sultanina": _v(50, 1.9, 0.3, 32, 101, 749, 0.7, 0, 0, 0.12, 2.3, 0.11, 0.08, 0.8, 0.17, 5, 0, "high", "CREA 2019"),
    "Ananas essiccato": _v(25, 0.5, 0.1, 20, 10, 150, 0.1, 3, 0, 0.02, 15, 0.08, 0.03, 0.4, 0.11, 10, 0, "medium", "USDA FDC dried pineapple"),
    "Mango essiccato":  _v(20, 0.5, 0.1, 18, 20, 280, 0.3, 40, 0, 0.7, 10, 0.04, 0.05, 0.8, 0.13, 30, 0, "medium", "USDA FDC dried mango"),
    "Papaya essiccata": _v(30, 0.6, 0.1, 15, 15, 200, 0.3, 35, 0, 0.25, 20, 0.03, 0.04, 0.5, 0.05, 25, 0, "medium", "USDA FDC dried papaya"),
    "Kaki essiccato":  _v(27, 0.8, 0.2, 18, 30, 310, 1.0, 120, 0, 0.5, 3, 0.04, 0.03, 0.2, 0.15, 12, 0, "medium", "USDA FDC dried persimmon"),
    "Carambola essiccata": _v(5, 0.2, 0.1, 12, 15, 160, 0.5, 1, 0, 0.1, 20, 0.01, 0.02, 0.3, 0.02, 8, 0, "low", "stima da carambola fresca"),
    "Giuggiole secche": _v(79, 1.8, 0.3, 37, 100, 531, 0, 2, 0, 0, 13, 0.05, 0.04, 0.9, 0.15, 0, 0, "high", "USDA FDC dried jujube"),
    "Kiwi giallo (golden)": _v(20, 0.2, 0.1, 12, 29, 315, 0.4, 2, 0, 1.4, 161, 0, 0.07, 0.3, 0.08, 31, 0, "high", "USDA FDC gold kiwi"),
    "Kiwi verde":     _v(34, 0.3, 0.1, 17, 34, 312, 0.2, 4, 0, 1.46, 92.7, 0.03, 0.03, 0.3, 0.06, 25, 0, "high", "CREA 2019 kiwi"),
    "Litchi essiccato": _v(33, 1.7, 0.3, 42, 150, 658, 1.1, 0, 0, 0.5, 183, 0.05, 0.21, 3.0, 0.17, 25, 0, "high", "USDA FDC dried lychee"),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, nome FROM alimenti
        WHERE categoria_id = 6 AND calcio_mg IS NULL ORDER BY nome
    """)
    fruits = c.fetchall()
    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    header = [
        "id", "nome", "calcio_mg", "ferro_mg", "zinco_mg", "magnesio_mg", "fosforo_mg",
        "potassio_mg", "selenio_ug", "vitamina_a_ug", "vitamina_d_ug", "vitamina_e_mg",
        "vitamina_c_mg", "vitamina_b1_mg", "vitamina_b2_mg", "vitamina_b3_mg",
        "vitamina_b6_mg", "vitamina_b9_ug", "vitamina_b12_ug", "confidence", "source_detail",
    ]

    matched = 0
    unmatched = []

    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for vid, vnome in fruits:
            match = None
            for key, data in CREA.items():
                if vnome == key or vnome.startswith(key):
                    match = data
                    break
            if not match:
                for key, data in CREA.items():
                    if key.lower() in vnome.lower():
                        match = data
                        break

            if match:
                writer.writerow([
                    vid, vnome,
                    match["calcio_mg"], match["ferro_mg"], match["zinco_mg"],
                    match["magnesio_mg"], match["fosforo_mg"], match["potassio_mg"],
                    match["selenio_ug"], match["vitamina_a_ug"], match["vitamina_d_ug"],
                    match["vitamina_e_mg"], match["vitamina_c_mg"], match["vitamina_b1_mg"],
                    match["vitamina_b2_mg"], match["vitamina_b3_mg"], match["vitamina_b6_mg"],
                    match["vitamina_b9_ug"], match["vitamina_b12_ug"],
                    match["confidence"], match["source_detail"],
                ])
                matched += 1
            else:
                unmatched.append((vid, vnome))

    print(f"CSV generato: {OUT_PATH}")
    print(f"  Matchati: {matched}/{len(fruits)}")
    print(f"  Non matchati: {len(unmatched)}")
    if unmatched:
        for uid, uname in unmatched:
            print(f"    {uid:4d} | {uname}")


if __name__ == "__main__":
    main()
