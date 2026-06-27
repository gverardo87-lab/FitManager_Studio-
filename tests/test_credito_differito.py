"""
G7.10 (ADR-018) — credito differito post-chiusura: azione A_CREDITO + entità `crediti_terminazione`.

Il credito a favore del trainer SOPRAVVIVE alla chiusura come receivable FUORI da `residuo()`:
- `terminate` A_CREDITO crea il receivable (importo = credito_trainer), storna il dovuto dal contratto
  (residuo()==0) e lo ri-traccia qui — mai una Rate viva su contratto chiuso;
- l'incasso (anche parziale) genera ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO` + `totale_versato +=`;
- `reopen` annulla il receivable e (via C-bis) inverte gli incassi parziali.

Fixture canonica: prezzo 1000, 10 crediti, acconto 100, 4 sedute erogate → R=400, V=100 →
credito_trainer=300, residuo_pre (P−V)=900, quota_non_erogata (P−R)=600.
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.models.event import Event
from api.models.trainer import Trainer
from api.models.credito_terminazione import CreditoTerminazione
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


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


def _complete_pt(session, trainer_id, client_id, contract_id, n):
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i), data_fine=datetime(2026, 1, 1, 10 + i),
        ))
    session.commit()


def _sum_movements(session, contract_id, tipo, categoria=None):
    rows = session.exec(select(CashMovement).where(
        CashMovement.id_contratto == contract_id,
        CashMovement.tipo == tipo,
        CashMovement.deleted_at == None,
    )).all()
    if categoria is not None:
        rows = [m for m in rows if m.categoria == categoria]
    return round(sum(m.importo for m in rows), 2)


def _credito_trainer_contract(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 4)  # R=400 > V=100 → credito_trainer 300
    return c


def _terminate_a_credito(client, auth_headers, contract_id):
    return client.post(f"/api/contracts/{contract_id}/terminate",
                       json={"azione_credito_trainer": "A_CREDITO"}, headers=auth_headers)


# ── AC §10.7-20: A_CREDITO crea il receivable, residuo()==0, zero cassa ──

def test_a_credito_crea_receivable(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    assert _terminate_a_credito(client, auth_headers, c["id"]).status_code == 200

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True
    assert contract.motivo_chiusura == "TERMINAZIONE_SALDO_TRAINER"
    assert round(contract.quota_stornata, 2) == 900.0      # residuo_pre interamente stornato
    assert cstate.residuo(contract) == 0.0                 # il differito NON resta nel contratto
    assert round(contract.totale_versato, 2) == 100.0      # nessuna cassa ora
    assert _sum_movements(session, c["id"], "ENTRATA", categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO) == 0.0

    credito = session.exec(select(CreditoTerminazione).where(
        CreditoTerminazione.id_contratto == c["id"])).first()
    assert credito is not None
    assert round(credito.importo, 2) == 300.0              # == credito_trainer
    assert round(credito.importo_incassato, 2) == 0.0
    assert credito.stato == "APERTO"


def test_a_credito_compare_in_worklist(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    wl = client.get("/api/dashboard/crediti-da-incassare", headers=auth_headers).json()
    assert wl["total"] == 1
    item = wl["items"][0]
    assert item["id_contratto"] == c["id"]
    assert round(item["residuo"], 2) == 300.0
    assert item["giorni_aperto"] == 0


# ── AC §10.7-21: incasso parziale poi a saldo → SALDATO ──

def _credito_id(session, contract_id):
    return session.exec(select(CreditoTerminazione).where(
        CreditoTerminazione.id_contratto == contract_id)).first().id


def test_incassa_credito_parziale_poi_saldo(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    cid = _credito_id(session, c["id"])

    # incasso parziale 200
    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/incassa",
                    json={"importo": 200.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert round(body["importo_incassato"], 2) == 200.0
    assert round(body["residuo"], 2) == 100.0
    assert body["stato"] == "APERTO"

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_versato, 2) == 300.0      # 100 + 200 (Strada B)
    assert cstate.residuo(contract) == 0.0                 # il contratto resta saldato/chiuso
    assert _sum_movements(session, c["id"], "ENTRATA", categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO) == 200.0

    # saldo finale 100 → SALDATO
    r2 = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/incassa",
                     json={"importo": 100.0, "metodo": "POS"}, headers=auth_headers)
    assert r2.status_code == 200, r2.text
    assert r2.json()["stato"] == "SALDATO"
    session.expire_all()
    assert round(session.get(Contract, c["id"]).totale_versato, 2) == 400.0
    # esce dalla worklist (non più APERTO)
    assert client.get("/api/dashboard/crediti-da-incassare", headers=auth_headers).json()["total"] == 0


# ── AC §10.7-22: incasso oltre il residuo del credito → 422 ──

def test_incassa_oltre_residuo_credito_422(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    cid = _credito_id(session, c["id"])
    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/incassa",
                    json={"importo": 400.0, "metodo": "CONTANTI"}, headers=auth_headers)  # > 300
    assert r.status_code == 422, r.text


def test_incassa_credito_annullato_400(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    cid = _credito_id(session, c["id"])
    assert client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/annulla",
                       headers=auth_headers).status_code == 200
    # incasso su un credito ANNULLATO → 400
    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/incassa",
                    json={"importo": 50.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 400, r.text


def test_incassa_bouncer_404(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/999999/incassa",
                    json={"importo": 50.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 404


# ── annulla: il trainer rinuncia al residuo non incassato → ANNULLATO, zero cassa ──

def test_annulla_credito(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    cid = _credito_id(session, c["id"])

    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/annulla", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["stato"] == "ANNULLATO"
    session.expire_all()
    # zero cassa: il dovuto era già stornato al terminate
    assert _sum_movements(session, c["id"], "ENTRATA", categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO) == 0.0
    assert round(session.get(Contract, c["id"]).totale_versato, 2) == 100.0
    # fuori dalla worklist
    assert client.get("/api/dashboard/crediti-da-incassare", headers=auth_headers).json()["total"] == 0


# ── AC §10.7-23: reopen dopo A_CREDITO (con incasso parziale) = round-trip esatto ──

def test_reopen_dopo_a_credito_con_incasso_parziale(client, auth_headers, sample_client, session):
    c = _credito_trainer_contract(client, auth_headers, sample_client, session)
    _terminate_a_credito(client, auth_headers, c["id"])
    cid = _credito_id(session, c["id"])
    # incasso parziale 200 (versato 100→300)
    client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{cid}/incassa",
                json={"importo": 200.0, "metodo": "CONTANTI"}, headers=auth_headers)
    session.expire_all()
    assert round(session.get(Contract, c["id"]).totale_versato, 2) == 300.0

    # reopen → receivable ANNULLATO + incasso parziale invertito (C-bis) + storno azzerato
    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert round(contract.totale_versato, 2) == 100.0          # incasso parziale invertito
    assert round(contract.quota_stornata, 2) == 0.0            # storno azzerato
    assert cstate.residuo(contract) == 900.0                   # residuo pre-terminate ripristinato (P−V)
    assert _sum_movements(session, c["id"], "ENTRATA", categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO) == 0.0

    credito = session.get(CreditoTerminazione, cid)
    assert credito.stato == "ANNULLATO"
    # il receivable annullato non compare più in worklist
    assert client.get("/api/dashboard/crediti-da-incassare", headers=auth_headers).json()["total"] == 0
