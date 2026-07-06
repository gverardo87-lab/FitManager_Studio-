"""
G8.4 F1.b — `saldo_progressivo` servito dal backend su `ContractMovementItem` (ADR-019 Addendum IV,
D-LEDGER-SALDO): il saldo riga-per-riga del sotto-libro contratto (ENTRATA +, USCITA −, ordine
`data_effettiva, id`) lo calcola `get_contract`; il frontend LEGGE, mai accumula (R-SSOT-FE).

Copre (AC-G84-2):
- ogni riga porta il running balance cumulativo; l'ultima riga riconcilia con la Σ firmata delle righe
- una USCITA (rimborso) fa scendere il saldo; senza wallet riassorbito, ultimo saldo == netto_incassato
- dopo reopen con wallet EROGATO riassorbito, ultimo saldo_progressivo ≠ netto_incassato — divergenza
  LEGITTIMA (le USCITA di erogazione wallet hanno `id_contratto=None` e NON sono nel sotto-libro),
  entrambi coerenti con la propria definizione. È il motivo per cui il ledger si etichetta «Saldo».
"""

from sqlmodel import select

from api.models.credito_cliente import CreditoCliente
from tests.test_contract_reopen import _complete_pt, _contract, _rate, _trainer


def _movimenti(client, auth_headers, contract_id):
    r = client.get(f"/api/contracts/{contract_id}", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_saldo_progressivo_reconciles_rows(client, auth_headers, sample_client):
    """Acconto + pagamento rata: saldi cumulativi [300, 800]; footer == Σ firmata == netto (zero rimborsi)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=300.0, crediti=10)
    rata = _rate(client, auth_headers, c["id"], 500.0)
    r = client.post(f"/api/rates/{rata['id']}/pay", json={"importo": 500.0, "metodo": "CONTANTI"},
                    headers=auth_headers)
    assert r.status_code == 200, r.text

    detail = _movimenti(client, auth_headers, c["id"])
    saldi = [m["saldo_progressivo"] for m in detail["movimenti"]]
    assert saldi == [300.0, 800.0]
    # il footer (ultima riga) riconcilia con la somma firmata delle righe mostrate
    somma_firmata = round(sum(m["importo"] if m["tipo"] == "ENTRATA" else -m["importo"]
                              for m in detail["movimenti"]), 2)
    assert saldi[-1] == somma_firmata
    # senza rimborsi né wallet, saldo-LEDGER e netto-POSIZIONE coincidono
    assert saldi[-1] == detail["netto_incassato"] == 800.0


def test_saldo_progressivo_con_rimborso(client, auth_headers, sample_client, session):
    """La USCITA di rimborso fa SCENDERE il saldo (convenzione del mastro); ultimo saldo == netto."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 < versato 800 → credito 600

    # terminate col rimborso pieno di default (600) → ENTRATA 800 poi USCITA 600
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    detail = _movimenti(client, auth_headers, c["id"])
    saldi = [m["saldo_progressivo"] for m in detail["movimenti"]]
    assert saldi == [800.0, 200.0]
    assert detail["movimenti"][1]["tipo"] == "USCITA"
    # rimborso DIRETTO (id_contratto set) → il sotto-libro lo vede: saldo == netto anche qui
    assert saldi[-1] == detail["netto_incassato"] == 200.0


def test_saldo_progressivo_diverge_da_netto_dopo_reopen_wallet(client, auth_headers, sample_client, session):
    """AC-G84-2: wallet erogato (USCITA id_contratto=None) + reopen R2-bis → i due numeri DIVERGONO
    legittimamente: saldo-LEDGER 800 (solo righe del contratto), netto-POSIZIONE 550 (riassorbito 250)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)

    # terminate rimborso 0 → wallet 600; eroga 250 (cassa a livello cliente); reopen riassorbe
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0},
                headers=auth_headers)
    session.expire_all()
    wallet = session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == c["id"])).first()
    client.post(f"/api/clients/{sample_client['id']}/crediti/{wallet.id}/eroga",
                json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200

    detail = _movimenti(client, auth_headers, c["id"])
    # il sotto-libro contiene SOLO l'acconto: l'erogazione wallet è id_contratto=None
    assert [m["saldo_progressivo"] for m in detail["movimenti"]] == [800.0]
    assert detail["netto_incassato"] == 550.0  # 800 − 250 riassorbiti (R2-bis)
    # entrambi coerenti con la propria definizione: la differenza è ESATTAMENTE l'erogato riassorbito
    assert round(detail["movimenti"][-1]["saldo_progressivo"] - detail["netto_incassato"], 2) == 250.0
