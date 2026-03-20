"""
recovery_foods_dairy.py — Dati macronutrienti latticini per recovery nutrition.db.

Fonte primaria: CREA 2019 — Tabelle di Composizione degli Alimenti (IV edizione).
Fonte secondaria: USDA FoodData Central (per prodotti non italiani).

Tutti i valori sono per 100g di prodotto edibile.

Formato tupla:
  (id, nome, categoria_id, energia_kcal, proteine_g, carboidrati_g, grassi_g,
   food_type, source)

categoria_id = 12 → "Latte, yogurt e formaggi"
"""

# ---------------------------------------------------------------------------
# DAIRY — 55 alimenti da micronutrients_dairy.csv
# ---------------------------------------------------------------------------

DAIRY = [
    # ── Latti ──────────────────────────────────────────────────────────────
    #  id   nome                              cat  kcal  prot  carb  gras  type          source
    (510, "Latte di capra, intero",            12,  76,   3.6,  4.7,  4.3, "ingrediente", "crea"),
    (511, "Latte condensato zuccherato",       12, 321,   8.2, 54.4,  8.7, "ingrediente", "crea"),
    (512, "Latte in polvere scremato",         12, 351,  36.2, 52.0,  0.8, "ingrediente", "crea"),
    (513, "Latte fermentato (kefir)",          12,  65,   3.3,  4.0,  3.5, "ingrediente", "crea"),
    (539, "Latte di cocco (in lattina)",       12, 197,   2.0,  2.8, 20.0, "ingrediente", "usda"),
    (769, "Latte d'asina (equino)",            12,  43,   1.7,  6.2,  1.0, "ingrediente", "crea"),
    (941, "Latte intero UHT",                  12,  64,   3.3,  4.9,  3.6, "ingrediente", "crea"),

    # ── Yogurt ─────────────────────────────────────────────────────────────
    (514, "Yogurt intero con frutta",          12,  97,   3.4, 14.1,  2.9, "ingrediente", "crea"),
    (515, "Yogurt magro bianco",               12,  43,   3.8,  5.4,  0.9, "ingrediente", "crea"),
    (516, "Yogurt greco 2% grassi",            12,  73,   8.7,  4.0,  2.0, "ingrediente", "usda"),
    (774, "Yogurt di capra, intero",           12,  74,   4.0,  4.3,  4.3, "ingrediente", "crea"),
    (875, "Yogurt greco proteico (15g prot/100g)", 12, 87, 15.0, 4.0, 1.5, "ingrediente", "usda"),
    (943, "Yogurt al frutto di bosco (magro)", 12,  55,   3.5,  8.5,  0.8, "ingrediente", "crea"),

    # ── Bevande fermentate ─────────────────────────────────────────────────
    (775, "Ayran (bevanda yogurt turca)",      12,  38,   1.7,  2.5,  1.8, "ingrediente", "usda"),
    (776, "Lassi dolce (bevanda yogurt indiana)", 12, 72,  2.0, 11.0,  2.0, "ingrediente", "usda"),
    (944, "Kefir di acqua (water kefir)",      12,  18,   0.0,  4.5,  0.0, "ingrediente", "usda"),

    # ── Formaggi duri / stagionati ─────────────────────────────────────────
    (517, "Parmigiano Reggiano DOP (grattugiato)", 12, 392, 33.0, 0.0, 28.4, "ingrediente", "crea"),
    (518, "Grana Padano DOP",                  12, 398,  33.9,  0.0, 29.0, "ingrediente", "crea"),
    (519, "Pecorino romano DOP",               12, 387,  25.8,  0.2, 31.8, "ingrediente", "crea"),
    (520, "Pecorino stagionato",               12, 392,  25.5,  0.2, 32.0, "ingrediente", "crea"),
    (762, "Parmigiano Reggiano 24 mesi",       12, 392,  33.0,  0.0, 28.4, "ingrediente", "crea"),
    (764, "Asiago d'allevo (stagionato)",      12, 382,  28.0,  0.0, 30.0, "ingrediente", "crea"),
    (872, "Caciocavallo podolico stagionato",  12, 380,  26.0,  0.5, 30.5, "ingrediente", "crea"),
    (873, "Pecorino di Pienza",                12, 390,  25.0,  0.3, 32.0, "ingrediente", "crea"),

    # ── Formaggi semiduri ──────────────────────────────────────────────────
    (521, "Emmenthal (Emmentaler)",            12, 380,  28.5,  0.4, 29.7, "ingrediente", "crea"),
    (522, "Fontina DOP",                       12, 343,  24.5,  0.8, 27.0, "ingrediente", "crea"),
    (523, "Provolone",                         12, 351,  26.3,  0.6, 26.6, "ingrediente", "crea"),
    (534, "Caciotta toscana",                  12, 364,  25.0,  0.5, 29.0, "ingrediente", "crea"),
    (763, "Asiago pressato (fresco)",          12, 356,  25.0,  0.0, 28.0, "ingrediente", "crea"),
    (765, "Scamorza affumicata",               12, 290,  22.0,  1.0, 22.0, "ingrediente", "crea"),
    (766, "Montasio DOP",                      12, 370,  25.5,  0.0, 30.0, "ingrediente", "crea"),
    (940, "Caciotta fresca (tipo formaggella)", 12, 285, 20.0,  0.8, 22.5, "ingrediente", "crea"),

    # ── Formaggi erborinati ────────────────────────────────────────────────
    (524, "Gorgonzola DOP",                    12, 320,  19.4,  0.5, 27.0, "ingrediente", "crea"),

    # ── Formaggi molli / crosta lavata ─────────────────────────────────────
    (525, "Taleggio DOP",                      12, 315,  19.0,  0.9, 26.2, "ingrediente", "crea"),
    (526, "Brie",                              12, 334,  20.8,  0.5, 27.7, "ingrediente", "usda"),
    (527, "Camembert",                         12, 299,  19.8,  0.5, 24.3, "ingrediente", "usda"),

    # ── Formaggi freschi / spalmabili ──────────────────────────────────────
    (528, "Ricotta di pecora",                 12, 157,  11.4,  3.5, 11.5, "ingrediente", "crea"),
    (529, "Mascarpone",                        12, 455,   4.6,  2.3, 47.0, "ingrediente", "crea"),
    (530, "Burrata",                           12, 240,  14.0,  1.0, 20.0, "ingrediente", "crea"),
    (531, "Crescenza (stracchino)",            12, 281,  16.1,  1.9, 23.3, "ingrediente", "crea"),
    (532, "Robiola",                           12, 338,  20.0,  1.6, 28.0, "ingrediente", "crea"),
    (533, "Formaggio spalmabile (tipo Philadelphia)", 12, 253, 6.2, 3.5, 24.5, "ingrediente", "usda"),
    (535, "Quark (fiocchi proteici 0.2%)",     12,  67,  12.0,  4.0,  0.2, "ingrediente", "usda"),
    (536, "Feta DOP",                          12, 264,  14.2,  4.1, 21.3, "ingrediente", "usda"),
    (537, "Halloumi (cipriota)",               12, 321,  21.0,  2.6, 25.0, "ingrediente", "usda"),
    (538, "Ricotta vaccina (light < 8%g)",     12, 110,   9.5,  4.0,  6.0, "ingrediente", "crea"),
    (767, "Stracchino (crescenza fresca)",     12, 281,  16.1,  1.9, 23.3, "ingrediente", "crea"),
    (768, "Squacquerone di Romagna DOP",       12, 230,  13.0,  2.0, 19.5, "ingrediente", "crea"),
    (874, "Mozzarella affumicata",             12, 265,  19.9,  1.0, 20.3, "ingrediente", "crea"),
    (876, "Ricotta al forno (siciliana)",      12, 204,  12.0,  3.0, 16.0, "ingrediente", "crea"),

    # ── Panna e grassi lattieri ────────────────────────────────────────────
    (770, "Burro di cacao (cosmesi/food)",     12, 884,   0.0,  0.0, 100.0, "ingrediente", "usda"),
    (771, "Panna da cucina (18% grassi)",      12, 178,   2.6,  3.8, 17.0, "ingrediente", "crea"),
    (772, "Panna fresca (35% grassi)",         12, 337,   2.0,  2.7, 35.0, "ingrediente", "crea"),
    (942, "Panna acida (sour cream)",          12, 193,   2.4,  3.4, 19.4, "ingrediente", "usda"),

    # ── Gelato / dessert ───────────────────────────────────────────────────
    (773, "Gelato proteico (alto prot, basso grassi)", 12, 120, 12.0, 14.0, 2.5, "ingrediente", "usda"),
]
