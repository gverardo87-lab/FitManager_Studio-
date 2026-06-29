"""
G8.1.1 / F6 — Storico stato/attività del contratto: `GET /contracts/{id}/history`.

Timeline CRM-grade derivata (curata) dall'`audit_log` (entity='contract'). Copre:
- ordine cronologico + tipi curati (creato → terminato → riaperto)
- dedup delle entry "companion" (la transizione lifecycle bare NON duplica la entry ricca)
- completamento (auto-close) → evento `saldato`
- la pura cassa (pagamento intermedio) NON inquina la timeline di stato (vive in F1/F5)
- bouncer: contratto inesistente/non-proprio → 404
"""

import json
from datetime import date, datetime, timedelta, timezone

from sqlmodel import select

from api.models.contract import Contract
from api.models.trainer import Trainer
from api.models.event import Event
from api.models.audit_log import AuditLog
from api.routers.contracts import _curate_contract_event

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": TODAY.isoformat(),
        "data_scadenza": FUTURE, "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _complete_pt(session, trainer_id, client_id, contract_id, n):
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i), data_fine=datetime(2026, 1, 1, 10 + i),
        ))
    session.commit()


def _history(client, auth_headers, contract_id):
    r = client.get(f"/api/contracts/{contract_id}/history", headers=auth_headers)
    assert r.status_code == 200, r.text
    return r.json()


# ── Creazione → sempre il primo evento ──────────────────────────────

def test_history_creazione(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=100.0, crediti=10)
    events = _history(client, auth_headers, c["id"])
    assert len(events) >= 1
    assert events[0]["tipo"] == "creato"
    assert events[0]["titolo"] == "Contratto creato"


# ── Terminazione: entry ricca + dedup della companion lifecycle ──────

def test_history_terminazione_ricca_senza_companion(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200

    rt = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert rt.status_code == 200, rt.text

    events = _history(client, auth_headers, c["id"])
    terminati = [e for e in events if e["tipo"] == "terminato"]
    assert len(terminati) == 1, events                       # entry ricca UNICA
    assert "motivo" in terminati[0]["dettaglio"]
    # la companion lifecycle bare (chiuso+motivo='terminazione') NON deve comparire come 'stato'
    stati_chiuso = [e for e in events if e["tipo"] == "stato" and "chius" in e["titolo"].lower()]
    assert stati_chiuso == [], events


# ── Round-trip terminate → reopen: ordine + tipi, companion deduplicate ──

def test_history_terminate_reopen_ordine(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)

    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)

    events = _history(client, auth_headers, c["id"])
    tipi = [e["tipo"] for e in events]
    assert tipi[0] == "creato"
    assert "terminato" in tipi
    assert "riaperto" in tipi
    # ordine cronologico: creato prima di terminato prima di riaperto
    assert tipi.index("creato") < tipi.index("terminato") < tipi.index("riaperto")
    # esattamente UN terminato e UN riaperto (nessuna companion duplicante)
    assert tipi.count("terminato") == 1, events
    assert tipi.count("riaperto") == 1, events


# ── Completamento (auto-close) → evento `saldato` ───────────────────

def test_history_completamento_saldato(client, auth_headers, sample_client, session):
    # acconto pieno + consuma l'unico credito → auto-close COMPLETAMENTO
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T09:00:00",
        "data_fine": f"{TODAY.isoformat()}T09:30:00",
        "categoria": "PT", "titolo": "Seduta",
        "id_cliente": sample_client["id"], "id_contratto": c["id"],
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True

    events = _history(client, auth_headers, c["id"])
    assert any(e["tipo"] == "saldato" for e in events), events


# ── La pura cassa NON inquina la timeline di stato ──────────────────

