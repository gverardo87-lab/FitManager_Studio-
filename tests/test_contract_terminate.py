"""
G7.3 — Endpoint terminazione anticipata + conguaglio cablato (Strada B).

Copre gli acceptance criteria del Commit A (core):
- AC-7.3-1  fonte-unica-importo (rimborso + write-off)
- AC-7.3-2  B-2-attiva: terminare un SOSPESO non lo riapre (terminate non chiama _sync)
- AC-7.3-3  invariante-àncora `totale_versato == Σ ENTRATA` + leg `totale_rimborsato == Σ USCITA RIMBORSO`
- AC-7.3-4  preview = dry-run, zero scritture
- AC-7.3-5  legacy-safe su contratto-muto (crediti_totali None) costruito via ORM
- AC-7.3-7  esclusione-burn: un RIMBORSO_CONTRATTO non gonfia _compute_variable_burn_rate
- AC-7.3-9  mappatura esito→motivo, mai COMPLETAMENTO
+ guardie: metodo_rimborso obbligatorio per il rimborso (422), bouncer 404, già-chiuso 400,
  soft-delete SOLO rate non-saldate (B-3).

La migrazione dei test PUT chiuso=True (§8) è del Commit B → non qui.
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.event import Event
from api.models.trainer import Trainer
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_RIMBORSO_CONTRATTO
from api.routers.movements import _compute_variable_burn_rate

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


# ── Helpers ────────────────────────────────────────────────────────

def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


def _contract(client, auth_headers, client_id, *, prezzo, acconto, crediti,
              inizio=None, scadenza=FUTURE):
    body = {
        "id_cliente": client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
        "prezzo_totale": prezzo, "data_inizio": (inizio or TODAY.isoformat()),
        "data_scadenza": scadenza, "acconto": acconto,
    }
    if acconto > 0:
        body["metodo_acconto"] = "CONTANTI"
    r = client.post("/api/contracts", json=body, headers=auth_headers)
    assert r.status_code == 201, r.text
    return r.json()


def _complete_pt(session, trainer_id, client_id, contract_id, n, stato="Completato"):
    """Inserisce n sedute PT via ORM nello stato dato (default Completato = servizio reso;
    'Programmato' = prenotate-non-svolte per D2)."""
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id,
            id_cliente=client_id,
            id_contratto=contract_id,
            categoria="PT",
            stato=stato,
            titolo="Seduta",
            data_inizio=datetime(2026, 1, 1, 9 + i),
            data_fine=datetime(2026, 1, 1, 10 + i),
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
    q = select(CashMovement).where(
        CashMovement.id_contratto == contract_id,
        CashMovement.tipo == tipo,
        CashMovement.deleted_at == None,
    )
    rows = session.exec(q).all()
    if categoria is not None:
        rows = [m for m in rows if m.categoria == categoria]
    return round(sum(m.importo for m in rows), 2)


# ── AC-7.3-1 + AC-7.3-9: rimborso, fonte-unica-importo, motivo ─────

def test_terminate_rimborso_fonte_unica_importo(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso = 1000*2/10 = 200

    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    # conguaglio = 200 - 500 = -300 → RIMBORSO 300; residuo_pre = 1000-500 = 500 → quota_stornata
    assert contract.chiuso is True
    assert contract.motivo_chiusura == "TERMINAZIONE_RIMBORSO"
    assert contract.data_chiusura is not None
    assert round(contract.totale_rimborsato, 2) == 300.0
    assert round(contract.quota_stornata, 2) == 500.0
    assert round(contract.totale_versato, 2) == 500.0          # LORDO immutato (Strada B)
    assert cstate.residuo(contract) == 0.0                     # storno azzera il residuo
    assert cstate.netto_incassato(contract) == 200.0           # versato − rimborsato == reso

    # AC-1: fonte-unica-importo — il CashMovement USCITA ha lo STESSO importo del delta totale_rimborsato
    refund = _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO)
    assert refund == 300.0


def test_terminate_write_off_fonte_unica(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso = 200

    r = client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    # conguaglio = 200 - 100 = +100 → SALDO_A_PERDERE (no rimborso); residuo_pre = 900 → quota_stornata
    assert contract.motivo_chiusura == "TERMINAZIONE_DECADENZA"
    assert round(contract.totale_rimborsato, 2) == 0.0
    assert round(contract.quota_stornata, 2) == 900.0          # AC-1 write-off: quota_delta == residuo_pre
    assert cstate.residuo(contract) == 0.0
    assert cstate.netto_incassato(contract) == 100.0
    assert _sum_movements(session, c["id"], "USCITA") == 0.0    # nessuna USCITA


def test_terminate_nullo_consunzione(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 5)  # reso = 500 == versato → conguaglio 0

    r = client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.motivo_chiusura == "CONSUNZIONE"           # conguaglio ~ 0 → money-neutral
    assert round(contract.totale_rimborsato, 2) == 0.0
    assert round(contract.quota_stornata, 2) == 500.0          # residuo (prezzo − versato) azzerato
    assert cstate.residuo(contract) == 0.0


def test_terminate_mai_completamento(client, auth_headers, sample_client, session):
    """AC-7.3-9: terminate non assegna MAI COMPLETAMENTO (lo riaprirebbe la reopen-allowlist G7.2)."""
    for acconto, n in [(500.0, 2), (100.0, 2), (500.0, 5)]:
        c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=acconto, crediti=10)
        t = _trainer(session)
        _complete_pt(session, t.id, sample_client["id"], c["id"], n)
        r = client.post(f"/api/contracts/{c['id']}/terminate",
                        json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
        assert r.status_code == 200, r.text
        session.expire_all()
        contract = session.get(Contract, c["id"])
        assert contract.motivo_chiusura != "COMPLETAMENTO"
        assert contract.motivo_chiusura in (
            "TERMINAZIONE_RIMBORSO", "TERMINAZIONE_DECADENZA", "CONSUNZIONE",
        )


# ── AC-7.3-2: B-2-attiva — terminare un SOSPESO NON lo riapre ──────

def test_terminate_sospeso_resta_chiuso(client, auth_headers, sample_client, session):
    """Un SOSPESO (scaduto, saldato, crediti residui) ha should_be_chiuso=False: se terminate
    chiamasse _sync_contract_chiuso si auto-riaprirebbe. Verifica che resti chiuso dopo il commit."""
    inizio = (TODAY - timedelta(days=60)).isoformat()
    scaduto = (TODAY - timedelta(days=10)).isoformat()
    c = _contract(client, auth_headers, sample_client["id"], prezzo=300.0, acconto=300.0,
                  crediti=3, inizio=inizio, scadenza=scaduto)
    # SALDATO (versato==prezzo) + 0 sedute usate + scaduto → lifecycle SOSPESO, should_be_chiuso=False
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert cstate.contract_lifecycle(contract, crediti_usati=0, today=TODAY) == cstate.Lifecycle.SOSPESO

    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True                              # NON riaperto da _sync
    assert contract.motivo_chiusura == "TERMINAZIONE_RIMBORSO"  # reso=0 → rimborso pieno
    assert round(contract.totale_rimborsato, 2) == 300.0
    assert cstate.residuo(contract) == 0.0


# ── AC-7.3-3 + B-3: riconciliazione e soft-delete selettivo ────────

def test_terminate_reconciliation_e_soft_delete_selettivo(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=200.0, crediti=10)
    t = _trainer(session)
    # rate1 SALDATA (300) + rate2 PENDENTE (500). versato sale a 500.
    r1 = _rate(client, auth_headers, c["id"], 300.0)
    client.post(f"/api/rates/{r1['id']}/pay", json={"importo": 300.0, "metodo": "CONTANTI"}, headers=auth_headers)
    r2 = _rate(client, auth_headers, c["id"], 500.0)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso=200 → conguaglio 200-500=-300 → RIMBORSO 300

    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "BONIFICO"}, headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, c["id"])
    # AC-3 àncora LORDO: Σ ENTRATA (mastro reale) == totale_versato; nessuna ENTRATA distrutta
    assert _sum_movements(session, c["id"], "ENTRATA") == round(contract.totale_versato, 2) == 500.0
    # AC-3 leg rimborso: Σ USCITA RIMBORSO == totale_rimborsato
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == \
        round(contract.totale_rimborsato, 2) == 300.0

    # B-3: rate2 (PENDENTE) soft-deleted; rate1 (SALDATA) + il suo CashMovement ENTRATA SOPRAVVIVONO
    rate1 = session.get(Rate, r1["id"])
    rate2 = session.get(Rate, r2["id"])
    assert rate1.deleted_at is None
    assert rate2.deleted_at is not None
    rate1_entrate = session.exec(
        select(CashMovement).where(
            CashMovement.id_rata == r1["id"],
            CashMovement.tipo == "ENTRATA",
            CashMovement.deleted_at == None,
        )
    ).all()
    assert len(rate1_entrate) == 1  # il pagamento della rata SALDATA non è stato distrutto


# ── AC-7.3-4: preview = dry-run, zero scritture ────────────────────

def test_settlement_preview_no_writes(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)

    movimenti_prima = len(session.exec(select(CashMovement)).all())

    r = client.get(f"/api/contracts/{c['id']}/settlement-preview", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["esito"] == "RIMBORSO"
    assert body["motivo_chiusura"] == "TERMINAZIONE_RIMBORSO"
    assert round(body["importo_rimborso"], 2) == 300.0
    assert body["metodo_rimborso_richiesto"] is True
    assert "verifica" in body["messaggio"].lower()            # framing di proposta (§0/§4)

    # Nessuna scrittura: stato contratto invariato + nessun nuovo movimento
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert round(contract.quota_stornata, 2) == 0.0
    assert round(contract.totale_rimborsato, 2) == 0.0
    assert len(session.exec(select(CashMovement)).all()) == movimenti_prima


# ── AC-7.3-5: legacy-safe su contratto-muto (ORM, non ContractCreate) ──

def test_terminate_legacy_muto_crediti_none(client, auth_headers, sample_client, session):
    """Contratto-muto legacy: crediti_totali=None, prezzo presente, versato parziale, scadenza futura.
    Costruito via ORM perché ContractCreate rifiuterebbe la forma muta. terminate deve reggere senza
    crash né violazione d'invariante (crediti None → 'tutto reso' nel modulo settlement)."""
    t = _trainer(session)
    muto = Contract(
        trainer_id=t.id,
        id_cliente=sample_client["id"],
        tipo_pacchetto="Legacy",
        crediti_totali=None,                # senza monte-sedute
        prezzo_totale=300.0,
        totale_versato=100.0,
        acconto=0.0,
        stato_pagamento="PARZIALE",
        data_inizio=None,
        data_scadenza=TODAY + timedelta(days=200),
        chiuso=False,
    )
    session.add(muto)
    session.commit()
    session.refresh(muto)

    r = client.post(f"/api/contracts/{muto.id}/terminate", json={}, headers=auth_headers)
    assert r.status_code == 200, r.text

    session.expire_all()
    contract = session.get(Contract, muto.id)
    # crediti None → valore_reso = prezzo intero (300); conguaglio = 300-100 = +200 → SALDO_A_PERDERE
    assert contract.chiuso is True
    assert contract.motivo_chiusura == "TERMINAZIONE_DECADENZA"
    assert round(contract.quota_stornata, 2) == 200.0          # residuo (300-100) azzerato
    assert cstate.residuo(contract) == 0.0
    assert round(contract.totale_versato, 2) == 100.0          # invariante: lordo immutato


