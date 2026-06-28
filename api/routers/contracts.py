# api/routers/contracts.py
"""
Endpoint Contratti — CRUD con Bouncer Pattern + Relational IDOR.

Sicurezza multi-tenant:
- trainer_id diretto su contratti (aggiunto via migration)
- Relational IDOR: su POST, verifica che id_cliente appartenga al trainer
- trainer_id iniettato dal JWT, mai dal body (Mass Assignment prevention)

Regola 404: se il contratto non esiste O non appartiene al trainer -> 404.
Mai 403, mai rivelare l'esistenza di dati altrui.
"""

import json
from typing import Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, or_, select, func

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.contract import Contract
from api.models.rate import Rate
from api.models.movement import CashMovement
from api.models.event import Event
from api.models.credito_terminazione import CreditoTerminazione
from api.models.credito_cliente import CreditoCliente
from api.models.audit_log import AuditLog
from api.schemas.financial import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractListResponse,
    ContractWithRatesResponse,
    ContractTerminate,
    ContractSettlementPreview,
    ContractMovementItem,
    ContractHistoryEvent,
    ReopenPreview,
    CreditoTerminazioneResponse,
    VALID_AZIONI_CREDITO_TRAINER,
    RateResponse,
    RatePayment,
    RatePaymentReceipt,
    RenewalChainItem,
    RenewalOutcomeCreate,
)
from api.routers._audit import (
    log_audit,
    log_contract_lifecycle_transition,
    log_contract_open_lifecycle_transition,
)
from api.routers.agenda import _sync_contract_chiuso
from api.services import contract_state as cstate
from api.services.cash_categories import (
    CATEGORIA_ACCONTO_CONTRATTO,
    CATEGORIA_PAGAMENTO_RATA,
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
    CATEGORIA_RIMBORSO_CONTRATTO,
)
from api.services.contract_settlement import compute_settlement, SettlementEsito, MotivoChiusura

# Categoria movimento cassa per acconto — SSoT in cash_categories.py
CATEGORIA_ACCONTO = CATEGORIA_ACCONTO_CONTRATTO

router = APIRouter(prefix="/contracts", tags=["contracts"])


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _to_response(contract: Contract) -> ContractResponse:
    """Converte un Contract ORM in ContractResponse."""
    return ContractResponse.model_validate(contract)


def _to_response_with_rates(
    contract: Contract,
    rates: list[Rate],
    receipt_map: dict[int, list[CashMovement]] | None = None,
    credit_breakdown: dict[str, int] | None = None,
) -> ContractWithRatesResponse:
    """
    Converte Contract + Rate in ContractWithRatesResponse con KPI computati.

    Unica fonte di verita' per tutti i valori finanziari.
    Il frontend legge i campi, non calcola nulla.

    receipt_map: {rate_id: [CashMovement, ...]} — storico pagamenti per ogni rata,
    ordinato cronologicamente (piu' vecchio prima).
    """
    today = date.today()

    # ── Enrich rate con campi computati ──
    enriched_rates = []
    somma_saldate = 0.0
    somma_pendenti = 0.0
    somma_tutte = 0.0
    n_pagate = 0
    n_scadute = 0

    for r in rates:
        rate_data = RateResponse.model_validate(r).model_dump()

        # Storico pagamenti (tutti i CashMovement di questa rata)
        movements = receipt_map.get(r.id, []) if receipt_map else []
        if movements:
            # Ultimo pagamento per backward-compat
            last = movements[-1]
            rate_data["data_pagamento"] = last.data_effettiva
            rate_data["metodo_pagamento"] = last.metodo
            # Lista completa cronologica
            rate_data["pagamenti"] = [
                RatePaymentReceipt(
                    id=m.id,
                    importo=m.importo,
                    metodo=m.metodo,
                    data_pagamento=m.data_effettiva,
                    note=m.note,
                ).model_dump()
                for m in movements
            ]

        # Campi computati per singola rata
        rate_data["importo_residuo"] = round(r.importo_previsto - r.importo_saldato, 2)
        is_scaduta = r.stato != "SALDATA" and r.data_scadenza < today
        rate_data["is_scaduta"] = is_scaduta
        rate_data["giorni_ritardo"] = max(0, (today - r.data_scadenza).days) if is_scaduta else 0

        enriched_rates.append(RateResponse(**rate_data))

        # Accumula aggregati
        somma_tutte += r.importo_previsto
        if r.stato == "SALDATA":
            somma_saldate += r.importo_previsto
            n_pagate += 1
        else:
            # Usa importo_residuo (previsto - saldato) per rate PARZIALI.
            # Es: previsto=400, saldato=100 → conta 300, non 400.
            somma_pendenti += r.importo_previsto - r.importo_saldato
        if is_scaduta:
            n_scadute += 1

    # ── KPI contratto ──
    prezzo = contract.prezzo_totale or 0
    versato = contract.totale_versato or 0

    residuo = cstate.residuo(contract)  # delega al SSoT (§2.2): byte-identica oggi, load-bearing con G7
    percentuale = round((versato / prezzo) * 100) if prezzo > 0 else 0
    # totale_versato e' la fonte di verita' (include acconto + rate + pagamenti legacy)
    importo_da_rateizzare = residuo
    disallineamento = round(importo_da_rateizzare - somma_pendenti, 2)

    # ── Credit breakdown (computed on read) ──
    cb = credit_breakdown or {}
    programmate = cb.get("Programmato", 0)
    completate = cb.get("Completato", 0)
    rinviate = cb.get("Rinviato", 0)  # display only (sedute_rinviate): NON occupa il credito (G7.8)
    crediti_totali = contract.crediti_totali or 0
    # [G7.8/ADR-017] occupazione-credito = Programmato + Completato; Rinviato libera il credito spendibile
    crediti_usati_computed = programmate + completate

    # Override crediti_usati nel dict base (sovrascrive il valore ORM = 0)
    contract_data = ContractResponse.model_validate(contract).model_dump()
    contract_data["crediti_usati"] = crediti_usati_computed

    # Stato derivato dal SSoT (SPEC_VOCABOLARIO §2.2): il dettaglio LEGGE, non ricalcola.
    state = cstate.evaluate_contract(contract, crediti_usati_computed, rates, today)

    return ContractWithRatesResponse(
        **contract_data,
        rate=enriched_rates,
        residuo=residuo,
        percentuale_versata=percentuale,
        importo_da_rateizzare=importo_da_rateizzare,
        somma_rate_previste=round(somma_tutte, 2),
        somma_rate_saldate=round(somma_saldate, 2),
        somma_rate_pendenti=round(somma_pendenti, 2),
        piano_allineato=abs(disallineamento) < 0.01,
        importo_disallineamento=disallineamento,
        rate_totali=len(rates),
        rate_pagate=n_pagate,
        rate_scadute=n_scadute,
        sedute_programmate=programmate,
        sedute_completate=completate,
        sedute_rinviate=rinviate,
        crediti_residui=max(0, crediti_totali - crediti_usati_computed),
        sedute_non_erogate_chiusura=cstate.sedute_non_erogate_alla_chiusura(contract, completate),  # M4
        lifecycle=state.lifecycle.value,
        money_substate=state.money.value,
        is_insolvente=cstate.is_insolvente(state),
        in_scadenza=state.in_scadenza,
    )


def _check_client_ownership(session: Session, client_id: int, trainer_id: int) -> None:
    """
    Relational IDOR: verifica che il cliente appartenga al trainer.
    Se non trovato -> 404 (mai 403).
    """
    client = session.exec(
        select(Client).where(
            Client.id == client_id, Client.trainer_id == trainer_id, Client.deleted_at == None
        )
    ).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente non trovato",
        )


def _occupied_credit_count(session: Session, contract_id: int) -> int:
    """Occupazione-credito del contratto (G7.8): PT `Programmato` + `Completato`, mai `Rinviato`.

    Helper locale a `contracts.py` per i siti che devono derivare il lifecycle dal SSoT senza
    reimplementare inline la semantica dei crediti usati.
    """
    count = session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato.in_(["Programmato", "Completato"]),
            Event.deleted_at == None,
        )
    ).one()
    return int(count or 0)


# ════════════════════════════════════════════════════════════
# GET: Lista contratti
# ════════════════════════════════════════════════════════════

