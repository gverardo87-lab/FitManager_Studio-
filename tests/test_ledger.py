"""G9.1 (ADR-022) — penna unica del libro mastro `post_inflow` / `post_outflow`.

La penna crea il `CashMovement` E applica il delta-colonna nello STESSO atto → I5 vero per costruzione.
post_outflow con `contract=None` (erogazione wallet) crea il movimento senza toccare colonne. Categoria
fuori asse → ValueError (fail-loud).
"""

from datetime import date, timedelta

import pytest
from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.services.cash_categories import CATEGORIA_PAGAMENTO_RATA, CATEGORIA_RIMBORSO_CONTRATTO
from api.services.financial.ledger import post_inflow, post_outflow

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _sum(session, contract_id, tipo):
    return round(sum(m.importo for m in session.exec(select(CashMovement).where(
        CashMovement.id_contratto == contract_id, CashMovement.tipo == tipo,
        CashMovement.deleted_at == None)).all()), 2)  # noqa: E711


def test_post_inflow_movimento_e_colonna_in_un_atto(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    v0 = contract.totale_versato or 0   # 200 (acconto)
    post_inflow(session, contract=contract, importo=150.0, categoria=CATEGORIA_PAGAMENTO_RATA,
                metodo="CONTANTI", data_effettiva=TODAY, trainer_id=contract.trainer_id,
                id_cliente=contract.id_cliente, note="t")
    session.commit()
    session.refresh(contract)
    assert round(contract.totale_versato, 2) == round(v0 + 150.0, 2)
    assert _sum(session, contract.id, "ENTRATA") == round(contract.totale_versato, 2)  # I5 per costruzione


def test_post_outflow_con_contratto_tocca_rimborsato(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    r0 = contract.totale_rimborsato or 0
    post_outflow(session, contract=contract, importo=80.0, categoria=CATEGORIA_RIMBORSO_CONTRATTO,
                 metodo="BONIFICO", data_effettiva=TODAY, trainer_id=contract.trainer_id,
                 id_cliente=contract.id_cliente, note="t")
    session.commit()
    session.refresh(contract)
    assert round(contract.totale_rimborsato, 2) == round(r0 + 80.0, 2)
    assert _sum(session, contract.id, "USCITA") == round(contract.totale_rimborsato, 2)


def test_post_outflow_senza_contratto_non_tocca_colonne(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    r0 = contract.totale_rimborsato or 0
    mv = post_outflow(session, contract=None, importo=50.0, categoria=CATEGORIA_RIMBORSO_CONTRATTO,
                      metodo="CONTANTI", data_effettiva=TODAY, trainer_id=contract.trainer_id,
                      id_cliente=contract.id_cliente, note="wallet")
    session.commit()
    session.refresh(contract)
    assert mv.id_contratto is None                                  # cassa a livello cliente
    assert round(contract.totale_rimborsato, 2) == round(r0, 2)     # colonna del contratto intatta


def test_post_inflow_categoria_sbagliata_raises(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    with pytest.raises(ValueError):
        post_inflow(session, contract=contract, importo=10.0, categoria=CATEGORIA_RIMBORSO_CONTRATTO,
                    metodo="CONTANTI", data_effettiva=TODAY, trainer_id=contract.trainer_id,
                    id_cliente=contract.id_cliente, note="x")


def test_post_outflow_categoria_sbagliata_raises(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    with pytest.raises(ValueError):
        post_outflow(session, contract=contract, importo=10.0, categoria=CATEGORIA_PAGAMENTO_RATA,
                     metodo="CONTANTI", data_effettiva=TODAY, trainer_id=contract.trainer_id,
                     id_cliente=contract.id_cliente, note="x")


# ── G9.1c: acconto di create_contract / renew via penna (I5 by-construction alla nascita) ──

def _create(client, auth, client_id, *, prezzo, acconto):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "X", "crediti_totali": 10,
        "prezzo_totale": prezzo, "data_inizio": TODAY.isoformat(), "data_scadenza": FUTURE,
        "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_g91c_create_acconto_i5_e_stato_parziale(client, auth_headers, sample_client, session):
    c = _create(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0)
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_versato, 2) == 200.0
    assert contract.stato_pagamento == "PARZIALE"            # dal SSoT recompute (4ª copia inline collassata)
    assert _sum(session, c["id"], "ENTRATA") == 200.0        # I5 per costruzione (acconto via penna)


def test_g91c_create_acconto_pieno_saldato(client, auth_headers, sample_client, session):
    c = _create(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=1000.0)
    contract = session.get(Contract, c["id"])
    assert contract.stato_pagamento == "SALDATO"
    assert _sum(session, c["id"], "ENTRATA") == round(contract.totale_versato, 2) == 1000.0


def test_g91c_create_senza_acconto_pendente_zero_movimenti(client, auth_headers, sample_client, session):
    c = _create(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0)
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_versato, 2) == 0.0
    assert contract.stato_pagamento == "PENDENTE"
    assert _sum(session, c["id"], "ENTRATA") == 0.0          # nessun movimento acconto


def test_g91c_renew_acconto_i5(client, auth_headers, sample_contract, session):
    r = client.post(f"/api/contracts/{sample_contract['id']}/renew", json={
        "id_cliente": sample_contract["id_cliente"], "tipo_pacchetto": "Rinnovo", "crediti_totali": 10,
        "prezzo_totale": 800.0, "data_inizio": TODAY.isoformat(), "data_scadenza": FUTURE,
        "acconto": 300.0, "metodo_acconto": "POS",
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    contract = session.get(Contract, r.json()["id"])
    assert round(contract.totale_versato, 2) == 300.0
    assert contract.stato_pagamento == "PARZIALE"
    assert _sum(session, contract.id, "ENTRATA") == 300.0    # I5 anche sul rinnovo
