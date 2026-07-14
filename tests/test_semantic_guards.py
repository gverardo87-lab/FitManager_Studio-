"""G9.4-b (ADR-022 D-INVARIANTI-IMPOSTI) — test SEMANTICI che sostituiscono i 4 grep-guard testuali.

Ogni guard di check-all.sh (ADR-016/017/018/019) ha qui il suo gemello che fallisce sullo STESSO
scenario ma sul SIMBOLO/COMPORTAMENTO reale, non su un pattern di testo in bash. Vive nella suite →
gira in CI a ogni run, non solo al quality-gate; ed è immune alla vacuità-da-rilocazione (lezione
G9.3: un grep che punta a un file svuotato passa in silenzio; un test comportamentale no).
I grep-guard sono stati RITIRATI da check-all.sh solo DOPO che questi test sono verdi (SPEC_G9 §G9.4-b).
"""

import inspect
from datetime import date, timedelta

from sqlmodel import select

import api.services.contract_settlement as contract_settlement
from api.models.contract import Contract
from api.models.movement import CashMovement
from api.services.cash_categories import (
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
    CATEGORIA_RIMBORSO_CONTRATTO,
    CONTRACT_CASH_IN,
    is_contract_inflow,
)
from api.services.contract_state import STATI_OCCUPAZIONE_CREDITO

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


# ── ADR-016 — barriera euro-da-crediti: il conguaglio è CIECO all'occupazione ──────────────────

def test_adr016_settlement_cieco_all_occupazione():
    """Il modulo puro del conguaglio non referenzia MAI l'asse occupazione/crediti: né i token nel
    sorgente, né simboli Event/occupazione nel namespace. Anti-vacuità inclusa: il modulo deve ancora
    contenere compute_settlement (un rename/rilocazione fallisce qui, non passa in silenzio)."""
    src = inspect.getsource(contract_settlement)
    assert "def compute_settlement" in src            # anti-vacuità (lezione guard G9.3)
    for token in ("crediti_residui", "crediti_usati", "sedute_rinviate", "sedute_prenotate"):
        assert token not in src, f"contract_settlement referenzia l'occupazione: {token}"
    assert not hasattr(contract_settlement, "Event")  # niente import dell'asse eventi
    assert not hasattr(contract_settlement, "STATI_OCCUPAZIONE_CREDITO")


# ── ADR-017 — bidirezionale: Rinviato NON occupa MA resta contato nel breakdown display ────────

def test_adr017_rinviato_fuori_occupazione_ma_nel_breakdown(client, auth_headers, sample_client, session):
    """Lo stesso scenario del grep-guard, sul comportamento: un Rinviato non consuma il credito
    (occupazione) ma alimenta `sedute_rinviate` (display, DISPLAY-EXEMPT §3.2). Se qualcuno
    'armonizza' il GROUP BY all'occupazione, sedute_rinviate va a zero → questo test fallisce."""
    assert "Rinviato" not in STATI_OCCUPAZIONE_CREDITO
    c = _contract(client, auth_headers, sample_client["id"])
    r = client.post("/api/events", json={
        "titolo": "PT", "categoria": "PT", "stato": "Rinviato",
        "id_cliente": sample_client["id"], "id_contratto": c["id"],
        "data_inizio": "2026-01-05T09:00:00", "data_fine": "2026-01-05T10:00:00",
    }, headers=auth_headers)
    assert r.status_code in (200, 201), r.text
    detail = client.get(f"/api/contracts/{c['id']}", headers=auth_headers).json()
    assert detail["sedute_rinviate"] == 1             # display conta il Rinviato
    assert detail["crediti_usati"] == 0               # occupazione NO (il rinvio libera il credito)


# ── ADR-018 — l'incasso di conguaglio è un inflow contrattuale (mai fuori dai ricavi) ──────────

def test_adr018_conguaglio_in_contract_cash_in():
    """Se INCASSO_CONGUAGLIO_CONTRATTO esce da CONTRACT_CASH_IN, `is_contract_inflow` lo perde e il
    conguaglio sparisce silenziosamente dai ricavi — il gemello asserisce il simbolo E il predicato."""
    assert CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO in CONTRACT_CASH_IN
    assert is_contract_inflow(CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO)


