"""G9.5 + G9.7.5 (ADR-022/ADR-024, SPEC_G9 §G9.5 · SPEC_G9.7 §G9.7.5) — macchina a stati Hypothesis
sul dominio finanziario.

Il gemello GENERATIVO dell'harness (`test_financial_invariants_harness.py`): dove l'harness enumera
~12 path manuali (una transizione per scenario), la macchina esplora SEQUENZE di transizioni
(create → rate → pay → terminate → reopen → unpay → …) e verifica `assert_contract_invariants`
(I1-I6, via `_invariants` dell'harness) dopo OGNI mossa (`@invariant`).

G9.7.5 estende la macchina all'asse OCCUPAZIONE (eventi × contratto): 5 rule — crea PT
auto-assegnato via API (la nascita dell'ORFANO quando i contratti del cliente sono chiusi/pieni:
il caso B1 del founder), crea PT su contratto esplicito via API, `nasce_orfano` (builder diretto,
dà orfani all'esplorazione), cambio stato seduta via API (penali comprese), assegna orfano via
API (G9.7.2) — + invariante **I-EVENTI**: ogni PT in stato di occupazione ha un contratto VALIDO
oppure è SEGNALATO come orfano dalla worklist — mai occupazione fantasma, mai orfano invisibile
(AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07).

Filosofia delle regole: ogni rule TENTA una transizione via API. Il dominio può legittimamente
rifiutarla (guard chiuso, cap 422, bouncer 404, gate G9.4 → 409): il rifiuto è un no-op ESPLORATO
(la proprietà è "qualunque cosa l'API accetti, gli invarianti reggono dopo"). Un 5xx è SEMPRE un bug.

AC-G95-1: sequenze generate + invariante post-mossa; una regressione iniettata fa fallire la macchina
(test dedicato). AC-G95-2: seed PINNATO (`@seed(SM_SEED)` + `database=None`) → run deterministico in CI.
AC-G95-3: dipendenza solo-test (mai importata da `api/`, fuori dal bundle Nuitka per costruzione).
AC-G95-4: i canary noti (Bug-1 eroga→reopen; floor unpay post-reopen) sono replay ESPLICITI delle
stesse rule della macchina.
AC-G97-5: liveness PROVATA — `RULE_FIRINGS` conta ogni invocazione di rule; il test principale
azzera il contatore e asserisce che NESSUNA rule resta a zero sotto il seed pinnato (sonda
2026-07-16, generalizza la sonda manuale del 2026-07-05). Il canary «crea-su-chiuso poi riapri»
è il replay esplicito della composizione B1→segnale→B2-propone→recupero.

Note di costruzione:
- Le fixture pytest sono function-scoped e la macchina gira N esempi nello stesso DB: ogni istanza
  traccia SOLO i contratti/eventi creati da sé (`self.tracked`/`self.tracked_events`) — i residui
  degli esempi precedenti non inquinano l'invariante.
- Le sedute di `registra_sedute` sono INSERT diretti via session (come i builder dell'harness),
  limitate agli stati pre-penale {Completato, Rinviato} sui contratti APERTI (temporal fence
  ADR-023). Le penali (Cancellato_Tardivo/No_Show) passano dall'API con companion `_sync`:
  da G9.7.5 le esercita `cambia_stato_seduta` (PUT), non più simulate a mano.
- Orologio CONDIVISO a livello modulo (`_CLOCK`): gli slot degli eventi non si sovrappongono MAI
  tra esempi. Un orologio per-istanza (il vecchio `self._hour`) farebbe scattare il 409 overlap
  dall'esempio 2 in poi sulle create via API (stesso DB), uccidendo la liveness delle rule nuove.
"""

from collections import Counter
from datetime import date, datetime, timedelta
from itertools import count

import pytest
from hypothesis import HealthCheck, seed, settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    multiple,
    precondition,
    rule,
    run_state_machine_as_test,
)
from sqlmodel import select

