"""
recovery_foods_vegetables.py — Dati macronutrienti CREA 2019 per verdure e ortaggi.

Fonte primaria: CREA 2019 (Tabelle di Composizione degli Alimenti, IV ed.)
Fonte secondaria: USDA FoodData Central (per alimenti non italiani)
Tutti i valori per 100g di prodotto edibile.

Formato tupla:
  (id, nome, categoria_id, energia_kcal, proteine_g, carboidrati_g, grassi_g, food_type, source)

categoria_id = 5 (Verdure e ortaggi) per tutti gli alimenti.
"""

# ---------------------------------------------------------------------------
# VEGETABLES — 106 alimenti (verdure e ortaggi)
# ---------------------------------------------------------------------------
# (id, nome, categoria_id, kcal, proteine, carboidrati, grassi, food_type, source)
#
# Fonti:
#   crea  = CREA 2019 — Tabelle di Composizione degli Alimenti (IV ed.)
#   usda  = USDA FoodData Central
#
# Tutti i valori sono per 100g di parte edibile.
# ---------------------------------------------------------------------------

VEGETABLES = [
    # ── Aglio, cipolla, allium ──────────────────────────────────────────
    (307, "Aglio, fresco",                          5, 41,   0.9,  8.4,  0.6, "ingrediente", "crea"),
    (330, "Cipolla rossa",                          5, 40,   1.1,  9.3,  0.1, "ingrediente", "crea"),
    (829, "Cipolla di Tropea, cruda",               5, 38,   1.0,  8.8,  0.1, "ingrediente", "crea"),
    (331, "Cipollotto (scalogno)",                  5, 72,   2.5, 16.8,  0.1, "ingrediente", "crea"),
    (332, "Porro, crudo",                           5, 29,   1.5,  6.1,  0.3, "ingrediente", "crea"),

    # ── Zucca ───────────────────────────────────────────────────────────
    (308, "Zucca (delica/butternut), cruda",        5, 26,   1.0,  6.5,  0.1, "ingrediente", "crea"),
    (309, "Zucca, cotta al vapore",                 5, 20,   0.7,  4.9,  0.1, "ingrediente", "crea"),
    (692, "Zucca butternut, cotta",                 5, 40,   0.9,  10.5, 0.1, "ingrediente", "usda"),
    (826, "Zucca gialla, gratinata al forno",       5, 34,   0.8,  8.0,  0.2, "ingrediente", "crea"),

    # ── Patate e tuberi ─────────────────────────────────────────────────
    (310, "Patate, crude",                          5, 77,   2.0, 17.9,  0.1, "ingrediente", "crea"),
    (311, "Patate, cotte al forno",                 5, 93,   2.5, 21.2,  0.1, "ingrediente", "crea"),
    (827, "Patate al vapore (no sale)",             5, 80,   1.9, 18.5,  0.1, "ingrediente", "crea"),
    (312, "Patate dolci (batata), crude",           5, 86,   1.6, 20.1,  0.1, "ingrediente", "crea"),
    (313, "Patate dolci, cotte",                    5, 76,   1.4, 17.7,  0.1, "ingrediente", "crea"),
    (314, "Topinambur, crudo",                      5, 73,   2.0, 17.4,  0.0, "ingrediente", "crea"),
    (684, "Topinambur, cotto",                      5, 73,   2.0, 17.4,  0.0, "ingrediente", "crea"),

    # ── Barbabietola ────────────────────────────────────────────────────
    (315, "Barbabietola rossa, cruda",              5, 19,   1.1,  4.0,  0.0, "ingrediente", "crea"),
    (316, "Barbabietola, cotta",                    5, 44,   1.7,  9.6,  0.2, "ingrediente", "crea"),
    (833, "Bietola rossa, cruda",                   5, 19,   1.1,  4.0,  0.0, "ingrediente", "crea"),

    # ── Brassicaceae (cavoli, broccoli) ─────────────────────────────────
    (317, "Cavolo broccolo (broccoletto)",          5, 31,   3.0,  4.4,  0.4, "ingrediente", "crea"),
    (668, "Broccoletti (cime di broccolo)",         5, 31,   3.0,  4.4,  0.4, "ingrediente", "crea"),
    (828, "Broccoli romanesco, crudi",              5, 25,   2.4,  3.9,  0.3, "ingrediente", "crea"),
    (318, "Cavolfiore, crudo",                      5, 25,   1.9,  5.3,  0.3, "ingrediente", "crea"),
    (319, "Cavolo di Bruxelles, crudo",             5, 37,   4.2,  5.5,  0.5, "ingrediente", "crea"),
    (320, "Cavolo di Bruxelles, cotto",             5, 36,   3.4,  5.6,  0.4, "ingrediente", "crea"),
    (825, "Cavoletti di Bruxelles arrosto",         5, 43,   3.4,  6.8,  0.5, "ingrediente", "crea"),
    (358, "Cavolo cappuccio, cotto",                5, 23,   1.3,  4.4,  0.1, "ingrediente", "crea"),
    (681, "Cavolo cappuccio viola",                 5, 31,   1.4,  7.4,  0.2, "ingrediente", "crea"),
    (669, "Verza (cavolo savoia)",                  5, 27,   2.0,  4.3,  0.1, "ingrediente", "crea"),
    (359, "Cime di rapa",                           5, 22,   2.9,  2.0,  0.3, "ingrediente", "crea"),
    (911, "Cavolo nero toscano (crudo)",            5, 35,   3.3,  5.0,  0.7, "ingrediente", "crea"),
    (912, "Cavolo nero toscano (cotto)",            5, 28,   2.5,  4.4,  0.5, "ingrediente", "crea"),

    # ── Cicorie e insalate ──────────────────────────────────────────────
    (321, "Cicoria, cruda",                         5, 10,   1.4,  0.7,  0.2, "ingrediente", "crea"),
    (322, "Catalogna (puntarelle)",                 5, 10,   1.4,  0.7,  0.2, "ingrediente", "crea"),
    (671, "Puntarelle (radici di catalogna)",       5, 10,   1.4,  0.7,  0.2, "ingrediente", "crea"),
    (325, "Lattuga romana",                         5, 17,   1.2,  3.3,  0.3, "ingrediente", "crea"),
    (326, "Valerianella (songino)",                 5, 21,   2.0,  3.6,  0.4, "ingrediente", "crea"),
    (329, "Indivia belga (witloof)",                5, 17,   0.9,  3.4,  0.1, "ingrediente", "crea"),
    (670, "Indivia riccia",                         5, 17,   1.3,  3.4,  0.2, "ingrediente", "crea"),
    (666, "Insalata mista (mix lattuga/radicchio)", 5, 16,   1.3,  2.6,  0.2, "ingrediente", "crea"),
    (667, "Misticanza (mix erbe e foglie)",         5, 20,   1.8,  3.0,  0.3, "ingrediente", "crea"),

    # ── Foglie (spinaci, bietole, rucola) ───────────────────────────────
    (327, "Spinaci, cotti",                         5, 23,   2.9,  3.8,  0.3, "ingrediente", "crea"),
    (357, "Spinaci baby, crudi",                    5, 23,   2.9,  3.6,  0.4, "ingrediente", "crea"),
    (328, "Bietola, cotta",                         5, 17,   1.6,  2.8,  0.2, "ingrediente", "crea"),
    (683, "Bietole colorate (arcobaleno), cotte",   5, 17,   1.6,  2.8,  0.2, "ingrediente", "crea"),
    (323, "Portulaca, cruda",                       5, 16,   1.3,  3.4,  0.1, "ingrediente", "crea"),
    (910, "Rucola selvaggia (wild rocket)",         5, 25,   2.6,  3.7,  0.7, "ingrediente", "crea"),
    (682, "Rucola, cotta",                          5, 23,   2.4,  3.2,  0.5, "ingrediente", "crea"),
    (360, "Tarassaco (dente di leone)",             5, 45,   2.7,  9.2,  0.7, "ingrediente", "crea"),
    (672, "Senape, foglie fresche",                 5, 27,   2.9,  4.7,  0.4, "ingrediente", "usda"),
    (354, "Crescione (watercress)",                 5, 11,   2.3,  1.3,  0.1, "ingrediente", "crea"),

    # ── Pak choi e orientali ────────────────────────────────────────────
    (324, "Pak choi (bok choy), crudo",             5, 13,   1.5,  2.2,  0.2, "ingrediente", "usda"),

    # ── Peperoni ────────────────────────────────────────────────────────
    (333, "Peperone giallo, crudo",                 5, 27,   1.0,  6.3,  0.2, "ingrediente", "crea"),
    (334, "Peperone verde, crudo",                  5, 22,   0.9,  4.6,  0.2, "ingrediente", "crea"),
    (335, "Peperoncino rosso, fresco",              5, 40,   1.9,  8.8,  0.4, "ingrediente", "crea"),
    (830, "Peperone rosso arrostito (in vasetto)",  5, 28,   0.9,  5.5,  0.5, "ingrediente", "crea"),
    (835, "Peperoni gialli arrostiti",              5, 29,   1.0,  6.0,  0.3, "ingrediente", "crea"),
    (832, "Friggitelli (peperoni piccoli verdi)",   5, 22,   0.9,  4.6,  0.2, "ingrediente", "crea"),
    (687, "Peperonata (peperoni cotti in olio/pomodoro)", 5, 55, 0.9, 5.0, 3.5, "ingrediente", "crea"),

    # ── Pomodori ────────────────────────────────────────────────────────
    (336, "Pomodori ciliegino",                     5, 20,   1.2,  3.9,  0.2, "ingrediente", "crea"),
    (831, "Pomodori datterini, freschi",            5, 20,   1.2,  3.9,  0.2, "ingrediente", "crea"),
    (836, "Pomodori ramati, freschi",               5, 20,   1.2,  3.9,  0.2, "ingrediente", "crea"),
    (678, "Pomodori verdi, crudi",                  5, 23,   1.2,  5.1,  0.2, "ingrediente", "usda"),
    (337, "Pomodori pelati (in scatola)",           5, 24,   1.2,  4.3,  0.2, "ingrediente", "crea"),
    (663, "Pomodoro secco (sun-dried)",             5, 258,  14.1, 55.8, 3.0, "ingrediente", "crea"),
    (664, "Pomodoro, passata (senza sale)",         5, 29,   1.3,  5.8,  0.2, "ingrediente", "crea"),
    (665, "Pomodoro, concentrato (doppio)",         5, 82,   4.3, 17.2,  0.5, "ingrediente", "crea"),

    # ── Zucchine ────────────────────────────────────────────────────────
    (338, "Zucchine, cotte a vapore",               5, 15,   1.2,  2.3,  0.1, "ingrediente", "crea"),
    (677, "Zucchine, crude a fettine",              5, 17,   1.3,  2.5,  0.1, "ingrediente", "crea"),
    (834, "Zucchine lunghe (romanesche)",           5, 17,   1.3,  2.5,  0.1, "ingrediente", "crea"),

    # ── Melanzane ───────────────────────────────────────────────────────
    (339, "Melanzane, grigliate",                   5, 35,   0.8,  6.6,  0.7, "ingrediente", "crea"),

    # ── Funghi ──────────────────────────────────────────────────────────
    (340, "Funghi porcini, crudi",                  5, 26,   3.1,  3.7,  0.3, "ingrediente", "crea"),
    (341, "Funghi shiitake, crudi",                 5, 34,   2.2,  6.8,  0.5, "ingrediente", "usda"),
    (342, "Funghi pleurotus (ostrica)",             5, 33,   3.3,  6.1,  0.4, "ingrediente", "usda"),
    (690, "Funghi secchi (porcini reidratati)",     5, 26,   3.1,  3.7,  0.3, "ingrediente", "crea"),

    # ── Radici e tuberi vari ────────────────────────────────────────────
    (343, "Ravanelli, crudi",                       5, 11,   0.7,  2.0,  0.1, "ingrediente", "crea"),
    (344, "Rape, crude",                            5, 18,   1.0,  3.8,  0.1, "ingrediente", "crea"),
    (345, "Daikon (ravanello giapponese)",          5, 18,   0.6,  4.1,  0.1, "ingrediente", "usda"),
    (346, "Sedano rapa, crudo",                     5, 23,   1.5,  3.7,  0.3, "ingrediente", "crea"),
    (347, "Pastinaca, cruda",                       5, 55,   1.2, 13.1,  0.3, "ingrediente", "crea"),

    # ── Asparagi ────────────────────────────────────────────────────────
    (348, "Asparagi, cotti",                        5, 22,   2.4,  4.1,  0.2, "ingrediente", "crea"),

    # ── Finocchio ───────────────────────────────────────────────────────
    (349, "Finocchio, cotto",                       5, 24,   1.0,  5.1,  0.2, "ingrediente", "crea"),
    (686, "Finocchi, crudi",                        5, 31,   1.3,  6.9,  0.1, "ingrediente", "crea"),

    # ── Legumi-ortaggi (piselli, mais, edamame) ─────────────────────────
    (350, "Piselli in scatola, sgocciolati",        5, 68,   4.4, 12.6,  0.3, "ingrediente", "crea"),
    (351, "Mais dolce, chicchi cotti",              5, 96,   3.4, 21.0,  1.2, "ingrediente", "crea"),
    (685, "Mais dolce in scatola, sgocciolato",     5, 72,   2.4, 15.4,  0.8, "ingrediente", "crea"),
    (680, "Edamame (baccelli cotti interi)",        5, 122, 11.9,  8.9,  5.2, "ingrediente", "usda"),

    # ── Germogli ────────────────────────────────────────────────────────
    (352, "Germogli di soia",                       5, 49,   5.5,  5.9,  1.4, "ingrediente", "crea"),
    (353, "Germogli di pisello",                    5, 124, 8.8, 22.1,  0.7, "ingrediente", "usda"),
    (676, "Germogli di bambù, in scatola",          5, 11,   1.5,  1.8,  0.2, "ingrediente", "usda"),

    # ── Erbe aromatiche ─────────────────────────────────────────────────
    (355, "Prezzemolo, fresco",                     5, 20,   3.0,  1.4,  0.6, "ingrediente", "crea"),
    (356, "Basilico, fresco",                       5, 22,   3.2,  1.0,  0.6, "ingrediente", "crea"),
    (913, "Erba cipollina, fresca",                 5, 30,   3.3,  4.4,  0.7, "ingrediente", "usda"),
    (914, "Menta fresca",                           5, 44,   3.3,  8.4,  0.7, "ingrediente", "crea"),
    (915, "Rosmarino fresco",                       5, 131,  3.3, 20.7,  5.9, "ingrediente", "crea"),
    (916, "Timo fresco",                            5, 101,  5.6, 24.4,  1.7, "ingrediente", "usda"),
    (917, "Origano fresco",                         5, 44,   2.2,  8.2,  1.0, "ingrediente", "crea"),

    # ── Olive ───────────────────────────────────────────────────────────
    (361, "Olive nere (in salamoia)",               5, 235,  1.6,  6.3, 23.0, "ingrediente", "crea"),
    (362, "Olive verdi (in salamoia)",              5, 142,  1.0,  3.8, 14.3, "ingrediente", "crea"),

    # ── Avocado ─────────────────────────────────────────────────────────
    (679, "Avocado, polpa",                         5, 160,  2.0,  8.5, 14.7, "ingrediente", "usda"),

    # ── Esotici e internazionali ────────────────────────────────────────
    (673, "Okra (gombo), cruda",                    5, 33,   1.9,  7.5,  0.2, "ingrediente", "usda"),
    (674, "Taro (colocasia), cotto",                5, 142,  0.5, 34.6,  0.1, "ingrediente", "usda"),
    (675, "Radice di loto, cruda",                  5, 74,   2.6, 17.2,  0.1, "ingrediente", "usda"),

    # ── Conserve e mix ──────────────────────────────────────────────────
    (688, "Passata di verdure mista",               5, 25,   1.0,  4.8,  0.3, "ingrediente", "crea"),
    (689, "Capperi sotto sale (dissalati)",          5, 23,   2.4,  1.7,  0.9, "ingrediente", "crea"),
    (691, "Cachi (persimon) secchi",                5, 274,  1.4, 73.4,  0.6, "ingrediente", "usda"),
]

# Sanity check
assert len(VEGETABLES) == 106, f"Expected 106 vegetables, got {len(VEGETABLES)}"
