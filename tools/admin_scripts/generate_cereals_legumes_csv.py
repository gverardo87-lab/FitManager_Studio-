"""
Genera CSV micronutrienti per cereali, pasta/riso, pane e legumi (categorie 1-4).

Fonte: CREA 2019 IV ed. + USDA FoodData Central.
Valori per 100g di prodotto edibile.

Uso: python -m tools.admin_scripts.generate_cereals_legumes_csv
Output: data/nutrition/micronutrients_cereals_legumes.csv
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
OUT_PATH = os.path.join(BASE_DIR, "nutrition", "micronutrients_cereals_legumes.csv")


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
    # =====================================================================
    # CATEGORIA 1 — Cereali e derivati (44 alimenti)
    # =====================================================================

    # --- Cereali crudi / chicchi ---
    "Amaranto, crudo":                      _v(159, 7.6, 2.9, 248, 557, 508, 18.7, 0, 0, 1.19, 4.2, 0.12, 0.2, 0.9, 0.59, 82, 0, "high", "USDA FDC amaranth grain"),
    "Farro spelta, chicchi crudi":          _v(27, 4.4, 3.3, 136, 401, 388, 11.7, 0, 0, 0.79, 0, 0.36, 0.11, 6.8, 0.23, 45, 0, "high", "USDA FDC spelt uncooked"),
    "Kamut (grano khorasan), crudo":        _v(22, 3.8, 3.7, 130, 364, 403, 81.3, 0, 0, 0.6, 0, 0.45, 0.12, 6.4, 0.25, 38, 0, "high", "USDA FDC kamut grain"),
    "Miglio, crudo":                        _v(8, 3.0, 1.7, 114, 285, 195, 2.7, 0, 0, 0.05, 0, 0.42, 0.29, 4.7, 0.38, 85, 0, "high", "USDA FDC millet raw"),
    "Orzo mondo (integrale), crudo":        _v(33, 3.6, 2.8, 133, 264, 452, 37.7, 1, 0, 0.57, 0, 0.65, 0.29, 4.6, 0.32, 19, 0, "high", "USDA FDC barley hulled"),
    "Segale, farina integrale":             _v(24, 2.6, 2.7, 110, 332, 510, 35.3, 0, 0, 0.96, 0, 0.32, 0.25, 4.3, 0.29, 38, 0, "high", "USDA FDC rye flour dark"),
    "Sorgo, crudo":                         _v(28, 4.4, 1.7, 165, 287, 350, 12.2, 0, 0, 0.5, 0, 0.24, 0.14, 2.9, 0.44, 20, 0, "high", "USDA FDC sorghum grain"),
    "Teff, crudo":                          _v(180, 7.6, 3.6, 184, 429, 427, 4.4, 0, 0, 0.08, 0, 0.39, 0.27, 3.4, 0.48, 0, 0, "high", "USDA FDC teff grain"),
    "Triticale, crudo":                     _v(37, 2.6, 3.5, 130, 358, 332, 1.2, 0, 0, 0.9, 0, 0.42, 0.13, 1.3, 0.14, 73, 0, "high", "USDA FDC triticale"),

    # --- Crusca e germe ---
    "Crusca di frumento":                   _v(73, 10.6, 7.3, 611, 1013, 1182, 77.6, 0, 0, 1.49, 0, 0.52, 0.58, 13.6, 1.3, 79, 0, "high", "CREA 2019"),
    "Crusca d'avena":                       _v(58, 5.4, 3.1, 235, 734, 566, 45.2, 0, 0, 1.01, 0, 1.17, 0.22, 0.9, 0.17, 52, 0, "high", "USDA FDC oat bran"),
    "Germe di grano":                       _v(39, 6.3, 12.3, 239, 842, 892, 79.2, 0, 0, 15.0, 0, 1.88, 0.5, 6.8, 1.3, 281, 0, "high", "CREA 2019"),

    # --- Fiocchi ---
    "Fiocchi di farro":                     _v(25, 3.6, 2.8, 120, 340, 350, 10, 0, 0, 0.6, 0, 0.3, 0.1, 5.5, 0.2, 38, 0, "medium", "CREA 2019 farro"),
    "Fiocchi di orzo":                      _v(30, 3.0, 2.3, 115, 230, 400, 30, 0, 0, 0.5, 0, 0.55, 0.25, 4.0, 0.28, 16, 0, "medium", "CREA 2019 orzo"),
    "Fiocchi di quinoa":                    _v(47, 4.6, 3.1, 197, 457, 563, 8.5, 1, 0, 2.44, 0, 0.36, 0.32, 1.5, 0.49, 184, 0, "high", "USDA FDC quinoa"),
    "Fiocchi di segale":                    _v(24, 2.6, 2.7, 110, 332, 510, 35, 0, 0, 0.96, 0, 0.32, 0.25, 4.3, 0.29, 38, 0, "medium", "CREA 2019 segale"),

    # --- Farine ---
    "Frumento tenero, farina 00":           _v(15, 0.7, 0.6, 17, 76, 108, 10.7, 0, 0, 0.06, 0, 0.1, 0.03, 1.0, 0.04, 22, 0, "high", "CREA 2019"),
    "Frumento tenero, farina 0":            _v(17, 1.0, 0.8, 22, 100, 126, 12, 0, 0, 0.1, 0, 0.14, 0.04, 1.5, 0.06, 28, 0, "high", "CREA 2019"),
    "Frumento tenero, farina 1":            _v(20, 1.4, 1.0, 35, 140, 160, 15, 0, 0, 0.2, 0, 0.22, 0.06, 2.2, 0.1, 33, 0, "high", "CREA 2019"),
    "Frumento tenero, farina 2 (semintegrale)": _v(25, 2.0, 1.5, 55, 200, 230, 20, 0, 0, 0.4, 0, 0.3, 0.1, 3.5, 0.15, 40, 0, "high", "CREA 2019"),
    "Frumento tenero, farina integrale":    _v(34, 3.9, 2.9, 138, 357, 405, 61.8, 0, 0, 0.71, 0, 0.5, 0.17, 6.4, 0.41, 44, 0, "high", "CREA 2019"),
    "Frumento duro, semola":                _v(17, 1.2, 1.0, 47, 136, 186, 63.2, 0, 0, 0.5, 0, 0.28, 0.1, 3.1, 0.1, 72, 0, "high", "CREA 2019"),
    "Farina di castagne":                   _v(50, 2.9, 0.8, 74, 131, 847, 1.2, 1, 0, 0.5, 0, 0.24, 0.38, 1.1, 0.41, 70, 0, "high", "CREA 2019"),
    "Farina di ceci":                       _v(45, 4.9, 2.8, 166, 318, 846, 8.3, 3, 0, 0.8, 0, 0.49, 0.1, 1.6, 0.49, 437, 0, "high", "USDA FDC chickpea flour"),
    "Farina di cocco":                      _v(26, 3.6, 2.0, 90, 196, 660, 14.3, 0, 0, 0.7, 1, 0.05, 0.1, 0.5, 0.3, 20, 0, "high", "USDA FDC coconut flour"),
    "Farina di grano saraceno":             _v(41, 4.1, 3.1, 251, 337, 577, 5.7, 0, 0, 0.32, 0, 0.42, 0.19, 6.2, 0.58, 54, 0, "high", "USDA FDC buckwheat flour"),
    "Farina di lupini":                     _v(176, 4.4, 4.8, 198, 440, 1013, 8.2, 1, 0, 0.5, 4.8, 0.6, 0.22, 2.0, 0.36, 355, 0, "high", "USDA FDC lupin flour"),
    "Farina di mais (maizena)":             _v(2, 0.5, 0.1, 3, 13, 3, 0.7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "CREA 2019 amido di mais"),
    "Farina di mandorle":                   _v(269, 3.7, 3.1, 270, 481, 733, 4.1, 0, 0, 25.6, 0, 0.21, 1.14, 3.6, 0.14, 44, 0, "high", "USDA FDC almond flour"),
    "Farina di riso":                       _v(10, 0.4, 0.8, 35, 98, 76, 15.1, 0, 0, 0.11, 0, 0.14, 0.02, 2.6, 0.44, 4, 0, "high", "USDA FDC rice flour white"),
    "Farina di soia sgrassata":             _v(241, 9.2, 4.0, 290, 674, 2490, 7.5, 2, 0, 0.5, 0, 0.7, 0.25, 2.6, 0.58, 305, 0, "high", "USDA FDC soy flour defatted"),
    "Semolino di frumento":                 _v(17, 1.2, 1.1, 47, 136, 186, 63, 0, 0, 0.3, 0, 0.28, 0.08, 3.1, 0.1, 72, 0, "high", "CREA 2019 semola"),

    # --- Riso crudo ---
    "Riso arborio, crudo":                  _v(6, 0.8, 1.1, 25, 94, 86, 15.1, 0, 0, 0.11, 0, 0.07, 0.02, 1.5, 0.15, 9, 0, "high", "CREA 2019 riso bianco"),
    "Riso basmati, crudo":                  _v(9, 0.8, 1.1, 32, 95, 115, 15.1, 0, 0, 0.11, 0, 0.07, 0.05, 1.6, 0.16, 8, 0, "high", "CREA 2019 riso"),
    "Riso parboiled, crudo":                _v(55, 1.1, 1.3, 44, 155, 150, 15, 0, 0, 0.14, 0, 0.22, 0.04, 3.5, 0.3, 11, 0, "high", "CREA 2019"),
    "Riso rosso (Camargue), crudo":         _v(20, 1.5, 1.8, 110, 264, 268, 23, 0, 0, 0.6, 0, 0.4, 0.09, 5.1, 0.51, 20, 0, "medium", "USDA FDC brown rice adj"),
    "Riso venere, crudo":                   _v(12, 1.8, 2.0, 143, 280, 256, 23.4, 0, 0, 1.2, 0, 0.41, 0.09, 5.1, 0.51, 20, 0, "medium", "USDA FDC black rice"),

    # --- Pasta secca / prodotti speciali ---
    "Pasta di edamame/soia, secca":         _v(130, 5.2, 3.5, 180, 380, 1100, 7, 2, 0, 0.4, 0, 0.45, 0.2, 2.0, 0.4, 250, 0, "medium", "USDA FDC edamame pasta"),
    "Pasta di konjac (shirataki, cotta)":   _v(43, 0.4, 0.1, 1, 6, 2, 0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "medium", "USDA FDC shirataki"),
    "Pasta di lenticchie rosse, secca":     _v(35, 6.5, 3.3, 47, 281, 677, 8.3, 2, 0, 0.5, 1.5, 0.5, 0.21, 2.6, 0.54, 479, 0, "medium", "USDA FDC lentil pasta"),
    "Pasta proteica (+proteine di legumi), secca": _v(40, 4.5, 2.8, 80, 300, 500, 8, 0, 0, 0.4, 0, 0.4, 0.15, 3.0, 0.35, 200, 0, "medium", "USDA FDC protein pasta est"),

    # --- Altro ---
    "Pop corn (sgonfio, senza grassi)":     _v(7, 2.7, 2.7, 131, 300, 274, 0, 10, 0, 0.29, 0, 0.1, 0.08, 1.9, 0.16, 31, 0, "high", "USDA FDC popcorn air-popped"),
    "Chapati (pane indiano integrale)":     _v(30, 2.7, 1.7, 62, 170, 166, 20, 0, 0, 0.5, 0, 0.22, 0.06, 2.2, 0.15, 24, 0, "medium", "USDA FDC chapati"),
    "Tortilla di farro":                    _v(25, 2.5, 1.5, 55, 170, 180, 15, 0, 0, 0.4, 0, 0.25, 0.08, 3.0, 0.12, 30, 0, "medium", "CREA 2019 farro stima"),

    # =====================================================================
    # CATEGORIA 2 — Pasta/riso/cereali cotti (23 alimenti)
    # =====================================================================

    # --- Cereali cotti ---
    "Amaranto, cotto":                      _v(47, 2.1, 0.9, 65, 148, 135, 5.5, 0, 0, 0.35, 1.1, 0.01, 0.02, 0.2, 0.11, 22, 0, "high", "USDA FDC amaranth cooked"),
    "Avena, cotta (porridge)":              _v(9, 1.4, 1.0, 27, 77, 61, 4.4, 0, 0, 0.08, 0, 0.08, 0.02, 0.2, 0.01, 6, 0, "high", "USDA FDC oatmeal cooked"),
    "Bulgur, cotto":                        _v(10, 1.0, 0.6, 32, 40, 68, 0.6, 0, 0, 0.01, 0, 0.06, 0.03, 1.0, 0.08, 18, 0, "high", "USDA FDC bulgur cooked"),
    "Grano saraceno, cotto":                _v(12, 0.8, 0.6, 51, 70, 88, 1.5, 0, 0, 0.09, 0, 0.04, 0.04, 0.9, 0.08, 14, 0, "high", "USDA FDC buckwheat groats cooked"),
    "Miglio, cotto":                        _v(3, 0.6, 0.9, 44, 100, 62, 0.9, 0, 0, 0.02, 0, 0.11, 0.08, 1.3, 0.11, 19, 0, "high", "USDA FDC millet cooked"),
    "Orzo perlato, cotto":                  _v(11, 1.3, 0.8, 22, 54, 93, 8.6, 0, 0, 0.01, 0, 0.08, 0.06, 2.1, 0.12, 16, 0, "high", "USDA FDC barley pearled cooked"),
    "Sorgo, cotto":                         _v(9, 1.4, 0.6, 50, 87, 117, 3.8, 0, 0, 0.15, 0, 0.08, 0.05, 1.0, 0.13, 7, 0, "medium", "USDA FDC sorghum cooked"),
    "Teff, cotto":                          _v(49, 2.1, 1.1, 50, 120, 120, 1.3, 0, 0, 0.02, 0, 0.11, 0.07, 1.0, 0.14, 0, 0, "medium", "USDA FDC teff cooked"),

    # --- Riso cotto ---
    "Riso basmati, cotto":                  _v(3, 0.2, 0.4, 12, 37, 35, 5.6, 0, 0, 0.04, 0, 0.02, 0.01, 0.4, 0.05, 3, 0, "high", "CREA 2019 riso cotto"),
    "Riso parboiled, cotto":               _v(19, 0.4, 0.5, 16, 56, 54, 5.6, 0, 0, 0.05, 0, 0.08, 0.01, 1.2, 0.1, 4, 0, "high", "CREA 2019 riso parboiled"),
    "Riso venere, cotto":                   _v(4, 0.6, 0.7, 43, 83, 79, 7.5, 0, 0, 0.35, 0, 0.12, 0.03, 1.5, 0.15, 6, 0, "medium", "USDA FDC black rice cooked"),
    "Risotto semplice (burro/parmigiano)":  _v(60, 0.3, 0.6, 15, 55, 50, 4, 50, 0.1, 0.15, 0, 0.03, 0.04, 0.5, 0.04, 4, 0, "medium", "CREA 2019 riso + parmigiano"),

    # --- Pasta cotta ---
    "Pasta all'uovo, secca":                _v(21, 2.8, 1.4, 41, 189, 161, 57, 35, 0.5, 0.5, 0, 0.59, 0.24, 4.5, 0.1, 29, 0.2, "high", "CREA 2019"),
    "Pasta all'uovo, cotta":                _v(7, 1.0, 0.5, 14, 66, 56, 20, 12, 0.2, 0.17, 0, 0.2, 0.08, 1.5, 0.04, 10, 0.07, "high", "CREA 2019"),
    "Pasta di farro, cotta":                _v(8, 1.2, 0.9, 40, 110, 100, 3.5, 0, 0, 0.2, 0, 0.1, 0.04, 1.8, 0.07, 12, 0, "medium", "CREA 2019 farro cotto"),
    "Pasta di legumi (ceci/lenticchie), cotta": _v(12, 2.2, 1.1, 16, 93, 220, 2.8, 1, 0, 0.15, 0.5, 0.17, 0.07, 0.9, 0.18, 160, 0, "medium", "USDA FDC legume pasta cooked"),
    "Pasta di riso, cotta":                 _v(4, 0.1, 0.3, 4, 16, 4, 3.6, 0, 0, 0, 0, 0.01, 0.01, 0.2, 0.01, 1, 0, "high", "USDA FDC rice noodles cooked"),
    "Pasta gluten-free riso/mais, cotta":   _v(5, 0.3, 0.3, 6, 22, 10, 3, 0, 0, 0.02, 0, 0.02, 0.01, 0.3, 0.02, 2, 0, "medium", "USDA FDC gf pasta cooked"),
    "Penne integrali, cotte":              _v(15, 1.4, 1.1, 42, 89, 62, 25.8, 0, 0, 0.3, 0, 0.16, 0.06, 1.8, 0.08, 10, 0, "high", "USDA FDC whole wheat pasta cooked"),
    "Trofie, cotte":                        _v(7, 0.5, 0.4, 13, 44, 44, 20, 0, 0, 0.06, 0, 0.1, 0.02, 1.0, 0.04, 7, 0, "medium", "CREA 2019 pasta cotta"),
    "Gnocchi di patate, cotti":             _v(7, 0.4, 0.3, 11, 30, 170, 0.7, 0, 0, 0.04, 5, 0.06, 0.02, 0.8, 0.12, 6, 0, "medium", "CREA 2019 gnocchi"),
    "Lasagne fresche, cotte":               _v(18, 1.0, 0.5, 15, 62, 55, 15, 20, 0.2, 0.15, 0, 0.15, 0.08, 1.2, 0.04, 8, 0.1, "medium", "CREA 2019 pasta uovo cotta"),
    "Spätzle (gnocchetti tirolesi), cotti": _v(15, 0.8, 0.4, 12, 55, 50, 12, 18, 0.2, 0.12, 0, 0.12, 0.07, 1.0, 0.03, 7, 0.08, "medium", "CREA 2019 pasta uovo cotta"),

    # =====================================================================
    # CATEGORIA 3 — Pane e prodotti da forno (41 alimenti)
    # =====================================================================

    # --- Pane ---
    "Pane ciabatta":                        _v(28, 1.1, 0.7, 22, 78, 110, 22, 0, 0, 0.1, 0, 0.12, 0.05, 1.6, 0.06, 28, 0, "high", "CREA 2019 pane tipo 0"),
    "Pane di Altamura (semola)":            _v(19, 1.3, 0.9, 30, 100, 130, 40, 0, 0, 0.3, 0, 0.2, 0.07, 2.3, 0.08, 45, 0, "high", "CREA 2019 pane semola"),
    "Pane al latte":                        _v(65, 1.0, 0.6, 18, 70, 100, 15, 12, 0.1, 0.2, 0, 0.14, 0.1, 1.4, 0.04, 20, 0, "high", "CREA 2019 pane latte"),
    "Pane in cassetta (toast)":             _v(95, 1.4, 0.8, 25, 95, 125, 20, 0, 0, 0.3, 0, 0.2, 0.07, 2.0, 0.06, 30, 0, "high", "CREA 2019 pan carre"),
    "Pane azzimo (matza)":                  _v(13, 1.2, 0.6, 19, 71, 92, 27, 0, 0, 0.08, 0, 0.1, 0.05, 1.3, 0.06, 18, 0, "high", "USDA FDC matzo"),
    "Pane azzimo integrale":                _v(30, 2.8, 1.8, 65, 200, 250, 35, 0, 0, 0.5, 0, 0.3, 0.12, 3.8, 0.18, 35, 0, "medium", "USDA FDC whole wheat matzo"),
    "Grissini torinesi":                    _v(22, 1.2, 0.7, 20, 80, 120, 25, 0, 0, 1.5, 0, 0.1, 0.05, 1.4, 0.06, 22, 0, "high", "CREA 2019"),
    "Crackers integrali":                   _v(45, 3.0, 2.0, 65, 200, 270, 28, 0, 0, 0.7, 0, 0.32, 0.15, 3.8, 0.16, 30, 0, "high", "CREA 2019"),
    "Fette biscottate classiche":           _v(32, 1.5, 0.7, 22, 90, 120, 20, 0, 0, 0.9, 0, 0.14, 0.07, 1.8, 0.06, 22, 0, "high", "CREA 2019"),
    "Piadina romagnola":                    _v(30, 1.2, 0.6, 18, 70, 100, 15, 0, 0, 1.0, 0, 0.12, 0.05, 1.5, 0.05, 20, 0, "high", "CREA 2019"),
    "Tortilla di frumento":                 _v(120, 2.0, 0.7, 24, 100, 100, 18, 0, 0, 0.6, 0, 0.25, 0.1, 2.2, 0.06, 25, 0, "high", "USDA FDC flour tortilla"),
    "Tortilla di mais":                     _v(46, 0.9, 0.5, 31, 82, 97, 3.3, 0, 0, 0.23, 0, 0.06, 0.04, 0.6, 0.1, 1, 0, "high", "USDA FDC corn tortilla"),
    "Pancarré di segale":                   _v(73, 2.8, 1.6, 40, 125, 166, 30, 1, 0, 0.4, 0, 0.34, 0.28, 3.4, 0.17, 51, 0, "high", "USDA FDC rye bread"),
    "Biscotti secchi (tipo digestive)":     _v(80, 2.5, 1.0, 30, 110, 180, 8, 0, 0.1, 1.5, 0, 0.15, 0.07, 2.0, 0.06, 20, 0, "medium", "CREA 2019"),
    "Biscotti frollini classici":           _v(35, 1.2, 0.5, 15, 80, 100, 8, 40, 0.2, 1.2, 0, 0.08, 0.05, 1.0, 0.03, 15, 0, "medium", "CREA 2019"),
    "Fette biscottate senza glutine":       _v(25, 1.0, 0.5, 12, 50, 60, 3, 0, 0, 0.5, 0, 0.06, 0.03, 0.8, 0.03, 8, 0, "medium", "USDA FDC gf crackers"),
    "Pane senza glutine":                   _v(40, 1.2, 0.5, 15, 60, 80, 3, 0, 0, 0.3, 0, 0.08, 0.04, 1.0, 0.04, 10, 0, "medium", "USDA FDC gf bread"),
    "Cracker di riso (gallette mini)":      _v(3, 0.2, 0.8, 25, 80, 75, 7.9, 0, 0, 0.1, 0, 0.06, 0.02, 1.6, 0.1, 4, 0, "high", "USDA FDC rice cakes"),
    "Taralli pugliesi":                     _v(20, 1.5, 0.8, 22, 85, 110, 20, 0, 0, 2.5, 0, 0.12, 0.05, 1.5, 0.06, 20, 0, "medium", "CREA 2019 taralli"),
    "Cornetto (brioche vuoto)":             _v(30, 1.5, 0.6, 14, 65, 90, 10, 45, 0.2, 0.5, 0, 0.16, 0.1, 1.5, 0.04, 18, 0.1, "medium", "CREA 2019 brioche"),
    "Muesli senza zucchero aggiunto":       _v(50, 4.0, 2.8, 110, 310, 390, 12, 0, 0, 1.5, 0, 0.4, 0.15, 4.0, 0.3, 40, 0, "high", "USDA FDC muesli"),
    "Granola tostata":                      _v(46, 3.1, 2.4, 100, 240, 300, 14, 0, 0, 2.0, 0, 0.35, 0.12, 3.5, 0.25, 35, 0, "medium", "USDA FDC granola"),
    "Pane di kamut, biologico":             _v(22, 1.8, 1.2, 40, 130, 160, 30, 0, 0, 0.3, 0, 0.2, 0.06, 2.5, 0.1, 30, 0, "medium", "USDA FDC kamut bread"),
    "Pane all'olio":                        _v(25, 1.0, 0.6, 20, 75, 105, 18, 0, 0, 1.5, 0, 0.12, 0.05, 1.5, 0.05, 25, 0, "medium", "CREA 2019 pane olio"),
    "Pane con noci":                        _v(35, 1.5, 1.0, 35, 110, 180, 18, 0, 0, 1.0, 0, 0.18, 0.08, 2.2, 0.1, 30, 0, "medium", "CREA 2019 pane noci"),
    "Focaccia genovese":                    _v(25, 1.0, 0.6, 18, 70, 100, 15, 0, 0, 2.0, 0, 0.1, 0.05, 1.3, 0.05, 22, 0, "medium", "CREA 2019 focaccia"),
    "Schiacciata toscana":                  _v(22, 1.0, 0.6, 17, 68, 95, 15, 0, 0, 1.8, 0, 0.1, 0.04, 1.3, 0.05, 20, 0, "medium", "CREA 2019 focaccia"),
    "Crespelle (crêpes, neutre)":           _v(62, 1.0, 0.6, 12, 80, 110, 10, 45, 0.5, 0.3, 0, 0.1, 0.14, 0.8, 0.04, 14, 0.3, "medium", "USDA FDC crepe"),
    "Waffle (neutro base)":                 _v(80, 1.7, 0.7, 16, 110, 130, 12, 50, 0.4, 0.4, 0, 0.18, 0.15, 1.5, 0.05, 20, 0.2, "medium", "USDA FDC waffle"),
    "Muffin all'avena (senza latticini)":   _v(30, 1.8, 0.9, 35, 120, 140, 8, 0, 0, 0.5, 0, 0.15, 0.08, 1.5, 0.1, 15, 0, "medium", "USDA FDC oat muffin"),
    "Fetta biscottata alla frutta":         _v(30, 1.2, 0.5, 18, 75, 130, 12, 0, 0, 0.6, 0, 0.1, 0.05, 1.2, 0.05, 16, 0, "medium", "CREA 2019 fette bisc est"),
    "Baguette francese":                    _v(28, 1.2, 0.7, 22, 78, 110, 22, 0, 0, 0.1, 0, 0.15, 0.06, 1.8, 0.06, 30, 0, "high", "USDA FDC french baguette"),
    "Naan indiano":                         _v(48, 2.0, 0.7, 20, 80, 100, 16, 0, 0.1, 0.4, 0, 0.23, 0.12, 2.4, 0.06, 20, 0, "high", "USDA FDC naan bread"),
    "Biscotto al cocco (tipo Oro Saiwa)":   _v(30, 1.0, 0.4, 15, 65, 90, 5, 5, 0, 1.0, 0, 0.06, 0.04, 0.8, 0.03, 10, 0, "medium", "CREA 2019 biscotti est"),
    "Crumble di avena (base dolce)":        _v(35, 2.0, 1.2, 50, 150, 180, 8, 10, 0.1, 0.8, 0, 0.2, 0.08, 1.5, 0.1, 18, 0, "medium", "USDA FDC oat crumble est"),
    "Pane tipo pugliese (semola rimacinata)": _v(19, 1.3, 0.9, 30, 100, 130, 40, 0, 0, 0.3, 0, 0.2, 0.07, 2.3, 0.08, 45, 0, "medium", "CREA 2019 pane semola"),
    "Panino al sesamo":                     _v(70, 2.0, 1.2, 35, 120, 130, 20, 0, 0, 0.5, 0, 0.2, 0.08, 2.2, 0.08, 30, 0, "medium", "USDA FDC sesame bun"),
    "Pane di mais senza glutine":           _v(15, 0.8, 0.4, 18, 50, 70, 3, 3, 0, 0.2, 0, 0.06, 0.03, 0.8, 0.06, 8, 0, "medium", "USDA FDC cornbread gf"),
    "Pane di segale compatto (tipo wasa)":  _v(40, 3.0, 2.0, 55, 170, 250, 30, 0, 0, 0.5, 0, 0.3, 0.2, 3.5, 0.2, 45, 0, "high", "USDA FDC rye crispbread"),
    "Pane di patate":                       _v(20, 0.8, 0.4, 15, 50, 150, 5, 0, 0, 0.1, 3, 0.08, 0.03, 1.0, 0.08, 12, 0, "medium", "USDA FDC potato bread"),
    "Tortino di mais (polenta al forno)":   _v(5, 0.5, 0.3, 15, 35, 50, 2, 5, 0, 0.15, 0, 0.04, 0.02, 0.5, 0.05, 3, 0, "medium", "CREA 2019 polenta est"),

    # =====================================================================
    # CATEGORIA 4 — Legumi (34 alimenti)
    # =====================================================================

    # --- Fagioli ---
    "Fagioli neri, cotti":                  _v(27, 2.1, 1.1, 70, 140, 355, 1.2, 0, 0, 0.12, 0, 0.24, 0.06, 0.5, 0.07, 149, 0, "high", "USDA FDC black beans cooked"),
    "Fagioli di soia (edamame sgranati, crudi)": _v(63, 2.3, 1.4, 64, 169, 436, 0.8, 9, 0, 0.68, 6.1, 0.2, 0.16, 1.3, 0.1, 303, 0, "high", "USDA FDC edamame raw"),
    "Lenticchie rosse, cotte":              _v(19, 2.5, 1.0, 22, 126, 248, 1.6, 1, 0, 0.11, 0.8, 0.11, 0.05, 0.6, 0.18, 100, 0, "high", "USDA FDC red lentils cooked"),
    "Lenticchie verdi, cotte":              _v(19, 3.3, 1.3, 36, 180, 369, 2.8, 1, 0, 0.11, 1.5, 0.17, 0.07, 1.1, 0.18, 181, 0, "high", "USDA FDC lentils cooked"),
    "Piselli freschi, crudi":               _v(25, 1.5, 1.2, 33, 108, 244, 1.8, 38, 0, 0.13, 40, 0.27, 0.13, 2.1, 0.17, 65, 0, "high", "CREA 2019"),
    "Fagioli cannellini, secchi":           _v(240, 10.4, 3.7, 190, 460, 1795, 12.8, 0, 0, 0.21, 0, 0.44, 0.15, 1.4, 0.32, 364, 0, "high", "USDA FDC white beans dry"),
    "Ceci, secchi tostati (snack)":         _v(92, 5.0, 3.4, 115, 320, 718, 6, 2, 0, 0.8, 1.3, 0.35, 0.16, 1.5, 0.47, 440, 0, "high", "USDA FDC chickpeas roasted"),
    "Lupini, lessati":                      _v(51, 1.2, 1.0, 54, 128, 245, 0.7, 1, 0, 0.2, 1.1, 0.1, 0.06, 0.5, 0.01, 38, 0, "high", "USDA FDC lupins cooked"),
    "Fagioli azuki, cotti":                 _v(28, 2.0, 1.8, 52, 168, 532, 1.2, 0, 0, 0.06, 0, 0.12, 0.06, 0.7, 0.1, 121, 0, "high", "USDA FDC adzuki beans cooked"),
    "Fagioli di Spagna, cotti":             _v(46, 2.2, 0.9, 55, 101, 454, 1.1, 0, 0, 0.05, 0, 0.14, 0.06, 0.5, 0.09, 78, 0, "high", "USDA FDC lima beans cooked"),
    "Cicerchie, cotte":                     _v(25, 1.8, 1.0, 35, 120, 300, 1.5, 1, 0, 0.1, 0.5, 0.12, 0.06, 0.6, 0.1, 100, 0, "medium", "CREA 2019 cicerchie"),
    "Piselli secchi, cotti":                _v(14, 1.3, 1.0, 36, 99, 362, 0.6, 7, 0, 0.03, 0.4, 0.19, 0.06, 0.9, 0.05, 65, 0, "high", "USDA FDC split peas cooked"),
    "Fagioli mung, cotti":                  _v(27, 1.4, 0.8, 48, 99, 266, 2.5, 1, 0, 0.15, 1, 0.16, 0.06, 0.6, 0.07, 159, 0, "high", "USDA FDC mung beans cooked"),
    "Soia, farina sgrassata":               _v(241, 9.2, 4.0, 290, 674, 2490, 7.5, 2, 0, 0.5, 0, 0.7, 0.25, 2.6, 0.58, 305, 0, "high", "USDA FDC soy flour"),
    "Tempeh (soia fermentata)":             _v(111, 2.7, 1.1, 81, 266, 412, 0, 0, 0, 0.05, 0, 0.08, 0.36, 2.6, 0.22, 24, 0, "high", "USDA FDC tempeh"),
    "Tofu, compatto (firm)":                _v(350, 5.4, 2.0, 30, 97, 121, 8.9, 0, 0, 0.01, 0, 0.07, 0.05, 0.1, 0.05, 15, 0, "high", "USDA FDC tofu firm"),
    "Tofu, morbido (silken)":               _v(111, 1.6, 0.6, 28, 76, 120, 4.6, 0, 0, 0.01, 0, 0.06, 0.03, 0.1, 0.05, 15, 0, "high", "USDA FDC tofu silken"),
    "Hummus (crema di ceci)":               _v(38, 1.6, 1.3, 29, 110, 173, 2.6, 1, 0, 0.65, 0, 0.1, 0.06, 0.6, 0.2, 59, 0, "high", "USDA FDC hummus"),
    "Ceci neri, cotti":                     _v(49, 2.9, 1.5, 48, 168, 291, 3.7, 1, 0, 0.35, 1.3, 0.12, 0.06, 0.5, 0.14, 172, 0, "medium", "USDA FDC chickpeas cooked"),
    "Fagioli all'occhio, cotti":            _v(24, 2.5, 1.1, 53, 156, 278, 2.5, 4, 0, 0.28, 0.4, 0.2, 0.06, 0.5, 0.1, 208, 0, "high", "USDA FDC black-eyed peas cooked"),
    "Fave fresche, crude":                  _v(37, 1.5, 1.0, 33, 125, 332, 1.4, 4, 0, 0.09, 3.7, 0.17, 0.11, 1.5, 0.1, 148, 0, "high", "USDA FDC fava beans raw"),
    "Lenticchie beluga (nere), cotte":      _v(19, 3.3, 1.3, 36, 180, 369, 2.8, 1, 0, 0.11, 1.5, 0.17, 0.07, 1.1, 0.18, 181, 0, "medium", "USDA FDC lentils cooked"),
    "Piselli spezzati gialli, cotti":       _v(14, 1.3, 1.0, 36, 99, 362, 0.6, 7, 0, 0.03, 0.4, 0.19, 0.06, 0.9, 0.05, 65, 0, "high", "USDA FDC yellow split peas cooked"),
    "Soia, granuli texturizzati secchi (TVP)": _v(199, 9.2, 3.9, 290, 620, 2200, 7, 0, 0, 0.4, 0, 0.6, 0.2, 2.5, 0.5, 280, 0, "medium", "USDA FDC soy protein tvp"),
    "Fagioli di Lamon, cotti":              _v(50, 2.5, 1.0, 55, 140, 400, 1.5, 0, 0, 0.1, 0.5, 0.15, 0.06, 0.5, 0.09, 120, 0, "medium", "CREA 2019 fagioli borlotti"),
    "Fagiolini piattoni, cotti":            _v(37, 1.0, 0.2, 18, 25, 146, 0.6, 35, 0, 0.39, 9.7, 0.08, 0.1, 0.5, 0.07, 33, 0, "high", "USDA FDC green beans cooked"),
    "Fagiolini in scatola (sgocciolati)":   _v(28, 0.8, 0.2, 13, 20, 100, 0.4, 25, 0, 0.3, 5, 0.04, 0.06, 0.3, 0.04, 22, 0, "medium", "USDA FDC canned green beans"),
    "Ceci al curry (piatto pronto)":        _v(40, 2.3, 1.2, 35, 120, 200, 3, 15, 0, 0.5, 2, 0.1, 0.06, 0.6, 0.14, 120, 0, "medium", "USDA FDC chana masala"),
    "Fagioli al pomodoro (in scatola)":     _v(55, 1.8, 0.9, 40, 100, 280, 1, 10, 0, 0.15, 3, 0.08, 0.05, 0.4, 0.06, 40, 0, "medium", "USDA FDC baked beans"),
    "Passata di ceci (hummus base ridotta)": _v(30, 1.4, 1.1, 25, 90, 150, 2, 1, 0, 0.5, 0, 0.08, 0.05, 0.5, 0.15, 50, 0, "medium", "USDA FDC hummus adj"),
    "Minestrone con legumi (piatto pronto)": _v(25, 1.0, 0.5, 18, 50, 200, 1, 50, 0, 0.3, 5, 0.05, 0.03, 0.5, 0.06, 30, 0, "medium", "USDA FDC minestrone"),
    "Piselli primavera surgelati (cotti)":  _v(22, 1.3, 1.0, 30, 95, 220, 1.5, 35, 0, 0.1, 15, 0.22, 0.1, 1.8, 0.14, 55, 0, "medium", "USDA FDC frozen peas cooked"),
    "Zuppa di fagioli neri":                _v(20, 1.5, 0.8, 45, 90, 250, 1, 5, 0, 0.1, 0.5, 0.15, 0.04, 0.4, 0.05, 100, 0, "medium", "USDA FDC black bean soup"),
    "Zuppa di lenticchie (piatto pronto)":  _v(15, 1.8, 0.8, 20, 85, 200, 1.2, 30, 0, 0.1, 2, 0.1, 0.04, 0.5, 0.1, 80, 0, "medium", "USDA FDC lentil soup"),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, nome FROM alimenti
        WHERE categoria_id IN (1, 2, 3, 4) AND calcio_mg IS NULL ORDER BY nome
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
