# api/routers/dashboard.py
"""
Endpoint Dashboard — KPI aggregati con query SQL ottimizzate.

Tutte le metriche vengono calcolate direttamente nel database
tramite func.count() e func.sum(). Nessun record viene caricato
in Python — latenza zero, scalabile anche con migliaia di record.

Multi-tenancy: ogni query filtra per trainer_id dal JWT.
"""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import bindparam
from sqlmodel import Session, select, func, text

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.movement import CashMovement
from api.models.rate import Rate
from api.models.event import Event
from api.models.contract import Contract
from api.models.exercise import Exercise
from api.models.credito_terminazione import CreditoTerminazione
from api.models.credito_cliente import CreditoCliente
from api.schemas.financial import (
    DashboardSummary, ReconciliationItem, ReconciliationResponse,
    AlertItem, DashboardAlerts,
)
from api.schemas.clinical import (
    ClinicalReadinessResponse,
    ClinicalReadinessWorklistResponse,
)
from api.routers.movements import _compute_saldo
from api.services import contract_state as cstate
from api.services.cash_categories import CATEGORIA_RIMBORSO_CONTRATTO
from api.services.clinical_readiness import (
    compute_clinical_readiness_data,
    filter_clinical_readiness_items,
    sort_clinical_readiness_items,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
):
    """
    KPI aggregati per la dashboard del trainer.

    Metriche:
    - active_clients: clienti con stato 'Attivo'
    - monthly_revenue: somma ENTRATE del mese corrente
    - pending_rates: rate scadute o in scadenza nei prossimi 7 giorni
    - todays_appointments: eventi di oggi

    Tutte le query usano func.count/func.sum — aggregazione SQL pura.
    """
    today = date.today()

    # 1. Clienti attivi
    active_clients = session.exec(
        select(func.count(Client.id)).where(
            Client.trainer_id == trainer.id,
            Client.stato == "Attivo",
            Client.deleted_at == None,
        )
    ).one()

    # 2. Revenue mese corrente — INCASSI DA CONTRATTI per cassa.
    # G9.4-bis.2: le due query sono le proiezioni SQL di ClasseContabile.RICAVO_CONTRATTUALE
    # (ENTRATA ∧ id_contratto≠NULL) e ClasseContabile.CONTRA_RICAVO (USCITA RIMBORSO): revenue NETTO.
    # Ristretto a id_contratto valorizzato (acconti + rate): esclude automaticamente
    # gli storni (STORNO_SPESA_FISSA, id_contratto NULL) e gli incassi fuori contratto
    # (id_contratto NULL). Coerente con TASSONOMIA §1/§2 e con L1 (financial-trend).
    # Prima era sum(ENTRATA) generico → sovrastimava (includeva storni e altri incassi).
    first_of_month = today.replace(day=1)
    if today.month == 12:
        first_of_next = today.replace(year=today.year + 1, month=1, day=1)
    else:
        first_of_next = today.replace(month=today.month + 1, day=1)

    revenue_result = session.exec(
        select(func.sum(CashMovement.importo)).where(
            CashMovement.trainer_id == trainer.id,
            CashMovement.tipo == "ENTRATA",
            CashMovement.id_contratto != None,  # solo incassi da contratti (per cassa)
            CashMovement.data_effettiva >= first_of_month,
            CashMovement.data_effettiva < first_of_next,
            CashMovement.deleted_at == None,
        )
    ).one()
    monthly_revenue = revenue_result or 0.0
    # G7.5: al netto dei rimborsi del mese (RIMBORSO_CONTRATTO = USCITA contra-ricavo) → revenue NETTO,
    # non lordo. Senza, un terminate-con-rimborso sovrastimerebbe il "revenue del mese".
    rimborsi_result = session.exec(
        select(func.sum(CashMovement.importo)).where(
            CashMovement.trainer_id == trainer.id,
            CashMovement.tipo == "USCITA",
            CashMovement.categoria == CATEGORIA_RIMBORSO_CONTRATTO,
            CashMovement.data_effettiva >= first_of_month,
            CashMovement.data_effettiva < first_of_next,
            CashMovement.deleted_at == None,
        )
    ).one()
    monthly_revenue = monthly_revenue - (rimborsi_result or 0.0)

    # 3. Rate pendenti: scadute (data_scadenza < oggi) + in scadenza (prossimi 7 giorni)
    #    Deep filter: solo rate di contratti del trainer

    deadline = today + timedelta(days=7)
    pending_rates = session.exec(
        select(func.count(Rate.id))
        .join(Contract, Rate.id_contratto == Contract.id)
        .where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza <= deadline,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
    ).one()

    # 4. Appuntamenti di oggi (solo attivi — escludi Cancellato)
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    todays_appointments = session.exec(
        select(func.count(Event.id)).where(
            Event.trainer_id == trainer.id,
            Event.data_inizio >= today_start,
            Event.data_inizio <= today_end,
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
    ).one()

    # 5. Ledger alerts: contratti con divergenza totale_versato vs movimenti
    divergent_count = session.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT c.id
            FROM contratti c
            LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id
                AND m.tipo = 'ENTRATA' AND m.deleted_at IS NULL
            WHERE c.trainer_id = :tid AND c.deleted_at IS NULL
            GROUP BY c.id
            HAVING ROUND(c.totale_versato - COALESCE(SUM(m.importo), 0), 2) > 0.01
               OR ROUND(COALESCE(SUM(m.importo), 0) - c.totale_versato, 2) > 0.01
        )
    """), {"tid": trainer.id}).scalar() or 0

    # 6. Saldo di cassa attuale (computed on read)
    saldo_attuale = _compute_saldo(session, trainer, as_of=today)

    # 7. Esercizi attivi (in_subset=True) — catalog.db
    exercise_count = catalog_session.exec(
        select(func.count(Exercise.id)).where(
            Exercise.in_subset == True,
            Exercise.deleted_at == None,
        )
    ).one()

    return DashboardSummary(
        active_clients=active_clients,
        monthly_revenue=round(monthly_revenue, 2),
        pending_rates=pending_rates,
        todays_appointments=todays_appointments,
        ledger_alerts=divergent_count,
        saldo_attuale=saldo_attuale,
        exercise_count=exercise_count,
    )


@router.get("/reconciliation", response_model=ReconciliationResponse)
def get_reconciliation(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Audit riconciliazione BIDIREZIONALE (G9.0b): confronta le colonne denormalizzate di ogni contratto
    con il libro mastro, su ENTRAMBE le ancore.

    - Lato VERSATO: `totale_versato == Σ ENTRATA[id_contratto]`.
    - Lato RIMBORSATO (ancora I5 raffinata, ADR-019 D1 forma-d):
      `totale_rimborsato == Σ USCITA RIMBORSO_CONTRATTO[id_contratto] + Σ erogato wallet ANNULLATO[origine]`
      (il secondo addendo è la cassa-wallet `id_contratto=None` riassorbita al reopen — senza, un reopen
      con wallet erogato sembrerebbe una falsa divergenza).

    Un contratto è "divergente" se diverge su versato E/O rimborsato. Soglia: 0.01 EUR (arrotondamento).
    """
    rows = session.execute(text("""
        SELECT c.id, cl.nome, cl.cognome, c.totale_versato, c.totale_rimborsato,
               COALESCE(SUM(CASE WHEN m.tipo = 'ENTRATA' THEN m.importo ELSE 0 END), 0) as ledger_entrate,
               COALESCE(SUM(CASE WHEN m.tipo = 'USCITA' AND m.categoria = :rimborso_cat
                                 THEN m.importo ELSE 0 END), 0) as ledger_rimborsi_diretti,
               COALESCE((SELECT SUM(cc.importo_erogato) FROM crediti_cliente cc
                         WHERE cc.id_contratto_origine = c.id AND cc.stato = :stato_annullato
                           AND cc.deleted_at IS NULL), 0) as wallet_riassorbito
        FROM contratti c
        LEFT JOIN clienti cl ON cl.id = c.id_cliente
        LEFT JOIN movimenti_cassa m ON m.id_contratto = c.id AND m.deleted_at IS NULL
        WHERE c.trainer_id = :tid AND c.deleted_at IS NULL
        GROUP BY c.id
    """), {"tid": trainer.id, "rimborso_cat": CATEGORIA_RIMBORSO_CONTRATTO,
         "stato_annullato": cstate.STATO_CREDITO_ANNULLATO}).fetchall()

    items = []
    aligned = 0
    for row in rows:
        cid, nome, cognome, versato, rimborsato, ledger_entrate, ledger_rimborsi_diretti, wallet_riassorbito = row
        versato = versato or 0
        rimborsato = rimborsato or 0
        # Ancora I5 raffinata (D1 forma-d): USCITA RIMBORSO dirette + erogato wallet ANNULLATO riassorbito.
        ledger_rimborsi = round((ledger_rimborsi_diretti or 0) + (wallet_riassorbito or 0), 2)
        delta_versato = round(versato - (ledger_entrate or 0), 2)
        delta_rimborsi = round(rimborsato - ledger_rimborsi, 2)
        if abs(delta_versato) > 0.01 or abs(delta_rimborsi) > 0.01:
            items.append(ReconciliationItem(
                contract_id=cid,
                client_name=f"{nome or ''} {cognome or ''}".strip(),
                totale_versato=round(versato, 2),
                ledger_total=round(ledger_entrate or 0, 2),
                delta=delta_versato,
                totale_rimborsato=round(rimborsato, 2),
                ledger_rimborsi=ledger_rimborsi,
                delta_rimborsi=delta_rimborsi,
            ))
        else:
            aligned += 1

    return ReconciliationResponse(
        total_contracts=len(rows),
        aligned=aligned,
        divergent=len(items),
        items=items,
    )