# ── ADR-019 — reopen NON-distruttivo: la cassa mossa non si tocca ──────────────────────────────

def test_adr019_reopen_non_cancella_la_cassa(client, auth_headers, sample_client, session):
    """Lo scenario esatto del grep-guard, end-to-end: terminate con rimborso → reopen → la USCITA
    RIMBORSO_CONTRATTO esiste ancora, non soft-cancellata. Se qualcuno reintroduce il delete della
    cassa nel reopen (in QUALUNQUE file — immune alla rilocazione), questo fallisce."""
    c = _contract(client, auth_headers, sample_client["id"], acconto=500.0)
    r = client.post(f"/api/contracts/{c['id']}/terminate",
                    json={"metodo_rimborso": "CONTANTI"}, headers=auth_headers)
    assert r.status_code == 200, r.text
    uscite_pre = session.exec(select(CashMovement).where(
        CashMovement.id_contratto == c["id"], CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None,  # noqa: E711
    )).all()
    assert len(uscite_pre) == 1
    r = client.post(f"/api/contracts/{c['id']}/reopen", headers=auth_headers)
    assert r.status_code == 200, r.text
    session.expire_all()
    uscite_post = session.exec(select(CashMovement).where(
        CashMovement.id_contratto == c["id"], CashMovement.tipo == "USCITA",
        CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
        CashMovement.deleted_at == None,  # noqa: E711
    )).all()
    assert len(uscite_post) == 1                      # la cassa RESTA (fatti datati, ADR-019)
    assert uscite_post[0].id == uscite_pre[0].id
    contract = session.get(Contract, c["id"])
    assert round(contract.totale_rimborsato, 2) == round(uscite_post[0].importo, 2)


# ── G8.4 F1.d — R-SSOT-FE: il frontend legge il denaro dal wire, MAI lo ricalcola ──────────────

def test_g84_fe_no_money_math():
    """R-SSOT-FE (SPEC_G8.4 §2 + F1.d): ogni cifra di denaro mostrata dal FE è un campo del backend
    formattato — mai aritmetica client su versato/rimborsato/movimenti. Scansione dei sorgenti
    .ts/.tsx; le eccezioni cap-locali (validazioni input nei dialog) entrano SOLO per allowlist
    esplicita (path, nome-pattern), mai in silenzio."""
    import re
    from pathlib import Path

    frontend_src = Path(__file__).resolve().parents[1] / "frontend" / "src"
    assert frontend_src.is_dir(), frontend_src

    forbidden = (
        ("netto ricalcolato (versato - rimborsato)", re.compile(r"versato\s*-\s*rimborsato")),
        ("aritmetica su totale_versato", re.compile(r"totale_versato\s*-")),
        ("running balance accumulato client-side", re.compile(r"segno\s*\*\s*m\.importo")),
        ("somma client-side dei movimenti", re.compile(r"\.reduce\([^\n]*importo")),
    )
    # Eccezioni LEGITTIME censite (mai in silenzio — ogni entry ha la sua dottrina):
    # - aggregato di VISTA: Σ delle sole righe mostrate (footer/KPI row-derived, riconcilia col
    #   visibile — stessa dottrina del saldo-LEDGER, AC-G84-2); il backend non serve quel totale.
    # - input-local: Σ della selezione utente in un form (stato client, non cifra canonica).
    allowlist: set[tuple[str, str]] = {
        ("app/(dashboard)/rinnovi-incassi/page.tsx", "somma client-side dei movimenti"),  # Σ worklist visualizzata (KPI di vista; consumo-SSoT pieno = Giro 2 SPEC_VOCABOLARIO)
        ("components/movements/LedgerColumn.tsx", "somma client-side dei movimenti"),     # footer di colonna row-derived (riconcilia con le righe filtrate mostrate)
        ("components/movements/RecurringExpensesTab.tsx", "somma client-side dei movimenti"),  # Σ selezione utente nel form conferma spese (input-local)
    }

    violations = []
    for path in sorted(frontend_src.rglob("*.ts")) + sorted(frontend_src.rglob("*.tsx")):
        rel = path.relative_to(frontend_src).as_posix()
        text = path.read_text(encoding="utf-8")
        for name, pattern in forbidden:
            if pattern.search(text) and (rel, name) not in allowlist:
                violations.append(f"{rel}: {name}")
    assert violations == [], (
        "money-math client-side vietato — il FE legge il SSoT dal wire (SPEC_G8.4 F1):\n"
        + "\n".join(violations)
    )


