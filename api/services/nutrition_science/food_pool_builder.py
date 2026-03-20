"""
Food Pool Auto-Builder — classifica automaticamente 880 alimenti in pool funzionali.

Sostituisce FOOD_POOLS hardcoded in meal_archetypes.py (~100 alimenti curati a mano).
Usa categoria + profilo nutrizionale + keyword exclusion per classificare l'intero catalogo.

Ordinamento interno: alimenti con piu' micronutrienti non-null prima (preferiti dal selector).
"""

from sqlmodel import Session, select

from api.models.nutrition import Food


# ---------------------------------------------------------------------------
# Campi micro usati per ordinamento (alimenti "ricchi" prima)
# ---------------------------------------------------------------------------
_MICRO_FIELDS = [
    "calcio_mg", "ferro_mg", "zinco_mg", "magnesio_mg", "fosforo_mg",
    "potassio_mg", "selenio_ug", "sodio_mg", "fibra_g",
    "vitamina_a_ug", "vitamina_d_ug", "vitamina_e_mg", "vitamina_c_mg",
    "vitamina_b1_mg", "vitamina_b2_mg", "vitamina_b3_mg", "vitamina_b6_mg",
    "vitamina_b9_ug", "vitamina_b12_ug",
]


def _micro_count(food: Food) -> int:
    """Conta quanti micronutrienti non-null ha l'alimento."""
    return sum(1 for f in _MICRO_FIELDS if getattr(food, f, None) is not None)


def _nome_lower(food: Food) -> str:
    return food.nome.lower()


def _matches_any(nome: str, keywords: list[str]) -> bool:
    """True se il nome contiene almeno una keyword."""
    return any(kw in nome for kw in keywords)


# ---------------------------------------------------------------------------
# Regole di classificazione: (ruolo, cat_ids, food_types, macro_filter, exclude_kw)
# ---------------------------------------------------------------------------

_POULTRY_KW = ["pollo", "tacchino", "gallina"]


def build_food_pools(session: Session) -> dict[str, list[Food]]:
    """Auto-classifica tutti gli alimenti attivi in pool funzionali.

    Ritorna: {ruolo: [Food, ...]} con oggetti ORM completi.
    Pool ordinati per micro_count decrescente (alimenti nutrient-dense prima).
    """
    foods = session.exec(select(Food).where(Food.is_active == True)).all()

    pools: dict[str, list[Food]] = {
        "dairy": [],
        "dairy_light": [],
        "cereal": [],
        "carb_light": [],
        "fruit": [],
        "nuts": [],
        "fat": [],
        "primo_piatto": [],
        "contorno": [],
        "secondo_fish": [],
        "secondo_poultry": [],
        "secondo_red_meat": [],
        "secondo_egg": [],
        "secondo_legume": [],
        "secondo_deli": [],
    }

    for food in foods:
        cat = food.categoria_id
        ft = food.food_type
        nome = _nome_lower(food)
        p = food.proteine_g
        c = food.carboidrati_g
        g = food.grassi_g
        kcal = food.energia_kcal

        # ── dairy (cat 12: Latte, yogurt e formaggi) ──
        if cat == 12 and ft in ("ingrediente", "bevanda"):
            if p >= 3 and g <= 20 and kcal <= 200:
                excl = ["gelato", "burro", "mascarpone"]
                if not _matches_any(nome, excl):
                    pools["dairy"].append(food)
                    # dairy_light subset
                    if g <= 8 and kcal <= 120 and not _matches_any(nome, ["formaggio"]):
                        pools["dairy_light"].append(food)

        # ── cereal (cat 1: Cereali e derivati, cat 3: Pane e prodotti da forno) ──
        if cat in (1, 3) and ft == "ingrediente":
            if c >= 40 and kcal >= 200:
                excl = ["torta", "biscott", "croissant", "brioche"]
                if not _matches_any(nome, excl):
                    pools["cereal"].append(food)

        # ── carb_light (cat 3: Pane e prodotti da forno) ──
        if cat == 3 and ft == "ingrediente":
            if c >= 40 and g <= 10:
                excl = ["torta", "biscott", "croissant"]
                if not _matches_any(nome, excl):
                    pools["carb_light"].append(food)

        # ── fruit (cat 6: Frutta fresca) ──
        if cat == 6 and ft == "ingrediente":
            if kcal <= 100:
                excl = ["candita", "sciroppat", "disidratat"]
                if not _matches_any(nome, excl):
                    pools["fruit"].append(food)

        # ── nuts (cat 7: Frutta secca e semi) ──
        if cat == 7 and ft == "ingrediente":
            if g >= 10 and p >= 5:
                pools["nuts"].append(food)

        # ── fat (cat 13: Oli e condimenti) ──
        if cat == 13 and ft == "ingrediente":
            if g >= 50:
                excl = ["maionese", "burro"]
                if not _matches_any(nome, excl):
                    pools["fat"].append(food)

        # ── primo_piatto (cat 2: Pasta, riso e cereali cotti) ──
        if cat == 2 and ft == "pietanza":
            if c >= 15 and kcal >= 80:
                pools["primo_piatto"].append(food)

        # ── contorno (cat 5: Verdure e ortaggi) ──
        if cat == 5 and ft in ("ingrediente", "pietanza"):
            if kcal <= 150:
                excl = ["fritte", "chips"]
                if not _matches_any(nome, excl):
                    pools["contorno"].append(food)

        # ── secondo_fish (cat 10: Prodotti ittici) ──
        if cat == 10 and ft in ("ingrediente", "pietanza"):
            if p >= 10:
                excl = ["bastoncin", "surimi"]
                if not _matches_any(nome, excl):
                    pools["secondo_fish"].append(food)

        # ── secondo_poultry / secondo_red_meat (cat 8: Carne e pollame) ──
        if cat == 8 and ft in ("ingrediente", "pietanza"):
            if p >= 15:
                excl = ["wurstel"]
                if not _matches_any(nome, excl):
                    if _matches_any(nome, _POULTRY_KW):
                        pools["secondo_poultry"].append(food)
                    else:
                        pools["secondo_red_meat"].append(food)

        # ── secondo_egg (cat 11: Uova) ──
        if cat == 11 and ft in ("ingrediente", "pietanza"):
            pools["secondo_egg"].append(food)

        # ── secondo_legume (cat 4: Legumi) ──
        if cat == 4 and ft in ("ingrediente", "pietanza"):
            if p >= 5:
                pools["secondo_legume"].append(food)

        # ── secondo_deli (cat 9: Salumi e affettati) ──
        if cat == 9 and ft == "ingrediente":
            if p >= 10:
                excl = ["pancetta", "lardo", "strutto"]
                if not _matches_any(nome, excl):
                    pools["secondo_deli"].append(food)

    # Ordina ogni pool: micro_count decrescente (nutrient-dense prima)
    for role in pools:
        pools[role].sort(key=lambda f: _micro_count(f), reverse=True)

    # Rimuovi pool vuoti
    return {k: v for k, v in pools.items() if v}