@router.get("", response_model=dict)
def list_contracts(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    id_cliente: Optional[int] = Query(default=None, description="Filtra per cliente"),
    chiuso: Optional[bool] = Query(default=None, description="Filtra per stato chiuso"),
):
    """
    Lista contratti enriched con KPI aggregati.

    3 query batch (zero N+1):
    1. Contratti (paginati + filtrati)
    2. Rate per quei contratti (batch IN)
    3. Clienti per quei contratti (batch IN)

    Response arricchita: nome cliente, conteggi rate, flag scaduti.
    """
    query = select(Contract).where(Contract.trainer_id == trainer.id, Contract.deleted_at == None)

    if id_cliente is not None:
        query = query.where(Contract.id_cliente == id_cliente)
    if chiuso is not None:
        query = query.where(Contract.chiuso == chiuso)

    # Count dalla stessa query base (zero duplicazione filtri)
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    # Paginazione
    offset = (page - 1) * page_size
    query = query.order_by(Contract.data_vendita.desc()).offset(offset).limit(page_size)
    contracts = session.exec(query).all()

    # ── KPI aggregati (calcolati sull'intero set del trainer, pre-filtro) ──
    today = date.today()
    all_contracts_q = select(Contract).where(
        Contract.trainer_id == trainer.id, Contract.deleted_at == None
    )
    all_contracts = session.exec(all_contracts_q).all()

    kpi_chiusi = sum(1 for c in all_contracts if c.chiuso)  # STATO: solo chiusi
    kpi_fatturato = round(sum(c.prezzo_totale or 0 for c in all_contracts), 2)  # CUMULATIVO: include chiusi
    # NETTO dei rimborsi (G7.3 §6, FDM §9.5): card "Incassato" = denaro reale incassato. Delega al SSoT
    # netto_incassato() (= versato − rimborsato). Oggi == Σ versato (rimborsato=0); sotto G7.3 NON sovrastima.
    kpi_incassato = round(sum(cstate.netto_incassato(c) for c in all_contracts), 2)  # CUMULATIVO: include chiusi

    # ── KPI headline per stato di vita (G4) — NON "non chiuso" ──
    # kpi_attivi = stato ATTIVO (aperto + vigente). SOSPESO/ESAURITO (scaduti aperti)
    # contati a parte: contarli come "attivi" mentirebbe sulla base clienti operativa.
    # Derivati da contract_state (regola d'oro §10). Serve crediti_usati solo per
    # distinguere SOSPESO (crediti residui) da ESAURITO; ATTIVO non ne dipende.
    open_contracts = [c for c in all_contracts if not c.chiuso]
    active_ids = [c.id for c in open_contracts]  # "aperti" = non chiusi (per rate scadute + cruscotto)
    open_credit_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id))
        .where(
            Event.id_contratto.in_(active_ids),
            Event.categoria == "PT",
            # G7.8: Rinviato libera il credito (ADR-017)
            Event.stato.in_(["Programmato", "Completato"]),
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto)
    ).all() if active_ids else []
    open_credits = {row[0]: int(row[1]) for row in open_credit_rows}
    open_lifecycles = [
        cstate.contract_lifecycle(c, open_credits.get(c.id, 0), today) for c in open_contracts
    ]
    kpi_attivi = sum(1 for lf in open_lifecycles if lf == cstate.Lifecycle.ATTIVO)
    kpi_sospesi = sum(1 for lf in open_lifecycles if lf == cstate.Lifecycle.SOSPESO)
    kpi_esauriti = sum(1 for lf in open_lifecycles if lf == cstate.Lifecycle.ESAURITO)

    # Rate scadute: rata individualmente scaduta O su contratto scaduto (modello Stripe)
    # Se il contratto e' scaduto, OGNI rata non pagata e' in ritardo.
    kpi_rate_scadute = 0
    if active_ids:
        overdue_rate_count = session.exec(
            select(func.count(Rate.id))
            .join(Contract, Rate.id_contratto == Contract.id)
            .where(
                Rate.id_contratto.in_(active_ids),
                Rate.deleted_at == None,
                Rate.stato != "SALDATA",
                or_(Rate.data_scadenza < today, Contract.data_scadenza < today),
            )
        ).one()
        kpi_rate_scadute = overdue_rate_count or 0

    # ── Cruscotto "Da incassare" (SPEC_RINNOVO §B.4 / TASSONOMIA §1 Asse 3, G1) ──
    # Scomposizione del RESIDUO sui contratti APERTI — equazione che torna a occhio:
    #   residuo            = Σ max(0, prezzo − versato)   ← ancora ("da incassare")
    #   a_rate             = Σ residui delle rate NON SALDATE (PENDENTE+PARZIALE) = già a scadenza
    #   da_pianificare     = resto da mettere a rata SOLO sui contratti ATTIVI (rateizzabili)
    #   da_incassare_scaduto = resto sui contratti SCADUTI aperti (SOSPESO/ESAURITO): NON
    #                          rateizzabile (G1) → si incassa diretto (G6). Bucket separato
    #                          per non gonfiare "da pianificare" con azioni impossibili.
    #   Invariante: residuo = a_rate + da_pianificare + da_incassare_scaduto.
    # NB: 'venduto' (Σ prezzo) NON sta qui — appartiene allo storico (kpi_fatturato).
    kpi_residuo = round(
        sum(cstate.residuo(c) for c in all_contracts if not c.chiuso),  # SSoT: Σ residuo() per contratto aperto
        2,
    )
    residui_a_rate_by_contract: dict[int, float] = {}
    if active_ids:
        nonsaldate_rows = session.exec(
            select(
                Rate.id_contratto,
                func.coalesce(func.sum(Rate.importo_previsto - Rate.importo_saldato), 0),
            )
            .where(
                Rate.id_contratto.in_(active_ids),
                Rate.deleted_at == None,
                Rate.stato != "SALDATA",  # non saldate = PENDENTE + PARZIALE
            )
            .group_by(Rate.id_contratto)
        ).all()
        residui_a_rate_by_contract = {row[0]: float(row[1] or 0) for row in nonsaldate_rows}

    kpi_a_rate = round(sum(residui_a_rate_by_contract.values()), 2)
    # Il "resto" (residuo non coperto da rate) va in da_pianificare se il contratto è ATTIVO
    # (vigente), altrimenti in da_incassare_scaduto. is_vigente deriva l'asse tempo dal SSoT:
    # su un contratto aperto+non eliminato, vigente ⟺ ATTIVO.
    da_pianificare_sum = 0.0
    da_incassare_scaduto_sum = 0.0
    for c in all_contracts:
        if c.chiuso:
            continue
        resto = max(0.0, cstate.residuo(c) - residui_a_rate_by_contract.get(c.id, 0.0))  # residuo SSoT − rate
        if resto <= 0:
            continue
        if cstate.is_vigente(c, today):
            da_pianificare_sum += resto
        else:
            da_incassare_scaduto_sum += resto
    kpi_da_pianificare = round(da_pianificare_sum, 2)
    kpi_da_incassare_scaduto = round(da_incassare_scaduto_sum, 2)

    kpi_data = {
        "kpi_attivi": kpi_attivi,             # STATO: ATTIVO (aperto + vigente) — G4
        "kpi_sospesi": kpi_sospesi,           # STATO: SOSPESO (scaduto, crediti residui)
        "kpi_esauriti": kpi_esauriti,         # STATO: ESAURITO (scaduto, crediti finiti)
        "kpi_chiusi": kpi_chiusi,
        "kpi_fatturato": kpi_fatturato,
        "kpi_incassato": kpi_incassato,
        "kpi_rate_scadute": kpi_rate_scadute,
        "kpi_residuo": kpi_residuo,           # aperti: residuo da incassare = a_rate + da_pianificare + da_incassare_scaduto
        "kpi_a_rate": kpi_a_rate,             # aperti: già a scadenza (residui rate non saldate)
        "kpi_da_pianificare": kpi_da_pianificare,  # ATTIVI: resta da mettere a rata (rateizzabile)
        "kpi_da_incassare_scaduto": kpi_da_incassare_scaduto,  # SCADUTI aperti: residuo non rateizzabile (G1→G6)
    }

    if not contracts:
        return {"items": [], "total": total, "page": page, "page_size": page_size, **kpi_data}

    # ── Batch fetch: rate per tutti i contratti (1 query) ──
    contract_ids = [c.id for c in contracts]
    all_rates = session.exec(
        select(Rate).where(Rate.id_contratto.in_(contract_ids), Rate.deleted_at == None)
    ).all()

    rates_by_contract: dict[int, list[Rate]] = {}
    for r in all_rates:
        rates_by_contract.setdefault(r.id_contratto, []).append(r)

    # ── Batch fetch: clienti per tutti i contratti (1 query) ──
    client_ids = list({c.id_cliente for c in contracts})
    clients = session.exec(
        select(Client).where(Client.id.in_(client_ids))
    ).all()
    client_map = {c.id: c for c in clients}

    # ── Batch fetch: crediti usati per contratto (1 query, zero N+1) ──
    credit_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            # G7.8: Rinviato libera il credito (ADR-017)
            Event.stato.in_(["Programmato", "Completato"]),
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto)
    ).all()
    credits_used_map: dict[int, int] = {row[0]: int(row[1]) for row in credit_rows}

    # ── Batch fetch: sedute EROGATE (Completato) per contratto — R4/L1 (erogato accanto ai residui) ──
    completate_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            Event.stato == "Completato",
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto)
    ).all()
    completate_map: dict[int, int] = {row[0]: int(row[1]) for row in completate_rows}

    # ── Build enriched responses ──
    results = []

    for contract in contracts:
        client = client_map.get(contract.id_cliente)
        rates = rates_by_contract.get(contract.id, [])
        crediti_usati = credits_used_map.get(contract.id, 0)

        # Override crediti_usati: computed on read (non dal valore ORM)
        contract_data = ContractResponse.model_validate(contract).model_dump()
        contract_data["crediti_usati"] = crediti_usati

        # Stato derivato dal SSoT (SPEC_VOCABOLARIO §2.2): un asse vita + un asse denaro +
        # flag derivati, calcolati UNA volta. ha_rate_scadute deriva da qui (AC-1b: una sola
        # formula — equivalente al vecchio inline grazie ai guard rate-date #9/#10).
        state = cstate.evaluate_contract(contract, crediti_usati, rates, today)

        results.append(ContractListResponse(
            **contract_data,
            client_nome=client.nome if client else "",
            client_cognome=client.cognome if client else "",
            rate_totali=len(rates),
            rate_pagate=sum(1 for r in rates if r.stato == "SALDATA"),
            ha_rate_scadute=state.rate_scadute,
            lifecycle=state.lifecycle.value,
            money_substate=state.money.value,
            is_insolvente=cstate.is_insolvente(state),
            in_scadenza=state.in_scadenza,
            residuo=state.residuo,  # SSoT (G6): il frontend legge questo, non ricalcola
            sedute_completate=completate_map.get(contract.id, 0),  # R4/L1: erogato (servizio reso)
            sedute_non_erogate_chiusura=cstate.sedute_non_erogate_alla_chiusura(
                contract, completate_map.get(contract.id, 0)
            ),  # M4: prenotate-non-erogate alla chiusura (solo COMPLETAMENTO)
        ))

    return {
        "items": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        **kpi_data,
    }


# ════════════════════════════════════════════════════════════
# GET: Dettaglio contratto (con rate embedded)
# ════════════════════════════════════════════════════════════

