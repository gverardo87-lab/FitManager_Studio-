"""
Test SPEC_GESTIONE_FINANZIARIA_TEMPORALE — Layer 1 (incassato per periodo, cassa).

Endpoint GET /api/movements/financial-trend:
- partizione incassi_contratti (id_contratto) vs altri_incassi (fuori contratto)
- esclusione storni (STORNO_SPESA_FISSA) da incassi, altri e cash flow reale
- bucket per mese su data_effettiva
- multi-tenant + finestra vuota
"""

from datetime import date, timedelta


def _manual_entrata(client, auth_headers, importo, data_eff, categoria=None):
    body = {"importo": importo, "tipo": "ENTRATA", "data_effettiva": data_eff.isoformat()}
    if categoria:
        body["categoria"] = categoria
    r = client.post("/api/movements", json=body, headers=auth_headers)
    assert r.status_code == 201, f"Movement create failed: {r.text}"
    return r.json()


def _storno_reale(session, trainer_id, importo, data_eff):
    """Storno VERO (id_spesa_ricorrente≠NULL) via ORM — simula il writer di recurring_expenses.
    G9.4-bis.2: la categoria STORNO è riservata (write-guard 422 sul manuale) e l'esclusione dal
    trend avviene per CLASSE (RETTIFICA_COSTO_FISSO = struttura), non più per stringa."""
    from api.models.movement import CashMovement
    session.add(CashMovement(
        trainer_id=trainer_id, tipo="ENTRATA", categoria="STORNO_SPESA_FISSA",
        importo=importo, data_effettiva=data_eff, id_spesa_ricorrente=999, operatore="TEST",
    ))
    session.commit()


def _pay_rate_today(client, auth_headers, contract_id, importo):
    today = date.today()
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": "2026-12-31",
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    rate_id = r.json()["id"]
    p = client.post(f"/api/rates/{rate_id}/pay", json={
        "importo": importo, "metodo": "CONTANTI", "data_pagamento": today.isoformat(),
    }, headers=auth_headers)
    assert p.status_code == 200, p.text


def _current_period(data, today):
    return next(p for p in data["periodi"] if p["anno"] == today.year and p["mese"] == today.month)


def test_trend_partitions_and_excludes_storno(client, auth_headers, sample_contract, session):
    """Mese corrente: rata→incassi_contratti, manuale→altri_incassi, storno (CLASSE) escluso."""
    today = date.today()
    cid = sample_contract["id"]

    _pay_rate_today(client, auth_headers, cid, 300.0)            # PAGAMENTO_RATA (id_contratto)
    _manual_entrata(client, auth_headers, 50.0, today)           # altri incassi (id_contratto NULL)
    from api.models.trainer import Trainer as _T
    from sqlmodel import select as _sel
    _tid = session.exec(_sel(_T)).first().id
    _storno_reale(session, _tid, 999.0, today)                   # RETTIFICA_COSTO_FISSO → esclusa

    r = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()

    cur = _current_period(data, today)
    assert cur["incassi_contratti"] == 300.0          # rata di oggi (acconto è dated 2026-01-01)
    assert cur["altri_incassi"] == 50.0               # storno 999 NON conteggiato
    assert cur["cash_flow_reale"] == 350.0
    # lo storno non entra nei totali altri/cash flow
    assert data["tot_altri_incassi"] == 50.0


def test_trend_buckets_by_month(client, auth_headers):
    """Due ENTRATA manuali in mesi diversi finiscono in bucket distinti."""
    today = date.today()
    prev_month_day = today.replace(day=1) - timedelta(days=15)  # garantito mese precedente

    _manual_entrata(client, auth_headers, 100.0, today)
    _manual_entrata(client, auth_headers, 70.0, prev_month_day)

    data = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers).json()

    cur = _current_period(data, today)
    assert cur["altri_incassi"] == 100.0
    prev = next(p for p in data["periodi"]
                if p["anno"] == prev_month_day.year and p["mese"] == prev_month_day.month)
    assert prev["altri_incassi"] == 70.0
    assert data["tot_altri_incassi"] == 170.0
    assert data["tot_cash_flow_reale"] == 170.0


def test_trend_venduto_competenza(client, auth_headers, sample_contract):
    """Venduto (competenza) su data_vendita, distinto dalla cassa: contratto venduto oggi → venduto del mese."""
    today = date.today()
    data = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers).json()

    cur = _current_period(data, today)
    assert cur["venduto"] == 1000.0          # sample_contract prezzo_totale, data_vendita = oggi
    assert data["tot_venduto"] == 1000.0
    # cassa e competenza sono assi distinti: l'acconto (gen 2026) non entra nel venduto del mese,
    # e il venduto non entra nella cassa del mese corrente
    assert cur["incassi_contratti"] == 0.0
    assert cur["cash_flow_reale"] == 0.0


