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
import logging
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
    ContractReopenResponse,
    OrfanoPeriodoChiusura,
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
    log_contract_open_lifecycle_transition,
)
from api.services import contract_state as cstate
from api.services.financial.invariant_gate import log_invariant_violations
from api.services.financial.transitions import (  # G9.3: TransitionExecutor + helpers settlement + auto-close
    count_sedute_penali,
    count_sedute_prenotate,
    execute_reopen,
    execute_terminate,
    motivo_from_esito,
    reconcile_rate_plan,
    settlement_for,
    sync_contract_chiuso,
)
from api.services.financial.ledger import post_adjustment, post_inflow  # G9.1/G9.2b penne di posting
from api.models.rettifica_contratto import (  # G9.2b: causali del ledger rettifiche (non-cash)
    CAUSALE_REVERSAL_INCASSO_DIFFERITO,
)
from api.services.cash_categories import (
    CATEGORIA_ACCONTO_CONTRATTO,
    CATEGORIA_PAGAMENTO_RATA,
    CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO,
)
from api.services.contract_settlement import SettlementEsito

# Categoria movimento cassa per acconto — SSoT in cash_categories.py
CATEGORIA_ACCONTO = CATEGORIA_ACCONTO_CONTRATTO

router = APIRouter(prefix="/contracts", tags=["contracts"])
logger = logging.getLogger(__name__)


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
    # Proiezione difesa (G8.3/ADR-021, leva A): il residuo() SSoT clampa il piano rate nel read-model —
    # un contratto saldato (residuo ≤ 0.01) NON ha rate scadute, anche se una rata è ancora stale (es. dato
    # pre-riconciliazione). Copre a vista i contratti già stale finché D-RICONCILIA-OVUNQUE non li sana.
    residuo_contratto = cstate.residuo(contract)

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
        # is_scaduta NON può contraddire il residuo() SSoT: su un contratto saldato (residuo ≤ 0.01)
        # nessuna rata è scaduta (proiezione difesa G8.3/ADR-021).
        is_scaduta = r.stato != "SALDATA" and r.data_scadenza < today and residuo_contratto > 0.01
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

    residuo = residuo_contratto  # delega al SSoT (§2.2): byte-identica oggi, load-bearing con G7 (computato sopra)
    percentuale = round((versato / prezzo) * 100) if prezzo > 0 else 0
    # totale_versato e' la fonte di verita' (include acconto + rate + pagamenti legacy)
    importo_da_rateizzare = residuo
    disallineamento = round(importo_da_rateizzare - somma_pendenti, 2)

    # ── Credit breakdown (computed on read) ──
    cb = credit_breakdown or {}
    programmate = cb.get("Programmato", 0)
    completate = cb.get("Completato", 0)
    rinviate = cb.get("Rinviato", 0)  # display only (sedute_rinviate): NON occupa il credito (G7.8)
    penali = sum(cb.get(stato, 0) for stato in cstate.STATI_PENALE)  # G7.8-bis: occupano (penale)
    crediti_totali = contract.crediti_totali or 0
    # [G7.8/ADR-017 + G7.8-bis] occupazione-credito DERIVATA DAL SSoT (penali incluse; Rinviato libera).
    # Era `programmate + completate` a mano: re-implementazione semantica che il literal-grep non vede —
    # da qui in poi somma le chiavi di STATI_OCCUPAZIONE_CREDITO, un solo punto di verità.
    crediti_usati_computed = sum(cb.get(stato, 0) for stato in cstate.STATI_OCCUPAZIONE_CREDITO)

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
        sedute_penali=penali,  # G7.8-bis: display trasparenza (occupano il credito, non sono svolte)
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
            Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
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
            Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
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

    # ── Batch fetch: conteggi PT per (contratto, stato) — 1 query, zero N+1 (G9.7.3) ──
    # Da qui derivano TUTTE le mappe (usati/completate/penali) via SSoT STATI_OCCUPAZIONE_CREDITO:
    # una sola fonte, mai due query che possono divergere (era: occupazione + Completato separate).
    stato_rows = session.exec(
        select(Event.id_contratto, Event.stato, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto, Event.stato)
    ).all()
    credits_used_map: dict[int, int] = {}
    completate_map: dict[int, int] = {}
    penali_map: dict[int, int] = {}
    for cid, stato_ev, n in stato_rows:
        n = int(n)
        if stato_ev in cstate.STATI_OCCUPAZIONE_CREDITO:  # G7.8: Rinviato libera (ADR-017)
            credits_used_map[cid] = credits_used_map.get(cid, 0) + n
        if stato_ev == "Completato":
            completate_map[cid] = completate_map.get(cid, 0) + n
        if stato_ev in cstate.STATI_PENALE:
            penali_map[cid] = penali_map.get(cid, 0) + n

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
            # G9.7.3 (D2/D3/D4): occupazione spiegabile in lista — penali separate dalle svolte,
            # residui dal wire (stessa formula del dettaglio, mai ricalcolo FE)
            sedute_penali=penali_map.get(contract.id, 0),
            crediti_residui=max(0, (contract.crediti_totali or 0) - crediti_usati),
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
    # [G7.8 DISPLAY-EXEMPT — ADR-017 Addendum I, D-DENYLIST-INTATTE] Questo GROUP BY conta
    #   ANCHE i Rinviato → alimenta `sedute_rinviate`
    #   (display). Resta `!= "Cancellato"` di proposito: NON migrarlo a IN('Programmato','Completato'),
    #   manderebbe `sedute_rinviate` a zero in silenzio. La SOMMA crediti_usati (dal SSoT) esclude i
    #   Rinviato; qui NO. Presidio vivo: `test_adr017_rinviato_fuori_occupazione_ma_nel_breakdown`.
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
    # D-LEDGER-SALDO (ADR-019 Add. IV / G8.4 F1.b): il saldo progressivo lo serve il backend —
    # il client non accumula mai denaro (R-SSOT-FE). Convenzione del mastro (ENTRATA +, USCITA −),
    # round 2dp per riga; valido perché la lista è ordinata (data_effettiva, id) e mai filtrata.
    items: list[ContractMovementItem] = []
    saldo = 0.0
    for m in movimenti:
        saldo = round(saldo + (m.importo if m.tipo == "ENTRATA" else -m.importo), 2)
        item = ContractMovementItem.model_validate(m)
        item.saldo_progressivo = saldo
        items.append(item)
    resp.movimenti = items

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
                Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
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
        # Slice C (audit AUDIT_INTEGRITA_RESIDUI_2026-06-29, P3): la cassa preservata è l'informazione più
        # importante del reopen non-distruttivo (ADR-019 D-CASSA-VISIBILE). Derivata dai campi GIÀ emessi dal
        # reopen — `totale_rimborsato.new` (rimborso diretto preservato + erogato wallet riassorbito foldato,
        # D1 forma-d) — non da `rimborso_preservato` (campo che il reopen non emette mai → riga muta).
        rimborsato = changes.get("totale_rimborsato")
        preservato = float(rimborsato.get("new") or 0) if isinstance(rimborsato, dict) else 0.0
        if preservato > 0:
            riassorbito = float(changes.get("wallet_erogato_riassorbito") or 0)
            msg = f"rimborso €{preservato:.2f} preservato"
            if riassorbito > 0:
                msg += f" (di cui €{riassorbito:.2f} da wallet riassorbito)"
            parti.append(msg)
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
    contract = Contract(
        trainer_id=trainer.id,
        id_cliente=data.id_cliente,
        tipo_pacchetto=data.tipo_pacchetto,
        crediti_totali=data.crediti_totali,
        prezzo_totale=data.prezzo_totale,
        data_inizio=data.data_inizio,
        data_scadenza=data.data_scadenza,
        acconto=data.acconto,
        totale_versato=0,   # G9.1c: la penna lo porta ad acconto (sotto); stato_pagamento ricalcolato dopo
        note=data.note,
    )
    session.add(contract)
    session.flush()  # ID del contratto: serve alla penna (acconto) e al suo CashMovement

    # 3. Acconto = PRIMO pagamento, posto via penna unica (G9.1c): CashMovement + totale_versato in UN atto
    #    (post_inflow → I5 per costruzione). data_effettiva: il denaro entra alla firma, non alla data inizio
    #    (backdate-safe: si rispetta data_inizio per i contratti retrodatati, oggi per quelli futuri).
    if data.acconto > 0:
        client = session.get(Client, data.id_cliente)
        client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{data.id_cliente}"
        acconto_date = min(data.data_inizio, date.today())
        post_inflow(
            session, contract=contract, importo=data.acconto, categoria=CATEGORIA_ACCONTO,
            metodo=data.metodo_acconto, data_effettiva=acconto_date, trainer_id=trainer.id,
            id_cliente=data.id_cliente, note=f"Acconto Contratto - {client_label}",
        )

    # stato_pagamento dal SSoT net-aware (G9.1c: collassa la 4ª copia inline `stato_iniziale`) — dopo la penna.
    contract.stato_pagamento = cstate.recompute_stato_pagamento(contract)
    session.add(contract)

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
    RESTRICT 1-2 (obbligazioni pendenti) — skippati se force=True:
    - Rate non saldate (PENDENTE/PARZIALE) -> 409
    - Crediti residui (sedute PT non consumate) -> 409
    RESTRICT 3 (posizione finanziaria aperta) — SEMPRE attivo, force NON lo bypassa (Slice B, P2):
    - Wallet cliente o credito differito APERTO (FUORI da residuo()) -> 409
      (si chiude via eroga/incassa/annulla; una delete lo orfanerebbe + reopen poi impossibile)
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
                    Event.stato.in_(cstate.STATI_OCCUPAZIONE_CREDITO),
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

    # RESTRICT 3 — SEMPRE, anche con force (Slice B, audit AUDIT_INTEGRITA_RESIDUI_2026-06-29 P2): posizione
    # finanziaria APERTA originata da questo contratto. Wallet del cliente (rimborso differito) o credito
    # differito a favore del trainer, entrambi FUORI da residuo(). `force` abbuona rate/crediti-seduta (write-off
    # che il trainer conosce), MAI una posizione con controparte (denaro dovuto a/da il cliente): si chiude via
    # eroga/incassa/annulla, mai con una delete che la orfanerebbe (reopen poi impossibile, bouncer 404).
    # Simmetrico a delete_client (clients.py). Prima il guard viveva solo nel ramo `not force` → buco su force.
    open_wallet = session.exec(
        select(func.count(CreditoCliente.id)).where(
            CreditoCliente.id_contratto_origine == contract_id,
            CreditoCliente.stato == cstate.STATO_CREDITO_APERTO,
            CreditoCliente.deleted_at == None,
        )
    ).one()
    open_receivable = session.exec(
        select(func.count(CreditoTerminazione.id)).where(
            CreditoTerminazione.id_contratto == contract_id,
            CreditoTerminazione.stato == cstate.STATO_CREDITO_APERTO,
            CreditoTerminazione.deleted_at == None,
        )
    ).one()
    if open_wallet > 0 or open_receivable > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Impossibile eliminare: il contratto ha crediti aperti (wallet del cliente o "
                   "credito differito). Gestiscili (eroga/incassa/annulla) prima di eliminare.",
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
    renewed = Contract(
        trainer_id=trainer.id,
        id_cliente=data.id_cliente,
        tipo_pacchetto=data.tipo_pacchetto,
        crediti_totali=data.crediti_totali,
        prezzo_totale=data.prezzo_totale,
        data_inizio=data.data_inizio,
        data_scadenza=data.data_scadenza,
        acconto=data.acconto,
        totale_versato=0,   # G9.1c: la penna lo porta ad acconto (sotto); stato_pagamento ricalcolato dopo
        note=data.note,
        rinnovo_di=contract_id,
    )
    session.add(renewed)
    session.flush()

    # 4. Acconto del rinnovo = primo pagamento, posto via penna unica (G9.1c): movimento + colonna in un atto.
    if data.acconto > 0:
        client = session.get(Client, data.id_cliente)
        client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{data.id_cliente}"
        acconto_date = min(data.data_inizio, date.today())
        post_inflow(
            session, contract=renewed, importo=data.acconto, categoria=CATEGORIA_ACCONTO,
            metodo=data.metodo_acconto, data_effettiva=acconto_date, trainer_id=trainer.id,
            id_cliente=data.id_cliente, note=f"Acconto Rinnovo Contratto - {client_label}",
        )

    # stato_pagamento dal SSoT net-aware (G9.1c: collassa la 4ª copia inline) — dopo la penna.
    renewed.stato_pagamento = cstate.recompute_stato_pagamento(renewed)
    session.add(renewed)

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
    G) Auto-close canonico via `sync_contract_chiuso` unificato (logga la transizione `chiuso`)
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

    # E) Penna unica (G9.1): crea il CashMovement ENTRATA E incrementa totale_versato in UN solo atto
    #    (post_inflow → I5 per costruzione, id_rata=None = incasso diretto); poi stato_pagamento net-aware.
    old_totale_versato = contract.totale_versato
    old_stato_pagamento = contract.stato_pagamento
    client = session.get(Client, contract.id_cliente)
    client_label = f"{client.nome} {client.cognome}" if client else f"Cliente #{contract.id_cliente}"
    post_inflow(
        session, contract=contract, importo=data.importo, categoria=CATEGORIA_PAGAMENTO_RATA,
        metodo=data.metodo, data_effettiva=data.data_pagamento, trainer_id=trainer.id,
        id_cliente=contract.id_cliente, id_rata=None,
        note=data.note or f"Incasso residuo diretto - {client_label}",
    )
    contract.stato_pagamento = cstate.recompute_stato_pagamento(contract)  # SSoT net-aware (F4), de-dup
    session.add(contract)

    # E-bis) D-RICONCILIA-OVUNQUE (G8.3/ADR-021): l'incasso NON-rata ha abbassato il residuo() → il piano
    #   rate va riallineato (INV-RATE: Σ residui-rata ≤ residuo). `_reconcile_rate_plan` taglia l'eventuale
    #   eccedenza (mai sotto il saldato) evitando la rata scaduta-fantasma; no-op se non ci sono rate o il
    #   piano è già ≤ residuo. Stessa funzione del reopen (riconciliazione, non un secondo modello).
    reconcile_rate_plan(session, contract, trainer.id)

    # G) Auto-close canonico (date-independent): se saldato + crediti esauriti → chiuso.
    #    Riusa l'helper SSoT condiviso con agenda/pay_rate (no 3ª copia inline) — logga
    #    da sé la transizione `chiuso` con motivo "completamento".
    sync_contract_chiuso(session, contract.id)

    # H) Audit + commit atomico. La transizione `chiuso` è già loggata da G (P2):
    #    qui si registra solo l'UPDATE denaro, identico a pay_rate (no doppio log).
    log_audit(session, "contract", contract.id, "UPDATE", trainer.id, {
        "totale_versato": {"old": old_totale_versato, "new": contract.totale_versato},
        "stato_pagamento": {"old": old_stato_pagamento, "new": contract.stato_pagamento},
    })
    # G9.0a (ADR-022): osserva gli invarianti (log-only) dopo l'incasso residuo. Atteso pulito.
    log_invariant_violations(session, contract, motivo="incassa_residuo")
    session.commit()
    session.refresh(contract)

    return _to_response(contract)


