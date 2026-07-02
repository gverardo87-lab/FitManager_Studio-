"""G9.2b (ADR-022 Addendum I) — terza penna `post_adjustment` + ledger separato `rettifiche_contratto`.

La penna crea la `RettificaContratto` E applica il delta su `quota_stornata` nello STESSO atto → l'àncora
`quota_stornata == Σ importo[rettifiche]` è vera per costruzione. Non-cash: MAI un `CashMovement`.
DEC-1: NESSUN clamp a 0 nella penna — uno stato che porterebbe la quota sotto zero deve diventare rumoroso
(I4/I1), mai mascherato. Causale fuori-enum → ValueError (fail-loud, parità con post_inflow/post_outflow).
"""

from datetime import date

import pytest
from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.models.rettifica_contratto import (
    CAUSALE_REVERSAL_REOPEN,
    CAUSALE_STORNO_TERMINAZIONE,
    RettificaContratto,
)
from api.services.financial.ledger import post_adjustment

TODAY = date.today()


def _sum_rettifiche(session, contract_id):
    return round(sum(r.importo for r in session.exec(select(RettificaContratto).where(
        RettificaContratto.id_contratto == contract_id,
        RettificaContratto.deleted_at == None)).all()), 2)  # noqa: E711


def test_post_adjustment_rettifica_e_colonna_in_un_atto(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    assert (contract.quota_stornata or 0) == 0
    rett = post_adjustment(session, contract=contract, importo_firmato=450.0,
                           causale=CAUSALE_STORNO_TERMINAZIONE, data_effettiva=TODAY,
                           trainer_id=contract.trainer_id, note="t")
    session.commit()
    session.refresh(contract)
    assert round(contract.quota_stornata, 2) == 450.0
    assert _sum_rettifiche(session, contract.id) == 450.0          # àncora per costruzione
    assert rett.causale == CAUSALE_STORNO_TERMINAZIONE
    assert rett.id_contratto == contract.id


def test_post_adjustment_reversal_append_only(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    post_adjustment(session, contract=contract, importo_firmato=450.0,
                    causale=CAUSALE_STORNO_TERMINAZIONE, data_effettiva=TODAY,
                    trainer_id=contract.trainer_id)
    post_adjustment(session, contract=contract, importo_firmato=-450.0,
                    causale=CAUSALE_REVERSAL_REOPEN, data_effettiva=TODAY,
                    trainer_id=contract.trainer_id)
    session.commit()
    session.refresh(contract)
    assert round(contract.quota_stornata, 2) == 0.0
    assert _sum_rettifiche(session, contract.id) == 0.0
    righe = session.exec(select(RettificaContratto).where(
        RettificaContratto.id_contratto == contract.id)).all()
    assert len(righe) == 2                                          # append-only: reversal = riga nuova, mai UPDATE


def test_post_adjustment_non_cash_zero_movimenti(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    movimenti_pre = len(session.exec(select(CashMovement)).all())
    post_adjustment(session, contract=contract, importo_firmato=100.0,
                    causale=CAUSALE_STORNO_TERMINAZIONE, data_effettiva=TODAY,
                    trainer_id=contract.trainer_id)
    session.commit()
    movimenti_post = len(session.exec(select(CashMovement)).all())
    assert movimenti_post == movimenti_pre                          # lo storno NON tocca il mastro cassa


def test_post_adjustment_no_clamp_sotto_zero(client, auth_headers, sample_contract, session):
    # DEC-1: la penna NON clampa. Un reversal oltre la quota è un BUG del caller che deve restare
    # VISIBILE nella colonna (I4 lo logga; G9.4 lo bloccherà) — un floor qui, ma non sul Σ, romperebbe
    # l'àncora quota == Σ rettifiche. MAI ripristinare un max(·, 0) in post_adjustment.
    contract = session.get(Contract, sample_contract["id"])
    post_adjustment(session, contract=contract, importo_firmato=-100.0,
                    causale=CAUSALE_REVERSAL_REOPEN, data_effettiva=TODAY,
                    trainer_id=contract.trainer_id)
    session.commit()
    session.refresh(contract)
    assert round(contract.quota_stornata, 2) == -100.0              # rumoroso, non mascherato
    assert _sum_rettifiche(session, contract.id) == -100.0          # l'àncora regge anche sullo stato corrotto


def test_post_adjustment_causale_fuori_enum_raises(client, auth_headers, sample_contract, session):
    contract = session.get(Contract, sample_contract["id"])
    with pytest.raises(ValueError):
        post_adjustment(session, contract=contract, importo_firmato=10.0,
                        causale="PAGAMENTO_RATA", data_effettiva=TODAY,
                        trainer_id=contract.trainer_id)
    with pytest.raises(ValueError):
        post_adjustment(session, contract=contract, importo_firmato=10.0,
                        causale="STORNO", data_effettiva=TODAY,
                        trainer_id=contract.trainer_id)
