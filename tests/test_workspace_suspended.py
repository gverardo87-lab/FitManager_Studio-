"""
SPEC_REVISIONE_PRE_G7 — Sezione B: copertura SOSPESO nel workspace `renewals_cash`.

Cambiamento FUNZIONALE (non output-invariante): si verifica con test che DESCRIVONO i case attesi.
Il buco: le maglie del workspace (renewal = `data_scadenza >= today`; overdue = rate scadute) NON
intercettano un contratto scaduto-con-crediti-senza-rate-scadute (SOSPESO) → finora invisibile nel
cockpit, mentre lista (`kpi_da_incassare_scaduto`) e `/dashboard/suspended-contracts` lo mostravano.

AC-B1 i SOSPESO compaiono · AC-B2 allineamento con /dashboard/suspended-contracts · AC-B3 semantica
(bucket/severity, dedup con payment_overdue via exclusion-set, doppio-debito sedute≠denaro).
"""

from datetime import date, timedelta

TODAY = date.today()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti, inizio, scadenza):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": inizio.isoformat(), "data_scadenza": scadenza.isoformat(),
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
        "categoria": "PT", "titolo": "Seduta",
        "id_cliente": client_id, "id_contratto": contract_id,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _renewals_cases(client, auth_headers, *, kind=None):
    r = client.get("/api/workspace/cases?workspace=renewals_cash", headers=auth_headers)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    return [c for c in items if kind is None or c["case_kind"] == kind]


def _sospeso(client, auth_headers, client_id, *, days_overdue=20, prezzo=500.0, acconto=0.0, crediti=10):
    """Contratto SOSPESO: aperto, scaduto da `days_overdue` giorni, con crediti residui."""
    return _contract(
        client, auth_headers, client_id,
        prezzo=prezzo, acconto=acconto, crediti=crediti,
        inizio=TODAY - timedelta(days=days_overdue + 40),
        scadenza=TODAY - timedelta(days=days_overdue),
    )


# ── AC-B1: i SOSPESO compaiono nel workspace ───────────────────────


def test_sospeso_appears_as_workspace_case(client, auth_headers, sample_client):
    c = _sospeso(client, auth_headers, sample_client["id"])  # 0 eventi → 10 crediti residui
    cases = _renewals_cases(client, auth_headers, kind="suspended_contract")
    mine = [x for x in cases if x["root_entity"]["id"] == c["id"]]
    assert len(mine) == 1, "il contratto SOSPESO deve materializzarsi come case suspended_contract"
    case = mine[0]
    assert case["workspace"] == "renewals_cash"
    assert case["root_entity"]["type"] == "contract"
    assert case["secondary_entity"]["type"] == "client"


def test_esaurito_not_in_workspace_suspended(client, auth_headers, sample_client):
    """ESAURITO (scaduto + crediti esauriti) NON è SOSPESO → niente case suspended_contract."""
    c = _sospeso(client, auth_headers, sample_client["id"], crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])  # esaurisce l'unico credito
    cases = _renewals_cases(client, auth_headers, kind="suspended_contract")
    assert not any(x["root_entity"]["id"] == c["id"] for x in cases)


def test_attivo_not_in_workspace_suspended(client, auth_headers, sample_client):
    """ATTIVO (non scaduto) → niente case suspended_contract (resta nel canale rinnovi)."""
    c = _contract(
        client, auth_headers, sample_client["id"],
        prezzo=500.0, acconto=0.0, crediti=10,
        inizio=TODAY, scadenza=TODAY + timedelta(days=30),
    )
    cases = _renewals_cases(client, auth_headers, kind="suspended_contract")
    assert not any(x["root_entity"]["id"] == c["id"] for x in cases)


# ── AC-B3: semantica (bucket/severity, doppio-debito, dedup) ───────


def test_suspended_case_bucket_and_finance(client, auth_headers, sample_client):
    """Bucket 'now' (obbligazione scaduta, azionabile subito); finance = residuo SSoT = dettaglio."""
    c = _sospeso(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=200.0)
    case = next(
        x for x in _renewals_cases(client, auth_headers, kind="suspended_contract")
        if x["root_entity"]["id"] == c["id"]
    )
    assert case["bucket"] == "now"
    assert case["severity"] in {"low", "medium", "high"}  # mai 'critical' (riservato all'arretrato)
    # asse denaro: total_residual_amount == residuo SSoT == quello del dettaglio
    det = client.get(f"/api/contracts/{c['id']}", headers=auth_headers)
    assert case["finance_context"]["total_residual_amount"] == det.json()["residuo"] == 300.0


def test_suspended_severity_scales_with_aging(client, auth_headers, sample_client):
    """Aging-invertito: molto scaduto → severity alta (l'obbligazione non decade)."""
    c = _sospeso(client, auth_headers, sample_client["id"], days_overdue=70)
    case = next(
        x for x in _renewals_cases(client, auth_headers, kind="suspended_contract")
        if x["root_entity"]["id"] == c["id"]
    )
    assert case["severity"] == "high"


def test_sospeso_with_overdue_rate_not_duplicated(client, auth_headers, sample_client):
    """Dedup (exclusion-set, non merge_key): un SOSPESO con rate scadute è già payment_overdue →
    NON deve comparire ANCHE come suspended_contract (una sola riga per contratto)."""
    c = _sospeso(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=0.0)
    # rata scaduta (data_scadenza <= scadenza contratto, già passata) → contratto "overdue"
    rr = client.post("/api/rates", json={
        "id_contratto": c["id"],
        "data_scadenza": (TODAY - timedelta(days=20)).isoformat(),
        "importo_previsto": 500.0,
    }, headers=auth_headers)
    assert rr.status_code == 201, rr.text

    suspended = [x for x in _renewals_cases(client, auth_headers, kind="suspended_contract")
                 if x["root_entity"]["id"] == c["id"]]
    overdue = [x for x in _renewals_cases(client, auth_headers, kind="payment_overdue")
               if x["root_entity"]["id"] == c["id"]]
    assert not suspended, "niente doppione: con rate scadute è già payment_overdue"
    assert len(overdue) == 1


# ── AC-B2: allineamento con /dashboard/suspended-contracts ─────────


def test_workspace_suspended_aligns_with_dashboard(client, auth_headers, sample_client):
    """Stesso dato → stesso contratto SOSPESO visibile su entrambe le superfici (coerenza)."""
    c = _sospeso(client, auth_headers, sample_client["id"])

    dash = client.get("/api/dashboard/suspended-contracts", headers=auth_headers)
    assert dash.status_code == 200, dash.text
    dash_ids = {it["contract_id"] for it in dash.json()["items"]}

    ws_ids = {x["root_entity"]["id"] for x in _renewals_cases(client, auth_headers, kind="suspended_contract")}

    assert c["id"] in dash_ids
    assert c["id"] in ws_ids