# ════════════════════════════════════════════════════════════
# Terminazione anticipata (G7.3) — conguaglio + atto atomico a 2 gambe
# ════════════════════════════════════════════════════════════

def _build_settlement_preview(contract: Contract, settlement, sedute_prenotate: int = 0,
                              sedute_penali: int = 0) -> ContractSettlementPreview:
    """Compone la preview leggibile dal conguaglio (ADR-018). Framing di PROPOSTA (§0/§4): mai
    "obbligo legale", sempre "calcolato col metodo standard, verifica con le condizioni del contratto"."""
    cliente = settlement.esito == SettlementEsito.CREDITO_CLIENTE
    trainer_credit = settlement.esito == SettlementEsito.CREDITO_TRAINER
    storno = settlement.residuo_pre > 0.009
    azioni_permesse: list[str] = []
    azione_consigliata: str | None = None
    if cliente:
        msg = f"Conguaglio calcolato (pro-rata sedute): risulta un rimborso di €{settlement.credito_cliente:.2f} a favore del cliente."
        if storno:
            msg += f" Il residuo di €{settlement.residuo_pre:.2f} per le sedute non erogate viene azzerato."
    elif trainer_credit:
        azioni_permesse = sorted(VALID_AZIONI_CREDITO_TRAINER)
        # F3.c (G8.4): advisory — l'opzione che tutela il trainer. MAI la rinuncia. Non cambia
        # il gate 422 (la scelta resta esplicita, ADR-018 D-SCELTA).
        azione_consigliata = "INCASSA_ORA"
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
        motivo_chiusura=motivo_from_esito(settlement.esito),
        valore_servizio_reso=settlement.valore_servizio_reso,
        conguaglio=settlement.conguaglio,
        importo_rimborso=settlement.credito_cliente,
        credito_trainer=settlement.credito_trainer,
        quota_da_stornare=settlement.residuo_pre,
        sedute_erogate=settlement.sedute_erogate,
        sedute_totali=contract.crediti_totali,
        sedute_prenotate=sedute_prenotate,
        sedute_penali=sedute_penali,
        metodo_rimborso_richiesto=cliente,
        azioni_permesse=azioni_permesse,
        azione_consigliata=azione_consigliata,
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
        settlement_for(session, contract),
        count_sedute_prenotate(session, contract.id),  # D2: solo display, query separata dal conguaglio
        count_sedute_penali(session, contract.id),     # G7.8-bis: trasparenza (entrano nel contabilizzato)
    )


