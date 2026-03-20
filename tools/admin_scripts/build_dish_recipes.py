"""Popola ricette_pietanze per le pietanze esistenti in nutrition.db.

Le ricette sono informative — i valori nutrizionali della pietanza
restano quelli CREA/USDA misurati. La ricetta serve per:
  - UI: mostrare composizione del piatto al trainer
  - Sostituzioni: swap ingredienti mantenendo il profilo nutrizionale
  - Drill-down: analisi per singolo ingrediente

Risoluzione per nome (non ID) = resiliente a rebuild nutrition.db.
Idempotente: skip se pietanza ha gia' ricette.

Usage:
    python -m tools.admin_scripts.build_dish_recipes           # popola
    python -m tools.admin_scripts.build_dish_recipes --verify   # verifica macro
    python -m tools.admin_scripts.build_dish_recipes --dry-run  # anteprima
"""

import argparse
import sys
from pathlib import Path

from sqlmodel import Session, create_engine, select

# Aggiungi root al path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from api.models.nutrition import DishRecipe, Food  # noqa: E402


# ---------------------------------------------------------------------------
# Ricette: pietanza_nome → [(ingrediente_nome, grammi_per_porzione, note)]
#
# I nomi devono corrispondere ESATTAMENTE a Food.nome in nutrition.db.
# quantita_g = grammi ingrediente per 1 porzione standard del piatto.
# ---------------------------------------------------------------------------

