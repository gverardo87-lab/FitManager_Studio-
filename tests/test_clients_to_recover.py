"""
Test SPEC_RINNOVI_SCADUTI v1.2 — "Clienti da recuperare" (client-aware).

GET /api/dashboard/clients-to-recover:
- lapsed = ha scaduto E zero contratti attivi (chiuso=False AND data_scadenza>=oggi)
- unità cliente (1 riga/cliente, rappresentante = scaduto più recente)
- NESSUN filtro opportunità (anche cliente che ha completato/pagato tutto compare)
- esclusi i marcati "non rinnova" (reversibile)
+ fix: i contratti già rinnovati sono esclusi da /dashboard/expiring-contracts
"""

from datetime import date, timedelta

TODAY = date.today()


def _past(days):
    return TODAY - timedelta(days=days)


def _future(days):
    return TODAY + timedelta(days=days)


def _contract(client, auth_headers, client_id, inizio, scadenza, prezzo=1000.0, acconto=200.0, crediti=10):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": inizio.isoformat(), "data_scadenza": scadenza.isoformat(),
        "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, f"Contract create failed: {r.text}"
    return r.json()


def _recover(client, auth_headers):
    r = client.get("/api/dashboard/clients-to-recover", headers=auth_headers)
    assert r.status_code == 200
    return r.json()


# ════════════════════════════════════════════════════════════
# Client-aware selection
# ════════════════════════════════════════════════════════════

def test_lapsed_client_appears(client, auth_headers, sample_client):
    """Cliente con scaduto e zero attivi → compare (1 riga, ritardo corretto)."""
    c = _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    item = data["items"][0]
    assert item["client_id"] == sample_client["id"]
    assert item["contract_id"] == c["id"]
    assert item["giorni_ritardo"] == 60


def test_active_unlinked_contract_suppresses(client, auth_headers, sample_client):
    """Cliente con scaduto + nuovo contratto attivo NON collegato → NON compare (il caso del founder)."""
    _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))   # scaduto
    _contract(client, auth_headers, sample_client["id"], _past(10), _future(60))  # attivo, non collegato
    assert _recover(client, auth_headers)["total"] == 0


def test_renewed_child_suppresses(client, auth_headers, sample_client):
    """Cliente con scaduto + figlio rinnovo attivo → NON compare (sussunto da 'zero attivi')."""
    parent = _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    r = client.post(f"/api/contracts/{parent['id']}/renew", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Rinnovo", "crediti_totali": 10,
        "prezzo_totale": 500.0, "data_inizio": TODAY.isoformat(), "data_scadenza": _future(60).isoformat(),
        "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    assert _recover(client, auth_headers)["total"] == 0


def test_two_expired_collapse_to_one(client, auth_headers, sample_client):
    """2 scaduti, zero attivi → 1 sola riga; rappresentante = scaduto più recente."""
    _contract(client, auth_headers, sample_client["id"], _past(200), _past(150))   # vecchio
    recent = _contract(client, auth_headers, sample_client["id"], _past(120), _past(40))  # più recente
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    item = data["items"][0]
    assert item["contract_id"] == recent["id"]
    assert item["giorni_ritardo"] == 40


def test_completed_paid_lapsed_still_appears(client, auth_headers, sample_client):
    """Cliente che ha pagato tutto (residuo 0) e non rinnova → compare comunque (no filtro opportunità)."""
    _contract(client, auth_headers, sample_client["id"], _past(120), _past(60), prezzo=500.0, acconto=500.0)
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    assert data["items"][0]["residuo"] == 0.0


def test_marked_not_renewed_excluded_and_reversible(client, auth_headers, sample_client, session):
    """Rappresentante marcato 'non rinnova' → escluso; riaperto (null) → ricompare."""
    from api.models.contract import Contract
    c = _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))

    contract = session.get(Contract, c["id"])
    contract.esito_rinnovo_motivo = "prezzo"
    session.add(contract)
    session.commit()
    assert _recover(client, auth_headers)["total"] == 0

    contract = session.get(Contract, c["id"])
    contract.esito_rinnovo_motivo = None
    session.add(contract)
    session.commit()
    assert _recover(client, auth_headers)["total"] == 1


