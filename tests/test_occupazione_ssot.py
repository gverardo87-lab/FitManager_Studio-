"""G7.8-bis-prep — SSoT del predicato occupazione credito (`STATI_OCCUPAZIONE_CREDITO`).

Enforcement semantico (lezione Giro-2/G9.3: enumerazione manuale dei siti ≠ enforcement): il predicato
vive in UN simbolo (`contract_state.STATI_OCCUPAZIONE_CREDITO`) e nessun sito può re-inlineare il
literal — né in ORM (`stato.in_([...])`) né in raw SQL (`IN ('Programmato', ...)`). Questo test è il
gemello semantico che G9.4 prescrive al posto dei grep-guard testuali: vive nella suite, fallisce sul
simbolo, non su un pattern di testo in uno script bash.
"""

from datetime import date, timedelta
from pathlib import Path

from api.services.contract_state import (
    STATI_OCCUPAZIONE_CREDITO,
    STATI_OCCUPAZIONE_SLOT,
    STATI_PENALE,
    STATI_SERVIZIO_CONTABILIZZATO,
)

TODAY = date.today()

API_DIR = Path(__file__).resolve().parent.parent / "api"
SSOT_FILE = API_DIR / "services" / "contract_state.py"
CONTRACTS_ROUTER_FILE = API_DIR / "routers" / "contracts.py"


def test_ssot_baseline_g78bis():
    """G7.8-bis (ADR-017 Addendum I): le penali OCCUPANO il credito; Rinviato/Cancellato liberano.
    L'asse CALENDARIO diverge (D-CALENDAR-OVERLAP): le penali NON bloccano lo slot orario.
    Estensione DELIBERATA della baseline G7.8 — ogni futura modifica del set passa da qui."""
    assert STATI_OCCUPAZIONE_CREDITO == frozenset(
        {"Programmato", "Completato", "Cancellato_Tardivo", "No_Show"})
    assert STATI_PENALE == frozenset({"Cancellato_Tardivo", "No_Show"})
    assert STATI_OCCUPAZIONE_SLOT == frozenset({"Programmato", "Completato"})
    assert STATI_PENALE < STATI_OCCUPAZIONE_CREDITO          # le penali sono un sottoinsieme proprio
    assert STATI_PENALE.isdisjoint(STATI_OCCUPAZIONE_SLOT)   # e non bloccano mai lo slot
    # G7.8-ter (ADR-023): l'asse CONTABILIZZATO = Completato + penali — la base del conguaglio,
    # protetta dal temporal fence. count_sedute_erogate/penali devono restare la sua partizione esatta.
    assert STATI_SERVIZIO_CONTABILIZZATO == frozenset({"Completato"}) | STATI_PENALE
    assert STATI_SERVIZIO_CONTABILIZZATO < STATI_OCCUPAZIONE_CREDITO


def test_nessun_literal_occupazione_fuori_ssot():
    """Nessun file di api/ re-inlinea il predicato occupazione: ORM `.in_(["Programmato", ...])` o
    raw SQL `IN ('Programmato', ...)`. L'unico punto di verità è il frozenset in contract_state.py."""
    violazioni = []
    for py in API_DIR.rglob("*.py"):
        if py == SSOT_FILE:
            continue
        src = py.read_text(encoding="utf-8")
        for i, line in enumerate(src.splitlines(), start=1):
            # Solo il PAIO CHIUSO esatto (predicato di conteggio a 2 stati): non matcha enum più larghi
            # come VALID_STATUSES di agenda (asse validazione-stati, legittimo e diverso).
            if '["Programmato", "Completato"]' in line or "('Programmato', 'Completato')" in line:
                violazioni.append(f"{py.relative_to(API_DIR.parent)}:{i}: {line.strip()}")
    assert not violazioni, (
        "Predicato occupazione re-inlineato fuori dal SSoT (usa STATI_OCCUPAZIONE_CREDITO):\n"
        + "\n".join(violazioni)
    )


