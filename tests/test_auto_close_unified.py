"""G9.3c/d (ADR-022) — FSM di chiusura esplicita + auto-close UNIFICATO `sync_contract_chiuso`.

AC-G93-3: payment-driven (pay_rate) e credit-driven (agenda) convergono su UN solo percorso logico —
a parità di condizioni producono lo stesso stato terminale (chiuso=True, COMPLETAMENTO). La direzione
permessa è policy del trigger (D-C6); la reopen-allowlist G7.2 vive nel predicato `puo_auto_riaprire`.
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.event import Event
from api.models.trainer import Trainer
from api.services.financial.transitions import puo_auto_riaprire, sync_contract_chiuso

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _contract(client, auth_headers, client_id, *, prezzo=400.0, acconto=0.0, crediti=2):
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


def _pay_full(client, auth_headers, contract_id, importo):
    rata = client.post("/api/rates", json={
        "id_contratto": contract_id, "data_scadenza": FUTURE, "importo_previsto": importo,
    }, headers=auth_headers).json()
    r = client.post(f"/api/rates/{rata['id']}/pay",
                    json={"importo": importo, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    return rata


def _event_completato(client, auth_headers, client_id, contract_id, hour):
    r = client.post("/api/events", json={
        "titolo": "PT", "categoria": "PT", "stato": "Completato",
        "id_cliente": client_id, "id_contratto": contract_id,
        "data_inizio": f"2026-01-01T{hour:02d}:00:00", "data_fine": f"2026-01-01T{hour + 1:02d}:00:00",
    }, headers=auth_headers)
    assert r.status_code in (200, 201), r.text


def test_ac_g93_3_payment_e_credit_driven_stesso_stato_terminale(client, auth_headers, sample_client, session):
    """Stesse condizioni (saldato + crediti esauriti), trigger diversi → STESSO stato terminale."""
    # A) payment-driven: prima esaurisce i crediti (non chiude: non saldato), poi l'ultimo euro chiude
    ca = _contract(client, auth_headers, sample_client["id"])
    _event_completato(client, auth_headers, sample_client["id"], ca["id"], 9)
    _event_completato(client, auth_headers, sample_client["id"], ca["id"], 11)
    session.expire_all()
    assert session.get(Contract, ca["id"]).chiuso is False       # crediti esauriti ma non saldato
    _pay_full(client, auth_headers, ca["id"], 400.0)             # → chiude via pay_rate

    # B) credit-driven: prima salda (non chiude: crediti residui), poi l'ultima seduta chiude
    cb = _contract(client, auth_headers, sample_client["id"])
    _pay_full(client, auth_headers, cb["id"], 400.0)
    session.expire_all()
    assert session.get(Contract, cb["id"]).chiuso is False       # saldato ma crediti residui
    _event_completato(client, auth_headers, sample_client["id"], cb["id"], 14)
    _event_completato(client, auth_headers, sample_client["id"], cb["id"], 16)  # → chiude via agenda

    session.expire_all()
    a, b = session.get(Contract, ca["id"]), session.get(Contract, cb["id"])
    assert (a.chiuso, a.motivo_chiusura) == (b.chiuso, b.motivo_chiusura) == (True, "COMPLETAMENTO")


def test_unpay_auto_reopen_via_transizione_unificata(client, auth_headers, sample_client, session):
    """Il reopen payment-driven passa dalla transizione unificata (motivo riapertura_pagamento)."""
    c = _contract(client, auth_headers, sample_client["id"])
    _event_completato(client, auth_headers, sample_client["id"], c["id"], 9)
    _event_completato(client, auth_headers, sample_client["id"], c["id"], 11)
    rata = _pay_full(client, auth_headers, c["id"], 400.0)
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True
    r = client.post(f"/api/rates/{rata['id']}/unpay", headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False and contract.motivo_chiusura is None  # FSM riga 2 → APERTO


def test_direzione_close_bloccata_su_trigger_reopen(client, auth_headers, sample_client, session):
    """D-C6: stato da-chiudere + directions solo-reopen → NON chiude (la direzione è policy del trigger)."""
    c = _contract(client, auth_headers, sample_client["id"])
    _event_completato(client, auth_headers, sample_client["id"], c["id"], 9)
    _event_completato(client, auth_headers, sample_client["id"], c["id"], 11)
    contract = session.get(Contract, c["id"])
    contract.totale_versato = 400.0
    contract.stato_pagamento = "SALDATO"
    contract.chiuso = False
    session.add(contract)
    session.commit()
    sync_contract_chiuso(session, c["id"], directions=frozenset({"reopen"}))
    session.commit()
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is False


def test_direzione_reopen_bloccata_su_trigger_close(client, auth_headers, sample_client, session):
    """D-C6: chiuso COMPLETAMENTO non più saldato + directions solo-close → NON riapre."""
    c = _contract(client, auth_headers, sample_client["id"])
    contract = session.get(Contract, c["id"])
    contract.chiuso = True
    contract.motivo_chiusura = "COMPLETAMENTO"
    contract.stato_pagamento = "PARZIALE"
    session.add(contract)
    session.commit()
    sync_contract_chiuso(session, c["id"], directions=frozenset({"close"}))
    session.commit()
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True


def test_fsm_riga3_terminazione_non_si_auto_riapre(client, auth_headers, sample_client, session):
    """FSM riga 3: chiusura TERMINAZIONE_* — l'auto-reopen bidirezionale NON scatta (allowlist G7.2)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    trainer = session.exec(select(Trainer)).first()
    for i in range(2):
        session.add(Event(
            trainer_id=trainer.id, id_cliente=sample_client["id"], id_contratto=c["id"],
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 2, 9 + i), data_fine=datetime(2026, 1, 2, 10 + i),
        ))
    session.commit()
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True and puo_auto_riaprire(contract) is False
    sync_contract_chiuso(session, c["id"])                       # bidirezionale, come agenda
    session.commit()
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True                               # VIETATO: resta chiuso
    assert contract.motivo_chiusura == "TERMINAZIONE_RIMBORSO"


def test_puo_auto_riaprire_predicato(client, auth_headers, sample_client, session):
    """Allowlist POSITIVA: solo COMPLETAMENTO; NULL (manuale/legacy) e TERMINAZIONE_* vietati."""
    c = _contract(client, auth_headers, sample_client["id"])
    contract = session.get(Contract, c["id"])
    contract.motivo_chiusura = "COMPLETAMENTO"
    assert puo_auto_riaprire(contract) is True
    for motivo in (None, "TERMINAZIONE_RIMBORSO", "TERMINAZIONE_SALDO_TRAINER", "CONSUNZIONE"):
        contract.motivo_chiusura = motivo
        assert puo_auto_riaprire(contract) is False, motivo