def test_multi_tenant(client, auth_headers, sample_client):
    """Trainer B non vede i lapsed di Trainer A."""
    _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    other = client.post("/api/auth/register", json={
        "email": "other@test.com", "nome": "Other", "cognome": "Trainer", "password": "otherpass123",
    })
    assert other.status_code == 201, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}
    assert _recover(client, other_headers)["total"] == 0


def test_empty(client, auth_headers):
    """Nessun contratto → lista vuota."""
    assert _recover(client, auth_headers) == {"items": [], "total": 0}


def test_alert_clients_to_recover(client, auth_headers, sample_client):
    """L'alert dashboard 'clients_to_recover' compare e conta i clienti lapsed."""
    _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    r = client.get("/api/dashboard/alerts", headers=auth_headers)
    assert r.status_code == 200
    alert = next((i for i in r.json()["items"] if i["category"] == "clients_to_recover"), None)
    assert alert is not None
    assert alert["count"] == 1
    assert alert["link"] == "/rinnovi-incassi"


# ════════════════════════════════════════════════════════════
# Azione "Non rinnova" (endpoint renewal-outcome)
# ════════════════════════════════════════════════════════════

def test_renewal_outcome_endpoint_excludes_and_reverses(client, auth_headers, sample_client):
    """POST renewal-outcome → escluso dalla worklist; DELETE → ricompare."""
    c = _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    assert _recover(client, auth_headers)["total"] == 1

    r = client.post(f"/api/contracts/{c['id']}/renewal-outcome",
                    json={"motivo": "prezzo", "note": "troppo caro"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert _recover(client, auth_headers)["total"] == 0

    d = client.delete(f"/api/contracts/{c['id']}/renewal-outcome", headers=auth_headers)
    assert d.status_code == 200, d.text
    assert _recover(client, auth_headers)["total"] == 1


def test_renewal_outcome_invalid_motivo(client, auth_headers, sample_client):
    """Motivo fuori set → 422."""
    c = _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    r = client.post(f"/api/contracts/{c['id']}/renewal-outcome",
                    json={"motivo": "boh"}, headers=auth_headers)
    assert r.status_code == 422


def test_renewal_outcome_ownership_404(client, auth_headers, sample_client):
    """Contratto di altro trainer → 404 (mai 403)."""
    c = _contract(client, auth_headers, sample_client["id"], _past(120), _past(60))
    other = client.post("/api/auth/register", json={
        "email": "o2@test.com", "nome": "O", "cognome": "T", "password": "otherpass123",
    })
    assert other.status_code == 201, other.text
    oh = {"Authorization": f"Bearer {other.json()['access_token']}"}
    r = client.post(f"/api/contracts/{c['id']}/renewal-outcome", json={"motivo": "prezzo"}, headers=oh)
    assert r.status_code == 404


# ════════════════════════════════════════════════════════════
# Fix: già-rinnovati esclusi da "in scadenza"
# ════════════════════════════════════════════════════════════

def test_expiring_excludes_renewed(client, auth_headers, sample_client):
    """Un contratto in scadenza ma già rinnovato (esiste figlio) NON compare in expiring-contracts."""
    parent = _contract(client, auth_headers, sample_client["id"], _past(60), _future(15))  # scade tra 15gg
    # senza rinnovo comparirebbe; lo rinnoviamo (figlio oltre i 30gg per non comparire a sua volta)
    r = client.post(f"/api/contracts/{parent['id']}/renew", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Rinnovo", "crediti_totali": 10,
        "prezzo_totale": 500.0, "data_inizio": TODAY.isoformat(), "data_scadenza": _future(90).isoformat(),
        "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text

    data = client.get("/api/dashboard/expiring-contracts", headers=auth_headers).json()
    assert all(it["contract_id"] != parent["id"] for it in data["items"])
