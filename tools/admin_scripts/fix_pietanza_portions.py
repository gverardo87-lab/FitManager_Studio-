"""Fix massivo porzioni pietanze: rimuovi tutte, inserisci LARN-correct.

Nei software professionali (MetaDieta, Dietosystem) la porzione standard
e' il peso del PIATTO FINITO, non la somma degli ingredienti crudi.

Fonte: SINU, Standard Quantitativi delle Porzioni, LARN IV Revisione 2014.

Usage:
    python -m tools.admin_scripts.fix_pietanza_portions           # esegui
    python -m tools.admin_scripts.fix_pietanza_portions --dry-run  # anteprima
"""

import argparse
import sys
from pathlib import Path

from sqlmodel import Session, create_engine, select

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from api.models.nutrition import Food, StandardPortion  # noqa: E402

# ---------------------------------------------------------------------------
# Porzioni LARN 2014 di default per categoria pietanza
# ---------------------------------------------------------------------------

LARN_PORTIONS_BY_CAT: dict[int, list[tuple[str, float]]] = {
    1: [("1 porzione", 30)],
    2: [("1 porzione", 200), ("1/2 porzione", 100)],
    3: [("1 porzione", 50)],
    4: [("1 porzione", 150), ("1/2 porzione", 75)],
    8: [("1 porzione", 100), ("1 porzione grande", 150)],
    9: [("2 fette", 30), ("1 porzione", 50)],
    10: [("1 porzione", 150), ("1 filetto", 200)],
    11: [("1 uovo", 50), ("2 uova", 100)],
    13: [("1 cucchiaio", 10), ("2 cucchiai", 20)],
    14: [("1 porzione", 50)],
}

# ---------------------------------------------------------------------------
# Override specifici dove il generico non va bene
# ---------------------------------------------------------------------------