# ── AC-7.3-7: esclusione-burn — il rimborso non gonfia il burn ─────

def test_terminate_burn_esclude_rimborso(client, auth_headers, sample_client, session):
    """Un RIMBORSO_CONTRATTO (USCITA) NON deve entrare nel burn variabile (gonfierebbe costo_operativo
    → falso CRITICO sulla protezione cassa). Baseline 300 nel mese scorso → burn = 100 sia con sia
    senza rimborso; il rimborso (300, stesso mese) è escluso."""
    t = _trainer(session)
    # mese precedente (dentro la finestra _prev_months di 3 mesi chiusi)
    first_of_this = date(TODAY.year, TODAY.month, 1)
    last_month = first_of_this - timedelta(days=1)
    mese_scorso = date(last_month.year, last_month.month, 15)

    # baseline: una USCITA variabile (categoria None → null-safe) di 300 nel mese scorso
    session.add(CashMovement(
        trainer_id=t.id, data_effettiva=mese_scorso, tipo="USCITA",
        categoria=None, importo=300.0, id_spesa_ricorrente=None,
    ))
    session.commit()
    baseline = _compute_variable_burn_rate(session, t, TODAY)
    assert baseline == round(300.0 / 3, 2)                     # 100.0

    # terminate con rimborso datato nel mese scorso → USCITA RIMBORSO_CONTRATTO 300 nello stesso mese
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # reso 200 → rimborso 300
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "BONIFICO", "data_chiusura": mese_scorso.isoformat()},
                    headers=auth_headers)
    assert r.status_code == 200, r.text
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == 300.0

    # il burn resta 100 (il rimborso è escluso); senza esclusione sarebbe (300+300)/3 = 200
    session.expire_all()
    assert _compute_variable_burn_rate(session, t, TODAY) == baseline == 100.0