@router.get("/{contract_id}", response_model=ContractWithRatesResponse)
def get_contract(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Dettaglio contratto con rate.

    Bouncer: query singola contract.id + trainer_id.
    """
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer.id, Contract.deleted_at == None
        )
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # Fetch cliente per nome (header pagina dettaglio)
    client = session.get(Client, contract.id_cliente)

    # Fetch rate associate (non eliminate)
    rates = list(session.exec(
        select(Rate).where(
            Rate.id_contratto == contract_id, Rate.deleted_at == None
        ).order_by(Rate.data_scadenza)
    ).all())

    # Batch fetch storico pagamenti per TUTTE le rate con id_rata (1 query, zero N+1)
    rate_ids = [r.id for r in rates]
    receipt_map: dict[int, list[CashMovement]] = {}
    if rate_ids:
        movements = session.exec(
            select(CashMovement).where(
                CashMovement.id_rata.in_(rate_ids),
                CashMovement.tipo == "ENTRATA",
                CashMovement.trainer_id == trainer.id,
                CashMovement.deleted_at == None,
            ).order_by(CashMovement.data_effettiva.asc())
        ).all()
        for mov in movements:
            if mov.id_rata:
                receipt_map.setdefault(mov.id_rata, []).append(mov)

    # Credit breakdown: PT events GROUP BY stato (1 query)
    # [G7.8 DISPLAY-EXEMPT §3.2] Questo GROUP BY conta ANCHE i Rinviato → alimenta `sedute_rinviate`
    #   (display). Resta `!= "Cancellato"` di proposito: NON migrarlo a IN('Programmato','Completato'),
    #   manderebbe `sedute_rinviate` a zero in silenzio. La SOMMA crediti_usati (~riga 149) esclude i
    #   Rinviato; qui NO. Presidiato dal grep-guard ADR-017 in check-all.sh.
    credit_breakdown: dict[str, int] = {}
    credit_rows = session.exec(
        select(Event.stato, func.count(Event.id))
        .where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato != "Cancellato",
            Event.deleted_at == None,
        )
        .group_by(Event.stato)
    ).all()
    for row in credit_rows:
        credit_breakdown[row[0]] = int(row[1])

    resp = _to_response_with_rates(contract, rates, receipt_map, credit_breakdown)
    if client:
        resp.client_nome = client.nome
        resp.client_cognome = client.cognome

    # F1 (G8.1.1): storico cassa unificato — TUTTI i movimenti con id_contratto=questo
    # contratto (acconto, rate, rimborsi USCITA, conguagli ENTRATA). Σ con segno ==
    # netto_incassato (ENTRATA +, USCITA −). Le erogazioni wallet hanno id_contratto=None
    # (client-level, ADR-020) → NON compaiono qui. Ordine cronologico per data_effettiva.
    movimenti = session.exec(
        select(CashMovement)
        .where(
            CashMovement.id_contratto == contract_id,
            CashMovement.trainer_id == trainer.id,
            CashMovement.deleted_at == None,
        )
        .order_by(CashMovement.data_effettiva, CashMovement.id)
    ).all()
    resp.movimenti = [ContractMovementItem.model_validate(m) for m in movimenti]

    # Renewal chain: parent + children — ogni nodo porta il PROPRIO lifecycle reale
    # (SPEC_VOCABOLARIO §2.7/G3): un genitore SOSPESO non deve apparire "Chiuso"/"Attivo".
    today = date.today()
    parent = None
    if contract.rinnovo_di:
        parent = session.exec(
            select(Contract).where(
                Contract.id == contract.rinnovo_di,
                Contract.trainer_id == trainer.id,
                Contract.deleted_at == None,
            )
        ).first()
    children = list(session.exec(
        select(Contract).where(
            Contract.rinnovo_di == contract_id,
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
        ).order_by(Contract.data_inizio)
    ).all())

    # crediti_usati per i nodi catena (1 query batch) → distingue SOSPESO da ESAURITO
    chain = ([parent] if parent else []) + children
    chain_credits: dict[int, int] = {}
    if chain:
        chain_credit_rows = session.exec(
            select(Event.id_contratto, func.count(Event.id))
            .where(
                Event.id_contratto.in_([c.id for c in chain]),
                Event.categoria == "PT",
                # G7.8: Rinviato libera il credito (ADR-017)
                Event.stato.in_(["Programmato", "Completato"]),
                Event.deleted_at == None,
            )
            .group_by(Event.id_contratto)
        ).all()
        chain_credits = {row[0]: int(row[1]) for row in chain_credit_rows}

    def _chain_item(c: Contract) -> RenewalChainItem:
        return RenewalChainItem(
            id=c.id,
            tipo_pacchetto=c.tipo_pacchetto,
            data_inizio=str(c.data_inizio) if c.data_inizio else None,
            data_scadenza=str(c.data_scadenza) if c.data_scadenza else None,
            chiuso=c.chiuso,
            lifecycle=cstate.contract_lifecycle(c, chain_credits.get(c.id, 0), today).value,
        )

    if parent:
        resp.contratto_originale = _chain_item(parent)
    resp.rinnovi_successivi = [_chain_item(c) for c in children]

    return resp


# ════════════════════════════════════════════════════════════
# GET: Storico stato/attività del contratto (G8.1.1 / F6)
# ════════════════════════════════════════════════════════════

def _curate_contract_event(row: AuditLog) -> Optional[ContractHistoryEvent]:
    """
    F6 (G8.1.1): traduce UNA riga `audit_log` (entity='contract') in un evento curato
    per la timeline di stato, oppure None se va nascosta.

    Dedup delle entry "companion": terminate/reopen scrivono SIA l'entry ricca (con
    `motivo_chiusura`) SIA la transizione lifecycle bare (`chiuso` + `motivo` tecnico).
    Teniamo la ricca, scartiamo la companion (`motivo` 'terminazione'/'riapertura_esplicita').
    Le mutazioni di pura cassa (solo `totale_versato`/`stato_pagamento`) NON entrano qui —
    vivono nello storico cassa (F1/F5), così la timeline di stato resta leggibile.
    """
    data = row.created_at
    changes: dict = {}
    if row.changes:
        try:
            parsed = json.loads(row.changes)
            if isinstance(parsed, dict):
                changes = parsed
        except (ValueError, TypeError):
            changes = {}

    if row.action == "CREATE":
        is_rinnovo = "rinnovo_di" in changes
        return ContractHistoryEvent(
            tipo="creato",
            titolo="Contratto creato per rinnovo" if is_rinnovo else "Contratto creato",
            data=data,
        )
    if row.action == "DELETE":
        return ContractHistoryEvent(tipo="eliminato", titolo="Contratto eliminato", data=data)
    if row.action == "RESTORE":
        return ContractHistoryEvent(tipo="ripristinato", titolo="Contratto ripristinato", data=data)

    # ── action == UPDATE ──
    mc = changes.get("motivo_chiusura")

    # 1) Terminazione (entry ricca): motivo_chiusura.new valorizzato.
    if isinstance(mc, dict) and mc.get("new"):
        parti: list[str] = []
        esito = changes.get("esito_balance")
        if esito:
            parti.append(f"esito {str(esito).replace('_', ' ').lower()}")
        rimborso = changes.get("totale_rimborsato")
        if isinstance(rimborso, dict):
            rimb_delta = round(float(rimborso.get("new") or 0) - float(rimborso.get("old") or 0), 2)
            if rimb_delta:
                parti.append(f"rimborso €{rimb_delta:.2f}")
        parti.append(f"motivo {mc['new']}")
        return ContractHistoryEvent(
            tipo="terminato",
            titolo="Contratto terminato",
            dettaglio=" · ".join(parti),
            data=data,
        )

    # 2) Riapertura (entry ricca): `motivo_chiusura` azzerato a None (l'unico discriminante affidabile —
    #    a #2 si arriva solo se #1 NON ha visto un motivo valorizzato). NON pretendere "chiuso" tra le
    #    chiavi: le riaperture in formato storico (G8.1) mettevano il toggle `chiuso` SOLO nella companion
    #    lifecycle (poi deduplicata da #3) → richiederlo qui faceva sparire la riapertura dalla timeline.
    if isinstance(mc, dict) and "new" in mc and mc.get("new") is None:
        parti = []
        residuo_dopo = changes.get("residuo_dopo")
        if residuo_dopo is not None:
            parti.append(f"residuo €{float(residuo_dopo):.2f}")
        rate_rial = changes.get("rate_riallineate")
        if rate_rial:
            parti.append(f"{int(rate_rial)} rate riallineate")
        rimborso_preservato = changes.get("rimborso_preservato")
        if rimborso_preservato:
            parti.append(f"rimborso €{float(rimborso_preservato):.2f} preservato")
        return ContractHistoryEvent(
            tipo="riaperto",
            titolo="Contratto riaperto",
            dettaglio=" · ".join(parti) if parti else None,
            data=data,
        )

    # 3) Transizione lifecycle bare (`chiuso` togglato, senza motivo_chiusura).
    if "chiuso" in changes:
        motivo = changes.get("motivo")
        if motivo in ("terminazione", "riapertura_esplicita"):
            return None  # companion della entry ricca → dedup
        if motivo == "completamento":
            return ContractHistoryEvent(tipo="saldato", titolo="Contratto completato e saldato", data=data)
        if motivo == "riapertura_pagamento":
            return ContractHistoryEvent(tipo="riaperto", titolo="Riaperto: pagamento revocato", data=data)
        if motivo == "riapertura_crediti":
            return ContractHistoryEvent(tipo="riaperto", titolo="Riaperto: crediti liberati", data=data)
        chiuso_field = changes.get("chiuso")
        chiuso_new = chiuso_field.get("new") if isinstance(chiuso_field, dict) else None
        return ContractHistoryEvent(
            tipo="stato",
            titolo="Contratto chiuso" if chiuso_new else "Contratto riaperto",
            data=data,
        )

    # 4) Transizione lifecycle aperto (ATTIVO/SOSPESO/ESAURITO crossing scadenza).
    lc = changes.get("lifecycle")
    if isinstance(lc, dict) and lc.get("old") and lc.get("new"):
        return ContractHistoryEvent(tipo="stato", titolo=f"Stato: {lc['old']} → {lc['new']}", data=data)

    # 5) Esito rinnovo.
    if "esito_rinnovo" in changes:
        esito = changes.get("esito_rinnovo")
        return ContractHistoryEvent(
            tipo="stato",
            titolo=f"Esito rinnovo: {esito}" if esito else "Esito rinnovo rimosso",
            data=data,
        )

    # 6) Modifica significativa di campi del contratto (prezzo/scadenza/sedute/pacchetto).
    _SIGNIFICATIVI = {
        "prezzo_totale": "prezzo",
        "data_scadenza": "scadenza",
        "data_inizio": "inizio",
        "numero_sedute": "sedute",
        "tipo_pacchetto": "pacchetto",
    }
    toccati = [label for key, label in _SIGNIFICATIVI.items() if key in changes]
    if toccati:
        return ContractHistoryEvent(
            tipo="modificato",
            titolo="Contratto modificato",
            dettaglio="Aggiornati: " + ", ".join(toccati),
            data=data,
        )

    # 7) Resto (pura cassa: totale_versato/stato_pagamento) → nascosto (vive in F1/F5).
    return None


@router.get("/{contract_id}/history", response_model=list[ContractHistoryEvent])
def get_contract_history(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    F6 (G8.1.1): storico dello STATO DI VITA del contratto — timeline CRM-grade.

    Read-only. Deriva eventi curati dall'`audit_log` (entity='contract'): creazione,
    terminazione (esito+rimborso+motivo), riapertura, completamento/saldo, transizioni
    di lifecycle, modifiche significative. Dedup delle entry companion. Ordine cronologico
    ascendente (più vecchio in cima). Lo storico CASSA (acconto/rate/rimborsi/conguagli)
    vive su `GET /contracts/{id}` campo `movimenti` (F1) — qui solo lo STATO.
    """
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)

    rows = session.exec(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "contract",
            AuditLog.entity_id == contract.id,
            AuditLog.trainer_id == trainer.id,
        )
        .order_by(AuditLog.created_at, AuditLog.id)
    ).all()

    events: list[ContractHistoryEvent] = []
    for row in rows:
        ev = _curate_contract_event(row)
        if ev is not None:
            events.append(ev)
    return events


# ════════════════════════════════════════════════════════════
# POST: Crea contratto
# ════════════════════════════════════════════════════════════

@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: ContractCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo contratto.

    Bouncer chain:
    1. Relational IDOR: verifica che id_cliente appartenga al trainer
    2. Iniezione sicura trainer_id dal JWT
    """
    # 1. Relational IDOR — il cliente deve appartenere a questo trainer
    _check_client_ownership(session, data.id_cliente, trainer.id)

    # 2. Crea contratto con trainer_id iniettato
    # stato_pagamento determinato dall'acconto
    if data.acconto >= data.prezzo_totale:
        stato_iniziale = "SALDATO"
    elif data.acconto > 0:
        stato_iniziale = "PARZIALE"
    else:
        stato_iniziale = "PENDENTE"

    contract = Contract(
        trainer_id=trainer.id,
        id_cliente=data.id_cliente,
        tipo_pacchetto=data.tipo_pacchetto,
        crediti_totali=data.crediti_totali,
        prezzo_totale=data.prezzo_totale,
        data_inizio=data.data_inizio,
        data_scadenza=data.data_scadenza,
        acconto=data.acconto,
        totale_versato=data.acconto,
        stato_pagamento=stato_iniziale,
        note=data.note,
    )
    session.add(contract)

    # Flush per ottenere l'ID del contratto (necessario per il CashMovement)
    session.flush()

    # 3. Se acconto > 0, registra nel libro mastro (CashMovement ENTRATA)
    # data_effettiva: il denaro è ricevuto al momento della firma, non alla data inizio.
    # Per contratti backdatati si rispetta data_inizio; per contratti futuri si usa oggi.
    if data.acconto > 0:
        client = session.get(Client, data.id_cliente)
        client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{data.id_cliente}"
        acconto_date = min(data.data_inizio, date.today())

        movement = CashMovement(
            trainer_id=trainer.id,
            data_effettiva=acconto_date,
            tipo="ENTRATA",
            categoria=CATEGORIA_ACCONTO,
            importo=data.acconto,
            metodo=data.metodo_acconto,
            id_cliente=data.id_cliente,
            id_contratto=contract.id,
            note=f"Acconto Contratto - {client_label}",
        )
        session.add(movement)

    log_audit(session, "contract", contract.id, "CREATE", trainer.id)
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# PUT: Aggiorna contratto (partial update)
# ════════════════════════════════════════════════════════════

@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    data: ContractUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna un contratto esistente (partial update).

    Bouncer: query singola contract.id + trainer_id.
    Campi protetti: trainer_id, id_cliente, crediti_usati, totale_versato.
    """
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer.id, Contract.deleted_at == None
        )
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # Partial update
    update_data = data.model_dump(exclude_unset=True)
    today = date.today()

    # Debt spec 2: il trigger resta l'update della scadenza, ma la semantica del crossing si deriva
    # sempre dal SSoT (ATTIVO/SOSPESO/ESAURITO), mai dal solo confronto data<oggi scritto inline.
    audit_lifecycle_crossing = False
    old_lifecycle = None
    new_lifecycle = None
    lifecycle_motivo = None
    crediti_usati = None
    if "data_scadenza" in update_data and not contract.chiuso:
        crediti_usati = _occupied_credit_count(session, contract_id)
        old_is_vigente = cstate.is_vigente(contract, today)
        old_lifecycle = cstate.contract_lifecycle(contract, crediti_usati, today).value
    else:
        old_is_vigente = None

    # Cross-field validation: se entrambe le date sono fornite, verifica ordine
    new_inizio = update_data.get("data_inizio", contract.data_inizio)
    new_scadenza = update_data.get("data_scadenza", contract.data_scadenza)
    if new_inizio and new_scadenza and new_scadenza <= new_inizio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_scadenza deve essere dopo data_inizio",
        )

    # Rate boundary (issue C / decisione founder): accorciando la scadenza, le rate NON-SALDATE oltre la
    # nuova data vengono RIPORTATE alla nuova scadenza (auto-cap Chargebee-style, come generate_payment_plan)
    # invece di bloccare con 422. Il dovuto resta intero, le date si comprimono — niente friction "modifica
    # prima le rate". Le SALDATE non si toccano (pagamento già avvenuto: nessuna riscossione futura da
    # ricollocare, né storico di cassa da riscrivere). Ogni spostamento è auditato.
    if "data_scadenza" in update_data and update_data["data_scadenza"]:
        nuova_scad = update_data["data_scadenza"]
        rate_oltre = session.exec(
            select(Rate).where(
                Rate.id_contratto == contract_id,
                Rate.deleted_at == None,
                Rate.stato.in_(["PENDENTE", "PARZIALE"]),
                Rate.data_scadenza > nuova_scad,
            )
        ).all()
        for r in rate_oltre:
            old_due = r.data_scadenza
            r.data_scadenza = nuova_scad
            session.add(r)
            log_audit(session, "rate", r.id, "UPDATE", trainer.id,
                      {"data_scadenza": {"old": str(old_due), "new": str(nuova_scad)}, "motivo": "scadenza_anticipata"})

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(contract, field)
        setattr(contract, field, value)
        if value != old_val:
            changes[field] = {"old": old_val, "new": value}

    if "data_scadenza" in update_data and old_is_vigente is not None:
        new_is_vigente = cstate.is_vigente(contract, today)
        if old_is_vigente != new_is_vigente:
            audit_lifecycle_crossing = True
            new_lifecycle = cstate.contract_lifecycle(contract, crediti_usati or 0, today).value
            lifecycle_motivo = "scadenza_estesa" if new_is_vigente else "scadenza_retrodatata"

    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, changes or None)
    if audit_lifecycle_crossing and old_lifecycle and new_lifecycle and lifecycle_motivo:
        log_contract_open_lifecycle_transition(
            session,
            contract,
            old_lifecycle=old_lifecycle,
            new_lifecycle=new_lifecycle,
            motivo=lifecycle_motivo,
        )
    session.add(contract)
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# DELETE: Elimina contratto
# ════════════════════════════════════════════════════════════

