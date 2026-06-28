"""
G7.4 — Riapertura esplicita di un contratto chiuso (inverso di terminate / auto-close).

`POST /contracts/{id}/reopen`: un solo endpoint state-driven che inverte CIÒ CHE LO STATO mostra
(rimborso, storno, rate), qualunque sia il motivo_chiusura. Path ESPLICITO (no allowlist G7.2).

Copre:
- riapertura di un auto-close COMPLETAMENTO (zero cassa) → solo chiuso=False
- riapertura di una TERMINAZIONE_RIMBORSO → refund annullato + storno + rate ripristinate (round-trip)
- riapertura di una TERMINAZIONE_SALDO_TRAINER/rinuncia (storno-only) → storno annullato, nessun rimborso
- invariante-àncora `totale_versato == Σ ENTRATA` + `totale_rimborsato == Σ USCITA RIMBORSO attivi` (→0)
- guardie: non-chiuso → 400, bouncer 404
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.trainer import Trainer
from api.models.event import Event
from api.services import contract_state as cstate
from api.services.cash_categories import (
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
    CATEGORIA_RIMBORSO_CONTRATTO,
)

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


# ── Helpers ────────────────────────────────────────────────────────

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


def _pt_event_api(client, auth_headers, client_id, contract_id, hour=9):
    """Evento PT via API (stato Programmato) → consuma un credito (auto-close se saldato+esaurito)."""
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T{hour:02d}:00:00",
        "data_fine": f"{TODAY.isoformat()}T{hour:02d}:30:00",
        "categoria": "PT", "titolo": "Seduta",
        "id_cliente": client_id, "id_contratto": contract_id,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _complete_pt(session, trainer_id, client_id, contract_id, n):
    """n sedute PT COMPLETATE via ORM (servizio reso, base del conguaglio)."""
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato="Completato", titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i), data_fine=datetime(2026, 1, 1, 10 + i),
        ))
    session.commit()


def _rate(client, auth_headers, contract_id, importo):
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _sum_movements(session, contract_id, tipo, categoria=None):
    rows = session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract_id,
            CashMovement.tipo == tipo,
            CashMovement.deleted_at == None,
        )
    ).all()
    if categoria is not None:
        rows = [m for m in rows if m.categoria == categoria]
    return round(sum(m.importo for m in rows), 2)


def _active_rate_ids(session, contract_id):
    return {
        r.id for r in session.exec(
            select(Rate).where(Rate.id_contratto == contract_id, Rate.deleted_at == None)
        ).all()
    }


def _count_active_movements(session, contract_id):
    return len(session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract_id,
            CashMovement.deleted_at == None,
        )
    ).all())


# ── Riapertura di un auto-close COMPLETAMENTO (zero cassa) ──────────

def test_reopen_completamento(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    _pt_event_api(client, auth_headers, sample_client["id"], c["id"])  # esaurisce → auto-close COMPLETAMENTO
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True and contract.motivo_chiusura == "COMPLETAMENTO"

    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert contract.motivo_chiusura is None
    assert contract.data_chiusura is None
    assert round(contract.totale_rimborsato, 2) == 0.0   # nessuna cassa da invertire
    assert round(contract.quota_stornata, 2) == 0.0


# ── Reopen NON-distruttivo: terminate RIMBORSO → reopen LASCIA la cassa, ricalcola (ADR-019) ──

def test_reopen_terminazione_rimborso_ricalcola(client, auth_headers, sample_client, session):
    """G8.1/ADR-019: reopen NON cancella più il rimborso (era 'inverso esatto'). La USCITA resta (fatto
    datato fiscalmente intoccabile), `totale_rimborsato` invariato; il residuo net-aware si ricalcola
    INCLUDENDO il rimborso che resta — il cliente ha riavuto denaro → deve di più."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200
    rata = _rate(client, auth_headers, c["id"], 300.0)             # PENDENTE → terminate la soft-elimina

    rate_pre = _active_rate_ids(session, c["id"])

    # terminate → RIMBORSO 300, quota_stornata 800 (= P − reso), rata soft-eliminata, chiuso
    rt = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert rt.status_code == 200, rt.text
    session.expire_all()
    assert session.get(Rate, rata["id"]).deleted_at is not None   # rata eliminata da terminate

    # reopen → cassa RESTA (rimborso non cancellato) + storno azzerato + rate ripristinate
    rr = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert rr.status_code == 200, rr.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert contract.motivo_chiusura is None
    assert round(contract.totale_rimborsato, 2) == 300.0          # RESTA (ADR-019: la cassa non si tocca)
    assert round(contract.quota_stornata, 2) == 0.0               # storno azzerato
    # residuo ricalcolato net-aware: P − netto = 1000 − (500 − 300) = 800 (il rimborso che resta lo alza)
    assert cstate.residuo(contract) == 800.0
    # rate ripristinate: lo stato attivo torna identico al pre-terminate
    assert _active_rate_ids(session, c["id"]) == rate_pre
    assert session.get(Rate, rata["id"]).deleted_at is None
    # àncora: Σ ENTRATA == versato (invariato); Σ USCITA RIMBORSO RESTA (non azzerata)
    assert _sum_movements(session, c["id"], "ENTRATA") == round(contract.totale_versato, 2) == 500.0
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == \
        round(contract.totale_rimborsato, 2) == 300.0


