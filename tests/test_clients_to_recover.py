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


def _consume_all_credits(client, auth_headers, contract, client_id):
    """Esaurisce i crediti con eventi PT → contratto ESAURITO (o CHIUSO se saldato)."""
    inizio = contract["data_inizio"]
    for i in range(contract["crediti_totali"]):
        r = client.post("/api/events", json={
            "data_inizio": f"{inizio}T{9 + i:02d}:00:00",
            "data_fine": f"{inizio}T{9 + i:02d}:30:00",
            "categoria": "PT",
            "titolo": f"Seduta {i + 1}",
            "id_cliente": client_id,
            "id_contratto": contract["id"],
        }, headers=auth_headers)
        assert r.status_code == 201, f"Event create failed: {r.text}"


def _lapsed(client, auth_headers, client_id, inizio, scadenza, prezzo=1000.0, acconto=200.0, crediti=1):
    """Contratto LAPSED reale: scaduto + crediti esauriti (ESAURITO) → cliente non ingaggiato."""
    c = _contract(client, auth_headers, client_id, inizio, scadenza, prezzo, acconto, crediti)
    _consume_all_credits(client, auth_headers, c, client_id)
    return c


def _recover(client, auth_headers):
    r = client.get("/api/dashboard/clients-to-recover", headers=auth_headers)
    assert r.status_code == 200
    return r.json()


# ════════════════════════════════════════════════════════════
# Client-aware selection
# ════════════════════════════════════════════════════════════

def test_lapsed_client_appears(client, auth_headers, sample_client):
    """Cliente ESAURITO (scaduto, crediti finiti) e zero ingaggi → compare (1 riga, ritardo corretto)."""
    c = _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60))
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    item = data["items"][0]
    assert item["client_id"] == sample_client["id"]
    assert item["contract_id"] == c["id"]
    assert item["giorni_ritardo"] == 60


def test_suspended_client_excluded(client, auth_headers, sample_client):
    """
    FIX SOSPESO: scaduto con sedute prepagate residue (crediti>0, zero eventi) = SOSPESO =
    ingaggiato → NON in clienti-da-recuperare (va in 'contratti sospesi'). Caso Paola/Merchiori.
    """
    _contract(client, auth_headers, sample_client["id"], _past(120), _past(60), crediti=10)  # 10 residui = SOSPESO
    assert _recover(client, auth_headers)["total"] == 0


def test_representative_is_most_recent_including_closed(client, auth_headers, sample_client):
    """Rappresentante = contratto più recente IN ASSOLUTO, anche se CHIUSO (§6, caso Dalila c29/c25)."""
    _lapsed(client, auth_headers, sample_client["id"], _past(200), _past(150))  # vecchio ESAURITO
    recent = _contract(client, auth_headers, sample_client["id"], _past(80), _past(40), crediti=10)
    client.post(f"/api/contracts/{recent['id']}/terminate", json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)  # più recente, CHIUSO (via terminate)
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    assert data["items"][0]["contract_id"] == recent["id"]  # il CHIUSO più recente, non il vecchio scaduto


def test_representative_future_scadenza_giorni_ritardo_clamped(client, auth_headers, sample_client):
    """Rappresentante CHIUSO con scadenza FUTURA (caso 3 contratti muti) → giorni_ritardo clampato a 0, mai negativo."""
    c = _contract(client, auth_headers, sample_client["id"], _past(30), _future(60))  # scadenza futura
    client.post(f"/api/contracts/{c['id']}/terminate", json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)  # chiuso "muto" (via terminate, scadenza futura accettata)
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    assert data["items"][0]["giorni_ritardo"] == 0  # non "-N giorni"


def test_active_unlinked_contract_suppresses(client, auth_headers, sample_client):
    """Cliente con ESAURITO + nuovo contratto attivo NON collegato → NON compare (il caso del founder)."""
    _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60))      # esaurito
    _contract(client, auth_headers, sample_client["id"], _past(10), _future(60))   # ATTIVO, non collegato
    assert _recover(client, auth_headers)["total"] == 0


def test_renewed_child_suppresses(client, auth_headers, sample_client):
    """Cliente con ESAURITO + figlio rinnovo attivo → NON compare (ingaggiato dal figlio attivo)."""
    parent = _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60))
    r = client.post(f"/api/contracts/{parent['id']}/renew", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Rinnovo", "crediti_totali": 10,
        "prezzo_totale": 500.0, "data_inizio": TODAY.isoformat(), "data_scadenza": _future(60).isoformat(),
        "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    assert _recover(client, auth_headers)["total"] == 0


def test_two_expired_collapse_to_one(client, auth_headers, sample_client):
    """2 ESAURITI, zero ingaggi → 1 sola riga; rappresentante = scaduto più recente."""
    _lapsed(client, auth_headers, sample_client["id"], _past(200), _past(150))   # vecchio
    recent = _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(40))  # più recente
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    item = data["items"][0]
    assert item["contract_id"] == recent["id"]
    assert item["giorni_ritardo"] == 40


def test_completed_paid_lapsed_still_appears(client, auth_headers, sample_client):
    """Cliente che ha pagato tutto e finito le sedute (residuo 0, auto-CHIUSO) → compare comunque (no filtro opportunità)."""
    _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60), prezzo=500.0, acconto=500.0)
    data = _recover(client, auth_headers)
    assert data["total"] == 1
    assert data["items"][0]["residuo"] == 0.0


def test_marked_not_renewed_excluded_and_reversible(client, auth_headers, sample_client, session):
    """Rappresentante marcato 'non rinnova' → escluso; riaperto (null) → ricompare."""
    from api.models.contract import Contract
    c = _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60))

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
    _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60))
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
    c = _lapsed(client, auth_headers, sample_client["id"], _past(120), _past(60))
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
