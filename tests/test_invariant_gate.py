"""G9.0a (ADR-022) — sensore osservabile degli invarianti (`invariant_gate.log_invariant_violations`).

Copre AC-G90-1:
- **Totalità**: il sensore NON solleva su un contratto normale (è la garanzia che sostituisce il
  `try/except`); su uno stato pulito non logga nulla.
- **Osservazione**: su una violazione iniettata logga un warning col codice invariante, senza sollevare.
- **Wiring**: il sensore è invocato (log-only) in coda a TUTTE le 6 transizioni denaro + reopen — un
  monkeypatch-spy prova che nessun aggancio è stato dimenticato (il fallimento che G9.0 deve evitare).
- **Reperto #1** (SPEC_G9 §A.3): `incassa_credito_terminazione` accende I1 (residuo_raw<0) perché
  `quota_stornata` assorbì `residuo_pre` al terminate A_CREDITO e non si riduce all'incasso del receivable.
  Documentato come `xfail(strict=True)`: rosso ORA (log-only, fix differito), tripwire quando verrà risolto.
"""

import logging
from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.credito_terminazione import CreditoTerminazione
from api.models.event import Event
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.trainer import Trainer
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_RIMBORSO_CONTRATTO
from api.services.financial.invariant_gate import log_invariant_violations

GATE_LOGGER = "api.services.financial.invariant_gate"
TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


# ── Helpers (mirror dell'harness invarianti) ────────────────────────────────

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


def _rate(client, auth, contract_id, importo):
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
        "importo_previsto": importo,
    }, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def _wallet(session, contract_id):
    session.expire_all()
    return session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract_id)).first()


def _receivable(session, contract_id):
    session.expire_all()
    return session.exec(select(CreditoTerminazione).where(
        CreditoTerminazione.id_contratto == contract_id)).first()


def _invariants(session, contract_id):
    """Violazioni d'invariante per un contratto (ancora ledger forte di I5 + rate attive per I6)."""
    session.expire_all()
    contract = session.get(Contract, contract_id)
    crediti = session.exec(select(CreditoCliente).where(
        CreditoCliente.id_contratto_origine == contract_id)).all()
    rimborso_diretto = round(sum(m.importo for m in session.exec(select(CashMovement).where(
        CashMovement.id_contratto == contract_id,
        CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None,  # noqa: E711
    )).all()), 2)
    rate_attive = session.exec(select(Rate).where(
        Rate.id_contratto == contract_id, Rate.deleted_at == None)).all()  # noqa: E711
    return cstate.assert_contract_invariants(
        contract, crediti, rimborso_cassa_diretto=rimborso_diretto, rate_attive=rate_attive)


def _spy(monkeypatch, module):
    """Sostituisce il sensore nel router `module` con uno spy che registra i `motivo`."""
    calls = []
    monkeypatch.setattr(
        f"api.routers.{module}.log_invariant_violations",
        lambda session, contract, *, motivo: calls.append(motivo),
    )
    return calls


# ── Totalità + osservazione (unit, AC-G90-1) ────────────────────────────────

def test_sensor_total_e_silenzioso_su_contratto_pulito(client, auth_headers, sample_client, session, caplog):
    """Il sensore NON solleva su un contratto normale e non logga nulla (garanzia anti-try/except)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    contract = session.get(Contract, c["id"])
    with caplog.at_level(logging.WARNING, logger=GATE_LOGGER):
        log_invariant_violations(session, contract, motivo="test")  # non deve sollevare
    assert [r for r in caplog.records if r.name == GATE_LOGGER] == []


def test_sensor_logga_violazione_iniettata_senza_sollevare(client, auth_headers, sample_client, session, caplog):
    """Stato impossibile iniettato (chiuso COMPLETAMENTO con residuo>0) → warning I1, nessuna eccezione."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    contract = session.get(Contract, c["id"])
    contract.chiuso = True                       # residuo 800 ≠ 0 su un chiuso COMPLETAMENTO → I1
    contract.motivo_chiusura = "COMPLETAMENTO"
    session.add(contract)
    session.commit()
    with caplog.at_level(logging.WARNING, logger=GATE_LOGGER):
        log_invariant_violations(session, contract, motivo="test")
    assert "I1" in caplog.text, caplog.text


# ── Wiring: il sensore è invocato in ogni transizione denaro (AC-G90-1) ──────

