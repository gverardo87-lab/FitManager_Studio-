"""G7.8-bis (ADR-017 Addendum I) — Late Cancel & No Show: le 3 tesi falsificabili della SPEC.

T1 — le penali OCCUPANO il credito ma non la performance (crediti_usati le conta, le erogate vere no).
T2 — asse scientifico intatto: `count_sedute_erogate` resta SOLO-Completato (D-CONTEGGI-SEPARATI).
T3 — settlement: le penali CONTABILIZZANO nel conguaglio (D-RECESSO-PENALE): 10×€100 versato 1000,
     6 Completato + 1 Cancellato_Tardivo + 1 No_Show → contabilizzato €800 → rimborso €200.
+ D-CALENDAR-OVERLAP (le penali liberano lo slot) + D-CREDIT-CONSUMPTION (auto-close a saturazione
con penali) + validazione stati agenda.
"""

from datetime import date, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.services.financial.transitions import count_sedute_erogate, count_sedute_penali

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _contract(client, auth_headers, client_id, *, prezzo=1000.0, acconto=0.0, crediti=10):
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


def _event(client, auth_headers, client_id, contract_id, stato, day, hour):
    r = client.post("/api/events", json={
        "titolo": "PT", "categoria": "PT", "stato": stato,
        "id_cliente": client_id, "id_contratto": contract_id,
        "data_inizio": f"2026-01-{day:02d}T{hour:02d}:00:00",
        "data_fine": f"2026-01-{day:02d}T{hour + 1:02d}:00:00",
    }, headers=auth_headers)
    return r


# ── T1 — le penali occupano il credito ──────────────────────────────────────

def test_t1_penali_occupano_credito(client, auth_headers, sample_client, session):
    """1 Completato + 1 Programmato + 1 Cancellato_Tardivo + 1 No_Show + 1 Rinviato su 10 crediti
    → usati 4 (il Rinviato libera), residui 6."""
    c = _contract(client, auth_headers, sample_client["id"])
    for i, stato in enumerate(["Completato", "Programmato", "Cancellato_Tardivo", "No_Show", "Rinviato"]):
        r = _event(client, auth_headers, sample_client["id"], c["id"], stato, day=5 + i, hour=9)
        assert r.status_code in (200, 201), f"{stato}: {r.text}"
    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert detail["crediti_usati"] == 4
    assert detail["crediti_residui"] == 6
    assert detail["sedute_completate"] == 1          # erogate vere: solo Completato
    assert detail["sedute_penali"] == 2              # trasparenza: penali separate dalle svolte
    assert detail["sedute_rinviate"] == 1


def test_g973_lista_espone_penali_e_residui(client, auth_headers, sample_client, session):
    """G9.7.3 (D2/D3/D4): la LISTA contratti porta sedute_penali e crediti_residui sul wire —
    il sub-label «N svolte · M penali» e il DeleteContractDialog LEGGONO, mai ricalcolo inline.
    Stessi numeri del dettaglio (un solo interprete)."""
    c = _contract(client, auth_headers, sample_client["id"])
    for i, stato in enumerate(["Completato", "Programmato", "Cancellato_Tardivo", "No_Show", "Rinviato"]):
        r = _event(client, auth_headers, sample_client["id"], c["id"], stato, day=12 + i, hour=9)
        assert r.status_code in (200, 201), f"{stato}: {r.text}"

    row = next(x for x in client.get("/api/contracts", headers=auth_headers).json()["items"]
               if x["id"] == c["id"])
    assert row["crediti_usati"] == 4
    assert row["crediti_residui"] == 6               # D4: sul wire, come nel dettaglio
    assert row["sedute_completate"] == 1
    assert row["sedute_penali"] == 2                 # D2/D3: penali separate dalle svolte

    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert (row["crediti_residui"], row["sedute_penali"]) == (
        detail["crediti_residui"], detail["sedute_penali"]
    )                                                # lista e dettaglio: un solo interprete


# ── T2 — asse scientifico/erogato intatto ───────────────────────────────────