from api.models.contract import Contract
from api.models.credito_cliente import CreditoCliente
from api.models.credito_terminazione import CreditoTerminazione
from api.models.event import Event
from api.models.trainer import Trainer
from api.routers.agenda import VALID_STATUSES
from api.services.contract_state import STATI_OCCUPAZIONE_CREDITO, STATO_CREDITO_APERTO
from tests.test_financial_invariants_harness import _invariants

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=120)).isoformat()

OK = {200, 201}
REFUSED = {400, 404, 409, 422}  # guard chiuso / bouncer / gate G9.4 / cap: no-op legittimo

# AC-G95-2 (determinismo CI): seed PINNATO via @seed sul test + database=None (niente replay di
# fallimenti locali cache-dipendenti). NON derandomize=True: misurato con la sonda (2026-07-05),
# derandomize replaya UNA generazione fissa "minimale" che non seleziona mai pay/unpay — il seed
# pinnato mantiene l'esplorazione ricca E il run byte-identico tra macchine (a parità di versione).
SM_SEED = 20260705
SM_SETTINGS = settings(
    max_examples=30,
    stateful_step_count=12,
    database=None,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)

# I rami di terminate dell'harness come payload (l'API sceglie il ramo dal balance server-side:
# un payload incoerente con lo stato → 422, no-op esplorato).
TERMINATE_VARIANTS = [
    {},                                                                      # PARI / CONSUNZIONE
    {"metodo_rimborso": "CONTANTI"},                                         # CREDITO_CLIENTE pieno
    {"importo_rimborso": 0.0},                                               # tutto a wallet
    {"importo_rimborso": 100.0, "metodo_rimborso": "BONIFICO"},              # rimborso parziale
    {"azione_credito_trainer": "INCASSA_ORA", "metodo_pagamento": "CONTANTI"},
    {"azione_credito_trainer": "RINUNCIA_ESPRESSA", "note": "rinuncia esplicita"},
    {"azione_credito_trainer": "A_CREDITO"},                                 # receivable G7.10
]

# Orologio CONDIVISO tra istanze/esempi (vedi Note di costruzione): monotono, mai un overlap.
_CLOCK = count(1)

# Sonda liveness AC-G97-5: ogni rule si conta alla PRIMA riga del corpo; il test principale
# azzera e poi asserisce che nessuna resta a zero. Regola: nuova rule ⇒ contatore + voce qui.
RULE_FIRINGS: Counter = Counter()
RULE_NAMES = (
    "create_contract", "add_rate", "pay_rate", "unpay_rate", "registra_sedute",
    "incassa_residuo", "terminate", "reopen", "eroga_wallet", "incassa_receivable",
    "crea_pt_auto", "crea_pt_su_contratto", "nasce_orfano", "cambia_stato_seduta",
    "assegna_orfano",
)


