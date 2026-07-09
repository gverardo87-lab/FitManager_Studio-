"""
G7.8 / ADR-017 — Il rinvio libera il credito (T1).

`Rinviato` non occupa il credito: occupazione-credito = Programmato + Completato. Nessun euro cambia
(asse denaro invariante per costruzione — `compute_settlement` non legge mai `!= Cancellato`). Copre gli
acceptance criteria di SPEC_RINVIO_LIBERA_CREDITO §8:
- AC-2  conteggio: crediti_residui == N − Completate − Programmate (Rinviato escluso) su tutte le viste
- AC-3  D-AUTO-CLOSE: saldato all-rinviate resta aperto, su ENTRAMBI i rami (pay_rate + agenda _sync)
- AC-4  D-GUARD: dopo aver rinviato, si può riprenotare (no 400 "Crediti esauriti")
- AC-5  overlap (§3-bis): una rinviata libera lo slot orario (no 409 sulla doppia prenotazione)
- AC-1  oracolo settlement: il conguaglio resta invariante con rinviate presenti
"""

from datetime import date, datetime, timedelta

from sqlmodel import select

from api.models.contract import Contract
from api.models.event import Event
from api.models.trainer import Trainer

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()


def _trainer(session) -> Trainer:
    return session.exec(select(Trainer)).first()


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