def test_wiring_pay_rate(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "rates")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    rata = _rate(client, auth_headers, c["id"], 400.0)
    r = client.post(f"/api/rates/{rata['id']}/pay",
                    json={"importo": 400.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "pagamento" in calls


def test_wiring_unpay_rate(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "rates")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    rata = _rate(client, auth_headers, c["id"], 400.0)
    client.post(f"/api/rates/{rata['id']}/pay",
                json={"importo": 400.0, "metodo": "CONTANTI"}, headers=auth_headers)
    r = client.post(f"/api/rates/{rata['id']}/unpay", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "revoca_pagamento" in calls


def test_wiring_incassa_residuo(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "contracts")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=0.0, crediti=10)
    r = client.post(f"/api/contracts/{c['id']}/incassa-residuo",
                    json={"importo": 200.0, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()},
                    headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "incassa_residuo" in calls


def test_wiring_terminate(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "contracts")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)  # reso 200 < versato → rimborso
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "terminazione" in calls


def test_wiring_reopen(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "contracts")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "reopen" in calls


def test_wiring_eroga_wallet(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "clients")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=800.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 2)  # reso 200 < 800 → CREDITO_CLIENTE
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"importo_rimborso": 0.0}, headers=auth_headers)  # tutto a wallet
    wallet = _wallet(session, c["id"])
    r = client.post(f"/api/clients/{sample_client['id']}/crediti/{wallet.id}/eroga",
                    json={"importo": 250.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "eroga_wallet" in calls


def test_wiring_incassa_credito_differito(client, auth_headers, sample_client, session, monkeypatch):
    calls = _spy(monkeypatch, "contracts")
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 8)  # reso 800 > 500 → CREDITO_TRAINER
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"azione_credito_trainer": "A_CREDITO"}, headers=auth_headers)
    rec = _receivable(session, c["id"])
    r = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{rec.id}/incassa",
                    json={"importo": 300.0, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()},
                    headers=auth_headers)
    assert r.status_code == 200, r.text
    assert "incassa_credito_differito" in calls


# ── Reperto #1: I1 atteso su incassa_credito_terminazione (log-only, fix differito) ──

def test_reperto1_fix_incassa_credito_differito_invarianti_ok(client, auth_headers, sample_client, session):
    """Reperto #1 RISOLTO (mini-blocco G9.0): `incassa_credito_terminazione` REVERTE lo storno provvisorio
    (`quota_stornata −= importo`) → `residuo_raw==0`, I1 non scatta più. Era `xfail(strict)`; ora passa.
    Verifica anche che `quota_stornata` converge a `quota_non_erogata` (P−R) e `residuo()==0` resta."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, _trainer(session).id, sample_client["id"], c["id"], 8)  # reso 800 → credito_trainer 300
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"azione_credito_trainer": "A_CREDITO"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    rec = _receivable(session, c["id"])
    r2 = client.post(f"/api/contracts/{c['id']}/crediti-terminazione/{rec.id}/incassa",
                     json={"importo": 300.0, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()},
                     headers=auth_headers)
    assert r2.status_code == 200, r2.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    # residuo_pre=500 stornato al terminate; incassati 300 → quota torna a quota_non_erogata = P−R = 200
    assert round(contract.quota_stornata, 2) == 200.0
    assert cstate.residuo(contract) == 0.0
    viol = _invariants(session, c["id"])
    assert viol == [], f"violazioni: {[(v.code, v.message) for v in viol]}"


# ── G9.2-a: il sensore osserva anche l'ancora ledger-VERSATO (totale_versato == Σ ENTRATA) ──

def test_g92a_sensore_logga_drift_versato_vs_ledger(client, auth_headers, sample_client, session, caplog):
    """Contratto penna-scritto: versato == Σ ENTRATA (nessun log). Drift artificiale → warning ledger-versato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    contract = session.get(Contract, c["id"])
    with caplog.at_level(logging.WARNING, logger=GATE_LOGGER):
        log_invariant_violations(session, contract, motivo="baseline")
    assert "ledger-versato" not in caplog.text   # by-construction: versato == Σ ENTRATA

    contract.totale_versato = (contract.totale_versato or 0) + 50.0   # drift fuori-penna
    session.add(contract)
    session.commit()
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=GATE_LOGGER):
        log_invariant_violations(session, contract, motivo="dopo_drift")
    assert "ledger-versato" in caplog.text, caplog.text


# ── G9.2b Stage 2: il sensore osserva anche l'ancora ledger-STORNO (quota_stornata == Σ rettifiche) ──

def test_g92b_sensore_logga_drift_storno_vs_ledger(client, auth_headers, sample_client, session, caplog):
    """Storno penna-scritto: quota == Σ rettifiche (nessun log). Drift a mano → warning ledger-storno."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    # 0 sedute erogate → esito CREDITO_CLIENTE (200): terminazione con rimborso pieno.
    # Storno via terza penna = residuo_pre (800) + rimborso_out (200) = 1000.
    r = client.post(f"/api/contracts/{c['id']}/terminate", json={
        "metodo_rimborso": "CONTANTI",
    }, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    with caplog.at_level(logging.WARNING, logger=GATE_LOGGER):
        log_invariant_violations(session, contract, motivo="baseline")
    assert "ledger-storno" not in caplog.text   # by-construction: quota == Σ rettifiche (terza penna)

    contract.quota_stornata = (contract.quota_stornata or 0) + 50.0   # write fuori-penna (drift)
    session.add(contract)
    session.commit()
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger=GATE_LOGGER):
        log_invariant_violations(session, contract, motivo="dopo_drift")
    assert "ledger-storno" in caplog.text, caplog.text
