"""
Genera CSV micronutrienti per carne, salumi, prodotti ittici e uova (categorie 8-11).

Fonte primaria: CREA 2019 (Tabelle di Composizione degli Alimenti, IV ed.)
Fonte secondaria: USDA FoodData Central
Tutti i valori per 100g di prodotto edibile.

Uso: python -m tools.admin_scripts.generate_meat_fish_csv
Output: data/nutrition/micronutrients_meat_fish.csv
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(BASE_DIR, "nutrition.db")
OUT_PATH = os.path.join(BASE_DIR, "nutrition", "micronutrients_meat_fish.csv")


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


# ══════════════════════════════════════════════════════════════
# DATI CREA 2019 + USDA — Carne, salumi, pesce, uova (per 100g edibili)
# ══════════════════════════════════════════════════════════════
# Campi: Ca, Fe, Zn, Mg, P, K, Se, VitA(RE), VitD, VitE, VitC,
#        B1, B2, B3, B6, B9(folato), B12
#
# Regole applicate:
# - Carne cotta: B-vitamine ridotte 15-25% vs cruda, minerali concentrati ~10%
# - Carne conservata/scatola: simile a cotta
# - Pesce grasso: alto VitD (5-20 ug), alto B12 (5-15 ug)
# - Pesce bianco: basso VitD (<2 ug), moderato B12
# - Frattaglie (fegato): VitA 16000+ ug, B12 60-110+ ug, Fe alto
# - Salumi: zero VitC, tracce VitD, B12 moderato
# - Uova: Se alto, B12 moderato, VitD ~1.8-2.2 ug, VitA ~140-180 ug
# ══════════════════════════════════════════════════════════════

CREA = {
    # ═══════════════════════════════════════════════
    # 1. POLLO (chicken varieties)
    # ═══════════════════════════════════════════════
    "Pollo intero, arrosto (senza pelle)":
        _v(15, 1.3, 2.4, 25, 200, 243, 27.6, 16, 0.2, 0.3, 0, 0.06, 0.18, 8.5, 0.45, 7, 0.34, "high", "CREA 2019 pollo arrosto"),
    "Pollo, arrosto con pelle":
        _v(15, 1.2, 2.0, 23, 182, 229, 25.0, 47, 0.2, 0.3, 0, 0.06, 0.17, 7.8, 0.40, 6, 0.30, "high", "CREA 2019 pollo con pelle"),
    "Ali di pollo, cotte al forno":
        _v(15, 1.3, 1.8, 20, 158, 177, 22.0, 30, 0.2, 0.3, 0, 0.05, 0.14, 6.5, 0.35, 4, 0.28, "high", "USDA FDC chicken wing baked"),
    "Cosce di pollo, crude":
        _v(11, 0.9, 1.8, 23, 173, 229, 15.7, 18, 0.2, 0.2, 0, 0.08, 0.16, 5.6, 0.35, 6, 0.35, "high", "CREA 2019 coscia pollo"),
    "Petto di pollo, cotto in padella":
        _v(15, 1.0, 1.0, 29, 228, 256, 27.6, 6, 0.1, 0.3, 0, 0.06, 0.11, 12.4, 0.54, 4, 0.34, "high", "CREA 2019 petto pollo cotto"),
    "Petto di pollo, affettato cotto":
        _v(14, 0.9, 0.9, 28, 220, 248, 26.0, 5, 0.1, 0.3, 0, 0.05, 0.10, 11.8, 0.50, 4, 0.32, "high", "CREA 2019 petto pollo"),
    "Pollo, stinco cotto":
        _v(14, 1.3, 2.8, 22, 175, 220, 23.5, 20, 0.2, 0.3, 0, 0.06, 0.19, 6.2, 0.30, 6, 0.30, "high", "USDA FDC chicken drumstick cooked"),
    "Pollo in scatola (al naturale)":
        _v(14, 1.0, 1.6, 22, 180, 200, 22.0, 10, 0.1, 0.2, 0, 0.04, 0.12, 7.5, 0.30, 5, 0.25, "medium", "USDA FDC canned chicken"),
    "Pollo, petto marinato alla griglia":
        _v(14, 1.0, 1.0, 28, 222, 250, 27.0, 6, 0.1, 0.3, 0, 0.05, 0.10, 11.5, 0.50, 4, 0.32, "medium", "CREA petto pollo cotto"),
    "Pollo tikka masala (piatto indiano)":
        _v(30, 1.2, 1.5, 25, 170, 220, 18.0, 40, 0.2, 0.5, 1, 0.08, 0.15, 5.0, 0.25, 8, 0.25, "low", "USDA FDC chicken tikka masala"),
    "Hamburger di pollo (grigliato)":
        _v(14, 1.2, 1.5, 24, 190, 230, 22.0, 8, 0.1, 0.3, 0, 0.06, 0.12, 7.0, 0.40, 5, 0.30, "medium", "USDA FDC chicken burger"),

    # ═══════════════════════════════════════════════
    # 2. MANZO (beef varieties)
    # ═══════════════════════════════════════════════
    "Manzo, controfiletto crudo":
        _v(6, 2.1, 4.1, 22, 197, 330, 18.5, 0, 0.1, 0.4, 0, 0.07, 0.15, 5.4, 0.55, 9, 2.5, "high", "CREA 2019 manzo controfiletto"),
    "Manzo, bistecca di costata cruda":
        _v(8, 1.9, 4.5, 20, 175, 300, 16.0, 0, 0.1, 0.3, 0, 0.06, 0.14, 4.8, 0.50, 8, 2.3, "high", "CREA 2019 costata manzo"),
    "Manzo macinato 10% grassi, crudo":
        _v(12, 2.3, 5.2, 21, 188, 315, 17.8, 0, 0.1, 0.3, 0, 0.04, 0.16, 5.3, 0.35, 7, 2.5, "high", "USDA FDC ground beef 90/10"),
    "Manzo macinato 15% grassi, crudo":
        _v(11, 2.1, 4.8, 19, 172, 295, 16.5, 0, 0.1, 0.3, 0, 0.04, 0.15, 4.9, 0.34, 7, 2.4, "high", "USDA FDC ground beef 85/15"),
    "Manzo macinato, cotto":
        _v(14, 2.7, 6.2, 22, 210, 315, 21.0, 0, 0.1, 0.3, 0, 0.04, 0.18, 5.7, 0.35, 8, 2.8, "high", "USDA FDC ground beef cooked"),
    "Manzo, roast beef cotto":
        _v(8, 2.6, 5.0, 23, 210, 320, 26.0, 0, 0.1, 0.3, 0, 0.05, 0.20, 5.5, 0.45, 8, 2.9, "high", "CREA 2019 roast beef"),
    "Manzo, carpaccio (crudo affettato)":
        _v(6, 2.3, 4.5, 22, 200, 340, 19.0, 0, 0.1, 0.4, 0, 0.07, 0.15, 5.5, 0.55, 9, 2.6, "high", "CREA 2019 manzo crudo"),
    "Manzo, fianco (flank steak), crudo":
        _v(7, 2.0, 4.3, 23, 200, 345, 18.0, 0, 0.1, 0.3, 0, 0.07, 0.16, 5.8, 0.50, 9, 2.4, "high", "USDA FDC flank steak"),
    "Manzo, girello (topside), crudo":
        _v(5, 2.2, 4.0, 24, 210, 355, 20.0, 0, 0.1, 0.3, 0, 0.08, 0.15, 6.0, 0.55, 10, 2.6, "high", "USDA FDC beef top round"),
    "Manzo, stinco cotto in umido":
        _v(16, 3.0, 6.5, 20, 190, 280, 22.0, 0, 0.1, 0.2, 0, 0.04, 0.22, 4.5, 0.30, 7, 3.0, "high", "USDA FDC beef shank braised"),
    "Hamburger di manzo (80% magro)":
        _v(18, 2.3, 5.4, 20, 175, 270, 18.0, 0, 0.1, 0.3, 0, 0.04, 0.16, 4.8, 0.33, 7, 2.5, "high", "USDA FDC beef patty 80/20"),
    "Cuore di manzo, crudo":
        _v(7, 4.3, 1.7, 21, 212, 287, 21.8, 0, 0.1, 0.2, 2, 0.24, 0.91, 7.5, 0.28, 3, 8.6, "high", "USDA FDC beef heart"),
    "Rene di manzo, crudo":
        _v(13, 4.6, 1.9, 17, 257, 262, 141, 354, 0, 0.3, 9.4, 0.36, 2.84, 8.0, 0.67, 98, 27.5, "high", "USDA FDC beef kidney"),
    "Polpette di carne al sugo (cotte)":
        _v(22, 2.0, 4.0, 18, 160, 250, 15.0, 15, 0.1, 0.5, 2, 0.06, 0.15, 4.5, 0.25, 8, 2.0, "low", "USDA FDC meatball cooked"),
    "Tonno-pollo proteico (piatto mix)":
        _v(12, 1.3, 1.5, 28, 210, 280, 30.0, 8, 0.5, 0.4, 0, 0.06, 0.12, 9.0, 0.45, 5, 1.5, "low", "stima media tonno+pollo"),

    # ═══════════════════════════════════════════════
    # 3. VITELLO (veal varieties)
    # ═══════════════════════════════════════════════
    "Vitello, cosciotto crudo":
        _v(10, 1.0, 2.6, 24, 210, 350, 10.0, 0, 0.1, 0.3, 0, 0.06, 0.22, 7.0, 0.45, 12, 1.4, "high", "CREA 2019 vitello cosciotto"),
    "Vitello, ossobuco crudo":
        _v(13, 1.2, 3.2, 20, 180, 300, 9.0, 0, 0.1, 0.2, 0, 0.05, 0.20, 5.5, 0.35, 10, 1.3, "high", "CREA 2019 vitello ossobuco"),
    "Vitello, fettina al limone (cotta)":
        _v(12, 1.2, 3.0, 25, 225, 340, 12.0, 0, 0.1, 0.3, 2, 0.05, 0.24, 7.5, 0.40, 10, 1.5, "medium", "CREA vitello cotto"),
    "Fegato di vitello, crudo":
        _v(8, 7.9, 8.4, 19, 358, 330, 17.4, 16500, 0.5, 0.6, 30, 0.17, 2.72, 14.7, 0.80, 290, 110.0, "high", "CREA 2019 fegato vitello"),
    "Vitello, fegato cotto in padella":
        _v(9, 8.8, 9.5, 20, 380, 310, 20.0, 21600, 0.5, 0.6, 23, 0.14, 3.40, 16.0, 0.85, 250, 95.0, "high", "USDA FDC veal liver cooked"),
    "Scaloppina di vitello al marsala":
        _v(12, 1.2, 3.0, 24, 220, 330, 11.0, 0, 0.1, 0.3, 1, 0.05, 0.22, 7.0, 0.38, 10, 1.4, "medium", "CREA vitello cotto"),

    # ═══════════════════════════════════════════════
    # 4. MAIALE (pork varieties)
    # ═══════════════════════════════════════════════
    "Maiale, bistecca cruda":
        _v(7, 0.9, 2.0, 23, 210, 360, 33.0, 2, 0.5, 0.2, 0, 0.80, 0.22, 5.0, 0.46, 5, 0.7, "high", "CREA 2019 maiale bistecca"),
    "Maiale, costolette cotte":
        _v(20, 1.0, 2.5, 22, 200, 310, 35.0, 2, 0.6, 0.2, 0, 0.60, 0.25, 5.2, 0.40, 4, 0.7, "high", "USDA FDC pork chop cooked"),
    "Maiale, spalla cruda":
        _v(8, 1.1, 2.8, 18, 170, 300, 25.0, 2, 0.5, 0.2, 0, 0.65, 0.20, 4.2, 0.35, 4, 0.6, "high", "CREA 2019 maiale spalla"),
    "Maiale, pancetta tesa cruda":
        _v(5, 0.7, 1.6, 12, 130, 220, 16.0, 9, 0.6, 0.2, 0, 0.40, 0.10, 3.5, 0.20, 3, 0.5, "high", "CREA 2019 pancetta"),
    "Maiale, arrosto al forno cotto":
        _v(10, 1.1, 2.6, 24, 230, 340, 38.0, 2, 0.6, 0.2, 0, 0.65, 0.25, 5.5, 0.42, 4, 0.8, "high", "USDA FDC pork loin roast"),
    "Maiale, salsiccia fresca cruda":
        _v(9, 1.0, 2.2, 16, 150, 260, 20.0, 3, 0.4, 0.2, 0, 0.50, 0.15, 3.8, 0.25, 3, 0.6, "high", "CREA 2019 salsiccia maiale"),

    # ═══════════════════════════════════════════════
    # 5. TACCHINO (turkey varieties)
    # ═══════════════════════════════════════════════
    "Petto di tacchino, macinato":
        _v(13, 1.1, 2.2, 27, 210, 290, 22.4, 5, 0.4, 0.1, 0, 0.06, 0.13, 7.5, 0.60, 8, 1.0, "high", "USDA FDC ground turkey breast"),
    "Coscia di tacchino, cotta":
        _v(22, 1.6, 3.6, 24, 195, 260, 30.0, 8, 0.3, 0.2, 0, 0.05, 0.20, 4.5, 0.35, 8, 1.4, "high", "USDA FDC turkey leg cooked"),
    "Tacchino, macinato cotto":
        _v(21, 1.5, 3.3, 23, 200, 270, 28.0, 6, 0.3, 0.2, 0, 0.04, 0.18, 6.0, 0.40, 7, 1.2, "high", "USDA FDC ground turkey cooked"),
    "Tacchino, petto macinato crudo":
        _v(11, 0.8, 1.8, 28, 220, 310, 24.0, 3, 0.4, 0.1, 0, 0.06, 0.11, 8.5, 0.65, 9, 1.1, "high", "USDA FDC turkey breast raw"),

    # ═══════════════════════════════════════════════
    # 6. AGNELLO, SELVAGGINA, ALTRO (lamb, game, misc)
    # ═══════════════════════════════════════════════
    "Agnello, coscia cruda":
        _v(10, 1.6, 3.5, 22, 188, 310, 10.5, 0, 0.1, 0.2, 0, 0.10, 0.22, 5.7, 0.30, 16, 2.6, "high", "CREA 2019 agnello coscia"),
    "Agnello, coscio cotto al forno":
        _v(12, 2.0, 4.2, 24, 210, 290, 12.0, 0, 0.1, 0.2, 0, 0.08, 0.25, 5.5, 0.25, 14, 2.8, "high", "USDA FDC lamb leg roasted"),
    "Agnello, costolette crude":
        _v(14, 1.5, 3.0, 20, 170, 280, 9.0, 0, 0.1, 0.1, 0, 0.09, 0.20, 5.0, 0.28, 14, 2.5, "high", "CREA 2019 agnello costolette"),
    "Agnello, macinato crudo":
        _v(13, 1.6, 3.4, 20, 175, 290, 10.0, 0, 0.1, 0.2, 0, 0.10, 0.21, 5.2, 0.30, 15, 2.7, "high", "USDA FDC ground lamb"),
    "Agnello, macinato cotto":
        _v(16, 2.0, 4.1, 22, 195, 275, 12.0, 0, 0.1, 0.2, 0, 0.08, 0.24, 5.3, 0.25, 13, 3.0, "high", "USDA FDC ground lamb cooked"),
    "Capretto, carne cruda":
        _v(13, 2.8, 4.0, 23, 180, 385, 8.8, 0, 0.1, 0.2, 0, 0.10, 0.49, 3.8, 0.40, 6, 1.1, "high", "USDA FDC goat raw"),
    "Cervo (capriolo), carne cruda":
        _v(5, 3.4, 2.1, 23, 202, 330, 10.3, 0, 0, 0.2, 0, 0.25, 0.48, 6.4, 0.37, 4, 5.7, "high", "USDA FDC venison raw"),
    "Cervo, coscia cotta":
        _v(7, 3.9, 2.5, 25, 225, 310, 12.0, 0, 0, 0.2, 0, 0.20, 0.55, 6.0, 0.32, 4, 6.3, "medium", "USDA FDC venison cooked"),
    "Cinghiale, carne cruda":
        _v(12, 3.3, 2.4, 22, 190, 330, 9.0, 0, 0, 0.2, 0, 0.39, 0.50, 4.0, 0.40, 5, 4.0, "high", "USDA FDC wild boar"),
    "Bisonte (bufalo americano), macinato crudo":
        _v(10, 2.8, 4.6, 22, 190, 328, 25.0, 0, 0.1, 0.3, 0, 0.05, 0.20, 5.0, 0.40, 7, 2.7, "high", "USDA FDC bison ground"),
    "Struzzo, filetto crudo":
        _v(7, 3.2, 3.6, 22, 210, 320, 10.0, 0, 0.1, 0.3, 0, 0.20, 0.25, 4.0, 0.43, 6, 5.3, "high", "USDA FDC ostrich raw"),
    "Struzzo, filetto cotto":
        _v(9, 3.7, 4.2, 24, 235, 300, 12.0, 0, 0.1, 0.3, 0, 0.17, 0.30, 4.2, 0.40, 5, 5.8, "medium", "USDA FDC ostrich cooked"),
    "Coniglio, dorso cotto":
        _v(18, 1.6, 1.8, 22, 230, 330, 15.0, 0, 0.1, 0.2, 0, 0.04, 0.14, 7.2, 0.32, 8, 7.2, "high", "CREA 2019 coniglio cotto"),
    "Anatra, petto crudo (senza pelle)":
        _v(10, 3.5, 1.8, 19, 203, 271, 14.0, 24, 0.5, 0.7, 2.8, 0.36, 0.45, 5.3, 0.34, 13, 3.0, "high", "USDA FDC duck breast raw"),
    "Anatra, coscia cotta":
        _v(12, 2.7, 2.0, 18, 190, 250, 16.0, 20, 0.5, 0.6, 2, 0.28, 0.40, 4.8, 0.28, 10, 2.8, "high", "USDA FDC duck leg cooked"),
    "Anatra, petto cotto al forno":
        _v(12, 4.0, 2.2, 20, 220, 260, 16.5, 20, 0.5, 0.6, 2, 0.30, 0.50, 5.5, 0.30, 11, 3.2, "medium", "USDA FDC duck breast cooked"),
    "Oca, petto crudo":
        _v(13, 2.6, 1.8, 20, 210, 280, 16.0, 12, 0.5, 0.7, 4.3, 0.13, 0.38, 4.3, 0.55, 31, 2.0, "high", "USDA FDC goose raw"),
    "Fagiano, petto crudo":
        _v(12, 1.2, 0.8, 22, 230, 260, 14.0, 15, 0.3, 0.2, 4, 0.10, 0.15, 6.5, 0.45, 6, 1.0, "high", "USDA FDC pheasant breast"),
    "Quaglia, intera cotta":
        _v(13, 4.5, 2.7, 22, 275, 216, 17.4, 70, 0.3, 0.6, 3, 0.22, 0.42, 7.5, 0.50, 8, 0.5, "high", "USDA FDC quail cooked"),

    # ═══════════════════════════════════════════════
    # 7. SALUMI E AFFETTATI (cat. 9)
    # ═══════════════════════════════════════════════
    "Prosciutto crudo DOP (con grasso)":
        _v(7, 1.3, 2.1, 18, 220, 370, 20.0, 0, 0.3, 0.2, 0, 0.50, 0.17, 5.0, 0.40, 3, 1.0, "high", "CREA 2019 prosciutto crudo"),
    "Prosciutto crudo magro affettato":
        _v(8, 1.4, 2.3, 20, 240, 390, 22.0, 0, 0.3, 0.2, 0, 0.55, 0.18, 5.5, 0.45, 3, 1.1, "high", "CREA 2019 prosciutto crudo magro"),
    "Prosciutto di Parma DOP, magro":
        _v(8, 1.4, 2.3, 20, 240, 390, 22.0, 0, 0.3, 0.2, 0, 0.55, 0.18, 5.5, 0.45, 3, 1.1, "high", "CREA 2019 prosciutto Parma"),
    "Prosciutto di San Daniele DOP":
        _v(8, 1.4, 2.2, 19, 235, 385, 21.0, 0, 0.3, 0.2, 0, 0.53, 0.18, 5.3, 0.44, 3, 1.0, "medium", "CREA prosciutto crudo"),
    "Prosciutto di Norcia":
        _v(8, 1.3, 2.2, 19, 230, 380, 21.0, 0, 0.3, 0.2, 0, 0.52, 0.17, 5.2, 0.43, 3, 1.0, "medium", "CREA prosciutto crudo"),
    "Prosciutto cotto alta qualit":
        _v(7, 0.7, 1.8, 17, 240, 300, 18.0, 0, 0.3, 0.1, 0, 0.60, 0.15, 5.0, 0.30, 2, 0.8, "high", "CREA 2019 prosciutto cotto"),
    "Prosciutto cotto al forno":
        _v(7, 0.7, 1.8, 17, 240, 300, 18.0, 0, 0.3, 0.1, 0, 0.60, 0.15, 5.0, 0.30, 2, 0.8, "high", "CREA 2019 prosciutto cotto"),
    "Bresaola della Valtellina IGP":
        _v(12, 2.8, 4.3, 21, 260, 505, 10.0, 0, 0.1, 0.4, 0, 0.08, 0.20, 6.0, 0.35, 5, 2.3, "high", "CREA 2019 bresaola"),
    "Coppa (capocollo)":
        _v(8, 1.1, 2.0, 15, 170, 320, 15.0, 0, 0.4, 0.2, 0, 0.45, 0.15, 4.5, 0.30, 2, 0.8, "high", "CREA 2019 coppa"),
    "Coppa di testa":
        _v(10, 0.9, 1.5, 10, 100, 150, 12.0, 0, 0.3, 0.1, 0, 0.20, 0.10, 2.5, 0.12, 2, 0.6, "medium", "USDA FDC head cheese"),
    "Culatello di Zibello DOP":
        _v(8, 1.3, 2.2, 19, 230, 380, 20.0, 0, 0.3, 0.2, 0, 0.53, 0.17, 5.3, 0.42, 3, 1.0, "medium", "CREA prosciutto crudo"),
    "Fiocchetto (prosciutto magro)":
        _v(8, 1.4, 2.3, 20, 240, 390, 22.0, 0, 0.3, 0.2, 0, 0.55, 0.18, 5.5, 0.45, 3, 1.1, "medium", "CREA prosciutto crudo magro"),
    "Lonza di maiale stagionata":
        _v(7, 1.0, 2.0, 22, 220, 360, 28.0, 0, 0.4, 0.2, 0, 0.70, 0.20, 5.0, 0.42, 3, 0.9, "medium", "CREA lonza stagionata"),
    "Pancetta affumicata (bacon)":
        _v(5, 0.7, 1.8, 15, 200, 220, 25.0, 11, 0.6, 0.2, 0, 0.35, 0.10, 4.8, 0.22, 2, 0.6, "high", "USDA FDC bacon"),
    "Pancetta tesa (non affumicata)":
        _v(5, 0.7, 1.6, 12, 130, 220, 16.0, 9, 0.6, 0.2, 0, 0.40, 0.10, 3.5, 0.20, 3, 0.5, "high", "CREA 2019 pancetta tesa"),
    "Guanciale (cured pork cheek)":
        _v(4, 0.5, 1.3, 8, 100, 180, 12.0, 8, 0.5, 0.2, 0, 0.30, 0.08, 2.5, 0.15, 2, 0.5, "medium", "CREA pancetta adattato"),
    "Lardo di Colonnata IGP":
        _v(2, 0.2, 0.4, 2, 30, 50, 5.0, 0, 0.3, 0.1, 0, 0.05, 0.02, 0.5, 0.03, 0, 0.1, "high", "CREA 2019 lardo"),
    "Salame Felino":
        _v(10, 1.5, 2.8, 18, 200, 340, 16.0, 0, 0.4, 0.2, 0, 0.35, 0.18, 4.8, 0.30, 2, 1.0, "high", "CREA 2019 salame"),
    "Salame Napoli":
        _v(10, 1.4, 2.6, 17, 195, 330, 15.0, 0, 0.4, 0.2, 0, 0.33, 0.17, 4.5, 0.28, 2, 1.0, "medium", "CREA 2019 salame"),
    "Salame di Varzi DOP":
        _v(10, 1.5, 2.7, 17, 200, 335, 15.0, 0, 0.4, 0.2, 0, 0.34, 0.17, 4.6, 0.29, 2, 1.0, "medium", "CREA 2019 salame"),
    "Soppressata calabrese":
        _v(10, 1.5, 2.7, 17, 195, 330, 15.0, 0, 0.4, 0.2, 0, 0.33, 0.16, 4.5, 0.28, 2, 1.0, "medium", "CREA salame"),
    "Finocchiona (salame al finocchio)":
        _v(10, 1.4, 2.6, 17, 195, 330, 15.0, 0, 0.4, 0.2, 0, 0.33, 0.17, 4.5, 0.28, 2, 1.0, "medium", "CREA salame"),
    "Spianata romana piccante":
        _v(10, 1.5, 2.7, 17, 195, 330, 15.0, 0, 0.4, 0.2, 0, 0.33, 0.17, 4.5, 0.28, 2, 1.0, "medium", "CREA salame"),
    "Nduja calabrese":
        _v(8, 1.2, 2.0, 13, 140, 250, 12.0, 120, 0.4, 1.8, 0, 0.30, 0.14, 3.5, 0.22, 2, 0.8, "medium", "USDA FDC nduja"),
    "Chorizo (salame spagnolo)":
        _v(11, 1.6, 2.8, 18, 200, 340, 16.0, 60, 0.5, 0.3, 0, 0.35, 0.20, 4.8, 0.32, 3, 1.1, "high", "USDA FDC chorizo"),
    "Mortadella di Bologna IGP":
        _v(11, 1.5, 1.6, 12, 130, 260, 14.0, 0, 0.3, 0.1, 0, 0.15, 0.12, 3.0, 0.15, 2, 0.8, "high", "CREA 2019 mortadella"),
    "Porchetta (arrosto di maiale)":
        _v(10, 1.0, 2.2, 18, 200, 300, 30.0, 2, 0.5, 0.2, 0, 0.55, 0.22, 5.0, 0.35, 3, 0.8, "medium", "CREA maiale arrosto"),
    "Cotechino (prodotto cotto)":
        _v(14, 1.2, 2.0, 11, 120, 180, 12.0, 0, 0.3, 0.1, 0, 0.15, 0.12, 2.8, 0.12, 2, 0.6, "high", "CREA 2019 cotechino"),
    "Wurstel di maiale":
        _v(7, 1.1, 1.8, 12, 140, 200, 15.0, 0, 0.4, 0.1, 0, 0.25, 0.10, 2.8, 0.12, 2, 0.6, "high", "CREA 2019 wurstel"),
    "Wurstel di pollo":
        _v(43, 0.8, 0.8, 10, 110, 130, 12.0, 0, 0.3, 0.1, 0, 0.05, 0.07, 3.5, 0.15, 3, 0.5, "high", "USDA FDC chicken frankfurter"),
    "Petto di pollo arrosto (affettato, packed)":
        _v(7, 0.5, 0.7, 25, 210, 260, 24.0, 3, 0.1, 0.2, 0, 0.04, 0.08, 10.0, 0.50, 4, 0.30, "high", "USDA FDC deli chicken breast"),
    "Petto di tacchino affumicato":
        _v(8, 0.6, 1.3, 23, 220, 280, 22.0, 3, 0.3, 0.1, 0, 0.04, 0.10, 6.5, 0.45, 5, 0.8, "high", "USDA FDC smoked turkey breast"),
    "Salume di cinghiale":
        _v(10, 2.0, 2.5, 18, 190, 330, 12.0, 0, 0.3, 0.2, 0, 0.35, 0.25, 4.0, 0.30, 3, 2.0, "low", "stima salame cinghiale"),
    "Salamella (salsiccia tipo mantovana)":
        _v(9, 1.0, 2.2, 16, 150, 260, 20.0, 3, 0.4, 0.2, 0, 0.50, 0.15, 3.8, 0.25, 3, 0.6, "medium", "CREA salsiccia maiale"),
    "Salsiccia di pollo e tacchino":
        _v(12, 0.8, 1.5, 18, 160, 230, 18.0, 5, 0.2, 0.2, 0, 0.06, 0.12, 5.5, 0.35, 5, 0.7, "medium", "USDA FDC chicken sausage"),
    "Testa in cassetta (headcheese)":
        _v(10, 0.9, 1.5, 10, 100, 150, 12.0, 0, 0.3, 0.1, 0, 0.20, 0.10, 2.5, 0.12, 2, 0.6, "medium", "USDA FDC head cheese"),
    "Zampone di Modena IGP (cotto)":
        _v(14, 1.2, 2.0, 11, 120, 180, 12.0, 0, 0.3, 0.1, 0, 0.15, 0.12, 2.8, 0.12, 2, 0.6, "medium", "CREA cotechino"),
    "Jam":  # partial match for Jamón ibérico
        _v(8, 1.3, 2.2, 19, 230, 380, 21.0, 0, 0.3, 0.2, 0, 0.52, 0.18, 5.3, 0.43, 3, 1.0, "medium", "USDA FDC Iberian ham"),

    # ═══════════════════════════════════════════════
    # 8. PESCE BIANCO (white fish, cat. 10)
    # ═══════════════════════════════════════════════
    "Merluzzo, cotto al vapore":
        _v(18, 0.4, 0.5, 32, 203, 328, 33.1, 12, 0.9, 0.7, 1, 0.08, 0.06, 2.5, 0.24, 7, 1.0, "high", "CREA 2019 merluzzo cotto"),
    "Merluzzo (baccal":
        _v(15, 0.5, 0.5, 30, 190, 300, 28.0, 10, 0.8, 0.6, 1, 0.07, 0.06, 2.3, 0.22, 6, 0.9, "high", "CREA 2019 baccala ammollato"),
    "Branzino, crudo":
        _v(18, 0.5, 0.4, 30, 194, 307, 36.5, 45, 3.0, 0.6, 0, 0.10, 0.12, 2.0, 0.30, 15, 3.8, "high", "CREA 2019 branzino"),
    "Branzino al cartoccio (cotto)":
        _v(20, 0.5, 0.5, 32, 210, 290, 40.0, 40, 2.8, 0.5, 0, 0.08, 0.10, 1.8, 0.25, 12, 3.5, "medium", "CREA branzino cotto"),
    "Spigola (branzino), cotta":
        _v(20, 0.5, 0.5, 32, 210, 290, 40.0, 40, 2.8, 0.5, 0, 0.08, 0.10, 1.8, 0.25, 12, 3.5, "high", "CREA 2019 spigola cotta"),
    "Ceviche di branzino (piatto crudo)":
        _v(18, 0.5, 0.4, 30, 194, 307, 36.5, 45, 3.0, 0.6, 5, 0.10, 0.12, 2.0, 0.30, 15, 3.8, "medium", "CREA branzino + lime"),
    "Dentice, crudo":
        _v(22, 0.4, 0.5, 30, 200, 350, 36.0, 30, 3.0, 0.5, 0, 0.09, 0.07, 3.5, 0.40, 10, 2.0, "high", "CREA 2019 dentice"),
    "Orata, cotta":
        _v(28, 0.5, 0.5, 28, 220, 350, 37.0, 12, 3.0, 0.6, 0, 0.08, 0.07, 3.0, 0.30, 8, 1.8, "high", "CREA 2019 orata cotta"),
    "Pagello, crudo":
        _v(25, 0.5, 0.4, 28, 210, 320, 35.0, 15, 2.5, 0.5, 0, 0.08, 0.07, 2.8, 0.35, 10, 2.0, "high", "CREA 2019 pagello"),
    "Rombo, crudo":
        _v(23, 0.3, 0.2, 25, 160, 238, 36.0, 10, 2.0, 0.5, 0, 0.06, 0.10, 2.2, 0.20, 10, 1.5, "high", "USDA FDC turbot"),
    "Sogliola, cruda":
        _v(21, 0.4, 0.4, 32, 220, 280, 32.7, 10, 1.0, 0.5, 0, 0.08, 0.10, 2.4, 0.20, 12, 1.3, "high", "CREA 2019 sogliola"),
    "Triglia, cruda":
        _v(40, 0.6, 0.5, 35, 230, 350, 38.0, 25, 2.5, 0.5, 0, 0.09, 0.06, 3.2, 0.35, 12, 2.5, "high", "CREA 2019 triglia"),
    "Halibut, crudo":
        _v(7, 0.2, 0.4, 23, 236, 435, 36.5, 14, 4.7, 0.6, 0, 0.05, 0.03, 6.4, 0.55, 12, 1.0, "high", "USDA FDC halibut"),
    "Pesce persico, filetto crudo":
        _v(80, 0.5, 0.6, 25, 200, 290, 12.6, 10, 1.0, 0.5, 1.5, 0.07, 0.07, 1.5, 0.12, 5, 2.0, "high", "USDA FDC perch"),
    "Tilapia, cruda":
        _v(10, 0.6, 0.3, 27, 170, 302, 54.4, 0, 3.1, 0.4, 0, 0.04, 0.06, 3.9, 0.16, 24, 1.6, "high", "USDA FDC tilapia"),
    "Pangasio, filetto crudo":
        _v(8, 0.3, 0.3, 20, 150, 280, 12.0, 5, 2.0, 0.3, 0, 0.04, 0.05, 2.5, 0.15, 8, 1.5, "medium", "USDA FDC pangasius"),
    "Luccio, crudo":
        _v(57, 0.6, 0.7, 28, 200, 259, 12.6, 17, 2.0, 0.3, 3.6, 0.06, 0.06, 2.4, 0.12, 15, 2.0, "high", "USDA FDC pike"),
    "Carpa, cruda":
        _v(41, 1.2, 1.5, 29, 415, 333, 12.6, 9, 1.0, 0.5, 1.6, 0.12, 0.05, 1.6, 0.19, 15, 1.5, "high", "USDA FDC carp"),
    "Pesce gatto (siluro), crudo":
        _v(9, 0.3, 0.5, 23, 209, 358, 12.6, 15, 2.0, 0.3, 0.7, 0.21, 0.07, 1.9, 0.12, 10, 2.4, "high", "USDA FDC catfish"),
    "Rana pescatrice (coda di rospo), cruda":
        _v(10, 0.4, 0.4, 21, 200, 320, 36.0, 12, 1.0, 0.4, 0, 0.02, 0.04, 2.1, 0.24, 7, 1.0, "high", "USDA FDC monkfish"),
    "Storione, crudo":
        _v(13, 0.7, 0.4, 35, 211, 284, 12.6, 210, 0, 0.5, 0, 0.07, 0.07, 8.0, 0.20, 15, 2.0, "high", "USDA FDC sturgeon"),
    "Grongo, crudo":
        _v(20, 0.5, 0.4, 25, 200, 290, 30.0, 25, 2.0, 0.5, 0, 0.06, 0.06, 2.5, 0.20, 8, 1.5, "medium", "USDA FDC conger eel"),
    "Mormora (sparo), cruda":
        _v(25, 0.5, 0.5, 28, 210, 330, 35.0, 20, 2.5, 0.5, 0, 0.08, 0.07, 2.8, 0.30, 10, 2.0, "medium", "CREA sparidae generico"),
    "Surimi (bastoncini di granchio)":
        _v(9, 0.2, 0.3, 37, 282, 76, 17.0, 17, 0, 0.2, 0, 0.02, 0.02, 0.2, 0.03, 2, 1.5, "high", "USDA FDC surimi"),

    # ═══════════════════════════════════════════════
    # 9. PESCE AZZURRO / GRASSO (fatty fish)
    # ═══════════════════════════════════════════════
    "Alici (acciughe), crude":
        _v(148, 2.5, 1.7, 41, 174, 383, 36.5, 15, 11.0, 1.0, 0, 0.06, 0.26, 14.0, 0.14, 9, 6.2, "high", "CREA 2019 acciughe"),
    "Acciughe sotto sale (lavate)":
        _v(232, 4.6, 1.7, 60, 252, 544, 68.1, 20, 11.0, 1.0, 0, 0.08, 0.36, 19.9, 0.14, 10, 6.2, "high", "USDA FDC anchovy canned"),
    "Acciughe in pasta (tubo)":
        _v(200, 4.0, 1.5, 50, 220, 500, 60.0, 18, 10.0, 0.9, 0, 0.07, 0.30, 17.0, 0.12, 9, 5.5, "medium", "USDA anchovy paste"),
    "Salmone affumicato":
        _v(11, 0.9, 0.3, 18, 164, 175, 32.4, 26, 11.0, 1.8, 0, 0.02, 0.10, 4.7, 0.28, 2, 3.3, "high", "CREA 2019 salmone affumicato"),
    "Salmone coho, crudo":
        _v(12, 0.6, 0.4, 28, 262, 394, 36.5, 10, 9.0, 1.3, 1, 0.10, 0.12, 7.5, 0.56, 10, 4.5, "high", "USDA FDC coho salmon"),
    "Salmone in scatola (al naturale)":
        _v(240, 0.7, 0.8, 29, 326, 277, 36.5, 40, 14.1, 2.0, 0, 0.02, 0.16, 6.6, 0.30, 12, 4.0, "high", "USDA FDC canned salmon w/bone"),
    "Salmone teriyaki al forno":
        _v(12, 0.7, 0.5, 28, 250, 360, 38.0, 12, 11.0, 1.5, 0, 0.08, 0.12, 7.0, 0.50, 8, 4.2, "medium", "USDA salmon cooked"),
    "Tonno fresco, crudo":
        _v(16, 1.0, 0.6, 50, 254, 444, 36.5, 655, 7.2, 1.0, 0, 0.24, 0.25, 8.7, 0.46, 2, 9.4, "high", "CREA 2019 tonno fresco"),
    "Tonno fresco, cotto":
        _v(4, 1.3, 0.8, 55, 278, 323, 90.6, 650, 7.2, 1.0, 0, 0.20, 0.23, 10.1, 0.46, 2, 10.9, "high", "USDA FDC tuna cooked"),
    "Tonno rosso (bluefin), crudo":
        _v(8, 1.3, 0.6, 50, 254, 252, 36.5, 655, 7.2, 1.0, 0, 0.24, 0.25, 8.7, 0.46, 2, 9.4, "high", "USDA FDC bluefin tuna"),
    "Tonno in scatola al naturale (sgocciolato)":
        _v(11, 1.1, 0.7, 29, 217, 237, 70.6, 18, 1.7, 0.5, 0, 0.02, 0.09, 13.3, 0.42, 4, 2.9, "high", "USDA FDC canned tuna water"),
    "Sarde, crude":
        _v(60, 1.8, 1.3, 39, 270, 397, 52.7, 13, 11.0, 0.8, 0, 0.07, 0.23, 5.2, 0.16, 8, 8.9, "high", "CREA 2019 sarde"),
    "Sardine in scatola al naturale":
        _v(382, 2.9, 1.3, 39, 490, 397, 52.7, 32, 4.8, 2.0, 0, 0.08, 0.23, 5.2, 0.17, 10, 8.9, "high", "USDA FDC sardine canned water"),
    "Sardine in scatola all'olio, scolate":
        _v(382, 2.9, 1.3, 39, 490, 397, 52.7, 32, 4.8, 2.0, 0, 0.08, 0.23, 5.2, 0.17, 10, 8.9, "high", "USDA FDC sardine canned oil"),
    "Sardine grigliate":
        _v(65, 2.0, 1.4, 40, 290, 380, 54.0, 15, 10.0, 0.8, 0, 0.06, 0.20, 5.0, 0.14, 7, 8.5, "medium", "CREA sarde cotte"),
    "Sgombro, cotto al forno":
        _v(15, 1.6, 0.6, 33, 240, 401, 44.1, 50, 16.1, 1.5, 0.4, 0.10, 0.31, 9.1, 0.40, 1, 19.0, "high", "USDA FDC mackerel cooked"),
    "Sgombro in scatola al naturale":
        _v(241, 1.4, 0.8, 33, 236, 297, 44.1, 48, 7.3, 1.5, 0, 0.08, 0.25, 6.3, 0.35, 2, 8.7, "high", "USDA FDC canned mackerel"),
    "Anguilla di fiume, cruda":
        _v(20, 0.5, 1.6, 20, 216, 272, 6.5, 1043, 23.3, 4.0, 1.8, 0.15, 0.04, 3.5, 0.08, 15, 3.0, "high", "CREA 2019 anguilla"),
    "Anguilla affumicata":
        _v(22, 0.6, 1.8, 22, 230, 260, 7.0, 1100, 20.0, 3.5, 1, 0.12, 0.04, 3.0, 0.07, 12, 2.8, "medium", "CREA anguilla cotta"),
    "Trota iridea, cotta":
        _v(67, 0.4, 0.5, 28, 253, 390, 12.6, 19, 3.9, 1.0, 1, 0.12, 0.11, 5.4, 0.36, 16, 7.8, "high", "USDA FDC rainbow trout cooked"),
    "Bottarga di muggine":
        _v(40, 2.0, 1.5, 55, 350, 420, 50.0, 100, 5.0, 3.0, 0, 0.15, 0.30, 5.0, 0.20, 15, 10.0, "medium", "USDA FDC mullet roe"),
    "Olio di fegato di merluzzo":
        _v(0, 0, 0, 0, 0, 0, 0, 30000, 250.0, 20.0, 0, 0, 0, 0, 0, 0, 0, "high", "USDA FDC cod liver oil"),

    # ═══════════════════════════════════════════════
    # 10. CROSTACEI E MOLLUSCHI (shellfish)
    # ═══════════════════════════════════════════════
    "Gamberi (scampi), crudi":
        _v(52, 0.2, 1.1, 37, 205, 259, 38.0, 2, 0, 1.5, 2, 0.03, 0.03, 2.5, 0.10, 3, 1.1, "high", "CREA 2019 gamberi"),
    "Gamberi tigre, crudi":
        _v(54, 0.3, 1.3, 35, 220, 264, 40.0, 2, 0, 1.5, 2, 0.03, 0.03, 2.6, 0.10, 3, 1.2, "high", "USDA FDC tiger shrimp"),
    "Gamberoni, cotti":
        _v(60, 0.3, 1.4, 37, 230, 250, 42.0, 2, 0, 1.5, 1.5, 0.02, 0.03, 2.5, 0.08, 3, 1.3, "high", "USDA FDC shrimp cooked"),
    "Mazzancolle (gamberi grandi), cotte":
        _v(60, 0.3, 1.4, 37, 230, 250, 42.0, 2, 0, 1.5, 1.5, 0.02, 0.03, 2.5, 0.08, 3, 1.3, "medium", "USDA FDC large shrimp cooked"),
    "Mazzancolle al vapore":
        _v(60, 0.3, 1.4, 37, 230, 250, 42.0, 2, 0, 1.5, 1.5, 0.02, 0.03, 2.5, 0.08, 3, 1.3, "medium", "USDA FDC shrimp steamed"),
    "Scampi fritti (impanati)":
        _v(55, 0.5, 1.2, 30, 190, 200, 32.0, 5, 0, 1.0, 1, 0.08, 0.05, 2.5, 0.08, 5, 1.0, "low", "USDA FDC fried shrimp"),
    "Aragosta, cotta":
        _v(96, 0.4, 2.8, 43, 185, 352, 73.1, 2, 0, 1.0, 0, 0.02, 0.05, 1.4, 0.10, 11, 1.4, "high", "USDA FDC lobster cooked"),
    "Granchio, cotto":
        _v(91, 0.7, 3.8, 49, 175, 259, 37.4, 2, 0, 1.5, 3, 0.07, 0.04, 2.6, 0.15, 44, 9.0, "high", "USDA FDC crab cooked"),
    "Calamari, cotti":
        _v(32, 0.7, 1.5, 33, 213, 237, 44.8, 9, 0, 1.2, 4.2, 0.02, 0.41, 2.2, 0.05, 5, 1.3, "high", "USDA FDC squid cooked"),
    "Polpo, crudo":
        _v(53, 5.3, 1.7, 30, 186, 350, 44.8, 45, 0, 1.2, 0, 0.03, 0.04, 2.1, 0.36, 16, 20.0, "high", "USDA FDC octopus raw"),
    "Polpo, in umido":
        _v(55, 5.8, 1.9, 32, 200, 330, 48.0, 42, 0, 1.0, 0, 0.02, 0.04, 1.9, 0.30, 14, 18.0, "medium", "USDA FDC octopus cooked"),
    "Seppie, crude":
        _v(90, 6.0, 1.7, 30, 350, 354, 44.8, 100, 0, 1.2, 3.0, 0.01, 0.73, 1.7, 0.14, 16, 5.4, "high", "CREA 2019 seppie"),
    "Totano, crudo":
        _v(31, 0.6, 1.5, 33, 220, 246, 44.8, 10, 0, 1.2, 4, 0.02, 0.40, 2.2, 0.06, 5, 1.3, "high", "USDA FDC flying squid"),
    "Cozze (mitili), cotte":
        _v(33, 6.7, 2.7, 37, 285, 268, 89.6, 91, 0, 0.7, 12, 0.16, 0.42, 3.0, 0.10, 76, 24.0, "high", "USDA FDC mussel cooked"),
    "Vongole (lupini di mare), cotte":
        _v(65, 28.0, 2.3, 15, 338, 534, 64.2, 171, 0, 0, 22, 0.15, 0.43, 3.0, 0.10, 28, 98.9, "high", "USDA FDC clam cooked"),
    "Ostrica, cruda":
        _v(44, 5.1, 16.6, 47, 135, 168, 77.0, 81, 0.8, 0.9, 3.7, 0.07, 0.23, 1.6, 0.05, 10, 16.0, "high", "USDA FDC oyster raw"),
    "Ostriche gratinate al forno":
        _v(48, 5.5, 18.0, 50, 145, 160, 80.0, 75, 0.7, 0.8, 2.5, 0.06, 0.22, 1.5, 0.05, 9, 15.0, "medium", "USDA oyster cooked"),
    "Capesante, crude":
        _v(24, 0.4, 0.9, 22, 334, 205, 12.8, 2, 0, 0.5, 0, 0.01, 0.02, 0.7, 0.07, 16, 1.4, "high", "USDA FDC scallop raw"),
    "Riccio di mare (uni), crudo":
        _v(10, 1.0, 1.5, 28, 150, 220, 25.0, 72, 0, 0.8, 2, 0.10, 0.25, 1.0, 0.10, 50, 5.0, "medium", "USDA FDC sea urchin"),
    "Baccal":
        _v(30, 0.7, 0.5, 28, 180, 280, 30.0, 10, 0.8, 0.5, 1, 0.07, 0.06, 2.0, 0.20, 6, 1.0, "low", "USDA FDC salt cod dish"),

    # ═══════════════════════════════════════════════
    # 11. UOVA (cat. 11)
    # ═══════════════════════════════════════════════
    "Albume d'uovo, cotto":
        _v(7, 0.1, 0.01, 11, 15, 163, 20.0, 0, 0, 0, 0, 0.00, 0.44, 0.1, 0.01, 4, 0.1, "high", "USDA FDC egg white cooked"),
    "Frittata base (uovo+latte), cotta":
        _v(66, 1.8, 1.2, 13, 200, 150, 31.0, 160, 1.8, 1.3, 0, 0.06, 0.44, 0.1, 0.14, 47, 1.0, "high", "USDA FDC omelette"),
    "Frittata proteica (2 uova+albume)":
        _v(45, 1.3, 0.8, 12, 170, 160, 28.0, 110, 1.4, 1.0, 0, 0.04, 0.44, 0.1, 0.10, 35, 0.7, "medium", "stima frittata proteica"),
    "Uovo intero, strapazzato (con latte)":
        _v(66, 1.6, 1.1, 12, 190, 145, 25.6, 165, 1.8, 1.3, 0, 0.06, 0.41, 0.1, 0.14, 43, 0.9, "high", "USDA FDC scrambled egg"),
    "Uovo in camicia (poch":
        _v(56, 1.8, 1.1, 12, 172, 138, 31.6, 149, 2.0, 1.0, 0, 0.03, 0.51, 0.1, 0.12, 44, 1.1, "high", "USDA FDC poached egg"),
    "Uovo di quaglia, crudo":
        _v(64, 3.7, 1.5, 13, 226, 132, 32.0, 156, 1.4, 1.1, 0, 0.13, 0.79, 0.2, 0.15, 66, 1.6, "high", "USDA FDC quail egg"),
    "Uovo di anatra, crudo":
        _v(64, 3.8, 1.4, 17, 220, 222, 36.4, 194, 1.7, 1.3, 0, 0.16, 0.40, 0.2, 0.25, 80, 5.4, "high", "USDA FDC duck egg"),
    "Uovo di struzzo, crudo":
        _v(58, 3.0, 1.3, 14, 198, 180, 28.0, 170, 1.5, 1.1, 0, 0.10, 0.45, 0.2, 0.15, 60, 2.5, "medium", "stima proporzionale uovo"),
}


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Query categories 8, 9, 10, 11
    c.execute("""
        SELECT id, nome FROM alimenti
        WHERE categoria_id IN (8, 9, 10, 11) AND calcio_mg IS NULL
        ORDER BY nome
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
    print(f"  Matchati: {matched}/{len(foods)}")
    print(f"  Non matchati: {len(unmatched)}")
    if unmatched:
        print("  Alimenti senza match:")
        for uid, uname in unmatched:
            print(f"    {uid:4d} | {uname}")


if __name__ == "__main__":
    main()