def test_read_model_contratti_consuma_stati_penale_ssot():
    """R1.2: dettaglio e lista leggono STATI_PENALE, senza ricostruirlo da literal o insiemi vicini.

    La parita' runtime sui due stati attuali non basta: un terzo stato-penale deve propagarsi ai due
    read-model per costruzione, senza richiedere una seconda modifica in contracts.py.
    """
    src = CONTRACTS_ROUTER_FILE.read_text(encoding="utf-8")
    assert src.count("cstate.STATI_PENALE") >= 2, (
        "dettaglio e lista contratti devono consumare direttamente STATI_PENALE"
    )
    assert 'cb.get("Cancellato_Tardivo"' not in src
    assert "_STATI_PENALE =" not in src


def test_expiring_contracts_endpoint_conta_occupazione(client, auth_headers, sample_client, session):
    """Smoke del sito raw-SQL migrato (dashboard `/expiring-contracts`, ex L406): il conteggio
    crediti usati passa dal SSoT via bindparam expanding — Rinviato NON conta (ADR-017)."""
    scadenza = (TODAY + timedelta(days=10)).isoformat()
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Pkg", "crediti_totali": 10,
        "prezzo_totale": 1000.0, "data_inizio": TODAY.isoformat(), "data_scadenza": scadenza,
        "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    for hour, stato in ((9, "Completato"), (11, "Programmato"), (14, "Rinviato")):
        er = client.post("/api/events", json={
            "titolo": "PT", "categoria": "PT", "stato": stato,
            "id_cliente": sample_client["id"], "id_contratto": cid,
            "data_inizio": f"2026-01-05T{hour:02d}:00:00", "data_fine": f"2026-01-05T{hour + 1:02d}:00:00",
        }, headers=auth_headers)
        assert er.status_code in (200, 201), er.text

    resp = client.get("/api/dashboard/expiring-contracts", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    items = [i for i in resp.json()["items"] if i["contract_id"] == cid]
    assert len(items) == 1
    assert items[0]["crediti_usati"] == 2          # Completato + Programmato; Rinviato liberato


def test_partizione_contabilizzato_runtime(client, auth_headers, sample_client, session):
    """G7.8-ter (LOW del verifier): presidio RUNTIME della partizione — la base del conguaglio derivata
    da transitions (erogate + penali) DEVE coincidere col COUNT diretto su STATI_SERVIZIO_CONTABILIZZATO."""
    from sqlmodel import func, select
    from api.models.event import Event
    from api.services.contract_state import STATI_SERVIZIO_CONTABILIZZATO
    from api.services.financial.transitions import count_sedute_erogate, count_sedute_penali

    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Pkg", "crediti_totali": 10,
        "prezzo_totale": 1000.0, "data_inizio": TODAY.isoformat(),
        "data_scadenza": (TODAY + timedelta(days=120)).isoformat(), "acconto": 0.0,
    }, headers=auth_headers)
    cid = r.json()["id"]
    for day, stato in ((5, "Completato"), (6, "Completato"), (7, "No_Show"),
                       (8, "Cancellato_Tardivo"), (9, "Programmato"), (10, "Rinviato")):
        er = client.post("/api/events", json={
            "titolo": "PT", "categoria": "PT", "stato": stato,
            "id_cliente": sample_client["id"], "id_contratto": cid,
            "data_inizio": f"2026-02-{day:02d}T09:00:00", "data_fine": f"2026-02-{day:02d}T10:00:00",
        }, headers=auth_headers)
        assert er.status_code in (200, 201), er.text

    diretta = session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == cid, Event.categoria == "PT",
            Event.stato.in_(STATI_SERVIZIO_CONTABILIZZATO),
            Event.deleted_at == None,  # noqa: E711
        )
    ).one()
    assert count_sedute_erogate(session, cid) + count_sedute_penali(session, cid) == diretta == 4
