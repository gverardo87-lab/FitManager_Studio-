"""
Prereq P2 — audit della transizione `chiuso` del contratto.

Oggi `pay_rate`/`unpay_rate` (auto-close/reopen) e `agenda._sync_contract_chiuso` accendono o
spengono `chiuso` senza loggarlo: l'evento più importante da tracciare legalmente (terminazione, G7)
non può ereditare un audit bucato. Il nuovo helper `log_contract_lifecycle_transition` lo registra,
idempotente (no-op se `chiuso` non cambia).
"""

import json
from datetime import date, timedelta

from sqlmodel import select

from api.models.audit_log import AuditLog

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": TODAY.isoformat(), "data_scadenza": FUTURE,
        "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _pt_event(client, auth_headers, client_id, contract_id, hour=9):
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T{hour:02d}:00:00",
        "data_fine": f"{TODAY.isoformat()}T{hour:02d}:30:00",
        "categoria": "PT",
        "titolo": "Seduta",
        "id_cliente": client_id,
        "id_contratto": contract_id,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _rate(client, auth_headers, contract_id, importo):
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _chiuso_transitions(session, contract_id):
    """Ritorna i changes (dict) delle audit entry sul contratto che toccano `chiuso`."""
    session.expire_all()
    rows = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "contract",
            AuditLog.entity_id == contract_id,
        )
    ).all()
    out = []
    for r in rows:
        if r.changes:
            ch = json.loads(r.changes)
            if "chiuso" in ch:
                out.append(ch)
    return out


# ── pay_rate → auto-close (completamento) ──────────────────────────

def test_pay_autoclose_logs_transition(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])  # consuma l'unico credito
    rate = _rate(client, auth_headers, c["id"], 100.0)

    # prima del pagamento: nessuna transizione chiuso loggata
    assert _chiuso_transitions(session, c["id"]) == []

    r = client.post(f"/api/rates/{rate['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    trans = _chiuso_transitions(session, c["id"])
    assert len(trans) == 1
    assert trans[0]["chiuso"] == {"old": False, "new": True}
    assert trans[0]["motivo"] == "completamento"


# ── unpay_rate → auto-reopen (riapertura_pagamento) ────────────────

def test_unpay_autoreopen_logs_transition(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])
    rate = _rate(client, auth_headers, c["id"], 100.0)
    client.post(f"/api/rates/{rate['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)

    r = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert r.status_code == 200, r.text

    trans = _chiuso_transitions(session, c["id"])
    # 2 transizioni: chiusura (pay) + riapertura (unpay)
    assert trans[-1]["chiuso"] == {"old": True, "new": False}
    assert trans[-1]["motivo"] == "riapertura_pagamento"


# ── agenda: evento chiude / cancella riapre ────────────────────────

def test_event_autoclose_and_reopen_log_transition(client, auth_headers, sample_client, session):
    # SALDATO dall'inizio (acconto==prezzo), 1 credito → l'evento finale chiude
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    assert _chiuso_transitions(session, c["id"]) == []  # alla creazione non si chiude (crediti non usati)

    ev = _pt_event(client, auth_headers, sample_client["id"], c["id"])
    trans = _chiuso_transitions(session, c["id"])
    assert len(trans) == 1
    assert trans[0]["chiuso"] == {"old": False, "new": True}
    assert trans[0]["motivo"] == "completamento"

    d = client.delete(f"/api/events/{ev['id']}", headers=auth_headers)
    assert d.status_code in (200, 204), d.text
    trans = _chiuso_transitions(session, c["id"])
    assert trans[-1]["chiuso"] == {"old": True, "new": False}
    assert trans[-1]["motivo"] == "riapertura_crediti"


# ── idempotenza: nessun audit chiuso se lo stato non cambia ────────

def test_no_transition_when_chiuso_unchanged(client, auth_headers, sample_contract_with_plan, session):
    # paga una rata SENZA esaurire i crediti (contratto resta aperto) → zero transizioni chiuso
    rate = sample_contract_with_plan["rates"][0]
    cid = sample_contract_with_plan["contract"]["id"]
    r = client.post(f"/api/rates/{rate['id']}/pay", json={"importo": rate["importo_previsto"], "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert _chiuso_transitions(session, cid) == []
