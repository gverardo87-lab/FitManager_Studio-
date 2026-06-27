"""Spec 2 — audit lifecycle dedicato sui crossing temporali di `update_contract`.

Il modello resta derivato: `PUT /contracts/{id}` cambia `data_scadenza`, e il backend deve lasciare
una traccia semantica quando il crossing della scadenza cambia il lifecycle aperto
ATTIVO/SOSPESO/ESAURITO.
"""

import json
from datetime import date, timedelta

from sqlmodel import select

from api.models.audit_log import AuditLog
from api.models.contract import Contract

TODAY = date.today()


def _future(days: int) -> str:
    return (TODAY + timedelta(days=days)).isoformat()


def _past(days: int) -> str:
    return (TODAY - timedelta(days=days)).isoformat()


def _contract(
    client,
    auth_headers,
    client_id,
    *,
    prezzo=100.0,
    acconto=0.0,
    crediti=10,
    inizio=None,
    scadenza=None,
):
    body = {
        "id_cliente": client_id,
        "tipo_pacchetto": "Pkg",
        "crediti_totali": crediti,
        "prezzo_totale": prezzo,
        "data_inizio": inizio or TODAY.isoformat(),
        "data_scadenza": scadenza or _future(120),
        "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _pt_event(client, auth_headers, client_id, contract_id, hour=9):
    r = client.post(
        "/api/events",
        json={
            "data_inizio": f"{TODAY.isoformat()}T{hour:02d}:00:00",
            "data_fine": f"{TODAY.isoformat()}T{hour:02d}:30:00",
            "categoria": "PT",
            "titolo": "Seduta",
            "id_cliente": client_id,
            "id_contratto": contract_id,
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _all_audit_changes(session, contract_id):
    session.expire_all()
    rows = session.exec(
        select(AuditLog)
        .where(AuditLog.entity_type == "contract", AuditLog.entity_id == contract_id)
        .order_by(AuditLog.id)
    ).all()
    return [json.loads(r.changes) for r in rows if r.changes]


def _lifecycle_entries(session, contract_id):
    return [ch for ch in _all_audit_changes(session, contract_id) if "lifecycle" in ch]


def _has_scadenza_diff(session, contract_id):
    return any("data_scadenza" in ch for ch in _all_audit_changes(session, contract_id))


def _detail(client, auth_headers, contract_id):
    r = client.get(f"/api/contracts/{contract_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_update_contract_logs_attivo_to_sospeso_on_retrodate(client, auth_headers, sample_client, session):
    c = _contract(
        client,
        auth_headers,
        sample_client["id"],
        crediti=10,
        inizio=_past(120),
        scadenza=_future(60),
    )

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _past(1)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "sospeso"
    assert _has_scadenza_diff(session, c["id"])
    entries = _lifecycle_entries(session, c["id"])
    assert len(entries) == 1
    assert entries[0]["lifecycle"] == {"old": "attivo", "new": "sospeso"}
    assert entries[0]["trigger"] == "data_scadenza_update"
    assert entries[0]["motivo"] == "scadenza_retrodatata"


def test_update_contract_logs_attivo_to_esaurito_on_retrodate(client, auth_headers, sample_client, session):
    c = _contract(
        client,
        auth_headers,
        sample_client["id"],
        crediti=1,
        inizio=_past(120),
        scadenza=_future(60),
    )
    _pt_event(client, auth_headers, sample_client["id"], c["id"])

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _past(1)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "esaurito"
    assert _has_scadenza_diff(session, c["id"])
    entries = _lifecycle_entries(session, c["id"])
    assert len(entries) == 1
    assert entries[0]["lifecycle"] == {"old": "attivo", "new": "esaurito"}
    assert entries[0]["trigger"] == "data_scadenza_update"
    assert entries[0]["motivo"] == "scadenza_retrodatata"


def test_update_contract_logs_sospeso_to_attivo_on_extend(client, auth_headers, sample_client, session):
    c = _contract(
        client,
        auth_headers,
        sample_client["id"],
        crediti=10,
        inizio=_past(120),
        scadenza=_past(5),
    )
    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "sospeso"

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _future(45)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "attivo"
    assert _has_scadenza_diff(session, c["id"])
    entries = _lifecycle_entries(session, c["id"])
    assert len(entries) == 1
    assert entries[0]["lifecycle"] == {"old": "sospeso", "new": "attivo"}
    assert entries[0]["trigger"] == "data_scadenza_update"
    assert entries[0]["motivo"] == "scadenza_estesa"


def test_update_contract_logs_esaurito_to_attivo_on_extend(client, auth_headers, sample_client, session):
    c = _contract(
        client,
        auth_headers,
        sample_client["id"],
        crediti=1,
        inizio=_past(120),
        scadenza=_future(60),
    )
    _pt_event(client, auth_headers, sample_client["id"], c["id"])

    contract = session.get(Contract, c["id"])
    contract.data_scadenza = TODAY - timedelta(days=2)
    session.add(contract)
    session.commit()
    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "esaurito"

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _future(45)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "attivo"
    assert _has_scadenza_diff(session, c["id"])
    entries = _lifecycle_entries(session, c["id"])
    assert len(entries) == 1
    assert entries[0]["lifecycle"] == {"old": "esaurito", "new": "attivo"}
    assert entries[0]["trigger"] == "data_scadenza_update"
    assert entries[0]["motivo"] == "scadenza_estesa"


def test_update_contract_future_to_future_has_no_lifecycle_audit(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=10, inizio=_past(30), scadenza=_future(30))

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _future(90)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "attivo"
    assert _has_scadenza_diff(session, c["id"])
    assert _lifecycle_entries(session, c["id"]) == []


def test_update_contract_past_to_past_has_no_lifecycle_audit(client, auth_headers, sample_client, session):
    c = _contract(
        client,
        auth_headers,
        sample_client["id"],
        crediti=10,
        inizio=_past(120),
        scadenza=_past(5),
    )
    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "sospeso"

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _past(20)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _detail(client, auth_headers, c["id"])["lifecycle"] == "sospeso"
    assert _has_scadenza_diff(session, c["id"])
    assert _lifecycle_entries(session, c["id"]) == []