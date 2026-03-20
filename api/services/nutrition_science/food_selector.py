"""
Selettore alimenti v3 per il generatore LARN.

v3: Nutrient-Aware Selection — selezione greedy che colma gap micronutrienti.
    Ogni pick aggiorna un accumulatore giornaliero. Top-3 candidati per score,
    poi scelta random per varieta'.

v2: gestisce pietanze composte (primo/secondo piatto) e ingredienti singoli.
    La rotazione proteica settimanale si applica al secondo piatto (CENA).
"""

import random
from dataclasses import dataclass, field
from typing import Optional

from sqlmodel import Session

from api.models.nutrition import Food
from api.services.nutrition_science.meal_archetypes import (
    ARCHETYPES,
    MEAL_ORDER,
    WEEKLY_SECONDO_ROTATION,
)


# ---------------------------------------------------------------------------
# Micronutrient fields used by the accumulator
# ---------------------------------------------------------------------------

_MICRO_FIELDS = [
    "calcio_mg", "ferro_mg", "zinco_mg", "magnesio_mg", "fosforo_mg",
    "potassio_mg", "selenio_ug", "sodio_mg", "fibra_g",
    "vitamina_a_ug", "vitamina_d_ug", "vitamina_e_mg", "vitamina_c_mg",
    "vitamina_b1_mg", "vitamina_b2_mg", "vitamina_b3_mg", "vitamina_b6_mg",
    "vitamina_b9_ug", "vitamina_b12_ug",
]


# ---------------------------------------------------------------------------
# DayNutrientAccumulator — tracks daily running totals vs LARN targets
# ---------------------------------------------------------------------------

@dataclass
class DayNutrientAccumulator:
    """Accumulatore nutrienti giornaliero per selezione gap-filling."""
    totals: dict[str, float] = field(default_factory=lambda: {f: 0.0 for f in _MICRO_FIELDS})
    targets: dict[str, float] = field(default_factory=dict)

    def gaps(self) -> dict[str, float]:
        """deficit_fraction per nutriente: (target - accumulato) / target.
        Valori positivi = carenza, negativi = surplus."""
        result = {}
        for campo, target in self.targets.items():
            if target > 0:
                result[campo] = (target - self.totals.get(campo, 0.0)) / target
        return result

    def add_food(self, food: Food, grammi: float) -> None:
        """Aggiorna totali dopo selezione."""
        ratio = grammi / 100.0
        for campo in _MICRO_FIELDS:
            val = getattr(food, campo, None)
            if val is not None:
                self.totals[campo] = self.totals.get(campo, 0.0) + val * ratio


# ---------------------------------------------------------------------------
# Nutrient-aware scoring
# ---------------------------------------------------------------------------

def _nutrient_score(food: Food, grammi: float, gaps: dict[str, float]) -> float:
    """Score 0-100: quanto un alimento colma i gap micro attuali.

    Per ogni gap positivo (nutriente carente), calcola quanto il food contribuisce
    a colmarlo. Score piu' alto = alimento piu' utile per i deficit correnti.
    """
    if not gaps:
        return 0.0

    ratio = grammi / 100.0
    score = 0.0
    n_gaps = 0

    for campo, deficit_frac in gaps.items():
        if deficit_frac <= 0:
            continue  # nutriente gia' coperto
        n_gaps += 1
        val = getattr(food, campo, None)
        if val is None or val <= 0:
            continue
        contributo = (val * ratio) / (deficit_frac * 100)  # normalized
        # Cap at 1.0 — un singolo alimento non puo' "super-coprire"
        score += min(1.0, contributo) * deficit_frac  # peso proporzionale al gap

    # Normalize to 0-100
    if n_gaps > 0:
        return (score / n_gaps) * 100
    return 0.0


# ---------------------------------------------------------------------------
# Pool resolution (uses auto-builder)
# ---------------------------------------------------------------------------

def resolve_food_pools(session: Session) -> dict[str, list[Food]]:
    """Carica i food pool da nutrition.db via auto-classificazione."""
    from api.services.nutrition_science.food_pool_builder import build_food_pools
    return build_food_pools(session)


# ---------------------------------------------------------------------------
# Pick functions
# ---------------------------------------------------------------------------

def _pick_from_pool(
    pool: list[Food],
    used_today: set[int],
    used_yesterday: set[int],
    rng: random.Random,
    accumulator: Optional[DayNutrientAccumulator] = None,
    grammi: float = 100,
) -> Optional[Food]:
    """Seleziona un alimento dal pool con nutrient-aware scoring.

    3-tier fallback per varieta': no today+yesterday → no today → tutti.
    Se accumulator fornito: top-3 per nutrient_score → rng.choice.
    Altrimenti: rng.choice (backward-compat).
    """
    # 3-tier candidate filtering
    avoid = used_today | used_yesterday
    candidates = [f for f in pool if f.id not in avoid]
    if not candidates:
        candidates = [f for f in pool if f.id not in used_today]
    if not candidates:
        candidates = pool
    if not candidates:
        return None

    # No accumulator → uniform random (backward-compat)
    if accumulator is None:
        return rng.choice(candidates)

    # Nutrient-aware: score all candidates, pick from top-3
    gaps = accumulator.gaps()
    scored = [(f, _nutrient_score(f, grammi, gaps)) for f in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)

    top_n = min(3, len(scored))
    top_candidates = [f for f, _ in scored[:top_n]]
    picked = rng.choice(top_candidates)

    # Update accumulator
    accumulator.add_food(picked, grammi)
    return picked


# ---------------------------------------------------------------------------
# Day builder
# ---------------------------------------------------------------------------

def build_day_selections(
    giorno: int,
    pools: dict[str, list[Food]],
    used_yesterday: set[int],
    rng: random.Random,
    daily_targets: Optional[dict[str, float]] = None,
) -> list[tuple[str, list[tuple[Food, float]]]]:
    """
    Costruisce le selezioni per un giorno completo.

    v3: se daily_targets fornito, usa DayNutrientAccumulator per selezione
    gap-filling che massimizza la copertura micronutrienti LARN.

    Ritorna: [(tipo_pasto, [(Food, grammi), ...]), ...]
    """
    # Pool secondo piatto per oggi (da rotazione settimanale)
    secondo_pool_name = WEEKLY_SECONDO_ROTATION[giorno - 1]

    # Create accumulator if targets provided
    accumulator = None
    if daily_targets:
        accumulator = DayNutrientAccumulator(targets=daily_targets)

    used_today: set[int] = set()
    day_meals: list[tuple[str, list[tuple[Food, float]]]] = []

    for tipo_pasto in MEAL_ORDER:
        arch = ARCHETYPES.get(tipo_pasto)
        if not arch:
            continue

        meal_foods: list[tuple[Food, float]] = []

        for slot in arch.slots:
            food: Optional[Food] = None

            if slot.ruolo == "secondo_piatto":
                # Secondo piatto: usa il pool proteico del giorno
                pool = pools.get(secondo_pool_name, [])
            else:
                # Tutti gli altri slot: usa il pool del ruolo
                pool = pools.get(slot.ruolo, [])

            food = _pick_from_pool(
                pool, used_today, used_yesterday, rng,
                accumulator=accumulator,
                grammi=slot.grammi,
            )

            if food:
                meal_foods.append((food, slot.grammi))
                used_today.add(food.id)
                # If no accumulator, add_food was not called in _pick_from_pool
                # (accumulator handles it internally when present)
            elif slot.obbligatorio:
                pass  # skip silenzioso se pool vuoto

        if meal_foods:
            day_meals.append((tipo_pasto, meal_foods))

    return day_meals