class FinancialStateMachine(RuleBasedStateMachine):
    # Legate dalla subclass costruita nel test (fixture function-scoped).
    api = None          # TestClient
    headers = None      # auth headers JWT
    client_id = None    # cliente di test
    db = None           # Session diretta (stesso engine)

    contracts = Bundle("contracts")
    rates = Bundle("rates")
    events = Bundle("events")

    def __init__(self):
        super().__init__()
        self.tracked = []          # contratti creati DA QUESTA istanza (perimetro invariante I1-I6)
        self.tracked_events = []   # eventi PT creati via API DA QUESTA istanza (perimetro I-EVENTI)

    # ── helper ──────────────────────────────────────────────────────────

    def _post(self, path, payload=None):
        r = self.api.post(path, json=payload, headers=self.headers)
        assert r.status_code in OK | REFUSED, f"POST {path} → {r.status_code}: {r.text}"
        return r

    def _put(self, path, payload):
        r = self.api.put(path, json=payload, headers=self.headers)
        assert r.status_code in OK | REFUSED, f"PUT {path} → {r.status_code}: {r.text}"
        return r

    def _contract_row(self, contract_id) -> Contract:
        self.db.expire_all()
        return self.db.get(Contract, contract_id)

    def _pt_body(self, stato):
        """Slot orario fresco dall'orologio condiviso: mai un 409 overlap tra esempi."""
        base = datetime(2026, 1, 1) + timedelta(hours=next(_CLOCK))
        return {
            "data_inizio": base.isoformat(),
            "data_fine": (base + timedelta(minutes=45)).isoformat(),
            "categoria": "PT", "titolo": "Seduta PT",
            "id_cliente": self.client_id, "stato": stato,
        }

    # ── rules: le transizioni del dominio ──────────────────────────────

    @precondition(lambda self: len(self.tracked) < 3)  # liveness: senza cap, i create diluiscono
    @rule(                                              # il bundle e reopen/eroga non vengono MAI
        target=contracts,                               # esercitati (misurato con la sonda 2026-07-05)
        prezzo=st.sampled_from([300.0, 500.0, 1000.0]),
        acconto=st.sampled_from([0.0, 100.0, 200.0, 500.0, 800.0]),
        crediti=st.sampled_from([2, 5, 10]),
    )
    def create_contract(self, prezzo, acconto, crediti):
        RULE_FIRINGS["create_contract"] += 1
        acconto = min(acconto, prezzo)  # il cap lo darebbe il 422: pieghiamo per esplorare di più
        body = {
            "id_cliente": self.client_id, "tipo_pacchetto": "Pkg", "crediti_totali": crediti,
            "prezzo_totale": prezzo, "data_inizio": TODAY.isoformat(), "data_scadenza": FUTURE,
            "acconto": acconto,
        }
        if acconto > 0:
            body["metodo_acconto"] = "CONTANTI"
        r = self._post("/api/contracts", body)
        if r.status_code != 201:
            return multiple()
        cid = r.json()["id"]
        self.tracked.append(cid)
        return cid

    @rule(target=rates, contract=contracts, importo=st.sampled_from([100.0, 250.0, 400.0]))
    def add_rate(self, contract, importo):
        RULE_FIRINGS["add_rate"] += 1
        r = self._post("/api/rates", {
            "id_contratto": contract,
            "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
            "importo_previsto": importo,
        })
        if r.status_code != 201:
            return multiple()
        return {"id": r.json()["id"], "importo": importo}

    @rule(rate=rates, quota=st.sampled_from([1.0, 0.5]))
    def pay_rate(self, rate, quota):
        RULE_FIRINGS["pay_rate"] += 1
        self._post(f"/api/rates/{rate['id']}/pay",
                   {"importo": round(rate["importo"] * quota, 2), "metodo": "CONTANTI"})

    @rule(rate=rates)
    def unpay_rate(self, rate):
        RULE_FIRINGS["unpay_rate"] += 1
        self._post(f"/api/rates/{rate['id']}/unpay")

    @rule(contract=contracts, stato=st.sampled_from(["Completato", "Rinviato"]),
          n=st.sampled_from([1, 2]))
    def registra_sedute(self, contract, stato, n):
        """Insert diretto (come l'harness), SOLO su contratto aperto (temporal fence ADR-023)."""
        RULE_FIRINGS["registra_sedute"] += 1
        row = self._contract_row(contract)
        if row is None or row.chiuso:
            return
        trainer_id = self.db.exec(select(Trainer)).first().id
        for _ in range(n):
            base = datetime(2026, 1, 1) + timedelta(hours=next(_CLOCK))
            self.db.add(Event(
                trainer_id=trainer_id, id_cliente=self.client_id, id_contratto=contract,
                categoria="PT", stato=stato, titolo="Seduta",
                data_inizio=base, data_fine=base + timedelta(hours=1),
            ))
        self.db.commit()

    @rule(contract=contracts, importo=st.sampled_from([50.0, 120.0, 200.0]))
    def incassa_residuo(self, contract, importo):
        RULE_FIRINGS["incassa_residuo"] += 1
        self._post(f"/api/contracts/{contract}/incassa-residuo",
                   {"importo": importo, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()})

    @rule(contract=contracts, variant=st.sampled_from(range(len(TERMINATE_VARIANTS))))
    def terminate(self, contract, variant):
        RULE_FIRINGS["terminate"] += 1
        self._post(f"/api/contracts/{contract}/terminate", TERMINATE_VARIANTS[variant])

    @rule(contract=contracts)
    def reopen(self, contract):
        RULE_FIRINGS["reopen"] += 1
        self._post(f"/api/contracts/{contract}/reopen")

    @rule(contract=contracts, importo=st.sampled_from([50.0, 250.0]))
    def eroga_wallet(self, contract, importo):
        RULE_FIRINGS["eroga_wallet"] += 1
        self.db.expire_all()
        wallet = self.db.exec(select(CreditoCliente).where(
            CreditoCliente.id_contratto_origine == contract,
            CreditoCliente.stato == STATO_CREDITO_APERTO,
        )).first()
        if wallet is None:
            return
        self._post(f"/api/clients/{self.client_id}/crediti/{wallet.id}/eroga",
                   {"importo": importo, "metodo": "CONTANTI"})

    @rule(contract=contracts, importo=st.sampled_from([50.0, 100.0]))
    def incassa_receivable(self, contract, importo):
        RULE_FIRINGS["incassa_receivable"] += 1
        self.db.expire_all()
        receivable = self.db.exec(select(CreditoTerminazione).where(
            CreditoTerminazione.id_contratto == contract,
            CreditoTerminazione.stato == STATO_CREDITO_APERTO,
        )).first()
        if receivable is None:
            return
        self._post(f"/api/contracts/{contract}/crediti-terminazione/{receivable.id}/incassa",
                   {"importo": importo, "metodo": "CONTANTI"})

    # ── rules G9.7.5: l'asse OCCUPAZIONE via API (eventi × contratto) ───

    @precondition(lambda self: len(self.tracked_events) < 4)  # liveness: stesso razionale del
    @rule(target=events,                                      # cap sui contratti
          stato=st.sampled_from(["Programmato", "Completato"]))
    def crea_pt_auto(self, stato):
        """POST /events SENZA id_contratto: auto-FIFO server-side. Se nessun contratto aperto del
        cliente ha crediti liberi → nasce un ORFANO (201 con id_contratto=None): la nascita B1,
        oggi SEGNALATA dalla worklist (G9.7.2) — I-EVENTI la verifica dopo ogni mossa."""
        RULE_FIRINGS["crea_pt_auto"] += 1
        r = self._post("/api/events", self._pt_body(stato))
        if r.status_code != 201:
            return multiple()
        body = r.json()
        if body["id_contratto"] is None:
            RULE_FIRINGS["_orfano_nato"] += 1
        self.tracked_events.append(body["id"])
        return body["id"]

    @precondition(lambda self: len(self.tracked_events) < 4)
    @rule(target=events, contract=contracts,
          stato=st.sampled_from(["Programmato", "Completato"]))
    def crea_pt_su_contratto(self, contract, stato):
        """POST /events CON id_contratto esplicito: bouncer chiuso → 400, credit-guard → 400
        (no-op esplorati); su contratto vivo con crediti liberi → 201 agganciato."""
        RULE_FIRINGS["crea_pt_su_contratto"] += 1
        body = self._pt_body(stato)
        body["id_contratto"] = contract
        r = self._post("/api/events", body)
        if r.status_code != 201:
            return multiple()
        self.tracked_events.append(r.json()["id"])
        return r.json()["id"]

    @precondition(lambda self: len(self.tracked_events) < 4)
    @rule(target=events, stato=st.sampled_from(["Programmato", "Completato"]))
    def nasce_orfano(self, stato):
        """Insert diretto di un PT ORFANO (id_contratto=NULL) — stato API-raggiungibile (canary
        B1 + test integrazione G9.7.2), builder come `registra_sedute`. Serve all'esplorazione:
        la nascita SPONTANEA via auto-FIFO è rara (i contratti aperti residui degli esempi
        precedenti trovano sempre casa all'evento: `_orfano_nato`≈0 sotto il seed) — senza
        questo builder il generativo non eserciterebbe mai assegna-con-successo né il ramo
        orfano di I-EVENTI."""
        RULE_FIRINGS["nasce_orfano"] += 1
        trainer_id = self.db.exec(select(Trainer)).first().id
        base = datetime(2026, 1, 1) + timedelta(hours=next(_CLOCK))
        ev = Event(
            trainer_id=trainer_id, id_cliente=self.client_id, id_contratto=None,
            categoria="PT", stato=stato, titolo="Seduta orfana",
            data_inizio=base, data_fine=base + timedelta(hours=1),
        )
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)
        self.tracked_events.append(ev.id)
        return ev.id

    @rule(event=events, stato=st.sampled_from(sorted(VALID_STATUSES)))
    def cambia_stato_seduta(self, event, stato):
        """PUT /events/{id} stato: l'occupazione sale/scende via API (penali G7.8-bis comprese) e
        il companion `_sync_contract_chiuso` può chiudere/riaprire il contratto (composizione);
        il temporal fence ADR-023 rifiuta (409) il tocco della base contabilizzata su contratto
        liquidato: no-op esplorato."""
        RULE_FIRINGS["cambia_stato_seduta"] += 1
        self._put(f"/api/events/{event}", {"stato": stato})

    @rule(event=events, contract=contracts)
    def assegna_orfano(self, event, contract):
        """POST /events/{id}/assegna-contratto (G9.7.2): l'UNICA via di re-parenting. Rifiuta
        già-agganciato / contratto chiuso / credit-guard (400, no-op esplorati); su orfano +
        contratto vivo con spazio → aggancia e OCCUPA (auto-close in composizione)."""
        RULE_FIRINGS["assegna_orfano"] += 1
        self._post(f"/api/events/{event}/assegna-contratto", {"id_contratto": contract})

    # ── l'oracolo: I1-I6 su ogni contratto tracciato, dopo OGNI mossa ───

    @invariant()
    def money_invariants_hold(self):
        for cid in self.tracked:
            violazioni = _invariants(self.db, cid)
            assert violazioni == [], (
                f"contratto {cid}: {[(v.code, v.message) for v in violazioni]}"
            )

    # ── l'oracolo G9.7.5: I-EVENTI su ogni evento tracciato, dopo OGNI mossa ──

    @invariant()
    def i_eventi_occupazione_sempre_spiegata(self):
        """I-EVENTI (ADR-024): ogni PT in stato di occupazione ha un contratto VALIDO (esiste,
        non eliminato, stesso cliente) OPPURE è SEGNALATO come orfano dalla worklist
        /dashboard/orphan-events — mai occupazione fantasma, mai orfano invisibile."""
        if not self.tracked_events:
            return
        self.db.expire_all()
        segnalati = None  # lazy: la worklist si interroga solo se c'è un orfano da spiegare
        for eid in self.tracked_events:
            ev = self.db.get(Event, eid)
            if ev is None or ev.deleted_at is not None or ev.stato not in STATI_OCCUPAZIONE_CREDITO:
                continue
            if ev.id_contratto is None:
                if segnalati is None:
                    r = self.api.get("/api/dashboard/orphan-events", headers=self.headers)
                    assert r.status_code == 200, r.text
                    segnalati = {row["id"] for row in r.json()["items"]}
                assert eid in segnalati, f"evento {eid}: orfano INVISIBILE (fuori dalla worklist)"
            else:
                c = self.db.get(Contract, ev.id_contratto)
                assert (
                    c is not None and c.deleted_at is None and c.id_cliente == ev.id_cliente
                ), f"evento {eid}: occupazione FANTASMA sul contratto {ev.id_contratto}"


