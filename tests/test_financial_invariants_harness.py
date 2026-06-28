"""
PASSO 3 (G8.2-prep) — Harness di proprietà: invariante × transizione × stato di partenza.

NON è il test del singolo bug: è la **rete strutturale** che chiude la CLASSE. Enumera le transizioni
finanziarie (terminate nei suoi rami, reopen, incassa_residuo, pay/unpay, eroga_wallet, incassa_receivable)
e, per ogni stato di partenza rilevante, verifica `cstate.assert_contract_invariants()` DOPO la transizione.

Costruito per fallire OGGI sul caso `eroga_wallet_then_reopen` (Bug-1 dell'audit: il wallet erogato
spariva dalla posizione alla riapertura) e tornare verde dopo il PASSO 4 (reopen ricalcola dalla
fotografia netta). Tutti gli altri scenari sono già verdi (sono corretti).

Riferimento: docs/technical/AUDIT_POSIZIONE_FINANZIARIA_E_INVARIANTI_2026-06-28.md (I1/I4/I5),
docs/technical/SPEC_INTEGRITA_CONTABILE_E_WALLET.md (blocco G8.2).
"""

from datetime import date, datetime, timedelta

import pytest
from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.models.event import Event
from api.models.trainer import Trainer
from api.models.credito_cliente import CreditoCliente
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_RIMBORSO_CONTRATTO

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


# ── Helpers di setup ────────────────────────────────────────────────

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


def _rate(client, auth_headers, contract_id, importo):
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _wallet(session, contract_id):
    return session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract_id)).first()


def _invariants(session, contract_id):
    """Calcola le violazioni d'invariante per un contratto, con l'ancora ledger forte di I5
    (`rimborso_cassa_diretto` = Σ USCITA RIMBORSO_CONTRATTO con id_contratto == contract_id)."""
    session.expire_all()
    contract = session.get(Contract, contract_id)
    crediti = session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract_id)).all()
    rimborso_diretto = round(sum(m.importo for m in session.exec(select(CashMovement).where(
        CashMovement.id_contratto == contract_id,
        CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None,
    )).all()), 2)
    return cstate.assert_contract_invariants(contract, crediti, rimborso_cassa_diretto=rimborso_diretto)


# ── Scenari (ogni builder applica UNA transizione e ritorna il contract_id) ──────────

def sc_terminate_rimborso_pieno(client, auth_headers, sample_client, session):
    """CREDITO_CLIENTE, rimborso pieno → nessun wallet, residuo 0."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)  # reso 200 → credito 600
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    return c["id"]


def sc_terminate_rimborso_parziale(client, auth_headers, sample_client, session):
    """CREDITO_CLIENTE, rimborso parziale → wallet APERTO del non-rimborsato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"importo_rimborso": 400.0, "metodo_rimborso": "BONIFICO"}, headers=auth_headers)
    return c["id"]


def sc_terminate_rimborso_zero(client, auth_headers, sample_client, session):
    """CREDITO_CLIENTE, rimborso 0 → tutto a wallet APERTO."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)
    return c["id"]


def sc_terminate_trainer_incassa(client, auth_headers, sample_client, session):
    """CREDITO_TRAINER, INCASSA_ORA → totale_versato cresce."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 8)  # reso 800 → credito_trainer 300
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"azione_credito_trainer": "INCASSA_ORA", "metodo_pagamento": "CONTANTI"},
                headers=auth_headers)
    return c["id"]


def sc_terminate_trainer_rinuncia(client, auth_headers, sample_client, session):
    """CREDITO_TRAINER, RINUNCIA_ESPRESSA → storno-only, nessuna cassa."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)  # reso 200 > 100 → credito_trainer
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "rinuncio"}, headers=auth_headers)
    return c["id"]


def sc_terminate_pari(client, auth_headers, sample_client, session):
    """PARI (reso == versato) → CONSUNZIONE, storno del residuo."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)  # reso 200 == versato
    client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    return c["id"]


def sc_incassa_residuo(client, auth_headers, sample_client, session):
    """G6: incasso diretto del residuo su un contratto aperto (funziona su qualsiasi aperto con residuo>0)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=0.0, crediti=10)
    r = client.post(f"/api/contracts/{c['id']}/incassa-residuo",
                    json={"importo": 200.0, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()},
                    headers=auth_headers)
    assert r.status_code == 200, r.text
    return c["id"]


def sc_pay_then_unpay(client, auth_headers, sample_client, session):
    """pay_rate → unpay_rate (la posizione torna a PENDENTE)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    rata = _rate(client, auth_headers, c["id"], 400.0)
    client.post(f"/api/rates/{rata['id']}/pay", json={"importo": 400.0, "metodo": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/rates/{rata['id']}/unpay", headers=auth_headers)
    return c["id"]


def sc_eroga_wallet_no_reopen(client, auth_headers, sample_client, session):
    """terminate rimborso 0 (wallet 600) → eroga 250 (wallet APERTO). Contratto resta chiuso.
    Invarianti reggono: il wallet APERTO è una passività propria, non un euro 'perso' dal contratto."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)
    session.expire_all()
    wallet = _wallet(session, c["id"])
    client.post(f"/api/clients/{sample_client['id']}/crediti/{wallet.id}/eroga",
                json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)
    return c["id"]


def sc_reopen_no_wallet(client, auth_headers, sample_client, session):
    """terminate con rimborso pieno (no wallet) → reopen. La cassa resta, residuo ricalcolato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    return c["id"]


def sc_eroga_wallet_then_reopen(client, auth_headers, sample_client, session):
    """🐞 Bug-1 (CANARY): terminate rimborso 0 (wallet 600) → eroga 250 → reopen. Il wallet erogato
    (250, USCITA id_contratto=None) deve RIENTRARE nella posizione del contratto riaperto.
    Rosso OGGI (I5: totale_rimborsato 0 ma 250 riassorbiti) → verde dopo il PASSO 4 (fold net-aware)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)
    session.expire_all()
    wallet = _wallet(session, c["id"])
    client.post(f"/api/clients/{sample_client['id']}/crediti/{wallet.id}/eroga",
                json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    return c["id"]


SCENARIOS = [
    ("terminate_rimborso_pieno", sc_terminate_rimborso_pieno),
    ("terminate_rimborso_parziale", sc_terminate_rimborso_parziale),
    ("terminate_rimborso_zero", sc_terminate_rimborso_zero),
    ("terminate_trainer_incassa", sc_terminate_trainer_incassa),
    ("terminate_trainer_rinuncia", sc_terminate_trainer_rinuncia),
    ("terminate_pari", sc_terminate_pari),
    ("incassa_residuo", sc_incassa_residuo),
    ("pay_then_unpay", sc_pay_then_unpay),
    ("eroga_wallet_no_reopen", sc_eroga_wallet_no_reopen),
    ("reopen_no_wallet", sc_reopen_no_wallet),
    ("eroga_wallet_then_reopen", sc_eroga_wallet_then_reopen),  # 🐞 Bug-1 — rosso finché non c'è il PASSO 4
]


@pytest.mark.parametrize("name,build", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_invariants_hold_after_transition(name, build, client, auth_headers, sample_client, session):
    """Per ogni transizione finanziaria, gli invarianti I1/I4/I5 reggono DOPO la transizione."""
    contract_id = build(client, auth_headers, sample_client, session)
    violations = _invariants(session, contract_id)
    assert violations == [], f"[{name}] violazioni: {[(v.code, v.message) for v in violations]}"