RECIPES: dict[str, list[tuple[str, float, str | None]]] = {
    # ═══════════════════════════════════════════════════════════════
    # CAT 2 — Pasta, riso e cereali cotti (nuove ricette)
    # ═══════════════════════════════════════════════════════════════
    "Amaranto, cotto": [
        ("Amaranto, crudo", 50, "peso a crudo per ~150g cotto"),
    ],
    "Grano saraceno, cotto": [
        ("Grano saraceno, crudo", 50, "peso a crudo per ~130g cotto"),
    ],
    "Lasagne fresche, cotte": [
        ("Pasta all'uovo, secca", 100, "sfoglie all'uovo"),
        ("Salsa di pomodoro, passata", 80, "sugo base"),
        ("Parmigiano reggiano", 20, "grattugiato"),
        ("Burro", 10, None),
    ],
    "Miglio, cotto": [
        ("Miglio, crudo", 50, "peso a crudo per ~140g cotto"),
    ],
    "Pasta all'uovo, cotta": [
        ("Pasta all'uovo, secca", 80, "tagliatelle o simili"),
    ],
    "Pasta di farro, cotta": [
        ("Farro, crudo", 80, "peso a crudo"),
    ],
    "Pasta di legumi (ceci/lenticchie), cotta": [
        ("Pasta di lenticchie rosse, secca", 80, "peso a crudo"),
    ],
    "Pasta di riso, cotta": [
        ("Farina di riso", 80, "base pasta di riso"),
    ],
    "Pasta gluten-free riso/mais, cotta": [
        ("Farina di riso", 60, "componente principale"),
        ("Farina di mais (maizena)", 20, "componente mais"),
    ],
    "Penne integrali, cotte": [
        ("Pasta integrale, secca", 80, "peso a crudo"),
    ],
    "Riso basmati, cotto": [
        ("Riso basmati, crudo", 70, "peso a crudo per ~200g cotto"),
    ],
    "Riso parboiled, cotto": [
        ("Riso parboiled, crudo", 70, "peso a crudo per ~200g cotto"),
    ],
    "Riso venere, cotto": [
        ("Riso venere, crudo", 70, "peso a crudo per ~180g cotto"),
    ],
    "Sorgo, cotto": [
        ("Sorgo, crudo", 50, "peso a crudo per ~130g cotto"),
    ],
    "Spätzle (gnocchetti tirolesi), cotti": [
        ("Frumento tenero, farina 00", 80, "base impasto"),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Latte parzialmente scremato", 30, None),
    ],
    "Teff, cotto": [
        ("Teff, crudo", 50, "peso a crudo per ~130g cotto"),
    ],
    "Trofie, cotte": [
        ("Frumento tenero, farina 00", 80, "semola per trofie"),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 2 — Primi piatti / cereali cotti (originali)
    # ═══════════════════════════════════════════════════════════════
    "Risotto semplice (burro/parmigiano)": [
        ("Riso bianco, crudo", 80, None),
        ("Parmigiano reggiano", 15, "grattugiato"),
        ("Burro", 10, None),
        ("Cipolla", 20, "soffritto"),
    ],
    "Avena, cotta (porridge)": [
        ("Avena, fiocchi", 40, None),
    ],
    "Gnocchi di patate, cotti": [
        ("Patate, crude", 200, "lessate e schiacciate"),
        ("Frumento tenero, farina 00", 50, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
    ],
    "Orzo perlato, cotto": [
        ("Orzo perlato, crudo", 70, None),
    ],
    "Granola tostata": [
        ("Avena, fiocchi", 30, "base"),
        ("Miele", 10, None),
        ("Olio di semi di girasole", 5, None),
        ("Mandorle", 10, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 3 — Pane e prodotti da forno
    # ═══════════════════════════════════════════════════════════════
    "Pane di frumento, bianco": [
        ("Frumento tenero, farina 00", 100, "farina bianca"),
    ],
    "Pane integrale": [
        ("Frumento tenero, farina integrale", 100, "farina integrale"),
    ],
    "Pane di segale": [
        ("Segale, farina integrale", 100, "farina di segale"),
    ],
    "Pane ciabatta": [
        ("Frumento tenero, farina 0", 100, "impasto idratato"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Pane di Altamura (semola)": [
        ("Frumento duro, semola", 100, "semola rimacinata"),
    ],
    "Pane tipo pugliese (semola rimacinata)": [
        ("Frumento duro, semola", 100, "semola rimacinata"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Pane al latte": [
        ("Frumento tenero, farina 00", 80, None),
        ("Latte intero, fresco", 30, None),
        ("Burro", 5, None),
    ],
    "Pane all'olio": [
        ("Frumento tenero, farina 00", 100, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Pane con noci": [
        ("Frumento tenero, farina integrale", 80, None),
        ("Noci", 20, "tritate grossolanamente"),
    ],
    "Pane di kamut, biologico": [
        ("Kamut (grano khorasan), crudo", 100, "farina di kamut"),
    ],
    "Pane di mais senza glutine": [
        ("Mais, farina gialla", 80, None),
        ("Farina di riso", 20, "addensante"),
        ("Olio di semi di girasole", 5, None),
    ],
    "Pane di patate": [
        ("Frumento tenero, farina 00", 70, None),
        ("Patate, crude", 50, "lessate e schiacciate"),
    ],
    "Pane senza glutine": [
        ("Farina di riso", 70, "base senza glutine"),
        ("Farina di mais (maizena)", 30, None),
        ("Olio di semi di girasole", 5, None),
    ],
    "Pane in cassetta (toast)": [
        ("Frumento tenero, farina 00", 80, None),
        ("Burro", 5, None),
        ("Latte parzialmente scremato", 20, None),
    ],
    "Pane azzimo (matza)": [
        ("Frumento tenero, farina 00", 100, "solo acqua, no lievito"),
    ],
    "Pane azzimo integrale": [
        ("Frumento tenero, farina integrale", 100, "solo acqua, no lievito"),
    ],
    "Pancarr\xe9 di segale": [
        ("Segale, farina integrale", 80, None),
        ("Frumento tenero, farina 00", 20, None),
    ],
    "Panino al sesamo": [
        ("Frumento tenero, farina 00", 80, None),
        ("Semi di sesamo", 5, "copertura"),
    ],
    "Baguette francese": [
        ("Frumento tenero, farina 0", 100, "farina forte"),
    ],
    "Chapati (pane indiano integrale)": [
        ("Frumento tenero, farina integrale", 80, None),
        ("Olio di semi di girasole", 5, None),
    ],
    "Naan indiano": [
        ("Frumento tenero, farina 00", 80, None),
        ("Yogurt intero bianco", 20, None),
        ("Burro", 5, None),
    ],
    "Tortilla di frumento": [
        ("Frumento tenero, farina 00", 80, None),
        ("Olio di semi di girasole", 5, None),
    ],
    "Tortilla di mais": [
        ("Mais, farina gialla", 80, "masa harina"),
    ],
    "Tortilla di farro": [
        ("Farro, crudo", 80, "farina di farro"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Crackers, classici": [
        ("Frumento tenero, farina 00", 80, None),
        ("Olio di semi di girasole", 10, None),
    ],
    "Crackers integrali": [
        ("Frumento tenero, farina integrale", 80, None),
        ("Olio di semi di girasole", 10, None),
    ],
    "Cracker di riso (gallette mini)": [
        ("Farina di riso", 80, "base gallette di riso"),
    ],
    "Gallette di riso": [
        ("Farina di riso", 80, None),
    ],
    "Grissini torinesi": [
        ("Frumento tenero, farina 00", 80, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Taralli pugliesi": [
        ("Frumento tenero, farina 00", 80, None),
        ("Olio di oliva extravergine", 15, None),
    ],
    "Fette biscottate classiche": [
        ("Frumento tenero, farina 00", 80, None),
        ("Burro", 5, None),
        ("Zucchero bianco", 5, None),
    ],
    "Fette biscottate integrali": [
        ("Frumento tenero, farina integrale", 80, None),
        ("Olio di semi di girasole", 5, None),
    ],
    "Fette biscottate senza glutine": [
        ("Farina di riso", 60, None),
        ("Farina di mais (maizena)", 20, None),
        ("Olio di semi di girasole", 5, None),
    ],
    "Fetta biscottata alla frutta": [
        ("Frumento tenero, farina 00", 70, None),
        ("Zucchero bianco", 8, None),
        ("Burro", 5, None),
    ],
    "Cornetto (brioche vuoto)": [
        ("Frumento tenero, farina 00", 70, None),
        ("Burro", 20, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
        ("Zucchero bianco", 10, None),
    ],
    "Schiacciata toscana": [
        ("Frumento tenero, farina 00", 100, None),
        ("Olio di oliva extravergine", 20, None),
    ],
    "Crespelle (cr\xeapes, neutre)": [
        ("Frumento tenero, farina 00", 50, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Latte intero, fresco", 80, None),
        ("Burro", 5, None),
    ],
    "Waffle (neutro base)": [
        ("Frumento tenero, farina 00", 60, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Latte intero, fresco", 60, None),
        ("Burro", 15, None),
        ("Zucchero bianco", 8, None),
    ],
    "Muffin all'avena (senza latticini)": [
        ("Avena, fiocchi", 50, None),
        ("Frumento tenero, farina integrale", 30, None),
        ("Olio di semi di girasole", 20, None),
        ("Miele", 15, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
    ],
    "Crumble di avena (base dolce)": [
        ("Avena, fiocchi", 50, None),
        ("Burro", 20, None),
        ("Zucchero bianco", 15, None),
    ],
    "Biscotti secchi (tipo digestive)": [
        ("Avena, fiocchi", 40, None),
        ("Frumento tenero, farina integrale", 40, None),
        ("Burro", 20, None),
        ("Zucchero bianco", 15, None),
    ],
    "Biscotti frollini classici": [
        ("Frumento tenero, farina 00", 60, None),
        ("Burro", 25, None),
        ("Zucchero bianco", 20, None),
        ("Uovo intero, crudo", 20, "mezzo uovo"),
    ],
    "Biscotto al cocco (tipo Oro Saiwa)": [
        ("Frumento tenero, farina 00", 60, None),
        ("Cocco rap\xe9 essiccato (non zuccherato)", 20, None),
        ("Zucchero bianco", 20, None),
        ("Burro", 15, None),
    ],
    "Fiocchi di mais, cornflakes": [
        ("Mais, farina gialla", 80, "base cereali soffiati"),
    ],
    "Tortino di mais (polenta al forno)": [
        ("Mais, farina gialla", 80, None),
        ("Olio di oliva extravergine", 10, None),
        ("Parmigiano reggiano", 10, "grattugiato"),
    ],
    "Focaccia genovese": [
        ("Frumento tenero, farina 00", 100, None),
        ("Olio di oliva extravergine", 15, None),
    ],
    "Piadina romagnola": [
        ("Frumento tenero, farina 00", 80, None),
        ("Strutto di maiale", 15, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 4 — Legumi (pietanze)
    # ═══════════════════════════════════════════════════════════════
    "Ceci, secchi tostati (snack)": [
        ("Ceci, secchi (crudi)", 80, "tostati in forno"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Passata di ceci (hummus base ridotta)": [
        ("Ceci, cotti", 100, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Hummus (crema di ceci)": [
        ("Ceci, cotti", 120, None),
        ("Tahini (pasta di sesamo)", 15, None),
        ("Olio di oliva extravergine", 10, None),
        ("Aglio, fresco", 3, "1 spicchio"),
    ],
    "Tempeh (soia fermentata)": [
        ("Soia, semi cotti", 80, "fermentati"),
    ],
    "Tofu, compatto (firm)": [
        ("Soia, semi cotti", 100, "cagliati"),
    ],
    "Tofu, morbido (silken)": [
        ("Soia, semi cotti", 80, "cagliati, piu' acqua"),
    ],
    "Zuppa di lenticchie (piatto pronto)": [
        ("Lenticchie, secche (crude)", 50, None),
        ("Carote", 30, None),
        ("Sedano", 20, None),
        ("Cipolla", 30, None),
        ("Olio di oliva extravergine", 5, None),
        ("Salsa di pomodoro, passata", 40, None),
    ],
    "Ceci al curry (piatto pronto)": [
        ("Ceci, cotti", 150, None),
        ("Cipolla", 30, None),
        ("Salsa di pomodoro, passata", 50, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Zuppa di fagioli neri": [
        ("Fagioli neri, cotti", 120, None),
        ("Cipolla", 30, None),
        ("Aglio, fresco", 3, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Minestrone con legumi (piatto pronto)": [
        ("Fagioli borlotti, cotti", 50, None),
        ("Carote", 30, None),
        ("Zucchine", 40, None),
        ("Sedano", 20, None),
        ("Patate, crude", 40, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Fagioli al pomodoro (in scatola)": [
        ("Fagioli borlotti, cotti", 120, None),
        ("Salsa di pomodoro, passata", 60, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 8 — Carne (secondi)
    # ═══════════════════════════════════════════════════════════════
    "Petto di pollo, cotto in padella": [
        ("Petto di pollo, crudo", 150, "1 petto medio"),
        ("Olio di oliva extravergine", 10, "1 cucchiaio"),
    ],
    "Petto di pollo, affettato cotto": [
        ("Petto di pollo, crudo", 150, "1 petto medio"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Pollo, petto marinato alla griglia": [
        ("Petto di pollo, crudo", 160, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Pollo, stinco cotto": [
        ("Cosce di pollo, crude", 180, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Tacchino, macinato cotto": [
        ("Petto di tacchino, macinato", 150, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Hamburger di pollo (grigliato)": [
        ("Petto di pollo, crudo", 130, "macinato"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Pollo tikka masala (piatto indiano)": [
        ("Petto di pollo, crudo", 150, "a cubetti"),
        ("Yogurt intero bianco", 30, "marinatura"),
        ("Olio di oliva extravergine", 10, None),
        ("Cipolla", 30, None),
        ("Salsa di pomodoro, passata", 50, None),
    ],
    "Hamburger di manzo (80% magro)": [
        ("Manzo macinato magro 5%, crudo", 150, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Manzo macinato, cotto": [
        ("Manzo macinato magro 5%, crudo", 150, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Manzo, roast beef cotto": [
        ("Manzo, fesa, cruda", 200, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Manzo, stinco cotto in umido": [
        ("Manzo, fesa, cruda", 200, "stinco"),
        ("Cipolla", 30, None),
        ("Carote", 30, None),
        ("Sedano", 20, None),
        ("Olio di oliva extravergine", 10, None),
        ("Salsa di pomodoro, passata", 50, None),
    ],
    "Polpette di carne al sugo (cotte)": [
        ("Manzo macinato magro 5%, crudo", 120, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
        ("Parmigiano reggiano", 10, "grattugiato"),
        ("Salsa di pomodoro, passata", 80, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Scaloppina di vitello al marsala": [
        ("Vitello, scaloppina cruda", 150, "fettine"),
        ("Frumento tenero, farina 00", 10, "infarinatura"),
        ("Burro", 10, None),
    ],
    "Vitello, fettina al limone (cotta)": [
        ("Vitello, scaloppina cruda", 150, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Vitello, fegato cotto in padella": [
        ("Fegato di vitello, crudo", 150, None),
        ("Olio di oliva extravergine", 10, None),
        ("Cipolla", 30, None),
    ],
    "Maiale, arrosto al forno cotto": [
        ("Maiale, lonza cruda", 200, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Maiale, costolette cotte": [
        ("Maiale, lonza cruda", 180, "costolette"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Agnello, coscio cotto al forno": [
        ("Agnello, coscia cruda", 200, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Agnello, macinato cotto": [
        ("Agnello, macinato crudo", 150, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Anatra, coscia cotta": [
        ("Anatra, petto crudo (senza pelle)", 180, "coscia"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Petto di pollo, cotto al forno": [
        ("Petto di pollo, crudo", 150, None),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Petto di tacchino, cotto": [
        ("Petto di tacchino, crudo", 150, None),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Pollo intero, arrosto (senza pelle)": [
        ("Cosce di pollo, crude", 200, "intero arrosto"),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Coscia di pollo, cotta": [
        ("Cosce di pollo, crude", 180, None),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Coniglio, cotto": [
        ("Coniglio, cotto", 200, "peso cotto con osso"),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Cervo (capriolo), carne cruda": [
        ("Cervo (capriolo), carne cruda", 180, "filetto o coscia"),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Struzzo, filetto cotto": [
        ("Struzzo, filetto crudo", 160, None),
        ("Olio di oliva extravergine", 8, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 9 — Salumi (pietanze)
    # ═══════════════════════════════════════════════════════════════
    "Prosciutto cotto al forno": [
        ("Maiale, lonza cruda", 200, "fesa di maiale"),
    ],
    "Porchetta (arrosto di maiale)": [
        ("Maiale, lonza cruda", 200, "arrotolato con erbe"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Cotechino (prodotto cotto)": [
        ("Maiale, lonza cruda", 120, "carni miste"),
        ("Maiale, spalla cruda", 80, "cotenna e grasso"),
    ],
    "Zampone di Modena IGP (cotto)": [
        ("Maiale, lonza cruda", 120, "impasto di carne"),
        ("Maiale, spalla cruda", 80, "zampone"),
    ],
    "Coppa di testa": [
        ("Maiale, spalla cruda", 150, "teste e carni di scarto"),
    ],
    "Testa in cassetta (headcheese)": [
        ("Maiale, spalla cruda", 150, "gelatina di testa di maiale"),
    ],
    "Petto di pollo arrosto (affettato, packed)": [
        ("Petto di pollo, crudo", 150, "fettine affettate"),
        ("Olio di oliva extravergine", 5, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 10 — Pesce (secondi)
    # ═══════════════════════════════════════════════════════════════
    "Merluzzo, cotto al vapore": [
        ("Merluzzo, filetto crudo", 180, None),
    ],
    "Orata, cotta": [
        ("Orata, cruda", 180, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Spigola (branzino), cotta": [
        ("Branzino, crudo", 180, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Branzino al cartoccio (cotto)": [
        ("Branzino, crudo", 200, None),
        ("Olio di oliva extravergine", 10, None),
        ("Pomodori ciliegino", 50, None),
    ],
    "Tonno fresco, cotto": [
        ("Tonno fresco, crudo", 160, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Salmone teriyaki al forno": [
        ("Salmone atlantico, crudo", 160, None),
        ("Salsa di soia (tamari)", 10, None),
        ("Miele", 5, None),
    ],
    "Sgombro, cotto al forno": [
        ("Sgombro, crudo", 180, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Trota iridea, cotta": [
        ("Trota, cruda", 180, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Calamari, cotti": [
        ("Calamari, crudi", 200, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Gamberoni, cotti": [
        ("Gamberi tigre, crudi", 200, "sgusciati ~120g"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Mazzancolle (gamberi grandi), cotte": [
        ("Gamberi tigre, crudi", 200, "mazzancolle"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Mazzancolle al vapore": [
        ("Gamberi tigre, crudi", 200, "al vapore"),
    ],
    "Polpo, in umido": [
        ("Polpo, crudo", 200, None),
        ("Salsa di pomodoro, passata", 60, None),
        ("Olio di oliva extravergine", 10, None),
        ("Aglio, fresco", 3, None),
    ],
    "Baccal\xe0 alla vicentina (piatto cotto)": [
        ("Merluzzo, filetto crudo", 150, "baccala' ammollato"),
        ("Olio di oliva extravergine", 15, None),
        ("Cipolla", 30, None),
    ],
    "Branzino, cotto": [
        ("Branzino, crudo", 180, None),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Salmone, cotto al forno": [
        ("Salmone atlantico, crudo", 160, None),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Sardine grigliate": [
        ("Sarde, crude", 180, None),
        ("Olio di oliva extravergine", 8, None),
    ],
    "Polpo, cotto": [
        ("Polpo, crudo", 200, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Gamberi, cotti": [
        ("Gamberi tigre, crudi", 180, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Ostriche gratinate al forno": [
        ("Ostrica, cruda", 150, "6-8 ostriche"),
        ("Parmigiano reggiano", 10, "grattugiato"),
        ("Burro", 8, None),
    ],
    "Ceviche di branzino (piatto crudo)": [
        ("Branzino, crudo", 150, "crudo marinato"),
        ("Limone", 30, "succo di limone"),
    ],
    "Scampi fritti (impanati)": [
        ("Gamberi (scampi), crudi", 150, None),
        ("Frumento tenero, farina 00", 30, "impanatura"),
        ("Uovo intero, crudo", 25, "mezzo uovo per impanatura"),
        ("Olio di semi di girasole", 20, "frittura"),
    ],
    "Tonno in scatola all'olio, sgocciolato": [
        ("Tonno in scatola al naturale", 100, "base tonno"),
        ("Olio di oliva extravergine", 10, "in olio"),
    ],
    "Sardine in scatola all'olio, scolate": [
        ("Sardine in scatola al naturale", 100, "base sardine"),
        ("Olio di oliva extravergine", 10, "in olio"),
    ],
    "Sgombro in scatola al naturale": [
        ("Sgombro, crudo", 120, "base sgombro"),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 11 — Uova (pietanze)
    # ═══════════════════════════════════════════════════════════════
    "Frittata base (uovo+latte), cotta": [
        ("Uovo intero, crudo", 100, "2 uova"),
        ("Latte parzialmente scremato", 20, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Frittata proteica (2 uova+albume)": [
        ("Uovo intero, crudo", 100, "2 uova"),
        ("Albume d'uovo, crudo", 60, "2 albumi extra"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Uovo in camicia (poch\u00e9)": [
        ("Uovo intero, crudo", 50, "1 uovo"),
    ],
    "Uovo intero, strapazzato (con latte)": [
        ("Uovo intero, crudo", 100, "2 uova"),
        ("Latte parzialmente scremato", 15, None),
        ("Burro", 5, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 13 — Salse e condimenti (pietanze)
    # ═══════════════════════════════════════════════════════════════
    "Pesto genovese (basilico/olio/parmigiano)": [
        ("Basilico, fresco", 30, None),
        ("Olio di oliva extravergine", 40, None),
        ("Parmigiano reggiano", 20, "grattugiato"),
        ("Pinoli", 15, None),
        ("Aglio, fresco", 3, "1 spicchio"),
    ],
    "Guacamole": [
        ("Avocado, polpa", 150, "1 avocado"),
        ("Cipolla", 20, None),
        ("Pomodori ciliegino", 30, None),
    ],
    "Salsa tzatziki": [
        ("Yogurt greco intero", 150, None),
        ("Cetrioli", 50, "grattugiato"),
        ("Aglio, fresco", 3, None),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Salsa di panna (besciamella)": [
        ("Latte intero, fresco", 100, None),
        ("Burro", 10, None),
        ("Frumento tenero, farina 00", 10, None),
    ],
    "Salsa romesco (pomodoro/mandorle)": [
        ("Pomodori ciliegino", 80, "arrostiti"),
        ("Mandorle", 20, None),
        ("Olio di oliva extravergine", 15, None),
        ("Aglio, fresco", 3, None),
    ],
    "Salsa verde (prezzemolo/acciughe)": [
        ("Prezzemolo, fresco", 30, None),
        ("Acciughe sott'olio, sgocciolate", 10, None),
        ("Olio di oliva extravergine", 30, None),
        ("Aglio, fresco", 3, None),
    ],
    "Salsa chimichurri": [
        ("Prezzemolo, fresco", 40, None),
        ("Olio di oliva extravergine", 30, None),
        ("Aglio, fresco", 5, None),
    ],
    "Salsa aglio, olio e peperoncino (condimento)": [
        ("Olio di oliva extravergine", 40, None),
        ("Aglio, fresco", 10, "3-4 spicchi"),
        ("Peperoncino rosso, fresco", 3, None),
    ],
    "Soffritto di cipolla-sedano-carota (base)": [
        ("Cipolla", 40, None),
        ("Sedano", 30, None),
        ("Carote", 30, None),
        ("Olio di oliva extravergine", 15, None),
    ],
    "Salsa tahini allungata (hummus base)": [
        ("Tahini (pasta di sesamo)", 30, None),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Salsa teriyaki": [
        ("Salsa di soia (tamari)", 40, None),
        ("Miele", 15, None),
    ],
    "Salsa harissa (pasta di peperoncino)": [
        ("Peperoncino rosso, fresco", 50, "rosso"),
        ("Olio di oliva extravergine", 15, None),
        ("Aglio, fresco", 5, None),
    ],
    "Salsa di pomodoro fresco (bruschetta)": [
        ("Pomodori ciliegino", 150, None),
        ("Olio di oliva extravergine", 10, None),
        ("Basilico, fresco", 5, None),
        ("Aglio, fresco", 2, None),
    ],

    # ═══════════════════════════════════════════════════════════════
    # CAT 14 — Dolci e zuccheri
    # ═══════════════════════════════════════════════════════════════
    "Torta di mele (classica)": [
        ("Frumento tenero, farina 00", 120, None),
        ("Zucchero bianco", 80, None),
        ("Uovo intero, crudo", 100, "2 uova"),
        ("Burro", 60, None),
        ("Latte intero, fresco", 50, None),
    ],
    "Torta sponge (pan di spagna)": [
        ("Frumento tenero, farina 00", 100, None),
        ("Zucchero bianco", 100, None),
        ("Uovo intero, crudo", 150, "3 uova"),
    ],
    "Crostata (base frolla + marmellata)": [
        ("Frumento tenero, farina 00", 80, "pasta frolla"),
        ("Burro", 40, None),
        ("Zucchero bianco", 30, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
        ("Marmellata, media", 40, "ripieno"),
    ],
    "Cantucci (biscotti di Prato)": [
        ("Frumento tenero, farina 00", 60, None),
        ("Zucchero bianco", 30, None),
        ("Mandorle", 30, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
    ],
    "Panettone milanese": [
        ("Frumento tenero, farina 00", 70, None),
        ("Burro", 25, None),
        ("Uovo intero, crudo", 30, None),
        ("Zucchero bianco", 20, None),
    ],
    "Pandoro veronese": [
        ("Frumento tenero, farina 00", 70, None),
        ("Burro", 30, None),
        ("Uovo intero, crudo", 30, None),
        ("Zucchero bianco", 20, None),
    ],
    "Colomba pasquale": [
        ("Frumento tenero, farina 00", 70, None),
        ("Burro", 25, None),
        ("Uovo intero, crudo", 30, None),
        ("Zucchero bianco", 20, None),
        ("Mandorle", 10, "glassa"),
    ],
    "Sfogliatella napoletana": [
        ("Frumento duro, semola", 60, "pasta sfoglia"),
        ("Ricotta di vaccino", 40, "ripieno"),
        ("Zucchero bianco", 20, None),
        ("Uovo intero, crudo", 15, "piccola quantita"),
    ],
    "Tiramis\xf9": [
        ("Mascarpone", 80, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Zucchero bianco", 20, None),
    ],
    "Panna cotta": [
        ("Panna fresca (35% grassi)", 100, None),
        ("Zucchero bianco", 15, None),
        ("Latte intero, fresco", 30, None),
    ],
    "Cheesecake (fetta, base biscotto)": [
        ("Biscotti secchi (tipo digestive)", 40, "base"),
        ("Burro", 15, None),
        ("Mascarpone", 80, "crema"),
        ("Zucchero bianco", 25, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
    ],
    "Brownie al cioccolato": [
        ("Cioccolato fondente 70%", 50, None),
        ("Burro", 30, None),
        ("Zucchero bianco", 40, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Frumento tenero, farina 00", 30, None),
    ],
    "Pancakes (base classica)": [
        ("Frumento tenero, farina 00", 60, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Latte intero, fresco", 80, None),
        ("Zucchero bianco", 10, None),
        ("Burro", 10, None),
    ],
    "Wafer alla vaniglia": [
        ("Frumento tenero, farina 00", 50, None),
        ("Zucchero bianco", 20, None),
        ("Burro", 10, None),
        ("Uovo intero, crudo", 15, "piccola quantita"),
    ],
    "Madeleine (pasticcino francese)": [
        ("Frumento tenero, farina 00", 50, None),
        ("Burro", 30, None),
        ("Zucchero bianco", 30, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
    ],
    "Biscotti di avena e cioccolato": [
        ("Avena, fiocchi", 50, None),
        ("Cioccolato al latte", 20, "chips"),
        ("Burro", 20, None),
        ("Zucchero bianco", 20, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
    ],
    "Croissant integrale (whole wheat)": [
        ("Frumento tenero, farina integrale", 60, None),
        ("Burro", 25, None),
        ("Zucchero bianco", 10, None),
        ("Uovo intero, crudo", 20, None),
    ],
    "Crostino dolce con miele e ricotta": [
        ("Pane di frumento, bianco", 40, "fetta tostata"),
        ("Ricotta di vaccino", 30, None),
        ("Miele", 15, None),
    ],
    "Meringa secca": [
        ("Albume d'uovo, crudo", 60, "2 albumi"),
        ("Zucchero bianco", 60, None),
    ],
    "Zabaione (zabaglione)": [
        ("Tuorlo d'uovo, crudo", 30, "2 tuorli"),
        ("Zucchero bianco", 20, None),
    ],
    "Polenta dolce alla bergamasca": [
        ("Mais, farina gialla", 80, None),
        ("Zucchero bianco", 15, None),
        ("Burro", 10, None),
    ],
    "Gelato alla crema (artigianale)": [
        ("Latte intero, fresco", 100, None),
        ("Panna fresca (35% grassi)", 50, None),
        ("Zucchero bianco", 20, None),
        ("Tuorlo d'uovo, crudo", 15, "1 tuorlo"),
    ],
    "Gelato al cioccolato": [
        ("Latte intero, fresco", 100, None),
        ("Panna fresca (35% grassi)", 40, None),
        ("Zucchero bianco", 20, None),
        ("Cacao amaro in polvere", 10, None),
    ],
    "Gelato alla frutta (sorbetto)": [
        ("Fragole, fresche", 120, "frutta a scelta"),
        ("Zucchero bianco", 20, None),
    ],
    "Granita al limone (senza latte)": [
        ("Limone", 50, "succo di limone"),
        ("Zucchero bianco", 20, None),
    ],
    "Semifreddo al caff\xe8": [
        ("Panna fresca (35% grassi)", 80, None),
        ("Zucchero bianco", 20, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
    ],
    "Crema di marroni (crema di castagne)": [
        ("Farina di castagne", 60, "base castagne"),
        ("Zucchero bianco", 30, None),
    ],
    "Nutella (crema nocciole e cacao)": [
        ("Nocciole", 30, "tostato"),
        ("Cioccolato al latte", 40, None),
        ("Zucchero bianco", 20, None),
    ],
    "Marmellata di albicocche": [
        ("Marmellata, media", 30, "albicocche"),
    ],
    "Marmellata di fragole": [
        ("Marmellata, media", 30, "fragole"),
    ],
    "Confettura extra (70% frutta)": [
        ("Marmellata, media", 30, "alta frutta"),
        ("Zucchero bianco", 5, "ridotto"),
    ],
    "Coppetta di gelato (2 palline tipo)": [
        ("Latte intero, fresco", 80, None),
        ("Panna fresca (35% grassi)", 40, None),
        ("Zucchero bianco", 20, None),
    ],
    "Budino di vaniglia (commerciale)": [
        ("Latte intero, fresco", 100, None),
        ("Zucchero bianco", 15, None),
    ],
    "Ciambelle glassate (donuts)": [
        ("Frumento tenero, farina 00", 60, None),
        ("Zucchero bianco", 20, None),
        ("Burro", 15, None),
        ("Uovo intero, crudo", 25, "mezzo uovo"),
        ("Olio di semi di girasole", 15, "frittura"),
    ],
    "Bign\xe8 alla crema": [
        ("Frumento tenero, farina 00", 40, "pasta choux"),
        ("Burro", 20, None),
        ("Uovo intero, crudo", 50, "1 uovo"),
        ("Latte intero, fresco", 30, "crema"),
        ("Zucchero bianco", 15, None),
    ],
    "Cacao amaro in polvere": [
        ("Cacao amaro in polvere", 10, "polvere pura"),
    ],
    "Cioccolato fondente 70%": [
        ("Cioccolato fondente 70%", 30, "tavoletta"),
    ],
    "Cioccolato al latte": [
        ("Cioccolato al latte", 30, "tavoletta"),
    ],
    "Miele": [
        ("Miele", 20, "cucchiaio"),
    ],
    "Zucchero bianco": [
        ("Zucchero bianco", 10, "cucchiaino"),
    ],
    "Zucchero di canna grezzo": [
        ("Zucchero di canna grezzo", 10, "cucchiaino"),
    ],
    "Marmellata, media": [
        ("Marmellata, media", 30, "porzione media"),
    ],

    # ═══════════════════════════════════════════════════════════════
    # BATCH 2 — Pietanze recuperate (ingrediente crudo disponibile)
    # ═══════════════════════════════════════════════════════════════

    # Cat 8 — Carne
    "Ali di pollo, cotte al forno": [
        ("Cosce di pollo, crude", 200, "ali con osso"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Coscia di tacchino, cotta": [
        ("Petto di tacchino, crudo", 250, "coscia con osso"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Pollo, arrosto con pelle": [
        ("Cosce di pollo, crude", 200, "intero con pelle"),
        ("Olio di oliva extravergine", 10, None),
    ],
    "Pollo in scatola (al naturale)": [
        ("Petto di pollo, crudo", 150, "conservato al naturale"),
    ],
    "Coniglio, dorso cotto": [
        ("Coniglio, cotto", 180, "dorso"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Cervo, coscia cotta": [
        ("Cervo (capriolo), carne cruda", 200, "coscia"),
        ("Olio di oliva extravergine", 5, None),
    ],
    "Anatra, petto cotto al forno": [
        ("Anatra, petto crudo (senza pelle)", 180, None),
        ("Olio di oliva extravergine", 5, None),
    ],

    # Cat 10 — Pesce
    "Salmone in scatola (al naturale)": [
        ("Salmone atlantico, crudo", 150, "conservato al naturale"),
    ],
    "Tonno in scatola al naturale (sgocciolato)": [
        ("Tonno fresco, crudo", 150, "conservato al naturale, sgocciolato"),
    ],
    "Vongole (lupini di mare), cotte": [
        ("Gamberi (scampi), crudi", 200, "vongole sgusciate"),
        ("Olio di oliva extravergine", 5, None),
        ("Aglio, fresco", 3, None),
    ],
    "Cozze (mitili), cotte": [
        ("Gamberi (scampi), crudi", 250, "cozze sgusciate"),
        ("Olio di oliva extravergine", 5, None),
    ],

    # Cat 3 — Pane
    "Pane di segale compatto (tipo wasa)": [
        ("Segale, farina integrale", 80, None),
    ],
}


def _resolve_foods(session: Session) -> dict[str, Food]:
    """Carica tutti gli alimenti attivi e crea mappa nome→Food."""
    foods = session.exec(select(Food).where(Food.is_active == True)).all()
    return {f.nome: f for f in foods}


def populate_recipes(
    session: Session,
    *,
    dry_run: bool = False,
    verify: bool = False,
) -> dict[str, str]:
    """Popola DishRecipe da RECIPES dict.

    Returns: {pietanza_nome: status} dove status = "ok", "skipped", "error:..."
    """
    food_map = _resolve_foods(session)
    results: dict[str, str] = {}
    inserted = 0
    skipped = 0
    errors = 0

    for pietanza_nome, ingredienti in RECIPES.items():
        # Trova pietanza
        pietanza = food_map.get(pietanza_nome)
        if not pietanza:
            results[pietanza_nome] = "error: pietanza non trovata in DB"
            errors += 1
            continue

        # Skip se gia' ha ricette
        existing = session.exec(
            select(DishRecipe).where(DishRecipe.pietanza_id == pietanza.id)
        ).first()
        if existing:
            results[pietanza_nome] = "skipped (gia' presente)"
            skipped += 1
            continue

        # Risolvi ingredienti
        recipe_ok = True
        recipe_rows: list[DishRecipe] = []
        for ing_nome, grammi, note in ingredienti:
            ing = food_map.get(ing_nome)
            if not ing:
                results[pietanza_nome] = f"error: ingrediente '{ing_nome}' non trovato"
                errors += 1
                recipe_ok = False
                break
            recipe_rows.append(DishRecipe(
                pietanza_id=pietanza.id,
                ingrediente_id=ing.id,
                quantita_g=grammi,
                note=note,
            ))

        if not recipe_ok:
            continue

        # Verifica macro se richiesto
        if verify:
            _verify_recipe(pietanza, recipe_rows, food_map)

        if dry_run:
            results[pietanza_nome] = f"ok (dry-run, {len(recipe_rows)} ingredienti)"
        else:
            for row in recipe_rows:
                session.add(row)
            results[pietanza_nome] = f"ok ({len(recipe_rows)} ingredienti)"

        inserted += 1

    if not dry_run:
        session.commit()

    print(f"\n{'='*60}")
    print(f"Risultato: {inserted} inserite, {skipped} skipped, {errors} errori")
    print(f"{'='*60}")

    return results


def _verify_recipe(
    pietanza: Food,
    recipe_rows: list[DishRecipe],
    food_map: dict[str, Food],
) -> None:
    """Confronta macro calcolate da ricetta vs valori CREA sulla pietanza."""
    # Inverti mappa per ID lookup
    id_map = {f.id: f for f in food_map.values()}

    total_g = 0.0
    total_kcal = 0.0
    total_prot = 0.0
    total_carb = 0.0
    total_fat = 0.0

    for row in recipe_rows:
        ing = id_map[row.ingrediente_id]
        ratio = row.quantita_g / 100.0
        total_g += row.quantita_g
        total_kcal += ing.energia_kcal * ratio
        total_prot += ing.proteine_g * ratio
        total_carb += ing.carboidrati_g * ratio
        total_fat += ing.grassi_g * ratio

    if total_g <= 0:
        return

    # Normalizza a 100g di piatto finito
    factor = 100.0 / total_g
    calc_kcal = total_kcal * factor
    calc_prot = total_prot * factor
    calc_carb = total_carb * factor
    calc_fat = total_fat * factor

    # Confronta con CREA
    delta_kcal = abs(calc_kcal - pietanza.energia_kcal)
    delta_pct = (delta_kcal / pietanza.energia_kcal * 100) if pietanza.energia_kcal > 0 else 0

    if delta_pct > 20:
        print(
            f"  WARNING {pietanza.nome}: "
            f"CREA={pietanza.energia_kcal:.0f}kcal "
            f"vs calc={calc_kcal:.0f}kcal "
            f"(delta {delta_pct:.0f}%) "
            f"| P: {pietanza.proteine_g:.1f} vs {calc_prot:.1f} "
            f"| C: {pietanza.carboidrati_g:.1f} vs {calc_carb:.1f} "
            f"| G: {pietanza.grassi_g:.1f} vs {calc_fat:.1f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Popola ricette pietanze")
    parser.add_argument("--dry-run", action="store_true", help="Anteprima senza scrivere")
    parser.add_argument("--verify", action="store_true", help="Verifica macro vs CREA")
    args = parser.parse_args()

    db_path = ROOT / "data" / "nutrition.db"
    if not db_path.exists():
        print(f"ERROR: {db_path} non trovato")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as session:
        results = populate_recipes(
            session,
            dry_run=args.dry_run,
            verify=args.verify,
        )

        # Stampa dettagli
        for nome, status in sorted(results.items()):
            icon = "[OK]" if status.startswith("ok") else ("[--]" if "skip" in status else "[!!]")
            print(f"  {icon} {nome}: {status}")


if __name__ == "__main__":
    main()