def _bind(client, auth_headers, sample_client, session):
    """Subclass con le fixture legate (le istanze le condividono, lo stato per-esempio no)."""
    @seed(SM_SEED)  # AC-G95-2: stesso seed → stessa serie di esempi (supporto ufficiale stateful)
    class BoundMachine(FinancialStateMachine):
        api = client
        headers = auth_headers
        client_id = sample_client["id"]
        db = session
    return BoundMachine


# ── AC-G95-1/2/3 + AC-G97-5: l'esplorazione generativa ──────────────────

def test_financial_state_machine(client, auth_headers, sample_client, session):
    """30 esempi × ≤12 mosse deterministiche: qualunque sequenza l'API accetti, I1-I6 + I-EVENTI
    reggono. AC-G97-5 (liveness): sotto il seed pinnato OGNI rule viene esercitata."""
    RULE_FIRINGS.clear()
    run_state_machine_as_test(
        _bind(client, auth_headers, sample_client, session), settings=SM_SETTINGS
    )
    mai_esercitate = sorted(n for n in RULE_NAMES if RULE_FIRINGS[n] == 0)
    assert not mai_esercitate, (
        f"AC-G97-5 liveness: rule mai esercitate sotto SM_SEED={SM_SEED}: {mai_esercitate} — "
        "la generazione è cambiata (rule nuove? bump Hypothesis?): ri-tarare cap/seed con la sonda"
    )


