"""
SPEC_REVISIONE_PRE_G7 — Sezione A: convergenza del residuo al SSoT contract_state.residuo().

Due reti, in quest'ordine (la 1ª è sintattica, la 2ª è semantica e cattura anche l'ignoto):
- AC-A1 — guard-rail anti-ricalcolo inline: nessun `prezzo_totale − totale_versato` fuori dal SSoT.
- AC-A2 — coerenza cross-surface: lo stesso contratto riporta lo STESSO residuo su lista,
  dettaglio e workspace (finance_context). È l'antidoto all'incompletezza dell'enumerazione
  manuale: il giorno in cui G7 ridefinisce residuo() e un sito non delega, AC-A2 diventa rosso.

AC-A3 (le occorrenze note delegano + invariante kpi_residuo = a_rate + da_pianificare +
da_incassare_scaduto) è già presidiato da tests/test_contracts_to_plan.py (218-219).
"""

import re
from datetime import date, timedelta
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent / "api"

# Il SSoT è l'UNICO autorizzato a calcolare prezzo − versato.
ALLOWLIST = {"services/contract_state.py"}

# Coppia di token in ordine "residuo" (prezzo prima), con un '-' fra i due sulla stessa riga.
# Mirato: esclude il residuo DI RATA (importo_previsto − importo_saldato), il `cap` (prezzo − acconto),
# la percentuale (versato / prezzo) e la riconciliazione (versato − Σ movimenti).
# Limiti noti (documentati, SPEC §A.3): cieco a predicati ORM (prezzo > versato), raw-SQL,
# forme multilinea/parafrasate e a TUTTO il frontend TS → AC-A2 è il backstop semantico.
_RESIDUO_INLINE = re.compile(r"prezzo_totale\b.{0,80}-.{0,80}\btotale_versato\b")


def test_ac_a1_no_inline_residuo_recalc():
    """Diventa rosso se ricompare un ricalcolo inline del residuo fuori da contract_state.py."""
    offenders = []
    for path in sorted(API_DIR.rglob("*.py")):
        rel = path.relative_to(API_DIR).as_posix()
        if rel in ALLOWLIST:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _RESIDUO_INLINE.search(line):
                offenders.append(f"{rel}:{i}: {line.strip()}")
    assert not offenders, (
        "Ricalcolo inline del residuo del contratto fuori da contract_state.residuo() "
        "(SPEC_REVISIONE_PRE_G7 §A / regola d'oro §8.1). Delega a cstate.residuo(contract):\n"
        + "\n".join(offenders)
    )


def test_ac_a1_guardrail_detects_a_violation(tmp_path, monkeypatch):
    """Meta-test: il guard-rail NON è un no-op — un sito inline finto viene davvero intercettato."""
    fake_api = tmp_path / "api"
    (fake_api / "routers").mkdir(parents=True)
    (fake_api / "routers" / "evil.py").write_text(
        "x = round((c.prezzo_totale or 0) - (c.totale_versato or 0), 2)\n", encoding="utf-8"
    )
    monkeypatch.setattr("tests.test_residuo_convergence.API_DIR", fake_api)
    import pytest
    with pytest.raises(AssertionError):
        test_ac_a1_no_inline_residuo_recalc()


def test_ac_a2_residuo_coincides_across_surfaces(client, auth_headers, sample_client):
    """Lo stesso contratto → stesso residuo su lista, dettaglio e workspace (renewals_cash).

    Fixture pilotata su un contratto in scadenza (finestra renewal [oggi, +30] + crediti residui)
    così da emergere come case contract-level nel workspace, dove `total_residual_amount` È il
    residuo del contratto (per gli overdue sarebbe la somma dei residui-rata → seam noto, SPEC AC-A2).
    """
    today = date.today()
    scad = (today + timedelta(days=15)).isoformat()
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Cross-surface",
        "crediti_totali": 10,
        "prezzo_totale": 1000.0,
        "data_inizio": today.isoformat(),
        "data_scadenza": scad,
        "acconto": 200.0,
        "metodo_acconto": "CONTANTI",
    }, headers=auth_headers)
    assert cr.status_code == 201, cr.text
    cid = cr.json()["id"]

    # Superficie 1 — lista
    lst = client.get("/api/contracts", headers=auth_headers)
    assert lst.status_code == 200
    row = next(it for it in lst.json()["items"] if it["id"] == cid)
    residuo_list = row["residuo"]

    # Superficie 2 — dettaglio
    det = client.get(f"/api/contracts/{cid}", headers=auth_headers)
    assert det.status_code == 200
    residuo_detail = det.json()["residuo"]

    # Superficie 3 — workspace (renewals_cash): case contract-level del contratto
    ws = client.get("/api/workspace/cases?workspace=renewals_cash", headers=auth_headers)
    assert ws.status_code == 200
    contract_cases = [
        c for c in ws.json()["items"]
        if c.get("root_entity", {}).get("type") == "contract"
        and c["root_entity"]["id"] == cid
        and c.get("finance_context")
        and c["finance_context"].get("total_residual_amount") is not None
    ]
    assert contract_cases, "atteso un OperationalCase contract-level per il contratto in scadenza"
    residuo_ws = contract_cases[0]["finance_context"]["total_residual_amount"]

    # Coincidenza cross-surface (e valore atteso 1000 − 200)
    assert residuo_list == residuo_detail == residuo_ws == 800.0