@router.get("/ghost-events")
def get_ghost_events(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Eventi fantasma: sessioni passate ancora in stato 'Programmato'.

    Restituisce la lista completa con dati cliente per risoluzione inline
    dalla Dashboard (Sheet con azioni 'Completata'/'Cancellata').

    Ordinamento: piu' vecchi prima (urgenza decrescente).
    """
    today_start = datetime.combine(date.today(), datetime.min.time())

    stmt = (
        select(Event)
        .where(
            Event.trainer_id == trainer.id,
            Event.data_fine < today_start,
            Event.stato == "Programmato",
            Event.deleted_at == None,
        )
        .order_by(Event.data_inizio.asc())
    )
    events = session.exec(stmt).all()

    # Batch fetch nomi clienti (anti-N+1)
    client_ids = {e.id_cliente for e in events if e.id_cliente}
    clients_map: dict[int, Client] = {}
    if client_ids:
        clients = session.exec(
            select(Client).where(Client.id.in_(client_ids))
        ).all()
        clients_map = {c.id: c for c in clients}

    items = []
    for e in events:
        cl = clients_map.get(e.id_cliente) if e.id_cliente else None
        items.append({
            "id": e.id,
            "data_inizio": e.data_inizio.isoformat() if isinstance(e.data_inizio, datetime) else str(e.data_inizio),
            "data_fine": e.data_fine.isoformat() if isinstance(e.data_fine, datetime) else str(e.data_fine),
            "categoria": e.categoria,
            "titolo": e.titolo,
            "id_cliente": e.id_cliente,
            "id_contratto": e.id_contratto,
            "stato": e.stato,
            "note": e.note,
            "cliente_nome": cl.nome if cl else None,
            "cliente_cognome": cl.cognome if cl else None,
        })

    return {"items": items, "total": len(items)}


def _orphan_pt_candidates(session: Session, trainer_id: int) -> list[Event]:
    """G9.7.2/B6: PT orfani in stati di OCCUPAZIONE (Programmato/Completato/penali) — visibili,
    mai limbo. Helper condiviso da worklist e alert → count == len(items) garantito.
    Rinviato/Cancellato esclusi: un orfano che non occuperebbe credito non è un caso da risolvere."""
    return list(session.exec(
        select(Event)
        .where(
            Event.trainer_id == trainer_id,
            Event.categoria == "PT",
            Event.id_contratto == None,
            Event.id_cliente != None,
            Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
            Event.deleted_at == None,
        )
        .order_by(Event.data_inizio.asc())
    ).all())


@router.get("/orphan-events")
def get_orphan_events(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    G9.7.2/B6 — worklist dei PT senza contratto (orfani) in stati di occupazione.

    Ogni riga porta l'AZIONE (D-SEGNALE-AZIONE): i contratti APERTI del cliente con crediti
    residui, così il FE offre «Assegna» inline via `POST /events/{id}/assegna-contratto`.
    Ordinamento: più vecchi prima.
    """
    orphans = _orphan_pt_candidates(session, trainer.id)

    client_ids = {e.id_cliente for e in orphans if e.id_cliente}
    clients_map: dict[int, Client] = {}
    contracts_by_client: dict[int, list[Contract]] = {}
    usage_map: dict[int, int] = {}
    if client_ids:
        clients_map = {
            c.id: c for c in session.exec(select(Client).where(Client.id.in_(client_ids))).all()
        }
        open_contracts = session.exec(
            select(Contract).where(
                Contract.id_cliente.in_(client_ids),
                Contract.trainer_id == trainer.id,
                Contract.chiuso == False,
                Contract.deleted_at == None,
            )
        ).all()
        for c in open_contracts:
            contracts_by_client.setdefault(c.id_cliente, []).append(c)
        contract_ids = [c.id for c in open_contracts]
        if contract_ids:
            usage_rows = session.exec(
                select(Event.id_contratto, func.count(Event.id))
                .where(
                    Event.id_contratto.in_(contract_ids),
                    Event.categoria == "PT",
                    Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
                    Event.deleted_at == None,
                )
                .group_by(Event.id_contratto)
            ).all()
            usage_map = {row[0]: int(row[1]) for row in usage_rows}

    items = []
    for e in orphans:
        cl = clients_map.get(e.id_cliente) if e.id_cliente else None
        contratti = [
            {
                "id": c.id,
                "tipo_pacchetto": c.tipo_pacchetto,
                "crediti_residui": (c.crediti_totali or 0) - usage_map.get(c.id, 0),
            }
            for c in contracts_by_client.get(e.id_cliente, [])
        ]
        items.append({
            "id": e.id,
            "data_inizio": e.data_inizio.isoformat() if isinstance(e.data_inizio, datetime) else str(e.data_inizio),
            "data_fine": e.data_fine.isoformat() if isinstance(e.data_fine, datetime) else str(e.data_fine),
            "titolo": e.titolo,
            "stato": e.stato,
            "id_cliente": e.id_cliente,
            "cliente_nome": cl.nome if cl else None,
            "cliente_cognome": cl.cognome if cl else None,
            "contratti_aperti": contratti,
        })

    return {"items": items, "total": len(items)}


@router.get("/overdue-rates")
def get_overdue_rates(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Rate scadute: rate PENDENTI/PARZIALI con data_scadenza < oggi.

    Restituisce dati completi per risoluzione inline dalla Dashboard
    (Sheet con pagamento rapido). Include dati cliente e contratto.

    Ordinamento: piu' vecchie prima (urgenza decrescente).
    """
    today = date.today()

    stmt = (
        select(Rate, Contract, Client)
        .join(Contract, Rate.id_contratto == Contract.id)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.data_scadenza < today,
            Rate.deleted_at == None,
            Contract.deleted_at == None,
            Contract.chiuso == False,
        )
        .order_by(Rate.data_scadenza.asc())
    )
    rows = session.exec(stmt).all()

    items = []
    for rate, contract, client in rows:
        residuo = round(rate.importo_previsto - rate.importo_saldato, 2)
        giorni = (today - rate.data_scadenza).days if isinstance(rate.data_scadenza, date) else 0
        items.append({
            "rate_id": rate.id,
            "data_scadenza": rate.data_scadenza.isoformat() if isinstance(rate.data_scadenza, date) else str(rate.data_scadenza),
            "importo_previsto": rate.importo_previsto,
            "importo_saldato": rate.importo_saldato,
            "importo_residuo": residuo,
            "giorni_ritardo": giorni,
            "stato": rate.stato,
            "contract_id": contract.id,
            "tipo_pacchetto": contract.tipo_pacchetto,
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
            "client_telefono": client.telefono,
        })

    return {"items": items, "total": len(items)}


@router.get("/expiring-contracts")
def get_expiring_contracts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Contratti in scadenza con crediti inutilizzati (30 giorni).

    Restituisce dati completi per risoluzione inline dalla Dashboard
    (Sheet con progress bar crediti e countdown). Include credit engine
    computed-on-read: crediti_usati + breakdown (completate/penali) da
    `_occupazione_breakdown_map` (SSoT STATI_OCCUPAZIONE_CREDITO, G9.7.3/D5).

    Ordinamento: scadenza piu' vicina prima.
    """
    today = date.today()
    deadline_30 = today + timedelta(days=30)

    # Contratti-padre già rinnovati (hanno un figlio non eliminato) → esclusi dai solleciti
    # di scadenza: il rinnovo è già stato fatto (SPEC_RINNOVI_SCADUTI §A.2, correzione).
    renewed_parent_ids = {
        row[0] for row in session.execute(text(
            "SELECT DISTINCT rinnovo_di FROM contratti "
            "WHERE trainer_id = :tid AND rinnovo_di IS NOT NULL AND deleted_at IS NULL"
        ), {"tid": trainer.id}).fetchall()
    }

    # Step 1: contratti in finestra scadenza con crediti
    contracts = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            Contract.data_scadenza != None,
            Contract.data_scadenza <= deadline_30,
            Contract.data_scadenza >= today,
            Contract.crediti_totali != None,
        )
        .order_by(Contract.data_scadenza.asc())
    ).all()

    if not contracts:
        return {"items": [], "total": 0}

    # Step 2: batch fetch breakdown occupazione (anti-N+1, un solo interprete — G9.7.3/D5)
    contract_ids = [c.id for c, _ in contracts]
    breakdown_map = _occupazione_breakdown_map(session, contract_ids)

    items = []
    for contract, client in contracts:
        # Già rinnovato (esiste figlio) → non sollecitare il rinnovo
        if contract.id in renewed_parent_ids:
            continue

        b = breakdown_map.get(contract.id, {"usati": 0, "completate": 0, "penali": 0})
        usati = b["usati"]
        totali = contract.crediti_totali or 0
        residui = max(totali - usati, 0)

        # Solo contratti con crediti residui
        if residui <= 0:
            continue

        scadenza = contract.data_scadenza
        if isinstance(scadenza, str):
            scadenza = date.fromisoformat(scadenza)
        giorni_rimasti = (scadenza - today).days if isinstance(scadenza, date) else 0

        # data_inizio del padre: serve al rinnovo per derivare la durata (SPEC_RINNOVO §A.2)
        inizio = contract.data_inizio
        if isinstance(inizio, str):
            inizio = date.fromisoformat(inizio)

        items.append({
            "contract_id": contract.id,
            "tipo_pacchetto": contract.tipo_pacchetto,
            "data_inizio": inizio.isoformat() if isinstance(inizio, date) else None,
            "data_scadenza": scadenza.isoformat() if isinstance(scadenza, date) else str(scadenza),
            "giorni_rimasti": giorni_rimasti,
            "crediti_totali": totali,
            "crediti_usati": usati,
            "crediti_residui": residui,
            # G9.7.3/D5 (D-DERIVATO-MAI-NUDO): il conteggio si spiega dalla stessa vista
            "sedute_completate": b["completate"],
            "sedute_penali": b["penali"],
            "prezzo_totale": contract.prezzo_totale,
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
            "client_telefono": client.telefono,
        })

    return {"items": items, "total": len(items)}