# ── AC-G95-1 (negativo): una regressione iniettata fa fallire la macchina ──

def test_regressione_iniettata_fa_fallire_la_macchina(client, auth_headers, sample_client, session):
    """L'oracolo della macchina non è vacuo: un drift I4 scritto a mano lo fa scattare."""
    m = _bind(client, auth_headers, sample_client, session)()
    cid = m.create_contract(prezzo=1000.0, acconto=200.0, crediti=10)
    contract = session.get(Contract, cid)
    contract.quota_stornata = -5.0
    session.add(contract)
    session.commit()
    with pytest.raises(AssertionError, match="I4"):
        m.money_invariants_hold()


# ── AC-G97-5 (negativo): l'oracolo I-EVENTI non è vacuo, su ENTRAMBI i rami ──

def test_i_eventi_non_vacuo(client, auth_headers, sample_client, session, monkeypatch):
    """L'oracolo I-EVENTI scatta su entrambe le gambe: (a) orfano INVISIBILE — se la worklist
    smette di segnalarlo (qui: helper svuotato a mano), l'invariante lo denuncia; (b) occupazione
    FANTASMA — un id_contratto che non esiste. Gemello del test-regressione-iniettata per I4."""
    m = _bind(client, auth_headers, sample_client, session)()
    eid = m.crea_pt_auto(stato="Programmato")   # nessun contratto del cliente → nasce orfano
    assert isinstance(eid, int)
    # Il segnale c'è (worklist lo porta): I-EVENTI passa
    m.i_eventi_occupazione_sempre_spiegata()

    # (a) orfano INVISIBILE: la worklist "perde" gli orfani → l'invariante scatta
    from api.routers import dashboard as dashboard_router
    monkeypatch.setattr(dashboard_router, "_orphan_pt_candidates", lambda session, trainer_id: [])
    with pytest.raises(AssertionError, match="INVISIBILE"):
        m.i_eventi_occupazione_sempre_spiegata()
    monkeypatch.undo()

    # (b) occupazione FANTASMA costruita a mano: id_contratto che non esiste
    ev = session.get(Event, eid)
    ev.id_contratto = 999_999
    session.add(ev)
    session.commit()
    with pytest.raises(AssertionError, match="FANTASMA"):
        m.i_eventi_occupazione_sempre_spiegata()


