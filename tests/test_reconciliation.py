"""G9.0b (ADR-022) — `/dashboard/reconciliation` BIDIREZIONALE (lato versato + lato rimborso).

Copre AC-G90-2:
- un contratto pulito è allineato (nessuna divergenza);
- una divergenza iniettata su `totale_rimborsato` (senza USCITA RIMBORSO) è RILEVATA in `delta_rimborsi`;
- il wallet erogato RIASSORBITO al reopen (cassa `id_contratto=None`) NON è una falsa divergenza — l'ancora
  I5 raffinata (D1 forma-d) lo copre. Senza il termine `wallet_riassorbito`, questo contratto risulterebbe
  divergente di tutto l'erogato: è il test che prova che il secondo addendo è necessario.
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.trainer import Trainer
from api.models.event import Event

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()
RECON_URL = "/api/dashboard/reconciliation"


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


def _contract(client, auth, client_id, *, prezzo, acconto, crediti):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": TODAY.isoformat(), "data_scadenza": FUTURE,
        "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth)
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


def _wallet(session, contract_id):
    session.expire_all()
    return session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract_id)).first()


def _items(client, auth):
    r = client.get(RECON_URL, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


# ── Baseline: contratto pulito = allineato ──────────────────────────────────

def test_reconciliation_contratto_pulito_allineato(client, auth_headers, sample_client):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    body = _items(client, auth_headers)
    div_ids = [it["contract_id"] for it in body["items"]]
    assert c["id"] not in div_ids   # versato 200 == Σ ENTRATA; rimborsato 0 == 0


# ── AC-G90-2a: divergenza sul lato rimborso rilevata ────────────────────────

def test_reconciliation_rileva_divergenza_rimborso(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    # Inietta totale_rimborsato senza alcuna USCITA RIMBORSO corrispondente (stato impossibile).
    contract = session.get(Contract, c["id"])
    contract.totale_rimborsato = 100.0
    session.add(contract)
    session.commit()
    body = _items(client, auth_headers)
    item = next(it for it in body["items"] if it["contract_id"] == c["id"])
    assert round(item["delta_rimborsi"], 2) == 100.0   # 100 colonna − 0 ledger
    assert round(item["delta"], 2) == 0.0              # lato versato resta allineato


# ── AC-G90-2b: il wallet riassorbito NON è una falsa divergenza ──────────────

def test_reconciliation_wallet_riassorbito_non_divergente(client, auth_headers, sample_client, session):
    """terminate rimborso 0 (wallet 600) → eroga 250 → reopen: totale_rimborsato=250, wallet ANNULLATO con
    erogato 250, NESSUNA USCITA RIMBORSO con id_contratto. L'ancora I5 raffinata (USCITA dirette + erogato
    wallet ANNULLATO) lo copre → NON divergente. Senza il termine wallet_riassorbito sarebbe falso-divergente 250."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)
    wallet = _wallet(session, c["id"])
    client.post(f"/api/clients/{sample_client['id']}/crediti/{wallet.id}/eroga",
                json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == 250.0   # fold R2-bis

    body = _items(client, auth_headers)
    divergenti = [it for it in body["items"] if it["contract_id"] == c["id"]]
    assert divergenti == [], divergenti   # coperto dall'ancora I5 raffinata