@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: int,
    force: bool = Query(False, description="Forza eliminazione anche con rate pendenti/crediti residui"),
    keep_payments: bool = Query(False, description="Mantieni pagamenti incassati nel ledger (solo con force)"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Soft-delete contratto — per errori o contratti completati.

    Bouncer: contract.id + trainer_id + non eliminato.
    RESTRICT (obbligazioni pendenti) — skippato se force=True:
    - Rate non saldate (PENDENTE/PARZIALE) -> 409
    - Crediti residui (sedute PT non consumate) -> 409
    CASCADE (pulizia completa):
    - Se force: reverse pagamenti rate + soft-delete TUTTE le rate
    - Se keep_payments: detach movimenti dal contratto (restano nel ledger)
    - Altrimenti: soft-delete tutti CashMovement
    - Detach eventi (id_contratto = NULL, restano in agenda)
    """
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id, Contract.trainer_id == trainer.id, Contract.deleted_at == None
        )
    ).first()

    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    if not force:
        # RESTRICT 1: rate con obbligazioni pendenti (PENDENTE o PARZIALE)
        rate_pendenti = session.exec(
            select(func.count(Rate.id)).where(
                Rate.id_contratto == contract_id,
                Rate.stato.in_(["PENDENTE", "PARZIALE"]),
                Rate.deleted_at == None,
            )
        ).one()
        if rate_pendenti > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Impossibile eliminare: il contratto ha {rate_pendenti} rate non saldate. "
                       f"Usa la chiusura (chiuso) per archiviarlo.",
            )

        # RESTRICT 2: crediti residui (sedute PT non ancora consumate)
        crediti_totali = contract.crediti_totali or 0
        if crediti_totali > 0:
            crediti_usati = session.exec(
                select(func.count(Event.id)).where(
                    Event.id_contratto == contract_id,
                    Event.categoria == "PT",
                    # G7.8: Rinviato libera il credito (ADR-017)
                    Event.stato.in_(["Programmato", "Completato"]),
                    Event.deleted_at == None,
                )
            ).one()
            crediti_residui = crediti_totali - crediti_usati
            if crediti_residui > 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Impossibile eliminare: il contratto ha {crediti_residui} crediti residui "
                           f"({crediti_usati}/{crediti_totali} usati). "
                           f"Usa la chiusura (chiuso) per archiviarlo.",
                )

    now = datetime.now(timezone.utc)

    # Fetch tutte le rate del contratto
    all_rates = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract_id,
            Rate.deleted_at == None,
        )
    ).all()

    # FORCE + keep_payments=False: reverse pagamenti (soft-delete movimenti rata)
    force_reversed_count = 0
    force_reversed_amount = 0.0
    if force and not keep_payments:
        for r in all_rates:
            if r.importo_saldato and r.importo_saldato > 0:
                rate_movements = session.exec(
                    select(CashMovement).where(
                        CashMovement.id_rata == r.id,
                        CashMovement.tipo == "ENTRATA",
                        CashMovement.deleted_at == None,
                    )
                ).all()
                for rm in rate_movements:
                    rm.deleted_at = now
                    session.add(rm)
                    log_audit(session, "movement", rm.id, "DELETE", trainer.id)

                force_reversed_amount += r.importo_saldato
                force_reversed_count += 1

    # CASCADE 1: soft-delete TUTTE le rate
    for r in all_rates:
        r.deleted_at = now
        session.add(r)
        log_audit(session, "rate", r.id, "DELETE", trainer.id)

    # CASCADE 2: gestione CashMovement (acconto + pagamenti)
    movements = session.exec(
        select(CashMovement).where(
            CashMovement.id_contratto == contract_id,
            CashMovement.trainer_id == trainer.id,
            CashMovement.deleted_at == None,
        )
    ).all()
    payments_kept = 0
    if force and keep_payments:
        # Detach: scollega movimenti dal contratto/rata (restano nel ledger)
        for mov in movements:
            mov.id_contratto = None
            mov.id_rata = None
            session.add(mov)
            payments_kept += 1
    else:
        # Soft-delete tutti i movimenti
        for mov in movements:
            mov.deleted_at = now
            session.add(mov)
            log_audit(session, "movement", mov.id, "DELETE", trainer.id)

    # CASCADE 3: detach eventi (mantieni in agenda, rimuovi link contratto)
    linked_events = session.exec(
        select(Event).where(
            Event.id_contratto == contract_id,
            Event.deleted_at == None,
        )
    ).all()
    for ev in linked_events:
        ev.id_contratto = None
        session.add(ev)

    contract.deleted_at = now
    session.add(contract)
    audit_changes = None
    if force:
        audit_changes = {
            "force": True,
            "keep_payments": keep_payments,
            "rate_reversed": force_reversed_count,
            "amount_reversed": round(force_reversed_amount, 2),
            "payments_kept": payments_kept,
        }
    log_audit(session, "contract", contract.id, "DELETE", trainer.id, audit_changes)
    session.commit()


# ════════════════════════════════════════════════════════════
# POST: Rinnova contratto (clone con nuove date)
# ════════════════════════════════════════════════════════════

@router.post("/{contract_id}/renew", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def renew_contract(
    contract_id: int,
    data: ContractCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Rinnova un contratto esistente creandone uno nuovo collegato.

    Il nuovo contratto:
    - Ha rinnovo_di = contract_id (catena di rinnovi)
    - Usa i dati dal payload (il frontend pre-compila con i dati del vecchio)
    - Segue le stesse regole di create_contract (Relational IDOR, acconto, ecc.)

    Bouncer: il contratto originale deve appartenere al trainer.
    """
    # 1. Bouncer: verifica ownership contratto originale
    original = session.exec(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
        )
    ).first()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")

    # 2. Relational IDOR — il cliente deve appartenere a questo trainer
    _check_client_ownership(session, data.id_cliente, trainer.id)

    # 3. Crea contratto rinnovato con link al precedente
    if data.acconto >= data.prezzo_totale:
        stato_iniziale = "SALDATO"
    elif data.acconto > 0:
        stato_iniziale = "PARZIALE"
    else:
        stato_iniziale = "PENDENTE"

    renewed = Contract(
        trainer_id=trainer.id,
        id_cliente=data.id_cliente,
        tipo_pacchetto=data.tipo_pacchetto,
        crediti_totali=data.crediti_totali,
        prezzo_totale=data.prezzo_totale,
        data_inizio=data.data_inizio,
        data_scadenza=data.data_scadenza,
        acconto=data.acconto,
        totale_versato=data.acconto,
        stato_pagamento=stato_iniziale,
        note=data.note,
        rinnovo_di=contract_id,
    )
    session.add(renewed)
    session.flush()

    # 4. Se acconto > 0, registra nel libro mastro
    if data.acconto > 0:
        client = session.get(Client, data.id_cliente)
        client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{data.id_cliente}"
        acconto_date = min(data.data_inizio, date.today())

        movement = CashMovement(
            trainer_id=trainer.id,
            data_effettiva=acconto_date,
            tipo="ENTRATA",
            categoria=CATEGORIA_ACCONTO,
            importo=data.acconto,
            metodo=data.metodo_acconto,
            id_cliente=data.id_cliente,
            id_contratto=renewed.id,
            note=f"Acconto Rinnovo Contratto - {client_label}",
        )
        session.add(movement)

    log_audit(session, "contract", renewed.id, "CREATE", trainer.id, {"rinnovo_di": contract_id})
    session.commit()
    session.refresh(renewed)

    return _to_response(renewed)


def _bouncer_contract_owned(session: Session, contract_id: int, trainer_id: int) -> Contract:
    """Bouncer: il contratto deve appartenere al trainer (404 mai 403)."""
    contract = session.exec(
        select(Contract).where(
            Contract.id == contract_id,
            Contract.trainer_id == trainer_id,
            Contract.deleted_at == None,
        )
    ).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")
    return contract


@router.post("/{contract_id}/renewal-outcome", response_model=ContractResponse)
def set_renewal_outcome(
    contract_id: int,
    data: RenewalOutcomeCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Marca un contratto come "non rinnova" (cliente perso) con motivo strutturato.

    Stato terminale che esce dalla worklist "clienti da recuperare" ma resta in storico
    (SPEC_RINNOVI_SCADUTI §5). Reversibile via DELETE. Bouncer ownership (404 mai 403) + audit.
    """
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)
    contract.esito_rinnovo_motivo = data.motivo
    contract.esito_rinnovo_note = data.note
    contract.esito_rinnovo_il = date.today()
    session.add(contract)
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {"esito_rinnovo": data.motivo})
    session.commit()
    session.refresh(contract)
    return _to_response(contract)


@router.delete("/{contract_id}/renewal-outcome", response_model=ContractResponse)
def clear_renewal_outcome(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Riapre l'opportunità di recupero (annulla "non rinnova"). Bouncer + audit."""
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)
    contract.esito_rinnovo_motivo = None
    contract.esito_rinnovo_note = None
    contract.esito_rinnovo_il = None
    session.add(contract)
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {"esito_rinnovo": None})
    session.commit()
    session.refresh(contract)
    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# POST: Incassa residuo diretto (G6, Blocco 4)
# ════════════════════════════════════════════════════════════