# ── AC-G95-4: i canary noti come replay ESPLICITI delle rule ────────────

def test_canary_bug1_eroga_wallet_then_reopen(client, auth_headers, sample_client, session):
    """🐞 Bug-1 (audit 2026-06-28): terminate rimborso 0 (wallet) → eroga → reopen. Il riassorbimento
    del wallet erogato (G8.2-prep R2-bis) tiene I5: se il reopen smette di riassorbire, rosso qui."""
    m = _bind(client, auth_headers, sample_client, session)()
    cid = m.create_contract(prezzo=1000.0, acconto=800.0, crediti=10)
    m.registra_sedute(contract=cid, stato="Completato", n=2)
    m.terminate(contract=cid, variant=2)          # importo_rimborso 0 → tutto a wallet
    m.eroga_wallet(contract=cid, importo=250.0)
    m.reopen(contract=cid)
    m.money_invariants_hold()


def test_canary_floor_unpay_post_reopen(client, auth_headers, sample_client, session):
    """Il reperto del full-suite G9.4 (aafba2d): reopen non-distruttivo preserva la cassa (ADR-019) →
    la cassa preservata fa da FLOOR alle revoche. L'unpay sotto il floor DEVE essere rifiutato (409,
    I4 dal gate) e gli invarianti reggono; se il gate si spegne, l'invariante della macchina scatta."""
    m = _bind(client, auth_headers, sample_client, session)()
    cid = m.create_contract(prezzo=1000.0, acconto=0.0, crediti=2)
    rata = {"id": None, "importo": 500.0}
    r = client.post("/api/rates", json={
        "id_contratto": cid, "data_scadenza": (TODAY + timedelta(days=20)).isoformat(),
        "importo_previsto": 500.0,
    }, headers=auth_headers)
    rata["id"] = r.json()["id"]
    m.pay_rate(rate=rata, quota=1.0)
    m.incassa_residuo(contract=cid, importo=200.0)
    m.registra_sedute(contract=cid, stato="Completato", n=2)
    m.terminate(contract=cid, variant=1)          # rimborso pieno del credito cliente
    m.reopen(contract=cid)
    unpay = client.post(f"/api/rates/{rata['id']}/unpay", headers=auth_headers)
    assert unpay.status_code in (200, 409), unpay.text
    m.money_invariants_hold()


