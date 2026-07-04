"""G7.8-ter (ADR-023) — Temporal fence: la base del conguaglio è immutabile su contratto liquidato.

Mappa 1:1 sugli AC della SPEC_TEMPORAL_FENCE_EVENTI_LIQUIDATI: su un contratto chiuso NON
auto-riapribile (TERMINAZIONE_*/CONSUNZIONE/NULL) le mutazioni che toccano la base CONTABILIZZATA
(Completato + penali) sono 409; la pulizia dei Programmato orfani resta libera; il varco è reopen;
i chiusi COMPLETAMENTO restano fuori dal fence (auto-reopen simmetrico invariato).
"""

from datetime import date, timedelta


from api.models.contract import Contract
from api.models.event import Event

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()

FENCE_MSG = "conguaglio di chiusura"


def _contract(client, auth_headers, client_id, *, prezzo=1000.0, acconto=100.0, crediti=10):
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


def _event(client, auth_headers, client_id, contract_id, stato, day, hour=9):
    r = client.post("/api/events", json={
        "titolo": "PT", "categoria": "PT", "stato": stato,
        "id_cliente": client_id, "id_contratto": contract_id,
        "data_inizio": f"2026-01-{day:02d}T{hour:02d}:00:00",
        "data_fine": f"2026-01-{day:02d}T{hour + 1:02d}:00:00",
    }, headers=auth_headers)
    assert r.status_code in (200, 201), r.text
    return r.json()


def _terminato(client, auth_headers, sample_client, session, *, con_programmato=False):
    """Contratto liquidato: 4 Completate + 1 No_Show (base contabilizzata 5) su acconto 100 →
    CREDITO_TRAINER → RINUNCIA_ESPRESSA (zero cassa). Opzionale: 1 Programmato orfano pre-terminate."""
    c = _contract(client, auth_headers, sample_client["id"])
    ids = {}
    for i in range(4):
        ev = _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5 + i)
        ids.setdefault("completate", []).append(ev["id"])
    ids["no_show"] = _event(client, auth_headers, sample_client["id"], c["id"], "No_Show", day=10)["id"]
    if con_programmato:
        ids["programmato"] = _event(client, auth_headers, sample_client["id"], c["id"], "Programmato", day=20)["id"]
    r = client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "fence test",
    }, headers=auth_headers)
    assert r.status_code == 200, r.text
    return c, ids


# ── AC-TF-1/2: mutare la base contabilizzata su liquidato → 409 ──────────────

def test_ac_tf1_completato_a_cancellato_409(client, auth_headers, sample_client, session):
    c, ids = _terminato(client, auth_headers, sample_client, session)
    ev_id = ids["completate"][0]
    r = client.put(f"/api/events/{ev_id}", json={"stato": "Cancellato"}, headers=auth_headers)
    assert r.status_code == 409, r.text
    assert FENCE_MSG in r.json()["detail"]
    session.expire_all()
    assert session.get(Event, ev_id).stato == "Completato"          # storia intatta


def test_ac_tf2_no_show_a_cancellato_409(client, auth_headers, sample_client, session):
    c, ids = _terminato(client, auth_headers, sample_client, session)
    r = client.put(f"/api/events/{ids['no_show']}", json={"stato": "Cancellato"}, headers=auth_headers)
    assert r.status_code == 409, r.text
    session.expire_all()
    assert session.get(Event, ids["no_show"]).stato == "No_Show"


def test_ac_tf3_programmato_a_completato_409(client, auth_headers, sample_client, session):
    """Arrivo contabilizzato: non si AGGIUNGE base a liquidazione già fatta."""
    c, ids = _terminato(client, auth_headers, sample_client, session, con_programmato=True)
    r = client.put(f"/api/events/{ids['programmato']}", json={"stato": "Completato"}, headers=auth_headers)
    assert r.status_code == 409, r.text


# ── AC-TF-4: delete — contabilizzato vietato, orfano libero ──────────────────