# ── Guardie: metodo obbligatorio, bouncer, già-chiuso ──────────────

def test_terminate_rimborso_richiede_metodo(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # esito RIMBORSO
    r = client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    assert r.status_code == 422, r.text
    # nessuna scrittura: l'atomicità ha tenuto
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False
    assert round(contract.quota_stornata, 2) == 0.0


def test_terminate_bouncer_404(client, auth_headers, sample_client):
    r = client.post("/api/contracts/999999/terminate", json={}, headers=auth_headers)
    assert r.status_code == 404


def test_terminate_gia_chiuso_400(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)
    r1 = client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    assert r1.status_code == 200, r1.text
    # seconda terminazione sullo stesso contratto → 400
    r2 = client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers)
    assert r2.status_code == 400
    # anche la preview su un chiuso → 400
    r3 = client.get(f"/api/contracts/{c['id']}/settlement-preview", headers=auth_headers)
    assert r3.status_code == 400


# ── D4 (G7.5c): data_chiusura non nel futuro ───────────────────────

def test_terminate_data_chiusura_futura_422(client, auth_headers, sample_client, session):
    """D4: una `data_chiusura` futura → 422 (un rimborso è denaro uscito ora/passato, mai impegno
    futuro). Atomicità: nessuna scrittura. Controprova: data odierna → 200."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=100.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)  # write-off, niente metodo richiesto

    futura = (TODAY + timedelta(days=10)).isoformat()
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"data_chiusura": futura}, headers=auth_headers)
    assert r.status_code == 422, r.text
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is False  # boundary respinge → nessuna scrittura

    # controprova: data odierna accettata
    r2 = client.post(f"/api/contracts/{c['id']}/terminate",
                     json={"data_chiusura": TODAY.isoformat()}, headers=auth_headers)
    assert r2.status_code == 200, r2.text


# ── D2 (G7.5c): la preview espone sedute_prenotate (SOLO display, non nel conguaglio) ──

def test_settlement_preview_sedute_prenotate(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)                      # 2 erogate (Completato)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 3, stato="Programmato")  # 3 prenotate

    p = client.get(f"/api/contracts/{c['id']}/settlement-preview", headers=auth_headers).json()
    assert p["sedute_erogate"] == 2
    assert p["sedute_prenotate"] == 3
    # prova che le prenotate NON entrano nel conguaglio: reso = 1000 * 2/10 = 200 (solo le erogate)
    assert p["valore_servizio_reso"] == 200.0

    # contratto senza PT Programmati → sedute_prenotate == 0 (l'avviso FE non si mostra)
    c2 = _contract(client, auth_headers, sample_client["id"], prezzo=500.0, acconto=0.0, crediti=5)
    _complete_pt(session, t.id, sample_client["id"], c2["id"], 1)  # solo erogata
    p2 = client.get(f"/api/contracts/{c2['id']}/settlement-preview", headers=auth_headers).json()
    assert p2["sedute_prenotate"] == 0


# ── H1 (G7.7-R1): unpay su contratto terminato (E2E) → 409, tetto preservato, reopen riabilita ──

def test_unpay_dopo_terminate_rifiutato_409(client, auth_headers, sample_client, session):
    """H1 (ADR-016/ADR-017) — E2E con terminate REALE. Dopo una terminazione con RIMBORSO, una rata
    SALDATA superstite NON è revocabile (409). È il test che avrebbe colto il money-bug: senza guard,
    `unpay` decrementerebbe `totale_versato` sotto `totale_rimborsato`, il clamp di netto_incassato()
    maschererebbe l'over-rimborso (ΣRIMBORSO > ΣENTRATA). Verifica anche il path canonico: reopen → la
    revoca torna possibile (riallineamento atomico). Sentinella del tetto totale_rimborsato ≤ totale_versato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    t = _trainer(session)
    # 2 rate SALDATE da 500 → versato 1000; 2 sedute → reso 200 → conguaglio -800 → RIMBORSO 800 (quota 0)
    r1 = _rate(client, auth_headers, c["id"], 500.0)
    client.post(f"/api/rates/{r1['id']}/pay", json={"importo": 500.0, "metodo": "CONTANTI"}, headers=auth_headers)
    r2 = _rate(client, auth_headers, c["id"], 500.0)
    client.post(f"/api/rates/{r2['id']}/pay", json={"importo": 500.0, "metodo": "CONTANTI"}, headers=auth_headers)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)

    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == 800.0
    assert round(contract.totale_versato, 2) == 1000.0

    # le 2 rate SALDATE sopravvivono al terminate (B-3) → unpay di una è rifiutato (409, riapri prima)
    unpay = client.post(f"/api/rates/{r1['id']}/unpay", headers=auth_headers)
    assert unpay.status_code == 409, unpay.text

    # tetto preservato: nessun decremento, totale_rimborsato ≤ totale_versato; rata intatta
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_versato, 2) == 1000.0
    assert contract.totale_rimborsato <= contract.totale_versato
    assert session.get(Rate, r1["id"]).stato == "SALDATA"

    # path canonico: reopen annulla rimborso+storno → la revoca torna possibile
    reopen = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert reopen.status_code == 200, reopen.text
    unpay2 = client.post(f"/api/rates/{r1['id']}/unpay", headers=auth_headers)
    assert unpay2.status_code == 200, unpay2.text


