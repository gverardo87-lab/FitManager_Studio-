"""Audit completo integrita' 3 database FitManager."""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"


def get_tables(db_path):
    conn = sqlite3.connect(str(db_path))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    conn.close()
    return tables


def get_count(db_path, table, where=""):
    conn = sqlite3.connect(str(db_path))
    q = f"SELECT COUNT(*) FROM [{table}]"
    if where:
        q += f" WHERE {where}"
    c = conn.execute(q).fetchone()[0]
    conn.close()
    return c


def get_columns(db_path, table):
    conn = sqlite3.connect(str(db_path))
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]
    conn.close()
    return cols


EXPECTED_CATALOG = {
    "esercizi", "esercizi_muscoli", "esercizi_articolazioni",
    "esercizi_condizioni", "esercizi_relazioni", "esercizi_media",
    "muscoli", "articolazioni", "condizioni_mediche", "metriche",
}
EXPECTED_NUTRITION = {
    "alimenti", "categorie_alimenti", "porzioni_standard",
    "ricette_pietanze", "plan_templates", "template_plan_meals",
    "template_plan_components", "alembic_version",
}


def main():
    results = []

    print("=" * 80)
    print("AUDIT DATABASE INTEGRITY")
    print("=" * 80)

    # ── 1. SEPARAZIONE ARCHITETTURALE ──
    print("\n### 1. SEPARAZIONE ARCHITETTURALE ###\n")

    crm_tables = get_tables(DATA / "crm.db")
    catalog_tables = get_tables(DATA / "catalog.db")
    nutrition_tables = get_tables(DATA / "nutrition.db")

    # metriche e' condivisa (catalog + crm), alembic_version e' legittimo in crm
    shared_ok = {"metriche", "alembic_version"}
    cat_in_crm = [t for t in crm_tables if t in EXPECTED_CATALOG and t not in shared_ok]
    nut_in_crm = [t for t in crm_tables if t in EXPECTED_NUTRITION and t not in shared_ok]
    ok = not cat_in_crm and not nut_in_crm
    results.append(("Separazione crm.db", "OK" if ok else "FAIL"))
    print(f"  crm.db: {len(crm_tables)} tabelle, contamination={cat_in_crm + nut_in_crm or 'NONE'} => {'OK' if ok else 'FAIL'}")

    missing_cat = EXPECTED_CATALOG - set(catalog_tables)
    ok = not missing_cat
    results.append(("catalog.db schema", "OK" if ok else "FAIL"))
    print(f"  catalog.db: {len(catalog_tables)} tabelle, missing={missing_cat or 'NONE'} => {'OK' if ok else 'FAIL'}")

    missing_nut = EXPECTED_NUTRITION - set(nutrition_tables)
    ok = not missing_nut
    results.append(("nutrition.db schema", "OK" if ok else "FAIL"))
    print(f"  nutrition.db: {len(nutrition_tables)} tabelle, missing={missing_nut or 'NONE'} => {'OK' if ok else 'FAIL'}")

    # trainer_id check
    for db, name in [(DATA / "catalog.db", "catalog"), (DATA / "nutrition.db", "nutrition")]:
        found = []
        for t in get_tables(db):
            if "trainer_id" in get_columns(db, t):
                found.append(t)
        ok = not found
        results.append((f"{name}.db no trainer_id", "OK" if ok else "FAIL"))
        print(f"  {name}.db trainer_id: {found or 'NONE'} => {'OK' if ok else 'FAIL'}")

    # ── 2. CONTEGGI ──
    print("\n### 2. CONTEGGI ###\n")

    counts = {
        "Esercizi attivi": get_count(DATA / "catalog.db", "esercizi", "in_subset=1"),
        "Relazioni": get_count(DATA / "catalog.db", "esercizi_relazioni"),
        "Media": get_count(DATA / "catalog.db", "esercizi_media"),
        "Muscoli": get_count(DATA / "catalog.db", "muscoli"),
        "Articolazioni": get_count(DATA / "catalog.db", "articolazioni"),
        "Condizioni": get_count(DATA / "catalog.db", "condizioni_mediche"),
        "Alimenti attivi": get_count(DATA / "nutrition.db", "alimenti", "is_active=1"),
        "Categorie alimenti": get_count(DATA / "nutrition.db", "categorie_alimenti"),
        "Porzioni standard": get_count(DATA / "nutrition.db", "porzioni_standard"),
        "Ricette pietanze": get_count(DATA / "nutrition.db", "ricette_pietanze"),
        "Plan templates": get_count(DATA / "nutrition.db", "plan_templates"),
    }
    for k, v in counts.items():
        print(f"  {k:25s} {v:>6}")

    # Pietanze coverage
    conn = sqlite3.connect(str(DATA / "nutrition.db"))
    total_p = conn.execute(
        "SELECT COUNT(*) FROM alimenti WHERE food_type='pietanza' AND is_active=1"
    ).fetchone()[0]
    with_recipe = conn.execute(
        "SELECT COUNT(DISTINCT pietanza_id) FROM ricette_pietanze"
    ).fetchone()[0]
    conn.close()
    print(f"  {'Pietanze con ricetta':25s} {with_recipe}/{total_p} ({with_recipe * 100 // total_p}%)")

    # crm.db tables with data
    print("\n  crm.db (tabelle con dati):")
    for t in sorted(crm_tables):
        if t != "alembic_version":
            c = get_count(DATA / "crm.db", t)
            if c > 0:
                print(f"    {t:35s} {c:>6}")
    crm_biz = len([t for t in crm_tables if t != "alembic_version"])
    print(f"  Tabelle business: {crm_biz}")

    # ── 3. INTEGRITA CROSS-DB ──
    print("\n### 3. INTEGRITA CROSS-DB ###\n")

    crm_conn = sqlite3.connect(str(DATA / "crm.db"))
    cat_conn = sqlite3.connect(str(DATA / "catalog.db"))
    nut_conn = sqlite3.connect(str(DATA / "nutrition.db"))

    if "esercizi_sessione" in crm_tables:
        ex_crm = set(r[0] for r in crm_conn.execute(
            "SELECT DISTINCT id_esercizio FROM esercizi_sessione WHERE id_esercizio IS NOT NULL"
        ).fetchall())
        ex_cat = set(r[0] for r in cat_conn.execute("SELECT id FROM esercizi").fetchall())
        orphans = ex_crm - ex_cat
        ok = not orphans
        status = "OK" if ok else "WARN"
        results.append(("Cross-DB esercizi", status))
        print(f"  esercizi_sessione -> catalog: {len(ex_crm)} refs, {len(orphans)} orphans => {status}")
        if orphans:
            print(f"    (debito tecnico: ID da catalogo pre-rebuild, UI mostra fallback)")

    if "componenti_pasto" in crm_tables:
        fd_crm = set(r[0] for r in crm_conn.execute(
            "SELECT DISTINCT alimento_id FROM componenti_pasto WHERE alimento_id IS NOT NULL"
        ).fetchall())
        fd_nut = set(r[0] for r in nut_conn.execute("SELECT id FROM alimenti").fetchall())
        orphans = fd_crm - fd_nut
        ok = not orphans
        results.append(("Cross-DB alimenti", "OK" if ok else "FAIL"))
        print(f"  componenti_pasto -> nutrition: {len(fd_crm)} refs, {len(orphans)} orphans => {'OK' if ok else 'FAIL'}")

    # Internal FK ricette
    rp = set(r[0] for r in nut_conn.execute("SELECT DISTINCT pietanza_id FROM ricette_pietanze").fetchall())
    ri = set(r[0] for r in nut_conn.execute("SELECT DISTINCT ingrediente_id FROM ricette_pietanze").fetchall())
    af = set(r[0] for r in nut_conn.execute("SELECT id FROM alimenti").fetchall())
    ok = not (rp - af) and not (ri - af)
    results.append(("ricette_pietanze FK", "OK" if ok else "FAIL"))
    print(f"  ricette_pietanze internal FK: pietanza orphans={len(rp - af)}, ingrediente orphans={len(ri - af)} => {'OK' if ok else 'FAIL'}")

    crm_conn.close()
    cat_conn.close()
    nut_conn.close()

    # ── 5. JSON FIELDS ──
    print("\n### 4. JSON FIELDS INTEGRITY ###\n")

    conn = sqlite3.connect(str(DATA / "catalog.db"))
    json_cols = ["muscoli_primari", "muscoli_secondari", "coaching_cues", "errori_comuni", "controindicazioni"]
    rows = conn.execute(
        f"SELECT id, nome, {', '.join(json_cols)} FROM esercizi ORDER BY RANDOM() LIMIT 10"
    ).fetchall()

    errors = 0
    for row in rows:
        for i, col in enumerate(json_cols):
            val = row[2 + i]
            if val is not None:
                try:
                    parsed = json.loads(val)
                    if isinstance(parsed, str):
                        errors += 1
                        print(f"  DOUBLE-ENCODED: {row[0]} {col}")
                except json.JSONDecodeError:
                    errors += 1
                    print(f"  INVALID JSON: {row[0]} {col}")

    ok = errors == 0
    results.append(("JSON integrity", "OK" if ok else "FAIL"))
    print(f"  50 JSON fields checked, {errors} errors => {'OK' if ok else 'FAIL'}")
    conn.close()

    # ── PRAGMA ──
    print("\n### 5. PRAGMA INTEGRITY ###\n")

    for db_name in ["crm.db", "catalog.db", "nutrition.db"]:
        conn = sqlite3.connect(str(DATA / db_name))
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        ok = integrity == "ok"
        results.append((f"{db_name} integrity", "OK" if ok else "FAIL"))
        print(f"  {db_name:15s} integrity={integrity:4s} journal={journal}")
        conn.close()

    # ── SUMMARY ──
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    fails = [r for r in results if r[1] == "FAIL"]
    warns = [r for r in results if r[1] == "WARN"]
    oks = [r for r in results if r[1] == "OK"]
    for name, status in results:
        icon = {"OK": "[OK]", "WARN": "[~~]", "FAIL": "[!!]"}[status]
        print(f"  {icon} {name}")
    print(f"\n  Total: {len(results)} checks, {len(oks)} OK, {len(warns)} WARN, {len(fails)} FAIL")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