# ── Riapertura di una TERMINAZIONE_SALDO_TRAINER/rinuncia (storno-only) ─────────

def test_reopen_terminazione_saldo_trainer_storno_only(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 > versato 100 → CREDITO_TRAINER (rinuncia)
    residuo_pre = cstate.residuo(session.get(Contract, c["id"]))  # 900

    rt = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "x"}, headers=auth_headers)
    assert rt.status_code == 200, rt.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.motivo_chiusura == "TERMINAZIONE_SALDO_TRAINER"
    assert round(contract.quota_stornata, 2) == 900.0

    rr = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert rr.status_code == 200, rr.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert round(contract.quota_stornata, 2) == 0.0
    assert round(contract.totale_rimborsato, 2) == 0.0            # non c'era rimborso
    assert cstate.residuo(contract) == residuo_pre == 900.0
    assert _sum_movements(session, c["id"], "USCITA") == 0.0      # nessuna USCITA creata né da invertire


# ── Guardie ────────────────────────────────────────────────────────

def test_reopen_non_chiuso_400(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=0.0, crediti=5)
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 400
    assert "chiuso" in r.json()["detail"].lower()


def test_reopen_bouncer_404(client, auth_headers, sample_client):
    r = client.post("/api/contracts/999999/reopen", headers=auth_headers)
    assert r.status_code == 404


# ── AC-3 (G8.1): reopen dopo INCASSA_ORA — l'incasso di conguaglio RESTA, residuo ricalcolato ──