SPECIFIC: dict[str, list[tuple[str, float]]] = {
    # Cat 2
    "Pasta all'uovo, cotta": [("1 porzione", 200), ("1/2 porzione", 100)],
    # Cat 3 — Biscotti
    "Biscotti frollini classici": [("3 biscotti", 30), ("5 biscotti", 50)],
    "Biscotti secchi (tipo digestive)": [("3 biscotti", 30), ("5 biscotti", 50)],
    "Biscotto al cocco (tipo Oro Saiwa)": [("2 biscotti", 20), ("4 biscotti", 40)],
    # Cat 3 — Fette biscottate
    "Fette biscottate classiche": [("2 fette", 20), ("3 fette", 30)],
    "Fette biscottate senza glutine": [("2 fette", 20), ("3 fette", 30)],
    "Fette biscottate integrali": [("2 fette", 20), ("3 fette", 30)],
    "Fetta biscottata alla frutta": [("2 fette", 20), ("3 fette", 30)],
    # Cat 3 — Crackers/grissini
    "Cracker di riso (gallette mini)": [("2 gallette", 16), ("4 gallette", 32)],
    "Crackers integrali": [("3 crackers", 25), ("5 crackers", 42)],
    "Grissini torinesi": [("3 grissini", 20), ("5 grissini", 33)],
    "Taralli pugliesi": [("3 taralli", 30), ("5 taralli", 50)],
    # Cat 3 — Pane specifico
    "Cornetto (brioche vuoto)": [("1 cornetto", 50)],
    "Crespelle (cr\u00e9pes, neutre)": [("1 crepe", 40), ("2 crepes", 80)],
    "Waffle (neutro base)": [("1 waffle", 50), ("2 waffle", 100)],
    "Muffin all'avena (senza latticini)": [("1 muffin", 60)],
    "Pane ciabatta": [("1 fetta", 40), ("1 panino", 80)],
    "Pane in cassetta (toast)": [("1 fetta", 25), ("2 fette", 50)],
    "Pane al latte": [("1 panino", 50), ("2 panini", 100)],
    "Pane all'olio": [("1 fetta", 40), ("1 panino", 80)],
    "Baguette francese": [("1/4 baguette", 60), ("1/2 baguette", 120)],
    "Naan indiano": [("1 naan", 90)],
    "Chapati (pane indiano integrale)": [("1 chapati", 50), ("2 chapati", 100)],
    "Schiacciata toscana": [("1 fetta", 60), ("2 fette", 120)],
    "Focaccia genovese": [("1 fetta", 60), ("2 fette", 120)],
    "Piadina romagnola": [("1 piadina", 100)],
    "Tortilla di frumento": [("1 tortilla", 40), ("2 tortillas", 80)],
    "Tortilla di mais": [("1 tortilla", 40), ("2 tortillas", 80)],
    "Tortilla di farro": [("1 tortilla", 40), ("2 tortillas", 80)],
    "Tortino di mais (polenta al forno)": [("1 porzione", 150)],
    "Pancarr\u00e8 di segale": [("1 fetta", 25), ("2 fette", 50)],
    "Pane azzimo (matza)": [("1 foglio", 30)],
    "Pane azzimo integrale": [("1 foglio", 30)],
    "Pane di segale compatto (tipo wasa)": [("2 fette", 20), ("4 fette", 40)],
    "Crumble di avena (base dolce)": [("1 porzione", 40)],
    # Cat 8 — Carne
    "Ali di pollo, cotte al forno": [("2 ali", 80), ("4 ali", 160)],
    "Maiale, costolette cotte": [("1 costoletta", 130)],
    "Polpette di carne al sugo (cotte)": [("2 polpette", 100), ("3 polpette", 150)],
    "Hamburger di manzo (80% magro)": [("1 hamburger", 100), ("1 doppio", 200)],
    "Hamburger di pollo (grigliato)": [("1 hamburger", 100)],
    "Scaloppina di vitello al marsala": [("1 scaloppina", 120)],
    "Petto di pollo, cotto in padella": [("1 petto", 150), ("1/2 petto", 75)],
    "Petto di pollo, affettato cotto": [("1 petto", 150), ("1/2 petto", 75)],
    "Pollo tikka masala (piatto indiano)": [("1 porzione", 200)],
    "Manzo, stinco cotto in umido": [("1 porzione", 200)],
    "Petto di pollo arrosto (affettato, packed)": [("2 fette", 40), ("4 fette", 80)],
    # Cat 9 — Salumi
    "Cotechino (prodotto cotto)": [("1 fetta", 50), ("2 fette", 100)],
    "Zampone di Modena IGP (cotto)": [("1 fetta", 50), ("2 fette", 100)],
    "Prosciutto cotto al forno": [("2 fette", 40), ("4 fette", 80)],
    "Porchetta (arrosto di maiale)": [("2 fette", 60), ("1 panino", 100)],
    "Coppa di testa": [("2 fette", 30), ("1 porzione", 50)],
    "Testa in cassetta (headcheese)": [("2 fette", 30), ("1 porzione", 50)],
    # Cat 10 — Pesce
    "Ostriche gratinate al forno": [("3 ostriche", 90), ("6 ostriche", 180)],
    "Sardine in scatola all'olio, scolate": [("1 scatoletta", 52)],
    "Scampi fritti (impanati)": [("1 porzione", 150)],
    "Polpo, in umido": [("1 porzione", 200)],
    "Ceviche di branzino (piatto crudo)": [("1 porzione", 150)],
    "Baccal\u00e0 alla vicentina (piatto cotto)": [("1 porzione", 200)],
    # Cat 11 — Uova
    "Frittata base (uovo+latte), cotta": [("1 frittata (2 uova)", 130), ("1/2 frittata", 65)],
    "Frittata proteica (2 uova+albume)": [("1 frittata", 165), ("1/2 frittata", 82)],
    "Uovo intero, strapazzato (con latte)": [("1 porzione (2 uova)", 120)],
    "Uovo in camicia (poch\u00e9)": [("1 uovo", 50), ("2 uova", 100)],
    # Cat 13 — Salse
    "Pesto genovese (basilico/olio/parmigiano)": [("1 cucchiaio", 15), ("2 cucchiai", 30)],
    "Guacamole": [("1 porzione", 50), ("2 porzioni", 100)],
    "Salsa tzatziki": [("2 cucchiai", 30), ("1 porzione", 60)],
    "Salsa di panna (besciamella)": [("2 cucchiai", 30), ("1 porzione", 60)],
    "Soffritto di cipolla-sedano-carota (base)": [("2 cucchiai", 30)],
    "Salsa di pomodoro fresco (bruschetta)": [("2 cucchiai", 30), ("1 porzione", 60)],
    "Salsa romesco (pomodoro/mandorle)": [("1 cucchiaio", 15), ("2 cucchiai", 30)],
    "Nutella (crema nocciole e cacao)": [("1 cucchiaio", 15), ("2 cucchiai", 30)],
    # Cat 14 — Dolci
    "Barretta ai cereali (media)": [("1 barretta", 35)],
    "Barretta proteica (media, 30% prot)": [("1 barretta", 40)],
    "Tiramis\u00f9": [("1 fetta", 100)],
    "Panna cotta": [("1 panna cotta", 120)],
    "Crostata (base frolla + marmellata)": [("1 fetta", 80)],
    "Budino di vaniglia (commerciale)": [("1 vasetto", 125)],
    "Gelato alla crema (artigianale)": [("1 pallina", 50), ("2 palline", 100)],
    "Gelato al cioccolato": [("1 pallina", 50), ("2 palline", 100)],
    "Gelato alla frutta (sorbetto)": [("1 pallina", 50), ("2 palline", 100)],
    "Granita al limone (senza latte)": [("1 bicchiere", 200)],
    "Coppetta di gelato (2 palline tipo)": [("1 coppetta", 100)],
    "Pancakes (base classica)": [("1 pancake", 40), ("3 pancakes", 120)],
    "Torta sponge (pan di spagna)": [("1 fetta", 80)],
    "Torta di mele (classica)": [("1 fetta", 120)],
    "Panettone milanese": [("1 fetta", 80)],
    "Pandoro veronese": [("1 fetta", 80)],
    "Colomba pasquale": [("1 fetta", 80)],
    "Cheesecake (fetta, base biscotto)": [("1 fetta", 120)],
    "Sfogliatella napoletana": [("1 sfogliatella", 100)],
    "Ciambelle glassate (donuts)": [("1 donut", 60)],
    "Croissant integrale (whole wheat)": [("1 croissant", 50)],
    "Cantucci (biscotti di Prato)": [("2 cantucci", 20), ("4 cantucci", 40)],
    "Madeleine (pasticcino francese)": [("1 madeleine", 25), ("3 madeleine", 75)],
    "Meringa secca": [("2 meringhe", 10), ("4 meringhe", 20)],
    "Biscotti di avena e cioccolato": [("2 biscotti", 20), ("4 biscotti", 40)],
    "Brownie al cioccolato": [("1 brownie", 60)],
    "Wafer alla vaniglia": [("2 wafer", 16), ("4 wafer", 32)],
    "Zabaione (zabaglione)": [("1 porzione", 100)],
    "Polenta dolce alla bergamasca": [("1 porzione", 150)],
    "Semifreddo al caff\u00e8": [("1 fetta", 100)],
    "Crostino dolce con miele e ricotta": [("1 crostino", 60)],
    "Bign\u00e8 alla crema": [("1 bigne", 40), ("2 bigne", 80)],
    "Crema di marroni (crema di castagne)": [("1 cucchiaio", 20), ("2 cucchiai", 40)],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix porzioni pietanze → LARN 2014")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db_path = ROOT / "data" / "nutrition.db"
    if not db_path.exists():
        print(f"ERROR: {db_path} non trovato")
        sys.exit(1)

    engine = create_engine(f"sqlite:///{db_path}")
    with Session(engine) as s:
        pietanze = s.exec(
            select(Food).where(Food.food_type == "pietanza", Food.is_active == True)
        ).all()
        pietanza_ids = [f.id for f in pietanze]

        # 1. Rimuovi TUTTE le porzioni esistenti su pietanze
        old = s.exec(
            select(StandardPortion).where(StandardPortion.alimento_id.in_(pietanza_ids))
        ).all()
        for p in old:
            if not args.dry_run:
                s.delete(p)
        print(f"Rimosse: {len(old)} porzioni vecchie")

        # 2. Inserisci porzioni LARN-correct
        added = 0
        for food in pietanze:
            if food.nome in SPECIFIC:
                portions = SPECIFIC[food.nome]
            elif food.categoria_id in LARN_PORTIONS_BY_CAT:
                portions = LARN_PORTIONS_BY_CAT[food.categoria_id]
            else:
                portions = [("1 porzione", 100)]

            for nome, grammi in portions:
                if not args.dry_run:
                    s.add(StandardPortion(alimento_id=food.id, nome=nome, grammi=grammi))
                added += 1

        if not args.dry_run:
            s.commit()

        print(f"Aggiunte: {added} porzioni LARN-correct")
        suffix = " (dry-run)" if args.dry_run else ""
        print(f"Fatto{suffix}.")


if __name__ == "__main__":
    main()