def _contracts_to_plan_candidates(session: Session, trainer_id: int, today: date):
    """
    Candidati "contratti da pianificare" (SPEC_RINNOVO §B + G1 del FINANCIAL_DOMAIN_MODEL).

    Un contratto è pianificabile (= si può creare una rata) SOLO se ATTIVO con residuo
    positivo e ZERO rate. G1: un contratto **scaduto** (SOSPESO/ESAURITO) con residuo e zero
    rate NON va qui — non lo puoi rateizzare, va incassato direttamente (G6, "da incassare
    scaduto"). La decisione passa da `contract_state.is_rate_planificabile` → mai inline.

    Usato da endpoint (items) e alert (count) → conteggio coerente.
    Ritorna: list[(Contract, Client)] ordinati per scadenza più vicina.
    """
    # Step 1: contratti aperti con residuo positivo (prezzo > versato)
    # G9.0c/QW2 (nota, SPEC_G9 §A.5): questo è un pre-filtro LORDO DELIBERATO (Sezione A) — over-seleziona,
    # la decisione finale la prende il SSoT `is_rate_planificabile` a valle (mai inline). Rischio noto:
    # UNDER-selezione di un riaperto-con-rimborso (`totale_rimborsato>0`, `prezzo≤versato` lordo ma
    # `residuo()` net-aware>0), escluso qui e mai valutato dal SSoT. NON si tocca finché la telemetria del
    # sensore (G9.0a) non conferma il caso reale; fix minimale eventuale = `OR totale_rimborsato>0` (può solo
    # AGGIUNGERE candidati al SSoT, mai escludere), non un rewrite net-aware (contraddirebbe la Sezione A).
    rows = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            func.coalesce(Contract.prezzo_totale, 0) > func.coalesce(Contract.totale_versato, 0),
        )
        .order_by(Contract.data_scadenza.asc())
    ).all()
    if not rows:
        return []

    # Step 2: escludi i contratti con almeno una rata non eliminata (zero rate, §B.3)
    candidate_ids = [c.id for c, _ in rows]
    with_rates = set(
        session.exec(
            select(Rate.id_contratto)
            .where(Rate.id_contratto.in_(candidate_ids), Rate.deleted_at == None)
            .distinct()
        ).all()
    )

    # Step 3 (G1): tieni solo gli ATTIVO. Zero-rate + residuo>0 ⟹ money=DA_PIANIFICARE,
    # quindi is_rate_planificabile equivale a lifecycle==ATTIVO (crediti_usati irrilevante:
    # uno scaduto non è mai ATTIVO). crediti_usati=0 è sufficiente per questa decisione.
    out = []
    for contract, client in rows:
        if contract.id in with_rates:
            continue
        # rates=[] è LECITO solo perché lo Step 2 ha già escluso i contratti con rate:
        # qui money_substate non può che essere DA_PIANIFICARE. Se un domani si togliesse
        # il filtro with_rates, passare le rate vere a evaluate_contract — altrimenti
        # money_substate mentirebbe. I due step sono accoppiati di proposito.
        st = cstate.evaluate_contract(contract, 0, [], today)
        if cstate.is_rate_planificabile(st):
            out.append((contract, client))
    return out


