"""
Food Pool Auto-Builder — classifica automaticamente 880 alimenti in pool funzionali.

Sostituisce FOOD_POOLS hardcoded in meal_archetypes.py (~100 alimenti curati a mano).
Usa categoria + profilo nutrizionale + keyword exclusion per classificare l'intero catalogo.

v5 — Servability Architecture:
  - Secondo pools (carne, pesce, uova): SOLO pietanze (food_type == "pietanza")
  - Primo pool: pietanze + ingredienti cotti (no crudo/secco)
  - Breakfast dairy: solo yogurt/latte/kefir/ricotta (no formaggi)
  - Breakfast cereal: solo fiocchi/crusca/muesli/fette biscottate (no farine/grani)
  - Dinner bread (carb_light): solo pane vero (no cornflakes/crackers)
  - Fat: solo oli salubri (no strutto/margarina/cocco/palma)
  - Legumi secondo: threshold alzato (p>=5 pietanze, p>=8 ingredienti)

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
# Keyword exclusion lists
# ---------------------------------------------------------------------------

_POULTRY_KW = ["pollo", "tacchino", "gallina"]

# Dolci/snack esclusi da cereal e carb_light
_SWEET_EXCL = [
    "torta", "biscotti", "biscotto", "croissant", "brioche", "cornett",
    "waffle", "muffin", "crumble", "colomba", "panettone", "pandoro",
]

# Dairy exclusion (generale)
_DAIRY_EXCL = [
    "gelato", "burro", "mascarpone", "condensato", "polvere", "panna",
    "cacao",
]

# Breakfast dairy: SOLO yogurt, latte, kefir, ricotta, fiocchi di latte
_BREAKFAST_DAIRY_KW = [
    "yogurt", "latte", "kefir", "quark", "fiocchi di latte", "ricotta",
]

# Breakfast cereal: SOLO fiocchi, crusca, muesli, granola, fette biscottate
_CEREAL_KW = [
    "fiocchi", "crusca", "muesli", "granola", "fette biscottat", "cereali",
]
# Cereal exclusion: farine, germe, grani crudi
_CEREAL_EXCL = [
    "farina", "germe", "crudo", "secca", "secco", "semola", "amido",
]

# Dinner bread (carb_light): SOLO pane vero
_BREAD_KW = ["pane ", "pane,", "tortilla", "piadina", "chapati"]
# Bread exclusion: snack non-pane
_BREAD_EXCL = [
    "cornflakes", "fiocchi", "crackers", "grissini", "taralli",
    "focaccia", "schiacciata",
]

# Fat exclusion: grassi insalubri
_FAT_EXCL = [
    "strutto", "margarin", "cocco", "palma", "burro", "lardo",
    "maionese",
]


def build_food_pools(session: Session) -> dict[str, list[Food]]:
    """Auto-classifica tutti gli alimenti attivi in pool funzionali.

    v5: Servability Architecture — secondo/primo pools SOLO pietanze servibili.
    Meal-context pools per colazione/cena coerenti.

    Ritorna: {ruolo: [Food, ...]} con oggetti ORM completi.
    Pool ordinati per micro_count decrescente (alimenti nutrient-dense prima).
    """
    foods = session.exec(select(Food).where(Food.is_active == True)).all()

    pools: dict[str, list[Food]] = {
        "dairy": [],
        "dairy_breakfast": [],
        "dairy_light": [],
        "dairy_aged": [],
        "dairy_plant": [],
        "cereal": [],
        "carb_light": [],
        "fruit": [],
        "nuts": [],
        "fat": [],
        "condimento": [],
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

        # ── dairy (cat 12: Latte, yogurt e formaggi freschi) ──
        if cat == 12 and ft in ("ingrediente", "bevanda"):
            if p >= 3 and g <= 25 and kcal <= 300:
                if not _matches_any(nome, _DAIRY_EXCL):
                    pools["dairy"].append(food)

                    # dairy_breakfast: SOLO yogurt/latte/kefir/ricotta
                    if _matches_any(nome, _BREAKFAST_DAIRY_KW):
                        pools["dairy_breakfast"].append(food)

                    # dairy_light subset (spuntino)
                    if g <= 10 and kcal <= 150 and not _matches_any(nome, ["formaggio"]):
                        pools["dairy_light"].append(food)

            # dairy_aged: formaggi stagionati (porzione piccola, condimento)
            elif p >= 15 and kcal <= 400:
                if not _matches_any(nome, _DAIRY_EXCL):
                    pools["dairy_aged"].append(food)

        # ── cereal (cat 1: Cereali e derivati, cat 3: Pane e prodotti da forno) ──
        # v5: SOLO fiocchi/crusca/muesli/granola/fette biscottate per colazione
        if cat in (1, 3) and ft in ("ingrediente", "pietanza"):
            if c >= 35 and kcal >= 180:
                if not _matches_any(nome, _SWEET_EXCL):
                    if _matches_any(nome, _CEREAL_KW) and not _matches_any(nome, _CEREAL_EXCL):
                        pools["cereal"].append(food)

        # ── carb_light (cena bread) ──
        # v5: SOLO pane vero per cena (no cornflakes, crackers, grissini)
        if cat == 3 and ft in ("ingrediente", "pietanza"):
            if c >= 35 and g <= 15:
                if not _matches_any(nome, _SWEET_EXCL + _BREAD_EXCL):
                    if _matches_any(nome, _BREAD_KW):
                        pools["carb_light"].append(food)

        # ── fruit (cat 6: Frutta fresca) ──
        if cat == 6 and ft == "ingrediente":
            if kcal <= 120:
                excl = ["candita", "sciroppat", "disidratat", "secch",
                        "essiccata", "chip"]
                if not _matches_any(nome, excl):
                    pools["fruit"].append(food)

        # ── nuts (cat 7: Frutta secca e semi) ──
        if cat == 7 and ft == "ingrediente":
            if g >= 10 and p >= 5:
                pools["nuts"].append(food)

        # ── fat (cat 13: Oli e condimenti — SOLO oli salubri) ──
        # v5: escludi strutto, margarina, olio di cocco/palma, burro, lardo
        if cat == 13 and ft == "ingrediente":
            if g >= 50:
                if not _matches_any(nome, _FAT_EXCL):
                    pools["fat"].append(food)

        # ── condimento (cat 13: Salse e condimenti a basso contenuto calorico) ──
        if cat == 13 and ft in ("ingrediente", "pietanza"):
            if g < 50 and kcal <= 250:
                excl = ["maionese", "burro", "strutto"]
                if not _matches_any(nome, excl):
                    pools["condimento"].append(food)

        # ── primo_piatto (cat 2: Pasta, riso e cereali cotti) ──
        # v5: SOLO pietanze O ingredienti cotti (no crudo/secco)
        if cat == 2:
            if ft == "pietanza":
                if c >= 10 and kcal >= 50:
                    pools["primo_piatto"].append(food)
            elif ft == "ingrediente":
                if c >= 10 and kcal >= 50:
                    if _matches_any(nome, ["cott"]) and not _matches_any(nome, ["secc", "crud"]):
                        pools["primo_piatto"].append(food)

        # ── contorno (cat 5: Verdure e ortaggi) ──
        if cat == 5 and ft in ("ingrediente", "pietanza"):
            if kcal <= 150:
                excl = ["fritte", "chips"]
                if not _matches_any(nome, excl):
                    pools["contorno"].append(food)

        # ── secondo_fish (cat 10: Prodotti ittici) — SOLO pietanze ──
        if cat == 10 and ft == "pietanza":
            if p >= 10:
                excl = ["bastoncin", "surimi", "olio di fegato"]
                if not _matches_any(nome, excl):
                    pools["secondo_fish"].append(food)

        # ── secondo_poultry / secondo_red_meat (cat 8: Carne) — SOLO pietanze ──
        if cat == 8 and ft == "pietanza":
            if p >= 12:
                excl = ["wurstel"]
                if not _matches_any(nome, excl):
                    if _matches_any(nome, _POULTRY_KW):
                        pools["secondo_poultry"].append(food)
                    else:
                        pools["secondo_red_meat"].append(food)

        # ── secondo_egg (cat 11: Uova) — SOLO pietanze ──
        if cat == 11 and ft == "pietanza":
            pools["secondo_egg"].append(food)

        # ── secondo_legume (cat 4: Legumi) ──
        # v5: threshold alzato — pietanze p>=5, ingredienti p>=8
        if cat == 4:
            excl = ["fagiolini"]
            if not _matches_any(nome, excl):
                if ft == "pietanza" and p >= 5:
                    pools["secondo_legume"].append(food)
                elif ft == "ingrediente" and p >= 8:
                    pools["secondo_legume"].append(food)

        # ── secondo_deli (cat 9: Salumi e affettati) ──
        if cat == 9 and ft in ("ingrediente", "pietanza"):
            if p >= 8:
                excl = ["pancetta", "lardo", "strutto", "guanciale"]
                if not _matches_any(nome, excl):
                    pools["secondo_deli"].append(food)

        # ── dairy_plant (cat 15: Bevande — latti vegetali per colazione) ──
        if cat == 15 and ft in ("ingrediente", "bevanda"):
            if _matches_any(nome, ["latte di ", "latte d'", "latte vegetale"]):
                if kcal <= 80:
                    pools["dairy_plant"].append(food)

    # Ordina ogni pool: micro_count decrescente (nutrient-dense prima)
    for role in pools:
        pools[role].sort(key=lambda f: _micro_count(f), reverse=True)

    # Rimuovi pool vuoti
    return {k: v for k, v in pools.items() if v}
