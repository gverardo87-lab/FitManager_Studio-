"""
Blocco 3 — worklist "Contratti sospesi" (stato SOSPESO) + azione ESTENDI.

SOSPESO = aperto + scaduto + crediti_residui > 0 (sedute prepagate da erogare). Unità = CONTRATTO.
Deriva da `contract_state` (mai inline). ESTENDI = PUT /contracts/{id} (riuso puro).
"""

from datetime import date, timedelta

TODAY = date.today()


def _past(d):
    return (TODAY - timedelta(days=d)).isoformat()


def _future(d):
    return (TODAY + timedelta(days=d)).isoformat()


def _contract(client, auth_headers, client_id, *, inizio, scadenza, prezzo=500.0, acconto=500.0, crediti=10):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": inizio, "data_scadenza": scadenza, "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _consume_all_credits(client, auth_headers, contract, client_id):
    inizio = contract["data_inizio"]
    for i in range(contract["crediti_totali"]):
        r = client.post("/api/events", json={
            "data_inizio": f"{inizio}T{9 + i:02d}:00:00",
            "data_fine": f"{inizio}T{9 + i:02d}:30:00",
            "categoria": "PT", "titolo": "Seduta",
            "id_cliente": client_id, "id_contratto": contract["id"],
        }, headers=auth_headers)
        assert r.status_code == 201, r.text


def _suspended(client, auth_headers):
    r = client.get("/api/dashboard/suspended-contracts", headers=auth_headers)
    assert r.status_code == 200
    return r.json()


def _suspended_alert(client, auth_headers):
    r = client.get("/api/dashboard/alerts", headers=auth_headers)
    assert r.status_code == 200
    return next((i for i in r.json()["items"] if i["category"] == "suspended_contracts"), None)


# ── Selezione per stato ────────────────────────────────────────────

def test_sospeso_appears_with_dual_debt(client, auth_headers, sample_client):
    """Scaduto + crediti residui → compare; sedute residue e residuo denaro sono campi distinti."""
    c = _contract(client, auth_headers, sample_client["id"],
                  inizio=_past(120), scadenza=_past(30), prezzo=500.0, acconto=300.0, crediti=10)
    data = _suspended(client, auth_headers)
    assert data["total"] == 1
    item = data["items"][0]
    assert item["contract_id"] == c["id"]
    assert item["giorni_ritardo"] == 30
    assert item["crediti_residui"] == 10        # sedute da recuperare (asse crediti)
    assert item["crediti_usati"] == 0
    assert item["residuo"] == 200.0             # denaro ancora dovuto (asse denaro, distinto)


def test_esaurito_excluded(client, auth_headers, sample_client):
    """Scaduto ma crediti esauriti (residuo denaro>0, non chiuso) = ESAURITO → NON sospeso."""
    c = _contract(client, auth_headers, sample_client["id"],
                  inizio=_past(120), scadenza=_past(30), prezzo=500.0, acconto=200.0, crediti=1)
    _consume_all_credits(client, auth_headers, c, sample_client["id"])  # 1/1 → crediti_residui 0
    assert _suspended(client, auth_headers)["total"] == 0


def test_attivo_excluded(client, auth_headers, sample_client):
    """Vigente (scadenza futura) → ATTIVO, non sospeso."""
    _contract(client, auth_headers, sample_client["id"], inizio=_past(10), scadenza=_future(60), crediti=10)
    assert _suspended(client, auth_headers)["total"] == 0