# ── M2 (G7.7-R2): rate di un contratto terminato non si modificano (guard chiuso) ──

def test_m2_update_rate_su_terminato_400(client, auth_headers, sample_client, session):
    """M2: una rata SALDATA superstite di un contratto terminato NON si modifica (guard `chiuso` in
    update_rate, allineato a create_rate) → 400. Senza, alzando importo_previsto tornerebbe PARZIALE
    (residuo-fantasma a livello rata). Dopo reopen la modifica torna possibile (guard chiuso-specifico)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    t = _trainer(session)
    r1 = _rate(client, auth_headers, c["id"], 500.0)
    client.post(f"/api/rates/{r1['id']}/pay", json={"importo": 500.0, "metodo": "CONTANTI"}, headers=auth_headers)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 5)  # reso 500 == versato → NULLO, nessun rimborso

    assert client.post(f"/api/contracts/{c['id']}/terminate", json={}, headers=auth_headers).status_code == 200
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is True
    assert round(contract.quota_stornata, 2) == 500.0   # residuo (prezzo−versato) stornato

    # modifica della SALDATA superstite → 400 (contratto chiuso); rata invariata
    r = client.put(f"/api/rates/{r1['id']}", json={"importo_previsto": 600.0}, headers=auth_headers)
    assert r.status_code == 400, r.text
    session.expire_all()
    assert session.get(Rate, r1["id"]).stato == "SALDATA"

    # controprova: dopo reopen (contratto aperto) la modifica è di nuovo permessa
    assert client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers).status_code == 200
    assert client.put(f"/api/rates/{r1['id']}", json={"importo_previsto": 600.0},
                      headers=auth_headers).status_code == 200


# ── L3 (G7.7-R6): le prenotate non riducono il rimborso sul path COMMITTATO (non solo preview) ──

def test_l3_terminate_prenotate_non_riducono_rimborso_write(client, auth_headers, sample_client, session):
    """L3: la forfeiture delle prenotate vale sul POST /terminate committato, non solo nel GET preview.
    2 Completato + 3 Programmato → rimborso su 2 (reso 200), USCITA RIMBORSO su 2 — le 3 prenotate non
    spostano né il campo `totale_rimborsato` né il movimento scritto."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _complete_pt(session, t.id, sample_client["id"], c["id"], 2)                       # 2 erogate → reso 200
    _complete_pt(session, t.id, sample_client["id"], c["id"], 3, stato="Programmato")  # 3 prenotate

    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    # conguaglio = 200 − 500 = −300 → rimborso 300 (le 3 Programmato NON contano nel reso)
    assert round(contract.totale_rimborsato, 2) == 300.0
    assert _sum_movements(session, c["id"], "USCITA", categoria=CATEGORIA_RIMBORSO_CONTRATTO) == 300.0
