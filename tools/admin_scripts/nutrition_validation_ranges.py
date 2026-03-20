"""
Range di validazione scientifica per micronutrienti — CREA 2019 / LARN 2014.

Usato da tutti gli script di seed e backfill per verificare che i valori
inseriti siano plausibili. Un valore fuori range NON viene inserito ma
viene loggato come WARNING per review manuale.

Fonte: Tabelle di Composizione degli Alimenti, CREA 2019, IV edizione.
Range derivati dai valori min/max osservati per categoria alimentare.

Per 100g di prodotto edibile.
"""

# Range plausibili per CATEGORIA → MICRONUTRIENTE
# Formato: (min, max) — valori fuori range = WARNING
# None = nessun limite (campo opzionale per quella categoria)

# ══════════════════════════════════════════════════════════════
# MINERALI (per 100g)
# ══════════════════════════════════════════════════════════════

MINERAL_RANGES = {
    "calcio_mg":    (0, 1300),   # max: parmigiano 1159mg, latte in polvere ~1200
    "ferro_mg":     (0, 50),     # max: fegato suino ~18, timo secco ~50 (spezie)
    "zinco_mg":     (0, 25),     # max: ostriche ~16, germe grano ~12
    "magnesio_mg":  (0, 650),    # max: crusca frumento ~611 (USDA), semi zucca ~530
    "fosforo_mg":   (0, 1500),   # max: crusca frumento ~1200, parmigiano ~700
    "potassio_mg":  (0, 3500),   # max: pomodoro secco ~3427, concentrato ~2500, legumi secchi ~1700
    "selenio_ug":   (0, 200),    # max: noci brasile ~1917 (outlier), pesce ~100
}

# ══════════════════════════════════════════════════════════════
# VITAMINE (per 100g)
# ══════════════════════════════════════════════════════════════

VITAMIN_RANGES = {
    "vitamina_a_ug":    (0, 35000),  # max: olio fegato merluzzo ~30000, fegato vitello ~21600
    "vitamina_d_ug":    (0, 260),    # max: olio fegato merluzzo ~250, pesce grasso ~25
    "vitamina_e_mg":    (0, 100),    # max: olio germe grano ~87, oli vegetali ~50
    "vitamina_c_mg":    (0, 250),    # max: peperoncino ~229, ribes nero ~200
    "vitamina_b1_mg":   (0, 5),      # max: lievito birra ~4.5, germe grano ~2
    "vitamina_b2_mg":   (0, 5),      # max: fegato ~3.5, lievito ~4
    "vitamina_b3_mg":   (0, 50),     # max: lievito birra ~40, fegato ~17
    "vitamina_b6_mg":   (0, 5),      # max: fegato ~1, patata ~0.7
    "vitamina_b9_ug":   (0, 600),    # max: fegato ~330, lievito ~500
    "vitamina_b12_ug":  (0, 120),    # max: fegato bovino ~110, reni ~60
}

ALL_MICRO_FIELDS = list(MINERAL_RANGES.keys()) + list(VITAMIN_RANGES.keys())
ALL_RANGES = {**MINERAL_RANGES, **VITAMIN_RANGES}


def validate_micronutrients(nome: str, micros: dict) -> list[str]:
    """Valida i micronutrienti di un alimento contro i range CREA.

    Returns: lista di warning (vuota = tutto OK).
    """
    warnings = []
    for field, value in micros.items():
        if value is None:
            continue
        range_limits = ALL_RANGES.get(field)
        if range_limits is None:
            continue
        lo, hi = range_limits
        if value < lo or value > hi:
            warnings.append(
                f"{nome}: {field}={value} fuori range [{lo}-{hi}]"
            )
    return warnings


# ══════════════════════════════════════════════════════════════
# VALORI TIPICI PER CATEGORIA (media CREA 2019)
# Usati come fallback quando il valore specifico non è noto.
# MAI usare come fonte primaria — solo per stima con source="stima"
# ══════════════════════════════════════════════════════════════

CATEGORY_TYPICAL_MICROS = {
    # cat_id: {field: valore_tipico_medio}
    # Verdure e ortaggi
    5: {
        "calcio_mg": 40, "ferro_mg": 0.8, "zinco_mg": 0.3, "magnesio_mg": 18,
        "fosforo_mg": 35, "potassio_mg": 260, "selenio_ug": 0.5,
        "vitamina_a_ug": 200, "vitamina_c_mg": 25, "vitamina_b1_mg": 0.06,
        "vitamina_b2_mg": 0.05, "vitamina_b3_mg": 0.5, "vitamina_b6_mg": 0.1,
        "vitamina_b9_ug": 40,
    },
    # Frutta fresca
    6: {
        "calcio_mg": 15, "ferro_mg": 0.3, "zinco_mg": 0.1, "magnesio_mg": 10,
        "fosforo_mg": 15, "potassio_mg": 170, "selenio_ug": 0.3,
        "vitamina_a_ug": 20, "vitamina_c_mg": 30, "vitamina_b1_mg": 0.03,
        "vitamina_b2_mg": 0.03, "vitamina_b3_mg": 0.3, "vitamina_b6_mg": 0.05,
        "vitamina_b9_ug": 10,
    },
    # Carne e pollame
    8: {
        "calcio_mg": 10, "ferro_mg": 1.5, "zinco_mg": 3.0, "magnesio_mg": 22,
        "fosforo_mg": 180, "potassio_mg": 300, "selenio_ug": 15,
        "vitamina_b1_mg": 0.08, "vitamina_b2_mg": 0.15, "vitamina_b3_mg": 5.0,
        "vitamina_b6_mg": 0.35, "vitamina_b12_ug": 2.0,
    },
    # Prodotti ittici
    10: {
        "calcio_mg": 25, "ferro_mg": 0.8, "zinco_mg": 0.6, "magnesio_mg": 28,
        "fosforo_mg": 200, "potassio_mg": 350, "selenio_ug": 35,
        "vitamina_d_ug": 5.0, "vitamina_b12_ug": 3.0, "vitamina_b3_mg": 4.0,
    },
    # Legumi
    4: {
        "calcio_mg": 50, "ferro_mg": 2.5, "zinco_mg": 1.2, "magnesio_mg": 50,
        "fosforo_mg": 150, "potassio_mg": 400, "selenio_ug": 2.0,
        "vitamina_b1_mg": 0.15, "vitamina_b9_ug": 100,
    },
    # Cereali e derivati
    1: {
        "calcio_mg": 25, "ferro_mg": 2.0, "zinco_mg": 1.5, "magnesio_mg": 50,
        "fosforo_mg": 200, "potassio_mg": 250, "selenio_ug": 10,
        "vitamina_b1_mg": 0.2, "vitamina_b2_mg": 0.1, "vitamina_b3_mg": 3.0,
    },
    # Latte, yogurt e formaggi
    12: {
        "calcio_mg": 200, "ferro_mg": 0.3, "zinco_mg": 1.0, "magnesio_mg": 15,
        "fosforo_mg": 150, "potassio_mg": 160, "selenio_ug": 3.0,
        "vitamina_a_ug": 50, "vitamina_d_ug": 0.5, "vitamina_b2_mg": 0.2,
        "vitamina_b12_ug": 0.5,
    },
    # Uova
    11: {
        "calcio_mg": 50, "ferro_mg": 1.5, "zinco_mg": 1.1, "magnesio_mg": 11,
        "fosforo_mg": 180, "potassio_mg": 130, "selenio_ug": 30,
        "vitamina_a_ug": 140, "vitamina_d_ug": 1.8, "vitamina_b2_mg": 0.4,
        "vitamina_b12_ug": 1.5,
    },
}
