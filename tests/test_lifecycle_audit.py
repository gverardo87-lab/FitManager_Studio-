"""
Prereq P2 — audit della transizione `chiuso` del contratto.

Oggi `pay_rate`/`unpay_rate` (auto-close/reopen) e `agenda._sync_contract_chiuso` accendono o
spengono `chiuso` senza loggarlo: l'evento più importante da tracciare legalmente (terminazione, G7)
non può ereditare un audit bucato. Il nuovo helper `log_contract_lifecycle_transition` lo registra,
idempotente (no-op se `chiuso` non cambia).
"""

import json
from datetime import date, timedelta

from sqlmodel import select

from api.models.audit_log import AuditLog
from api.models.contract import Contract

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti):
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


def _pt_event(client, auth_headers, client_id, contract_id, hour=9):
    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T{hour:02d}:00:00",
        "data_fine": f"{TODAY.isoformat()}T{hour:02d}:30:00",
        "categoria": "PT",
        "titolo": "Seduta",
        "id_cliente": client_id,
        "id_contratto": contract_id,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _rate(client, auth_headers, contract_id, importo):
    r = client.post("/api/rates", json={
        "id_contratto": contract_id,
        "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
        "importo_previsto": importo,
    }, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _chiuso_transitions(session, contract_id):
    """Ritorna i changes (dict) delle audit entry sul contratto che toccano `chiuso`."""
    session.expire_all()
    rows = session.exec(
        select(AuditLog).where(
            AuditLog.entity_type == "contract",
            AuditLog.entity_id == contract_id,
        )
    ).all()
    out = []
    for r in rows:
        if r.changes:
            ch = json.loads(r.changes)
            if "chiuso" in ch:
                out.append(ch)
    return out


# ── pay_rate → auto-close (completamento) ──────────────────────────

def test_pay_autoclose_logs_transition(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])  # consuma l'unico credito
    rate = _rate(client, auth_headers, c["id"], 100.0)

    # prima del pagamento: nessuna transizione chiuso loggata
    assert _chiuso_transitions(session, c["id"]) == []

    r = client.post(f"/api/rates/{rate['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    trans = _chiuso_transitions(session, c["id"])
    assert len(trans) == 1
    assert trans[0]["chiuso"] == {"old": False, "new": True}
    assert trans[0]["motivo"] == "completamento"


# ── unpay_rate → auto-reopen (riapertura_pagamento) ────────────────

def test_unpay_autoreopen_logs_transition(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    _pt_event(client, auth_headers, sample_client["id"], c["id"])
    rate = _rate(client, auth_headers, c["id"], 100.0)
    client.post(f"/api/rates/{rate['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)

    r = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)
    assert r.status_code == 200, r.text

    trans = _chiuso_transitions(session, c["id"])
    # 2 transizioni: chiusura (pay) + riapertura (unpay)
    assert trans[-1]["chiuso"] == {"old": True, "new": False}
    assert trans[-1]["motivo"] == "riapertura_pagamento"


# ── agenda: evento chiude / cancella riapre ────────────────────────

def test_event_autoclose_and_reopen_log_transition(client, auth_headers, sample_client, session):
    # SALDATO dall'inizio (acconto==prezzo), 1 credito → l'evento finale chiude
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    assert _chiuso_transitions(session, c["id"]) == []  # alla creazione non si chiude (crediti non usati)

    ev = _pt_event(client, auth_headers, sample_client["id"], c["id"])
    trans = _chiuso_transitions(session, c["id"])
    assert len(trans) == 1
    assert trans[0]["chiuso"] == {"old": False, "new": True}
    assert trans[0]["motivo"] == "completamento"

    d = client.delete(f"/api/events/{ev['id']}", headers=auth_headers)
    assert d.status_code in (200, 204), d.text
    trans = _chiuso_transitions(session, c["id"])
    assert trans[-1]["chiuso"] == {"old": True, "new": False}
    assert trans[-1]["motivo"] == "riapertura_crediti"


# ── idempotenza: nessun audit chiuso se lo stato non cambia ────────

def test_no_transition_when_chiuso_unchanged(client, auth_headers, sample_contract_with_plan, session):
    # paga una rata SENZA esaurire i crediti (contratto resta aperto) → zero transizioni chiuso
    rate = sample_contract_with_plan["rates"][0]
    cid = sample_contract_with_plan["contract"]["id"]
    r = client.post(f"/api/rates/{rate['id']}/pay", json={"importo": rate["importo_previsto"], "metodo": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert _chiuso_transitions(session, cid) == []


# ── [G7.2 — FIXED] reopen-allowlist su ENTRAMBI i rami di auto-riapertura ──────────────────────
# Prima (bug latente bridge §1/§6): qualsiasi chiusura con crediti_usati < crediti_totali veniva
# riaperta da una mutazione d'agenda (`_sync_contract_chiuso`, credit-driven) o da una revoca-pagamento
# (`unpay_rate`, payment-driven) → latente sulle chiusure manuali (motivo=NULL), bomba per G7.3 (ogni
# terminazione riaperta → zombie chiuso=False ∧ quota_stornata>0). Fix: allowlist POSITIVA su entrambi
# i rami — riapri SOLO se motivo_chiusura==COMPLETAMENTO. Il NULL è il contro-esempio che una denylist
# (motivo∈TERMINAZIONE_*) mancherebbe. Delta modello: FDM §9.5.6, IMPL_PLAN §4.7.
# Verifica call-site (G7.2): COMPLETAMENTO scritto da pay_rate inline + ramo chiusura _sync; riapertura
# in DUE rami distinti (_sync credit-driven + unpay_rate payment-driven) → allowlist su entrambi.
# NB orologio: il conteggio crediti di _sync NON ha filtro data → niente flakiness di mezzanotte su
# questo meccanismo (a differenza dei test workspace 22-23/06); date comunque ancorate a TODAY.


def test_manual_close_not_reopened_by_agenda_edit(client, auth_headers, sample_client, session):
    """Ramo NULL: chiusura manuale (motivo=NULL, nessuno storno) → l'edit-agenda NON la riapre.
    Ex xfail-strict (bug latente bridge §1/§6, dal 21/06) → ora presidio permanente (G7.2)."""
    # SOSPESO-like: crediti non esauriti (1/3) + residuo>0 (non saldato → no auto-close)
    c = _contract(client, auth_headers, sample_client["id"], prezzo=300.0, acconto=100.0, crediti=3)
    ev = _pt_event(client, auth_headers, sample_client["id"], c["id"])  # 1/3 crediti usati

    # chiusura DELIBERATA con motivo NULL, costruita via ORM. Post-G7.3 il canale PUT chiuso è ritirato
    # (§8) e `terminate` scrive SEMPRE un motivo → lo stato chiuso=True ∧ motivo=NULL non è più
    # producibile via API. Ma resta come LEGACY (contratti chiusi pre-G7, ereditati a motivo=NULL) e il
    # ramo NULL della reopen-allowlist DEVE continuare a proteggerlo: lo si fabbrica a mano (come i
    # forward-guard :200/:224) così il presidio resta verde E VIVO, non verde-e-morto.
    contract = session.get(Contract, c["id"])
    contract.chiuso = True
    contract.motivo_chiusura = None
    session.add(contract)
    session.commit()

    # mutazione d'agenda su un evento del contratto → _sync_contract_chiuso
    client.delete(f"/api/events/{ev['id']}", headers=auth_headers)

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True  # la chiusura deliberata (NULL) NON viene riaperta (allowlist)


def test_completamento_si_riapre_ancora(client, auth_headers, sample_client, session):
    """AC-7.2-3 — ramo POSITIVO: un contratto auto-chiuso da completamento (saldato + crediti esauriti,
    motivo=COMPLETAMENTO) torna riaperto quando l'edit-agenda libera un credito. Guardiano contro la
    guardia troppo stretta (un `if False` passerebbe il caso NULL ma romperebbe il completamento)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)  # SALDATO
    ev = _pt_event(client, auth_headers, sample_client["id"], c["id"])  # esaurisce → auto-close (COMPLETAMENTO)
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True and contract.motivo_chiusura == "COMPLETAMENTO"

    client.delete(f"/api/events/{ev['id']}", headers=auth_headers)  # libera il credito → _sync riapre
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False                  # riaperto (legittimo)
    assert contract.motivo_chiusura is None          # AC-7.2-5: clear-on-reopen (opzione a)


def test_terminazione_non_si_riapre_da_agenda(client, auth_headers, sample_client, session):
    """AC-7.2-4 — forward-guard G7.3 (ramo credit-driven): chiusura con motivo TERMINAZIONE_RIMBORSO
    + quota_stornata>0 (scritti a mano, l'endpoint terminate è G7.3) → l'edit-agenda NON la riapre.
    Lo stato-zombie chiuso=False ∧ quota_stornata>0 non si formerà quando G7.3 arriverà."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=300.0, acconto=100.0, crediti=3)
    ev = _pt_event(client, auth_headers, sample_client["id"], c["id"])  # 1/3 crediti
    # simula la terminazione (G7.3 non esiste ancora): chiusura + motivo + storno via ORM
    contract = session.get(Contract, c["id"])
    contract.chiuso = True
    contract.motivo_chiusura = "TERMINAZIONE_RIMBORSO"
    contract.quota_stornata = 200.0
    session.add(contract)
    session.commit()

    client.delete(f"/api/events/{ev['id']}", headers=auth_headers)  # edit-agenda → _sync_contract_chiuso

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True                              # NON riaperto (allowlist)
    assert contract.motivo_chiusura == "TERMINAZIONE_RIMBORSO"  # invariato
    assert contract.quota_stornata == 200.0                    # no zombie chiuso=False ∧ quota>0


def test_terminazione_non_si_riapre_da_unpay(client, auth_headers, sample_client, session):
    """AC-7.2-4 (gemello sul 2° ramo, payment-driven): una terminazione con una rata SALDATA che
    sopravvive (G7.3 soft-elimina solo le NON-saldate) → la revoca di quella rata NON riapre il
    contratto (allowlist anche in unpay_rate). Presidia che ENTRAMBI i rami siano coperti."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=3)
    rate = _rate(client, auth_headers, c["id"], 100.0)
    client.post(f"/api/rates/{rate['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"}, headers=auth_headers)
    # simula terminazione (G7.3 non esiste): chiusura + motivo + storno via ORM
    contract = session.get(Contract, c["id"])
    contract.chiuso = True
    contract.motivo_chiusura = "TERMINAZIONE_DECADENZA"
    contract.quota_stornata = 50.0
    session.add(contract)
    session.commit()

    ur = client.post(f"/api/rates/{rate['id']}/unpay", headers=auth_headers)  # revoca → ramo reopen di unpay_rate
    assert ur.status_code == 200, ur.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True                              # NON riaperto da unpay (allowlist)
    assert contract.motivo_chiusura == "TERMINAZIONE_DECADENZA"  # invariato