@router.get("/contracts-to-plan")
def get_contracts_to_plan(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Contratti da pianificare: ATTIVI, con residuo positivo e ZERO rate (SPEC_RINNOVO §B, G1).

    Contract-first (non Rate-first): l'aging report itera sulle rate ed e'
    strutturalmente cieco a questi contratti. Qui si parte dal contratto.

    Dati completi per risoluzione inline dalla Dashboard (Sheet → "Definisci piano").
    Ordinamento: scadenza piu' vicina prima (urgenza decrescente).
    """
    today = date.today()
    items = []
    for contract, client in _contracts_to_plan_candidates(session, trainer.id, today):
        residuo = cstate.residuo(contract)  # SSoT (SPEC_REVISIONE_PRE_G7 §A): no ricalcolo inline
        scad = contract.data_scadenza
        items.append({
            "contract_id": contract.id,
            "tipo_pacchetto": contract.tipo_pacchetto,
            "data_scadenza": scad.isoformat() if isinstance(scad, date) else (str(scad) if scad else None),
            "prezzo_totale": contract.prezzo_totale,
            "totale_versato": contract.totale_versato,
            "importo_residuo": residuo,
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
            "client_telefono": client.telefono,
        })

    return {"items": items, "total": len(items)}


def _coerce_date(d):
    return date.fromisoformat(d) if isinstance(d, str) else d


def _occupazione_breakdown_map(
    session: Session, contract_ids: list[int]
) -> dict[int, dict[str, int]]:
    """Breakdown occupazione per contratto — UNA query group-by (id_contratto, stato),
    derivazione dal SSoT (G9.7.3/D5, stesso interprete della lista contratti): usati,
    completate e penali nascono dalle stesse righe, mai due query divergibili. Anti-N+1.

    Ritorna: {id_contratto: {"usati": n, "completate": n, "penali": n}}.
    """
    if not contract_ids:
        return {}
    rows = session.exec(
        select(Event.id_contratto, Event.stato, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto, Event.stato)
    ).all()
    out: dict[int, dict[str, int]] = {}
    for cid, stato_ev, n in rows:
        b = out.setdefault(cid, {"usati": 0, "completate": 0, "penali": 0})
        n = int(n)
        if stato_ev in cstate.STATI_OCCUPAZIONE_CREDITO:  # G7.8: Rinviato libera (ADR-017)
            b["usati"] += n
        if stato_ev == "Completato":
            b["completate"] += n
        if stato_ev in cstate.STATI_PENALE:
            b["penali"] += n
    return out


def _crediti_usati_map(session: Session, contract_ids: list[int]) -> dict[int, int]:
    """Batch crediti usati (eventi PT in occupazione) per i contratti dati.
    Delega al breakdown (un solo interprete dell'asse occupazione)."""
    return {
        cid: b["usati"]
        for cid, b in _occupazione_breakdown_map(session, contract_ids).items()
    }


def _contract_recency_key(c) -> date:
    """Recency assoluta: scadenza → inizio → vendita → date.min (per max())."""
    return (
        _coerce_date(c.data_scadenza)
        or _coerce_date(c.data_inizio)
        or _coerce_date(c.data_vendita)
        or date.min
    )


def _lapsed_client_candidates(session: Session, trainer_id: int, today: date):
    """
    Candidati "cliente da recuperare" (lapsed) — CLIENT-AWARE, derivato dal SSoT.

    Un cliente è lapsed se NON è ingaggiato (`cstate.is_engaged` = zero contratti
    ATTIVO **o SOSPESO**) e ha ≥1 contratto. Il SOSPESO conta come ingaggio: un cliente
    con sedute prepagate residue su un contratto scaduto va in "contratti sospesi", NON
    in win-back (fix difetto SOSPESO — FINANCIAL_DOMAIN_MODEL §4.1; regola d'oro §10:
    lo stato di vita si deriva da `contract_state`, mai inline `data_scadenza >= today`).

    Rappresentante = contratto più recente IN ASSOLUTO, inclusi CHIUSO/ESAURITO (§6):
    è l'ancora del win-back (caso Dalila c29 vs c25). Escluso se quel rappresentante è
    marcato "non rinnova" (esito_rinnovo_motivo valorizzato).
    Usato da endpoint (items) e alert (count) → conteggi coerenti.

    Ritorna: list[(Client, rappresentante: Contract, rep_crediti_usati: int)].
    """
    rows = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,  # include i CHIUSO → rappresentante §6
        )
    ).all()
    if not rows:
        return []

    # crediti_usati serve a distinguere SOSPESO (crediti residui) da ESAURITO →
    # determina l'ingaggio: senza, un SOSPESO sembrerebbe terminale (= il bug).
    credits_map = _crediti_usati_map(session, [c.id for c, _ in rows])

    by_client: dict[int, dict] = {}
    for contract, client in rows:
        by_client.setdefault(client.id, {"client": client, "contracts": []})["contracts"].append(contract)

    candidates = []
    for entry in by_client.values():
        contracts = entry["contracts"]
        lifecycles = [
            cstate.contract_lifecycle(c, credits_map.get(c.id, 0), today) for c in contracts
        ]
        if cstate.is_engaged(lifecycles):
            continue  # ATTIVO o SOSPESO → ingaggiato (non è win-back)
        representative = max(contracts, key=_contract_recency_key)
        if representative.esito_rinnovo_motivo is not None:
            continue
        candidates.append((entry["client"], representative, credits_map.get(representative.id, 0)))
    return candidates


def _suspended_contracts_candidates(session: Session, trainer_id: int, today: date):
    """
    Candidati "contratti sospesi" (stato SOSPESO) — unità = CONTRATTO (FINANCIAL_DOMAIN_MODEL §6).

    SOSPESO = aperto + scaduto + crediti_residui > 0 (sedute prepagate ancora da erogare: gliele DEVI).
    Pre-filtro SQL grossolano (aperti + scaduti); la classificazione fine è del SSoT
    `contract_state` (esclude gli ESAURITO, crediti_residui == 0 — regola d'oro §10).
    Usato da endpoint (items) e alert (count) → conteggio coerente.

    Ordine: aging **INVERTITO** (più vecchio = più urgente). Il SOSPESO non decade: è
    un'obbligazione, l'urgenza cresce nel tempo (§4.1, decadimento asimmetrico).

    Ritorna: list[(Contract, Client, breakdown: dict)] — breakdown = usati/completate/penali
    dal SSoT (G9.7.3/D5), la classificazione usa breakdown["usati"].
    """
    rows = session.exec(
        select(Contract, Client)
        .join(Client, Contract.id_cliente == Client.id)
        .where(
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
            Contract.chiuso == False,
            Contract.data_scadenza < today,  # scaduto (NULL escluso dal confronto)
        )
    ).all()
    if not rows:
        return []

    breakdown_map = _occupazione_breakdown_map(session, [c.id for c, _ in rows])

    out = []
    for contract, client in rows:
        b = breakdown_map.get(contract.id, {"usati": 0, "completate": 0, "penali": 0})
        if cstate.contract_lifecycle(contract, b["usati"], today) == cstate.Lifecycle.SOSPESO:
            out.append((contract, client, b))
    out.sort(key=lambda t: (today - _coerce_date(t[0].data_scadenza)).days, reverse=True)
    return out


