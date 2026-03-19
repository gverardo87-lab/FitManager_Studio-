"""
Genera CSV micronutrienti per verdure e ortaggi (categoria 5).

Fonte primaria: CREA 2019 (Tabelle di Composizione degli Alimenti, IV ed.)
Fonte secondaria: USDA FoodData Central
Tutti i valori per 100g di prodotto edibile.

Uso: python -m tools.admin_scripts.generate_vegetables_csv
Output: data/nutrition/micronutrients_vegetables.csv
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
OUT_PATH = os.path.join(BASE_DIR, "nutrition", "micronutrients_vegetables.csv")

# ══════════════════════════════════════════════════════════════
# DATI CREA 2019 + USDA — Verdure e ortaggi (per 100g edibili)
# ══════════════════════════════════════════════════════════════
# Chiave: stringa che matcha l'inizio di Food.nome nel DB
# Confidence: high = dato CREA/USDA diretto, medium = adattato da alimento simile
#
# Campi: Ca, Fe, Zn, Mg, P, K, Se, VitA(RE), VitD, VitE, VitC,
#        B1, B2, B3, B6, B9(folato), B12
# ══════════════════════════════════════════════════════════════

def _v(ca, fe, zn, mg, p, k, se, va, vd, ve, vc, b1, b2, b3, b6, b9, b12, conf, src):
    """Helper: crea dict micro da valori posizionali."""
    return {
        "calcio_mg": ca, "ferro_mg": fe, "zinco_mg": zn, "magnesio_mg": mg,
        "fosforo_mg": p, "potassio_mg": k, "selenio_ug": se,
        "vitamina_a_ug": va, "vitamina_d_ug": vd, "vitamina_e_mg": ve,
        "vitamina_c_mg": vc, "vitamina_b1_mg": b1, "vitamina_b2_mg": b2,
        "vitamina_b3_mg": b3, "vitamina_b6_mg": b6, "vitamina_b9_ug": b9,
        "vitamina_b12_ug": b12, "confidence": conf, "source_detail": src,
    }

CREA = {
    # === AGLIO, CIPOLLA ===
    "Aglio":          _v(181, 1.7, 1.2, 25, 153, 401, 14.2, 0, 0, 0.01, 31.2, 0.2, 0.11, 0.7, 1.24, 3, 0, "high", "CREA 2019"),
    "Cipolla rossa":  _v(23, 0.2, 0.2, 10, 29, 146, 0.5, 0, 0, 0.02, 7.4, 0.05, 0.03, 0.1, 0.12, 19, 0, "high", "CREA 2019"),
    "Cipolla di Tropea": _v(20, 0.2, 0.2, 10, 27, 140, 0.5, 0, 0, 0.02, 6, 0.04, 0.03, 0.1, 0.1, 18, 0, "medium", "CREA 2019 cipolla"),
    "Cipolla bianca": _v(23, 0.2, 0.2, 10, 29, 146, 0.5, 0, 0, 0.02, 7.4, 0.05, 0.03, 0.1, 0.12, 19, 0, "medium", "CREA 2019 cipolla"),
    "Cipollotto":     _v(72, 1.5, 0.4, 20, 37, 276, 0.6, 50, 0, 0.55, 8, 0.06, 0.02, 0.5, 0.06, 64, 0, "high", "CREA 2019 scalogno"),
    "Porro":          _v(59, 2.1, 0.1, 28, 35, 180, 1.0, 83, 0, 0.92, 12, 0.06, 0.03, 0.4, 0.23, 64, 0, "high", "CREA 2019"),

    # === BRASSICACEAE ===
    "Cavolfiore":     _v(22, 0.4, 0.3, 15, 44, 299, 0.6, 0, 0, 0.08, 48.2, 0.05, 0.06, 0.5, 0.18, 57, 0, "high", "CREA 2019"),
    "Cavolo broccolo": _v(47, 0.7, 0.4, 21, 66, 316, 2.5, 31, 0, 0.78, 89.2, 0.07, 0.12, 0.6, 0.18, 63, 0, "high", "CREA 2019"),
    "Cavolo di Bruxelles, crudo": _v(42, 1.4, 0.4, 23, 69, 389, 1.6, 38, 0, 0.88, 85, 0.14, 0.09, 0.7, 0.22, 61, 0, "high", "CREA 2019"),
    "Cavolo di Bruxelles, cotto": _v(36, 1.2, 0.3, 20, 56, 317, 1.5, 35, 0, 0.7, 62, 0.1, 0.07, 0.6, 0.18, 50, 0, "high", "CREA 2019"),
    "Cavolo cappuccio, cotto": _v(40, 0.5, 0.2, 12, 26, 170, 0.3, 5, 0, 0.15, 36.6, 0.06, 0.04, 0.2, 0.12, 43, 0, "high", "CREA 2019"),
    "Cavolo cappuccio viola": _v(45, 0.8, 0.2, 16, 30, 243, 0.6, 56, 0, 0.11, 57, 0.06, 0.07, 0.4, 0.21, 18, 0, "high", "USDA FDC"),
    "Cavolo nero toscano (crudo)": _v(150, 1.5, 0.6, 47, 92, 491, 0.9, 500, 0, 1.5, 120, 0.11, 0.13, 1.0, 0.27, 141, 0, "high", "USDA FDC kale"),
    "Cavolo nero toscano (cotto)": _v(130, 1.2, 0.5, 40, 73, 350, 0.8, 450, 0, 1.2, 70, 0.07, 0.1, 0.7, 0.2, 80, 0, "medium", "USDA FDC kale cooked"),
    "Broccoli romanesco": _v(32, 0.5, 0.3, 17, 50, 280, 0.7, 20, 0, 0.5, 60, 0.06, 0.07, 0.5, 0.16, 50, 0, "medium", "CREA 2019 cavolfiore"),
    "Broccoletti":    _v(40, 0.7, 0.4, 22, 60, 300, 1.0, 30, 0, 0.7, 80, 0.07, 0.1, 0.6, 0.17, 60, 0, "medium", "USDA broccoli rabe"),
    "Cavoletti di Bruxelles arrosto": _v(36, 1.2, 0.3, 20, 56, 317, 1.5, 35, 0, 0.7, 62, 0.1, 0.07, 0.6, 0.18, 50, 0, "medium", "CREA cavoletti cotti"),
    "Cime di rapa":   _v(97, 1.1, 0.4, 22, 65, 390, 0.7, 225, 0, 0.8, 110, 0.09, 0.17, 1.0, 0.17, 83, 0, "high", "CREA 2019"),
    "Cavolo rapa":    _v(24, 0.4, 0.03, 19, 46, 350, 0.7, 2, 0, 0.48, 62, 0.05, 0.02, 0.6, 0.15, 16, 0, "high", "USDA FDC kohlrabi"),
    "Verza":          _v(35, 0.4, 0.2, 12, 42, 230, 0.3, 5, 0, 0.17, 31, 0.05, 0.04, 0.3, 0.19, 80, 0, "high", "CREA 2019"),

    # === SOLANACEAE ===
    "Peperone rosso":  _v(10, 0.4, 0.2, 12, 26, 211, 0.1, 157, 0, 1.58, 128, 0.05, 0.09, 1.0, 0.29, 46, 0, "high", "CREA 2019"),
    "Peperone giallo": _v(11, 0.5, 0.2, 12, 24, 212, 0.3, 10, 0, 0.5, 184, 0.03, 0.03, 1.0, 0.17, 26, 0, "high", "USDA FDC"),
    "Peperone verde":  _v(10, 0.3, 0.1, 10, 20, 175, 0.1, 18, 0, 0.37, 80.4, 0.06, 0.03, 0.5, 0.22, 10, 0, "high", "CREA 2019"),
    "Peperoncino fresco": _v(14, 1.0, 0.3, 23, 43, 322, 0.5, 48, 0, 0.69, 144, 0.07, 0.09, 1.2, 0.51, 23, 0, "high", "USDA FDC"),
    "Melanzana, cruda": _v(9, 0.2, 0.2, 14, 24, 229, 0.3, 1, 0, 0.3, 2.2, 0.04, 0.04, 0.6, 0.08, 22, 0, "high", "CREA 2019"),
    "Melanzana, cotta": _v(7, 0.2, 0.1, 11, 18, 172, 0.2, 1, 0, 0.25, 1.3, 0.03, 0.02, 0.5, 0.07, 14, 0, "high", "CREA 2019"),
    "Pomodorini":     _v(11, 0.3, 0.2, 11, 27, 250, 0.4, 42, 0, 0.54, 23, 0.04, 0.02, 0.6, 0.08, 15, 0, "high", "CREA 2019"),
    "Pomodoro da insalata": _v(10, 0.3, 0.2, 11, 24, 237, 0.4, 42, 0, 0.54, 21, 0.04, 0.02, 0.6, 0.08, 15, 0, "high", "CREA 2019"),
    "Pomodoro secco":  _v(110, 9.1, 1.9, 194, 356, 3427, 5.5, 44, 0, 0.01, 39.2, 0.53, 0.49, 9.1, 0.33, 68, 0, "high", "USDA FDC"),
    "Pomodoro San Marzano": _v(10, 0.3, 0.2, 11, 24, 237, 0.4, 42, 0, 0.54, 21, 0.04, 0.02, 0.6, 0.08, 15, 0, "medium", "CREA 2019 pomodoro"),
    "Passata di pomodoro": _v(11, 0.5, 0.2, 18, 32, 293, 0.5, 25, 0, 2.8, 12, 0.04, 0.05, 1.3, 0.15, 11, 0, "high", "USDA FDC"),
    "Concentrato di pomodoro": _v(36, 2.9, 0.6, 50, 83, 1014, 1.2, 63, 0, 5.0, 21.9, 0.1, 0.15, 4.3, 0.22, 13, 0, "high", "USDA FDC"),

    # === CUCURBITACEAE ===
    "Zucca": _v(21, 0.8, 0.3, 12, 44, 340, 0.3, 426, 0, 1.06, 9, 0.05, 0.11, 0.6, 0.06, 16, 0, "high", "CREA 2019"),
    "Zucca, cotta": _v(18, 0.6, 0.2, 10, 35, 270, 0.3, 400, 0, 0.8, 6, 0.04, 0.08, 0.4, 0.05, 12, 0, "medium", "CREA 2019"),
    "Zucchina chiara": _v(16, 0.3, 0.3, 18, 38, 261, 0.2, 10, 0, 0.12, 17.9, 0.05, 0.04, 0.5, 0.16, 24, 0, "high", "CREA 2019"),
    "Zucchina scura": _v(16, 0.3, 0.3, 18, 38, 261, 0.2, 10, 0, 0.12, 17.9, 0.05, 0.04, 0.5, 0.16, 24, 0, "high", "CREA 2019"),
    "Zucchine, cotte": _v(14, 0.3, 0.3, 16, 33, 220, 0.2, 8, 0, 0.1, 12, 0.04, 0.03, 0.4, 0.12, 18, 0, "medium", "CREA 2019 cotte"),
    "Cetriolo": _v(16, 0.3, 0.2, 13, 24, 147, 0.3, 5, 0, 0.03, 2.8, 0.03, 0.03, 0.1, 0.04, 7, 0, "high", "CREA 2019"),

    # === LEAFY GREENS ===
    "Asparagi":       _v(23, 0.9, 0.6, 14, 54, 224, 6.1, 38, 0, 1.5, 7.7, 0.14, 0.13, 1.0, 0.07, 149, 0, "high", "CREA 2019"),
    "Basilico":       _v(177, 3.2, 0.8, 64, 56, 295, 0.3, 264, 0, 0.8, 18, 0.03, 0.08, 0.9, 0.16, 68, 0, "high", "USDA FDC"),
    "Bietola, cotta": _v(58, 1.8, 0.4, 86, 46, 379, 0.9, 306, 0, 1.89, 18, 0.03, 0.09, 0.4, 0.09, 9, 0, "high", "CREA 2019"),
    "Bietola rossa":  _v(51, 1.8, 0.4, 81, 46, 379, 0.9, 306, 0, 1.89, 30, 0.04, 0.09, 0.4, 0.1, 14, 0, "medium", "CREA 2019 bietola"),
    "Bietole colorate": _v(55, 1.8, 0.4, 84, 46, 379, 0.9, 306, 0, 1.89, 18, 0.03, 0.09, 0.4, 0.09, 9, 0, "medium", "CREA 2019 bietola"),
    "Catalogna":      _v(74, 0.8, 0.3, 12, 31, 182, 0.3, 267, 0, 0.4, 10, 0.03, 0.06, 0.3, 0.06, 48, 0, "high", "CREA 2019"),
    "Cicoria":        _v(100, 0.9, 0.4, 30, 47, 420, 0.3, 286, 0, 2.3, 24, 0.06, 0.1, 0.5, 0.11, 110, 0, "high", "CREA 2019"),
    "Crescione":      _v(81, 0.2, 0.1, 21, 60, 330, 0.9, 160, 0, 1.0, 43, 0.09, 0.12, 0.2, 0.13, 9, 0, "high", "USDA FDC"),
    "Indivia":        _v(19, 0.2, 0.2, 10, 26, 211, 0.2, 1, 0, 0.11, 2.8, 0.06, 0.03, 0.2, 0.04, 37, 0, "high", "CREA 2019"),
    "Lattuga iceberg": _v(18, 0.4, 0.2, 7, 20, 141, 0.1, 25, 0, 0.18, 2.8, 0.04, 0.03, 0.1, 0.04, 29, 0, "high", "CREA 2019"),
    "Lattuga romana":  _v(33, 1.0, 0.2, 14, 30, 247, 0.4, 436, 0, 0.13, 24, 0.07, 0.07, 0.3, 0.07, 136, 0, "high", "USDA FDC"),
    "Rucola":         _v(160, 1.5, 0.5, 47, 52, 369, 0.3, 119, 0, 0.43, 15, 0.04, 0.09, 0.3, 0.07, 97, 0, "high", "CREA/USDA"),
    "Songino":        _v(38, 2.2, 0.5, 13, 49, 459, 0.9, 355, 0, 0.6, 38.2, 0.06, 0.07, 0.4, 0.07, 14, 0, "high", "USDA FDC"),
    "Radicchio":      _v(19, 0.6, 0.6, 13, 40, 302, 0.9, 27, 0, 2.26, 8, 0.02, 0.03, 0.3, 0.06, 60, 0, "high", "CREA 2019"),
    "Spinaci, crudi": _v(99, 2.7, 0.5, 79, 49, 558, 1.0, 469, 0, 2.03, 28.1, 0.08, 0.19, 0.7, 0.2, 194, 0, "high", "CREA 2019"),
    "Spinaci, cotti": _v(136, 3.6, 0.8, 87, 56, 466, 1.5, 524, 0, 2.1, 9.8, 0.1, 0.24, 0.5, 0.24, 146, 0, "high", "CREA 2019"),
    "Prezzemolo":     _v(138, 6.2, 1.1, 50, 58, 554, 0.1, 421, 0, 1.33, 133, 0.09, 0.1, 1.3, 0.09, 152, 0, "high", "CREA 2019"),

    # === ROOT / TUBER ===
    "Barbabietola rossa, cruda": _v(16, 0.8, 0.4, 23, 40, 325, 0.7, 2, 0, 0.04, 4.9, 0.03, 0.04, 0.3, 0.07, 109, 0, "high", "CREA 2019"),
    "Barbabietola, cotta": _v(16, 0.8, 0.4, 23, 38, 305, 0.7, 2, 0, 0.04, 3.6, 0.03, 0.04, 0.3, 0.07, 80, 0, "high", "CREA 2019"),
    "Daikon":         _v(27, 0.4, 0.2, 16, 23, 227, 0.7, 0, 0, 0, 22, 0.02, 0.02, 0.2, 0.05, 28, 0, "high", "USDA FDC"),
    "Ravanello":      _v(25, 0.3, 0.3, 10, 20, 233, 0.6, 7, 0, 0, 14.8, 0.01, 0.04, 0.3, 0.07, 25, 0, "high", "CREA 2019"),
    "Topinambur":     _v(14, 3.4, 0.1, 17, 78, 429, 0.7, 1, 0, 0.19, 4, 0.2, 0.06, 1.3, 0.08, 13, 0, "high", "USDA FDC"),
    "Pastinaca":      _v(36, 0.6, 0.6, 29, 71, 375, 1.8, 0, 0, 1.49, 17, 0.09, 0.05, 0.7, 0.09, 67, 0, "high", "USDA FDC"),
    "Patata dolce":   _v(30, 0.6, 0.3, 25, 47, 337, 0.6, 709, 0, 0.26, 2.4, 0.08, 0.06, 0.6, 0.21, 11, 0, "high", "USDA FDC"),
    "Patata":         _v(12, 0.8, 0.3, 23, 57, 421, 0.4, 0, 0, 0.01, 19.7, 0.08, 0.03, 1.1, 0.3, 15, 0, "high", "CREA 2019"),
    "Patata, cotta":  _v(8, 0.3, 0.3, 20, 40, 328, 0.3, 0, 0, 0.01, 7.4, 0.1, 0.02, 1.3, 0.3, 9, 0, "high", "CREA 2019"),

    # === MISC VEGETABLES ===
    "Avocado":        _v(12, 0.6, 0.6, 29, 52, 485, 0.4, 7, 0, 2.07, 10, 0.07, 0.13, 1.7, 0.26, 81, 0, "high", "USDA FDC"),
    "Cachi":          _v(8, 0.2, 0.1, 9, 17, 161, 0.6, 81, 0, 0.73, 7.5, 0.03, 0.02, 0.1, 0.1, 8, 0, "high", "USDA FDC persimmon"),
    "Capperi":        _v(40, 1.7, 0.3, 33, 10, 40, 1.2, 7, 0, 0.88, 4.3, 0.02, 0.14, 0.7, 0.02, 23, 0, "high", "USDA FDC"),
    "Carciofo, crudo": _v(44, 1.3, 0.5, 60, 90, 370, 0.2, 0, 0, 0.19, 11.7, 0.07, 0.07, 1.0, 0.12, 68, 0, "high", "CREA 2019"),
    "Carciofo, cotto": _v(40, 1.0, 0.4, 50, 75, 300, 0.2, 0, 0, 0.15, 7.4, 0.05, 0.05, 0.7, 0.1, 50, 0, "medium", "CREA 2019 cotto"),
    "Finocchio":      _v(49, 0.7, 0.2, 17, 50, 414, 0.7, 7, 0, 0.58, 12, 0.01, 0.03, 0.6, 0.05, 27, 0, "high", "CREA 2019"),
    "Funghi champignon": _v(3, 0.5, 0.5, 9, 86, 318, 9.3, 0, 0.2, 0.01, 2.1, 0.08, 0.4, 3.6, 0.1, 17, 0.04, "high", "CREA 2019"),
    "Funghi porcini":  _v(5, 0.6, 0.8, 12, 100, 350, 7.0, 0, 0.3, 0.01, 3, 0.1, 0.45, 4.0, 0.1, 20, 0, "medium", "CREA 2019 porcini"),
    "Funghi pleurotus": _v(3, 1.3, 0.8, 18, 120, 420, 3.0, 0, 0.4, 0.01, 0, 0.13, 0.35, 5.0, 0.1, 38, 0, "medium", "USDA FDC oyster mushroom"),
    "Funghi misti":   _v(4, 0.8, 0.6, 13, 100, 360, 6.5, 0, 0.3, 0.01, 2, 0.1, 0.38, 3.8, 0.1, 25, 0, "medium", "media CREA funghi"),
    "Olive nere":     _v(88, 3.3, 0.2, 4, 3, 8, 0.9, 20, 0, 1.65, 0, 0, 0, 0.04, 0.01, 0, 0, "high", "CREA 2019"),
    "Olive verdi":    _v(52, 0.5, 0.04, 11, 4, 42, 0.9, 56, 0, 3.81, 0, 0.02, 0, 0.24, 0.03, 3, 0, "high", "USDA FDC"),
    "Sedano":         _v(40, 0.2, 0.1, 11, 24, 260, 0.4, 22, 0, 0.27, 3.1, 0.02, 0.06, 0.3, 0.07, 36, 0, "high", "CREA 2019"),
    "Sedano rapa":    _v(43, 0.7, 0.3, 20, 115, 300, 0.7, 0, 0, 0.36, 8, 0.05, 0.06, 0.7, 0.17, 8, 0, "high", "USDA FDC"),
    "Mais dolce":     _v(2, 0.5, 0.5, 37, 89, 270, 0.6, 10, 0, 0.07, 6.8, 0.2, 0.06, 1.7, 0.06, 46, 0, "high", "CREA 2019"),
    "Mais dolce, cotto": _v(2, 0.5, 0.5, 32, 77, 248, 0.6, 10, 0, 0.06, 5.5, 0.15, 0.05, 1.5, 0.05, 36, 0, "medium", "CREA 2019 cotto"),
    "Piselli":        _v(25, 1.5, 1.2, 33, 108, 244, 1.8, 38, 0, 0.13, 40, 0.27, 0.13, 2.1, 0.17, 65, 0, "high", "CREA 2019"),
    "Piselli, cotti": _v(23, 1.3, 1.0, 30, 95, 217, 1.6, 35, 0, 0.1, 14, 0.2, 0.1, 1.6, 0.14, 50, 0, "medium", "CREA 2019 cotti"),
    "Peperoni arrostiti": _v(10, 0.4, 0.2, 12, 25, 200, 0.1, 120, 0, 1.2, 100, 0.04, 0.07, 0.8, 0.22, 35, 0, "medium", "CREA peperone cotto"),
    "Zenzero fresco": _v(16, 0.6, 0.3, 43, 34, 415, 0.7, 0, 0, 0.26, 5, 0.03, 0.03, 0.75, 0.16, 11, 0, "high", "USDA FDC"),
    "Curcuma fresca": _v(183, 41.4, 4.4, 193, 268, 2525, 4.4, 0, 0, 3.1, 25.9, 0.15, 0.23, 5.1, 1.8, 39, 0, "high", "USDA FDC turmeric"),

    # === VARIANTI PATATE ===
    "Patate, crude":  _v(12, 0.8, 0.3, 23, 57, 421, 0.4, 0, 0, 0.01, 19.7, 0.08, 0.03, 1.1, 0.3, 15, 0, "high", "CREA 2019"),
    "Patate, cotte al forno": _v(10, 0.6, 0.3, 22, 50, 380, 0.3, 0, 0, 0.01, 12, 0.07, 0.03, 1.2, 0.27, 12, 0, "medium", "CREA 2019 cotte"),
    "Patate al vapore": _v(8, 0.3, 0.3, 20, 40, 328, 0.3, 0, 0, 0.01, 7.4, 0.1, 0.02, 1.3, 0.3, 9, 0, "medium", "CREA 2019 bollite"),
    "Patate dolci (batata), crude": _v(30, 0.6, 0.3, 25, 47, 337, 0.6, 709, 0, 0.26, 2.4, 0.08, 0.06, 0.6, 0.21, 11, 0, "high", "USDA FDC sweet potato"),
    "Patate dolci, cotte": _v(27, 0.5, 0.3, 18, 32, 230, 0.2, 960, 0, 0.71, 12.8, 0.07, 0.05, 0.5, 0.17, 6, 0, "high", "USDA FDC sweet potato baked"),

    # === VARIANTI POMODORO ===
    "Pomodori ciliegino": _v(11, 0.3, 0.2, 11, 27, 250, 0.4, 42, 0, 0.54, 23, 0.04, 0.02, 0.6, 0.08, 15, 0, "high", "CREA 2019 pomodoro"),
    "Pomodori datterini": _v(11, 0.3, 0.2, 11, 27, 250, 0.4, 42, 0, 0.54, 23, 0.04, 0.02, 0.6, 0.08, 15, 0, "medium", "CREA 2019 pomodoro"),
    "Pomodori ramati": _v(10, 0.3, 0.2, 11, 24, 237, 0.4, 42, 0, 0.54, 21, 0.04, 0.02, 0.6, 0.08, 15, 0, "medium", "CREA 2019 pomodoro"),
    "Pomodori pelati": _v(24, 0.5, 0.2, 12, 21, 217, 0.3, 25, 0, 0.5, 13, 0.04, 0.03, 0.8, 0.1, 11, 0, "high", "USDA FDC canned tomato"),
    "Pomodori verdi": _v(13, 0.5, 0.1, 10, 28, 204, 0.4, 32, 0, 0.38, 23.4, 0.06, 0.04, 0.5, 0.08, 9, 0, "high", "USDA FDC green tomato"),
    "Pomodoro, concentrato (doppio)": _v(36, 2.9, 0.6, 50, 83, 1014, 1.2, 63, 0, 5.0, 21.9, 0.1, 0.15, 4.3, 0.22, 13, 0, "high", "USDA FDC"),
    "Pomodoro, passata (senza sale)": _v(11, 0.5, 0.2, 18, 32, 293, 0.5, 25, 0, 2.8, 12, 0.04, 0.05, 1.3, 0.15, 11, 0, "high", "USDA FDC"),

    # === ERBE AROMATICHE ===
    "Erba cipollina": _v(92, 1.6, 0.4, 42, 58, 296, 0.9, 218, 0, 0.21, 58, 0.08, 0.12, 0.6, 0.14, 105, 0, "high", "USDA FDC chives"),
    "Menta fresca":   _v(243, 5.1, 1.1, 80, 73, 569, 0.3, 212, 0, 0.73, 31.8, 0.08, 0.27, 1.7, 0.13, 114, 0, "high", "USDA FDC spearmint"),
    "Origano fresco": _v(310, 3.3, 0.9, 50, 76, 312, 1.0, 230, 0, 1.69, 2.3, 0.04, 0.32, 4.6, 1.04, 274, 0, "high", "USDA FDC oregano fresh"),
    "Rosmarino fresco": _v(317, 6.6, 0.9, 91, 66, 668, 0.4, 146, 0, 0, 21.8, 0.04, 0.15, 0.9, 0.34, 109, 0, "high", "USDA FDC rosemary"),
    "Timo fresco":    _v(405, 17.5, 1.8, 160, 106, 609, 0.5, 190, 0, 0, 160, 0.05, 0.47, 1.8, 0.35, 45, 0, "high", "USDA FDC thyme"),

    # === FUNGHI / GERMOGLI / ALTRO ===
    "Edamame":        _v(63, 2.3, 1.4, 64, 169, 436, 0.8, 9, 0, 0.68, 6.1, 0.2, 0.16, 1.3, 0.1, 311, 0, "high", "USDA FDC edamame"),
    "Funghi secchi":  _v(10, 1.2, 1.6, 24, 200, 700, 14, 0, 0.5, 0.02, 4, 0.2, 0.8, 7.2, 0.2, 40, 0, "medium", "USDA FDC dried mushroom"),
    "Funghi shiitake": _v(2, 0.4, 1.0, 20, 112, 304, 5.7, 0, 0.4, 0.01, 0, 0.02, 0.22, 3.9, 0.29, 13, 0, "high", "USDA FDC shiitake"),
    "Germogli di soia": _v(13, 0.9, 0.4, 21, 54, 149, 0.6, 1, 0, 0.1, 13.2, 0.08, 0.12, 0.7, 0.09, 61, 0, "high", "USDA FDC soybean sprouts"),
    "Germogli di pisello": _v(15, 0.8, 0.5, 18, 50, 140, 0.5, 12, 0, 0.08, 10, 0.06, 0.1, 0.5, 0.07, 40, 0, "medium", "USDA FDC pea shoots"),
    "Germogli di bamb": _v(13, 0.5, 1.1, 3, 59, 533, 0.8, 1, 0, 1.0, 4, 0.15, 0.07, 0.6, 0.24, 7, 0, "high", "USDA FDC bamboo shoots"),

    # === MENO COMUNI ===
    "Portulaca":      _v(65, 2.0, 0.2, 68, 44, 494, 0.9, 267, 0, 0, 21, 0.05, 0.11, 0.5, 0.07, 12, 0, "high", "USDA FDC purslane"),
    "Okra":           _v(82, 0.6, 0.6, 57, 61, 299, 0.7, 36, 0, 0.27, 23, 0.2, 0.06, 1.0, 0.22, 60, 0, "high", "USDA FDC okra"),
    "Radice di loto": _v(45, 1.2, 0.4, 23, 100, 556, 0.7, 0, 0, 0.24, 44, 0.16, 0.22, 0.4, 0.26, 13, 0, "high", "USDA FDC lotus root"),
    "Taro":           _v(43, 0.6, 0.3, 33, 84, 591, 0.7, 4, 0, 2.38, 4.5, 0.1, 0.03, 0.6, 0.28, 22, 0, "high", "USDA FDC taro"),
    "Senape, foglie": _v(115, 1.6, 0.3, 32, 58, 384, 0.9, 151, 0, 2.01, 70, 0.08, 0.11, 0.8, 0.18, 187, 0, "high", "USDA FDC mustard greens"),
    "Tarassaco":      _v(187, 3.1, 0.4, 36, 66, 397, 0.5, 508, 0, 3.44, 35, 0.19, 0.26, 0.8, 0.25, 27, 0, "high", "USDA FDC dandelion"),
    "Pak choi":       _v(105, 0.8, 0.2, 19, 37, 252, 0.5, 223, 0, 0.09, 45, 0.04, 0.07, 0.5, 0.19, 66, 0, "high", "USDA FDC bok choy"),
    "Rape":           _v(30, 0.3, 0.3, 11, 27, 191, 0.7, 0, 0, 0.03, 21, 0.04, 0.03, 0.4, 0.09, 15, 0, "high", "USDA FDC turnip"),
    "Ravanelli, crudi": _v(25, 0.3, 0.3, 10, 20, 233, 0.6, 7, 0, 0, 14.8, 0.01, 0.04, 0.3, 0.07, 25, 0, "high", "CREA 2019 ravanello"),
    "Spinaci baby":   _v(99, 2.7, 0.5, 79, 49, 558, 1.0, 469, 0, 2.03, 28.1, 0.08, 0.19, 0.7, 0.2, 194, 0, "high", "CREA 2019 spinaci"),

    # === PREPARAZIONI ===
    "Melanzane, grigliate": _v(7, 0.2, 0.1, 11, 18, 172, 0.2, 1, 0, 0.25, 1.3, 0.03, 0.02, 0.5, 0.07, 14, 0, "medium", "CREA 2019 melanzana cotta"),
    "Friggitelli":    _v(10, 0.3, 0.1, 10, 20, 175, 0.1, 18, 0, 0.37, 80, 0.06, 0.03, 0.5, 0.22, 10, 0, "medium", "CREA 2019 peperone verde"),
    "Peperoni gialli arrostiti": _v(10, 0.4, 0.2, 12, 25, 200, 0.1, 120, 0, 1.2, 100, 0.04, 0.07, 0.8, 0.22, 35, 0, "medium", "CREA peperone cotto"),
    "Peperoncino rosso": _v(14, 1.0, 0.3, 23, 43, 322, 0.5, 48, 0, 0.69, 144, 0.07, 0.09, 1.2, 0.51, 23, 0, "high", "USDA FDC hot pepper"),
    "Misticanza":     _v(50, 1.0, 0.3, 20, 35, 300, 0.3, 200, 0, 0.5, 15, 0.05, 0.07, 0.3, 0.07, 70, 0, "low", "stima media insalate miste CREA"),
    "Passata di verdure": _v(20, 0.4, 0.2, 12, 25, 200, 0.3, 100, 0, 0.5, 10, 0.04, 0.04, 0.4, 0.08, 20, 0, "low", "stima media verdure cotte CREA"),
    "Peperonata":     _v(12, 0.4, 0.2, 12, 25, 200, 0.2, 80, 0, 1.0, 60, 0.04, 0.05, 0.7, 0.18, 25, 0, "low", "stima peperoni cotti CREA"),
    "Zucchine lunghe": _v(16, 0.3, 0.3, 18, 38, 261, 0.2, 10, 0, 0.12, 17.9, 0.05, 0.04, 0.5, 0.16, 24, 0, "medium", "CREA 2019 zucchine"),
    "Zucchine, crude": _v(16, 0.3, 0.3, 18, 38, 261, 0.2, 10, 0, 0.12, 17.9, 0.05, 0.04, 0.5, 0.16, 24, 0, "high", "CREA 2019 zucchine"),
    "Finocchi, crudi": _v(49, 0.7, 0.2, 17, 50, 414, 0.7, 7, 0, 0.58, 12, 0.01, 0.03, 0.6, 0.05, 27, 0, "high", "CREA 2019 finocchio"),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT id, nome FROM alimenti
        WHERE categoria_id = 5 AND calcio_mg IS NULL
        ORDER BY nome
    """)
    vegetables = c.fetchall()
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

        for vid, vnome in vegetables:
            match = None
            # Exact or startswith match
            for key, data in CREA.items():
                if vnome == key or vnome.startswith(key):
                    match = data
                    break
            # Substring match
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
    print(f"  Matchati: {matched}/{len(vegetables)}")
    print(f"  Non matchati: {len(unmatched)}")
    if unmatched:
        print("  Alimenti senza match:")
        for uid, uname in unmatched:
            print(f"    {uid:4d} | {uname}")


if __name__ == "__main__":
    main()
