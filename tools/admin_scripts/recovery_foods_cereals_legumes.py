"""
recovery_foods_cereals_legumes.py — Dati macronutrienti CREA 2019 per cereali e legumi.

142 alimenti da micronutrients_cereals_legumes.csv.
Valori per 100g di prodotto edibile.

Fonte primaria: CREA 2019 — Tabelle di Composizione degli Alimenti (IV edizione).
Fonte secondaria: USDA FoodData Central (per alimenti non presenti in CREA).

Formato tupla:
  (id, nome, categoria_id, energia_kcal, proteine_g, carboidrati_g, grassi_g,
   food_type, source)

Categorie:
  1 = Cereali e derivati
  2 = Pasta, riso e cereali cotti
  3 = Pane e prodotti da forno
  4 = Legumi
"""

CEREALS_LEGUMES = [
    # ======================================================================
    # CATEGORIA 1 — Cereali e derivati (farine, chicchi crudi, fiocchi, crusca)
    # ======================================================================

    # --- Farine ---
    (227, "Frumento tenero, farina 00",              1, 340, 11.0, 74.3, 0.7, "ingrediente", "crea"),
    (228, "Frumento tenero, farina integrale",       1, 319, 11.9, 63.2, 1.9, "ingrediente", "crea"),
    (229, "Frumento duro, semola",                   1, 339, 11.5, 72.0, 0.5, "ingrediente", "crea"),
    (230, "Segale, farina integrale",                1, 325, 10.9, 60.7, 2.0, "ingrediente", "crea"),
    (240, "Farina di ceci",                          1, 387, 22.4, 46.9, 6.7, "ingrediente", "crea"),
    (241, "Farina di mandorle",                      1, 589, 20.0,  9.6, 54.0, "ingrediente", "usda"),
    (242, "Farina di cocco",                         1, 443, 19.3, 17.6, 14.7, "ingrediente", "usda"),
    (243, "Farina di riso",                          1, 362, 7.4, 78.5, 1.4, "ingrediente", "crea"),
    (244, "Farina di mais (maizena)",                1, 353, 0.3, 86.9, 0.1, "ingrediente", "crea"),
    (245, "Farina di castagne",                      1, 343, 6.1, 71.4, 3.4, "ingrediente", "crea"),
    (627, "Frumento tenero, farina 0",               1, 341, 11.5, 73.0, 1.0, "ingrediente", "crea"),
    (628, "Frumento tenero, farina 1",               1, 337, 12.0, 70.0, 1.2, "ingrediente", "crea"),
    (629, "Frumento tenero, farina 2 (semintegrale)", 1, 330, 12.3, 67.5, 1.5, "ingrediente", "crea"),
    (632, "Farina di lupini",                        1, 371, 40.4, 14.1, 9.7, "ingrediente", "usda"),
    (633, "Farina di soia sgrassata",                1, 329, 47.0, 30.6, 1.2, "ingrediente", "crea"),
    (634, "Farina di grano saraceno",                1, 335, 12.6, 66.7, 3.1, "ingrediente", "crea"),
    (635, "Semolino di frumento",                    1, 339, 11.5, 72.0, 0.5, "ingrediente", "crea"),

    # --- Chicchi crudi ---
    (231, "Miglio, crudo",                           1, 356, 11.0, 72.9, 4.2, "ingrediente", "crea"),
    (232, "Amaranto, crudo",                         1, 371, 13.6, 65.3, 7.0, "ingrediente", "usda"),
    (233, "Triticale, crudo",                        1, 336, 13.1, 72.1, 2.1, "ingrediente", "usda"),
    (234, "Kamut (grano khorasan), crudo",           1, 337, 14.5, 68.2, 2.1, "ingrediente", "usda"),
    (235, "Teff, crudo",                             1, 367, 13.3, 73.1, 2.4, "ingrediente", "usda"),
    (236, "Sorgo, crudo",                            1, 339, 11.3, 74.6, 3.3, "ingrediente", "usda"),
    (249, "Riso basmati, crudo",                     1, 346, 8.1, 75.0, 0.6, "ingrediente", "crea"),
    (250, "Riso parboiled, crudo",                   1, 337, 7.4, 75.8, 0.3, "ingrediente", "crea"),
    (251, "Riso venere, crudo",                      1, 340, 8.5, 72.0, 2.8, "ingrediente", "usda"),
    (252, "Riso arborio, crudo",                     1, 354, 6.5, 79.4, 0.5, "ingrediente", "crea"),
    (631, "Orzo mondo (integrale), crudo",           1, 354, 12.5, 73.5, 2.3, "ingrediente", "usda"),
    (814, "Riso rosso (Camargue), crudo",            1, 355, 7.0, 76.0, 2.5, "ingrediente", "usda"),
    (815, "Farro spelta, chicchi crudi",             1, 338, 14.6, 70.2, 2.4, "ingrediente", "usda"),

    # --- Crusca e germe ---
    (237, "Crusca di frumento",                      1, 216, 14.1, 26.6, 4.3, "ingrediente", "crea"),
    (238, "Crusca d'avena",                          1, 246, 17.3, 50.8, 7.0, "ingrediente", "usda"),
    (239, "Germe di grano",                          1, 382, 23.2, 51.8, 9.7, "ingrediente", "crea"),

    # --- Fiocchi ---
    (246, "Fiocchi di orzo",                         1, 319, 10.0, 68.0, 1.0, "ingrediente", "crea"),
    (247, "Fiocchi di segale",                       1, 325, 10.9, 60.7, 2.0, "ingrediente", "crea"),
    (248, "Fiocchi di farro",                        1, 335, 14.7, 67.7, 2.5, "ingrediente", "crea"),
    (630, "Fiocchi di quinoa",                       1, 368, 14.1, 64.2, 6.1, "ingrediente", "usda"),

    # --- Pasta secca e simili (cat 1 = materia prima cruda) ---
    (253, "Pasta all'uovo, secca",                   1, 366, 13.0, 68.0, 4.6, "ingrediente", "crea"),
    (636, "Pop corn (sgonfio, senza grassi)",        1, 387, 12.9, 77.8, 4.5, "ingrediente", "usda"),

    # --- Cereali da colazione ---
    (287, "Muesli senza zucchero aggiunto",          1, 365, 10.4, 60.4, 9.7, "ingrediente", "usda"),
    (288, "Granola tostata",                         1, 471, 10.1, 60.5, 20.3, "pietanza", "usda"),

    # --- Pasta secca speciale (cat 1) ---
    (811, "Pasta proteica (+proteine di legumi), secca", 1, 348, 23.0, 53.0, 4.0, "ingrediente", "usda"),
    (813, "Pasta di edamame/soia, secca",            1, 345, 42.0, 22.0, 7.5, "ingrediente", "usda"),
    (898, "Pasta di lenticchie rosse, secca",        1, 344, 25.0, 48.0, 2.5, "ingrediente", "usda"),

    # ======================================================================
    # CATEGORIA 2 — Pasta, riso e cereali cotti
    # ======================================================================

    (254, "Pasta all'uovo, cotta",                   2, 136, 5.1, 24.0, 1.8, "pietanza", "crea"),
    (255, "Gnocchi di patate, cotti",                2, 133, 3.2, 27.0, 1.0, "pietanza", "crea"),
    (256, "Riso basmati, cotto",                     2, 121, 3.5, 25.2, 0.4, "pietanza", "crea"),
    (257, "Orzo perlato, cotto",                     2, 123, 2.3, 28.2, 0.4, "pietanza", "crea"),
    (258, "Miglio, cotto",                           2, 119, 3.5, 23.7, 1.0, "pietanza", "usda"),
    (259, "Bulgur, cotto",                           2,  83, 3.1, 18.6, 0.2, "pietanza", "crea"),
    (260, "Avena, cotta (porridge)",                 2,  71, 2.5, 12.0, 1.5, "pietanza", "usda"),
    (261, "Riso venere, cotto",                      2, 122, 3.2, 24.5, 1.1, "pietanza", "usda"),
    (262, "Pasta di riso, cotta",                    2, 109, 0.9, 24.9, 0.2, "pietanza", "usda"),
    (263, "Pasta di farro, cotta",                   2, 141, 6.0, 27.0, 0.9, "pietanza", "crea"),
    (264, "Pasta di legumi (ceci/lenticchie), cotta", 2, 137, 8.8, 19.8, 2.0, "pietanza", "usda"),
    (265, "Grano saraceno, cotto",                   2,  92, 3.4, 19.9, 0.6, "pietanza", "usda"),
    (266, "Amaranto, cotto",                         2, 102, 3.8, 18.7, 1.6, "pietanza", "usda"),
    (267, "Risotto semplice (burro/parmigiano)",     2, 145, 3.5, 22.0, 4.5, "pietanza", "crea"),
    (637, "Riso parboiled, cotto",                   2, 123, 2.9, 27.5, 0.2, "pietanza", "crea"),
    (638, "Pasta gluten-free riso/mais, cotta",      2, 124, 1.8, 27.0, 0.5, "pietanza", "usda"),
    (639, "Spätzle (gnocchetti tirolesi), cotti",    2, 140, 5.0, 24.0, 2.5, "pietanza", "usda"),
    (640, "Trofie, cotte",                           2, 140, 5.0, 28.0, 0.8, "pietanza", "crea"),
    (641, "Penne integrali, cotte",                  2, 136, 5.3, 26.5, 0.8, "pietanza", "crea"),
    (642, "Lasagne fresche, cotte",                  2, 131, 5.3, 22.0, 2.3, "pietanza", "crea"),
    (812, "Pasta di konjac (shirataki, cotta)",      2,   9, 0.1,  2.3, 0.0, "pietanza", "usda"),
    (901, "Teff, cotto",                             2, 101, 3.9, 19.9, 0.6, "pietanza", "usda"),
    (902, "Sorgo, cotto",                            2, 100, 3.5, 21.7, 0.7, "pietanza", "usda"),

    # ======================================================================
    # CATEGORIA 3 — Pane e prodotti da forno
    # ======================================================================

    # --- Pane ---
    (268, "Pane ciabatta",                           3, 271, 8.3, 52.0, 3.1, "pietanza", "crea"),
    (269, "Pane di Altamura (semola)",               3, 269, 8.3, 53.0, 1.5, "pietanza", "crea"),
    (270, "Pane al latte",                           3, 296, 8.4, 50.0, 6.5, "pietanza", "crea"),
    (271, "Pane in cassetta (toast)",                3, 261, 8.0, 49.0, 3.5, "pietanza", "crea"),
    (272, "Pane azzimo (matza)",                     3, 371, 10.5, 77.7, 1.4, "pietanza", "crea"),
    (279, "Pancarr\u00e9 di segale",                 3, 259, 8.5, 48.0, 3.3, "pietanza", "crea"),
    (283, "Pane senza glutine",                      3, 252, 3.3, 50.0, 3.8, "pietanza", "usda"),
    (643, "Pane di kamut, biologico",                3, 262, 9.5, 49.0, 2.2, "pietanza", "usda"),
    (644, "Pane con noci",                           3, 303, 8.5, 44.0, 10.5, "pietanza", "crea"),
    (645, "Pane all'olio",                           3, 299, 7.8, 50.0, 7.5, "pietanza", "crea"),
    (652, "Pane azzimo integrale",                   3, 345, 12.2, 69.0, 2.4, "pietanza", "usda"),
    (653, "Baguette francese",                       3, 274, 9.0, 53.0, 1.6, "pietanza", "usda"),
    (654, "Naan indiano",                            3, 291, 9.1, 47.5, 7.1, "pietanza", "usda"),
    (816, "Panino al sesamo",                        3, 280, 8.6, 48.0, 5.5, "pietanza", "usda"),
    (817, "Pane tipo pugliese (semola rimacinata)",  3, 267, 8.0, 53.0, 1.3, "pietanza", "crea"),
    (818, "Pane di mais senza glutine",              3, 260, 4.2, 48.5, 5.0, "pietanza", "usda"),
    (819, "Pane di segale compatto (tipo wasa)",     3, 320, 10.0, 62.0, 2.0, "pietanza", "usda"),
    (899, "Chapati (pane indiano integrale)",        3, 299, 9.8, 52.0, 5.7, "pietanza", "usda"),
    (903, "Pane di patate",                          3, 266, 5.8, 47.0, 5.5, "pietanza", "usda"),

    # --- Crackers, grissini, fette biscottate ---
    (273, "Grissini torinesi",                       3, 412, 12.3, 68.0, 10.0, "pietanza", "crea"),
    (274, "Crackers integrali",                      3, 413, 10.0, 63.0, 13.0, "pietanza", "crea"),
    (275, "Fette biscottate classiche",              3, 408, 11.3, 75.0, 6.5, "pietanza", "crea"),
    (282, "Fette biscottate senza glutine",          3, 400, 4.5, 72.0, 9.5, "pietanza", "usda"),
    (284, "Cracker di riso (gallette mini)",         3, 392, 7.4, 84.0, 2.8, "pietanza", "usda"),
    (651, "Fetta biscottata alla frutta",            3, 385, 8.5, 72.0, 7.0, "pietanza", "crea"),

    # --- Piadine, tortillas, focacce ---
    (276, "Piadina romagnola",                       3, 345, 8.6, 50.0, 12.6, "pietanza", "crea"),
    (277, "Tortilla di frumento",                    3, 312, 8.1, 52.0, 8.0, "pietanza", "usda"),
    (278, "Tortilla di mais",                        3, 218, 5.7, 44.6, 2.4, "pietanza", "usda"),
    (646, "Focaccia genovese",                       3, 283, 7.0, 41.0, 10.0, "pietanza", "crea"),
    (647, "Schiacciata toscana",                     3, 293, 7.5, 43.0, 10.5, "pietanza", "crea"),
    (900, "Tortilla di farro",                       3, 300, 9.5, 49.0, 7.0, "pietanza", "usda"),

    # --- Taralli, biscotti, dolci da forno ---
    (285, "Taralli pugliesi",                        3, 438, 9.4, 60.0, 17.5, "pietanza", "crea"),
    (280, "Biscotti secchi (tipo digestive)",        3, 457, 7.1, 65.0, 18.5, "pietanza", "crea"),
    (281, "Biscotti frollini classici",              3, 475, 6.5, 62.0, 22.0, "pietanza", "crea"),
    (286, "Cornetto (brioche vuoto)",                3, 396, 7.2, 52.0, 17.0, "pietanza", "crea"),
    (648, "Crespelle (cr\u00eapes, neutre)",         3, 204, 6.4, 23.0, 9.4, "pietanza", "usda"),
    (649, "Waffle (neutro base)",                    3, 312, 7.5, 38.0, 14.0, "pietanza", "usda"),
    (650, "Muffin all'avena (senza latticini)",      3, 310, 6.0, 48.0, 10.0, "pietanza", "usda"),
    (820, "Tortino di mais (polenta al forno)",      3, 160, 3.5, 25.0, 5.0, "pietanza", "crea"),
    (904, "Crumble di avena (base dolce)",           3, 420, 7.0, 55.0, 18.5, "pietanza", "usda"),
    (905, "Biscotto al cocco (tipo Oro Saiwa)",      3, 480, 5.5, 63.0, 22.5, "pietanza", "crea"),

    # ======================================================================
    # CATEGORIA 4 — Legumi
    # ======================================================================

    # --- Fagioli ---
    (289, "Fagioli neri, cotti",                     4, 132, 8.9, 23.7, 0.5, "ingrediente", "usda"),
    (290, "Fagioli di soia (edamame sgranati, crudi)", 4, 147, 12.4, 11.1, 6.8, "ingrediente", "usda"),
    (294, "Fagioli cannellini, secchi",              4, 311, 23.4, 47.0, 1.6, "ingrediente", "crea"),
    (297, "Fagioli azuki, cotti",                    4, 128, 7.5, 24.8, 0.1, "ingrediente", "usda"),
    (298, "Fagioli di Spagna, cotti",                4, 128, 8.3, 22.4, 0.4, "ingrediente", "crea"),
    (301, "Fagioli mung, cotti",                     4, 105, 7.0, 19.2, 0.4, "ingrediente", "usda"),
    (655, "Fagioli di Lamon, cotti",                 4, 130, 9.0, 22.0, 0.5, "ingrediente", "crea"),
    (658, "Fagioli all'occhio, cotti",               4, 116, 7.7, 20.8, 0.5, "ingrediente", "usda"),

    # --- Lenticchie ---
    (291, "Lenticchie rosse, cotte",                 4, 116, 9.0, 20.1, 0.4, "ingrediente", "crea"),
    (292, "Lenticchie verdi, cotte",                 4, 116, 9.0, 20.1, 0.4, "ingrediente", "crea"),
    (660, "Lenticchie beluga (nere), cotte",         4, 116, 9.0, 20.1, 0.4, "ingrediente", "usda"),

    # --- Ceci ---
    (295, "Ceci, secchi tostati (snack)",            4, 419, 21.3, 47.1, 15.2, "pietanza", "usda"),
    (657, "Ceci neri, cotti",                        4, 164, 8.9, 27.4, 2.6, "ingrediente", "usda"),

    # --- Piselli ---
    (293, "Piselli freschi, crudi",                  4,  81, 5.4, 14.5, 0.4, "ingrediente", "crea"),
    (300, "Piselli secchi, cotti",                   4, 118, 8.3, 21.1, 0.4, "ingrediente", "crea"),
    (661, "Piselli spezzati gialli, cotti",          4, 118, 8.3, 21.1, 0.4, "ingrediente", "usda"),
    (907, "Piselli primavera surgelati (cotti)",     4,  78, 5.2, 13.6, 0.3, "ingrediente", "crea"),

    # --- Fave ---
    (659, "Fave fresche, crude",                     4,  62, 5.6, 10.2, 0.6, "ingrediente", "crea"),

    # --- Cicerchie ---
    (299, "Cicerchie, cotte",                        4, 138, 8.9, 24.2, 0.7, "ingrediente", "crea"),

    # --- Lupini ---
    (296, "Lupini, lessati",                         4, 119, 16.4, 9.9, 2.9, "ingrediente", "crea"),

    # --- Soia e derivati ---
    (302, "Soia, farina sgrassata",                  4, 329, 47.0, 30.6, 1.2, "ingrediente", "crea"),
    (303, "Tempeh (soia fermentata)",                4, 192, 20.3, 7.6, 10.8, "pietanza", "usda"),
    (304, "Tofu, compatto (firm)",                   4,  76, 8.1, 1.9, 4.8, "pietanza", "usda"),
    (305, "Tofu, morbido (silken)",                  4,  55, 4.8, 2.5, 2.7, "pietanza", "usda"),
    (662, "Soia, granuli texturizzati secchi (TVP)", 4, 327, 51.5, 33.9, 1.2, "ingrediente", "usda"),

    # --- Fagiolini (legumi freschi) ---
    (656, "Fagiolini piattoni, cotti",               4,  35, 2.4, 7.1, 0.3, "ingrediente", "crea"),
    (906, "Fagiolini in scatola (sgocciolati)",      4,  25, 1.5, 4.7, 0.2, "ingrediente", "crea"),

    # --- Hummus e piatti pronti di legumi ---
    (306, "Hummus (crema di ceci)",                  4, 166, 7.9, 14.3, 9.6, "pietanza", "usda"),
    (821, "Zuppa di lenticchie (piatto pronto)",     4,  62, 3.8, 10.0, 0.8, "pietanza", "usda"),
    (822, "Passata di ceci (hummus base ridotta)",   4, 139, 7.0, 14.0, 6.0, "pietanza", "usda"),
    (823, "Fagioli al pomodoro (in scatola)",        4,  82, 4.8, 14.0, 0.5, "pietanza", "usda"),
    (824, "Minestrone con legumi (piatto pronto)",   4,  50, 2.5,  8.5, 0.5, "pietanza", "crea"),
    (908, "Ceci al curry (piatto pronto)",           4, 140, 6.0, 18.0, 5.0, "pietanza", "usda"),
    (909, "Zuppa di fagioli neri",                   4,  68, 4.2, 11.0, 0.8, "pietanza", "usda"),
]

# Validazione: 142 alimenti attesi
assert len(CEREALS_LEGUMES) == 142, (
    f"Attesi 142 alimenti, trovati {len(CEREALS_LEGUMES)}"
)

# Validazione: nessun ID duplicato
_ids = [t[0] for t in CEREALS_LEGUMES]
assert len(_ids) == len(set(_ids)), (
    f"ID duplicati: {[x for x in _ids if _ids.count(x) > 1]}"
)
