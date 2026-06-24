"""
G6 (Blocco 4) — incasso residuo diretto: POST /contracts/{id}/incassa-residuo.

Prima cassa ENTRATA legata al contratto SENZA passare da una rata. Gemello in entrata
del rimborso da terminazione (G7). Mirror di test_pay_rate + test_lifecycle_audit.

Invarianti verificate:
- ENTRATA nel libro mastro con `id_contratto` set e `id_rata` None (incasso diretto).
- `totale_versato` cresce (Strada B, LORDO); `stato_pagamento` ricalcolato.
- Auto-close canonico (date-independent): saldato + crediti esauriti → chiuso.
- NESSUN auto-close se restano crediti (caso SOSPESO saldato con sedute residue).
- Cap anti-overpayment (422), residuo già saldato (400), contratto chiuso (400), IDOR (404).
- Audit della transizione `chiuso` loggato UNA volta (no doppio log con _sync_contract_chiuso).
"""

import json
from datetime import date, timedelta

from sqlmodel import select

from api.models.audit_log import AuditLog

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()
PAST_START = (TODAY - timedelta(days=60)).isoformat()
PAST_END = (TODAY - timedelta(days=10)).isoformat()


# ── helpers (stile test_lifecycle_audit, date-robusti) ─────────────


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti, inizio=None, scadenza=FUTURE):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": inizio or TODAY.isoformat(), "data_scadenza": scadenza,
        "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _pt_event(client, auth_headers, client_id, contract_id, hour=9):
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T{hour:02d}:00:00",
        "data_fine": f"{TODAY.isoformat()}T{hour:02d}:30:00",
        "categoria": "PT",
        "titolo": "Seduta",
        "id_cliente": client_id,
        "id_contratto": contract_id,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _chiuso_transitions(session, contract_id):
    """Audit entry sul contratto che toccano `chiuso` (mirror test_lifecycle_audit)."""
    session.expire_all()
    rows = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "contract",
            AuditLog.entity_id == contract_id,
        )
    ).all()
    return [json.loads(r.changes) for r in rows if r.changes and "chiuso" in json.loads(r.changes)]


def _incassa(client, auth_headers, contract_id, importo, **extra):
    payload = {"importo": importo, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()}
    payload.update(extra)
    return client.post(f"/api/contracts/{contract_id}/incassa-residuo", json=payload, headers=auth_headers)


# ── happy path ─────────────────────────────────────────────────────


def test_incassa_residuo_partial(client, auth_headers, sample_contract):
    """Incasso parziale del residuo: totale_versato cresce, stato PARZIALE."""
    # sample_contract: prezzo 1000, acconto 200 → residuo 800
    r = _incassa(client, auth_headers, sample_contract["id"], 300.0)
    assert r.status_code == 200, r.text
    assert r.json()["totale_versato"] == 500.0
    assert r.json()["stato_pagamento"] == "PARZIALE"
    assert r.json()["chiuso"] is False


def test_incassa_residuo_full_saldato(client, auth_headers, sample_contract):
    """Incasso dell'intero residuo: contratto SALDATO."""
    r = _incassa(client, auth_headers, sample_contract["id"], 800.0)
    assert r.status_code == 200, r.text
    assert r.json()["totale_versato"] == 1000.0
    assert r.json()["stato_pagamento"] == "SALDATO"


def test_incassa_residuo_creates_cash_movement(client, auth_headers, sample_client):
    """Crea un CashMovement ENTRATA legato al contratto con id_rata None (incasso diretto)."""
    # acconto 0 → l'unico movimento contrattuale sarà l'incasso (niente movimento acconto)
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=10)
    r = _incassa(client, auth_headers, c["id"], 100.0)
    assert r.status_code == 200, r.text

    mr = client.get(f"/api/movements?anno={TODAY.year}&mese={TODAY.month}", headers=auth_headers)
    contract_movs = [m for m in mr.json()["items"] if m.get("id_contratto") == c["id"]]
    assert len(contract_movs) == 1
    mov = contract_movs[0]
    assert mov["tipo"] == "ENTRATA"
    assert mov["importo"] == 100.0
    assert mov.get("id_rata") is None  # incasso diretto, NON legato a una rata
    # categoria load-bearing: PAGAMENTO_RATA ∈ CONTRACT_CASH_IN (cash_categories) → conta come
    # incasso contrattuale nei KPI/financial-trend. Un refactor verso una OUT (es. RIMBORSO) NON
    # cambierebbe tipo=ENTRATA → senza questa asserzione passerebbe muto corrompendo la classificazione.
    assert mov["categoria"] == "PAGAMENTO_RATA"


def test_incassa_residuo_totale_versato_reconciles_ledger(client, auth_headers, sample_client):
    """totale_versato == acconto + incasso (Strada B, LORDO) E il ledger combacia:
    Σ ENTRATA del contratto == totale_versato (chiude il loop contratto↔libro mastro)."""
    # contratto fresco con acconto OGGI → acconto e incasso cadono nello stesso mese (query ledger)
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    r = _incassa(client, auth_headers, c["id"], 500.0)
    assert r.status_code == 200, r.text
    assert r.json()["totale_versato"] == 700.0  # acconto 200 + incasso 500

    mr = client.get(f"/api/movements?anno={TODAY.year}&mese={TODAY.month}", headers=auth_headers)
    entrate = [
        m["importo"] for m in mr.json()["items"]
        if m.get("id_contratto") == c["id"] and m["tipo"] == "ENTRATA"
    ]
    assert sum(entrate) == 700.0 == r.json()["totale_versato"]


# ── boundary auto-close (date-independent, credit-driven) ──────────