def test_t2_erogate_vere_ignorano_penali(client, auth_headers, sample_client, session):
    """`count_sedute_erogate` (base dell'asse EROGATO/scientifico) resta SOLO-Completato;
    `count_sedute_penali` conta il resto. D-CONTEGGI-SEPARATI: mai fusi."""
    c = _contract(client, auth_headers, sample_client["id"])
    _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5, hour=9)
    _event(client, auth_headers, sample_client["id"], c["id"], "Cancellato_Tardivo", day=6, hour=9)
    _event(client, auth_headers, sample_client["id"], c["id"], "No_Show", day=7, hour=9)
    assert count_sedute_erogate(session, c["id"]) == 1
    assert count_sedute_penali(session, c["id"]) == 2


# ── T3 — settlement: le penali contabilizzano nel conguaglio ────────────────

def test_t3_settlement_contabilizza_penali(client, auth_headers, sample_client, session):
    """10×€100, versato 1000: 6 Completato + 2 penali → contabilizzato €800 → CREDITO_CLIENTE 200."""
    c = _contract(client, auth_headers, sample_client["id"], acconto=1000.0)
    for i in range(6):
        _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5 + i, hour=9)
    _event(client, auth_headers, sample_client["id"], c["id"], "Cancellato_Tardivo", day=12, hour=9)
    _event(client, auth_headers, sample_client["id"], c["id"], "No_Show", day=13, hour=9)

    prev = client.get(f"/api/contracts/{c['id']}/settlement-preview", headers=auth_headers)
    assert prev.status_code == 200, prev.text
    p = prev.json()
    assert p["esito"] == "CREDITO_CLIENTE"
    assert round(p["importo_rimborso"], 2) == 200.0          # 1000 − 800 contabilizzato
    assert round(p["valore_servizio_reso"], 2) == 800.0      # 6 vere + 2 penali (D-RECESSO-PENALE)
    assert p["sedute_penali"] == 2                           # trasparenza in preview

    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == 200.0
    uscite = [m for m in session.exec(select(CashMovement).where(
        CashMovement.id_contratto == c["id"], CashMovement.tipo == "USCITA")).all()]
    assert len(uscite) == 1 and round(uscite[0].importo, 2) == 200.0


def test_t3_audit_snapshot_separati(client, auth_headers, sample_client, session):
    """D-CONTEGGI-SEPARATI: l'audit della terminazione registra erogate VERE e penali distinte."""
    import json
    from api.models.audit_log import AuditLog
    c = _contract(client, auth_headers, sample_client["id"], acconto=1000.0)
    for i in range(6):
        _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5 + i, hour=9)
    _event(client, auth_headers, sample_client["id"], c["id"], "No_Show", day=12, hour=9)
    _event(client, auth_headers, sample_client["id"], c["id"], "Cancellato_Tardivo", day=13, hour=9)
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    entries = session.exec(select(AuditLog).where(
        AuditLog.entity_type == "contract", AuditLog.entity_id == c["id"])).all()
    payloads = [json.loads(e.changes) for e in entries if e.changes and "sedute_penali_snapshot" in e.changes]
    assert payloads, "audit snapshot con conteggi separati non trovato"
    snap = payloads[0]
    assert snap["sedute_erogate_snapshot"] == 6
    assert snap["sedute_penali_snapshot"] == 2
    assert snap["sedute_contabilizzate_snapshot"] == 8


# ── D-CALENDAR-OVERLAP — le penali liberano lo slot ─────────────────────────

def test_overlap_penale_libera_slot(client, auth_headers, sample_client, session):
    """Un No_Show nello slot NON blocca una nuova prenotazione nello stesso orario;
    un Programmato sì (asse calendario ≠ asse credito)."""
    c = _contract(client, auth_headers, sample_client["id"])
    r1 = _event(client, auth_headers, sample_client["id"], c["id"], "No_Show", day=5, hour=9)
    assert r1.status_code in (200, 201), r1.text
    r2 = _event(client, auth_headers, sample_client["id"], c["id"], "Programmato", day=5, hour=9)
    assert r2.status_code in (200, 201), r2.text            # slot libero nonostante il No_Show
    r3 = _event(client, auth_headers, sample_client["id"], c["id"], "Programmato", day=5, hour=9)
    assert r3.status_code == 409                            # il Programmato invece lo blocca


# ── D-CREDIT-CONSUMPTION — auto-close a saturazione con penali ──────────────

