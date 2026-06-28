"""
G8.1 (ADR-020) — wallet del cliente: rimborso editabile + entità `crediti_cliente`.

Ramo CREDITO_CLIENTE della terminazione: il rimborso è EDITABILE [0, credito_cliente] (default pieno).
Il non-rimborsato NON si perde → diventa un credito a wallet del cliente (RIMBORSO_DIFFERITO), FUORI dal
`residuo()`. `reopen` annulla il wallet di quella terminazione (le erogazioni parziali, Step 4, restano).

Fixture canonica: prezzo 1000, 10 crediti, acconto 800, 2 sedute erogate → reso 200, credito_cliente 600,
residuo_pre (P−V) 200.
"""

from datetime import date, datetime, timedelta

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


def _credito_cliente_contract(client, auth_headers, sample_client, session):
    """prezzo 1000, acconto 800, 2 sedute → reso 200 < versato 800 → credito_cliente 600."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)
    return c


def _wallet(session, contract_id):
    return session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract_id)).first()


def _sum_movements_client(session, client_id, tipo, categoria):
    """Somma per id_cliente (l'erogazione wallet ha id_contratto=None → non la prende _sum_movements)."""
    rows = session.exec(select(CashMovement).where(
        CashMovement.id_cliente == client_id,
        CashMovement.tipo == tipo,
        CashMovement.categoria == categoria,
        CashMovement.deleted_at == None,
    )).all()
    return round(sum(m.importo for m in rows), 2)


# ── AC-9: rimborso pieno (default) → nessun wallet, residuo 0, netto == reso ──

def test_rimborso_pieno_nessun_wallet(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)  # default = pieno (600)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.motivo_chiusura == "TERMINAZIONE_RIMBORSO"
    assert round(contract.totale_rimborsato, 2) == 600.0
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == 600.0
    assert cstate.residuo(contract) == 0.0
    assert cstate.netto_incassato(contract) == 200.0          # versato 800 − rimborsato 600 == reso
    assert _wallet(session, c["id"]) is None                  # nessun credito a wallet


# ── AC-10: rimborso parziale → wallet del non-rimborsato, residuo 0 ──

def test_rimborso_parziale_crea_wallet(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"importo_rimborso": 400.0, "metodo_rimborso": "BONIFICO"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == 400.0
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == 400.0
    assert cstate.residuo(contract) == 0.0                    # storno = residuo_pre 200 + rimborso 400 = 600
    wallet = _wallet(session, c["id"])
    assert wallet is not None
    assert round(wallet.importo, 2) == 200.0                  # 600 − 400, NON perso
    assert wallet.stato == "APERTO"
    assert wallet.causale == "RIMBORSO_DIFFERITO"
    assert round(wallet.importo_erogato, 2) == 0.0


# ── AC-11: rimborso zero → tutto a wallet, nessuna USCITA, metodo non richiesto ──

def test_rimborso_zero_tutto_a_wallet(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"importo_rimborso": 0.0}, headers=auth_headers)  # metodo NON richiesto
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == 0.0
    assert _sum_movements(session, c["id"], "USCITA") == 0.0   # nessuna cassa
    assert cstate.residuo(contract) == 0.0
    wallet = _wallet(session, c["id"])
    assert round(wallet.importo, 2) == 600.0                  # tutto il credito a wallet
    assert wallet.stato == "APERTO"


# ── AC-12: rimborso oltre il credito del cliente → 422 ──

def test_rimborso_oltre_credito_422(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"importo_rimborso": 700.0, "metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 422, r.text
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is False     # zero scritture


# ── AC-6 (§9.2): reopen annulla il wallet della terminazione, residuo ricalcolato ──

def test_reopen_annulla_wallet(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    # rimborso 0 → wallet pieno (600)
    assert client.post(f"/api/contracts/{c['id']}/terminate",
                       json={"importo_rimborso": 0.0}, headers=auth_headers).status_code == 200
    session.expire_all()
    assert _wallet(session, c["id"]).stato == "APERTO"

    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert _wallet(session, c["id"]).stato == "ANNULLATO"      # R4
    assert round(contract.quota_stornata, 2) == 0.0
    assert round(contract.totale_versato, 2) == 800.0         # invariato (nessuna cassa mossa)
    assert round(contract.totale_rimborsato, 2) == 0.0
    assert cstate.residuo(contract) == 200.0                  # P − netto = 1000 − 800 (riassorbe il credito)


# ── AC-13: eroga (parziale → saldo) del wallet in cassa + cap 422 ──

def test_eroga_wallet_parziale_poi_saldo(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)
    session.expire_all()
    wallet = _wallet(session, c["id"])
    cid = sample_client["id"]

    # erogazione parziale 250 (di 600)
    r = client.post(f"/api/clients/{cid}/crediti/{wallet.id}/eroga",
                    json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert round(body["importo_erogato"], 2) == 250.0
    assert round(body["residuo"], 2) == 350.0
    assert body["stato"] == "APERTO"
    # USCITA RIMBORSO_CONTRATTO creata (id_contratto=None → conta per cliente, non per contratto)
    assert _sum_movements_client(session, cid, "USCITA", CATEGORIA_RIMBORSO_CONTRATTO) == 250.0
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == 0.0        # il contratto NON è toccato (id_contratto=None)
    assert cstate.residuo(contract) == 0.0                    # resta saldato

    # saldo finale 350 → SALDATO
    r2 = client.post(f"/api/clients/{cid}/crediti/{wallet.id}/eroga",
                     json={"importo": 350.0, "metodo": "BONIFICO"}, headers=auth_headers)
    assert r2.status_code == 200, r2.text
    assert r2.json()["stato"] == "SALDATO"
    # esce dalla worklist
    assert client.get("/api/dashboard/rimborsi-da-erogare", headers=auth_headers).json()["total"] == 0


def test_eroga_oltre_residuo_422(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)
    session.expire_all()
    wallet = _wallet(session, c["id"])
    r = client.post(f"/api/clients/{sample_client['id']}/crediti/{wallet.id}/eroga",
                    json={"importo": 700.0, "metodo": "CONTANTI"}, headers=auth_headers)  # > 600
    assert r.status_code == 422, r.text


# ── AC-14: worklist rimborsi-da-erogare + lista crediti del cliente ──

def test_worklist_rimborsi_da_erogare(client, auth_headers, sample_client, session):
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"importo_rimborso": 0.0}, headers=auth_headers)

    wl = client.get("/api/dashboard/rimborsi-da-erogare", headers=auth_headers).json()
    assert wl["total"] == 1
    item = wl["items"][0]
    assert item["id_cliente"] == sample_client["id"]
    assert round(item["residuo"], 2) == 600.0
    assert item["causale"] == "RIMBORSO_DIFFERITO"
    assert item["giorni_aperto"] == 0

    # lista crediti del cliente (profilo)
    crediti = client.get(f"/api/clients/{sample_client['id']}/crediti", headers=auth_headers).json()
    assert len(crediti) == 1
    assert crediti[0]["stato"] == "APERTO"
    assert round(crediti[0]["residuo"], 2) == 600.0


# ── F1/AC-8: l'erogazione wallet (id_contratto=None) NON entra nei movimenti del contratto ──

def test_f1_eroga_wallet_non_in_movimenti_contratto(client, auth_headers, sample_client, session):
    """La cassa dell'erogazione wallet è a livello CLIENTE (id_contratto=None, ADR-020) → lo storico
    cassa del contratto (F1) NON la mostra: Σ-con-segno dei movimenti contratto resta == netto del
    contratto, immune all'erogazione."""
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    cid = sample_client["id"]
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"importo_rimborso": 0.0}, headers=auth_headers)   # wallet 600, zero cassa contratto
    session.expire_all()
    wallet = _wallet(session, c["id"])
    client.post(f"/api/clients/{cid}/crediti/{wallet.id}/eroga",
                json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)  # USCITA client-level

    movimenti = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()["movimenti"]
    # niente USCITA nel contratto (l'erogazione è altrove) → solo l'acconto ENTRATA 800
    assert all(m["tipo"] == "ENTRATA" for m in movimenti), movimenti
    assert CATEGORIA_RIMBORSO_CONTRATTO not in {m["categoria"] for m in movimenti}
    signed = round(sum(m["importo"] for m in movimenti), 2)
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert signed == round(contract.totale_versato, 2) == 800.0   # immune all'erogazione wallet