@router.post("/{contract_id}/incassa-residuo", response_model=ContractResponse)
def incassa_residuo(
    contract_id: int,
    data: RatePayment,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Incassa il residuo di un contratto DIRETTAMENTE, senza passare da una rata (G6).

    È l'azione per i contratti SCADUTI aperti (SOSPESO/ESAURITO) il cui residuo NON è
    più rateizzabile (FDM §1 Asse 3, bucket "da incassare scaduto" di list_contracts) —
    ma funziona su qualsiasi contratto aperto con residuo > 0. Gemello in ENTRATA del
    rimborso da terminazione (G7).

    Strada B (LORDO crescente): `totale_versato` aumenta, mai si riscrive a ritroso.

    Operazione atomica (UN solo commit):
    A) Bouncer ownership → 404
    B) Guard contratto chiuso → 400
    C) Residuo via SSoT `contract_state.residuo()` (regola d'oro §10); residuo ~0 → 400
    D) Cap anti-overpayment: importo > residuo → 422
    E) `totale_versato += importo` + ricalcolo `stato_pagamento`
    F) CashMovement ENTRATA (categoria PAGAMENTO_RATA, id_rata=None) nel libro mastro
    G) Auto-close canonico via `_sync_contract_chiuso` (logga la transizione `chiuso`)
    H) Audit contract UPDATE (`totale_versato`+`stato_pagamento`; `chiuso` lo logga G)
    """
    # A) Bouncer ownership (404 mai 403)
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)

    # B) Guard: contratto chiuso non incassabile
    if contract.chiuso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile incassare: il contratto è chiuso",
        )

    # C) Residuo dal SSoT (delega obbligatoria — niente ricalcolo inline)
    residuo = cstate.residuo(contract)
    if residuo <= 0.009:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun residuo da incassare: il contratto è già saldato",
        )

    # D) Cap anti-overpayment a livello contratto
    if data.importo > residuo + 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Importo ({data.importo:.2f}) supera il residuo del contratto ({residuo:.2f})",
        )

    # E) Aggiorna totale_versato (incrementale, Strada B) + stato_pagamento
    old_totale_versato = contract.totale_versato
    old_stato_pagamento = contract.stato_pagamento
    contract.totale_versato = contract.totale_versato + data.importo
    if cstate.is_saldato(contract):  # G8.1.1/F4: net-aware (residuo()==0), non versato≥prezzo lordo
        contract.stato_pagamento = "SALDATO"
    elif contract.totale_versato > 0:
        contract.stato_pagamento = "PARZIALE"
    session.add(contract)

    # F) Registra nel libro mastro (CashMovement ENTRATA, id_rata=None → incasso diretto)
    client = session.get(Client, contract.id_cliente)
    client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{contract.id_cliente}"
    movement = CashMovement(
        trainer_id=trainer.id,
        data_effettiva=data.data_pagamento,
        tipo="ENTRATA",
        categoria=CATEGORIA_PAGAMENTO_RATA,
        importo=data.importo,
        metodo=data.metodo,
        id_cliente=contract.id_cliente,
        id_contratto=contract.id,
        id_rata=None,
        note=data.note or f"Incasso residuo diretto - {client_label}",
    )
    session.add(movement)

    # G) Auto-close canonico (date-independent): se saldato + crediti esauriti → chiuso.
    #    Riusa l'helper SSoT condiviso con agenda/pay_rate (no 3ª copia inline) — logga
    #    da sé la transizione `chiuso` con motivo "completamento".
    _sync_contract_chiuso(session, contract.id)

    # H) Audit + commit atomico. La transizione `chiuso` è già loggata da G (P2):
    #    qui si registra solo l'UPDATE denaro, identico a pay_rate (no doppio log).
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "totale_versato": {"old": old_totale_versato, "new": contract.totale_versato},
        "stato_pagamento": {"old": old_stato_pagamento, "new": contract.stato_pagamento},
    })
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# Terminazione anticipata (G7.3) — conguaglio + atto atomico a 2 gambe
# ════════════════════════════════════════════════════════════

def _count_sedute_erogate(session: Session, contract_id: int) -> int:
    """Sedute PT **erogate** (servizio reso) = Event PT Completati, non eliminati. Base del conguaglio
    pro-sedute (IMPL_PLAN §4.2). NB: ≠ `crediti_usati` dell'auto-close (che conta i NON-Cancellati,
    incl. i Programmati): il conguaglio valuta ciò che è stato reso, non ciò che è solo prenotato."""
    return session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato == "Completato",
            Event.deleted_at == None,
        )
    ).one()


def _count_sedute_prenotate(session: Session, contract_id: int) -> int:
    """Sedute PT **prenotate ma non svolte** = Event PT Programmati, non eliminati. Proiezione di Event
    (gemello di `_count_sedute_erogate`, stato diverso), query SEPARATA: NON tocca il path del conguaglio
    (codice verde). **SOLO display** nella preview (D2, G7.5c): NON entra in `compute_settlement` — il
    conguaglio resta su base sedute Completate. Serve all'avviso UI 'le prenotate non riducono il rimborso'."""
    return session.exec(
        select(func.count(Event.id)).where(
            Event.id_contratto == contract_id,
            Event.categoria == "PT",
            Event.stato == "Programmato",
            Event.deleted_at == None,
        )
    ).one()


def _motivo_from_esito(esito: SettlementEsito) -> str:
    """Mappa esito→motivo_chiusura (AC-7.3-9 + ADR-018). terminate NON assegna MAI COMPLETAMENTO
    (riservato all'auto-close; lo riaprirebbe la reopen-allowlist G7.2). TERMINAZIONE_DECADENZA è
    legacy: non più emesso qui (il ramo trainer è ora TERMINAZIONE_SALDO_TRAINER)."""
    if esito == SettlementEsito.CREDITO_CLIENTE:
        return MotivoChiusura.TERMINAZIONE_RIMBORSO.value
    if esito == SettlementEsito.CREDITO_TRAINER:
        return MotivoChiusura.TERMINAZIONE_SALDO_TRAINER.value
    return MotivoChiusura.CONSUNZIONE.value  # PARI (conguaglio ~ 0)


def _settlement_for(session: Session, contract: Contract):
    """Conguaglio di terminazione (puro, zero scritture). Fonte-unica-importo (§2): il
    `residuo_corrente = contract_state.residuo()` PRE-storno passa in UNA variabile a compute_settlement."""
    residuo_corrente = cstate.residuo(contract)
    sedute_erogate = _count_sedute_erogate(session, contract.id)
    return compute_settlement(
        sedute_erogate=sedute_erogate,
        prezzo_totale=contract.prezzo_totale,
        crediti_totali=contract.crediti_totali,
        totale_versato=contract.totale_versato,
        totale_rimborsato=contract.totale_rimborsato,  # G8.1: net-aware (ri-terminazione post-reopen)
        residuo_corrente=residuo_corrente,
    )


def _build_settlement_preview(contract: Contract, settlement, sedute_prenotate: int = 0) -> ContractSettlementPreview:
    """Compone la preview leggibile dal conguaglio (ADR-018). Framing di PROPOSTA (§0/§4): mai
    "obbligo legale", sempre "calcolato col metodo standard, verifica con le condizioni del contratto"."""
    cliente = settlement.esito == SettlementEsito.CREDITO_CLIENTE
    trainer_credit = settlement.esito == SettlementEsito.CREDITO_TRAINER
    storno = settlement.residuo_pre > 0.009
    azioni_permesse: list[str] = []
    if cliente:
        msg = f"Conguaglio calcolato (pro-rata sedute): risulta un rimborso di €{settlement.credito_cliente:.2f} a favore del cliente."
        if storno:
            msg += f" Il residuo di €{settlement.residuo_pre:.2f} per le sedute non erogate viene azzerato."
    elif trainer_credit:
        azioni_permesse = sorted(VALID_AZIONI_CREDITO_TRAINER)
        msg = (
            f"Conguaglio calcolato (pro-rata sedute): il cliente ha ricevuto più servizio di quanto versato. "
            f"Saldo a tuo favore €{settlement.credito_trainer:.2f}: scegli se incassarlo ora (importo "
            f"modificabile), metterlo a credito (il cliente paga dopo) o rinunciarvi."
        )
    elif storno:
        msg = f"Conguaglio calcolato (pro-rata sedute): nessun rimborso. Il cliente ha già consumato il servizio reso; il residuo di €{settlement.residuo_pre:.2f} viene azzerato."
    else:
        msg = "Conguaglio calcolato (pro-rata sedute): nessun rimborso e nessun residuo da azzerare."
    msg += " Importo proposto col metodo standard pro-rata sedute — verifica con le condizioni del tuo contratto."
    return ContractSettlementPreview(
        esito=settlement.esito.value,
        motivo_chiusura=_motivo_from_esito(settlement.esito),
        valore_servizio_reso=settlement.valore_servizio_reso,
        conguaglio=settlement.conguaglio,
        importo_rimborso=settlement.credito_cliente,
        credito_trainer=settlement.credito_trainer,
        quota_da_stornare=settlement.residuo_pre,
        sedute_erogate=settlement.sedute_erogate,
        sedute_totali=contract.crediti_totali,
        sedute_prenotate=sedute_prenotate,
        metodo_rimborso_richiesto=cliente,
        azioni_permesse=azioni_permesse,
        messaggio=msg,
    )


