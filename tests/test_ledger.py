"""G9.1 (ADR-022) — penna unica del libro mastro `post_inflow` / `post_outflow`.

La penna crea il `CashMovement` E applica il delta-colonna nello STESSO atto → I5 vero per costruzione.
post_outflow con `contract=None` (erogazione wallet) crea il movimento senza toccare colonne. Categoria
fuori asse → ValueError (fail-loud).
"""

from datetime import date

import pytest
from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.services.cash_categories import CATEGORIA_PAGAMENTO_RATA, CATEGORIA_RIMBORSO_CONTRATTO
from api.services.financial.ledger import post_inflow, post_outflow

TODAY = date.today()


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