def test_reopen_dopo_incassa_ora_mantiene_entrata(client, auth_headers, sample_client, session):
    """AC-3/ADR-019: il conguaglio incassato (INCASSA_ORA) è reddito reale → reopen NON lo fa sparire.
    L'ENTRATA resta attiva, `totale_versato` invariato; diventa un pagamento sul contratto riaperto e
    il residuo net-aware lo riflette (P − netto)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 8)  # reso 800 > versato 500 → credito_trainer 300

    rt = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"azione_credito_trainer": "INCASSA_ORA", "metodo_pagamento": "CONTANTI"},
                     headers=auth_headers)
    assert rt.status_code == 200, rt.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_versato, 2) == 800.0   # 500 + 300 conguaglio
    assert _sum_movements(session, c["id"], "ENTRATA", categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO) == 300.0

    rr = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert rr.status_code == 200, rr.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    # l'ENTRATA di conguaglio RESTA attiva; versato invariato (ADR-019: cassa non toccata)
    assert _sum_movements(session, c["id"], "ENTRATA", categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO) == 300.0
    assert round(contract.totale_versato, 2) == 800.0
    assert round(contract.quota_stornata, 2) == 0.0
    # residuo ricalcolato: 1000 − netto(800) = 200 (il conguaglio incassato è un pagamento sul contratto)
    assert cstate.residuo(contract) == 200.0
    assert _sum_movements(session, c["id"], "ENTRATA") == round(contract.totale_versato, 2) == 800.0  # àncora


# ── AC-7 (G8.1): le ancore reggono — reopen non cancella NESSUN CashMovement ──

def test_reopen_non_cancella_cash_movements(client, auth_headers, sample_client, session):
    """AC-7/ADR-019 (tesi falsificabile): dopo reopen, nessun CashMovement è soft-deleted. Il conteggio
    dei movimenti attivi prima e dopo è identico; le ancore Σ ENTRATA==versato / Σ USCITA==rimborsato reggono."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=600.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 < 600 → rimborso 400
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "BONIFICO"}, headers=auth_headers)
    session.expire_all()
    movimenti_pre = _count_active_movements(session, c["id"])     # acconto ENTRATA + rimborso USCITA = 2

    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert _count_active_movements(session, c["id"]) == movimenti_pre   # NESSUN movimento cancellato
    assert _sum_movements(session, c["id"], "ENTRATA") == round(contract.totale_versato, 2)
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == \
        round(contract.totale_rimborsato, 2)


# ── AC-8 (G8.1): reopen-preview espone l'impatto pieno (dry-run, zero scritture) ──

def test_reopen_preview_dopo_rimborso(client, auth_headers, sample_client, session):
    """AC-8: reopen-preview mostra residuo_dopo (ricalcolato), il rimborso che RESTA e le rate da
    ripristinare, senza scrivere nulla. ha_rinnovo_vivo=False se non c'è un figlio aperto."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 → rimborso 300
    _rate(client, auth_headers, c["id"], 300.0)                    # PENDENTE → terminate la marca
    client.post(f"/api/contracts/{c['id']}/terminate",
                json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)

    pv = client.get(f"/api/contracts/{c['id']}/reopen-preview", headers=auth_headers)
    assert pv.status_code == 200, pv.text
    body = pv.json()
    assert body["residuo_dopo"] == 800.0          # P − netto = 1000 − (500 − 300)
    assert body["rimborso_che_resta"] == 300.0
    assert body["incasso_che_resta"] == 0.0
    assert body["rate_da_ripristinare"] == 1
    assert body["receivable_da_annullare"] == 0
    assert body["ha_rinnovo_vivo"] is False
    assert body["id_rinnovo_vivo"] is None
    assert body["messaggio"]
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True   # dry-run: nessuna scrittura


def test_reopen_preview_segnala_rinnovo_vivo(client, auth_headers, sample_client, session):
    """AC-8 (S5): se esiste un rinnovo figlio ancora aperto, reopen-preview lo segnala (ha_rinnovo_vivo
    + id) perché il FE proponga la gestione — reopen NON agisce in automatico (D-PROPONE)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=0.0, crediti=5)
    t = _trainer(session)
    figlio = Contract(trainer_id=t.id, id_cliente=sample_client["id"], rinnovo_di=c["id"],
                      chiuso=False, prezzo_totale=500.0, crediti_totali=5,
                      data_inizio=TODAY, data_scadenza=TODAY + timedelta(days=120))
    session.add(figlio)
    session.commit()
    session.refresh(figlio)
    # chiudi il parent (PARI: reso 0 == versato 0 → CONSUNZIONE)
    client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)

    pv = client.get(f"/api/contracts/{c['id']}/reopen-preview", headers=auth_headers).json()
    assert pv["ha_rinnovo_vivo"] is True
    assert pv["id_rinnovo_vivo"] == figlio.id


# ── Re-terminazione dopo riapertura (nessuno stato-zombie) ─────────