@router.get("/{contract_id}/settlement-preview", response_model=ContractSettlementPreview)
def settlement_preview(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Anteprima del conguaglio di terminazione (dry-run, AC-7.3-4): **ZERO scritture**.

    Il default pro_sedute NON esegue mai silenziosamente: propone l'esito (rimborso/storno/nullo)
    e l'utente ratifica via `terminate`. Bouncer 404; contratto già chiuso → 400.
    """
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)
    if contract.chiuso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il contratto è già chiuso")
    return _build_settlement_preview(
        contract,
        _settlement_for(session, contract),
        _count_sedute_prenotate(session, contract.id),  # D2: solo display, query separata dal conguaglio
    )


@router.post("/{contract_id}/terminate", response_model=ContractResponse)
def terminate_contract(
    contract_id: int,
    data: ContractTerminate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Terminazione anticipata di un contratto vivo (G7.3 + ADR-018, Strada B). Atto UMANO esplicito,
    terza via a CHIUSO. Transazione UNICA atomica.

    Flusso (un solo commit):
    A) Bouncer 404 → B) guard chiuso 400
    C) Conguaglio puro balance-based (fonte-unica-importo §2: `residuo()` PRE-storno in UNA variabile)
    D) Gamba d'azione (un solo CashMovement), derivata dall'esito:
       • CREDITO_CLIENTE → USCITA RIMBORSO_CONTRATTO (`metodo_rimborso` → 422) + `totale_rimborsato +=`
       • CREDITO_TRAINER → scelta esplicita (422 se assente): INCASSA_ORA (ENTRATA INCASSO_CONGUAGLIO,
         importo editabile [0, credito_trainer], `metodo_pagamento` → 422, `totale_versato +=`) oppure
         RINUNCIA_ESPRESSA (no cassa, nota obbligatoria → 422). A_CREDITO è G7.10 (422 a schema).
       • PARI → nessun movimento
    E) Gamba STORNO (SEMPRE): `quota_stornata += residuo_pre − incasso_ora + rimborso_out` → `residuo()` → 0
       (net-aware G8.1/ADR-019: il rimborso che ESCE riduce il netto → entra nello storno, simmetrico
       all'incasso che lo cresce; pre-G8.1 il rimborso non toccava il residuo e bastava `− incasso_ora`)
    F) Soft-delete SOLO rate NON-saldate (B-3): mai SALDATA né i loro CashMovement
    G) Stato terminale DIRETTO (B-2-attiva): chiuso/motivo/data — **MAI** via `_sync_contract_chiuso`
       (su un SOSPESO terminato `_sync` vedrebbe should_be_chiuso=False e riaprirebbe nello stesso commit)
    H) Audit (snapshot `sedute_erogate`, no-silent-loss) + transizione `chiuso`
    """
    # A) Bouncer ownership (404 mai 403)
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)

    # B) Guard: già chiuso → non terminabile
    if contract.chiuso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il contratto è già chiuso")

    # C) Conguaglio puro balance-based (fonte-unica-importo: residuo PRE-storno). ADR-018.
    settlement = _settlement_for(session, contract)
    motivo = _motivo_from_esito(settlement.esito)
    data_chiusura = data.data_chiusura or date.today()
    old_quota = contract.quota_stornata or 0
    old_rimborsato = contract.totale_rimborsato or 0
    old_versato = contract.totale_versato or 0
    old_chiuso = contract.chiuso

    client = session.get(Client, contract.id_cliente)
    client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{contract.id_cliente}"

    # D) Gamba d'azione, derivata dall'esito (ADR-018): un solo CashMovement per terminazione.
    movement = None
    incasso_ora = 0.0                 # X incassato dal trainer (ramo CREDITO_TRAINER + INCASSA_ORA)
    rimborso_out = 0.0                # X rimborsato al cliente (ramo CREDITO_CLIENTE) — entra nello storno (G8.1)
    saldo_trainer_rinunciato = 0.0    # parte del credito_trainer abbuonata (credito_trainer − X)
    credito_differito = None          # receivable creato dal ramo A_CREDITO (G7.10)
    wallet_cliente = None             # crediti_cliente creato dal ramo CREDITO_CLIENTE (G8.1, non-rimborsato)

    if settlement.esito == SettlementEsito.CREDITO_CLIENTE:
        # G8.1/ADR-020: rimborso EDITABILE [0, credito_cliente] (default = pieno → retro-compatibile). Il
        # non-rimborsato NON si perde: diventa un credito a wallet del cliente (RIMBORSO_DIFFERITO), FUORI
        # dal residuo(). Niente "rinuncia" lato cliente: non si abbuona denaro dovuto al cliente (asimmetria).
        rimborso_out = (
            settlement.credito_cliente if data.importo_rimborso is None
            else round(data.importo_rimborso, 2)
        )
        if rimborso_out > settlement.credito_cliente + 0.009:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"L'importo da rimborsare (€{rimborso_out:.2f}) non può superare il credito del "
                    f"cliente (€{settlement.credito_cliente:.2f})."
                ),
            )
        rimborso_out = max(rimborso_out, 0.0)
        if rimborso_out > 0.009:
            if not data.metodo_rimborso:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Metodo di rimborso obbligatorio per una terminazione con rimborso",
                )
            movement = CashMovement(
                trainer_id=trainer.id,
                data_effettiva=data_chiusura,
                tipo="USCITA",
                categoria=CATEGORIA_RIMBORSO_CONTRATTO,
                importo=rimborso_out,                 # fonte-unica-importo: == delta totale_rimborsato
                metodo=data.metodo_rimborso,
                id_cliente=contract.id_cliente,
                id_contratto=contract.id,
                id_rata=None,
                note=data.note or f"Rimborso terminazione - {client_label}",
            )
            session.add(movement)
            contract.totale_rimborsato = old_rimborsato + rimborso_out
        # Il non-rimborsato → wallet del cliente (ADR-020), fuori dal residuo (storno = residuo_pre + rimborso_out).
        wallet_credit = round(settlement.credito_cliente - rimborso_out, 2)
        if wallet_credit > 0.009:
            wallet_cliente = CreditoCliente(
                trainer_id=trainer.id,
                id_cliente=contract.id_cliente,
                importo=wallet_credit,
                importo_erogato=0.0,
                stato="APERTO",
                causale="RIMBORSO_DIFFERITO",
                id_contratto_origine=contract.id,
                data_creazione=data_chiusura,
            )
            session.add(wallet_cliente)

    elif settlement.esito == SettlementEsito.CREDITO_TRAINER:
        # Il cliente deve ancora per servizio già reso → scelta esplicita obbligatoria (ADR-018).
        if data.azione_credito_trainer is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Il cliente ha ricevuto più servizio di quanto versato (saldo a tuo favore "
                    f"€{settlement.credito_trainer:.2f}): scegli se incassarlo ora o rinunciarvi."
                ),
            )
        if data.azione_credito_trainer == "INCASSA_ORA":
            if not data.metodo_pagamento:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Metodo di pagamento obbligatorio per incassare il saldo a tuo favore",
                )
            # Importo proposto = credito_trainer; EDITABILE solo verso il basso (cap [0, credito_trainer]).
            incasso_ora = (
                settlement.credito_trainer if data.importo_incassato is None
                else round(data.importo_incassato, 2)
            )
            if incasso_ora > settlement.credito_trainer + 0.009:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"L'importo da incassare (€{incasso_ora:.2f}) non può superare il saldo a tuo "
                        f"favore (€{settlement.credito_trainer:.2f}): non si fattura servizio non erogato."
                    ),
                )
            incasso_ora = max(incasso_ora, 0.0)
            saldo_trainer_rinunciato = round(settlement.credito_trainer - incasso_ora, 2)
            if incasso_ora > 0.009:
                movement = CashMovement(
                    trainer_id=trainer.id,
                    data_effettiva=data_chiusura,
                    tipo="ENTRATA",
                    categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
                    importo=incasso_ora,
                    metodo=data.metodo_pagamento,
                    id_cliente=contract.id_cliente,
                    id_contratto=contract.id,
                    id_rata=None,
                    note=data.note or f"Incasso conguaglio terminazione - {client_label}",
                )
                session.add(movement)
                contract.totale_versato = old_versato + incasso_ora  # Strada B: cresce sul forward
        elif data.azione_credito_trainer == "RINUNCIA_ESPRESSA":
            if not (data.note and data.note.strip()):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Nota obbligatoria per rinunciare al saldo a tuo favore (presidio auditabile)",
                )
            saldo_trainer_rinunciato = settlement.credito_trainer
        elif data.azione_credito_trainer == "A_CREDITO":
            # G7.10: "chiudo oggi, il cliente paga dopo". Il credito_trainer NON resta nel contratto
            # (romperebbe residuo()==0): viene STORNATO (gamba E, incasso_ora=0 → quota_stornata piena) e
            # RI-TRACCIATO come receivable FUORI da residuo(). Nessuna cassa ora; mai una Rate su chiuso.
            credito_differito = CreditoTerminazione(
                trainer_id=trainer.id,
                id_contratto=contract.id,
                id_cliente=contract.id_cliente,
                importo=settlement.credito_trainer,
                importo_incassato=0.0,
                stato="APERTO",
                data_creazione=data_chiusura,
            )
            session.add(credito_differito)

    # E) Gamba STORNO (sempre): porta residuo() a 0 sotto il net-aware (G8.1/ADR-019). quota = P − netto =
    #    residuo_pre − incasso_ora + rimborso_out. Il rimborso che ESCE (USCITA) riduce il netto incassato →
    #    va aggiunto allo storno, simmetrico all'incasso che lo cresce. (Pre-G8.1 il rimborso non entrava nel
    #    residuo → bastava residuo_pre − incasso_ora; net-aware lo richiede esplicito per tenere residuo()==0.)
    contract.quota_stornata = old_quota + round(settlement.residuo_pre - incasso_ora + rimborso_out, 2)

    # F) Soft-delete SOLO le rate NON-saldate (B-3). Le SALDATE e i loro CashMovement ENTRATA
    #    SOPRAVVIVONO: cancellarle romperebbe l'àncora `totale_versato == Σ ENTRATA` (Σ ENTRATA
    #    scenderebbe, il lordo no). NON riusare il cascade di delete_contract (tocca anche le SALDATE).
    now = datetime.now(timezone.utc)
    rate_non_saldate = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at == None,
        )
    ).all()
    for r in rate_non_saldate:
        r.deleted_at = now
        r.chiusa_da_terminazione = True  # M1: marca per il reopen inverso esatto (solo queste si ripristinano)
        session.add(r)
        log_audit(session, "rate", r.id, "DELETE", trainer.id)

    # G) Stato terminale DIRETTO (B-2-attiva). MAI `_sync_contract_chiuso`: su un SOSPESO terminato
    #    (saldato, crediti residui) ricalcolerebbe should_be_chiuso=False → reset `chiuso=False`.
    contract.chiuso = True
    contract.motivo_chiusura = motivo
    contract.data_chiusura = data_chiusura
    session.add(contract)

    # H) Audit atomico. flush per popolare l'id del movimento. Snapshot `sedute_erogate` (no-silent-loss:
    #    crediti_usati è event-derived e può driftare; è l'unico record del servizio forfettato).
    #    Payload ADR-018 (§6.2): ricostruibile se il trainer ha incassato, abbuonato o rinunciato.
    is_cliente = settlement.esito == SettlementEsito.CREDITO_CLIENTE
    if movement is not None or credito_differito is not None or wallet_cliente is not None:
        session.flush()  # popola gli id (movimento, receivable e/o wallet) per l'audit
    if movement is not None:
        log_audit(session, "movement", movement.id, "CREATE", trainer.id)
    if credito_differito is not None:
        log_audit(session, "credito_terminazione", credito_differito.id, "CREATE", trainer.id)
    if wallet_cliente is not None:
        log_audit(session, "credito_cliente", wallet_cliente.id, "CREATE", trainer.id)
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "motivo_chiusura": {"old": None, "new": motivo},
        "data_chiusura": {"old": None, "new": data_chiusura},
        "quota_stornata": {"old": old_quota, "new": contract.quota_stornata},
        "totale_rimborsato": {"old": old_rimborsato, "new": contract.totale_rimborsato},
        "totale_versato": {"old": old_versato, "new": contract.totale_versato or 0},
        "sedute_erogate_snapshot": settlement.sedute_erogate,
        "valore_servizio_reso": settlement.valore_servizio_reso,
        "esito_balance": settlement.esito.value,
        "credito_cliente": settlement.credito_cliente,
        "credito_trainer": settlement.credito_trainer,
        "quota_non_erogata": settlement.quota_non_erogata,
        "azione_credito_trainer": data.azione_credito_trainer,
        "importo_incassato": round(incasso_ora, 2),
        "saldo_trainer_rinunciato": round(saldo_trainer_rinunciato, 2),
        "importo_differito": round(settlement.credito_trainer, 2) if credito_differito is not None else 0.0,
        "importo_rimborsato": round(rimborso_out, 2),
        "wallet_cliente_credito": round(settlement.credito_cliente - rimborso_out, 2) if is_cliente else 0.0,
        "movimento_cassa_id": movement.id if movement is not None else None,
        "credito_terminazione_id": credito_differito.id if credito_differito is not None else None,
        "credito_cliente_id": wallet_cliente.id if wallet_cliente is not None else None,
    })
    # Transizione `chiuso` (P2): terminate la logga DA SÉ (non chiama _sync, che altrimenti la loggherebbe)
    log_contract_lifecycle_transition(
        session,
        contract,
        old_chiuso=old_chiuso,
        motivo="terminazione",
        importo_rimborsato=settlement.credito_cliente if is_cliente else None,
        residuo_annullato=round(settlement.residuo_pre - incasso_ora, 2),
        data_chiusura=data_chiusura,
    )
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


