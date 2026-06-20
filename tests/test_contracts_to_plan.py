"""
Test SPEC_RINNOVO Criterio B — contratti da pianificare.

Copre:
- B2: endpoint GET /api/dashboard/contracts-to-plan (Contract-first, selezione §B.3, multi-tenant)
- B5: cruscotto KPI venduto / a_rate / da_pianificare in GET /api/contracts (riconciliazione)
- B1: alert 'orphan_contracts' filtrato su residuo positivo
"""



def _create_contract(client, auth_headers, client_id, prezzo, acconto):
    """Helper: crea contratto con prezzo/acconto dati (zero rate)."""
    r = client.post("/api/contracts", json={
        "id_cliente": client_id,
        "tipo_pacchetto": "Test Pkg",
        "crediti_totali": 10,
        "prezzo_totale": prezzo,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
        "acconto": acconto,
        "metodo_acconto": "CONTANTI" if acconto > 0 else None,
    }, headers=auth_headers)
    assert r.status_code == 201, f"Contract creation failed: {r.text}"
    return r.json()


def _register_other_trainer(client):
    """Registra un secondo trainer, ritorna i suoi headers JWT."""
    r = client.post("/api/auth/register", json={
        "email": "other@test.com",
        "nome": "Other",
        "cognome": "Trainer",
        "password": "otherpass123",
    })
    assert r.status_code == 201, f"Register failed: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ════════════════════════════════════════════════════════════
# B2 — Endpoint contracts-to-plan
# ════════════════════════════════════════════════════════════

def test_contract_with_residuo_and_no_rates_appears(client, auth_headers, sample_contract):
    """Contratto aperto, residuo>0 (1000-200=800), zero rate → compare con residuo corretto."""
    r = client.get("/api/dashboard/contracts-to-plan", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["contract_id"] == sample_contract["id"]
    assert item["importo_residuo"] == 800.0
    assert item["client_nome"] == "Mario"


def test_fully_paid_acconto_no_rates_excluded(client, auth_headers, sample_client):
    """Contratto saldato in acconto (residuo 0), zero rate → NON compare (§B.3 residuo>0)."""
    _create_contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=500.0)
    r = client.get("/api/dashboard/contracts-to-plan", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_contract_with_rates_excluded(client, auth_headers, sample_contract_with_plan):
    """Contratto con piano rate → NON compare (ha rate)."""
    r = client.get("/api/dashboard/contracts-to-plan", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_closed_contract_excluded(client, auth_headers, sample_contract):
    """Contratto chiuso → NON compare anche se senza rate."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={"chiuso": True}, headers=auth_headers)
    r = client.get("/api/dashboard/contracts-to-plan", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_multi_tenant_isolation(client, auth_headers, sample_contract):
    """Trainer B non vede i contratti-da-pianificare di Trainer A."""
    other_headers = _register_other_trainer(client)
    r = client.get("/api/dashboard/contracts-to-plan", headers=other_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0  # B non ha contratti, A non deve trapelare


def test_empty_returns_zero(client, auth_headers):
    """Nessun contratto → lista vuota."""
    r = client.get("/api/dashboard/contracts-to-plan", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0}


# ════════════════════════════════════════════════════════════
# B5 — Cruscotto KPI (riconciliazione)
# ════════════════════════════════════════════════════════════

def test_cruscotto_zero_rate_contract(client, auth_headers, sample_contract):
    """Zero rate: residuo=800 (1000-200), a_rate=0, da_pianificare=residuo pieno=800."""
    r = client.get("/api/contracts", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["kpi_residuo"] == 800.0
    assert data["kpi_a_rate"] == 0.0
    assert data["kpi_da_pianificare"] == 800.0
    # ancora: residuo = a_rate + da_pianificare
    assert round(data["kpi_a_rate"] + data["kpi_da_pianificare"], 2) == data["kpi_residuo"]


def test_cruscotto_partial_plan_reconciles(client, auth_headers, sample_contract):
    """Rata parziale (300 su 800 residuo): a_rate=300, da_pianificare=residuo-a_rate=500."""
    cid = sample_contract["id"]
    r = client.post("/api/rates", json={
        "id_contratto": cid,
        "data_scadenza": "2026-06-01",
        "importo_previsto": 300.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text

    data = client.get("/api/contracts", headers=auth_headers).json()
    assert data["kpi_residuo"] == 800.0
    assert data["kpi_a_rate"] == 300.0
    assert data["kpi_da_pianificare"] == 500.0
    # ancora: a_rate + da_pianificare == residuo (800)
    assert round(data["kpi_a_rate"] + data["kpi_da_pianificare"], 2) == data["kpi_residuo"]


def test_cruscotto_excludes_closed(client, auth_headers, sample_contract):
    """Contratto chiuso non contribuisce al cruscotto (KPI sugli aperti)."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={"chiuso": True}, headers=auth_headers)
    data = client.get("/api/contracts", headers=auth_headers).json()
    assert data["kpi_residuo"] == 0.0
    assert data["kpi_a_rate"] == 0.0
    assert data["kpi_da_pianificare"] == 0.0


# ════════════════════════════════════════════════════════════
# B1 — Alert orphan_contracts su residuo positivo
# ════════════════════════════════════════════════════════════

def _orphan_alert(client, auth_headers):
    r = client.get("/api/dashboard/alerts", headers=auth_headers)
    assert r.status_code == 200
    return next((i for i in r.json()["items"] if i["category"] == "orphan_contracts"), None)


def test_alert_present_for_residuo_positivo(client, auth_headers, sample_contract):
    """Contratto residuo>0 senza rate → alert orphan_contracts presente."""
    assert _orphan_alert(client, auth_headers) is not None


def test_alert_absent_for_fully_paid(client, auth_headers, sample_client):
    """Contratto saldato in acconto (residuo 0) senza rate → nessun alert (B1)."""
    _create_contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=500.0)
    assert _orphan_alert(client, auth_headers) is None