def test_reopen_then_reterminate(client, auth_headers, sample_client, session):
    """G8.1/ADR-019: dopo un reopen NON-distruttivo il primo rimborso RESTA (il netto lo sconta già).
    Ri-terminando, il conguaglio net-aware vede netto == reso → PARI: NESSUN secondo rimborso (niente
    doppio rimborso). Il vecchio modello 'funzionava' solo perché cancellava e rifaceva la cassa."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200

    client.post(f"/api/contracts/{c['id']}/terminate", json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    # seconda terminazione: netto = 500 − 300 = 200 == reso 200 → PARI (nessun rimborso, motivo CONSUNZIONE)
    rt2 = client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    assert rt2.status_code == 200, rt2.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True
    assert contract.motivo_chiusura == "CONSUNZIONE"        # PARI, non un secondo RIMBORSO
    assert round(contract.totale_rimborsato, 2) == 300.0    # il rimborso originale, NON raddoppiato
    assert cstate.residuo(contract) == 0.0
    # un solo movimento RIMBORSO attivo: il primo RESTA, la riterminazione PARI non ne crea un secondo
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == 300.0


# ── M1 (G7.7): reopen inverso ESATTO — non resuscita rate eliminate fuori dal terminate ──

def test_reopen_non_resuscita_rate_pre_eliminate(client, auth_headers, sample_client, session):
    """M1: `reopen` ripristina SOLO le rate marcate `chiusa_da_terminazione` (soft-eliminate DA terminate),
    non ogni rata con `deleted_at`. Una rata cancellata MANUALMENTE prima del terminate NON deve
    resuscitare. Prima del fix: reopen le riapriva tutte → rate-fantasma in forecast/worklist."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    # R1 PENDENTE poi cancellata MANUALMENTE (delete_rate) → deleted_at set, marker resta False
    r1 = _rate(client, auth_headers, c["id"], 300.0)
    assert client.delete(f"/api/rates/{r1['id']}", headers=auth_headers).status_code == 204
    # R2 PENDENTE viva → la eliminerà il terminate (con marker)
    r2 = _rate(client, auth_headers, c["id"], 500.0)

    # terminate (0 sedute → write-off, nessun rimborso): soft-elimina+marca R2; R1 era già fuori
    assert client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers).status_code == 200
    session.expire_all()
    assert session.get(Rate, r2["id"]).chiusa_da_terminazione is True
    assert session.get(Rate, r2["id"]).deleted_at is not None
    assert session.get(Rate, r1["id"]).chiusa_da_terminazione is False   # mai marcata (cancellata a mano)

    # reopen: ripristina SOLO R2 (marcata); R1 resta eliminata
    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200
    session.expire_all()
    assert session.get(Rate, r2["id"]).deleted_at is None               # ripristinata
    assert session.get(Rate, r2["id"]).chiusa_da_terminazione is False   # marker consumato
    assert session.get(Rate, r1["id"]).deleted_at is not None           # NON resuscitata (era manuale)


# ── L3 (G7.7-R6): auto-close COMPLETAMENTO su prenotate → reopen → preview rimborso pieno ──

def test_l3_autoclose_completamento_reopen_preview_rimborso_pieno(client, auth_headers, sample_client, session):
    """L3 (seam): un contratto auto-chiuso COMPLETAMENTO su sedute solo PRENOTATE (erogato=0), una volta
    riaperto, mostra in settlement-preview il rimborso PIENO dovuto (reso=0 → tutto il versato). Cuce
    auto-close → reopen → preview, che i test esistenti coprivano solo a pezzi."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=500.0, crediti=1)  # SALDATO
    _pt_event_api(client, auth_headers, sample_client["id"], c["id"])  # 1 Programmato → auto-close COMPLETAMENTO
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True and contract.motivo_chiusura == "COMPLETAMENTO"

    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200
    p = client.get(f"/api/contracts/{c['id']}/settlement-preview", headers=auth_headers).json()
    assert p["sedute_erogate"] == 0                  # solo prenotata, nessuna Completata
    assert p["valore_servizio_reso"] == 0.0
    assert p["esito"] == "CREDITO_CLIENTE"           # reso 0 < versato 500 → rimborso al cliente (ADR-018)
    assert round(p["importo_rimborso"], 2) == 500.0  # rimborso pieno (tutto il versato)
