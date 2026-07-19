"""
G9.7.2 — Recupero esplicito degli orfani (ADR-024 D-RECUPERO-ESPLICITO + ADR-019 D-PROPONE).

`POST /events/{id}/assegna-contratto` è l'UNICA via di re-parenting per i PT orfani
(l'`EventUpdate` generico resta chiuso su `id_contratto` — fence ADR-023 intatto).
Copre gli acceptance criteria di SPEC_G9.7 §G9.7.2:
- AC-G97-2   orfano assegnato → occupa il credito; rifiuta contratto chiuso (400) e
             cliente diverso (404); rifiuta re-parenting (400) e non-PT (400); credit-guard.
- AC-G97-2b  reopen-preview e response di reopen NOMINANO gli orfani nati nel periodo
             di chiusura (propongono, MAI riagganciano da soli).
- B6         worklist /dashboard/orphan-events: count == len(items), porta l'azione
             (contratti aperti del cliente); alert `orphan_events` coerente.
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.event import Event
from api.models.trainer import Trainer

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


def _contract(client, auth_headers, client_id, *, prezzo=1000.0, acconto=0.0, crediti=10):
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


def _orphan(session, trainer_id, client_id, *, stato="Programmato", hour0=8, categoria="PT"):
    """Inserisce via ORM un evento ORFANO (id_contratto=NULL) e ritorna l'id."""
    e = Event(
        trainer_id=trainer_id, id_cliente=client_id, id_contratto=None,
        categoria=categoria, stato=stato, titolo="Seduta orfana",
        data_inizio=datetime(2026, 1, 2, hour0), data_fine=datetime(2026, 1, 2, hour0 + 1),
    )
    session.add(e)
    session.commit()
    session.refresh(e)
    return e.id


def _second_client(client, auth_headers):
    r = client.post("/api/clients", json={
        "nome": "Altro", "cognome": "Cliente", "telefono": "3391112223",
        "email": "altro.cliente@example.com", "stato": "Attivo",
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


# ── AC-G97-2: assegnazione felice + guard chain ──

def test_assegna_orfano_occupa_credito(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=10)
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"], stato="Programmato")

    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["id_contratto"] == c["id"]

    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["crediti_usati"] == 1          # l'orfano assegnato ORA occupa


def test_assegna_rifiuta_contratto_chiuso(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=2)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"note": "test G9.7.2"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"])

    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_assegna_rifiuta_cliente_diverso_404(client, auth_headers, sample_client, session):
    altro = _second_client(client, auth_headers)
    c_altro = _contract(client, auth_headers, altro["id"], crediti=5)
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"])

    # Il contratto esiste ed è mio, ma è di un ALTRO cliente → 404 (mai rivelare)
    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c_altro["id"]}, headers=auth_headers)
    assert r.status_code == 404


def test_assegna_rifiuta_reparenting(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=10)
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"])
    ok = client.post(f"/api/events/{eid}/assegna-contratto",
                     json={"id_contratto": c["id"]}, headers=auth_headers)
    assert ok.status_code == 200

    # Già agganciato: la via resta chiusa (fence — solo orfani)
    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 400


def test_assegna_rifiuta_non_pt(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=10)
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"], categoria="COLLOQUIO")

    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 400


def test_assegna_credit_guard(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=1)
    t = _trainer(session)
    # Il credito unico è già occupato da una seduta agganciata
    session.add(Event(
        trainer_id=t.id, id_cliente=sample_client["id"], id_contratto=c["id"],
        categoria="PT", stato="Completato", titolo="Occupa",
        data_inizio=datetime(2026, 1, 3, 8), data_fine=datetime(2026, 1, 3, 9),
    ))
    session.commit()
    eid = _orphan(session, t.id, sample_client["id"], hour0=10)

    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 400
    assert "crediti esauriti" in r.json()["detail"].lower()


def test_assegna_rinviato_non_soggetto_a_credit_guard(client, auth_headers, sample_client, session):
    """Un orfano RINVIATO non occupa credito (ADR-017) → assegnabile anche a contratto pieno."""
    c = _contract(client, auth_headers, sample_client["id"], crediti=1, acconto=0.0)
    t = _trainer(session)
    session.add(Event(
        trainer_id=t.id, id_cliente=sample_client["id"], id_contratto=c["id"],
        categoria="PT", stato="Programmato", titolo="Occupa",
        data_inizio=datetime(2026, 1, 3, 8), data_fine=datetime(2026, 1, 3, 9),
    ))
    session.commit()
    eid = _orphan(session, t.id, sample_client["id"], stato="Rinviato", hour0=10)

    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 200, r.text
    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["crediti_usati"] == 1          # il Rinviato non conta


