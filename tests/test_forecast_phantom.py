"""
Prereq P1 — fix Forecast "entrata-fantasma".

Una rata PENDENTE su un contratto CHIUSO (non eliminato) NON deve essere proiettata come
entrata certa dal Forecast (`movements.py` get_forecast filtra ora `Contract.chiuso == False`).
"""

from datetime import date, timedelta

from api.models.contract import Contract

TODAY = date.today()


def _add_rate(client, auth_headers, contract_id, importo, scadenza):
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": scadenza.isoformat(),
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _forecast(client, auth_headers):
    r = client.get("/api/movements/forecast?mesi=3", headers=auth_headers)
    assert r.status_code == 200
    return r.json()


def test_pending_rate_on_open_contract_is_projected(client, auth_headers, sample_contract):
    """Controprova: su contratto APERTO la rata PENDENTE futura è entrata attesa."""
    _add_rate(client, auth_headers, sample_contract["id"], 300.0, TODAY + timedelta(days=30))
    data = _forecast(client, auth_headers)
    assert data["kpi"]["entrate_attese_90gg"] >= 300.0
    assert any("Rata" in t["descrizione"] or t["tipo"] == "ENTRATA" for t in data["timeline"])


def test_pending_rate_on_closed_contract_is_phantom_excluded(client, auth_headers, sample_contract, session):
    """Chiudendo il contratto, la stessa rata PENDENTE sparisce dalla proiezione (no fantasma)."""
    cid = sample_contract["id"]
    _add_rate(client, auth_headers, cid, 300.0, TODAY + timedelta(days=30))

    before = _forecast(client, auth_headers)["kpi"]["entrate_attese_90gg"]

    # Chiudi via ORM MANTENENDO la rata PENDENTE viva. Post-G7.3 il canale PUT chiuso è ritirato;
    # `terminate` soft-eliminerebbe la rata → il test verificherebbe la cancellazione, NON il
    # FILTRO-chiuso del forecast (il fix P1 che questo test presidia). Lo stato chiuso=True ∧ rata
    # viva resta legittimo (legacy) e va costruito a mano, come i forward-guard di test_lifecycle_audit.
    contract = session.get(Contract, cid)
    contract.chiuso = True
    session.add(contract)
    session.commit()

    after_data = _forecast(client, auth_headers)
    after = after_data["kpi"]["entrate_attese_90gg"]

    assert round(before - after, 2) == 300.0  # l'entrata-fantasma è stata rimossa
    # nessuna riga timeline residua per quella rata
    assert all(t["importo"] != 300.0 or t["tipo"] != "ENTRATA" for t in after_data["timeline"])
