"""
Archetipi pasto e pool alimentari per il generatore LARN v5.

v5 — Servability Architecture:
  - PRANZO: primo piatto + SECONDO piatto (rotazione) + contorno + olio
  - CENA: secondo piatto (rotazione separata) + contorno + pane + olio
  - COLAZIONE: dairy_breakfast (yogurt/latte) + cereali veri + frutta + noci
  - SPUNTINI: frutta, yogurt, frutta secca
  - 14 slot proteici settimanali (7 pranzi + 7 cene) con rotazione separata

Pattern alimentari italiani:
  - PRANZO: primo + secondo + contorno + olio
  - CENA: secondo (protein-rotated) + contorno + pane + olio
  - COLAZIONE: yogurt/latte + cereali + frutta + frutta secca
  - SPUNTINI: frutta, yogurt, frutta secca

Porzioni default allineate a LARN 2014:
  - Primo piatto: ~200g (peso finito, include condimento)
  - Secondo piatto: ~130-160g (peso finito, include condimento)
  - Contorno: 200g | Pane: 50g | Frutta: 150g | Olio: 5-10g
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
# Archetipi pasto (struttura standard italiana v5 — Servability Architecture)
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, MealArchetype] = {
    "COLAZIONE": MealArchetype(
        tipo_pasto="COLAZIONE",
        slots=[
            MealSlot("dairy_breakfast", 125),  # yogurt/latte (LARN: 125g)
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
            # Secondo piatto (protein-rotated, porzione ridotta vs cena)
            MealSlot("secondo_piatto", 130),
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
# Rotazione settimanale proteine — PRANZO (Lun-Dom)
#
# v5: 14 slot proteici (7 pranzi + 7 cene) con rotazioni separate.
# Allineata a CREA 2018 Dir. 9:
#   Pesce 2-3x, Carne bianca 1-3x, Legumi 2-4x, Uova 2-4x,
#   Carne rossa max 1-2x, Affettati max 1x.
#
# Totale settimana (pranzo + cena):
#   Pesce 3x, Pollo 3x, Legumi 4x, Uova 2x,
#   Carne rossa 1x, Affettati 1x → compliant CREA 2018
# ---------------------------------------------------------------------------

WEEKLY_PRANZO_ROTATION: list[str] = [
    "secondo_legume",      # Lun pranzo: legumi
    "secondo_poultry",     # Mar pranzo: pollo
    "secondo_fish",        # Mer pranzo: pesce
    "secondo_legume",      # Gio pranzo: legumi
    "secondo_red_meat",    # Ven pranzo: carne rossa (1x/sett)
    "secondo_poultry",     # Sab pranzo: pollo
    "secondo_deli",        # Dom pranzo: affettati (1x/sett)
]

# ---------------------------------------------------------------------------
# Rotazione settimanale proteine — CENA (Lun-Dom)
# ---------------------------------------------------------------------------

WEEKLY_CENA_ROTATION: list[str] = [
    "secondo_fish",        # Lun cena: pesce
    "secondo_egg",         # Mar cena: uova
    "secondo_poultry",     # Mer cena: pollo
    "secondo_legume",      # Gio cena: legumi
    "secondo_fish",        # Ven cena: pesce
    "secondo_egg",         # Sab cena: uova
    "secondo_legume",      # Dom cena: legumi
]

# Backward-compat: alias per codice che importa la vecchia rotazione singola
WEEKLY_SECONDO_ROTATION = WEEKLY_CENA_ROTATION

# Mapping secondo_* → ruolo proteico per il frequency_validator
SECONDO_TO_PROTEIN_ROLE: dict[str, str] = {
    "secondo_poultry": "protein_poultry",
    "secondo_fish": "protein_fish",
    "secondo_legume": "protein_legume",
    "secondo_egg": "protein_egg",
    "secondo_red_meat": "protein_red_meat",
    "secondo_deli": "protein_deli",
}
