"""
SPEC_G7.0 — schema terminazione + marcatura COMPLETAMENTO (AC-7.0-3/5/6).

G7.0 NON termina nulla: rende il sistema *capace di rappresentare* una terminazione (colonne +
response) e marca il completamento con `motivo_chiusura = COMPLETAMENTO` (load-bearing per la
reopen-allowlist di G7.2). `residuo()` NON cambia (è G7.1); nessun endpoint di terminazione (G7.3+).
"""

from datetime import date, timedelta

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()
TERMINATION_FIELDS = ("totale_rimborsato", "quota_stornata", "data_chiusura", "motivo_chiusura", "netto_incassato")
VALID_MOTIVI = {"COMPLETAMENTO", "CONSUNZIONE", "TERMINAZIONE_RIMBORSO", "TERMINAZIONE_DECADENZA"}


def _mini_contract(client, auth_headers, client_id, *, prezzo, acconto, crediti):
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


def _pt_event(client, auth_headers, client_id, contract_id):
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T09:00:00", "data_fine": f"{TODAY.isoformat()}T09:30:00",
        "categoria": "PT", "titolo": "Seduta", "id_cliente": client_id, "id_contratto": contract_id,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


# ── AC-7.0-6: lista, dettaglio e response base espongono i 5 campi ─


def test_list_and_detail_expose_termination_fields(client, auth_headers, sample_contract):
    row = next(it for it in client.get("/api/contracts", headers=auth_headers).json()["items"]
               if it["id"] == sample_contract["id"])
    for f in TERMINATION_FIELDS:
        assert f in row, f"manca {f} nella lista"
    assert row["totale_rimborsato"] == 0 and row["quota_stornata"] == 0
    assert row["data_chiusura"] is None and row["motivo_chiusura"] is None
    # netto_incassato oggi == totale_versato (nessun rimborso esiste ancora); sample_contract acconto 200
    assert row["netto_incassato"] == row["totale_versato"] == 200.0

    d = client.get(f"/api/contracts/{sample_contract['id']}", headers=auth_headers).json()
    for f in TERMINATION_FIELDS:
        assert f in d, f"manca {f} nel dettaglio"
    assert d["netto_incassato"] == d["totale_versato"]


def test_base_response_exposes_termination_fields(client, auth_headers, sample_client):
    """La ContractResponse base (POST) espone i 5 campi → il base Contract TS è accurato."""
    r = _mini_contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    for f in TERMINATION_FIELDS:
        assert f in r, f"manca {f} nella response base POST"
    assert r["netto_incassato"] == 0.0


# ── AC-7.0-3: i due percorsi di completamento marcano COMPLETAMENTO ─


def test_completamento_via_pay_rate_marks_motivo(client, auth_headers, sample_client):
    """Auto-close inline di pay_rate (saldato + crediti esauriti) → motivo_chiusura = COMPLETAMENTO."""
    c = _mini_contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])  # esaurisce l'unico credito
    rr = client.post("/api/rates", json={
        "id_contratto": c["id"], "data_scadenza": FUTURE, "importo_previsto": 100.0,
    }, headers=auth_headers)
    pr = client.post(f"/api/rates/{rr.json()['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert pr.status_code == 200, pr.text
    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["chiuso"] is True
    assert d["motivo_chiusura"] == "COMPLETAMENTO"


def test_completamento_via_agenda_marks_motivo(client, auth_headers, sample_client):
    """Auto-close di _sync_contract_chiuso (evento che esaurisce i crediti su contratto SALDATO)
    → motivo_chiusura = COMPLETAMENTO."""
    c = _mini_contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])  # chiude via _sync_contract_chiuso
    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["chiuso"] is True
    assert d["motivo_chiusura"] == "COMPLETAMENTO"


# ── AC-7.0-5: enum esaustivo + NULL ammesso per i non-chiusi ────────


def test_motivo_chiusura_enum_and_null(client, auth_headers, sample_client):
    # contratto vivo (non chiuso) → motivo_chiusura NULL
    c = _mini_contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    assert client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()["motivo_chiusura"] is None
    # chiuso per completamento → motivo valorizzato ∈ enum a 4
    _pt_event(client, auth_headers, sample_client["id"], c["id"])
    rr = client.post("/api/rates", json={
        "id_contratto": c["id"], "data_scadenza": FUTURE, "importo_previsto": 100.0,
    }, headers=auth_headers)
    client.post(f"/api/rates/{rr.json()['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    motivo = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()["motivo_chiusura"]
    assert motivo in VALID_MOTIVI
    assert motivo == "COMPLETAMENTO"
