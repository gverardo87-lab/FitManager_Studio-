"""
Genera CSV micronutrienti per latte, yogurt e formaggi (categoria 12).

Fonte: CREA 2019 IV ed. + USDA FoodData Central.
Valori per 100g di prodotto edibile.

Uso: python -m tools.admin_scripts.generate_dairy_csv
Output: data/nutrition/micronutrients_dairy.csv
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
OUT_PATH = os.path.join(BASE_DIR, "nutrition", "micronutrients_dairy.csv")


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
    # === LATTE VACCINO E VARIANTI ===
    "Latte intero UHT":
        _v(120, 0.1, 0.4, 11, 94, 150, 1.5, 37, 0.03, 0.07, 1, 0.04, 0.17, 0.1, 0.04, 5, 0.4, "high", "CREA 2019 latte intero"),

    # === LATTE DI ALTRI ANIMALI ===
    "Latte di capra, intero":
        _v(134, 0.1, 0.3, 14, 111, 204, 1.4, 57, 0.1, 0.04, 1.3, 0.05, 0.14, 0.3, 0.05, 1, 0.07, "high", "USDA FDC goat milk"),
    "Latte d'asina (equino)":
        _v(68, 0.3, 0.2, 7, 50, 64, 0.5, 2, 0.03, 0.05, 4.7, 0.04, 0.02, 0.2, 0.03, 5, 0.03, "medium", "USDA FDC donkey milk"),

    # === LATTE TRASFORMATO ===
    "Latte condensato zuccherato":
        _v(284, 0.2, 0.9, 26, 224, 371, 5.4, 100, 0.2, 0.16, 2.6, 0.06, 0.42, 0.2, 0.05, 11, 0.44, "high", "CREA 2019"),
    "Latte in polvere scremato":
        _v(1257, 0.3, 4.1, 110, 968, 1794, 27.3, 7, 0.2, 0.01, 5.6, 0.42, 1.55, 0.9, 0.36, 50, 4.03, "high", "USDA FDC nonfat dry milk"),

    # === LATTE FERMENTATO ===
    "Latte fermentato (kefir)":
        _v(130, 0.04, 0.5, 12, 100, 164, 3.6, 15, 0.1, 0.04, 0.2, 0.03, 0.17, 0.1, 0.06, 13, 0.3, "high", "USDA FDC kefir"),

    # === LATTE VEGETALE / DIVERSO ===
    "Latte di cocco (in lattina)":
        _v(16, 1.6, 0.7, 37, 100, 263, 6.2, 0, 0, 0.15, 2.8, 0.03, 0, 0.8, 0.03, 16, 0, "high", "USDA FDC coconut milk canned"),
    "Kefir di acqua (water kefir)":
        _v(5, 0.1, 0.05, 2, 3, 15, 0.1, 0, 0, 0, 0, 0.01, 0.01, 0.05, 0.01, 1, 0, "low", "stima: acqua fermentata, micronutrienti minimi"),

    # === YOGURT ===
    "Yogurt intero con frutta":
        _v(130, 0.1, 0.5, 12, 100, 165, 2.2, 12, 0.04, 0.03, 0.6, 0.04, 0.15, 0.1, 0.04, 8, 0.35, "high", "CREA 2019 yogurt frutta"),
    "Yogurt magro bianco":
        _v(140, 0.1, 0.6, 14, 116, 186, 3.3, 2, 0.01, 0.01, 0.7, 0.04, 0.2, 0.1, 0.05, 11, 0.45, "high", "CREA 2019 yogurt magro"),
    "Yogurt greco 2% grassi":
        _v(110, 0.1, 0.5, 11, 130, 141, 9.7, 5, 0.01, 0.03, 0, 0.02, 0.27, 0.2, 0.06, 7, 0.75, "high", "USDA FDC Greek yogurt lowfat"),
    "Yogurt greco proteico (15g prot/100g)":
        _v(120, 0.1, 0.6, 12, 150, 160, 10.0, 3, 0.01, 0.02, 0, 0.03, 0.30, 0.2, 0.07, 8, 0.80, "medium", "USDA FDC Greek yogurt high-protein"),
    "Yogurt di capra, intero":
        _v(170, 0.1, 0.4, 14, 120, 210, 1.7, 50, 0.1, 0.03, 1.2, 0.04, 0.14, 0.3, 0.05, 6, 0.1, "medium", "USDA FDC goat milk yogurt"),
    "Yogurt al frutto di bosco (magro)":
        _v(135, 0.1, 0.5, 13, 110, 175, 2.8, 2, 0.01, 0.01, 0.5, 0.04, 0.18, 0.1, 0.05, 10, 0.42, "medium", "CREA 2019 yogurt magro frutta"),
    "Ayran (bevanda yogurt turca)":
        _v(90, 0.05, 0.3, 8, 70, 110, 1.5, 10, 0.02, 0.02, 0.3, 0.03, 0.11, 0.07, 0.03, 5, 0.22, "medium", "USDA FDC ayran"),
    "Lassi dolce (bevanda yogurt indiana)":
        _v(80, 0.05, 0.3, 7, 65, 100, 1.2, 8, 0.02, 0.02, 0.3, 0.02, 0.10, 0.06, 0.03, 4, 0.20, "medium", "stima da yogurt diluito zuccherato"),

    # === FORMAGGI STAGIONATI / DURI ===
    "Parmigiano Reggiano DOP (grattugiato)":
        _v(1184, 0.8, 2.8, 44, 694, 92, 22.5, 207, 0.5, 0.22, 0, 0.04, 0.33, 0.1, 0.09, 7, 1.2, "high", "CREA 2019 parmigiano"),
    "Parmigiano Reggiano 24 mesi":
        _v(1160, 0.7, 2.8, 43, 680, 100, 22.0, 200, 0.5, 0.22, 0, 0.04, 0.33, 0.1, 0.09, 7, 1.2, "high", "CREA 2019 parmigiano"),
    "Grana Padano DOP":
        _v(1165, 0.6, 3.9, 63, 692, 120, 12.0, 224, 0.5, 0.28, 0, 0.02, 0.35, 0.06, 0.08, 10, 2.1, "high", "CREA 2019 grana padano"),
    "Pecorino romano DOP":
        _v(1064, 0.8, 3.6, 40, 760, 100, 15.0, 147, 0.5, 0.4, 0, 0.04, 0.37, 0.1, 0.09, 5, 1.5, "high", "CREA 2019 pecorino romano"),
    "Pecorino stagionato":
        _v(950, 0.7, 3.3, 38, 700, 95, 14.5, 180, 0.5, 0.35, 0, 0.04, 0.35, 0.1, 0.08, 5, 1.4, "high", "CREA 2019 pecorino"),
    "Pecorino di Pienza":
        _v(900, 0.6, 3.2, 36, 680, 90, 14.0, 170, 0.5, 0.33, 0, 0.04, 0.34, 0.1, 0.08, 5, 1.3, "medium", "CREA 2019 pecorino"),
    "Caciocavallo podolico stagionato":
        _v(860, 0.5, 3.0, 35, 660, 85, 12.0, 240, 0.5, 0.30, 0, 0.03, 0.30, 0.1, 0.07, 6, 1.5, "medium", "CREA 2019 caciocavallo"),

    # === FORMAGGI SEMI-STAGIONATI ===
    "Emmenthal (Emmentaler)":
        _v(970, 0.3, 3.9, 33, 636, 119, 14.5, 265, 0.5, 0.56, 0, 0.04, 0.37, 0.04, 0.08, 10, 3.06, "high", "CREA 2019 emmenthal"),
    "Fontina DOP":
        _v(700, 0.3, 3.4, 17, 466, 64, 14.5, 261, 0.6, 0.55, 0, 0.03, 0.29, 0.1, 0.08, 6, 1.7, "high", "CREA 2019 fontina"),
    "Provolone":
        _v(756, 0.5, 3.2, 28, 496, 138, 14.5, 233, 0.5, 0.28, 0, 0.02, 0.32, 0.2, 0.07, 10, 1.46, "high", "USDA FDC provolone"),
    "Asiago pressato (fresco)":
        _v(700, 0.3, 3.0, 30, 480, 90, 12.0, 200, 0.4, 0.30, 0, 0.03, 0.28, 0.1, 0.07, 8, 1.5, "medium", "CREA 2019 asiago"),
    "Asiago d'allevo (stagionato)":
        _v(850, 0.4, 3.5, 35, 600, 95, 14.0, 240, 0.5, 0.35, 0, 0.03, 0.32, 0.1, 0.08, 7, 1.8, "medium", "CREA 2019 asiago stagionato"),
    "Montasio DOP":
        _v(770, 0.3, 3.3, 32, 520, 88, 13.0, 230, 0.5, 0.32, 0, 0.03, 0.30, 0.1, 0.07, 8, 1.6, "medium", "CREA 2019 montasio"),
    "Scamorza affumicata":
        _v(575, 0.3, 2.8, 20, 410, 70, 10.0, 180, 0.3, 0.25, 0, 0.02, 0.25, 0.1, 0.06, 7, 1.3, "medium", "CREA 2019 scamorza"),
    "Caciotta toscana":
        _v(620, 0.3, 2.7, 25, 430, 80, 11.0, 200, 0.4, 0.28, 0, 0.03, 0.27, 0.1, 0.06, 7, 1.4, "medium", "CREA 2019 caciotta"),
    "Caciotta fresca (tipo formaggella)":
        _v(480, 0.3, 2.2, 20, 360, 75, 9.0, 160, 0.3, 0.22, 0, 0.03, 0.24, 0.1, 0.05, 8, 1.1, "medium", "CREA 2019 caciotta fresca"),
    "Mozzarella affumicata":
        _v(505, 0.3, 2.5, 18, 380, 68, 9.5, 170, 0.3, 0.23, 0, 0.02, 0.24, 0.1, 0.05, 7, 1.2, "medium", "CREA 2019 mozzarella affum."),
    "Feta DOP":
        _v(493, 0.7, 2.9, 19, 337, 62, 15.0, 125, 0.4, 0.18, 0, 0.15, 0.84, 1.0, 0.42, 32, 1.69, "high", "USDA FDC feta"),
    "Halloumi (cipriota)":
        _v(700, 0.3, 3.0, 22, 420, 100, 12.0, 150, 0.3, 0.20, 0, 0.03, 0.28, 0.1, 0.07, 10, 1.4, "medium", "USDA FDC halloumi"),

    # === FORMAGGI MOLLI / ERBORINATI ===
    "Gorgonzola DOP":
        _v(528, 0.3, 2.7, 23, 387, 256, 14.5, 228, 0.5, 0.25, 0, 0.03, 0.38, 1.0, 0.17, 36, 1.22, "high", "USDA FDC blue cheese"),
    "Taleggio DOP":
        _v(433, 0.3, 2.4, 18, 328, 89, 14.5, 260, 0.5, 0.35, 0, 0.02, 0.34, 0.1, 0.07, 18, 1.5, "high", "CREA 2019 taleggio"),
    "Brie":
        _v(184, 0.5, 2.4, 20, 188, 152, 14.5, 174, 0.5, 0.24, 0, 0.07, 0.52, 0.4, 0.24, 65, 1.65, "high", "USDA FDC brie"),
    "Camembert":
        _v(388, 0.3, 2.4, 20, 347, 187, 14.5, 240, 0.4, 0.21, 0, 0.03, 0.49, 0.6, 0.23, 62, 1.3, "high", "USDA FDC camembert"),

    # === FORMAGGI FRESCHI ===
    "Ricotta di pecora":
        _v(160, 0.4, 1.2, 11, 140, 100, 3.5, 120, 0.3, 0.15, 0, 0.02, 0.18, 0.1, 0.03, 12, 0.5, "high", "CREA 2019 ricotta pecora"),
    "Ricotta vaccina (light < 8%g)":
        _v(207, 0.4, 1.2, 11, 158, 105, 14.5, 44, 0.2, 0.05, 0, 0.01, 0.19, 0.1, 0.02, 12, 0.34, "high", "USDA FDC ricotta part-skim"),
    "Ricotta al forno (siciliana)":
        _v(250, 0.5, 1.5, 13, 180, 110, 6.0, 90, 0.3, 0.12, 0, 0.02, 0.20, 0.1, 0.03, 10, 0.5, "medium", "CREA 2019 ricotta al forno stima"),
    "Mascarpone":
        _v(68, 0.1, 0.4, 4, 50, 40, 1.0, 300, 0.2, 0.70, 0, 0.01, 0.06, 0.04, 0.01, 4, 0.15, "high", "CREA 2019 mascarpone"),
    "Burrata":
        _v(300, 0.2, 1.8, 14, 200, 70, 7.0, 150, 0.3, 0.20, 0, 0.02, 0.22, 0.1, 0.04, 8, 0.8, "medium", "USDA FDC burrata"),
    "Crescenza (stracchino)":
        _v(295, 0.1, 1.7, 10, 200, 65, 7.0, 230, 0.3, 0.20, 0, 0.02, 0.20, 0.2, 0.04, 18, 0.6, "high", "CREA 2019 crescenza"),
    "Stracchino (crescenza fresca)":
        _v(295, 0.1, 1.7, 10, 200, 65, 7.0, 230, 0.3, 0.20, 0, 0.02, 0.20, 0.2, 0.04, 18, 0.6, "high", "CREA 2019 crescenza"),
    "Robiola":
        _v(180, 0.2, 1.3, 9, 150, 60, 5.0, 160, 0.3, 0.18, 0, 0.02, 0.19, 0.15, 0.03, 15, 0.5, "medium", "CREA 2019 robiola"),
    "Squacquerone di Romagna DOP":
        _v(270, 0.1, 1.5, 9, 180, 60, 6.0, 200, 0.3, 0.18, 0, 0.02, 0.19, 0.15, 0.04, 16, 0.55, "medium", "CREA 2019 stima crescenza"),
    "Formaggio spalmabile (tipo Philadelphia)":
        _v(98, 0.1, 0.5, 9, 104, 119, 2.4, 250, 0.2, 0.20, 0, 0.02, 0.12, 0.1, 0.03, 13, 0.3, "high", "USDA FDC cream cheese"),
    "Quark (fiocchi proteici 0.2%)":
        _v(86, 0.1, 0.5, 9, 160, 105, 9.7, 3, 0.01, 0.01, 0, 0.02, 0.22, 0.2, 0.05, 17, 0.5, "high", "USDA FDC quark"),

    # === PANNA E BURRO ===
    "Panna da cucina (18% grassi)":
        _v(96, 0.04, 0.3, 8, 74, 122, 0.9, 140, 0.1, 0.35, 0.6, 0.03, 0.12, 0.07, 0.03, 4, 0.17, "high", "USDA FDC light cream"),
    "Panna fresca (35% grassi)":
        _v(65, 0.03, 0.2, 6, 54, 75, 0.4, 411, 0.1, 1.06, 0.6, 0.02, 0.10, 0.04, 0.02, 3, 0.17, "high", "USDA FDC heavy cream"),
    "Panna acida (sour cream)":
        _v(100, 0.06, 0.3, 8, 71, 115, 1.6, 150, 0.1, 0.45, 0.7, 0.02, 0.11, 0.06, 0.02, 9, 0.18, "high", "USDA FDC sour cream"),
    "Burro di cacao (cosmesi/food)":
        _v(0, 0.02, 0, 0, 0, 0, 0, 0, 0, 1.8, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC cocoa butter"),

    # === ALTRO ===
    "Gelato proteico (alto prot, basso grassi)":
        _v(150, 0.2, 0.6, 15, 120, 180, 3.0, 20, 0.1, 0.10, 0, 0.04, 0.20, 0.1, 0.04, 8, 0.40, "low", "stima da gelato proteico commerciale"),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, nome FROM alimenti
        WHERE categoria_id = 12 AND calcio_mg IS NULL ORDER BY nome
    """)
    foods = c.fetchall()
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

        for vid, vnome in foods:
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
    print(f"  Matchati: {matched}/{len(foods)}")
    print(f"  Non matchati: {len(unmatched)}")
    if unmatched:
        for uid, uname in unmatched:
            print(f"    {uid:4d} | {uname}")


if __name__ == "__main__":
    main()