@router.post("/{contract_id}/terminate", response_model=ContractResponse)
def terminate_contract(
    contract_id: int,
    data: ContractTerminate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Terminazione anticipata (G7.3 + ADR-018 + ADR-022/G9.3): il corpo vive nel TransitionExecutor
    `transitions.execute_terminate` (conguaglio balance-based, gamba d'azione 3-vie, storno via terza
    penna, soft-delete rate non-saldate, stato terminale diretto, audit, sensore, commit atomico).
    Qui restano SOLO bouncer + delega + serialize (AC-G93-1).
    """
    # A) Bouncer ownership (404 mai 403) — routing concern, resta nel router (D-C2)
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)
    contract = execute_terminate(session, contract=contract, data=data, trainer=trainer)
    return _to_response(contract)


def _orfani_periodo_chiusura(session: Session, contract: Contract) -> list[OrfanoPeriodoChiusura]:
    """G9.7.2/B2-B3: PT orfani del cliente creati nel periodo di chiusura (`data_creazione ≥
    data_chiusura`). Il reopen li PROPONE al recupero (D-PROPONE) — mai riaggancio automatico:
    la via esplicita è `POST /events/{id}/assegna-contratto`."""
    if not contract.data_chiusura or not contract.id_cliente:
        return []
    soglia = datetime.combine(contract.data_chiusura, datetime.min.time())
    events = session.exec(
        select(Event).where(
            Event.trainer_id == contract.trainer_id,
            Event.id_cliente == contract.id_cliente,
            Event.categoria == "PT",
            Event.id_contratto == None,
            Event.deleted_at == None,
            Event.data_creazione >= soglia,
        ).order_by(Event.data_inizio.asc())
    ).all()
    return [
        OrfanoPeriodoChiusura(
            id=e.id,
            titolo=e.titolo,
            data_inizio=e.data_inizio.isoformat() if isinstance(e.data_inizio, datetime) else str(e.data_inizio),
            stato=e.stato,
        )
        for e in events
    ]


@router.post("/{contract_id}/reopen", response_model=ContractReopenResponse)
def reopen_contract(
    contract_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Riapre un contratto chiuso (G7.4 → ADR-019 → ADR-022/G9.3): il corpo vive nel TransitionExecutor
    `transitions.execute_reopen` (ricalcola-e-instrada NON-distruttivo: cassa immutabile, storno
    revertito via terza penna, receivable/wallet annullati, fold R2-bis, rate ripristinate+riconciliate,
    audit, sensore, commit atomico). Qui restano SOLO bouncer + delega + serialize (AC-G93-1).

    G9.7.2/B3: la response PROPONE gli eventuali PT orfani nati nel periodo di chiusura
    (snapshot PRIMA del reopen: la riapertura azzera `data_chiusura`) — mai riaggancio automatico.
    """
    # A) Bouncer ownership (404 mai 403) — routing concern, resta nel router (D-C2)
    contract = _bouncer_contract_owned(session, contract_id, trainer.id)
    orfani = _orfani_periodo_chiusura(session, contract)  # snapshot pre-reopen (B3)
    contract = execute_reopen(session, contract=contract, trainer=trainer)
    base = _to_response(contract)
    return ContractReopenResponse(
        **base.model_dump(),
        orfani_periodo_chiusura=orfani,
    )


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

    # Wallet vivi della terminazione: alla riapertura l'erogato RIENTRA nella posizione (D1 forma-d, fold
    # R2-bis), mentre il residuo del wallet si annulla. Calcolato qui per residuo_dopo + messaggio esplicito.
    open_wallets = session.exec(
        select(CreditoCliente).where(
            CreditoCliente.id_contratto_origine == contract.id,
            CreditoCliente.stato != cstate.STATO_CREDITO_ANNULLATO,
            CreditoCliente.deleted_at == None,
        )
    ).all()
    wallet_da_annullare = len(open_wallets)
    wallet_erogato_riassorbito = round(sum(w.importo_erogato or 0 for w in open_wallets), 2)

    # residuo dopo la riapertura: quota azzerata (R2) + erogato wallet riassorbito (R2-bis) → P − netto (R7).
    residuo_dopo = round(
        cstate.residuo(contract) + (contract.quota_stornata or 0) + wallet_erogato_riassorbito, 2
    )
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
            CreditoTerminazione.stato != cstate.STATO_CREDITO_ANNULLATO,
            CreditoTerminazione.deleted_at == None,
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
    if wallet_erogato_riassorbito > 0.009:
        # D1 forma-d: mai silenzioso — l'erogato torna dovuto sul contratto (chiude Bug-1).
        parti.append(
            f"il cliente risulta aver già riavuto €{wallet_erogato_riassorbito:.2f} dal wallet, "
            f"che torna dovuto sul contratto riaperto"
        )
    # G9.7.2/B2: PT orfani del cliente nati nel periodo di chiusura — il preview li PROPONE
    # al recupero (D-PROPONE), il riaggancio resta un atto esplicito post-riapertura.
    orfani = _orfani_periodo_chiusura(session, contract)

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
    if orfani:
        n = len(orfani)
        messaggio += (
            f" Nel periodo di chiusura {'è nata' if n == 1 else 'sono nate'} {n} "
            f"{'seduta PT senza contratto' if n == 1 else 'sedute PT senza contratto'}: "
            f"dopo la riapertura potrai assegnarle dal dettaglio evento."
        )

    return ReopenPreview(
        residuo_dopo=residuo_dopo,
        rimborso_che_resta=rimborso_che_resta,
        incasso_che_resta=incasso_che_resta,
        rate_da_ripristinare=rate_da_ripristinare,
        receivable_da_annullare=receivable_da_annullare,
        wallet_da_annullare=wallet_da_annullare,
        wallet_erogato_riassorbito=wallet_erogato_riassorbito,
        ha_rinnovo_vivo=rinnovo_vivo is not None,
        id_rinnovo_vivo=rinnovo_vivo.id if rinnovo_vivo is not None else None,
        orfani_periodo_chiusura=orfani,
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
    `_sync_contract_chiuso`**: il contratto resta CHIUSO (terminato, motivo SALDO_TRAINER). residuo()==0
    resta intatto perché l'incasso REVERTE lo storno provvisorio (`quota_stornata −= importo`) mentre
    `totale_versato +=`: i due si compensano (Reperto #1 G9.0, chiude I1 residuo_raw<0; corregge reopen-preview).
    """
    credito = _bouncer_credito(session, contract_id, credito_id, trainer.id)
    if credito.stato != cstate.STATO_CREDITO_APERTO:
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
    movement = post_inflow(  # penna unica (G9.1): ENTRATA + totale_versato += in UN atto
        session, contract=contract, importo=data.importo,
        categoria=CATEGORIA_INCASSO_CONGUAGLIO_CONTRATTO, metodo=data.metodo,
        data_effettiva=data.data_pagamento or date.today(), trainer_id=trainer.id,
        id_cliente=contract.id_cliente, id_rata=None,
        note=data.note or f"Incasso credito differito - {client_label}",
    )  # totale_versato += data.importo (== old_versato + data.importo; Strada B)
    # Reperto #1 fix (G9.0): l'incasso REVERTE lo storno PROVVISORIO di pari importo. Al terminate A_CREDITO
    # `quota_stornata` assorbì l'INTERO `residuo_pre` (per forzare residuo()==0 su CHIUSO), inclusa la parte
    # differita (`credito_trainer`) che NON era un write-off ma un differimento. Incassandola torna ricavo
    # (versato +=) e va tolta dallo storno → la quota converge a `quota_non_erogata` (P−R). Tiene residuo()==0
    # (il + su versato e il − su quota si compensano) e azzera residuo_raw (chiude I1).
    # DEC-1 (G9.2b): NESSUN clamp max(·,0) — un floor sulla colonna ma non sul Σ rettifiche romperebbe
    # l'àncora quota == Σ. Il clamp era comunque irraggiungibile (old_quota ≥ credito_trainer ≥ Σ incassi,
    # cap sopra); uno stato corrotto ora diventa RUMOROSO (I4/I1 log-only, 409 in G9.4), non mascherato.
    # MAI ripristinare il floor qui.
    old_quota = contract.quota_stornata or 0
    post_adjustment(
        session, contract=contract, importo_firmato=-data.importo,
        causale=CAUSALE_REVERSAL_INCASSO_DIFFERITO,
        data_effettiva=data.data_pagamento or date.today(), trainer_id=trainer.id,
    )

    credito.importo_incassato = round((credito.importo_incassato or 0) + data.importo, 2)
    if credito.importo_incassato >= (credito.importo or 0) - 0.009:
        credito.stato = cstate.STATO_CREDITO_SALDATO
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
        "quota_stornata": {"old": old_quota, "new": contract.quota_stornata},  # Reperto #1: storno provvisorio revertito
    })
    # G9.0a (ADR-022): osserva gli invarianti (log-only). Reperto #1 RISOLTO sopra (lo storno provvisorio è
    # revertito all'incasso → residuo_raw==0, I1 non scatta più); il sensore resta come sentinella.
    log_invariant_violations(session, contract, motivo="incassa_credito_differito")
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
    if credito.stato != cstate.STATO_CREDITO_APERTO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Il credito non è più aperto (saldato o già annullato)")
    credito.stato = cstate.STATO_CREDITO_ANNULLATO
    credito.data_chiusura = date.today()
    session.add(credito)
    log_audit(session, "credito_terminazione", credito.id, "UPDATE", trainer.id, {
        "stato": {"old": cstate.STATO_CREDITO_APERTO, "new": cstate.STATO_CREDITO_ANNULLATO},
    })
    session.commit()
    session.refresh(credito)
    return CreditoTerminazioneResponse.model_validate(credito)