def _reconcile_rate_plan(session: Session, contract, trainer_id: int) -> dict:
    """G8.1.1/F2 (ADR-019 Addendum, D-RECONCILIA-RATE): dopo `reopen`, riallinea il piano rate non-saldate
    al `residuo()` net-aware ricalcolato. L'inverso-esatto (M1) ripristina le rate al loro importo
    PRE-terminate: se la cassa è rimasta (rimborso/conguaglio), il residuo ricalcolato ≠ pre-terminate →
    le rate non combaciano.

    - **Eccedenza** (Σ residui-rata > residuo): taglio CRONOLOGICO — si copre il residuo riempiendo dalle
      rate più vecchie; la rata a cavallo è ridotta a coprire l'esatto residuo rimanente; le successive
      sono azzerate (soft-delete se `importo_saldato==0`, altrimenti `importo_previsto=importo_saldato` →
      SALDATA: **mai sotto il saldato**, la cassa non si orfaneggia).
    - **Sotto-copertura** (Σ < residuo): nessuna mutazione — il resto resta "da pianificare".
    - **Pari** (Σ == residuo, es. reopen senza-cassa): no-op (round-trip esatto preservato).

    Non tocca cassa né `residuo()` (modifica solo `importo_previsto`/`stato`/`deleted_at` delle rate; il
    `saldato` resta, quindi anche `totale_versato`/`netto`). Ritorna un riassunto per l'audit.
    """
    residuo = round(cstate.residuo(contract), 2)
    rate = list(session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at == None,
        ).order_by(Rate.data_scadenza, Rate.id)
    ).all())
    somma_residui = round(sum(max((r.importo_previsto or 0) - (r.importo_saldato or 0), 0.0) for r in rate), 2)
    if abs(somma_residui - residuo) <= 0.01:
        # Pari (es. reopen senza-cassa): round-trip esatto preservato.
        return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": 0, "rimosse": 0, "cresciute": 0}

    if somma_residui < residuo - 0.01:
        # SOTTO-COPERTURA. Auto-copertura (scelta founder) LIMITATA al RIMBORSO che resta (re-incassabile):
        # è il SOLO € che il reopen ha aggiunto al residuo e che il piano ripristinato non copre. L'eventuale
        # ammanco oltre il rimborso è "da pianificare" ORIGINALE del trainer → NON lo fabbrichiamo (mai una
        # rata-fantasma su residuo mai pianificato: romperebbe la CONSUNZIONE/storno-puro senza pendenti, dove
        # il residuo torna "da pianificare" com'era). Cresce SOLO una rata pendente ESISTENTE (mirror del
        # taglio cronologico); senza pendenti o senza rimborso → no-op (Fix A lascia aggiungere a mano).
        # Non tocca cassa (solo importo_previsto).
        ammanco = min(round(residuo - somma_residui, 2), round(contract.totale_rimborsato or 0, 2))
        if ammanco > 0.01 and rate:
            last = rate[-1]
            last.importo_previsto = round((last.importo_previsto or 0) + ammanco, 2)
            session.add(last)
            log_audit(session, "rate", last.id, "UPDATE", trainer_id,
                      {"importo_previsto": {"new": last.importo_previsto}, "riallineo": "reopen_cover"})
            return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": 0, "rimosse": 0, "cresciute": 1}
        return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": 0, "rimosse": 0, "cresciute": 0}

    # ECCEDENZA (Σ residui-rata > residuo): taglio cronologico.
    now = datetime.now(timezone.utc)
    coperto = 0.0
    tagliate = 0
    rimosse = 0
    for r in rate:
        saldato = round(r.importo_saldato or 0, 2)
        residuo_rata = round(max((r.importo_previsto or 0) - saldato, 0.0), 2)
        spazio = round(residuo - coperto, 2)  # residuo ancora da coprire col piano
        if spazio <= 0.01:
            # Residuo già coperto → questa rata (e le successive) sono eccedenti.
            if saldato <= 0.01:
                r.deleted_at = now
                session.add(r)
                log_audit(session, "rate", r.id, "DELETE", trainer_id)
                rimosse += 1
            else:
                r.importo_previsto = saldato          # mai sotto il saldato
                r.stato = "SALDATA"
                session.add(r)
                log_audit(session, "rate", r.id, "UPDATE", trainer_id,
                          {"importo_previsto": {"new": saldato}, "riallineo": "reopen"})
                tagliate += 1
        elif residuo_rata > spazio + 0.01:
            # Rata a cavallo: riduci il previsto a coprire l'esatto residuo rimanente.
            nuovo_previsto = round(saldato + spazio, 2)
            r.importo_previsto = nuovo_previsto
            r.stato = "PARZIALE" if saldato > 0.01 else "PENDENTE"
            session.add(r)
            log_audit(session, "rate", r.id, "UPDATE", trainer_id,
                      {"importo_previsto": {"new": nuovo_previsto}, "riallineo": "reopen"})
            tagliate += 1
            coperto = residuo
        else:
            coperto = round(coperto + residuo_rata, 2)
    return {"residuo": residuo, "somma_rate_pre": somma_residui, "tagliate": tagliate, "rimosse": rimosse, "cresciute": 0}


@router.post("/{contract_id}/reopen", response_model=ContractResponse)
def reopen_contract(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Riapre un contratto chiuso (G7.4 → G8.1/ADR-019: **ricalcola-e-instrada, NON-distruttivo**).

    State-driven: porta il contratto allo stato CORRETTO rispetto alla cassa reale, qualunque sia il
    `motivo_chiusura`. È il path esplicito che la reopen-allowlist G7.2 demanda (vs l'auto-riapertura
    credit/payment-driven, bloccata per le chiusure non-COMPLETAMENTO). Copre i muti del runbook G7.6.

    **PRINCIPIO ADR-019 — la cassa mossa non si tocca mai.** A differenza del vecchio "inverso esatto"
    (G7.4/G7.9/G7.10, che soft-cancellava i CashMovement di terminazione scavalcando la protezione del
    mastro e facendo SPARIRE reddito incassato), reopen ora LASCIA FERME le scritture di cassa (fatti
    datati, fiscalmente intoccabili) e RICALCOLA: la cassa di terminazione che resta diventa
    semplicemente pagamento/rimborso sul contratto riaperto, e `residuo()` net-aware (G8.1) la riflette.

    Operazione atomica (UN solo commit):
    A) Bouncer 404 → B) guard `chiuso==True` else 400
    R1) Cassa IMMUTABILE: i `CashMovement` USCITA `RIMBORSO_CONTRATTO` e ENTRATA
        `INCASSO_CONGUAGLIO_CONTRATTO` NON si toccano; `totale_versato`/`totale_rimborsato` invariati.
    R2) Storno inverso: `quota_stornata = 0`.
    R3) Receivable trainer (G7.10): `crediti_terminazione` del contratto → `ANNULLATO` (non-cash). Gli
        eventuali incassi parziali RESTANO (R1) e diventano pagamenti sul contratto.
    R4) Wallet cliente (ADR-020): i `crediti_cliente` di questa terminazione → `ANNULLATO` (G8.1 Step 3).
    R5) Ripristino rate: `deleted_at=None` SOLO sulle rate marcate `chiusa_da_terminazione` (M1, non
        resuscita le cancellate a mano / dal piano rigenerato). Marker azzerato. Le SALDATE intatte (B-3).
    R5-bis) Riallineo piano rate al residuo net-aware (G8.1.1/F2, `_reconcile_rate_plan`): eccedenza
        tagliata cronologicamente, sotto-copertura → "da pianificare". `stato_pagamento` ricalcolato (F4).
    R6) `chiuso=False` + `motivo_chiusura=None` + `data_chiusura=None`.
    R7) Residuo: ricalcolato AUTOMATICAMENTE dal SSoT net-aware (`P − netto − 0`); la cassa che resta
        (rimborso uscito, conguaglio incassato) è già dentro `netto`. Nessuna scrittura.
    G) Audit (cosa resta / cosa si annulla) + transizione `chiuso` (motivo riapertura_esplicita).

    NB: le ancore `totale_versato == Σ ENTRATA` e `totale_rimborsato == Σ USCITA RIMBORSO` reggono
    MEGLIO ora (nulla viene cancellato). Un'eventuale restituzione di denaro è un movimento NUOVO
    esplicito, mai una cancellazione. `stato_pagamento` NON si tocca (coerente col pre-terminazione).
    R8 (rinnovo vivo) è esposto da `GET /reopen-preview`, che il FE usa per avvisare/confermare.
    """
    # A) Bouncer ownership (404 mai 403)
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)

    # B) Guard: solo un contratto chiuso si riapre
    if not contract.chiuso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il contratto non è chiuso")

    old_chiuso = contract.chiuso
    old_motivo = contract.motivo_chiusura
    old_rimborsato = contract.totale_rimborsato or 0
    old_versato = contract.totale_versato or 0
    old_quota = contract.quota_stornata or 0

    # R1) Cassa IMMUTABILE (ADR-019 D-CASSA-IMMUTABILE): NON si soft-cancellano i CashMovement di
    #   terminazione (USCITA RIMBORSO_CONTRATTO, ENTRATA INCASSO_CONGUAGLIO_CONTRATTO) e NON si
    #   decrementano `totale_versato`/`totale_rimborsato`. Restano fatti datati, fiscalmente intoccabili:
    #   il rimborso uscito e il conguaglio incassato diventano rimborso/pagamento sul contratto riaperto,
    #   e il residuo() net-aware (G8.1) li riflette da sé (R7). Le ancore Σ ENTRATA/USCITA reggono.
    #   (Pre-G8.1 qui c'erano le gambe C/C-bis che CANCELLAVANO la cassa — rimosse, ADR-019.)

    # R3) Receivable trainer (G7.10): il differito non-cash si chiude → ANNULLATO. Gli incassi parziali
    #   già registrati (ENTRATA INCASSO_CONGUAGLIO) RESTANO (R1) e contano come pagamento sul contratto.
    crediti_annullati = 0
    open_credits = session.exec(
        select(CreditoTerminazione).where(
            CreditoTerminazione.id_contratto == contract.id,
            CreditoTerminazione.stato != "ANNULLATO",
            CreditoTerminazione.deleted_at == None,
        )
    ).all()
    for cr in open_credits:
        cr.stato = "ANNULLATO"
        cr.data_chiusura = date.today()
        session.add(cr)
        log_audit(session, "credito_terminazione", cr.id, "UPDATE", trainer.id, {
            "stato": {"old": "APERTO/SALDATO", "new": "ANNULLATO"},
        })
        crediti_annullati += 1

    # R4) Wallet cliente (ADR-020): i crediti_cliente di QUESTA terminazione → ANNULLATO. Le erogazioni
    #   parziali già fatte (USCITA, G8.1 Step 4) RESTANO (R1); il credito residuo si riassorbe nel
    #   contratto (il residuo net-aware lo riflette). È l'altra metà del "instrada il credito" (D-INSTRADA).
    wallet_annullati = 0
    open_wallets = session.exec(
        select(CreditoCliente).where(
            CreditoCliente.id_contratto_origine == contract.id,
            CreditoCliente.stato != "ANNULLATO",
            CreditoCliente.deleted_at == None,
        )
    ).all()
    for w in open_wallets:
        w.stato = "ANNULLATO"
        w.data_chiusura = date.today()
        session.add(w)
        log_audit(session, "credito_cliente", w.id, "UPDATE", trainer.id, {
            "stato": {"old": "APERTO/SALDATO", "new": "ANNULLATO"},
        })
        wallet_annullati += 1

    # R2) Storno inverso: azzera la quota → il residuo() net-aware si ricalcola da sé (R7).
    contract.quota_stornata = 0

    # E) Ripristino SOLO le rate marcate da terminate (M1, inverso esatto; le SALDATE non erano toccate, B-3)
    rate_ripristinate = 0
    deleted_rates = session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.stato.in_(["PENDENTE", "PARZIALE"]),
            Rate.deleted_at != None,
            Rate.chiusa_da_terminazione == True,  # M1: SOLO le rate eliminate da QUESTO terminate
        )
    ).all()
    for r in deleted_rates:
        r.deleted_at = None
        r.chiusa_da_terminazione = False  # M1: marker consumato (inverso esatto del terminate)
        session.add(r)
        log_audit(session, "rate", r.id, "RESTORE", trainer.id)
        rate_ripristinate += 1

    # R5-bis) G8.1.1/F2: riallinea il piano rate al residuo() net-aware ricalcolato (la cassa che resta ha
    #   cambiato il residuo → le rate ripristinate AS-IS potrebbero non combaciare). Auto-realign (founder).
    reconcile = _reconcile_rate_plan(session, contract, trainer.id)

    # Ricalcola stato_pagamento net-aware (F4): il reopen ha cambiato il residuo.
    if cstate.is_saldato(contract):
        contract.stato_pagamento = "SALDATO"
    elif (contract.totale_versato or 0) > 0:
        contract.stato_pagamento = "PARZIALE"
    else:
        contract.stato_pagamento = "PENDENTE"

    # F) Riapertura: stato terminale azzerato
    contract.chiuso = False
    contract.motivo_chiusura = None
    contract.data_chiusura = None
    session.add(contract)

    # G) Audit atomico + transizione `chiuso` (la logga log_contract_lifecycle_transition, no doppio).
    #   ADR-019: la cassa resta (rimborso/versato INVARIATI) → si registrano i fatti datati preservati
    #   accanto a ciò che si annulla (storno, receivable, rate ripristinate).
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "motivo_chiusura": {"old": old_motivo, "new": None},
        "chiuso": {"old": True, "new": False},
        "quota_stornata": {"old": old_quota, "new": 0},
        "rate_ripristinate": rate_ripristinate,
        "rate_riallineate": reconcile["tagliate"] + reconcile["rimosse"] + reconcile["cresciute"],  # F2: piano riconciliato al residuo (taglio/crescita)
        "residuo_dopo": reconcile["residuo"],
        "crediti_differiti_annullati": crediti_annullati,
        "wallet_cliente_annullati": wallet_annullati,
        "rimborso_preservato": round(old_rimborsato, 2),        # ADR-019: cassa NON toccata
        "totale_versato_preservato": round(old_versato, 2),
    })
    log_contract_lifecycle_transition(
        session,
        contract,
        old_chiuso=old_chiuso,
        motivo="riapertura_esplicita",
    )
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


@router.get("/{contract_id}/reopen-preview", response_model=ReopenPreview)
def reopen_preview(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Anteprima dell'impatto di una riapertura (G8.1/ADR-019, dry-run): **ZERO scritture**.

    Gemello di settlement-preview per il reopen NON-distruttivo. Mostra cosa RESTA (la cassa di
    terminazione non si cancella → diventa pagamento/rimborso sul contratto) e cosa si ANNULLA
    (storno, receivable, wallet), col residuo ricalcolato net-aware. Segnala un eventuale rinnovo vivo
    a valle (S5) perché il FE proponga la gestione. Bouncer 404; contratto non chiuso → 400.
    """
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)
    if not contract.chiuso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il contratto non è chiuso")

    # residuo dopo la riapertura: la quota verrà azzerata (R2) → residuo() + quota = P − netto (R7).
    residuo_dopo = round(cstate.residuo(contract) + (contract.quota_stornata or 0), 2)
    rimborso_che_resta = round(contract.totale_rimborsato or 0, 2)
    incasso_che_resta = round(sum(
        m.importo for m in session.exec(
            select(CashMovement).where(
                CashMovement.id_contratto == contract.id,
                CashMovement.categoria == CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
                CashMovement.tipo == "ENTRATA",
                CashMovement.deleted_at == None,
            )
        ).all()
    ), 2)
    rate_da_ripristinare = len(session.exec(
        select(Rate).where(
            Rate.id_contratto == contract.id,
            Rate.deleted_at != None,
            Rate.chiusa_da_terminazione == True,
        )
    ).all())
    receivable_da_annullare = len(session.exec(
        select(CreditoTerminazione).where(
            CreditoTerminazione.id_contratto == contract.id,
            CreditoTerminazione.stato != "ANNULLATO",
            CreditoTerminazione.deleted_at == None,
        )
    ).all())
    wallet_da_annullare = len(session.exec(
        select(CreditoCliente).where(
            CreditoCliente.id_contratto_origine == contract.id,
            CreditoCliente.stato != "ANNULLATO",
            CreditoCliente.deleted_at == None,
        )
    ).all())
    # R8: rinnovo vivo a valle (figlio rinnovo_di ancora aperto). G8.1 PROPONE, non agisce (D-PROPONE).
    rinnovo_vivo = session.exec(
        select(Contract).where(
            Contract.rinnovo_di == contract.id,
            Contract.chiuso == False,
            Contract.deleted_at == None,
        )
    ).first()

    parti: list[str] = []
    if rimborso_che_resta > 0.009:
        parti.append(f"il rimborso di €{rimborso_che_resta:.2f} già erogato resta (diventa rimborso sul contratto)")
    if incasso_che_resta > 0.009:
        parti.append(f"l'incasso di conguaglio di €{incasso_che_resta:.2f} resta (diventa pagamento)")
    if rate_da_ripristinare:
        parti.append(f"{rate_da_ripristinare} rate tornano attive")
    if receivable_da_annullare:
        parti.append(f"{receivable_da_annullare} crediti differiti vengono annullati")
    if wallet_da_annullare:
        parti.append(f"{wallet_da_annullare} crediti a wallet del cliente vengono annullati")
    dettaglio = "; ".join(parti) if parti else "nessuna cassa da preservare"
    messaggio = (
        f"Riaprendo, la cassa registrata NON viene cancellata: {dettaglio}. "
        f"Il residuo si ricalcola a €{residuo_dopo:.2f}."
    )
    if rinnovo_vivo is not None:
        messaggio += (
            f" ATTENZIONE: esiste un rinnovo ancora attivo (contratto #{rinnovo_vivo.id}); "
            f"verifica se va gestito prima di procedere."
        )

    return ReopenPreview(
        residuo_dopo=residuo_dopo,
        rimborso_che_resta=rimborso_che_resta,
        incasso_che_resta=incasso_che_resta,
        rate_da_ripristinare=rate_da_ripristinare,
        receivable_da_annullare=receivable_da_annullare,
        wallet_da_annullare=wallet_da_annullare,
        ha_rinnovo_vivo=rinnovo_vivo is not None,
        id_rinnovo_vivo=rinnovo_vivo.id if rinnovo_vivo is not None else None,
        messaggio=messaggio,
    )