def test_g84_fe_consuma_ssot_netto_e_saldo():
    """Anti-vacuità del gemello sopra (lezione guard G9.3): le superfici DEVONO consumare i campi
    SSoT — se hero/lista smettono di leggere `netto_incassato` o lo storico smette di leggere
    `saldo_progressivo` dal wire, il divieto di money-math sarebbe vero-ma-vuoto."""
    from pathlib import Path

    from api.schemas.financial import ContractMovementItem

    frontend_src = Path(__file__).resolve().parents[1] / "frontend" / "src"
    hero = (frontend_src / "components/contracts/ContractFinancialHero.tsx").read_text(encoding="utf-8")
    # La cella Finanze della lista vive in ContractRow.tsx (riga presentazionale, split F5)
    row = (frontend_src / "components/contracts/ContractRow.tsx").read_text(encoding="utf-8")
    history = (frontend_src / "components/contracts/ContractHistoryTab.tsx").read_text(encoding="utf-8")
    types_api = (frontend_src / "types/api.ts").read_text(encoding="utf-8")

    assert "contract.netto_incassato" in hero          # netto-POSIZIONE dal SSoT (F1.a)
    assert "contract.netto_incassato" in row
    assert "saldo_progressivo" in history              # saldo-LEDGER dal wire (F1.b)
    assert "saldo_progressivo" in types_api            # contratto typescript sincronizzato
    # e il campo esiste davvero sul wire: lo schema Pydantic è l'autorità, non il type FE
    assert "saldo_progressivo" in ContractMovementItem.model_fields


# ── G9.7.4 — D-LEGGI-PER-CLASSE: il guard no-recalc si estende dall'asse denaro all'asse crediti ──

def test_g974_fe_no_credit_math():
    """Il gemello-crediti di `test_g84_fe_no_money_math` (SPEC_G9.7 §G9.7.4): ogni derivato
    dell'asse occupazione mostrato dal FE è un campo del backend — mai `totali − usati`,
    mai `totali − residui`, mai conteggi di stati evento spacciati per occupazione contratto.
    Le eccezioni entrano SOLO per allowlist esplicita motivata, mai in silenzio."""
    import re
    from pathlib import Path

    frontend_src = Path(__file__).resolve().parents[1] / "frontend" / "src"
    assert frontend_src.is_dir(), frontend_src

    forbidden = (
        ("residui ricalcolati inline (totali − usati)",
         re.compile(r"crediti_totali[^\n]{0,24}-\s*(?:\w+\.)?crediti_usati")),
        ("usati ricalcolati inline (totali − residui)",
         re.compile(r"crediti_totali\s*-\s*(?:\w+\.)?crediti_residui")),
        ("occupazione contata da stati evento client-side",
         re.compile(r"\.filter\([^\n]*\.stato\s*===?\s*\"(?:Programmato|Completato|Cancellato_Tardivo|No_Show)\"[^\n]*\)\s*\.length")),
    )
    # Eccezioni LEGITTIME censite (stessa dottrina del money-guard: aggregato di VISTA = conteggio
    # delle sole righe visibili, riconcilia col visibile; NON è l'occupazione di un contratto):
    allowlist: set[tuple[str, str]] = {
        ("lib/dashboard-helpers.ts", "occupazione contata da stati evento client-side"),          # KPI del giorno sul buffer visibile
        ("app/(dashboard)/agenda/page.tsx", "occupazione contata da stati evento client-side"),   # RangeStatsBar: KPI del range visibile
    }

    violations = []
    for path in sorted(frontend_src.rglob("*.ts")) + sorted(frontend_src.rglob("*.tsx")):
        rel = path.relative_to(frontend_src).as_posix()
        text = path.read_text(encoding="utf-8")
        for name, pattern in forbidden:
            if pattern.search(text) and (rel, name) not in allowlist:
                violations.append(f"{rel}: {name}")
    assert violations == [], (
        "credit-math client-side vietato — il FE legge l'occupazione dal wire (SPEC_G9.7 G9.7.4):\n"
        + "\n".join(violations)
    )