# ── Bug-4 (G8.2-prep): le delete RESTRICT sulla posizione-cliente aperta (wallet/receivable) ──

def test_delete_client_bloccato_da_wallet_aperto(client, auth_headers, sample_client, session):
    """delete_client → 400 se il cliente ha un wallet APERTO (gli devi denaro), anche SENZA contratti
    attivi (il contratto terminato è chiuso). La posizione FUORI da residuo() non va orfanata."""
    c = _credito_cliente_contract(client, auth_headers, sample_client, session)
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"importo_rimborso": 0.0}, headers=auth_headers)   # wallet 600 APERTO, contratto chiuso
    r = client.delete(f"/api/clients/{sample_client['id']}", headers=auth_headers)
    assert r.status_code == 400
    assert "posizione finanziaria" in r.json()["detail"].lower()


def test_delete_contract_bloccato_da_receivable_aperto(client, auth_headers, sample_client, session):
    """delete_contract (no force) → 409 se il contratto ha un credito differito APERTO (A_CREDITO):
    crediti tutti usati (RESTRICT 2 passa), nessuna rata (RESTRICT 1 passa) → solo la nuova RESTRICT 3
    sui crediti aperti blocca. Senza, il receivable resterebbe orfano (Bug-4 dell'audit)."""
    from api.models.credito_terminazione import CreditoTerminazione
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 10)  # reso 1000 → credito_trainer 900
    rt = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"azione_credito_trainer": "A_CREDITO"}, headers=auth_headers)
    assert rt.status_code == 200, rt.text
    assert session.exec(select(CreditoTerminazione).where(
        CreditoTerminazione.id_contratto == c["id"])).first().stato == "APERTO"

    r = client.delete(f"/api/contracts/{c['id']}", headers=auth_headers)
    assert r.status_code == 409
    assert "crediti aperti" in r.json()["detail"].lower()