def test_auto_close_scatta_con_penali(client, auth_headers, sample_client, session):
    """Contratto 2 crediti SALDATO: 1 Completato + 1 No_Show = saturazione → chiuso COMPLETAMENTO."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=200.0, acconto=200.0, crediti=2)
    _event(client, auth_headers, sample_client["id"], c["id"], "Completato", day=5, hour=9)
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is False
    _event(client, auth_headers, sample_client["id"], c["id"], "No_Show", day=6, hour=9)
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True
    assert contract.motivo_chiusura == "COMPLETAMENTO"


# ── Validazione stati agenda ─────────────────────────────────────────────────

def test_stati_penale_validi_e_stato_inventato_rifiutato(client, auth_headers, sample_client):
    c = _contract(client, auth_headers, sample_client["id"])
    ok = _event(client, auth_headers, sample_client["id"], c["id"], "Cancellato_Tardivo", day=5, hour=9)
    assert ok.status_code in (200, 201), ok.text
    bad = _event(client, auth_headers, sample_client["id"], c["id"], "Fantasma", day=6, hour=9)
    assert bad.status_code == 422


# ── G9.7.3/D5 — le worklist dashboard espongono il breakdown occupazione ─────

def test_g973_d5_suspended_contracts_espone_breakdown(client, auth_headers, sample_client):
    """G9.7.3/D5: la worklist SOSPESI porta sedute_completate + sedute_penali sul wire —
    il sub-label «N svolte · M penali» LEGGE, mai ricalcolo inline. Stessi numeri del
    dettaglio contratto (un solo interprete: _occupazione_breakdown_map)."""
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Pkg", "crediti_totali": 10,
        "prezzo_totale": 1000.0, "data_inizio": (TODAY - timedelta(days=120)).isoformat(),
        "data_scadenza": (TODAY - timedelta(days=30)).isoformat(), "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    c = r.json()
    for i, stato in enumerate(["Completato", "Completato", "Cancellato_Tardivo", "No_Show", "Rinviato"]):
        er = _event(client, auth_headers, sample_client["id"], c["id"], stato, day=5 + i, hour=9)
        assert er.status_code in (200, 201), f"{stato}: {er.text}"

    data = client.get("/api/dashboard/suspended-contracts", headers=auth_headers).json()
    item = next(x for x in data["items"] if x["contract_id"] == c["id"])
    assert item["crediti_usati"] == 4                # 2 svolte + 2 penali; Rinviato libera
    assert item["crediti_residui"] == 6
    assert item["sedute_completate"] == 2
    assert item["sedute_penali"] == 2

    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert (item["crediti_usati"], item["sedute_completate"], item["sedute_penali"]) == (
        detail["crediti_usati"], detail["sedute_completate"], detail["sedute_penali"]
    )                                                # worklist e dettaglio: un solo interprete


def test_g973_d5_expiring_contracts_espone_breakdown(client, auth_headers, sample_client):
    """G9.7.3/D5: la worklist IN SCADENZA porta sedute_completate + sedute_penali sul wire,
    coerenti col dettaglio (un solo interprete)."""
    r = client.post("/api/contracts", json={
        "id_cliente": sample_client["id"], "tipo_pacchetto": "Pkg", "crediti_totali": 10,
        "prezzo_totale": 1000.0, "data_inizio": TODAY.isoformat(),
        "data_scadenza": (TODAY + timedelta(days=10)).isoformat(), "acconto": 0.0,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    c = r.json()
    for i, stato in enumerate(["Completato", "Programmato", "Cancellato_Tardivo", "Rinviato"]):
        er = _event(client, auth_headers, sample_client["id"], c["id"], stato, day=5 + i, hour=9)
        assert er.status_code in (200, 201), f"{stato}: {er.text}"

    data = client.get("/api/dashboard/expiring-contracts", headers=auth_headers).json()
    item = next(x for x in data["items"] if x["contract_id"] == c["id"])
    assert item["crediti_usati"] == 3                # Completato + Programmato + penale
    assert item["crediti_residui"] == 7
    assert item["sedute_completate"] == 1
    assert item["sedute_penali"] == 1

    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert (item["crediti_usati"], item["sedute_completate"], item["sedute_penali"]) == (
        detail["crediti_usati"], detail["sedute_completate"], detail["sedute_penali"]
    )