def test_g974_fe_consuma_occupazione_dal_wire():
    """Anti-vacuità del gemello sopra (lezione guard G9.3): le superfici DEVONO consumare i campi
    wire dell'asse occupazione — se hero/liste/banner smettono di leggere `crediti_residui`/
    `sedute_penali`/`crediti_usati`, il divieto di credit-math sarebbe vero-ma-vuoto."""
    from pathlib import Path

    from api.schemas.financial import ContractListResponse

    frontend_src = Path(__file__).resolve().parents[1] / "frontend" / "src"
    hero = (frontend_src / "components/contracts/ContractFinancialHero.tsx").read_text(encoding="utf-8")
    row = (frontend_src / "components/contracts/ContractRow.tsx").read_text(encoding="utf-8")
    delete_dialog = (frontend_src / "components/contracts/DeleteContractDialog.tsx").read_text(encoding="utf-8")
    assegna_banner = (frontend_src / "components/agenda/AssegnaContrattoBanner.tsx").read_text(encoding="utf-8")
    rinnovi = (frontend_src / "app/(dashboard)/rinnovi-incassi/page.tsx").read_text(encoding="utf-8")

    assert "contract.crediti_residui" in hero          # D1: residui dal SSoT, mai derivati
    assert "sedute_penali" in hero                     # D1: penali = segnale, dal wire
    assert "sedute_penali" in row                      # D2: sub-label «N svolte · M penali»
    assert "contract.crediti_residui" in delete_dialog  # D4: delete-guard legge il wire
    assert "crediti_residui" in assegna_banner         # G9.7.4: dropdown orfani dal wire
    assert "crediti_usati" in rinnovi                  # G9.7.4: progress bar dal wire
    # e i campi esistono davvero sul wire: lo schema Pydantic è l'autorità, non il type FE
    for campo in ("crediti_residui", "sedute_penali", "sedute_completate"):
        assert campo in ContractListResponse.model_fields, campo


def test_g974_stati_credito_no_reinline():
    """Asse stati crediti/wallet (matrice, flag LOW G9.4-bis chiuso qui): le CLASSIFICAZIONI su
    `CreditoCliente`/`CreditoTerminazione.stato` passano dalle costanti SSoT `STATO_CREDITO_*` —
    mai literal re-inlined nei confronti. `SALDATO` è escluso dalla rete (collide con l'asse
    `stato_pagamento`, che è un altro asse); ogni classificazione wallet realistica tocca
    APERTO (worklist) o ANNULLATO (reopen). Default del modello e stringhe display/audit non
    classificano → fuori dal pattern per costruzione (nessun `==`/`!=`/`in_`)."""
    import re
    from pathlib import Path

    from api.services import contract_state as cstate

    api_src = Path(__file__).resolve().parents[1] / "api"
    assert api_src.is_dir(), api_src

    forbidden = re.compile(
        r"stato\s*(?:==|!=)\s*\"(?:APERTO|ANNULLATO)\""     # confronto diretto con literal
        r"|\.in_\([^\n]*\"(?:APERTO|ANNULLATO)\""            # membership SQL con literal
        r"|stato\s+in\s*[\({\[][^\n]*\"(?:APERTO|ANNULLATO)\""  # membership python con literal
    )
    violations = [
        f"{path.relative_to(api_src).as_posix()}: {m.group(0)!r}"
        for path in sorted(api_src.rglob("*.py"))
        for m in [forbidden.search(path.read_text(encoding="utf-8"))]
        if m
    ]
    assert violations == [], (
        "classificazione stati credito re-inlined — usare cstate.STATO_CREDITO_* (SSoT):\n"
        + "\n".join(violations)
    )
    # Anti-vacuità: il SSoT esiste coi valori attesi E le transizioni lo CONSUMANO davvero
    assert cstate.STATO_CREDITO_APERTO == "APERTO"
    assert cstate.STATO_CREDITO_ANNULLATO == "ANNULLATO"
    from api.services.financial import transitions
    assert "STATO_CREDITO_ANNULLATO" in inspect.getsource(transitions)


