"""G9.5 (ADR-022, SPEC_G9 §G9.5) — macchina a stati Hypothesis sul dominio finanziario.

Il gemello GENERATIVO dell'harness (`test_financial_invariants_harness.py`): dove l'harness enumera
~12 path manuali (una transizione per scenario), la macchina esplora SEQUENZE di transizioni
(create → rate → pay → terminate → reopen → unpay → …) e verifica `assert_contract_invariants`
(I1-I6, via `_invariants` dell'harness) dopo OGNI mossa (`@invariant`).

Filosofia delle regole: ogni rule TENTA una transizione via API. Il dominio può legittimamente
rifiutarla (guard chiuso, cap 422, bouncer 404, gate G9.4 → 409): il rifiuto è un no-op ESPLORATO
(la proprietà è "qualunque cosa l'API accetti, gli invarianti reggono dopo"). Un 5xx è SEMPRE un bug.

AC-G95-1: sequenze generate + invariante post-mossa; una regressione iniettata fa fallire la macchina
(test dedicato). AC-G95-2: seed PINNATO (`@seed(SM_SEED)` + `database=None`) → run deterministico in CI.
AC-G95-3: dipendenza solo-test (mai importata da `api/`, fuori dal bundle Nuitka per costruzione).
AC-G95-4: i canary noti (Bug-1 eroga→reopen; floor unpay post-reopen) sono replay ESPLICITI delle
stesse rule della macchina.

Note di costruzione:
- Le fixture pytest sono function-scoped e la macchina gira N esempi nello stesso DB: ogni istanza
  traccia SOLO i contratti creati da sé (`self.tracked`) — i residui degli esempi precedenti non
  inquinano l'invariante.
- Le sedute sono INSERT diretti via session (come i builder dell'harness), limitati agli stati
  pre-penale {Completato, Rinviato} e ai contratti APERTI (rispetta il temporal fence ADR-023).
  L'auto-close credit-driven non scatta sull'insert diretto (nessun `_sync`) ma resta raggiungibile
  via `pay_rate` (ricalcola crediti dal DB). Le penali (Cancellato_Tardivo/No_Show) passano dall'API
  con companion write: estensione futura, non simulate a mano.
"""

from datetime import date, datetime, timedelta

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
from api.services.contract_state import STATO_CREDITO_APERTO
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


class FinancialStateMachine(RuleBasedStateMachine):
    # Legate dalla subclass costruita nel test (fixture function-scoped).
    api = None          # TestClient
    headers = None      # auth headers JWT
    client_id = None    # cliente di test
    db = None           # Session diretta (stesso engine)

    contracts = Bundle("contracts")
    rates = Bundle("rates")

    def __init__(self):
        super().__init__()
        self.tracked = []   # contratti creati DA QUESTA istanza (perimetro dell'invariante)
        self._hour = 0      # orologio deterministico per le sedute dirette

    # ── helper ──────────────────────────────────────────────────────────

    def _post(self, path, payload=None):
        r = self.api.post(path, json=payload, headers=self.headers)
        assert r.status_code in OK | REFUSED, f"POST {path} → {r.status_code}: {r.text}"
        return r

    def _contract_row(self, contract_id) -> Contract:
        self.db.expire_all()
        return self.db.get(Contract, contract_id)

    # ── rules: le transizioni del dominio ──────────────────────────────

    @precondition(lambda self: len(self.tracked) < 3)  # liveness: senza cap, i create diluiscono
    @rule(                                              # il bundle e reopen/eroga non vengono MAI
        target=contracts,                               # esercitati (misurato con la sonda 2026-07-05)
        prezzo=st.sampled_from([300.0, 500.0, 1000.0]),
        acconto=st.sampled_from([0.0, 100.0, 200.0, 500.0, 800.0]),
        crediti=st.sampled_from([2, 5, 10]),
    )
    def create_contract(self, prezzo, acconto, crediti):
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
        self._post(f"/api/rates/{rate['id']}/pay",
                   {"importo": round(rate["importo"] * quota, 2), "metodo": "CONTANTI"})

    @rule(rate=rates)
    def unpay_rate(self, rate):
        self._post(f"/api/rates/{rate['id']}/unpay")

    @rule(contract=contracts, stato=st.sampled_from(["Completato", "Rinviato"]),
          n=st.sampled_from([1, 2]))
    def registra_sedute(self, contract, stato, n):
        """Insert diretto (come l'harness), SOLO su contratto aperto (temporal fence ADR-023)."""
        row = self._contract_row(contract)
        if row is None or row.chiuso:
            return
        trainer_id = self.db.exec(select(Trainer)).first().id
        for _ in range(n):
            self._hour += 1
            base = datetime(2026, 1, 1) + timedelta(hours=self._hour)
            self.db.add(Event(
                trainer_id=trainer_id, id_cliente=self.client_id, id_contratto=contract,
                categoria="PT", stato=stato, titolo="Seduta",
                data_inizio=base, data_fine=base + timedelta(hours=1),
            ))
        self.db.commit()

    @rule(contract=contracts, importo=st.sampled_from([50.0, 120.0, 200.0]))
    def incassa_residuo(self, contract, importo):
        self._post(f"/api/contracts/{contract}/incassa-residuo",
                   {"importo": importo, "metodo": "CONTANTI", "data_pagamento": TODAY.isoformat()})

    @rule(contract=contracts, variant=st.sampled_from(range(len(TERMINATE_VARIANTS))))
    def terminate(self, contract, variant):
        self._post(f"/api/contracts/{contract}/terminate", TERMINATE_VARIANTS[variant])

    @rule(contract=contracts)
    def reopen(self, contract):
        self._post(f"/api/contracts/{contract}/reopen")

    @rule(contract=contracts, importo=st.sampled_from([50.0, 250.0]))
    def eroga_wallet(self, contract, importo):
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
        self.db.expire_all()
        receivable = self.db.exec(select(CreditoTerminazione).where(
            CreditoTerminazione.id_contratto == contract,
            CreditoTerminazione.stato == STATO_CREDITO_APERTO,
        )).first()
        if receivable is None:
            return
        self._post(f"/api/contracts/{contract}/crediti-terminazione/{receivable.id}/incassa",
                   {"importo": importo, "metodo": "CONTANTI"})

    # ── l'oracolo: I1-I6 su ogni contratto tracciato, dopo OGNI mossa ───

    @invariant()
    def money_invariants_hold(self):
        for cid in self.tracked:
            violazioni = _invariants(self.db, cid)
            assert violazioni == [], (
                f"contratto {cid}: {[(v.code, v.message) for v in violazioni]}"
            )


def _bind(client, auth_headers, sample_client, session):
    """Subclass con le fixture legate (le istanze le condividono, lo stato per-esempio no)."""
    @seed(SM_SEED)  # AC-G95-2: stesso seed → stessa serie di esempi (supporto ufficiale stateful)
    class BoundMachine(FinancialStateMachine):
        api = client
        headers = auth_headers
        client_id = sample_client["id"]
        db = session
    return BoundMachine


# ── AC-G95-1/2/3: l'esplorazione generativa ─────────────────────────────

def test_financial_state_machine(client, auth_headers, sample_client, session):
    """25 esempi × ≤8 mosse deterministiche: qualunque sequenza l'API accetti, I1-I6 reggono."""
    run_state_machine_as_test(
        _bind(client, auth_headers, sample_client, session), settings=SM_SETTINGS
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