def test_incassa_residuo_autoclose_on_last_credit(client, auth_headers, sample_client):
    """BOUNDARY: incasso dell'ultimo residuo su contratto a crediti esauriti → chiuso=True."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])  # consuma l'unico credito

    r = _incassa(client, auth_headers, c["id"], 100.0)
    assert r.status_code == 200, r.text
    assert r.json()["stato_pagamento"] == "SALDATO"
    assert r.json()["chiuso"] is True


def test_incassa_residuo_no_close_with_credits_residui(client, auth_headers, sample_client):
    """BOUNDARY: saldare il residuo con crediti residui NON chiude (close credit-driven,
    date-independent). Qui il contratto è ATTIVO; il gemello SOSPESO è il test successivo."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=10)
    # zero eventi → 10 crediti residui

    r = _incassa(client, auth_headers, c["id"], 100.0)
    assert r.status_code == 200, r.text
    assert r.json()["stato_pagamento"] == "SALDATO"
    assert r.json()["chiuso"] is False  # crediti residui → resta aperto (debito di sedute)


def test_incassa_residuo_on_genuine_sospeso_contract(client, auth_headers, sample_client):
    """Caso d'uso PRIMARIO di G6: contratto realmente SCADUTO con crediti residui (SOSPESO).
    L'incasso del residuo funziona (zero gate lifecycle nell'endpoint) e NON chiude (sedute
    ancora dovute → resta SOSPESO). Esercita end-to-end lo scenario documentato, non un proxy."""
    c = _contract(
        client, auth_headers, sample_client["id"],
        prezzo=100.0, acconto=0.0, crediti=10, inizio=PAST_START, scadenza=PAST_END,
    )
    r = _incassa(client, auth_headers, c["id"], 100.0)
    assert r.status_code == 200, r.text
    assert r.json()["stato_pagamento"] == "SALDATO"
    assert r.json()["chiuso"] is False

    # conferma che è davvero SOSPESO (scaduto + crediti residui), non ATTIVO
    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers)
    assert detail.json()["lifecycle"] == "sospeso"


# ── guardie ed errori ──────────────────────────────────────────────


def test_incassa_residuo_overpayment_422(client, auth_headers, sample_contract):
    """Importo > residuo → 422, nessuna modifica."""
    r = _incassa(client, auth_headers, sample_contract["id"], 801.0)
    assert r.status_code == 422
    assert "residuo" in r.json()["detail"].lower()


def test_incassa_residuo_already_settled_400(client, auth_headers, sample_client):
    """Contratto già saldato (residuo 0) → 400."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=5)
    r = _incassa(client, auth_headers, c["id"], 10.0)
    assert r.status_code == 400
    assert "saldato" in r.json()["detail"].lower()


def test_incassa_residuo_double_incasso_settles_then_400(client, auth_headers, sample_contract):
    """Primo incasso satura il residuo; il secondo non ha nulla da incassare → 400."""
    r1 = _incassa(client, auth_headers, sample_contract["id"], 800.0)
    assert r1.status_code == 200
    r2 = _incassa(client, auth_headers, sample_contract["id"], 10.0)
    assert r2.status_code == 400


def test_incassa_residuo_closed_contract_400(client, auth_headers, sample_contract):
    """Contratto chiuso → 400 (non incassabile)."""
    client.post(f"/api/contracts/{sample_contract['id']}/terminate", json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    r = _incassa(client, auth_headers, sample_contract["id"], 100.0)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_incassa_residuo_deep_idor_404(client, auth_headers, sample_contract):
    """Trainer non proprietario → 404 (mai 403)."""
    r = client.post("/api/auth/register", json={
        "email": "evil@test.com", "nome": "Evil", "cognome": "T", "password": "evilpass123",
    })
    evil_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    rr = _incassa(client, evil_headers, sample_contract["id"], 100.0)
    assert rr.status_code == 404


def test_incassa_residuo_unknown_contract_404(client, auth_headers):
    """Contratto inesistente → 404."""
    r = _incassa(client, auth_headers, 999999, 100.0)
    assert r.status_code == 404


def test_incassa_residuo_invalid_input_is_atomic(client, auth_headers, sample_contract):
    """Input invalido (importo<=0) → 422 e nessuna mutazione del contratto (atomicità)."""
    r = _incassa(client, auth_headers, sample_contract["id"], -50.0)
    assert r.status_code == 422
    cr = client.get(f"/api/contracts/{sample_contract['id']}", headers=auth_headers)
    assert cr.json()["totale_versato"] == 200.0  # invariato (solo acconto)
    assert cr.json()["stato_pagamento"] == "PARZIALE"


# ── audit della transizione `chiuso` (P2): loggata una volta sola ──


def test_incassa_residuo_autoclose_logs_single_transition(client, auth_headers, sample_client, session):
    """L'auto-close da incasso logga la transizione `chiuso` UNA volta (no doppio log)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])

    assert _chiuso_transitions(session, c["id"]) == []  # prima dell'incasso: nessuna transizione

    r = _incassa(client, auth_headers, c["id"], 100.0)
    assert r.status_code == 200, r.text

    trans = _chiuso_transitions(session, c["id"])
    assert len(trans) == 1  # esattamente una entry (no doppio log _sync + UPDATE)
    assert trans[0]["chiuso"] == {"old": False, "new": True}
    assert trans[0]["motivo"] == "completamento"


def test_incassa_residuo_no_transition_when_not_closing(client, auth_headers, sample_client, session):
    """Incasso che salda ma NON chiude (crediti residui) → zero transizioni `chiuso`."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=10)
    r = _incassa(client, auth_headers, c["id"], 100.0)
    assert r.status_code == 200, r.text
    assert _chiuso_transitions(session, c["id"]) == []