def _events(session, trainer_id, client_id, contract_id, n, stato, hour0=8):
    """Inserisce n eventi PT via ORM nello stato dato (orari distinti per evitare collisioni)."""
    for i in range(n):
        session.add(Event(
            trainer_id=trainer_id, id_cliente=client_id, id_contratto=contract_id,
            categoria="PT", stato=stato, titolo="Seduta",
            data_inizio=datetime(2026, 1, 1 + (hour0 + i) // 24, (hour0 + i) % 24),
            data_fine=datetime(2026, 1, 1 + (hour0 + i + 1) // 24, (hour0 + i + 1) % 24),
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


# ── AC-2: il conteggio esclude Rinviato (dettaglio + lista contratti + lista clienti) ──

def test_ac2_dettaglio_contratto_esclude_rinviato(client, auth_headers, sample_client, session):
    """N=10, 2 Completate + 3 Programmate + 4 Rinviate → usati 5, residui 5. Le rinviate restano
    visibili (sedute_rinviate) ma NON occupano il credito."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    t = _trainer(session)
    _events(session, t.id, sample_client["id"], c["id"], 2, "Completato", hour0=8)
    _events(session, t.id, sample_client["id"], c["id"], 3, "Programmato", hour0=11)
    _events(session, t.id, sample_client["id"], c["id"], 4, "Rinviato", hour0=15)

    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["sedute_completate"] == 2
    assert d["sedute_programmate"] == 3
    assert d["sedute_rinviate"] == 4          # display: ancora visibili
    assert d["crediti_usati"] == 5            # 2 + 3 (Rinviato escluso)
    assert d["crediti_residui"] == 5          # 10 − 5 (le 4 rinviate sono tornate spendibili)


def test_ac2_lista_contratti_esclude_rinviato(client, auth_headers, sample_client, session):
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    t = _trainer(session)
    _events(session, t.id, sample_client["id"], c["id"], 2, "Completato", hour0=8)
    _events(session, t.id, sample_client["id"], c["id"], 4, "Rinviato", hour0=12)

    row = next(x for x in client.get("/api/contracts", headers=auth_headers).json()["items"]
               if x["id"] == c["id"])
    assert row["crediti_usati"] == 2          # solo le Completate (Rinviato escluso)


def test_ac2_lista_clienti_esclude_rinviato(client, auth_headers, sample_client, session):
    """Sito della segnalazione di Chiara: crediti_residui del cliente esclude le rinviate."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    t = _trainer(session)
    _events(session, t.id, sample_client["id"], c["id"], 2, "Completato", hour0=8)
    _events(session, t.id, sample_client["id"], c["id"], 4, "Rinviato", hour0=12)

    row = next(x for x in client.get("/api/clients", headers=auth_headers).json()["items"]
               if x["id"] == sample_client["id"])
    assert row["crediti_residui"] == 8        # 10 − 2 (le 4 rinviate tornano al pool)


def test_g971bis_orfana_non_decrementa_crediti_cliente(client, auth_headers, sample_client, session):
    """G9.7.1-bis: la seduta ORFANA (id_contratto=NULL) NON consuma crediti acquistati.

    Regressione della trappola vista LIVE 2026-07-09: 2 orfane su cliente con 2 crediti da
    contratto CHIUSO → dropdown «(0 crediti)» → hard-block «Crediti esauriti» → cliente
    intrappolato. Il B4 promette «non scala crediti»: il numero client-level deve dire il vero
    (interprete allineato a `crediti_usati` contract-level, che le orfane non toccano)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=2)
    t = _trainer(session)
    # 2 orfane in stati di occupazione (Programmato + Completato) + 1 agganciata
    _events(session, t.id, sample_client["id"], None, 1, "Programmato", hour0=8)
    _events(session, t.id, sample_client["id"], None, 1, "Completato", hour0=9)
    _events(session, t.id, sample_client["id"], c["id"], 1, "Programmato", hour0=10)

    row = next(x for x in client.get("/api/clients", headers=auth_headers).json()["items"]
               if x["id"] == sample_client["id"])
    assert row["crediti_residui"] == 1        # 2 − 1 agganciata; le 2 orfane NON contano

    # L'interprete contract-level resta invariato: solo l'agganciata occupa
    d = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert d["crediti_usati"] == 1


# ── AC-3: D-AUTO-CLOSE su ENTRAMBI i rami (pay_rate + agenda _sync) ──

def test_ac3_autoclose_pay_rate_non_chiude_su_rinviate(client, auth_headers, sample_client, session):
    """Ramo payment-driven (rates.py): saldare un contratto le cui sedute sono tutte RINVIATE NON
    deve auto-chiuderlo (crediti_residui > 0). È il sito che la spec v1 aveva mancato."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    t = _trainer(session)
    _events(session, t.id, sample_client["id"], c["id"], 1, "Rinviato", hour0=9)
    rate = _rate(client, auth_headers, c["id"], 100.0)

    r = client.post(f"/api/rates/{rate['id']}/pay", json={"importo": 100.0, "metodo": "CONTANTI"},
                    headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False           # la rinviata non esaurisce il credito → resta aperto


def test_ac3_autoclose_agenda_sync_riapre_su_rinvio(client, auth_headers, sample_client, session):
    """Ramo credit-driven (agenda._sync): un saldato auto-chiuso da una prenotazione che esaurisce il
    monte-sedute si RIAPRE quando quella seduta viene rinviata (il rinvio restituisce il credito)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)
    ev = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T09:00:00", "data_fine": f"{TODAY.isoformat()}T10:00:00",
        "categoria": "PT", "titolo": "Seduta", "id_cliente": sample_client["id"], "id_contratto": c["id"],
    }, headers=auth_headers).json()
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True   # 1/1 occupato (Programmato) → auto-close

    r = client.put(f"/api/events/{ev['id']}", json={"stato": "Rinviato"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is False  # rinviata → credito liberato → riaperto


def test_ac3_autoclose_agenda_sync_non_chiude_su_rinvio(client, auth_headers, sample_client, session):
    """Ramo credit-driven (_sync), caso 'arriva e non chiude': un saldato con scadenza futura le cui
    sedute vengono portate a Rinviato NON deve auto-chiudersi (crediti liberati). Isola la transizione
    'pieno-di-rinviate → resta aperto' sul ramo edit-evento, che il test di riapertura non copre."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=100.0, crediti=1)  # SALDATO
    ev = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T09:00:00", "data_fine": f"{TODAY.isoformat()}T10:00:00",
        "categoria": "PT", "titolo": "Seduta", "id_cliente": sample_client["id"], "id_contratto": c["id"],
    }, headers=auth_headers).json()
    session.expire_all()
    assert session.get(Contract, c["id"]).chiuso is True   # 1/1 Programmato → auto-close (baseline)

    # NON passare da delete (che è il path di riapertura già testato): rinviare in-place
    r = client.put(f"/api/events/{ev['id']}", json={"stato": "Rinviato"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    contract = session.get(Contract, c["id"])
    assert contract.chiuso is False              # rinviata → 0/1 occupato → non più chiuso
    assert contract.motivo_chiusura is None      # clear-on-reopen (AC-7.2-5)


# ── AC-4: D-GUARD — dopo il rinvio si può riprenotare ──

def test_ac4_guard_riprenotabile_dopo_rinvio(client, auth_headers, sample_client, session):
    """Una seduta rinviata libera lo slot-credito: il credit guard di create_event NON deve bloccare
    una nuova prenotazione (no 400 'Crediti esauriti')."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=100.0, acconto=0.0, crediti=1)
    t = _trainer(session)
    _events(session, t.id, sample_client["id"], c["id"], 1, "Rinviato", hour0=9)

    r = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T15:00:00", "data_fine": f"{TODAY.isoformat()}T16:00:00",
        "categoria": "PT", "titolo": "Riprenotata", "id_cliente": sample_client["id"], "id_contratto": c["id"],
    }, headers=auth_headers)
    assert r.status_code == 201, r.text       # prima del fix: 400 (la rinviata occupava l'unico credito)


# ── AC-5: overlap (§3-bis) — la rinviata libera lo slot orario ──

def test_ac5_overlap_rinviato_libera_slot(client, auth_headers, sample_client, session):
    """Una seduta Rinviato non blocca più la doppia prenotazione sullo stesso orario (D-GUARD)."""
    slot = {"data_inizio": f"{TODAY.isoformat()}T11:00:00", "data_fine": f"{TODAY.isoformat()}T12:00:00"}
    a = client.post("/api/events", json={
        **slot, "categoria": "PT", "titolo": "A", "id_cliente": sample_client["id"],
    }, headers=auth_headers).json()
    # stesso slot mentre A è Programmato → overlap 409
    dup = client.post("/api/events", json={
        **slot, "categoria": "PT", "titolo": "B", "id_cliente": sample_client["id"],
    }, headers=auth_headers)
    assert dup.status_code == 409, dup.text

    # rinvio A → lo slot si libera
    client.put(f"/api/events/{a['id']}", json={"stato": "Rinviato"}, headers=auth_headers)
    ok = client.post("/api/events", json={
        **slot, "categoria": "PT", "titolo": "B", "id_cliente": sample_client["id"],
    }, headers=auth_headers)
    assert ok.status_code == 201, ok.text     # niente 409: la rinviata non occupa lo slot


# ── AC-1: oracolo settlement — il conguaglio è invariante con rinviate presenti ──

def test_ac1_settlement_invariante_con_rinviate(client, auth_headers, sample_client, session):
    """Le rinviate NON entrano nel conguaglio: reso = solo Completate (asse EROGATO, ADR-016 intatto)."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=500.0, crediti=10)
    t = _trainer(session)
    _events(session, t.id, sample_client["id"], c["id"], 2, "Completato", hour0=8)
    _events(session, t.id, sample_client["id"], c["id"], 4, "Rinviato", hour0=12)

    p = client.get(f"/api/contracts/{c['id']}/settlement-preview", headers=auth_headers).json()
    assert p["sedute_erogate"] == 2
    assert p["valore_servizio_reso"] == 200.0   # 1000 * 2/10, le rinviate non spostano l'importo
    assert round(p["importo_rimborso"], 2) == 300.0  # conguaglio 200 − 500 = −300


# ── Decisione #2 (G7.8/ADR-017): una seduta GIÀ SVOLTA non si rinvia (guard 422 in update_event) ──

def test_completato_non_si_rinvia_422(client, auth_headers, sample_client, session):
    """Decisione di dominio: Completato→Rinviato libererebbe credito E valore (unica transizione
    money-moving di G7.8) → bloccata a monte con 422. Le altre uscite da Completato (Programmato per
    riprogrammare, Cancellato per non-avvenuta) restano permesse — correzioni legittime di un 'done'
    errato, dove il valore DEVE seguire la realtà."""
    c = _contract(client, auth_headers, sample_client["id"], prezzo=1000.0, acconto=0.0, crediti=10)
    ev = client.post("/api/events", json={
        "data_inizio": f"{TODAY.isoformat()}T09:00:00", "data_fine": f"{TODAY.isoformat()}T10:00:00",
        "categoria": "PT", "titolo": "Svolta", "id_cliente": sample_client["id"], "id_contratto": c["id"],
    }, headers=auth_headers).json()
    client.put(f"/api/events/{ev['id']}", json={"stato": "Completato"}, headers=auth_headers)

    # Completato → Rinviato: rifiutato 422 (a monte, nessuna scrittura)
    r = client.put(f"/api/events/{ev['id']}", json={"stato": "Rinviato"}, headers=auth_headers)
    assert r.status_code == 422, r.text
    session.expire_all()
    assert session.get(Event, ev["id"]).stato == "Completato"   # invariato

    # controprova: le altre uscite da Completato restano permesse
    assert client.put(f"/api/events/{ev['id']}", json={"stato": "Programmato"},
                      headers=auth_headers).status_code == 200
    client.put(f"/api/events/{ev['id']}", json={"stato": "Completato"}, headers=auth_headers)
    assert client.put(f"/api/events/{ev['id']}", json={"stato": "Cancellato"},
                      headers=auth_headers).status_code == 200