def test_assegna_ultimo_credito_su_saldato_autoclose(client, auth_headers, sample_client, session):
    """Composizione con auto-close (regola #4): assegnare l'orfano che riempie l'ultimo credito
    di un contratto SALDATO → il contratto si chiude da solo (via _sync_contract_chiuso)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"], stato="Completato")

    r = client.post(f"/api/events/{eid}/assegna-contratto",
                    json={"id_contratto": c["id"]}, headers=auth_headers)
    assert r.status_code == 200, r.text
    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["chiuso"] is True              # SALDATO + crediti pieni → auto-close


# ── AC-G97-2b: reopen PROPONE gli orfani del periodo di chiusura ──

def test_reopen_preview_e_response_nominano_orfani(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=5)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"note": "test orfani periodo"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    # Orfano nato DOPO la chiusura (data_creazione = now ≥ data_chiusura = oggi)
    t = _trainer(session)
    eid = _orphan(session, t.id, sample_client["id"], stato="Completato")

    prev = client.get(f"/api/contracts/{c['id']}/reopen-preview", headers=auth_headers)
    assert prev.status_code == 200, prev.text
    body = prev.json()
    ids = [o["id"] for o in body["orfani_periodo_chiusura"]]
    assert eid in ids                        # il preview li NOMINA
    assert "senza contratto" in body["messaggio"]

    rr = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert rr.status_code == 200, rr.text
    rbody = rr.json()
    assert eid in [o["id"] for o in rbody["orfani_periodo_chiusura"]]
    # PROPONE, non riaggancia: l'evento resta orfano
    ev = client.get(f"/api/events/{eid}", headers=auth_headers).json()
    assert ev["id_contratto"] is None


# ── B6: worklist + alert coerenti ──

def test_orphan_worklist_delega_ssot_e_clampa_sovraoccupato(
    client, auth_headers, sample_client, session, monkeypatch,
):
    """R1.3: dati legacy sovra-occupati non producono residui negativi nella worklist azionabile.

    Il conteggio passa dal batch helper canonico e il residuo da `cstate.crediti_residui`: la worklist
    non mantiene un secondo interprete dell'asse occupazione e resta coerente con gli altri read-model.
    """
    from api.routers import dashboard as dashboard_router

    c = _contract(client, auth_headers, sample_client["id"], crediti=1)
    t = _trainer(session)
    for hour in (8, 10):
        session.add(Event(
            trainer_id=t.id, id_cliente=sample_client["id"], id_contratto=c["id"],
            categoria="PT", stato="Completato", titolo="Occupazione legacy",
            data_inizio=datetime(2026, 1, 3, hour), data_fine=datetime(2026, 1, 3, hour + 1),
        ))
    session.commit()
    orphan_id = _orphan(session, t.id, sample_client["id"], hour0=12)

    original = dashboard_router._crediti_usati_map
    calls: list[tuple[int, ...]] = []

    def _spy_crediti_usati_map(db_session, contract_ids):
        calls.append(tuple(contract_ids))
        return original(db_session, contract_ids)

    monkeypatch.setattr(dashboard_router, "_crediti_usati_map", _spy_crediti_usati_map)

    response = client.get("/api/dashboard/orphan-events", headers=auth_headers)
    assert response.status_code == 200, response.text
    orphan_row = next(item for item in response.json()["items"] if item["id"] == orphan_id)
    contract_row = next(item for item in orphan_row["contratti_aperti"] if item["id"] == c["id"])
    assert contract_row["crediti_residui"] == 0       # 1 totale - 2 usati, clamp SSoT
    assert len(calls) == 1 and c["id"] in calls[0]    # una delega batch, nessun interprete locale


def test_orphan_events_worklist_e_alert(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], crediti=10)
    t = _trainer(session)
    _orphan(session, t.id, sample_client["id"], stato="Programmato", hour0=8)
    _orphan(session, t.id, sample_client["id"], stato="Completato", hour0=10)
    _orphan(session, t.id, sample_client["id"], stato="Rinviato", hour0=12)   # NON in worklist

    w = client.get("/api/dashboard/orphan-events", headers=auth_headers)
    assert w.status_code == 200, w.text
    body = w.json()
    assert body["total"] == 2 == len(body["items"])
    # Ogni riga porta l'azione: i contratti aperti del cliente con crediti residui
    row = body["items"][0]
    aperto = next(x for x in row["contratti_aperti"] if x["id"] == c["id"])
    assert aperto["crediti_residui"] == 10

    alerts = client.get("/api/dashboard/alerts", headers=auth_headers).json()
    orphan_alert = next(a for a in alerts["items"] if a["category"] == "orphan_events")
    assert orphan_alert["count"] == 2        # stesso helper → count == len(items)