def test_ac_tf4_delete_contabilizzato_409_orfano_200(client, auth_headers, sample_client, session):
    c, ids = _terminato(client, auth_headers, sample_client, session, con_programmato=True)
    r = client.delete(f"/api/events/{ids['completate'][0]}", headers=auth_headers)
    assert r.status_code == 409, r.text
    r = client.delete(f"/api/events/{ids['programmato']}", headers=auth_headers)
    assert r.status_code in (200, 204), r.text                      # pulizia orfano libera


# ── AC-TF-5: pulizia Programmato orfano libera, contratto resta chiuso ───────

def test_ac_tf5_programmato_a_cancellato_200_resta_chiuso(client, auth_headers, sample_client, session):
    c, ids = _terminato(client, auth_headers, sample_client, session, con_programmato=True)
    r = client.put(f"/api/events/{ids['programmato']}", json={"stato": "Cancellato"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True                                   # reopen-allowlist regge
    assert contract.motivo_chiusura == "TERMINAZIONE_SALDO_TRAINER"


# ── AC-TF-6: chiuso COMPLETAMENTO fuori dal fence (comportamento odierno) ────

def test_ac_tf6_completamento_resta_editabile(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=200.0, acconto=200.0, crediti=2)
    ev1 = _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5)
    ev2 = _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=6)
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True             # auto-close COMPLETAMENTO
    r = client.put(f"/api/events/{ev2['id']}", json={"stato": "Cancellato"}, headers=auth_headers)
    assert r.status_code == 200, r.text                              # fence NON scatta
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is False            # auto-reopen simmetrico invariato
    assert ev1 is not None


# ── AC-TF-7: legacy motivo NULL dentro il fence ──────────────────────────────

def test_ac_tf7_chiuso_legacy_null_fenced(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"])
    ev = _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5)
    contract = session.get(Contract, c["id"])
    contract.chiuso = True
    contract.motivo_chiusura = None                                  # chiusura manuale/legacy
    session.add(contract)
    session.commit()
    r = client.put(f"/api/events/{ev['id']}", json={"stato": "Cancellato"}, headers=auth_headers)
    assert r.status_code == 409, r.text


# ── AC-TF-8: il varco — dopo reopen tutto torna editabile ────────────────────

def test_ac_tf8_reopen_e_il_varco(client, auth_headers, sample_client, session):
    c, ids = _terminato(client, auth_headers, sample_client, session)
    ev_id = ids["completate"][0]
    assert client.put(f"/api/events/{ev_id}", json={"stato": "Cancellato"},
                      headers=auth_headers).status_code == 409
    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200
    r = client.put(f"/api/events/{ev_id}", json={"stato": "Cancellato"}, headers=auth_headers)
    assert r.status_code == 200, r.text                              # varco aperto
    # ri-terminazione: ricalcola sulla storia corretta (3 Completate + 1 No_Show = 4 contabilizzate)
    r = client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "ri-terminazione post-correzione",
    }, headers=auth_headers)
    assert r.status_code == 200, r.text


# ── AC-TF-9: eventi senza contratto mai toccati ──────────────────────────────

def test_ac_tf9_evento_senza_contratto_libero(client, auth_headers, sample_client, session):
    r = client.post("/api/events", json={
        "titolo": "PT libero", "categoria": "PT", "stato": "Completato",
        "id_cliente": sample_client["id"],
        "data_inizio": "2026-01-25T09:00:00", "data_fine": "2026-01-25T10:00:00",
    }, headers=auth_headers)
    assert r.status_code in (200, 201), r.text
    ev = r.json()
    assert client.put(f"/api/events/{ev['id']}", json={"stato": "Cancellato"},
                      headers=auth_headers).status_code == 200


# ── D-TF-PULIZIA: date/titolo/note liberi anche su contabilizzato ────────────

def test_dtf_pulizia_date_titolo_note_liberi(client, auth_headers, sample_client, session):
    c, ids = _terminato(client, auth_headers, sample_client, session)
    ev_id = ids["completate"][0]
    r = client.put(f"/api/events/{ev_id}", json={
        "titolo": "PT (nota corretta)", "note": "orario corretto a posteriori",
        "data_inizio": "2026-01-05T10:00:00", "data_fine": "2026-01-05T11:00:00",
    }, headers=auth_headers)
    assert r.status_code == 200, r.text                              # non tocca la base contabilizzata
