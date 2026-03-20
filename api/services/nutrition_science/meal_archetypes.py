"""
Archetipi pasto e pool alimentari per il generatore LARN v2.

Architettura dish-based: PRANZO e CENA usano pietanze composte,
COLAZIONE e spuntini usano ingredienti singoli.

Pattern alimentari italiani:
  - PRANZO: primo piatto (pietanza) + contorno + olio
  - CENA: secondo piatto (pietanza, protein-rotated) + contorno + pane + olio
  - COLAZIONE: yogurt/latte + cereali + frutta + frutta secca
  - SPUNTINI: frutta, yogurt, frutta secca

Porzioni default allineate a LARN 2014:
  - Primo piatto: ~200g (peso finito, include condimento)
  - Secondo piatto: ~160g (peso finito, include condimento)
  - Contorno: 200g | Pane: 50g | Frutta: 150g | Olio: 10g
  - Yogurt/latte: 125g | Frutta secca: 30g

Frequenze allineate a CREA 2018 Direttive 1-13.
"""

from dataclasses import dataclass, field


@dataclass
class MealSlot:
    """Slot funzionale dentro un pasto."""
    ruolo: str       # es. "primo_piatto", "secondo_poultry", "vegetable"
    grammi: float    # porzione default
    obbligatorio: bool = True


@dataclass
class MealArchetype:
    """Struttura di un tipo pasto."""
    tipo_pasto: str
    slots: list[MealSlot] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Archetipi pasto (struttura standard italiana v2 — dish-based)
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, MealArchetype] = {
    "COLAZIONE": MealArchetype(
        tipo_pasto="COLAZIONE",
        slots=[
            MealSlot("dairy", 125),           # yogurt/latte (LARN: 125g)
            MealSlot("cereal", 30),            # fiocchi/fette bisc. (LARN: 30g)
            MealSlot("fruit", 150),            # frutta fresca (LARN: 150g)
            MealSlot("nuts", 30, obbligatorio=False),  # frutta secca (LARN: 30g)
        ],
    ),
    "SPUNTINO_MATTINA": MealArchetype(
        tipo_pasto="SPUNTINO_MATTINA",
        slots=[
            MealSlot("fruit", 150),            # frutta fresca (LARN: 150g)
        ],
    ),
    "PRANZO": MealArchetype(
        tipo_pasto="PRANZO",
        slots=[
            # Primo piatto pietanza (peso finito: pasta cotta + sugo + condimento)
            MealSlot("primo_piatto", 200),
            # Contorno: pietanza composta o verdura cruda
            MealSlot("contorno", 200),
            # Olio extra per il contorno (se contorno non composto)
            MealSlot("fat", 5),
        ],
    ),
    "SPUNTINO_POMERIGGIO": MealArchetype(
        tipo_pasto="SPUNTINO_POMERIGGIO",
        slots=[
            MealSlot("dairy_light", 125),      # yogurt (LARN: 125g)
            MealSlot("nuts", 30, obbligatorio=False),  # frutta secca (LARN: 30g)
        ],
    ),
    "CENA": MealArchetype(
        tipo_pasto="CENA",
        slots=[
            # Secondo piatto pietanza (proteina-rotated settimanalmente)
            MealSlot("secondo_piatto", 160),
            # Contorno
            MealSlot("contorno", 200),
            # Pane
            MealSlot("carb_light", 50),        # pane (LARN: 50g)
            # Olio extra
            MealSlot("fat", 5),
        ],
    ),
}

# Ordine pasti nella giornata
MEAL_ORDER = ["COLAZIONE", "SPUNTINO_MATTINA", "PRANZO", "SPUNTINO_POMERIGGIO", "CENA"]

# ---------------------------------------------------------------------------
# Rotazione settimanale proteine (Lun-Dom)
#
# Allineata a CREA 2018 Dir. 9:
#   Pesce 2-3x, Carne bianca 1-3x, Legumi 2-4x, Uova 2-4x,
#   Carne rossa max 1-2x, Affettati max 1x.
#
# Il primo piatto a PRANZO ha proteine integrate (pasta e fagioli,
# pasta con tonno, ecc.). La rotazione proteica si applica al
# SECONDO piatto a CENA.
#
# Totale cena: pesce 2x, pollo 1x, legumi 3x, uova 2x = 7 cene
# + primi pranzo con proteine (legumi 3x nel pranzo = dentro range CREA)
# ---------------------------------------------------------------------------

# Secondo piatto per CENA di ogni giorno 1-7
#
# Allineato a CREA 2018 Dir. 9 sub-frequenze:
#   Pesce 2-3x, Pollo 1-3x, Legumi 2-4x, Uova 2-4x,
#   Carne rossa max 1-2x, Affettati max 1x.
#
# Totale: pesce 2x, pollo 1x, legumi 3x, uova 2x = 7 cene
# Allineato a DIETA_DONNA_ATTIVA in build_nutrition.py
WEEKLY_SECONDO_ROTATION: list[str] = [
    "secondo_fish",        # Lun: merluzzo (pesce magro)
    "secondo_egg",         # Mar: uova
    "secondo_legume",      # Mer: lenticchie
    "secondo_poultry",     # Gio: pollo
    "secondo_fish",        # Ven: salmone (omega-3)
    "secondo_legume",      # Sab: ceci
    "secondo_egg",         # Dom: uova
]

# Mapping secondo_* → ruolo proteico per il frequency_validator
SECONDO_TO_PROTEIN_ROLE: dict[str, str] = {
    "secondo_poultry": "protein_poultry",
    "secondo_fish": "protein_fish",
    "secondo_legume": "protein_legume",
    "secondo_egg": "protein_egg",
    "secondo_red_meat": "protein_red_meat",
    "secondo_deli": "protein_deli",
}
