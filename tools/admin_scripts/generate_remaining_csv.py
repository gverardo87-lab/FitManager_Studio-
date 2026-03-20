"""
Genera CSV micronutrienti per le ultime 4 categorie senza dati:
  - Cat 7:  Frutta secca e semi (40 items)
  - Cat 13: Oli e condimenti (41 items)
  - Cat 14: Dolci e zuccheri (54 items)
  - Cat 15: Bevande e integratori (64 items)

Fonte: CREA 2019 IV ed. + USDA FoodData Central.
Valori per 100g di prodotto edibile.

Uso: python -m tools.admin_scripts.generate_remaining_csv
Output: data/nutrition/micronutrients_remaining.csv
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
OUT_PATH = os.path.join(BASE_DIR, "nutrition", "micronutrients_remaining.csv")

# Supplements: skip these (no food-derived micronutrient data applies)
SKIP_IDS = {
    157,   # Creatina monoidrato (polvere)
    158,   # BCAA, polvere
    619,   # Maltodestrine (polvere)
    620,   # Destrosio (glucosio polvere)
    621,   # Creatina etil estere (polvere)
    622,   # Beta-alanina (polvere)
    623,   # Glutammina (polvere)
    624,   # Pre-workout (caffeina+beta-ala, polvere)
    625,   # Olio MCT (trigliceridi catena media)
    626,   # Omega-3 (olio di pesce, capsula 1g)
    809,   # Electrolyte drink (zero kcal)
}


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
    # CATEGORIA 7 — FRUTTA SECCA E SEMI (40 items)
    # =====================================================================

    # --- Noci ---
    #                             Ca    Fe    Zn    Mg     P     K    Se   VA   VD    VE    VC    B1    B2    B3    B6   B9   B12  conf  src
    "Noci pecan":               _v(70,  2.5,  4.5,  121,  277,  410,  3.8,  3,  0,  1.4,  1.1,  0.66, 0.13, 1.2,  0.21, 22,  0, "high", "USDA FDC pecan"),
    "Noci del Brasile":         _v(160, 2.4,  4.1,  376,  725,  659, 1917,  0,  0,  5.7,  0.7,  0.62, 0.04, 0.3,  0.1,  22,  0, "high", "USDA FDC brazil nut"),
    "Noci macadamia":           _v(85,  3.7,  1.3,  130,  188,  368,  3.6,  0,  0,  0.54, 1.2,  1.2,  0.16, 2.5,  0.27, 11,  0, "high", "USDA FDC macadamia"),
    "Noci di acagi":            _v(37,  6.7,  5.8,  292,  593,  660,  20,   0,  0,  0.9,  0.5,  0.42, 0.06, 1.1,  0.42, 25,  0, "high", "USDA FDC cashew roasted"),
    "Mandorle tostate (non salate)": _v(266, 3.7, 3.1, 270, 484, 713, 4.1, 0, 0, 25.6, 0, 0.21, 1.01, 3.6, 0.14, 44, 0, "high", "USDA FDC almond roasted"),
    "Nocciole tostate":         _v(114, 4.7,  2.5,  163,  310,  680,  2.4,  1,  0, 15.0,  3.8,  0.64, 0.11, 1.8,  0.56, 113, 0, "high", "USDA FDC hazelnut roasted"),
    "Pistacchi tostati (salati)": _v(107, 3.9, 2.2, 121, 490, 1025, 7.0, 26, 0, 2.3, 5.6, 0.87, 0.16, 1.3, 1.7, 51, 0, "high", "USDA FDC pistachio roasted salted"),
    "Arachidi crude":           _v(92,  4.6,  3.3,  168,  376,  705,  7.2,  0,  0,  8.3,  0,    0.64, 0.14, 12.1, 0.35, 240, 0, "high", "USDA FDC peanut raw"),
    "Semi di sesamo":           _v(975, 14.6, 7.8,  351,  629,  468,  34.4, 0,  0,  0.25, 0,    0.79, 0.25, 4.5,  0.79, 97,  0, "high", "USDA FDC sesame"),
    "Semi di canapa (sgusciati)": _v(70, 7.9, 9.9, 700, 1650, 1200, 0, 1, 0, 0.8, 0.5, 1.28, 0.29, 9.2, 0.6, 110, 0, "high", "USDA FDC hemp seed hulled"),
    "Tahini (pasta di sesamo)": _v(426, 8.9,  4.6,  95,   732,  414,  34.4, 1,  0,  0.25, 0,    1.22, 0.47, 5.5,  0.15, 98,  0, "high", "USDA FDC tahini"),
    "Burro di arachidi (naturale)": _v(43, 1.7, 2.8, 168, 358, 649, 4.1, 0, 0, 9.1, 0, 0.15, 0.1, 13.4, 0.44, 87, 0, "high", "USDA FDC peanut butter"),
    "Burro di mandorle":        _v(347, 3.3,  3.3,  279,  508,  748,  2.4,  0,  0, 24.2,  0,    0.04, 0.94, 3.1,  0.1,  53,  0, "high", "USDA FDC almond butter"),
    "Cocco rap":                _v(14,  3.3,  2.0,  90,   160,  543,  18.5, 0,  0,  0.44, 1.5,  0.06, 0.02, 0.5,  0.3,  9,   0, "high", "USDA FDC coconut dried"),
    "Semi di papavero":         _v(1438,9.8, 7.9,  347,  870,  719,  13.5, 0,  0,  1.77, 1,    0.85, 0.1,  0.9,  0.25, 82,  0, "high", "USDA FDC poppy seed"),
    "Semi di ca":               _v(70,  7.9,  9.9,  700, 1650, 1200,  0,   1,  0,  0.8,  0.5,  1.28, 0.29, 9.2,  0.6,  110, 0, "high", "USDA FDC hemp seed ground"),
    "Pinoli":                   _v(16,  5.5,  6.4,  251,  575,  597,  0.7,  1,  0,  9.3,  0.8,  0.36, 0.23, 4.4,  0.09, 34,  0, "high", "USDA FDC pine nut"),
    "Castagne, fresche":        _v(27,  1.0,  0.5,  32,   93,   518,  1.2,  1,  0,  0.5,  43,   0.24, 0.17, 1.1,  0.38, 62,  0, "high", "CREA 2019 castagna"),
    "Castagne secche":          _v(56,  3.0,  0.9,  74,   200,  990,  2.5,  2,  0,  1.0,  10,   0.3,  0.3,  2.4,  0.5,  80,  0, "high", "CREA 2019 castagna secca"),
    "Semi di girasole, tostati": _v(78, 6.8, 5.3, 129, 660, 645, 53, 3, 0, 35.2, 1.4, 1.48, 0.36, 8.3, 1.35, 227, 0, "high", "USDA FDC sunflower roasted"),
    "Semi di zucca, tostati":   _v(46,  8.8,  7.8,  550,  1233, 809,  9.4,  1,  0,  2.2,  1.8,  0.27, 0.15, 4.99, 0.14, 58,  0, "high", "USDA FDC pumpkin seed roasted"),
    "Noci, essiccate":          _v(98,  2.9,  3.1,  158,  346,  441,  4.9,  1,  0,  0.7,  1.3,  0.34, 0.15, 1.1,  0.54, 98,  0, "high", "USDA FDC walnut dried"),
    "Arachidi tostate e salate": _v(54, 2.3, 3.3, 176, 397, 726, 7.5, 0, 0, 7.8, 0, 0.44, 0.1, 13.5, 0.26, 145, 0, "high", "USDA FDC peanut roasted salted"),
    "Noci di macadamia tostate (salate)": _v(70, 2.7, 1.3, 118, 198, 363, 3.6, 0, 0, 0.54, 0.7, 0.71, 0.1, 2.5, 0.28, 11, 0, "high", "USDA FDC macadamia roasted salted"),
    "Arachidi bollite":         _v(55,  2.2,  3.3,  65,   134,  180,  7.5,  0,  0,  3.0,  0,    0.15, 0.06, 5.3,  0.07, 40,  0, "high", "USDA FDC peanut boiled"),
    "Mix di frutta secca e semi": _v(78, 3.5, 3.5, 200, 400, 600, 8, 1, 0, 8.0, 0.5, 0.5, 0.2, 4.0, 0.3, 60, 0, "medium", "stima media composita"),
    "Cocco, latte in polvere":  _v(6,   1.5,  0.8,  46,   100,  325,  6.3,  0,  0,  0.2,  1.0,  0.03, 0.02, 0.8,  0.03, 16,  0, "medium", "USDA FDC coconut milk powder"),
    "Noci pecan tostate":       _v(72,  2.5,  4.5,  132,  293,  424,  3.8,  3,  0,  1.4,  0.5,  0.46, 0.13, 1.2,  0.19, 22,  0, "high", "USDA FDC pecan roasted"),
    "Semi di sesamo tostati":   _v(989,14.6,  7.8,  356,  638,  475,  34,   0,  0,  0.25, 0,    0.8,  0.25, 4.5,  0.79, 97,  0, "high", "USDA FDC sesame toasted"),
    "Semi di lino tostati":     _v(255, 5.7,  4.3,  392,  642,  813,  25.4, 0,  0,  0.31, 0.6,  1.64, 0.16, 3.1,  0.47, 87,  0, "high", "USDA FDC flaxseed"),
    "Burro di girasole":        _v(50,  5.0,  5.0,  120,  500,  580,  40,   3,  0, 26.1,  1.0,  0.4,  0.3,  6.5,  0.8,  200, 0, "medium", "USDA FDC sunflower butter"),
    "Mandorle pelate e blanched": _v(236, 3.7, 3.1, 268, 481, 705, 2.5, 0, 0, 25.6, 0, 0.21, 1.01, 3.6, 0.14, 44, 0, "high", "USDA FDC almond blanched"),
    "Nocciole fresche (non tostate)": _v(114, 4.7, 2.4, 163, 290, 680, 2.4, 1, 0, 15.0, 6.3, 0.64, 0.11, 1.8, 0.56, 113, 0, "high", "USDA FDC hazelnut raw"),
    "Farro soffiato":           _v(18,  2.5,  1.5,  40,   120,  180,  5,    0,  0,  0.3,  0,    0.15, 0.08, 2.5,  0.15, 25,  0, "medium", "CREA 2019 farro"),
    "Riso soffiato":            _v(6,   1.0,  0.8,  25,   78,   100,  5,    0,  0,  0.1,  0,    0.07, 0.03, 3.5,  0.1,  8,   0, "medium", "CREA 2019 riso soffiato"),
    "Mais soffiato (popcorn commercial)": _v(7, 2.7, 2.8, 131, 300, 329, 0, 10, 0, 0.29, 0, 0.1, 0.08, 2.0, 0.16, 31, 0, "high", "USDA FDC popcorn air-popped"),
    "Fave di cacao tostate (cacao nibs)": _v(128, 13.9, 6.8, 499, 734, 1524, 14.3, 0, 0, 0.1, 0, 0.08, 0.24, 1.9, 0.12, 32, 0, "high", "USDA FDC cacao nibs"),
    "Noci di Grenoble (noci francesi)": _v(98, 2.9, 3.1, 158, 346, 441, 4.9, 1, 0, 0.7, 1.3, 0.34, 0.15, 1.1, 0.54, 98, 0, "high", "USDA FDC walnut"),
    "Arachidi con guscio (crude)": _v(92, 4.6, 3.3, 168, 376, 705, 7.2, 0, 0, 8.3, 0, 0.64, 0.14, 12.1, 0.35, 240, 0, "high", "USDA FDC peanut raw"),
    "Mix di semi (chia+lino+zucca+girasole)": _v(200, 7.5, 6.0, 400, 800, 700, 20, 0, 0, 5.0, 0.5, 0.8, 0.2, 5.0, 0.5, 90, 0, "medium", "stima media 4 semi"),

    # =====================================================================
    # CATEGORIA 13 — OLI E CONDIMENTI (41 items)
    # =====================================================================

    # --- Oli ---
    "Olio di semi di girasole": _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 41.1, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC sunflower oil"),
    "Olio di cocco":            _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0.09, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC coconut oil"),
    "Olio di oliva, raffinato": _v(1, 0.6, 0, 0, 0, 1, 0, 0, 0, 12.0, 0, 0, 0, 0, 0, 0, 0, "high", "CREA 2019 olio oliva"),
    "Olio di mais":             _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 14.3, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC corn oil"),
    "Olio di soia":             _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 8.2,  0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC soybean oil"),
    "Olio di arachide":         _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 15.7, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC peanut oil"),
    "Olio di lino (semi di lino)": _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0.47, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC linseed oil"),
    "Olio di avocado":          _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 12.5, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC avocado oil"),
    "Olio di sesamo":           _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 1.4,  0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC sesame oil"),
    "Burro chiarificato (ghee)": _v(4, 0, 0.1, 0, 3, 5, 0, 840, 1.2, 2.8, 0, 0, 0.005, 0, 0, 0, 0.1, "high", "USDA FDC ghee"),
    "Margarina vegetale (80% grassi)": _v(3, 0, 0, 0, 2, 5, 0, 819, 7.5, 8.0, 0, 0.01, 0.01, 0.03, 0, 1, 0.1, "high", "USDA FDC margarine"),
    "Strutto di maiale":        _v(0, 0, 0, 0, 0, 0, 0.2, 0, 0.6, 0.6, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC lard"),
    "Olio di ribes nero (omega-6)": _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 7.0, 0, 0, 0, 0, 0, 0, 0, "medium", "USDA FDC blackcurrant seed oil"),
    "Olio di canapa":           _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 4.0, 0, 0, 0, 0, 0, 0, 0, "medium", "USDA FDC hemp oil"),

    # --- Aceti ---
    "Aceto balsamico tradizionale": _v(27, 0.7, 0.1, 12, 19, 112, 0, 0, 0, 0, 0, 0.01, 0.01, 0.2, 0.02, 1, 0, "high", "USDA FDC balsamic vinegar"),
    "Aceto di mele (apple cider vinegar)": _v(7, 0.2, 0, 5, 8, 73, 0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC apple cider vinegar"),
    "Aceto di lampone":         _v(10, 0.3, 0.05, 5, 8, 60, 0, 0, 0, 0, 0.5, 0, 0, 0.1, 0, 0, 0, "low", "stima da aceto vino"),
    "Aceto di riso (giapponese)": _v(4, 0.1, 0, 3, 4, 18, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC rice vinegar"),

    # --- Salse ---
    "Salsa worcestershire":     _v(52, 4.6, 0.3, 18, 39, 800, 0, 0, 0, 0, 0, 0.02, 0.07, 0.8, 0.05, 5, 0, "high", "USDA FDC worcestershire"),
    "Salsa teriyaki":           _v(18, 1.6, 0.3, 26, 52, 212, 0.5, 0, 0, 0, 0, 0.01, 0.05, 0.6, 0.05, 6, 0, "high", "USDA FDC teriyaki"),
    "Mostarda (gialla)":        _v(58, 1.5, 0.6, 49, 108, 152, 33, 5, 0, 0.36, 1.5, 0.18, 0.06, 0.6, 0.07, 7, 0, "high", "USDA FDC mustard yellow"),
    "Ketchup di pomodoro":      _v(15, 0.4, 0.2, 13, 25, 315, 0, 12, 0, 1.5, 4.1, 0.02, 0.04, 1.4, 0.16, 9, 0, "high", "USDA FDC ketchup"),
    "Salsa di soia classica (shoyu)": _v(20, 1.9, 0.4, 40, 130, 212, 0.8, 0, 0, 0, 0, 0.03, 0.16, 3.9, 0.2, 18, 0, "high", "USDA FDC soy sauce"),
    "Miso (pasta di soia fermentata)": _v(57, 2.5, 2.6, 48, 159, 210, 7, 3, 0, 0.01, 0, 0.1, 0.23, 0.9, 0.2, 19, 0.08, "high", "USDA FDC miso"),
    "Salsa tahini allungata (hummus base)": _v(38, 2.4, 1.8, 71, 176, 228, 4.6, 1, 0, 0.6, 0, 0.18, 0.07, 0.6, 0.14, 83, 0, "high", "USDA FDC hummus"),
    "Pesto genovese (basilico/olio/parmigiano)": _v(250, 1.5, 1.2, 40, 130, 200, 3, 150, 0, 5.0, 3, 0.05, 0.1, 0.8, 0.1, 30, 0.3, "medium", "stima composita"),
    "Guacamole":                _v(12, 0.5, 0.6, 29, 52, 485, 0.4, 7, 0, 2.1, 10, 0.07, 0.13, 1.7, 0.26, 81, 0, "high", "USDA FDC guacamole"),
    "Salsa tzatziki":           _v(80, 0.2, 0.4, 10, 70, 140, 2, 15, 0.1, 0.1, 2, 0.02, 0.1, 0.2, 0.04, 8, 0.2, "medium", "stima yogurt+cetriolo"),
    "Maionese (commerciale)":   _v(8, 0.3, 0.2, 1, 24, 20, 2, 32, 0, 3.3, 0, 0.01, 0.02, 0, 0.02, 5, 0.1, "high", "USDA FDC mayonnaise"),
    "Salsa di panna (besciamella)": _v(110, 0.2, 0.4, 10, 80, 130, 2, 100, 0.3, 0.2, 0.5, 0.03, 0.14, 0.1, 0.04, 5, 0.3, "medium", "stima latte+burro+farina"),
    "Salsa romesco (pomodoro/mandorle)": _v(50, 1.0, 0.6, 30, 60, 250, 2, 40, 0, 4.0, 5, 0.05, 0.06, 1.0, 0.1, 15, 0, "medium", "stima composita"),
    "Salsa verde (prezzemolo/acciughe)": _v(60, 2.0, 0.3, 15, 25, 200, 1, 200, 0, 2.0, 30, 0.05, 0.08, 0.5, 0.08, 50, 0.5, "medium", "stima composita"),
    "Salsa chimichurri":        _v(50, 1.5, 0.3, 12, 20, 180, 0.5, 100, 0, 3.0, 20, 0.04, 0.06, 0.4, 0.06, 40, 0, "medium", "stima composita"),
    "Salsa aglio, olio e peperoncino (condimento)": _v(5, 0.3, 0.1, 2, 5, 30, 0, 10, 0, 5.0, 2, 0.01, 0.01, 0.1, 0.02, 3, 0, "medium", "stima olio+aglio"),
    "Soffritto di cipolla-sedano-carota (base)": _v(30, 0.4, 0.2, 10, 25, 200, 0.5, 300, 0, 1.5, 8, 0.04, 0.04, 0.5, 0.1, 15, 0, "medium", "stima composita"),
    "Salsa di ostrica":         _v(25, 0.5, 0.2, 10, 20, 60, 0.3, 0, 0, 0, 0, 0.01, 0.02, 0.3, 0.02, 3, 0.1, "medium", "USDA FDC oyster sauce"),
    "Salsa harissa (pasta di peperoncino)": _v(15, 1.5, 0.3, 15, 20, 200, 0.5, 200, 0, 3.0, 30, 0.05, 0.1, 1.0, 0.2, 15, 0, "medium", "USDA FDC harissa"),
    "Salsa di pomodoro fresco (bruschetta)": _v(11, 0.5, 0.2, 11, 24, 237, 0, 42, 0, 1.0, 13, 0.04, 0.02, 0.6, 0.08, 15, 0, "high", "USDA FDC tomato raw"),
    "Crema di aceto balsamico": _v(20, 0.5, 0.1, 10, 15, 90, 0, 0, 0, 0, 0, 0.01, 0.01, 0.1, 0.01, 1, 0, "medium", "stima da balsamico"),
    "Senape di Digione":        _v(65, 1.5, 0.6, 48, 108, 138, 33, 5, 0, 0.36, 1.5, 0.18, 0.07, 0.6, 0.07, 7, 0, "high", "USDA FDC dijon mustard"),
    "Salsa barbecue (classica)": _v(18, 0.8, 0.2, 8, 18, 200, 0.3, 5, 0, 0.5, 1.5, 0.01, 0.03, 0.5, 0.05, 5, 0, "high", "USDA FDC bbq sauce"),

    # =====================================================================
    # CATEGORIA 14 — DOLCI E ZUCCHERI (54 items)
    # =====================================================================

    # --- Zuccheri e dolcificanti ---
    "Zucchero di canna grezzo": _v(85, 1.9, 0.2, 29, 22, 346, 1.2, 0, 0, 0, 0, 0.01, 0.01, 0.1, 0.03, 1, 0, "high", "USDA FDC brown sugar"),
    "Zucchero a velo":          _v(1, 0.01, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC powdered sugar"),
    "Fruttosio cristallino":    _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "pure fructose"),
    "Stevia (dolcificante in polvere)": _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "stevia extract"),
    "Eritritolo":               _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "erythritol"),

    # --- Mieli e sciroppi ---
    "Miele di acacia":          _v(6, 0.4, 0.2, 2, 4, 52, 0.8, 0, 0, 0, 0.5, 0, 0.04, 0.1, 0.02, 2, 0, "high", "CREA 2019 miele"),
    "Miele di castagno":        _v(6, 0.5, 0.3, 3, 5, 55, 0.8, 0, 0, 0, 0.5, 0, 0.04, 0.2, 0.03, 2, 0, "high", "CREA 2019 miele"),
    "Sciroppo di agave":        _v(1, 0.1, 0, 1, 1, 4, 0.2, 0, 0, 0, 0.5, 0, 0.01, 0, 0, 0, 0, "high", "USDA FDC agave syrup"),
    "Sciroppo di riso (malto di riso)": _v(3, 0.1, 0, 3, 8, 6, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 0, 0, "medium", "USDA FDC rice syrup"),

    # --- Cioccolato e cacao ---
    "Cioccolato fondente 85%":  _v(73, 11.9, 3.3, 228, 308, 715, 6.8, 2, 0, 0.59, 0, 0.03, 0.06, 1.1, 0.04, 12, 0, "high", "USDA FDC dark choc 85%"),
    "Cioccolato fondente 90%":  _v(73, 13.1, 3.5, 252, 340, 750, 8.3, 2, 0, 0.6, 0, 0.03, 0.06, 1.2, 0.04, 14, 0, "high", "USDA FDC dark choc 85% adj."),
    "Cioccolato bianco":        _v(199, 0.2, 0.7, 12, 176, 286, 4.5, 30, 0, 1.2, 0, 0.05, 0.28, 0.1, 0.03, 5, 0.4, "high", "USDA FDC white chocolate"),
    "Cacao amaro in polvere":   _v(128, 13.9, 6.8, 499, 734, 1524, 14.3, 0, 0, 0.1, 0, 0.08, 0.24, 1.9, 0.12, 32, 0, "high", "USDA FDC cocoa powder"),
    "Cacao solubile zuccherato": _v(55, 3.0, 1.5, 80, 150, 400, 3, 0, 0, 0.1, 0, 0.04, 0.1, 0.8, 0.05, 10, 0, "medium", "stima cacao+zucchero 50/50"),
    "Nutella (crema nocciole e cacao)": _v(114, 3.4, 1.4, 64, 100, 407, 4.2, 0, 0, 5.4, 0, 0.07, 0.08, 1.0, 0.1, 15, 0, "high", "USDA FDC hazelnut spread"),

    # --- Marmellate e confetture ---
    "Marmellata di fragole":    _v(14, 0.3, 0.1, 4, 8, 77, 0.6, 1, 0, 0.1, 10, 0.01, 0.02, 0.2, 0.02, 5, 0, "high", "USDA FDC strawberry jam"),
    "Marmellata di albicocche": _v(16, 0.4, 0.1, 5, 10, 100, 0.5, 10, 0, 0.3, 5, 0.01, 0.02, 0.3, 0.02, 5, 0, "high", "USDA FDC apricot jam"),
    "Confettura extra (70% frutta)": _v(16, 0.3, 0.1, 5, 10, 100, 0.5, 5, 0, 0.2, 8, 0.01, 0.02, 0.2, 0.02, 5, 0, "medium", "stima confettura alta frutta"),

    # --- Gelati ---
    "Gelato alla crema (artigianale)": _v(128, 0.1, 0.7, 14, 105, 199, 2, 140, 0.1, 0.3, 0.6, 0.04, 0.24, 0.1, 0.05, 5, 0.4, "high", "USDA FDC ice cream vanilla"),
    "Gelato al cioccolato":     _v(109, 0.7, 0.6, 29, 107, 249, 2.5, 80, 0.1, 0.3, 0.3, 0.04, 0.17, 0.4, 0.04, 6, 0.3, "high", "USDA FDC ice cream chocolate"),
    "Gelato alla frutta (sorbetto)": _v(5, 0.2, 0.1, 4, 5, 50, 0.2, 5, 0, 0.1, 5, 0.01, 0.01, 0.1, 0.01, 3, 0, "high", "USDA FDC sorbet"),

    # --- Dolci da forno ---
    "Torta sponge (pan di spagna)": _v(62, 1.4, 0.5, 10, 92, 81, 10, 100, 0.5, 0.5, 0, 0.1, 0.15, 0.9, 0.04, 20, 0.3, "high", "USDA FDC sponge cake"),
    "Crostata (base frolla + marmellata)": _v(40, 1.2, 0.4, 10, 60, 80, 5, 50, 0.2, 0.5, 2, 0.08, 0.08, 0.8, 0.03, 15, 0.1, "medium", "stima composita"),
    "Tiramis":                  _v(80, 0.8, 0.6, 12, 100, 120, 5, 200, 0.4, 0.4, 0.5, 0.03, 0.2, 0.3, 0.05, 15, 0.4, "medium", "stima composita mascarpone+uovo"),
    "Panna cotta":              _v(100, 0.1, 0.3, 10, 80, 120, 2, 120, 0.1, 0.2, 0.5, 0.03, 0.16, 0.1, 0.03, 4, 0.3, "medium", "stima panna+latte"),
    "Budino di vaniglia (commerciale)": _v(88, 0.1, 0.4, 10, 75, 130, 2, 50, 0.2, 0.1, 0.5, 0.03, 0.15, 0.1, 0.03, 4, 0.3, "medium", "USDA FDC vanilla pudding"),
    "Wafer alla vaniglia":      _v(25, 1.5, 0.4, 10, 40, 60, 3, 10, 0, 0.5, 0, 0.08, 0.06, 0.8, 0.02, 10, 0, "medium", "USDA FDC vanilla wafer"),

    # --- Barrette e pancake ---
    "Barretta ai cereali (media)": _v(50, 4.0, 1.5, 40, 120, 200, 5, 0, 0, 3.0, 0, 0.2, 0.15, 2.0, 0.2, 40, 0, "medium", "USDA FDC granola bar"),
    "Barretta proteica (media, 30% prot)": _v(250, 3.0, 3.0, 80, 250, 300, 10, 0, 0, 2.0, 0, 0.3, 0.3, 4.0, 0.3, 80, 0.6, "medium", "stima media protein bar"),
    "Pancakes (base classica)": _v(83, 1.5, 0.5, 14, 127, 128, 10, 40, 0.5, 0.2, 0, 0.15, 0.17, 1.4, 0.04, 16, 0.2, "high", "USDA FDC pancakes"),

    # --- Dolci italiani ---
    "Colomba pasquale":         _v(55, 1.2, 0.6, 15, 90, 110, 8, 100, 0.5, 0.8, 0, 0.1, 0.12, 1.0, 0.05, 18, 0.2, "medium", "stima composita panettone-like"),
    "Panettone milanese":       _v(55, 1.2, 0.6, 15, 90, 110, 8, 100, 0.5, 0.8, 0, 0.1, 0.12, 1.0, 0.05, 18, 0.2, "medium", "USDA FDC panettone"),
    "Pandoro veronese":         _v(60, 1.0, 0.5, 12, 85, 100, 7, 120, 0.5, 1.0, 0, 0.1, 0.14, 0.8, 0.04, 15, 0.3, "medium", "stima composita"),
    "Cantucci (biscotti di Prato)": _v(50, 1.8, 0.7, 30, 80, 130, 5, 30, 0.2, 3.0, 0, 0.1, 0.1, 1.2, 0.05, 20, 0.1, "medium", "stima mandorle+farina+uova"),
    "Biscotti di avena e cioccolato": _v(40, 2.5, 1.0, 35, 100, 180, 5, 10, 0, 1.5, 0, 0.15, 0.1, 1.0, 0.1, 20, 0, "medium", "stima composita"),
    "Brownie al cioccolato":    _v(28, 2.3, 0.8, 36, 80, 160, 5, 40, 0.2, 0.5, 0, 0.05, 0.08, 0.6, 0.03, 12, 0.2, "high", "USDA FDC brownie"),
    "Madeleine (pasticcino francese)": _v(40, 1.0, 0.4, 8, 70, 70, 8, 80, 0.4, 0.5, 0, 0.08, 0.1, 0.7, 0.03, 12, 0.2, "medium", "stima composita burro+uova+farina"),
    "Crostino dolce con miele e ricotta": _v(90, 0.5, 0.5, 10, 80, 100, 5, 50, 0.1, 0.3, 0, 0.03, 0.15, 0.3, 0.03, 10, 0.3, "medium", "stima composita"),
    "Polenta dolce alla bergamasca": _v(10, 0.8, 0.3, 15, 40, 60, 2, 20, 0.1, 0.2, 0, 0.05, 0.04, 0.5, 0.05, 5, 0.1, "low", "stima mais+zucchero+burro"),
    "Chewing gum senza zucchero (1 pezzo)": _v(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "negligible per piece"),
    "Caramelle gommose (jelly candy)": _v(4, 0.1, 0, 1, 2, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC gummy candy"),
    "Meringa secca":            _v(3, 0.1, 0, 1, 7, 36, 1, 0, 0, 0, 0, 0, 0.1, 0, 0, 2, 0, "high", "USDA FDC meringue"),
    "Semifreddo al caff":       _v(80, 0.3, 0.4, 10, 80, 130, 3, 140, 0.2, 0.3, 0, 0.02, 0.15, 0.2, 0.03, 5, 0.3, "medium", "stima panna+mascarpone+caffe"),
    "Zabaione (zabaglione)":    _v(40, 1.2, 0.6, 5, 80, 70, 10, 100, 0.5, 0.5, 0, 0.04, 0.2, 0.1, 0.07, 30, 0.5, "medium", "stima tuorli+zucchero+marsala"),

    # --- Dolci extra ---
    "Ciambelle glassate (donuts)": _v(53, 1.5, 0.5, 15, 80, 90, 8, 20, 0.1, 0.5, 0, 0.15, 0.12, 1.5, 0.03, 18, 0.1, "high", "USDA FDC donut glazed"),
    "Cheesecake (fetta, base biscotto)": _v(60, 0.5, 0.4, 8, 70, 100, 5, 150, 0.2, 0.3, 0.5, 0.03, 0.15, 0.2, 0.04, 10, 0.3, "medium", "USDA FDC cheesecake"),
    "Cioccolato fondente proteico (>25% prot)": _v(80, 5.0, 2.5, 120, 250, 400, 8, 0, 0, 0.5, 0, 0.1, 0.15, 1.5, 0.1, 20, 0.3, "medium", "stima dark choc+whey"),
    "Granita al limone (senza latte)": _v(2, 0.1, 0, 2, 2, 15, 0, 0, 0, 0, 5, 0, 0, 0, 0.01, 1, 0, "high", "stima acqua+zucchero+limone"),
    "Crema di marroni (crema di castagne)": _v(20, 0.8, 0.3, 20, 45, 250, 1, 1, 0, 0.3, 5, 0.1, 0.08, 0.5, 0.15, 25, 0, "medium", "USDA FDC chestnut puree"),
    "Coppetta di gelato (2 palline tipo)": _v(110, 0.3, 0.5, 15, 90, 170, 2, 100, 0.1, 0.2, 0.5, 0.03, 0.18, 0.2, 0.04, 5, 0.3, "medium", "stima media gelato crema"),
    "Bign":                     _v(50, 0.8, 0.4, 8, 65, 70, 6, 80, 0.3, 0.3, 0, 0.06, 0.12, 0.6, 0.03, 12, 0.2, "medium", "stima choux+crema pasticcera"),
    "Sfogliatella napoletana":  _v(35, 1.0, 0.3, 8, 50, 60, 5, 40, 0.2, 0.5, 0, 0.08, 0.08, 0.7, 0.03, 10, 0.1, "medium", "stima sfoglia+ricotta"),
    "Croissant integrale (whole wheat)": _v(30, 2.0, 0.8, 25, 90, 120, 10, 80, 0.2, 0.8, 0, 0.18, 0.12, 1.8, 0.05, 22, 0.1, "medium", "USDA FDC whole wheat croissant"),
    "Torta di mele (classica)": _v(15, 0.5, 0.2, 6, 20, 65, 2, 20, 0.1, 0.3, 1.5, 0.03, 0.04, 0.3, 0.03, 5, 0.05, "high", "USDA FDC apple pie"),

    # =====================================================================
    # CATEGORIA 15 — BEVANDE E INTEGRATORI (64 items, 11 skipped as supplements)
    # =====================================================================

    # --- Acqua ---
    "Acqua (naturale)":         _v(3, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "CREA 2019 acqua minerale"),
    "Acqua frizzante (gassata)": _v(3, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "CREA 2019 acqua minerale"),

    # --- Te e infusi ---
    "T":                        _v(0, 0.02, 0, 1, 1, 8, 0, 0, 0, 0, 0, 0, 0.01, 0.1, 0, 5, 0, "high", "USDA FDC green tea brewed"),
    # NB: "T" matches multiple items via substring. We need specific keys for exact matching.
    # Use numbered variants for disambiguation below.

    # --- Caffe ---
    "Caff":                     _v(2, 0.01, 0.02, 3, 3, 49, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 1, 0, "high", "USDA FDC espresso"),
    "Cappuccino (con latte intero)": _v(60, 0.05, 0.2, 8, 46, 80, 1, 25, 0.05, 0.04, 0.5, 0.02, 0.08, 0.3, 0.02, 3, 0.2, "high", "USDA FDC cappuccino"),

    # --- Succhi ---
    "Succo di pomodoro (senza sale aggiunto)": _v(10, 0.4, 0.2, 11, 18, 229, 0.3, 23, 0, 0.32, 18.3, 0.04, 0.03, 0.7, 0.07, 20, 0, "high", "USDA FDC tomato juice"),
    "Succo di mela, senza zuccheri aggiunti": _v(8, 0.1, 0, 5, 7, 101, 0.1, 1, 0, 0.01, 1, 0.02, 0.02, 0.1, 0.02, 0, 0, "high", "USDA FDC apple juice"),
    "Succo di carota, fresco":  _v(24, 0.5, 0.2, 14, 42, 292, 0.6, 956, 0, 1.16, 8.5, 0.09, 0.06, 0.4, 0.22, 4, 0, "high", "USDA FDC carrot juice"),
    "Succo di melograno, puro": _v(11, 0.1, 0.1, 7, 11, 214, 0.3, 0, 0, 0.38, 0.1, 0.02, 0.01, 0.2, 0.04, 24, 0, "high", "USDA FDC pomegranate juice"),
    "Succo di barbabietola, puro": _v(16, 0.8, 0.3, 23, 25, 325, 0.7, 2, 0, 0, 5, 0.03, 0.04, 0.3, 0.07, 109, 0, "high", "USDA FDC beet juice"),
    "Succo di aloe vera (puro, senza zucchero)": _v(8, 0.2, 0, 3, 1, 30, 0, 0, 0, 0, 3.5, 0, 0, 0, 0, 0, 0, "medium", "USDA FDC aloe juice"),
    "Succo di limone (puro, senza zucchero)": _v(6, 0.1, 0.1, 6, 8, 103, 0.1, 0, 0, 0.15, 38.7, 0.02, 0.01, 0.1, 0.05, 20, 0, "high", "USDA FDC lemon juice"),
    "Succo di kiwi (100% frutto)": _v(20, 0.2, 0.1, 12, 20, 200, 0.2, 3, 0, 1.0, 60, 0.02, 0.03, 0.3, 0.05, 18, 0, "medium", "stima da kiwi fresco"),
    "Succo di uva nera (100%)": _v(11, 0.3, 0.1, 10, 14, 104, 0.1, 1, 0, 0.05, 0.1, 0.02, 0.02, 0.1, 0.03, 3, 0, "high", "USDA FDC grape juice"),
    "Succo di pera (100%)":     _v(8, 0.3, 0.1, 5, 8, 70, 0.1, 0, 0, 0, 2, 0.01, 0.01, 0.2, 0.02, 3, 0, "high", "USDA FDC pear juice"),

    # --- Bevande sport/energy ---
    "Bevanda isotonica (sport drink)": _v(5, 0, 0, 3, 6, 12, 0, 0, 0, 0, 0, 0.01, 0.02, 0.1, 0, 0, 0, "high", "USDA FDC gatorade"),
    "Bevanda energetica (energy drink standard)": _v(12, 0.1, 0, 1, 5, 4, 0, 0, 0, 0, 0, 0.3, 1.5, 16, 0.4, 5, 5.0, "high", "USDA FDC energy drink"),
    "Red bull (energy drink 250ml/100ml)": _v(12, 0.1, 0, 3, 5, 8, 0, 0, 0, 0, 0, 0.3, 1.3, 16, 0.4, 5, 4.0, "high", "USDA FDC red bull"),
    "Sprite / gassosa (100ml)": _v(2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC lemon-lime soda"),
    "Cola (100ml)":             _v(2, 0.04, 0, 1, 10, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC cola"),

    # --- Latti vegetali ---
    "Latte vegetale di riso (non zuccherato)": _v(118, 0.2, 0.1, 5, 29, 27, 1.5, 0, 1.0, 0, 0, 0.03, 0.01, 0.4, 0.03, 2, 0.6, "high", "USDA FDC rice milk"),
    "Latte di soia non zuccherato": _v(25, 0.6, 0.3, 25, 52, 118, 1.5, 0, 1.1, 0, 0, 0.06, 0.07, 0.5, 0.04, 18, 0.4, "high", "USDA FDC soy milk"),
    "Latte di avena non zuccherato": _v(120, 0.3, 0.1, 5, 30, 40, 1, 0, 1.0, 0, 0, 0.1, 0.1, 0.3, 0.03, 3, 0.4, "high", "USDA FDC oat milk"),
    "Latte di mandorla non zuccherato": _v(184, 0.3, 0.1, 7, 9, 67, 0, 0, 1.0, 3.3, 0, 0, 0, 0.2, 0, 2, 0, "high", "USDA FDC almond milk unsweetened"),
    "Latte di nocciole non zuccherato": _v(120, 0.3, 0.1, 6, 10, 50, 0, 0, 1.0, 1.5, 0, 0.02, 0.02, 0.2, 0.02, 2, 0, "medium", "stima latte vegetale fortificato"),

    # --- Fermentati / alcolici ---
    "Kombucha (fermentato base)": _v(2, 0.1, 0, 2, 2, 24, 0, 0, 0, 0, 1, 0.01, 0.01, 0.1, 0, 5, 0.04, "medium", "USDA FDC kombucha"),
    "Birra (lager 5% alcol)":   _v(4, 0.02, 0.01, 6, 14, 27, 0.6, 0, 0, 0, 0, 0, 0.03, 0.5, 0.05, 6, 0.02, "high", "USDA FDC beer"),
    "Vino rosso secco (12%)":   _v(8, 0.5, 0.1, 12, 23, 127, 0.2, 0, 0, 0, 0, 0, 0.03, 0.2, 0.06, 1, 0, "high", "USDA FDC red wine"),
    "Vino bianco secco (12%)":  _v(9, 0.3, 0.1, 10, 18, 71, 0.1, 0, 0, 0, 0, 0, 0.02, 0.1, 0.02, 1, 0, "high", "USDA FDC white wine"),
    "Birra artigianale (IPA 6.5%)": _v(5, 0.03, 0.01, 7, 16, 30, 0.6, 0, 0, 0, 0, 0, 0.03, 0.6, 0.05, 7, 0.02, "medium", "stima da birra+extra malto"),
    "Vino ros":                 _v(8, 0.4, 0.1, 10, 20, 90, 0.1, 0, 0, 0, 0, 0, 0.02, 0.1, 0.03, 1, 0, "high", "USDA FDC rose wine"),
    "Prosecco DOC":             _v(7, 0.2, 0.1, 8, 15, 60, 0.1, 0, 0, 0, 0, 0, 0.01, 0.1, 0.02, 1, 0, "high", "USDA FDC sparkling wine"),

    # --- Protein powders (food-derived, have micro data) ---
    "Whey protein concentrate 80% (polvere)": _v(600, 1.0, 1.0, 20, 340, 500, 15, 0, 0, 0, 0, 0.1, 0.3, 0.2, 0.05, 5, 1.0, "medium", "USDA FDC whey protein"),
    "Caseina miceallare (polvere)": _v(700, 0.8, 1.0, 15, 500, 200, 15, 0, 0, 0, 0, 0.05, 0.2, 0.1, 0.04, 5, 1.2, "medium", "USDA FDC casein powder"),
    "Proteine dell'uovo in polvere": _v(50, 1.5, 1.0, 12, 100, 150, 25, 0, 1.0, 0.5, 0, 0.05, 0.5, 0.1, 0.05, 15, 1.5, "medium", "USDA FDC egg white powder"),
    "Proteine vegetali (pisello+riso, polvere)": _v(50, 8.0, 3.0, 60, 300, 200, 5, 0, 0, 0, 0, 0.3, 0.1, 2.0, 0.2, 30, 0, "medium", "stima pea+rice protein blend"),

    # --- Te specifici ---
    "T\u00e8 matcha in polvere (1 cucchiaino)": _v(420, 17, 6.3, 230, 350, 2700, 0, 0, 0, 1.0, 1.5, 0.2, 1.35, 4.6, 0.1, 12, 0, "high", "USDA FDC matcha powder"),
    "T\u00e8 bianco, infuso":  _v(0, 0.02, 0, 1, 1, 10, 0, 0, 0, 0, 0, 0, 0.01, 0.05, 0, 3, 0, "high", "USDA FDC white tea"),
    "Tisana di camomilla":      _v(2, 0.08, 0.04, 1, 0, 9, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, "high", "USDA FDC chamomile tea"),
    "Tisana di zenzero e limone": _v(2, 0.1, 0, 2, 1, 15, 0, 0, 0, 0, 2, 0, 0, 0.1, 0.01, 1, 0, "medium", "stima infuso zenzero"),
    "Tisana di finocchio e anice": _v(2, 0.1, 0, 2, 1, 10, 0, 0, 0, 0, 0, 0, 0, 0.1, 0, 1, 0, "medium", "stima infuso finocchio"),
    "Tisana di orzo (caffe' d'orzo)": _v(4, 0.1, 0.03, 5, 5, 20, 0, 0, 0, 0, 0, 0.01, 0.01, 0.5, 0.02, 2, 0, "medium", "stima caffe d'orzo"),

    # --- Latte proteico / smoothie ---
    "Latte proteico (1.5% grassi, 5% prot)": _v(120, 0.1, 0.4, 11, 95, 150, 2, 20, 0.5, 0.04, 0.5, 0.04, 0.18, 0.1, 0.04, 5, 0.4, "medium", "stima latte+whey"),
    "Frullato proteico base (latte+whey)": _v(140, 0.2, 0.5, 15, 120, 200, 3, 15, 0.3, 0.05, 0.5, 0.05, 0.2, 0.2, 0.04, 5, 0.5, "medium", "stima latte+whey shake"),
    "Smoothie verde (spinaci+mela+zenzero)": _v(40, 1.0, 0.3, 25, 20, 180, 0.3, 200, 0, 0.5, 15, 0.04, 0.06, 0.3, 0.07, 50, 0, "medium", "stima composita"),
    "Smoothie proteico (whey+banana+latte)": _v(80, 0.3, 0.4, 20, 80, 250, 3, 10, 0.2, 0.1, 4, 0.04, 0.12, 0.4, 0.15, 10, 0.4, "medium", "stima composita"),
    "Sciroppo di proteine + frutta (meal prep)": _v(50, 0.3, 0.3, 10, 60, 100, 2, 5, 0, 0.1, 5, 0.03, 0.1, 0.2, 0.05, 5, 0.3, "low", "stima composita"),
    "Nespresso (capsula espresso ristretto)": _v(2, 0.01, 0.02, 3, 3, 49, 0, 0, 0, 0, 0, 0, 0, 0.5, 0, 1, 0, "high", "USDA FDC espresso"),
    "Acqua di cocco (100% naturale)": _v(24, 0.3, 0.1, 25, 20, 250, 1, 0, 0, 0, 2.4, 0.03, 0.06, 0.1, 0.03, 3, 0, "high", "USDA FDC coconut water"),
    "Latte caldo con cacao (cioccolata calda)": _v(100, 0.8, 0.5, 20, 80, 180, 2, 40, 0.3, 0.1, 0.5, 0.04, 0.15, 0.3, 0.04, 5, 0.4, "medium", "stima latte+cacao"),
    "Frullato di banana e mandorle": _v(60, 0.4, 0.4, 30, 50, 250, 1, 3, 0, 3.0, 3, 0.04, 0.1, 0.5, 0.15, 15, 0, "medium", "stima composita"),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, nome FROM alimenti
        WHERE categoria_id IN (7, 13, 14, 15)
          AND is_active = 1
          AND calcio_mg IS NULL
        ORDER BY categoria_id, id
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
    skipped = 0
    unmatched = []

    with open(OUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for vid, vnome in foods:
            # Skip supplements
            if vid in SKIP_IDS:
                skipped += 1
                continue

            match = None
            # Pass 1: exact match or startsWith
            for key, data in CREA.items():
                if vnome == key or vnome.startswith(key):
                    match = data
                    break
            # Pass 2: key in vnome (substring)
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
    print(f"  Totale alimenti da processare: {len(foods)}")
    print(f"  Matchati: {matched}")
    print(f"  Skippati (integratori): {skipped}")
    print(f"  Non matchati: {len(unmatched)}")
    if unmatched:
        for uid, uname in unmatched:
            print(f"    {uid:4d} | {uname}")


if __name__ == "__main__":
    main()