# ════════════════════════════════════════════════════════════
# Credito differito post-chiusura (G7.10, ADR-018) — receivable FUORI da residuo()
# ════════════════════════════════════════════════════════════

def _bouncer_credito(session: Session, contract_id: int, credito_id: int, trainer_id: int) -> CreditoTerminazione:
    """Ownership del receivable via la catena id_contratto → Contract.trainer_id (Deep Relational IDOR).
    Non trovato = 404 (mai 403)."""
    credito = session.exec(
        select(CreditoTerminazione)
        .join(Contract, CreditoTerminazione.id_contratto == Contract.id)
        .where(
            CreditoTerminazione.id == credito_id,
            CreditoTerminazione.id_contratto == contract_id,
            Contract.trainer_id == trainer_id,
            CreditoTerminazione.deleted_at == None,
        )
    ).first()
    if not credito:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credito da incassare non trovato")
    return credito


@router.get("/{contract_id}/crediti-terminazione", response_model=list[CreditoTerminazioneResponse])
def list_crediti_terminazione(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Crediti differiti (G7.10) di un contratto — per il dettaglio contratto chiuso con A_CREDITO."""
    _bouncer_contract_owned(session, contract_id, trainer.id)
    rows = session.exec(
        select(CreditoTerminazione)
        .where(
            CreditoTerminazione.id_contratto == contract_id,
            CreditoTerminazione.deleted_at == None,
        )
        .order_by(CreditoTerminazione.data_creazione.desc())
    ).all()
    return [CreditoTerminazioneResponse.model_validate(c) for c in rows]


@router.post("/{contract_id}/crediti-terminazione/{credito_id}/incassa", response_model=CreditoTerminazioneResponse)
def incassa_credito_terminazione(
    contract_id: int,
    credito_id: int,
    data: RatePayment,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Incassa (anche PARZIALE) un credito differito post-chiusura (G7.10). Gemello di G6 ma sul receivable.

    Atomico (UN commit): bouncer 404 → guard stato APERTO 400 → cap `importo ≤ residuo_credito` 422 →
    `CashMovement` ENTRATA `INCASSO_CONGUAGLIO_CONTRATTO` (id_rata=None) + `totale_versato +=` (Strada B) +
    `importo_incassato +=`; a saldo (`importo_incassato == importo`) → `stato=SALDATO`. **Niente
    `_sync_contract_chiuso`**: il contratto resta CHIUSO (terminato, motivo SALDO_TRAINER), residuo()==0
    intatto (`quota_stornata` ha già assorbito il differito → l'incasso non riapre il residuo).
    """
    credito = _bouncer_credito(session, contract_id, credito_id, trainer.id)
    if credito.stato != "APERTO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Il credito non è più aperto (saldato o annullato)")
    residuo_credito = round(max((credito.importo or 0) - (credito.importo_incassato or 0), 0.0), 2)
    if residuo_credito <= 0.009:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Nessun residuo da incassare su questo credito")
    if data.importo <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="L'importo da incassare deve essere positivo")
    if data.importo > residuo_credito + 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Importo ({data.importo:.2f}) supera il residuo del credito ({residuo_credito:.2f})",
        )

    contract = session.get(Contract, contract_id)
    client = session.get(Client, contract.id_cliente)
    client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{contract.id_cliente}"

    old_versato = contract.totale_versato or 0
    movement = CashMovement(
        trainer_id=trainer.id,
        data_effettiva=data.data_pagamento or date.today(),
        tipo="ENTRATA",
        categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
        importo=data.importo,
        metodo=data.metodo,
        id_cliente=contract.id_cliente,
        id_contratto=contract.id,
        id_rata=None,
        note=data.note or f"Incasso credito differito - {client_label}",
    )
    session.add(movement)
    contract.totale_versato = old_versato + data.importo  # Strada B: cresce sul forward
    session.add(contract)

    credito.importo_incassato = round((credito.importo_incassato or 0) + data.importo, 2)
    if credito.importo_incassato >= (credito.importo or 0) - 0.009:
        credito.stato = "SALDATO"
        credito.data_chiusura = data.data_pagamento or date.today()
    session.add(credito)

    session.flush()
    log_audit(session, "movement", movement.id, "CREATE", trainer.id)
    log_audit(session, "credito_terminazione", credito.id, "UPDATE", trainer.id, {
        "importo_incassato": {"old": round((credito.importo_incassato or 0) - data.importo, 2),
                              "new": credito.importo_incassato},
        "stato": credito.stato,
    })
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "totale_versato": {"old": old_versato, "new": contract.totale_versato},
    })
    session.commit()
    session.refresh(credito)
    return CreditoTerminazioneResponse.model_validate(credito)


@router.post("/{contract_id}/crediti-terminazione/{credito_id}/annulla", response_model=CreditoTerminazioneResponse)
def annulla_credito_terminazione(
    contract_id: int,
    credito_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Il trainer rinuncia al residuo NON incassato di un credito differito (G7.10) → `stato=ANNULLATO`.
    Zero cassa: il dovuto era già stornato dal residuo del contratto al `terminate` (e ri-tracciato qui);
    annullare il receivable smette solo di tracciarlo, non muove denaro. Bouncer 404; non-APERTO → 400.
    """
    credito = _bouncer_credito(session, contract_id, credito_id, trainer.id)
    if credito.stato != "APERTO":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Il credito non è più aperto (saldato o già annullato)")
    credito.stato = "ANNULLATO"
    credito.data_chiusura = date.today()
    session.add(credito)
    log_audit(session, "credito_terminazione", credito.id, "UPDATE", trainer.id, {
        "stato": {"old": "APERTO", "new": "ANNULLATO"},
    })
    session.commit()
    session.refresh(credito)
    return CreditoTerminazioneResponse.model_validate(credito)