def test_trend_composition_nuovo_rate(client, auth_headers, sample_contract):
    """Composizione: contratto nuovo, rata oggi → nuovi+rate; riconcilia con incassi_contratti."""
    today = date.today()
    _pay_rate_today(client, auth_headers, sample_contract["id"], 300.0)
    data = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers).json()
    cur = _current_period(data, today)

    # riconciliazione: ogni taglio somma a incassi_contratti
    assert round(cur["incassi_nuovi"] + cur["incassi_rinnovi"], 2) == cur["incassi_contratti"]
    assert round(cur["incassi_acconti"] + cur["incassi_rate"], 2) == cur["incassi_contratti"]
    # sample_contract è nuovo (rinnovo_di NULL); l'incasso di oggi è una rata
    assert cur["incassi_nuovi"] == 300.0
    assert cur["incassi_rinnovi"] == 0.0
    assert cur["incassi_acconti"] == 0.0
    assert cur["incassi_rate"] == 300.0


def test_trend_composition_rinnovo_acconto(client, auth_headers, sample_contract):
    """Composizione: rinnovo con acconto oggi → rinnovi+acconti."""
    today = date.today()
    r = client.post(f"/api/contracts/{sample_contract['id']}/renew", json={
        "id_cliente": sample_contract["id_cliente"],
        "tipo_pacchetto": "Rinnovo",
        "crediti_totali": 10,
        "prezzo_totale": 500.0,
        "data_inizio": today.isoformat(),
        "data_scadenza": "2026-12-31",
        "acconto": 100.0,
        "metodo_acconto": "CONTANTI",
    }, headers=auth_headers)
    assert r.status_code == 201, r.text

    data = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers).json()
    cur = _current_period(data, today)
    assert cur["incassi_rinnovi"] == 100.0   # contratto-figlio (rinnovo_di valorizzato)
    assert cur["incassi_nuovi"] == 0.0
    assert cur["incassi_acconti"] == 100.0   # acconto del rinnovo
    assert cur["incassi_rate"] == 0.0
    assert cur["incassi_contratti"] == 100.0


def test_trend_window_length_and_chronology(client, auth_headers):
    """`mesi` periodi, cronologici, ultimo = mese corrente."""
    today = date.today()
    data = client.get("/api/movements/financial-trend?mesi=6", headers=auth_headers).json()
    assert data["mesi"] == 6
    assert len(data["periodi"]) == 6
    last = data["periodi"][-1]
    assert (last["anno"], last["mese"]) == (today.year, today.month)
    # ordine cronologico crescente
    keys = [(p["anno"], p["mese"]) for p in data["periodi"]]
    assert keys == sorted(keys)


def test_trend_empty_all_zero(client, auth_headers):
    """Nessun movimento → periodi pieni di zeri, totali a zero."""
    data = client.get("/api/movements/financial-trend?mesi=12", headers=auth_headers).json()
    assert len(data["periodi"]) == 12
    assert data["tot_incassi_contratti"] == 0.0
    assert data["tot_altri_incassi"] == 0.0
    assert data["tot_cash_flow_reale"] == 0.0
    assert all(p["cash_flow_reale"] == 0.0 for p in data["periodi"])


def test_monthly_revenue_only_contract_incassi(client, auth_headers, sample_contract):
    """dashboard/summary monthly_revenue = solo incassi da contratti del mese (no storni, no altri)."""
    today = date.today()
    cid = sample_contract["id"]
    _pay_rate_today(client, auth_headers, cid, 300.0)                 # incasso da contratto (mese corrente)
    _manual_entrata(client, auth_headers, 50.0, today)               # altri incassi → ESCLUSO
    # (lo storno-manuale mislabeled non esiste più: write-guard 422, vedi test_write_guard sotto)

    r = client.get("/api/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["monthly_revenue"] == 300.0


def test_trend_multi_tenant(client, auth_headers, sample_contract):
    """Trainer B non vede gli incassi di Trainer A."""
    today = date.today()
    _manual_entrata(client, auth_headers, 100.0, today)

    other = client.post("/api/auth/register", json={
        "email": "other@test.com", "nome": "Other", "cognome": "Trainer", "password": "otherpass123",
    })
    assert other.status_code == 201, other.text
    other_headers = {"Authorization": f"Bearer {other.json()['access_token']}"}

    data = client.get("/api/movements/financial-trend?mesi=12", headers=other_headers).json()
    assert data["tot_cash_flow_reale"] == 0.0


def test_write_guard_categorie_riservate(client, auth_headers):
    """G9.4-bis.2 (ADR-022 Add. II): un movimento MANUALE con categoria riservata (contrattuale o
    storno) è rifiutato 422 — chiude la cella ambigua stringa-riservata/struttura-libera che faceva
    divergere trend (esclusione per stringa) e stats (conteggio per struttura)."""
    today = date.today()
    for categoria, tipo in [
        ("STORNO_SPESA_FISSA", "ENTRATA"),
        ("PAGAMENTO_RATA", "ENTRATA"),
        ("ACCONTO_CONTRATTO", "ENTRATA"),
        ("INCASSO_CONGUAGLIO_CONTRATTO", "ENTRATA"),
        ("RIMBORSO_CONTRATTO", "USCITA"),
    ]:
        r = client.post("/api/movements", json={
            "tipo": tipo, "categoria": categoria, "importo": 10.0,
            "data_effettiva": today.isoformat(),
        }, headers=auth_headers)
        assert r.status_code == 422, f"{categoria}: {r.status_code} {r.text}"
        assert "riservata" in r.json()["detail"]
