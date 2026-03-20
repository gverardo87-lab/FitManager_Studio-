"""
recovery_foods_fruits.py — Dati macronutrienti frutta per recovery nutrition.db.

Contiene 60 alimenti dalla lista micronutrients_fruits.csv (recovery_food_list.json).
Tutti i valori sono per 100g di prodotto edibile.

Fonte primaria: CREA 2019 — Tabelle di Composizione degli Alimenti (IV edizione).
Fonte secondaria: USDA FoodData Central (per frutti non presenti nelle tabelle CREA).

Formato tupla:
  (id, nome, categoria_id, energia_kcal, proteine_g, carboidrati_g, grassi_g,
   food_type, source)

categoria_id = 6 (Frutta fresca) per tutti.
food_type = "ingrediente" per tutti.
source = "crea" per alimenti presenti nelle tabelle CREA italiane,
         "usda" per frutti tropicali/esotici non coperti da CREA.
"""

FRUITS = [
    # ── Frutta fresca — bacche e piccoli frutti ───────────────────────────
    #  (id,   nome,                                    cat, kcal,  prot, carb, gras, food_type, source)
    (363, "Ciliegia, fresca",                           6,   63,   1.1, 12.8,  0.3, "ingrediente", "crea"),
    (364, "Fico, fresco",                               6,   47,   1.0, 11.2,  0.2, "ingrediente", "crea"),
    (365, "Susina (prugna), fresca",                    6,   42,   0.5, 10.5,  0.1, "ingrediente", "crea"),
    (366, "Lamponi, freschi",                           6,   34,   1.0,  6.5,  0.6, "ingrediente", "crea"),
    (367, "More, fresche",                              6,   36,   1.4,  5.1,  0.4, "ingrediente", "crea"),
    (368, "Ribes rosso, fresco",                        6,   28,   1.1,  4.4,  0.2, "ingrediente", "crea"),
    (369, "Ribes nero, fresco",                         6,   28,   1.4,  6.6,  0.4, "ingrediente", "crea"),
    (370, "Uva spina (gooseberry)",                     6,   44,   0.9, 10.2,  0.6, "ingrediente", "crea"),
    (383, "Mirtilli rossi (cranberries), freschi",      6,   46,   0.5, 11.9,  0.1, "ingrediente", "usda"),
    (705, "Fragoline di bosco, fresche",                6,   27,   0.8,  6.0,  0.3, "ingrediente", "crea"),
    (841, "Bacche di aronia (chokeberry)",              6,   47,   1.4,  9.6,  0.5, "ingrediente", "usda"),

    # ── Frutta fresca — frutti tropicali ed esotici ───────────────────────
    (371, "Mango, fresco",                              6,   53,   0.8, 12.6,  0.4, "ingrediente", "crea"),
    (372, "Papaya, fresca",                             6,   28,   0.5,  6.9,  0.1, "ingrediente", "crea"),
    (388, "Lychee, fresco",                             6,   66,   0.8, 16.5,  0.4, "ingrediente", "usda"),
    (389, "Guava, fresca",                              6,   68,   2.6, 14.3,  1.0, "ingrediente", "usda"),
    (390, "Maracuja (frutto della passione)",           6,   97,   2.2, 23.4,  0.7, "ingrediente", "usda"),
    (698, "Carambola (star fruit)",                     6,   31,   1.0,  6.7,  0.3, "ingrediente", "usda"),

    # ── Frutta fresca — agrumi ────────────────────────────────────────────
    (384, "Lime, fresco",                               6,   30,   0.7, 10.5,  0.2, "ingrediente", "crea"),
    (385, "Clementina, fresca",                         6,   37,   0.9,  8.7,  0.1, "ingrediente", "crea"),
    (386, "Cedro, fresco",                              6,   11,   0.9,  2.3,  0.0, "ingrediente", "crea"),
    (693, "Pompelmo rosa, fresco",                      6,   42,   0.8, 10.7,  0.1, "ingrediente", "crea"),

    # ── Frutta fresca — pomacee e drupacee ────────────────────────────────
    (373, "Melograno, semi (arilli)",                   6,   63,   0.9, 15.9,  0.3, "ingrediente", "crea"),
    (374, "Kaki (cachi), fresco",                       6,   65,   0.6, 16.0,  0.3, "ingrediente", "crea"),
    (375, "Nespola, fresca",                            6,   28,   0.4,  6.8,  0.2, "ingrediente", "crea"),
    (376, "Giuggiola, fresca",                          6,   79,   1.2, 20.2,  0.2, "ingrediente", "usda"),
    (377, "Cocco, polpa fresca",                        6,  354,   3.3,  6.2, 33.5, "ingrediente", "crea"),
    (387, "Melograno, succo fresco",                    6,   44,   0.1, 10.6,  0.1, "ingrediente", "crea"),
    (694, "Nettarina (pesca noce), fresca",             6,   44,   1.1, 10.6,  0.3, "ingrediente", "crea"),
    (695, "Cocomero (anguria) a fette",                 6,   30,   0.6,  7.6,  0.2, "ingrediente", "crea"),
    (696, "Melone cantalupo, polpa",                    6,   34,   0.8,  8.2,  0.2, "ingrediente", "crea"),
    (697, "Mora di gelso, fresca",                      6,   43,   1.4,  9.8,  0.4, "ingrediente", "usda"),
    (699, "Mela cotogna, cruda",                        6,   26,   0.3,  6.7,  0.1, "ingrediente", "crea"),
    (701, "Kiwi verde, sbucciato",                      6,   61,   1.1, 14.6,  0.5, "ingrediente", "crea"),
    (702, "Kiwi giallo (golden), sbucciato",            6,   63,   1.0, 15.4,  0.3, "ingrediente", "usda"),
    (703, "Banana plantano, cotta",                     6,  116,   0.8, 31.2,  0.2, "ingrediente", "usda"),
    (704, "Pera abate, fresca",                         6,   35,   0.3,  8.8,  0.1, "ingrediente", "crea"),
    (837, "Fico d'India (ficodindia), polpa",           6,   53,   0.7, 12.0,  0.5, "ingrediente", "crea"),
    (838, "Corbezzolo, fresco",                         6,   76,   0.8, 17.1,  0.6, "ingrediente", "crea"),
    (842, "Mela rossa (Fuji), fresca",                  6,   52,   0.3, 13.8,  0.2, "ingrediente", "crea"),
    (843, "Mela verde (Granny Smith), fresca",          6,   52,   0.4, 13.6,  0.1, "ingrediente", "crea"),
    (844, "Pera Williams, fresca",                      6,   57,   0.4, 15.2,  0.1, "ingrediente", "crea"),
    (845, "Pesca bianca, fresca",                       6,   27,   0.8,  6.2,  0.1, "ingrediente", "crea"),
    (846, "Pesca tabacchiera, fresca",                  6,   39,   0.9,  9.5,  0.1, "ingrediente", "crea"),
    (921, "Giuggiola fresca tipo cinese",               6,   79,   1.2, 20.2,  0.2, "ingrediente", "usda"),

    # ── Frutta fresca — superberries / polveri ────────────────────────────
    (839, "Bacche di acai (polvere, 100%)",             6,  534,   8.1, 52.2, 32.5, "ingrediente", "usda"),
    (840, "Bacche di goji, essiccate",                  6,  349,  14.3, 64.1,  0.4, "ingrediente", "usda"),

    # ── Frutta essiccata ──────────────────────────────────────────────────
    (378, "Prugne secche (senza nocciolo)",             6,  220,   2.2, 54.7,  0.4, "ingrediente", "crea"),
    (379, "Albicocche secche",                          6,  266,   3.4, 63.4,  0.5, "ingrediente", "crea"),
    (380, "Fichi secchi",                               6,  256,   3.5, 58.0,  1.0, "ingrediente", "crea"),
    (381, "Datteri secchi",                             6,  282,   2.5, 73.5,  0.5, "ingrediente", "crea"),
    (382, "Uvetta sultanina",                           6,  283,   2.5, 72.6,  0.5, "ingrediente", "crea"),
    (391, "Banana, essiccata (chip)",                   6,  519,   2.3, 58.4, 33.6, "ingrediente", "crea"),
    (700, "Giuggiole secche",                           6,  287,   3.7, 73.6,  1.1, "ingrediente", "usda"),
    (706, "Ananas essiccato",                           6,  245,   1.7, 60.7,  0.4, "ingrediente", "usda"),
    (707, "Mango essiccato",                            6,  319,   2.4, 78.6,  1.2, "ingrediente", "usda"),
    (708, "Papaya essiccata",                           6,  327,   1.6, 82.2,  0.6, "ingrediente", "usda"),
    (918, "Litchi essiccato",                           6,  277,   3.8, 70.7,  1.2, "ingrediente", "usda"),
    (919, "Kaki essiccato (hoshigaki)",                 6,  274,   1.4, 72.6,  0.6, "ingrediente", "usda"),
    (922, "Carambola (starfruit) essiccata",            6,  243,   1.4, 60.5,  0.3, "ingrediente", "usda"),

    # ── Succhi / derivati liquidi ─────────────────────────────────────────
    (920, "Ribes nero (succo, senza zucchero)",         6,   28,   0.3,  6.5,  0.1, "ingrediente", "usda"),
]

# Sanity check: 60 alimenti
assert len(FRUITS) == 60, f"Attesi 60 frutti, trovati {len(FRUITS)}"

# Verifica ID unici
_ids = [f[0] for f in FRUITS]
assert len(_ids) == len(set(_ids)), f"ID duplicati: {[x for x in _ids if _ids.count(x) > 1]}"
