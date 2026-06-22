"""Test integrità contratto — validazione residuo, chiuso guard, auto-close."""


# ── F1: Validazione residuo rate ──


def test_rate_exceeding_residual_rejected(client, auth_headers, sample_contract):
    """Rata con importo > residuo rateizzabile → 422."""
    # sample_contract: prezzo=1000, acconto=200 → residuo = 800
    r = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 801.0,
    }, headers=auth_headers)
    assert r.status_code == 422
    assert "residuo" in r.json()["detail"].lower()


def test_rate_exactly_at_residual_accepted(client, auth_headers, sample_contract):
    """Rata con importo = residuo rateizzabile → 201."""
    r = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 800.0,
    }, headers=auth_headers)
    assert r.status_code == 201


def test_second_rate_exceeds_residual(client, auth_headers, sample_contract):
    """Prima rata OK, seconda eccede il residuo → 422."""
    # Prima rata: 500 (residuo dopo = 300)
    r1 = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 500.0,
    }, headers=auth_headers)
    assert r1.status_code == 201

    # Seconda rata: 301 eccede il residuo di 300
    r2 = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-04-01",
        "importo_previsto": 301.0,
    }, headers=auth_headers)
    assert r2.status_code == 422


# ── F1+F2: Chiuso guard ──


def test_rate_on_closed_contract_rejected(client, auth_headers, sample_contract):
    """Rata su contratto chiuso → 400."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.post("/api/rates", json={
        "id_contratto": sample_contract["id"],
        "data_scadenza": "2026-03-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_plan_on_closed_contract_rejected(client, auth_headers, sample_contract):
    """Piano rate su contratto chiuso → 400."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.post(f"/api/rates/generate-plan/{sample_contract['id']}", json={
        "importo_da_rateizzare": 800.0,
        "numero_rate": 4,
        "data_prima_rata": "2026-02-01",
        "frequenza": "MENSILE",
    }, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_event_on_closed_contract_rejected(client, auth_headers, sample_client, sample_contract):
    """Evento PT con id_contratto su contratto chiuso → 400."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.post("/api/events", json={
        "data_inizio": "2026-03-01T09:00:00",
        "data_fine": "2026-03-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione bloccata",
        "id_cliente": sample_client["id"],
        "id_contratto": sample_contract["id"],
    }, headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


# ── F2: Close/Reopen via update ──


def test_close_contract_via_update(client, auth_headers, sample_contract):
    """Chiudere un contratto via PUT → chiuso = True."""
    r = client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)
    assert r.status_code == 200

    cr = client.get(f"/api/contracts/{sample_contract['id']}", headers=auth_headers)
    assert cr.json()["chiuso"] is True


def test_delete_client_with_closed_contract(client, auth_headers, sample_client, sample_contract):
    """Cancellazione cliente con contratto chiuso → OK (non blocca)."""
    client.put(f"/api/contracts/{sample_contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    r = client.delete(f"/api/clients/{sample_client['id']}", headers=auth_headers)
    assert r.status_code == 204


# ── F5: Auto-close + auto-reopen ──


def _create_mini_contract(client, auth_headers, client_id):
    """Helper: contratto 1 credito, 100€, acconto 0."""
    r = client.post("/api/contracts", json={
        "id_cliente": client_id,
        "tipo_pacchetto": "Mini 1",
        "crediti_totali": 1,
        "prezzo_totale": 100.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert r.status_code == 201
    return r.json()


def test_auto_close_after_full_payment_and_credits(client, auth_headers, sample_client):
    """Auto-close: contratto saldato + crediti esauriti → chiuso automatico."""
    contract = _create_mini_contract(client, auth_headers, sample_client["id"])

    # Crea 1 rata da 100
    rr = client.post("/api/rates", json={
        "id_contratto": contract["id"],
        "data_scadenza": "2026-02-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Crea 1 evento PT (consuma il credito)
    er = client.post("/api/events", json={
        "data_inizio": "2026-02-01T09:00:00",
        "data_fine": "2026-02-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione test",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)
    assert er.status_code == 201

    # Paga la rata → saldato + crediti esauriti → auto-close
    pr = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)
    assert pr.status_code == 200

    # Verifica contratto chiuso
    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    data = check.json()
    assert data["stato_pagamento"] == "SALDATO"
    assert data["chiuso"] is True


def test_unpay_reopens_closed_contract(client, auth_headers, sample_client):
    """Revoca pagamento su contratto auto-chiuso → riapre (chiuso = False)."""
    contract = _create_mini_contract(client, auth_headers, sample_client["id"])

    rr = client.post("/api/rates", json={
        "id_contratto": contract["id"],
        "data_scadenza": "2026-02-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    rate = rr.json()

    # Evento PT per consumare il credito
    client.post("/api/events", json={
        "data_inizio": "2026-02-01T11:00:00",
        "data_fine": "2026-02-01T12:00:00",
        "categoria": "PT",
        "titolo": "Sessione test 2",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)

    # Paga → auto-close
    client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)

    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check.json()["chiuso"] is True

    # Revoca pagamento → riapre
    ur = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert ur.status_code == 200

    check2 = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check2.json()["chiuso"] is False
    assert check2.json()["stato_pagamento"] != "SALDATO"


# ── Delete contract guards ──


def test_delete_contract_blocked_if_pending_rates(client, auth_headers, sample_contract_with_plan):
    """Delete contratto con rate PENDENTI (non pagate) → 409."""
    contract = sample_contract_with_plan["contract"]

    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 409
    assert "rate" in r.json()["detail"].lower()


def test_delete_contract_blocked_if_credits_residui(client, auth_headers, sample_client):
    """Delete contratto con crediti residui (sedute non consumate) → 409."""
    # Crea contratto con 5 crediti, senza rate
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Test crediti",
        "crediti_totali": 5,
        "prezzo_totale": 500.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Crea 1 evento PT (consuma 1 credito, ne restano 4)
    client.post("/api/events", json={
        "data_inizio": "2026-03-01T09:00:00",
        "data_fine": "2026-03-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione test",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)

    # Delete → bloccato per crediti residui (4 su 5)
    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 409
    assert "crediti" in r.json()["detail"].lower()


def test_delete_clean_contract_ok(client, auth_headers, sample_client):
    """Delete contratto senza rate e crediti esauriti → 204."""
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Errore",
        "crediti_totali": 1,
        "prezzo_totale": 50.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Consuma l'unico credito con 1 evento PT
    client.post("/api/events", json={
        "data_inizio": "2026-02-01T09:00:00",
        "data_fine": "2026-02-01T10:00:00",
        "categoria": "PT",
        "titolo": "Consumo credito",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)

    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 204

    # Contratto non piu' accessibile
    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check.status_code == 404


def test_delete_contract_cascades_acconto_movement(client, auth_headers, sample_client):
    """Delete contratto con acconto → CashMovement acconto soft-deleted."""
    # Crea contratto con acconto (genera CashMovement automaticamente)
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Errore con acconto",
        "crediti_totali": 1,
        "prezzo_totale": 100.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
        "acconto": 50.0,
        "metodo_acconto": "CONTANTI",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Consuma l'unico credito
    client.post("/api/events", json={
        "data_inizio": "2026-02-01T09:00:00",
        "data_fine": "2026-02-01T10:00:00",
        "categoria": "PT",
        "titolo": "Consumo credito",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)

    # Verifica che il movimento acconto esista (mese gennaio 2026)
    mr = client.get("/api/movements?anno=2026&mese=1", headers=auth_headers)
    acconto_before = [m for m in mr.json()["items"] if m.get("id_contratto") == contract["id"]]
    assert len(acconto_before) >= 1

    # Delete contratto → cascade acconto
    r = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert r.status_code == 204

    # Movimento acconto non piu' visibile
    mr2 = client.get("/api/movements?anno=2026&mese=1", headers=auth_headers)
    acconto_after = [m for m in mr2.json()["items"] if m.get("id_contratto") == contract["id"]]
    assert len(acconto_after) == 0


def test_delete_completed_contract_full_cascade(client, auth_headers, sample_client):
    """Delete contratto completato (tutto SALDATO + crediti esauriti) → 204 + cascade."""
    # Crea contratto: 1 credito, 100€, zero acconto
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Mini 1",
        "crediti_totali": 1,
        "prezzo_totale": 100.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Crea 1 rata da 100
    rr = client.post("/api/rates", json={
        "id_contratto": contract["id"],
        "data_scadenza": "2026-02-01",
        "importo_previsto": 100.0,
    }, headers=auth_headers)
    assert rr.status_code == 201
    rate = rr.json()

    # Crea 1 evento PT (consuma il credito)
    er = client.post("/api/events", json={
        "data_inizio": "2026-02-01T09:00:00",
        "data_fine": "2026-02-01T10:00:00",
        "categoria": "PT",
        "titolo": "Sessione completata",
        "id_cliente": sample_client["id"],
        "id_contratto": contract["id"],
    }, headers=auth_headers)
    assert er.status_code == 201
    event_id = er.json()["id"]

    # Paga la rata → SALDATA + auto-close
    pr = client.post(f"/api/rates/{rate['id']}/pay", json={
        "importo": 100.0,
        "metodo": "POS",
        "data_pagamento": "2026-02-01",
    }, headers=auth_headers)
    assert pr.status_code == 200

    # Verifica pre-delete: contratto chiuso e saldato
    check = client.get(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert check.json()["chiuso"] is True
    assert check.json()["stato_pagamento"] == "SALDATO"

    # DELETE → deve passare (zero rate pendenti, zero crediti residui)
    dr = client.delete(f"/api/contracts/{contract['id']}", headers=auth_headers)
    assert dr.status_code == 204

    # CASCADE verifiche:
    # 1. Contratto non piu' accessibile
    assert client.get(f"/api/contracts/{contract['id']}", headers=auth_headers).status_code == 404

    # 2. Rata SALDATA soft-deleted
    assert client.get(f"/api/rates/{rate['id']}", headers=auth_headers).status_code == 404

    # 3. Evento detached (esiste ma senza id_contratto)
    ev = client.get(f"/api/events/{event_id}", headers=auth_headers)
    assert ev.status_code == 200
    assert ev.json()["id_contratto"] is None

    # 4. CashMovement pagamento non piu' visibile
    mr = client.get("/api/movements?anno=2026&mese=2", headers=auth_headers)
    contract_movements = [m for m in mr.json()["items"] if m.get("id_contratto") == contract["id"]]
    assert len(contract_movements) == 0


# ── Credit engine: contratti chiusi ──


def test_credits_include_closed_contracts(client, auth_headers, sample_client):
    """Crediti residui includono contratti chiusi (chiuso non invalida crediti)."""
    # Crea contratto con 5 crediti
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Test 5",
        "crediti_totali": 5,
        "prezzo_totale": 500.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert cr.status_code == 201
    contract = cr.json()

    # Chiudi il contratto
    client.put(f"/api/contracts/{contract['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    # Crediti del cliente devono includere i 5 del contratto chiuso
    cl = client.get(f"/api/clients/{sample_client['id']}", headers=auth_headers)
    assert cl.json()["crediti_residui"] == 5


# ── KPI fatturato/incassato: contratti chiusi inclusi (INC-2026-06-08) ──


def test_kpi_fatturato_includes_closed_contracts(client, auth_headers, sample_client):
    """KPI fatturato e incassato devono includere contratti chiusi.

    Regressione INC-2026-06-08: chiudere un contratto saldato faceva
    calare i KPI, dando l'impressione di fatturato in declino.
    """
    # Crea 2 contratti
    c1 = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Aperto",
        "prezzo_totale": 1000.0,
        "crediti_totali": 10,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert c1.status_code == 201

    c2 = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Da chiudere",
        "prezzo_totale": 500.0,
        "crediti_totali": 5,
        "data_inizio": "2026-01-01",
        "data_scadenza": "2026-12-31",
    }, headers=auth_headers)
    assert c2.status_code == 201

    # KPI prima della chiusura
    r1 = client.get("/api/contracts", headers=auth_headers)
    assert r1.status_code == 200
    fatturato_before = r1.json()["kpi_fatturato"]

    # Chiudi il secondo contratto
    client.put(f"/api/contracts/{c2.json()['id']}", json={
        "chiuso": True,
    }, headers=auth_headers)

    # KPI dopo la chiusura — DEVE restare uguale
    r2 = client.get("/api/contracts", headers=auth_headers)
    assert r2.status_code == 200
    fatturato_after = r2.json()["kpi_fatturato"]

    assert fatturato_after == fatturato_before, (
        f"kpi_fatturato calato da {fatturato_before} a {fatturato_after} "
        f"dopo chiusura contratto — regressione INC-2026-06-08"
    )


# ── SPEC_VOCABOLARIO: campi derivati dal SSoT su lista + dettaglio ──


def test_list_contracts_exposes_ssot_derived_fields(client, auth_headers, sample_contract):
    """AC-2/AC-2b/AC-3: lista e dettaglio espongono lifecycle/money_substate/is_insolvente/in_scadenza
    derivati dal SSoT, coerenti coi KPI e mutuamente esclusivi (is_insolvente vs in_scadenza)."""
    valid_life = {"attivo", "sospeso", "esaurito", "chiuso"}
    valid_money = {"saldato", "da_pianificare", "parziale", "pianificato"}

    r = client.get("/api/contracts", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    items = body["items"]
    assert items, "atteso almeno un contratto (sample_contract)"

    for it in items:
        assert it["lifecycle"] in valid_life
        assert it["money_substate"] in valid_money
        assert isinstance(it["is_insolvente"], bool)
        assert isinstance(it["in_scadenza"], bool)
        # AC-2b: mai entrambi accesi (uno scaduto, l'altro ATTIVO-non-scaduto)
        assert not (it["is_insolvente"] and it["in_scadenza"])

    # AC-2: i KPI headline coincidono col conteggio dei lifecycle delle righe (stessa fonte)
    if body["total"] <= body["page_size"]:
        assert body["kpi_attivi"] == sum(1 for it in items if it["lifecycle"] == "attivo")
        assert body["kpi_sospesi"] == sum(1 for it in items if it["lifecycle"] == "sospeso")
        assert body["kpi_esauriti"] == sum(1 for it in items if it["lifecycle"] == "esaurito")

    # sample_contract: residuo 800 > 0, ZERO rate → asserzioni date-robuste
    row = next(it for it in items if it["id"] == sample_contract["id"])
    assert row["money_substate"] == "da_pianificare"  # residuo>0 + zero rate
    assert row["is_insolvente"] is False               # zero rate ⇒ niente rate scadute

    # AC-3: il dettaglio espone gli stessi 4 campi
    rd = client.get(f"/api/contracts/{sample_contract['id']}", headers=auth_headers)
    assert rd.status_code == 200
    d = rd.json()
    assert d["lifecycle"] in valid_life
    assert d["money_substate"] == "da_pianificare"
    assert d["is_insolvente"] is False
    assert "in_scadenza" in d


def test_renew_chain_items_carry_lifecycle(client, auth_headers, sample_contract, sample_client):
    """AC-13b (G3): i nodi della catena rinnovi (RenewalChainItem) portano il PROPRIO lifecycle reale,
    su genitore (contratto_originale) e figli (rinnovi_successivi)."""
    valid_life = {"attivo", "sospeso", "esaurito", "chiuso"}

    # Rinnova sample_contract → nuovo contratto figlio collegato (rinnovo_di = parent)
    r = client.post(f"/api/contracts/{sample_contract['id']}/renew", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Gold 10 (rinnovo)",
        "crediti_totali": 10,
        "prezzo_totale": 1000.0,
        "data_inizio": "2027-01-01",
        "data_scadenza": "2027-12-31",
        "acconto": 0.0,
        "metodo_acconto": "CONTANTI",
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    renewed_id = r.json()["id"]

    # Dettaglio del FIGLIO → il genitore porta lifecycle (non solo `chiuso`)
    rd = client.get(f"/api/contracts/{renewed_id}", headers=auth_headers)
    assert rd.status_code == 200
    parent = rd.json()["contratto_originale"]
    assert parent is not None and parent["id"] == sample_contract["id"]
    assert parent["lifecycle"] in valid_life

    # Dettaglio del GENITORE → il figlio porta lifecycle
    rp = client.get(f"/api/contracts/{sample_contract['id']}", headers=auth_headers)
    assert rp.status_code == 200
    children = rp.json()["rinnovi_successivi"]
    assert children and children[0]["id"] == renewed_id
    assert children[0]["lifecycle"] in valid_life


# ── PREREQ-prezzo (FDM §9.5.7): invariante prezzo_totale > 0 ──


def test_create_contract_zero_price_rejected(client, auth_headers, sample_client):
    """AC-B1/B2: POST con prezzo_totale=0 → 422 con messaggio italiano didattico, contratto NON creato."""
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Senza prezzo",
        "crediti_totali": 10,
        "prezzo_totale": 0.0,
        "data_inizio": "2026-07-01",
        "data_scadenza": "2026-12-31",
        "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 422
    # AC-B2: messaggio IT didattico (non default Pydantic), comunica il perché (coperture/incassi)
    body = str(r.json()).lower()
    assert "prezzo" in body and "copertur" in body


def test_update_contract_zero_price_rejected(client, auth_headers, sample_contract):
    """Leak di update chiuso: PUT con prezzo_totale=0 → 422 (non si azzera il prezzo a posteriori)."""
    r = client.put(f"/api/contracts/{sample_contract['id']}", json={
        "prezzo_totale": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 422
    assert "prezzo" in str(r.json()).lower()


def test_renew_zero_price_rejected(client, auth_headers, sample_contract, sample_client):
    """AC-B3: renew_contract usa ContractCreate → eredita il vincolo prezzo>0."""
    r = client.post(f"/api/contracts/{sample_contract['id']}/renew", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Rinnovo senza prezzo",
        "crediti_totali": 10,
        "prezzo_totale": 0.0,
        "data_inizio": "2027-01-01",
        "data_scadenza": "2027-12-31",
        "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 422