def test_history_pagamento_intermedio_non_inquina(client, auth_headers, sample_client, session):
    """Un incasso residuo che NON chiude (crediti residui) muove solo cassa → niente evento di stato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=100.0, crediti=10)
    # incassa parte del residuo senza chiudere (restano crediti) → solo cassa
    r = client.post(f"/api/contracts/{c['id']}/incassa-residuo",
                    json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    events = _history(client, auth_headers, c["id"])
    # niente "saldato"/"terminato"/"riaperto"; resta solo la creazione (la cassa è in F1/F5)
    assert [e["tipo"] for e in events] == ["creato"], events


# ── Bouncer: contratto inesistente → 404 ────────────────────────────

def test_history_contratto_inesistente_404(client, auth_headers):
    r = client.get("/api/contracts/999999/history", headers=auth_headers)
    assert r.status_code == 404


# ── Regressione (Playwright-found): riapertura in formato STORICO senza chiave 'chiuso' ──

def test_curate_riapertura_formato_storico_senza_chiuso():
    """Le riaperture in formato G8.1 mettono `motivo_chiusura.new=None` ma NON la chiave `chiuso`
    (il toggle stava SOLO nella companion lifecycle). La curation deve comunque produrre 'riaperto'
    — pretendere `chiuso` la faceva sparire dalla timeline (due 'terminato' senza 'riaperto' in mezzo)."""
    row = AuditLog(
        entity_type="contract", entity_id=1, action="UPDATE", trainer_id=1,
        changes=json.dumps({
            "motivo_chiusura": {"old": "TERMINAZIONE_RIMBORSO", "new": None},
            "totale_rimborsato": {"old": 37.0, "new": 37.0},
            "quota_stornata": {"old": 733.0, "new": 0},
            "rate_ripristinate": 1,
        }),
        created_at=datetime(2026, 6, 26, 16, 27, tzinfo=timezone.utc),
    )
    ev = _curate_contract_event(row)
    assert ev is not None and ev.tipo == "riaperto"


def test_curate_companion_riapertura_esplicita_dedup():
    """La companion lifecycle bare della riapertura (chiuso + motivo='riapertura_esplicita', senza
    motivo_chiusura) viene scartata → niente doppione accanto alla entry ricca."""
    row = AuditLog(
        entity_type="contract", entity_id=1, action="UPDATE", trainer_id=1,
        changes=json.dumps({
            "chiuso": {"old": True, "new": False},
            "motivo": "riapertura_esplicita",
            "importo_rimborsato": None,
        }),
        created_at=datetime(2026, 6, 26, 16, 27, tzinfo=timezone.utc),
    )
    assert _curate_contract_event(row) is None


# ── Slice C (AUDIT_INTEGRITA_RESIDUI_2026-06-29 §16.3, P3): lo storico del reopen spiega la cassa preservata ──

def test_c_history_reopen_mostra_cassa_preservata_e2e(client, auth_headers, sample_client, session):
    """AC-C1 (E2E, prova producer↔consumer): dopo terminate-con-rimborso → reopen, l'evento 'Riaperto' del
    history espone la cassa preservata. Prima del fix la curation cercava `rimborso_preservato` (mai emesso)
    → riga muta pur avendo i dati nell'audit (`totale_rimborsato`)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 → rimborso pieno 300
    assert client.post(f"/api/contracts/{c['id']}/terminate",
                       json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers).status_code == 200
    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200

    riaperto = next(e for e in _history(client, auth_headers, c["id"]) if e["tipo"] == "riaperto")
    assert "rimborso €300.00 preservato" in (riaperto["dettaglio"] or ""), riaperto
    assert "wallet riassorbito" not in (riaperto["dettaglio"] or "")   # nessun wallet in questo scenario


def test_c_curate_reopen_cassa_preservata_derivata():
    """AC-C2 + AC-C3 (unit): la curation #2 deriva la cassa preservata da `totale_rimborsato.new` +
    `wallet_erogato_riassorbito` (campi già emessi dal reopen), MAI dal defunto `rimborso_preservato`."""
    def _curate(changes):
        return _curate_contract_event(AuditLog(
            entity_type="contract", entity_id=1, action="UPDATE", trainer_id=1,
            changes=json.dumps(changes),
            created_at=datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc),
        ))

    # AC-C2: wallet erogato riassorbito (D1 forma-d: acconto 800/reso 200/wallet 600/eroga 250 → reopen)
    ev = _curate({
        "motivo_chiusura": {"old": "TERMINAZIONE_RIMBORSO", "new": None},
        "chiuso": {"old": True, "new": False},
        "totale_rimborsato": {"old": 0.0, "new": 250.0},
        "wallet_erogato_riassorbito": 250.0,
        "residuo_dopo": 450.0,
    })
    assert ev.tipo == "riaperto"
    assert "rimborso €250.00 preservato" in ev.dettaglio
    assert "(di cui €250.00 da wallet riassorbito)" in ev.dettaglio
    assert "residuo €450.00" in ev.dettaglio

    # AC-C3 (no-regressione): storno-puro senza cassa (CONSUNZIONE) → niente riga 'preservato',
    # ma residuo/rate continuano a comparire (i campi già funzionanti non regrediscono)
    ev2 = _curate({
        "motivo_chiusura": {"old": "CONSUNZIONE", "new": None},
        "chiuso": {"old": True, "new": False},
        "totale_rimborsato": {"old": 0.0, "new": 0.0},
        "wallet_erogato_riassorbito": 0.0,
        "residuo_dopo": 500.0,
        "rate_riallineate": 1,
    })
    assert ev2.tipo == "riaperto"
    assert "preservato" not in (ev2.dettaglio or "")
    assert "residuo €500.00" in ev2.dettaglio
    assert "1 rate riallineate" in ev2.dettaglio
