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


# ── G9.2b.4 — wiring dei 3 write-site: l'ancora quota == Σ rettifiche regge su ogni transizione ──

from datetime import datetime, timedelta

from api.models.event import Event
from api.models.trainer import Trainer
from api.models.credito_terminazione import CreditoTerminazione
from api.models.rettifica_contratto import (
    CAUSALE_REVERSAL_INCASSO_DIFFERITO,
)
from api.services import contract_state as cstate

FUTURE = (TODAY + timedelta(days=120)).isoformat()


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


def _complete_pt(session, client_id, contract_id, n):
    trainer = session.exec(select(Trainer)).first()
    for i in range(n):
        session.add(Event(
            trainer_id=trainer.id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i), data_fine=datetime(2026, 1, 1, 10 + i),
        ))
    session.commit()


def _assert_ancora(session, contract_id):
    """quota_stornata == Σ importo[rettifiche] — la legge di G9.2b, ad ogni passo."""
    session.expire_all()
    contract = session.get(Contract, contract_id)
    assert round(contract.quota_stornata or 0, 2) == _sum_rettifiche(session, contract_id)
    return contract


def _causali(session, contract_id):
    return [r.causale for r in session.exec(select(RettificaContratto).where(
        RettificaContratto.id_contratto == contract_id).order_by(RettificaContratto.id)).all()]


def test_wiring_terminate_storno_via_penna(client, auth_headers, sample_client, session):
    """terminate (RINUNCIA, zero cassa): 1 riga STORNO_TERMINAZIONE = residuo_pre; residuo()==0."""
    c = _contract(client, auth_headers, sample_client["id"])          # P=1000, V=100
    _complete_pt(session, sample_client["id"], c["id"], 4)            # R=400 → credito_trainer 300
    r = client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "rinuncia test",
    }, headers=auth_headers)
    assert r.status_code == 200, r.text
    contract = _assert_ancora(session, c["id"])
    assert round(contract.quota_stornata, 2) == 900.0                 # residuo_pre (P−V), zero cassa
    assert _causali(session, c["id"]) == [CAUSALE_STORNO_TERMINAZIONE]
    assert round(cstate.residuo(contract), 2) == 0.0


def test_wiring_reopen_reversal_append_only(client, auth_headers, sample_client, session):
    """terminate → reopen: 2 righe (+X, −X), quota == Σ == 0 (mai UPDATE, mai delete)."""
    c = _contract(client, auth_headers, sample_client["id"])
    _complete_pt(session, sample_client["id"], c["id"], 4)
    client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "x",
    }, headers=auth_headers)
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200, r.text
    contract = _assert_ancora(session, c["id"])
    assert round(contract.quota_stornata, 2) == 0.0
    assert _causali(session, c["id"]) == [CAUSALE_STORNO_TERMINAZIONE, CAUSALE_REVERSAL_REOPEN]


def test_wiring_incassa_credito_differito_reversal(client, auth_headers, sample_client, session):
    """A_CREDITO → incassa parziale: riga −importo (Reperto #1 senza clamp); residuo()==0 tenuto."""
    c = _contract(client, auth_headers, sample_client["id"])
    _complete_pt(session, sample_client["id"], c["id"], 4)            # credito_trainer 300
    client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "A_CREDITO",
    }, headers=auth_headers)
    credito = session.exec(select(CreditoTerminazione).where(
        CreditoTerminazione.id_contratto == c["id"])).first()
    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{credito.id}/incassa",
                    json={"importo": 200.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    contract = _assert_ancora(session, c["id"])
    assert round(contract.quota_stornata, 2) == 700.0                 # 900 − 200 (storno provvisorio revertito)
    assert _causali(session, c["id"]) == [
        CAUSALE_STORNO_TERMINAZIONE, CAUSALE_REVERSAL_INCASSO_DIFFERITO]
    assert round(cstate.residuo(contract), 2) == 0.0                  # +versato e −quota si compensano


def test_wiring_sequenza_terminate_incassa_reopen(client, auth_headers, sample_client, session):
    """AC-G92-4: sequenza composta — Σ == colonna ad OGNI passo, ledger append-only completo."""
    c = _contract(client, auth_headers, sample_client["id"])
    _complete_pt(session, sample_client["id"], c["id"], 4)
    client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "A_CREDITO",
    }, headers=auth_headers)
    _assert_ancora(session, c["id"])                                  # +900
    credito = session.exec(select(CreditoTerminazione).where(
        CreditoTerminazione.id_contratto == c["id"])).first()
    client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{credito.id}/incassa",
                json={"importo": 300.0, "metodo": "CONTANTI"}, headers=auth_headers)
    contract = _assert_ancora(session, c["id"])                       # 900 − 300 = 600
    assert round(contract.quota_stornata, 2) == 600.0
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200, r.text
    contract = _assert_ancora(session, c["id"])                       # −600 → 0
    assert round(contract.quota_stornata, 2) == 0.0
    assert _causali(session, c["id"]) == [
        CAUSALE_STORNO_TERMINAZIONE, CAUSALE_REVERSAL_INCASSO_DIFFERITO, CAUSALE_REVERSAL_REOPEN]
    assert contract.chiuso is False


def test_wiring_terminate_reopen_ri_terminate(client, auth_headers, sample_client, session):
    """AC-G92-4: terminate → reopen → ri-terminate — l'ancora regge, 3 righe cumulative."""
    c = _contract(client, auth_headers, sample_client["id"])
    _complete_pt(session, sample_client["id"], c["id"], 4)
    payload = {"azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "x"}
    assert client.post(f"/api/contracts/{c['id']}/terminate", json=payload,
                       headers=auth_headers).status_code == 200
    _assert_ancora(session, c["id"])
    assert client.post(f"/api/contracts/{c['id']}/reopen",
                       headers=auth_headers).status_code == 200
    _assert_ancora(session, c["id"])
    assert client.post(f"/api/contracts/{c['id']}/terminate", json=payload,
                       headers=auth_headers).status_code == 200
    contract = _assert_ancora(session, c["id"])
    assert round(contract.quota_stornata, 2) == 900.0                 # stato identico al 1° terminate
    assert len(_causali(session, c["id"])) == 3                       # +900, −900, +900 (append-only)
    assert round(cstate.residuo(contract), 2) == 0.0


# ── G9.2b Stage 2 — project_columns_from_ledger espone anche lo storno (Σ rettifiche) ──

def test_stage2_project_columns_stornato(client, auth_headers, sample_client, session):
    """La proiezione deriva quota_stornata dal ledger rettifiche: colonna == proiezione ad ogni passo."""
    from api.services.financial.ledger import project_columns_from_ledger
    c = _contract(client, auth_headers, sample_client["id"])
    _complete_pt(session, sample_client["id"], c["id"], 4)
    client.post(f"/api/contracts/{c['id']}/terminate", json={
        "azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "x",
    }, headers=auth_headers)
    session.expire_all()
    contract = session.get(Contract, c["id"])
    proj = project_columns_from_ledger(session, c["id"])
    assert proj["stornato"] == round(contract.quota_stornata, 2) == 900.0
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200
    session.expire_all()
    contract = session.get(Contract, c["id"])
    proj = project_columns_from_ledger(session, c["id"])
    assert proj["stornato"] == round(contract.quota_stornata, 2) == 0.0