def test_canary_crea_su_chiuso_poi_riapri(client, auth_headers, sample_client, session):
    """🐞 B1/B2 (AUDIT_CREDITI_EVENTI_ORFANI_2026-07-07, caso founder contratto 39): il PT creato
    quando l'unico contratto del cliente è CHIUSO nasce ORFANO (l'auto-assign filtra i chiusi) —
    MAI in silenzio: la worklist lo segnala (I-EVENTI); il reopen lo NOMINA (D-PROPONE) e non lo
    riaggancia da solo; il recupero è l'atto esplicito `assegna-contratto` → occupa il credito e
    il segnale si spegne. Se una gamba della composizione sparisce (segnale, proposta, via
    esplicita), rosso qui — è il deadlock-da-protezioni-giuste che G9.7 ha sciolto."""
    m = _bind(client, auth_headers, sample_client, session)()
    cid = m.create_contract(prezzo=500.0, acconto=500.0, crediti=5)
    m.registra_sedute(contract=cid, stato="Completato", n=2)
    m.terminate(contract=cid, variant=2)          # credito cliente → wallet, contratto CHIUSO
    assert m._contract_row(cid).chiuso is True    # precondizione del canary: chiusura riuscita

    # B1: la nascita dell'orfano via API (auto-assign non trova contratti aperti)
    eid = m.crea_pt_auto(stato="Programmato")
    assert isinstance(eid, int), "la nascita dell'orfano è stata rifiutata"
    ev = client.get(f"/api/events/{eid}", headers=auth_headers).json()
    assert ev["id_contratto"] is None
    # Mai orfano invisibile: la worklist lo segnala e l'invariante lo copre
    w = client.get("/api/dashboard/orphan-events", headers=auth_headers).json()
    assert eid in {row["id"] for row in w["items"]}
    m.i_eventi_occupazione_sempre_spiegata()

    # B2: il reopen NOMINA l'orfano del periodo di chiusura e NON lo riaggancia (D-PROPONE)
    rr = client.post(f"/api/contracts/{cid}/reopen", headers=auth_headers)
    assert rr.status_code == 200, rr.text
    assert eid in [o["id"] for o in rr.json()["orfani_periodo_chiusura"]]
    assert client.get(f"/api/events/{eid}", headers=auth_headers).json()["id_contratto"] is None

    # Recupero esplicito: assegna → aggancia, occupa, il segnale si spegne
    m.assegna_orfano(event=eid, contract=cid)
    ev = client.get(f"/api/events/{eid}", headers=auth_headers).json()
    assert ev["id_contratto"] == cid, "l'assegnazione esplicita deve riuscire (era il limbo B1/B2)"
    d = client.get(f"/api/contracts/{cid}", headers=auth_headers).json()
    assert d["crediti_usati"] == 3                # 2 registrate + l'orfano recuperato
    w2 = client.get("/api/dashboard/orphan-events", headers=auth_headers).json()
    assert eid not in {row["id"] for row in w2["items"]}
    m.money_invariants_hold()
    m.i_eventi_occupazione_sempre_spiegata()