# ── G9.7.4 — D-PERIMETRO-TRANSIZIONI: le transizioni dichiarano il destino di OGNI satellite ────

def _tabelle_satellite_contratto(tables):
    """Pura (testabile con tabelle finte): scopre le tabelle che referenziano `contratti` — via FK
    dichiarata O colonna cross-ref per nome. La rete per-nome copre il pattern cross-DB senza FK
    (pitfall #15: una satellite può nascere senza `foreign_key=` e sfuggire alla rete FK)."""
    found = set()
    for table in tables:
        for col in table.columns:
            fk_verso_contratto = any(fk.column.table.name == "contratti" for fk in col.foreign_keys)
            if fk_verso_contratto or col.name in ("id_contratto", "id_contratto_origine"):
                found.add(table.name)
                break
    return found


def test_g974_perimetro_transizioni_esaustivo():
    """SPEC_G9.7 §G9.7.4 (gemello di esaustività della classe «5 produttori»): l'insieme delle
    satellite scoperte dal metadata ORM == l'insieme dichiarato in PERIMETRO_TRANSIZIONE.
    Una tabella nuova che referenzia il contratto → rosso finché terminate/reopen non ne
    dichiarano il destino; una voce fantasma (tabella rimossa/rinominata) → rosso uguale."""
    import api.models  # noqa: F401 — registra tutti i modelli business nel metadata
    from sqlmodel import SQLModel

    from api.services.financial.transitions import PERIMETRO_TRANSIZIONE

    satellites = _tabelle_satellite_contratto(SQLModel.metadata.tables.values())
    non_dichiarate = satellites - set(PERIMETRO_TRANSIZIONE)
    fantasma = set(PERIMETRO_TRANSIZIONE) - satellites
    assert non_dichiarate == set(), (
        "entità satellite del contratto SENZA destino dichiarato nelle transizioni "
        f"(aggiungile a PERIMETRO_TRANSIZIONE con la dottrina terminate/reopen): {sorted(non_dichiarate)}"
    )
    assert fantasma == set(), f"voci fantasma nel perimetro (tabella inesistente): {sorted(fantasma)}"
    # mai un perimetro-segnaposto: ogni voce porta la sua dottrina, non una stringa vuota
    for nome, dottrina in PERIMETRO_TRANSIZIONE.items():
        assert len(dottrina.strip()) >= 20, f"perimetro senza dottrina: {nome}"


def test_g974_perimetro_becca_satellite_nuova():
    """AC-G97-4 (anti-vacuità del gemello sopra): una tabella satellite FINTA con `id_contratto`
    viene scoperta dalla rete per-nome anche SENZA FK dichiarata (pitfall #15) e non essendo nel
    perimetro manderebbe rosso il gemello. Provato sulla funzione pura con un MetaData separato
    (zero inquinamento del registry reale)."""
    from sqlalchemy import Column, Integer, MetaData, Table

    from api.services.financial.transitions import PERIMETRO_TRANSIZIONE

    md = MetaData()
    finta = Table(
        "prestazioni_finte", md,
        Column("id", Integer, primary_key=True),
        Column("id_contratto", Integer),  # cross-ref per nome, NESSUNA FK (il caso pitfall #15)
    )
    trovate = _tabelle_satellite_contratto([finta])
    assert "prestazioni_finte" in trovate              # la rete per-nome la becca
    assert "prestazioni_finte" not in PERIMETRO_TRANSIZIONE  # → il gemello andrebbe rosso
