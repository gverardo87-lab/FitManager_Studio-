"""G9.4-b (ADR-022 D-INVARIANTI-IMPOSTI) — test SEMANTICI che sostituiscono i 4 grep-guard testuali.

Ogni guard di check-all.sh (ADR-016/017/018/019) ha qui il suo gemello che fallisce sullo STESSO
scenario ma sul SIMBOLO/COMPORTAMENTO reale, non su un pattern di testo in bash. Vive nella suite →
gira in CI a ogni run, non solo al quality-gate; ed è immune alla vacuità-da-rilocazione (lezione
G9.3: un grep che punta a un file svuotato passa in silenzio; un test comportamentale no).
I grep-guard sono stati RITIRATI da check-all.sh solo DOPO che questi test sono verdi (SPEC_G9 §G9.4-b).
"""

import inspect
from datetime import date, timedelta

from sqlmodel import select

import api.services.contract_settlement as contract_settlement
from api.models.contract import Contract
from api.models.movement import CashMovement
from api.services.cash_categories import (
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
    CATEGORIA_RIMBORSO_CONTRATTO,
    CONTRACT_CASH_IN,
    is_contract_inflow,
)
from api.services.contract_state import STATI_OCCUPAZIONE_CREDITO

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


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


# ── ADR-016 — barriera euro-da-crediti: il conguaglio è CIECO all'occupazione ──────────────────

def test_adr016_settlement_cieco_all_occupazione():
    """Il modulo puro del conguaglio non referenzia MAI l'asse occupazione/crediti: né i token nel
    sorgente, né simboli Event/occupazione nel namespace. Anti-vacuità inclusa: il modulo deve ancora
    contenere compute_settlement (un rename/rilocazione fallisce qui, non passa in silenzio)."""
    src = inspect.getsource(contract_settlement)
    assert "def compute_settlement" in src            # anti-vacuità (lezione guard G9.3)
    for token in ("crediti_residui", "crediti_usati", "sedute_rinviate", "sedute_prenotate"):
        assert token not in src, f"contract_settlement referenzia l'occupazione: {token}"
    assert not hasattr(contract_settlement, "Event")  # niente import dell'asse eventi
    assert not hasattr(contract_settlement, "STATI_OCCUPAZIONE_CREDITO")


# ── ADR-017 — bidirezionale: Rinviato NON occupa MA resta contato nel breakdown display ────────

def test_adr017_rinviato_fuori_occupazione_ma_nel_breakdown(client, auth_headers, sample_client, session):
    """Lo stesso scenario del grep-guard, sul comportamento: un Rinviato non consuma il credito
    (occupazione) ma alimenta `sedute_rinviate` (display, DISPLAY-EXEMPT §3.2). Se qualcuno
    'armonizza' il GROUP BY all'occupazione, sedute_rinviate va a zero → questo test fallisce."""
    assert "Rinviato" not in STATI_OCCUPAZIONE_CREDITO
    c = _contract(client, auth_headers, sample_client["id"])
    r = client.post("/api/events", json={
        "titolo": "PT", "categoria": "PT", "stato": "Rinviato",
        "id_cliente": sample_client["id"], "id_contratto": c["id"],
        "data_inizio": "2026-01-05T09:00:00", "data_fine": "2026-01-05T10:00:00",
    }, headers=auth_headers)
    assert r.status_code in (200, 201), r.text
    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert detail["sedute_rinviate"] == 1             # display conta il Rinviato
    assert detail["crediti_usati"] == 0               # occupazione NO (il rinvio libera il credito)


# ── ADR-018 — l'incasso di conguaglio è un inflow contrattuale (mai fuori dai ricavi) ──────────

def test_adr018_conguaglio_in_contract_cash_in():
    """Se INCASSO_CONGUAGLIO_CONTRATTO esce da CONTRACT_CASH_IN, `is_contract_inflow` lo perde e il
    conguaglio sparisce silenziosamente dai ricavi — il gemello asserisce il simbolo E il predicato."""
    assert CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO in CONTRACT_CASH_IN
    assert is_contract_inflow(CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO)


# ── ADR-019 — reopen NON-distruttivo: la cassa mossa non si tocca ──────────────────────────────

def test_adr019_reopen_non_cancella_la_cassa(client, auth_headers, sample_client, session):
    """Lo scenario esatto del grep-guard, end-to-end: terminate con rimborso → reopen → la USCITA
    RIMBORSO_CONTRATTO esiste ancora, non soft-cancellata. Se qualcuno reintroduce il delete della
    cassa nel reopen (in QUALUNQUE file — immune alla rilocazione), questo fallisce."""
    c = _contract(client, auth_headers, sample_client["id"], acconto=500.0)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    uscite_pre = session.exec(select(CashMovement).where(
        CashMovement.id_contratto == c["id"], CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None,  # noqa: E711
    )).all()
    assert len(uscite_pre) == 1
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    uscite_post = session.exec(select(CashMovement).where(
        CashMovement.id_contratto == c["id"], CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None,  # noqa: E711
    )).all()
    assert len(uscite_post) == 1                      # la cassa RESTA (fatti datati, ADR-019)
    assert uscite_post[0].id == uscite_pre[0].id
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == round(uscite_post[0].importo, 2)
