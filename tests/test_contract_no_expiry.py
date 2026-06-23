"""
Contratti senza scadenza (carnet a crediti) — FDM §2, audit Contract 2026-06-23.

I pacchetti/carnet a crediti senza termine sono un'offerta reale: `data_scadenza` è
nullable a creazione. Il SSoT (`contract_state.py`) è null-safe end-to-end → un contratto
senza scadenza resta ATTIVO finché non si esauriscono i crediti (auto-close), non scade mai
per data. Questi test blindano il boundary (ContractCreate) e la derivazione di stato.
"""
from datetime import date

from api.services import contract_state as cstate


# ── Boundary: ContractCreate accetta l'assenza di scadenza ─────────────

def test_create_contract_without_data_scadenza(client, auth_headers, sample_client):
    """Omettere data_scadenza → 201, contratto persistito con scadenza null."""
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Carnet 10",
        "crediti_totali": 10,
        "prezzo_totale": 500.0,
        "data_inizio": "2026-01-01",
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    assert r.json()["data_scadenza"] is None


def test_create_contract_with_explicit_null_scadenza(client, auth_headers, sample_client):
    """data_scadenza esplicitamente null → 201 (idem all'omissione)."""
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Carnet open",
        "crediti_totali": 5,
        "prezzo_totale": 250.0,
        "data_inizio": "2026-01-01",
        "data_scadenza": None,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    assert r.json()["data_scadenza"] is None


def test_no_expiry_contract_is_attivo_in_list(client, auth_headers, sample_client):
    """Un carnet senza scadenza NON è mai 'sospeso/esaurito per data' → lifecycle ATTIVO."""
    client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Carnet 8",
        "crediti_totali": 8,
        "prezzo_totale": 400.0,
        "data_inizio": "2020-01-01",  # data inizio nel passato, ma senza scadenza non scade
    }, headers=auth_headers)
    r = client.get("/api/contracts", headers=auth_headers)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    carnet = next(c for c in items if c["tipo_pacchetto"] == "Carnet 8")
    assert carnet["data_scadenza"] is None
    assert carnet["lifecycle"] == "attivo"


def test_rate_on_no_expiry_contract_has_no_boundary(client, auth_headers, sample_client):
    """La rate boundary (#9) è null-safe: senza scadenza contratto, nessun cap di data."""
    cr = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"],
        "tipo_pacchetto": "Carnet rate",
        "crediti_totali": 4,
        "prezzo_totale": 200.0,
        "data_inizio": "2026-01-01",
    }, headers=auth_headers)
    contract_id = cr.json()["id"]
    # Una rata con scadenza lontana nel futuro: senza cap del contratto deve passare.
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": "2030-06-01",
        "importo_previsto": 200.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text


# ── SSoT puro: derivazione null-safe ───────────────────────────────────

class _FakeContract:
    """Stub minimale per le funzioni pure di contract_state."""
    def __init__(self, data_scadenza, crediti_totali=10, chiuso=False):
        self.data_scadenza = data_scadenza
        self.crediti_totali = crediti_totali
        self.prezzo_totale = 100.0
        self.totale_versato = 0.0
        self.chiuso = chiuso
        self.deleted_at = None


def test_ssot_no_expiry_never_scaduto():
    c = _FakeContract(data_scadenza=None)
    today = date(2030, 1, 1)
    assert cstate.is_scaduto(c, today) is False
    assert cstate.is_vigente(c, today) is True
    assert cstate.is_in_scadenza(c, today) is False
    # Senza scadenza + crediti residui → ATTIVO (non SOSPESO/ESAURITO).
    assert cstate.contract_lifecycle(c, crediti_usati=2, today=today) == cstate.Lifecycle.ATTIVO
