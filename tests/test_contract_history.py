"""
G8.1.1 / F6 — Storico stato/attività del contratto: `GET /contracts/{id}/history`.

Timeline CRM-grade derivata (curata) dall'`audit_log` (entity='contract'). Copre:
- ordine cronologico + tipi curati (creato → terminato → riaperto)
- dedup delle entry "companion" (la transizione lifecycle bare NON duplica la entry ricca)
- completamento (auto-close) → evento `saldato`
- la pura cassa (pagamento intermedio) NON inquina la timeline di stato (vive in F1/F5)
- bouncer: contratto inesistente/non-proprio → 404
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.trainer import Trainer
from api.models.event import Event

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": TODAY.isoformat(),
        "data_scadenza": FUTURE, "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _complete_pt(session, trainer_id, client_id, contract_id, n):
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i), data_fine=datetime(2026, 1, 1, 10 + i),
        ))
    session.commit()


def _history(client, auth_headers, contract_id):
    r = client.get(f"/api/contracts/{contract_id}/history", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


# ── Creazione → sempre il primo evento ──────────────────────────────

def test_history_creazione(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=100.0, crediti=10)
    events = _history(client, auth_headers, c["id"])
    assert len(events) >= 1
    assert events[0]["tipo"] == "creato"
    assert events[0]["titolo"] == "Contratto creato"


# ── Terminazione: entry ricca + dedup della companion lifecycle ──────

def test_history_terminazione_ricca_senza_companion(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200

    rt = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert rt.status_code == 200, rt.text

    events = _history(client, auth_headers, c["id"])
    terminati = [e for e in events if e["tipo"] == "terminato"]
    assert len(terminati) == 1, events                       # entry ricca UNICA
    assert "motivo" in terminati[0]["dettaglio"]
    # la companion lifecycle bare (chiuso+motivo='terminazione') NON deve comparire come 'stato'
    stati_chiuso = [e for e in events if e["tipo"] == "stato" and "chius" in e["titolo"].lower()]
    assert stati_chiuso == [], events


# ── Round-trip terminate → reopen: ordine + tipi, companion deduplicate ──

def test_history_terminate_reopen_ordine(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)

    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)

    events = _history(client, auth_headers, c["id"])
    tipi = [e["tipo"] for e in events]
    assert tipi[0] == "creato"
    assert "terminato" in tipi
    assert "riaperto" in tipi
    # ordine cronologico: creato prima di terminato prima di riaperto
    assert tipi.index("creato") < tipi.index("terminato") < tipi.index("riaperto")
    # esattamente UN terminato e UN riaperto (nessuna companion duplicante)
    assert tipi.count("terminato") == 1, events
    assert tipi.count("riaperto") == 1, events


# ── Completamento (auto-close) → evento `saldato` ───────────────────

def test_history_completamento_saldato(client, auth_headers, sample_client, session):
    # acconto pieno + consuma l'unico credito → auto-close COMPLETAMENTO
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T09:00:00",
        "data_fine": f"{TODAY.isoformat()}T09:30:00",
        "categoria": "PT", "titolo": "Seduta",
        "id_cliente": sample_client["id"], "id_contratto": c["id"],
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True

    events = _history(client, auth_headers, c["id"])
    assert any(e["tipo"] == "saldato" for e in events), events


# ── La pura cassa NON inquina la timeline di stato ──────────────────

def test_history_pagamento_intermedio_non_inquina(client, auth_headers, sample_client, session):
    """Un incasso residuo che NON chiude (crediti residui) muove solo cassa → niente evento di stato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=100.0, crediti=10)
    # incassa parte del residuo senza chiudere (restano crediti) → solo cassa
    r = client.post(f"/api/contracts/{c['id']}/incassa-residuo",
                    json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    events = _history(client, auth_headers, c["id"])
    # niente "saldato"/"terminato"/"riaperto"; resta solo la creazione (la cassa è in F1/F5)
    assert [e["tipo"] for e in events] == ["creato"], events


# ── Bouncer: contratto inesistente → 404 ────────────────────────────

def test_history_contratto_inesistente_404(client, auth_headers):
    r = client.get("/api/contracts/999999/history", headers=auth_headers)
    assert r.status_code == 404