@router.get("/clients-to-recover")
def get_clients_to_recover(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Clienti da recuperare (lapsed) — CLIENT-AWARE, derivato dal SSoT.

    Un cliente compare se NON è ingaggiato (zero contratti ATTIVO **o SOSPESO** —
    `cstate.is_engaged`) e ha ≥1 contratto. Il SOSPESO (scaduto con sedute prepagate
    residue) conta come ingaggio → quel cliente sta in "contratti sospesi", non qui
    (fix difetto SOSPESO). "Non ingaggiato" sussume rinnovo-figlio e nuovo-contratto-
    non-collegato → zero falsi positivi.

    Unità = CLIENTE (1 riga), rappresentato dal contratto più recente IN ASSOLUTO
    (incl. CHIUSO/ESAURITO, §6). Escluso se quel rappresentante è "non rinnova".
    Opportunità residua = info + priorità, mai filtro (invariante: nessun cliente perso
    in silenzio). Read-only. Ordinato per ritardo decrescente.
    """
    today = date.today()
    candidates = _lapsed_client_candidates(session, trainer.id, today)
    if not candidates:
        return {"items": [], "total": 0}

    items = []
    for client, rep, rep_crediti_usati in candidates:
        scad = _coerce_date(rep.data_scadenza)
        inizio = _coerce_date(rep.data_inizio)
        # max(0): il rappresentante è il contratto più recente IN ASSOLUTO e può essere CHIUSO con
        # scadenza FUTURA (caso 3 contratti muti) → niente "Scaduto da -N giorni".
        giorni_ritardo = max(0, (today - scad).days) if isinstance(scad, date) else 0
        items.append({
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
            "client_telefono": client.telefono,
            "contract_id": rep.id,
            "tipo_pacchetto": rep.tipo_pacchetto,
            "prezzo_totale": rep.prezzo_totale,
            "data_inizio": inizio.isoformat() if isinstance(inizio, date) else None,
            "data_scadenza": scad.isoformat() if isinstance(scad, date) else None,
            "giorni_ritardo": giorni_ritardo,
            "residuo": cstate.residuo(rep),
            "crediti_totali": rep.crediti_totali or 0,
            "crediti_residui": cstate.crediti_residui(rep, rep_crediti_usati),
        })

    items.sort(key=lambda x: x["giorni_ritardo"], reverse=True)
    return {"items": items, "total": len(items)}


@router.get("/suspended-contracts")
def get_suspended_contracts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Contratti sospesi (stato SOSPESO) — FINANCIAL_DOMAIN_MODEL §6.

    Contratto aperto, scaduto, con **sedute prepagate residue** (crediti_residui > 0): il trainer
    le DEVE al cliente. Unità = CONTRATTO. Derivato da `contract_state` (mai inline).
    Doppio debito esplicito (assi ortogonali §2): `crediti_residui` (sedute da recuperare) e
    `residuo` (denaro eventualmente ancora da incassare) sono debiti DISTINTI, non un doppione.

    Azione disponibile ORA: **estendi** (PUT /contracts/{id} su data_scadenza → torna ATTIVO).
    Chiudi-con-conguaglio / decadi arrivano col blocco terminazione (G7).
    Read-only, multi-tenant. Ordine: ritardo decrescente (aging invertito).
    """
    today = date.today()
    items = []
    for contract, client, breakdown in _suspended_contracts_candidates(session, trainer.id, today):
        scad = _coerce_date(contract.data_scadenza)
        inizio = _coerce_date(contract.data_inizio)
        giorni_ritardo = (today - scad).days if isinstance(scad, date) else 0
        crediti_usati = breakdown["usati"]
        items.append({
            "contract_id": contract.id,
            "tipo_pacchetto": contract.tipo_pacchetto,
            "data_inizio": inizio.isoformat() if isinstance(inizio, date) else None,
            "data_scadenza": scad.isoformat() if isinstance(scad, date) else None,
            "giorni_ritardo": giorni_ritardo,
            "prezzo_totale": contract.prezzo_totale,
            "crediti_totali": contract.crediti_totali or 0,
            "crediti_usati": crediti_usati,
            "crediti_residui": cstate.crediti_residui(contract, crediti_usati),  # sedute da recuperare
            # G9.7.3/D5 (D-DERIVATO-MAI-NUDO): le "sedute da recuperare" si spiegano dalla vista
            "sedute_completate": breakdown["completate"],
            "sedute_penali": breakdown["penali"],
            "residuo": cstate.residuo(contract),  # denaro eventualmente ancora dovuto (asse distinto)
            "client_id": client.id,
            "client_nome": client.nome,
            "client_cognome": client.cognome,
            "client_telefono": client.telefono,
        })

    return {"items": items, "total": len(items)}


@router.get("/crediti-da-incassare")
def get_crediti_da_incassare(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Worklist "Crediti da incassare (post-chiusura)" (G7.10, ADR-018) — gemella di G6 "incassa residuo".

    Elenca i receivable `crediti_terminazione` ANCORA APERTI: il credito a favore del trainer creato da
    una terminazione `A_CREDITO` ("chiudo oggi, il cliente paga dopo"). Vive FUORI da `residuo()`: non è
    un debito sul contratto (che resta CHIUSO, residuo 0), è un credito da incassare a sé.
    Read-only, multi-tenant. Ordine: aging INVERTITO (più vecchio = più urgente).
    """
    today = date.today()
    rows = session.exec(
        select(CreditoTerminazione, Client)
        .join(Client, CreditoTerminazione.id_cliente == Client.id)
        .where(
            CreditoTerminazione.trainer_id == trainer.id,
            CreditoTerminazione.stato == cstate.STATO_CREDITO_APERTO,
            CreditoTerminazione.deleted_at == None,
        )
    ).all()
    items = []
    for credito, client in rows:
        creato = _coerce_date(credito.data_creazione)
        residuo = round(max((credito.importo or 0) - (credito.importo_incassato or 0), 0.0), 2)
        items.append({
            "id": credito.id,
            "id_contratto": credito.id_contratto,
            "id_cliente": credito.id_cliente,
            "cliente_nome": client.nome,
            "cliente_cognome": client.cognome,
            "client_telefono": client.telefono,
            "importo": credito.importo,
            "importo_incassato": credito.importo_incassato or 0,
            "residuo": residuo,
            "data_creazione": creato.isoformat() if isinstance(creato, date) else None,
            "giorni_aperto": (today - creato).days if isinstance(creato, date) else 0,
        })
    items.sort(key=lambda x: x["giorni_aperto"], reverse=True)
    return {"items": items, "total": len(items)}


@router.get("/rimborsi-da-erogare")
def get_rimborsi_da_erogare(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Worklist "Rimborsi da erogare" (G8.1, ADR-020) — gemella di crediti-da-incassare, in USCITA.

    Elenca i wallet `crediti_cliente` ANCORA APERTI: credito a favore del CLIENTE (rimborso differito da
    una terminazione, o overpayment) da erogare in cassa. Vive FUORI da `residuo()`: non è un debito del
    cliente, è denaro che il trainer deve restituire. Read-only, multi-tenant. Aging INVERTITO.
    """
    today = date.today()
    rows = session.exec(
        select(CreditoCliente, Client)
        .join(Client, CreditoCliente.id_cliente == Client.id)
        .where(
            CreditoCliente.trainer_id == trainer.id,
            CreditoCliente.stato == cstate.STATO_CREDITO_APERTO,
            CreditoCliente.deleted_at == None,
        )
    ).all()
    items = []
    for credito, client in rows:
        creato = _coerce_date(credito.data_creazione)
        residuo = round(max((credito.importo or 0) - (credito.importo_erogato or 0), 0.0), 2)
        items.append({
            "id": credito.id,
            "id_contratto_origine": credito.id_contratto_origine,
            "id_cliente": credito.id_cliente,
            "cliente_nome": client.nome,
            "cliente_cognome": client.cognome,
            "client_telefono": client.telefono,
            "importo": credito.importo,
            "importo_erogato": credito.importo_erogato or 0,
            "residuo": residuo,
            "causale": credito.causale,
            "data_creazione": creato.isoformat() if isinstance(creato, date) else None,
            "giorni_aperto": (today - creato).days if isinstance(creato, date) else 0,
        })
    items.sort(key=lambda x: x["giorni_aperto"], reverse=True)
    return {"items": items, "total": len(items)}


@router.get("/birthday-clients")
def get_birthday_clients(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Clienti con compleanno oggi o nei prossimi 7 giorni.

    Restituisce dati per auguri WhatsApp: nome, telefono, data nascita,
    giorni mancanti, eta' che compie.
    Ordinamento: compleanno piu' vicino prima.
    """
    today = date.today()

    rows = session.execute(text("""
        SELECT cl.id, cl.nome, cl.cognome, cl.data_nascita, cl.telefono, cl.email
        FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND cl.data_nascita IS NOT NULL
    """), {"tid": trainer.id}).fetchall()

    items = []
    for cid, nome, cognome, dn_raw, telefono, email in rows:
        try:
            dn = date.fromisoformat(dn_raw) if isinstance(dn_raw, str) else dn_raw
            this_year_bday = dn.replace(year=today.year)
            if this_year_bday < today:
                this_year_bday = dn.replace(year=today.year + 1)
            days_until = (this_year_bday - today).days
            if days_until > 7:
                continue
            eta = this_year_bday.year - dn.year
            items.append({
                "client_id": cid,
                "nome": nome,
                "cognome": cognome,
                "telefono": telefono,
                "email": email,
                "data_nascita": dn.isoformat(),
                "giorni_mancanti": days_until,
                "eta_compie": eta,
            })
        except (ValueError, TypeError):
            continue

    items.sort(key=lambda x: x["giorni_mancanti"])
    return {"items": items, "total": len(items)}


@router.get("/inactive-clients")
def get_inactive_clients(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Clienti inattivi: attivi senza eventi negli ultimi 14 giorni.

    Restituisce dati completi per risoluzione inline dalla Dashboard
    (Sheet con info contatto e ultimo evento). Include telefono, email,
    data/categoria ultimo evento.

    Ordinamento: piu' a lungo inattivi prima.
    """
    today = date.today()
    cutoff_14 = today - timedelta(days=14)
    cutoff_start = datetime.combine(cutoff_14, datetime.min.time())

    # Step 1: clienti attivi senza eventi recenti
    inactive_clients = session.execute(text("""
        SELECT cl.id, cl.nome, cl.cognome, cl.telefono, cl.email
        FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM agenda e
              WHERE e.id_cliente = cl.id
                AND e.data_inizio >= :cutoff
                AND e.stato != 'Cancellato'
                AND e.deleted_at IS NULL
          )
        ORDER BY cl.nome, cl.cognome
    """), {"tid": trainer.id, "cutoff": cutoff_start.isoformat()}).fetchall()

    if not inactive_clients:
        return {"items": [], "total": 0}

    # Step 2: batch fetch ultimo evento per ciascuno (anti-N+1)
    client_ids = [row[0] for row in inactive_clients]
    last_events = session.execute(
        text("""
        SELECT e.id_cliente, e.data_inizio, e.categoria
        FROM agenda e
        INNER JOIN (
            SELECT id_cliente, MAX(data_inizio) as max_data
            FROM agenda
            WHERE id_cliente IN :client_ids
              AND stato != 'Cancellato'
              AND deleted_at IS NULL
            GROUP BY id_cliente
        ) latest ON e.id_cliente = latest.id_cliente AND e.data_inizio = latest.max_data
        WHERE e.deleted_at IS NULL AND e.stato != 'Cancellato'
    """).bindparams(bindparam("client_ids", expanding=True)),
        {"client_ids": client_ids},
    ).fetchall()

    last_event_map: dict[int, tuple] = {}
    for row in last_events:
        last_event_map[row[0]] = (row[1], row[2])

    items = []
    for cid, nome, cognome, telefono, email in inactive_clients:
        last = last_event_map.get(cid)
        last_data = None
        last_cat = None
        giorni_inattivo = 14  # minimo

        if last:
            last_data_raw = last[0]
            last_cat = last[1]
            # Parse datetime string
            if isinstance(last_data_raw, str):
                try:
                    last_dt = datetime.fromisoformat(last_data_raw.replace(" ", "T"))
                    last_data = last_dt.date().isoformat()
                    giorni_inattivo = (today - last_dt.date()).days
                except ValueError:
                    last_data = last_data_raw
            elif isinstance(last_data_raw, datetime):
                last_data = last_data_raw.date().isoformat()
                giorni_inattivo = (today - last_data_raw.date()).days
            elif isinstance(last_data_raw, date):
                last_data = last_data_raw.isoformat()
                giorni_inattivo = (today - last_data_raw).days

        items.append({
            "client_id": cid,
            "nome": nome,
            "cognome": cognome,
            "telefono": telefono,
            "email": email,
            "giorni_inattivo": giorni_inattivo,
            "ultimo_evento_data": last_data,
            "ultimo_evento_categoria": last_cat,
        })

    # Ordinamento: piu' inattivi prima
    items.sort(key=lambda x: -x["giorni_inattivo"])

    return {"items": items, "total": len(items)}


@router.get("/alerts", response_model=DashboardAlerts)
def get_dashboard_alerts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Warning proattivi — "Cosa richiede la mia attenzione ORA?"

    Categorie di alert (query SQL aggregate, zero N+1):
    1. ghost_events: eventi passati ancora 'Programmato'
    2. orphan_contracts: contratti attivi con prezzo > 0 e zero rate
    3. expiring_contracts: contratti in scadenza (30gg) con crediti residui
    4. overdue_rates: rate scadute (data_scadenza < oggi)
    5. inactive_clients: clienti attivi senza eventi da >14 giorni
    6. stale_schede / stale_measurements: dati clinici non aggiornati (>35gg)
    7. birthdays: compleanni oggi + prossimi 7 giorni
    """
    today = date.today()
    items: list[AlertItem] = []

    # ── 1. Eventi fantasma: ieri o prima, ancora "Programmato" ──
    yesterday_end = datetime.combine(today, datetime.min.time())
    ghost_count = session.exec(
        select(func.count(Event.id)).where(
            Event.trainer_id == trainer.id,
            Event.data_fine < yesterday_end,
            Event.stato == "Programmato",
            Event.deleted_at == None,
        )
    ).one()

    if ghost_count > 0:
        items.append(AlertItem(
            severity="critical",
            category="ghost_events",
            title=f"{ghost_count} {'evento' if ghost_count == 1 else 'eventi'} senza esito",
            detail="Aggiorna lo stato: completate o cancellate?",
            count=ghost_count,
            link="/agenda",
        ))

    # ── 1-bis. Sedute PT senza contratto (orfani in stati di occupazione) — G9.7.2/B6 ──
    # Stesso helper della worklist /dashboard/orphan-events → count == len(items).
    # Mai limbo invisibile (ADR-024 D-RECUPERO-ESPLICITO): il CTA apre lo sheet con «Assegna» inline.
    orphan_events_count = len(_orphan_pt_candidates(session, trainer.id))
    if orphan_events_count > 0:
        items.append(AlertItem(
            severity="warning",
            category="orphan_events",
            title=f"{orphan_events_count} {'seduta senza contratto' if orphan_events_count == 1 else 'sedute senza contratto'}",
            detail="Non scalano crediti: assegnale a un contratto del cliente",
            count=orphan_events_count,
            link=None,
        ))

    # ── 2. Contratti da pianificare (ATTIVI, residuo positivo, zero rate) ──
    # SPEC_RINNOVO §B.3 + G1: stesso helper della worklist → count == len(items).
    # G1: gli scaduti con residuo+zero rate NON sono pianificabili (vanno incassati,
    # non rateizzati) → esclusi qui dalla derivazione `contract_state`.
    orphan_count = len(_contracts_to_plan_candidates(session, trainer.id, today))

    if orphan_count > 0:
        items.append(AlertItem(
            severity="warning",
            category="orphan_contracts",
            title=f"{orphan_count} {'contratto senza piano' if orphan_count == 1 else 'contratti senza piano'}",
            detail="Genera il piano rate per iniziare a incassare",
            count=orphan_count,
            link="/contratti",
        ))

    # ── 2-bis. Clienti da recuperare (lapsed: scaduto + zero attivi) — conta CLIENTI ──
    # Stesso helper della worklist /rinnovi-incassi → conteggio coerente (incl. esclusione "non rinnova").
    recover_count = len(_lapsed_client_candidates(session, trainer.id, today))
    if recover_count > 0:
        items.append(AlertItem(
            severity="warning",
            category="clients_to_recover",
            title=f"{recover_count} {'cliente da recuperare' if recover_count == 1 else 'clienti da recuperare'}",
            detail="Contratto scaduto e nessuna copertura attiva — riattivali",
            count=recover_count,
            link="/rinnovi-incassi",
        ))

    # ── 2-ter. Contratti sospesi (scaduti con sedute prepagate residue) — conta CONTRATTI ──
    # Stesso helper della worklist → conteggio coerente. Obbligazione, non opportunità: gli devi le sedute.
    suspended_count = len(_suspended_contracts_candidates(session, trainer.id, today))
    if suspended_count > 0:
        items.append(AlertItem(
            severity="warning",
            category="suspended_contracts",
            title=f"{suspended_count} {'contratto sospeso' if suspended_count == 1 else 'contratti sospesi'}",
            detail="Scaduti con sedute prepagate da erogare — estendi o regola",
            count=suspended_count,
            link="/rinnovi-incassi",
        ))

    # ── 3. Contratti in scadenza con crediti inutilizzati ──
    deadline_30 = today + timedelta(days=30)

    # Wrapped subquery: SQLite non accetta HAVING senza GROUP BY.
    # Calcoliamo crediti_usati come subquery scalare, poi filtriamo nel WHERE esterno.
    expiring_rows = session.execute(text("""
        SELECT * FROM (
            SELECT c.id, cl.nome, cl.cognome, c.tipo_pacchetto,
                   c.data_scadenza, c.crediti_totali,
                   COALESCE(
                       (SELECT COUNT(*) FROM agenda e
                        WHERE e.id_contratto = c.id
                          AND e.categoria = 'PT'
                          -- G7.8: Rinviato libera il credito (ADR-017)
                          AND e.stato IN :stati_occupazione
                          AND e.deleted_at IS NULL), 0
                   ) as crediti_usati
            FROM contratti c
            JOIN clienti cl ON cl.id = c.id_cliente
            WHERE c.trainer_id = :tid
              AND c.deleted_at IS NULL
              AND c.chiuso = 0
              AND c.data_scadenza IS NOT NULL
              AND c.data_scadenza <= :deadline
              AND c.data_scadenza >= :today
              AND c.crediti_totali IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM contratti ch
                  WHERE ch.rinnovo_di = c.id AND ch.deleted_at IS NULL
              )
        ) sub
        WHERE sub.crediti_usati < sub.crediti_totali
    """).bindparams(bindparam("stati_occupazione", expanding=True)),
        {"tid": trainer.id, "deadline": deadline_30.isoformat(), "today": today.isoformat(),
         "stati_occupazione": tuple(sorted(cstate.STATI_OCCUPAZIONE_CREDITO))}).fetchall()

    if expiring_rows:
        for row in expiring_rows:
            cid, nome, cognome, pacchetto, scadenza_raw, totali, usati = row
            residui = totali - usati
            # Raw SQL restituisce date come stringa ISO — parse esplicito
            scadenza = date.fromisoformat(scadenza_raw) if isinstance(scadenza_raw, str) else scadenza_raw
            days_left = (scadenza - today).days if isinstance(scadenza, date) else 0
            # Grammatica condizionale: singolare/plurale
            crediti_label = "credito inutilizzato" if residui == 1 else "crediti inutilizzati"
            if days_left == 0:
                scadenza_label = f"{pacchetto or 'Contratto'} scade oggi"
            elif days_left == 1:
                scadenza_label = f"{pacchetto or 'Contratto'} scade domani"
            else:
                scadenza_label = f"{pacchetto or 'Contratto'} scade tra {days_left} giorni"
            items.append(AlertItem(
                severity="warning" if days_left > 7 else "critical",
                category="expiring_contracts",
                title=f"{nome} {cognome} — {residui} {crediti_label}",
                detail=scadenza_label,
                count=1,
                link="/contratti",
            ))

    # ── 3. Rate scadute (non solo "in scadenza", ma GIA' scadute) ──
    overdue_data = session.execute(text("""
        SELECT COUNT(*) as cnt,
               COALESCE(SUM(r.importo_previsto - r.importo_saldato), 0) as tot
        FROM rate_programmate r
        JOIN contratti c ON r.id_contratto = c.id
        WHERE c.trainer_id = :tid
          AND r.stato IN ('PENDENTE', 'PARZIALE')
          AND r.data_scadenza < :today
          AND r.deleted_at IS NULL
          AND c.deleted_at IS NULL
          AND c.chiuso = 0
    """), {"tid": trainer.id, "today": today.isoformat()}).fetchone()

    overdue_count = overdue_data[0] if overdue_data else 0
    overdue_amount = overdue_data[1] if overdue_data else 0

    if overdue_count > 0:
        items.append(AlertItem(
            severity="critical",
            category="overdue_rates",
            title=f"{overdue_count} {'rata scaduta' if overdue_count == 1 else 'rate scadute'}",
            detail=f"€{overdue_amount:,.2f} da riscuotere — registra i pagamenti".replace(",", "."),
            count=overdue_count,
            link="/cassa",
        ))

    # ── 4. Clienti inattivi: attivi senza eventi negli ultimi 14 giorni ──
    cutoff_14 = today - timedelta(days=14)
    cutoff_start = datetime.combine(cutoff_14, datetime.min.time())

    inactive_count = session.execute(text("""
        SELECT COUNT(*) FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM agenda e
              WHERE e.id_cliente = cl.id
                AND e.data_inizio >= :cutoff
                AND e.stato != 'Cancellato'
                AND e.deleted_at IS NULL
          )
    """), {"tid": trainer.id, "cutoff": cutoff_start.isoformat()}).scalar() or 0

    if inactive_count > 0:
        items.append(AlertItem(
            severity="warning" if inactive_count <= 2 else "critical",
            category="inactive_clients",
            title=f"{inactive_count} {'cliente inattivo' if inactive_count == 1 else 'clienti inattivi'}",
            detail="Nessuna sessione da 14+ giorni — pianifica un contatto",
            count=inactive_count,
            link="/clienti",
        ))

    # ── 5. Azioni cliniche: schede vecchie (>35gg) e misurazioni scadute (>35gg) ──
    scheda_cutoff = (today - timedelta(days=35)).isoformat()
    misura_cutoff = (today - timedelta(days=35)).isoformat()

    # Clienti attivi con scheda piu' recente creata/aggiornata >35gg fa
    stale_schede_count = session.execute(text("""
        SELECT COUNT(DISTINCT cl.id) FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND EXISTS (
              SELECT 1 FROM schede_allenamento sa
              WHERE sa.id_cliente = cl.id
                AND sa.deleted_at IS NULL
          )
          AND NOT EXISTS (
              SELECT 1 FROM schede_allenamento sa
              WHERE sa.id_cliente = cl.id
                AND sa.deleted_at IS NULL
                AND COALESCE(sa.updated_at, sa.created_at) > :cutoff
          )
    """), {"tid": trainer.id, "cutoff": scheda_cutoff}).scalar() or 0

    # Clienti attivi con ultima misurazione >35gg fa
    stale_misure_count = session.execute(text("""
        SELECT COUNT(DISTINCT cl.id) FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND EXISTS (
              SELECT 1 FROM misurazioni_cliente m
              WHERE m.id_cliente = cl.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM misurazioni_cliente m
              WHERE m.id_cliente = cl.id
                AND m.data_misurazione > :cutoff
          )
    """), {"tid": trainer.id, "cutoff": misura_cutoff}).scalar() or 0

    if stale_schede_count > 0:
        items.append(AlertItem(
            severity="warning",
            category="stale_schede",
            title=f"{stale_schede_count} {'scheda da aggiornare' if stale_schede_count == 1 else 'schede da aggiornare'}",
            detail="Programmi non aggiornati da oltre 5 settimane",
            count=stale_schede_count,
            link="/schede",
        ))

    if stale_misure_count > 0:
        items.append(AlertItem(
            severity="warning",
            category="stale_measurements",
            title=f"{stale_misure_count} {'cliente senza misurazioni recenti' if stale_misure_count == 1 else 'clienti senza misurazioni recenti'}",
            detail="Misurazioni non aggiornate da oltre 5 settimane",
            count=stale_misure_count,
            link="/monitoraggio",
        ))

    # ── 6. Compleanni imminenti (oggi + prossimi 7 giorni) ──
    birthday_clients = session.execute(text("""
        SELECT cl.id, cl.nome, cl.cognome, cl.data_nascita, cl.telefono
        FROM clienti cl
        WHERE cl.trainer_id = :tid
          AND cl.stato = 'Attivo'
          AND cl.deleted_at IS NULL
          AND cl.data_nascita IS NOT NULL
    """), {"tid": trainer.id}).fetchall()

    birthday_today = []
    birthday_upcoming = []
    for cid, nome, cognome, dn_raw, telefono in birthday_clients:
        try:
            dn = date.fromisoformat(dn_raw) if isinstance(dn_raw, str) else dn_raw
            # Confronto mese+giorno (ignora anno)
            this_year_bday = dn.replace(year=today.year)
            # Se gia' passato quest'anno, controlla il prossimo anno
            if this_year_bday < today:
                this_year_bday = dn.replace(year=today.year + 1)
            days_until = (this_year_bday - today).days
            if days_until == 0:
                birthday_today.append((nome, cognome))
            elif days_until <= 7:
                birthday_upcoming.append((nome, cognome, days_until))
        except (ValueError, TypeError):
            continue

    if birthday_today:
        names = ", ".join(f"{n} {c}" for n, c in birthday_today)
        items.append(AlertItem(
            severity="info",
            category="birthdays",
            title=f"Buon compleanno {names}!" if len(birthday_today) == 1 else f"{len(birthday_today)} compleanni oggi!",
            detail="Invia un messaggio di auguri" if len(birthday_today) == 1 else f"Auguri a: {names}",
            count=len(birthday_today),
        ))

    if birthday_upcoming:
        birthday_upcoming.sort(key=lambda x: x[2])
        closest = birthday_upcoming[0]
        items.append(AlertItem(
            severity="info",
            category="birthdays",
            title=f"{len(birthday_upcoming)} {'compleanno' if len(birthday_upcoming) == 1 else 'compleanni'} nei prossimi 7 giorni",
            detail=f"Prossimo: {closest[0]} {closest[1]} tra {closest[2]} {'giorno' if closest[2] == 1 else 'giorni'}",
            count=len(birthday_upcoming),
        ))

    # ── Conteggi severity ──
    critical = sum(1 for i in items if i.severity == "critical")
    warning = sum(1 for i in items if i.severity == "warning")
    info = sum(1 for i in items if i.severity == "info")

    return DashboardAlerts(
        total_alerts=len(items),
        critical_count=critical,
        warning_count=warning,
        info_count=info,
        items=items,
    )


@router.get("/clinical-readiness", response_model=ClinicalReadinessResponse)
def get_clinical_readiness(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Coda operativa per onboarding/migrazione legacy a basso attrito.

    Regola deterministica per cliente attivo:
    1) anamnesi (missing/legacy/structured)
    2) baseline misurazioni presente?
    3) scheda allenamento assegnata?
    """
    summary, items = compute_clinical_readiness_data(
        trainer_id=trainer.id,
        session=session,
        reference_date=date.today(),
    )
    return ClinicalReadinessResponse(summary=summary, items=items)


@router.get("/clinical-readiness/worklist", response_model=ClinicalReadinessWorklistResponse)
def get_clinical_readiness_worklist(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    view: str = Query(default="todo", pattern="^(all|todo|ready)$"),
    sort_by: str = Query(default="priority", pattern="^(priority|due_date)$"),
    priority: str | None = Query(default=None, pattern="^(high|medium|low)$"),
    timeline_status: str | None = Query(default=None, pattern="^(overdue|today|upcoming_7d|upcoming_14d|future|none)$"),
    search: str | None = Query(default=None, max_length=120),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Worklist paginata readiness per MyPortal.

    Mantiene la stessa logica deterministica dell'endpoint legacy ma
    applica filtri server-side e paginazione per scalare oltre 50 clienti.
    """
    summary, items = compute_clinical_readiness_data(
        trainer_id=trainer.id,
        session=session,
        reference_date=date.today(),
    )
    filtered = filter_clinical_readiness_items(
        items,
        view=view,
        priority=priority,
        timeline_status=timeline_status,
        search=search,
    )
    sorted_items = sort_clinical_readiness_items(filtered, sort_by=sort_by)
    total = len(filtered)
    offset = (page - 1) * page_size
    paged_items = sorted_items[offset: offset + page_size]

    return ClinicalReadinessWorklistResponse(
        summary=summary,
        items=paged_items,
        total=total,
        page=page,
        page_size=page_size,
    )