def test_chiuso_excluded(client, auth_headers, sample_client):
    """Contratto chiuso non compare anche se scaduto con crediti."""
    c = _contract(client, auth_headers, sample_client["id"], inizio=_past(120), scadenza=_past(30), crediti=10)
    client.post(f"/api/contracts/{c['id']}/terminate", json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert _suspended(client, auth_headers)["total"] == 0


# ── Azione ESTENDI (riuso PUT update_contract) ─────────────────────

def test_estendi_removes_from_worklist_and_flips_kpi(client, auth_headers, sample_client):
    """Estendi (data_scadenza futura) → SOSPESO torna ATTIVO: esce dalla worklist, kpi sospesi→attivi."""
    c = _contract(client, auth_headers, sample_client["id"], inizio=_past(120), scadenza=_past(30), crediti=10)
    assert _suspended(client, auth_headers)["total"] == 1

    kpi_before = client.get("/api/contracts", headers=auth_headers).json()
    assert kpi_before["kpi_sospesi"] == 1
    assert kpi_before["kpi_attivi"] == 0

    r = client.put(f"/api/contracts/{c['id']}", json={"data_scadenza": _future(60)}, headers=auth_headers)
    assert r.status_code == 200, r.text

    assert _suspended(client, auth_headers)["total"] == 0
    kpi_after = client.get("/api/contracts", headers=auth_headers).json()
    assert kpi_after["kpi_sospesi"] == 0
    assert kpi_after["kpi_attivi"] == 1


# ── Unità = contratto + ordine aging invertito ─────────────────────

def test_unit_is_contract_two_rows_same_client(client, auth_headers, sample_client):
    """2 contratti SOSPESO dello stesso cliente → 2 righe (unità=contratto, no collapse)."""
    _contract(client, auth_headers, sample_client["id"], inizio=_past(200), scadenza=_past(100), crediti=10)
    _contract(client, auth_headers, sample_client["id"], inizio=_past(120), scadenza=_past(20), crediti=10)
    data = _suspended(client, auth_headers)
    assert data["total"] == 2
    # aging INVERTITO: il più vecchio (ritardo maggiore) prima
    assert data["items"][0]["giorni_ritardo"] == 100
    assert data["items"][1]["giorni_ritardo"] == 20


# ── Coerenza con clients-to-recover (il SOSPESO è ingaggiato) ──────

def test_sospeso_client_not_in_recover(client, auth_headers, sample_client):
    """Un cliente col solo SOSPESO è ingaggiato → in sospesi, NON in clienti-da-recuperare."""
    _contract(client, auth_headers, sample_client["id"], inizio=_past(120), scadenza=_past(30), crediti=10)
    assert _suspended(client, auth_headers)["total"] == 1
    rec = client.get("/api/dashboard/clients-to-recover", headers=auth_headers).json()
    assert rec["total"] == 0


# ── Alert ──────────────────────────────────────────────────────────

def test_alert_present_count_matches(client, auth_headers, sample_client):
    """Alert suspended_contracts presente, count == len(items), grammatica singolare."""
    _contract(client, auth_headers, sample_client["id"], inizio=_past(120), scadenza=_past(30), crediti=10)
    alert = _suspended_alert(client, auth_headers)
    assert alert is not None
    assert alert["count"] == 1
    assert "contratto sospeso" in alert["title"]
    assert alert["link"] == "/rinnovi-incassi"


def test_alert_absent_when_none(client, auth_headers, sample_client):
    """Nessun SOSPESO (solo ATTIVO) → nessun alert."""
    _contract(client, auth_headers, sample_client["id"], inizio=_past(10), scadenza=_future(60), crediti=10)
    assert _suspended_alert(client, auth_headers) is None


# ── Multi-tenant + empty ───────────────────────────────────────────

def test_multi_tenant(client, auth_headers, sample_client):
    _contract(client, auth_headers, sample_client["id"], inizio=_past(120), scadenza=_past(30), crediti=10)
    other = client.post("/api/auth/register", json={
        "email": "other@test.com", "nome": "Other", "cognome": "Trainer", "password": "otherpass123",
    })
    assert other.status_code == 201, other.text
    oh = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert _suspended(client, oh)["total"] == 0


def test_empty(client, auth_headers):
    assert _suspended(client, auth_headers) == {"items": [], "total": 0}
