# api/routers/agenda.py
"""
Endpoint Agenda — gestione eventi e sessioni.

Sicurezza multi-tenant a 2 livelli:
1. trainer_id diretto: ogni evento ha trainer_id = trainer autenticato
2. Relational IDOR: se l'evento ha id_cliente, verifica che il cliente
   appartenga al trainer (clienti.trainer_id == trainer.id)

Regola 404: se l'evento non esiste O non appartiene al trainer -> 404.
Mai 403, mai rivelare l'esistenza di dati altrui.

Validazioni:
- data_fine > data_inizio (model_validator)
- durata massima 4 ore
- categoria in SessionCategory enum
- Conflict Prevention: no sovrapposizioni temporali per lo stesso trainer
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func
from pydantic import BaseModel, Field, field_validator, model_validator

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.event import Event
from api.models.client import Client
from api.models.contract import Contract
from api.routers._audit import log_audit
from api.services.financial.transitions import puo_auto_riaprire, sync_contract_chiuso
from api.services.contract_state import (
    STATI_OCCUPAZIONE_CREDITO,
    STATI_OCCUPAZIONE_SLOT,
    STATI_SERVIZIO_CONTABILIZZATO,
)

router = APIRouter(prefix="/events", tags=["events"])

# Categorie valide (mirror di core/constants.py SessionCategory)
VALID_CATEGORIES = {"PT", "SALA", "CORSO", "COLLOQUIO", "PERSONALE"}

# Stati validi (mirror di core/constants.py EventStatus)
VALID_STATUSES = {"Programmato", "Completato", "Cancellato", "Rinviato", "Cancellato_Tardivo", "No_Show"}  # G7.8-bis: stati-penale (ADR-017 Add. I)


# --- Input schemas ---
# SICUREZZA: nessun campo trainer_id. Il trainer viene dal JWT token.

class EventCreate(BaseModel):
    """
    Schema per creazione evento via API.

    trainer_id e' ASSENTE: viene iniettato dall'endpoint.
    id_cliente e' opzionale: eventi generici (SALA, CORSO) non hanno cliente.
    id_contratto e' opzionale: gestito server-side con logica FIFO crediti.

    Validazioni temporali:
    - data_fine deve essere strettamente maggiore di data_inizio
    - durata massima 4 ore (coerente con core/models.py)
    """
    model_config = {"extra": "forbid"}

    data_inizio: datetime
    data_fine: datetime
    categoria: str
    titolo: str = Field(min_length=1, max_length=200)
    id_cliente: Optional[int] = Field(None, gt=0)
    id_contratto: Optional[int] = Field(None, gt=0)
    stato: str = Field(default="Programmato")
    note: Optional[str] = Field(None, max_length=500)

    @field_validator("categoria")
    @classmethod
    def validate_categoria(cls, v: str) -> str:
        normalized = v.upper()
        if normalized not in VALID_CATEGORIES:
            raise ValueError(f"Categoria non valida. Ammesse: {', '.join(sorted(VALID_CATEGORIES))}")
        return normalized

    @field_validator("stato")
    @classmethod
    def validate_stato(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Stato non valido. Ammessi: {', '.join(sorted(VALID_STATUSES))}")
        return v

    @model_validator(mode="after")
    def validate_temporal(self):
        """data_fine deve essere strettamente dopo data_inizio, max 12 ore."""
        if self.data_fine <= self.data_inizio:
            raise ValueError("data_fine deve essere dopo data_inizio")
        duration_hours = (self.data_fine - self.data_inizio).total_seconds() / 3600
        if duration_hours > 12:
            raise ValueError("La durata massima di un evento e' 12 ore")
        return self


class EventAssignContract(BaseModel):
    """
    G9.7.2 (ADR-024 D-RECUPERO-ESPLICITO): input dell'UNICA via di re-parenting per i PT orfani.
    L'`EventUpdate` generico resta chiuso su `id_contratto` (fence ADR-023 intatto).
    """
    model_config = {"extra": "forbid"}

    id_contratto: int = Field(gt=0)


class EventUpdate(BaseModel):
    """
    Schema per update evento via API (partial update).

    Campi modificabili: data_inizio, data_fine, titolo, note, stato.
    NON modificabili via update: categoria, id_cliente, id_contratto, trainer_id.
    Coerente con AgendaRepository.update_event() che aggiorna solo scheduling.
    """
    model_config = {"extra": "forbid"}

    data_inizio: Optional[datetime] = None
    data_fine: Optional[datetime] = None
    titolo: Optional[str] = Field(None, min_length=1, max_length=200)
    note: Optional[str] = Field(None, max_length=500)
    stato: Optional[str] = None

    @field_validator("stato")
    @classmethod
    def validate_stato(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"Stato non valido. Ammessi: {', '.join(sorted(VALID_STATUSES))}")
        return v

    @model_validator(mode="after")
    def validate_temporal(self):
        """Se entrambe le date sono fornite, verifica coerenza temporale."""
        if self.data_inizio is not None and self.data_fine is not None:
            if self.data_fine <= self.data_inizio:
                raise ValueError("data_fine deve essere dopo data_inizio")
            duration_hours = (self.data_fine - self.data_inizio).total_seconds() / 3600
            if duration_hours > 12:
                raise ValueError("La durata massima di un evento e' 12 ore")
        return self


# --- Response schemas ---

class EventResponse(BaseModel):
    """Dati evento restituiti dall'API. Include nome cliente per eventi PT."""
    id: int
    data_inizio: str
    data_fine: str
    categoria: str
    titolo: Optional[str] = None
    id_cliente: Optional[int] = None
    id_contratto: Optional[int] = None
    stato: str
    note: Optional[str] = None
    cliente_nome: Optional[str] = None
    cliente_cognome: Optional[str] = None
    cliente_telefono: Optional[str] = None


class EventListResponse(BaseModel):
    """Risposta paginata per lista eventi."""
    items: List[EventResponse]
    total: int


# --- Bouncer helpers (early return functions) ---

def _check_client_ownership(
    session: Session, client_id: int, trainer_id: int
) -> None:
    """
    Relational IDOR: verifica che il cliente appartenga al trainer.

    Se il cliente non esiste O appartiene a un altro trainer -> 404.
    Mai rivelare l'esistenza di clienti altrui.
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


def _check_overlap(
    session: Session,
    trainer_id: int,
    data_inizio: datetime,
    data_fine: datetime,
    exclude_event_id: int | None = None,
) -> None:
    """
    Anti-Overlapping: verifica che il trainer non abbia eventi sovrapposti.

    Condizione di sovrapposizione:
        existing.data_inizio < new.data_fine AND existing.data_fine > new.data_inizio

    Per PUT: exclude_event_id esclude l'evento corrente dal check.
    Se c'e' sovrapposizione -> 409 Conflict.
    """
    query = select(Event).where(
        Event.trainer_id == trainer_id,
        Event.data_inizio < data_fine,
        Event.data_fine > data_inizio,
        # G7.8/§3-bis + G7.8-bis D-CALENDAR-OVERLAP: Rinviato E le penali liberano lo slot →
        # riprenotabile. Asse CALENDARIO ≠ asse credito (le penali occupano il credito, non lo slot).
        Event.stato.in_(STATI_OCCUPAZIONE_SLOT),
        Event.deleted_at == None,
    )

    if exclude_event_id is not None:
        query = query.where(Event.id != exclude_event_id)

    conflict = session.exec(query).first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Sovrapposizione con evento id={conflict.id} "
                   f"({conflict.data_inizio} - {conflict.data_fine}, {conflict.categoria})",
        )


def _load_client_names_batch(
    session: Session, client_ids: set[int]
) -> Dict[int, Tuple[str, str, Optional[str]]]:
    """Batch load client info. Returns {id: (nome, cognome, telefono)}. Zero N+1."""
    if not client_ids:
        return {}
    rows = session.exec(
        select(Client.id, Client.nome, Client.cognome, Client.telefono)
        .where(Client.id.in_(list(client_ids)))
    ).all()
    return {r[0]: (r[1], r[2], r[3]) for r in rows}


def _to_response(
    event: Event,
    cliente_nome: Optional[str] = None,
    cliente_cognome: Optional[str] = None,
    cliente_telefono: Optional[str] = None,
) -> EventResponse:
    """Converte un Event ORM in EventResponse con dati cliente opzionali."""
    return EventResponse(
        id=event.id,
        data_inizio=str(event.data_inizio),
        data_fine=str(event.data_fine),
        categoria=event.categoria,
        titolo=event.titolo,
        id_cliente=event.id_cliente,
        id_contratto=event.id_contratto,
        stato=event.stato,
        note=event.note,
        cliente_nome=cliente_nome,
        cliente_cognome=cliente_cognome,
        cliente_telefono=cliente_telefono,
    )


def _auto_assign_contract(
    session: Session, client_id: int, trainer_id: int
) -> Optional[int]:
    """
    Auto-FIFO: assegna l'evento PT al contratto attivo piu' vecchio
    con crediti residui > 0.

    2 query batch:
    1. Contratti attivi del cliente, ordinati per data_inizio ASC (FIFO)
    2. Conteggio PT events (non cancellati) per contratto

    Returns: contract.id oppure None se nessun contratto ha crediti.
    """
    contracts = session.exec(
        select(Contract).where(
            Contract.id_cliente == client_id,
            Contract.trainer_id == trainer_id,
            Contract.chiuso == False,
            Contract.deleted_at == None,
        ).order_by(Contract.data_inizio.asc())
    ).all()

    if not contracts:
        return None

    # Batch count PT events per contratto (zero N+1)
    contract_ids = [c.id for c in contracts]
    usage_rows = session.exec(
        select(Event.id_contratto, func.count(Event.id))
        .where(
            Event.id_contratto.in_(contract_ids),
            Event.categoria == "PT",
            # G7.8: Rinviato libera il credito (ADR-017)
            Event.stato.in_(STATI_OCCUPAZIONE_CREDITO),
            Event.deleted_at == None,
        )
        .group_by(Event.id_contratto)
    ).all()
    usage_map: Dict[int, int] = {row[0]: int(row[1]) for row in usage_rows}

    # FIFO: primo contratto con crediti residui
    for contract in contracts:
        totali = contract.crediti_totali or 0
        usati = usage_map.get(contract.id, 0)
        if totali - usati > 0:
            return contract.id

    return None


_FENCE_DETAIL = (
    "Contratto terminato: la seduta è entrata nel conguaglio di chiusura e non è modificabile. "
    "Riapri il contratto per correggere la storia, poi termina di nuovo."
)


def _assert_storia_liquidata_intatta(session: Session, event, new_stato: str | None = None) -> None:
    """Temporal fence (G7.8-ter / ADR-023): la base del conguaglio è immutabile su contratto liquidato.

    Blocca (409) la mutazione di un evento quando: l'evento appartiene a un contratto `chiuso` NON
    auto-riapribile (motivo TERMINAZIONE_*/CONSUNZIONE/NULL — riuso della reopen-allowlist G7.2 via
    `puo_auto_riaprire`) E la mutazione tocca la base CONTABILIZZATA (stato di partenza o di arrivo in
    `STATI_SERVIZIO_CONTABILIZZATO` = Completato + penali; per il delete conta lo stato attuale).
    NON blocca la pulizia dei `Programmato` orfani (D-TF-PULIZIA: Programmato→Cancellato/Rinviato,
    delete di non-contabilizzati) né date/titolo/note. Varco unico: POST /reopen (D-TF-VARCO) — dopo,
    la storia torna editabile e la ri-terminazione ricalcola sul corretto."""
    if not event.id_contratto:
        return
    tocca_base = event.stato in STATI_SERVIZIO_CONTABILIZZATO or (
        new_stato is not None and new_stato in STATI_SERVIZIO_CONTABILIZZATO
    )
    if not tocca_base:
        return
    contract = session.get(Contract, event.id_contratto)
    if contract is not None and contract.chiuso and not puo_auto_riaprire(contract):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_FENCE_DETAIL)


def _sync_contract_chiuso(session: Session, contract_id: int) -> None:
    """Alias deprecato (G9.3d): delega alla transizione UNIFICATA `transitions.sync_contract_chiuso`
    (bidirezionale, reopen_motivo="riapertura_crediti" — il trigger di agenda è credit-driven).
    Tenuto per i 3 call-site di agenda; i nuovi consumer importino direttamente da transitions."""
    sync_contract_chiuso(session, contract_id)


# --- Endpoints ---

@router.get("", response_model=EventListResponse)
def list_events(
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    start: Optional[str] = Query(None, description="Inizio range ISO (YYYY-MM-DD o datetime)"),
    end: Optional[str] = Query(None, description="Fine range ISO (YYYY-MM-DD o datetime)"),
    categoria: Optional[str] = Query(None, description="Filtra per categoria (PT, SALA, ...)"),
    stato: Optional[str] = Query(None, description="Filtra per stato (Programmato, Completato, ...)"),
    id_cliente: Optional[int] = Query(None, description="Filtra per cliente"),
    id_contratto: Optional[int] = Query(None, description="Filtra per contratto"),
):
    """
    Lista eventi del trainer autenticato.

    Supporta filtri per range temporale, categoria, stato, cliente, contratto.
    Nessuna paginazione: il calendario ha bisogno di tutti gli eventi nel range.
    """
    query = select(Event).where(Event.trainer_id == trainer.id, Event.deleted_at == None)

    if start:
        query = query.where(Event.data_inizio >= start)
    if end:
        query = query.where(Event.data_fine <= end)
    if categoria:
        query = query.where(Event.categoria == categoria.upper())
    if stato:
        query = query.where(Event.stato == stato)
    if id_cliente:
        _check_client_ownership(session, id_cliente, trainer.id)
        query = query.where(Event.id_cliente == id_cliente)
    if id_contratto:
        query = query.where(Event.id_contratto == id_contratto)

    query = query.order_by(Event.data_inizio)
    events = session.exec(query).all()

    # Batch load client names (1 query aggiuntiva, zero N+1)
    client_ids = {e.id_cliente for e in events if e.id_cliente}
    client_names = _load_client_names_batch(session, client_ids)

    def _names(cid: Optional[int]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not cid:
            return (None, None, None)
        return client_names.get(cid, (None, None, None))

    return EventListResponse(
        items=[
            _to_response(e, *_names(e.id_cliente))
            for e in events
        ],
        total=len(events),
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Dettaglio evento. Bouncer: trainer_id filter."""
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    names = _load_client_names_batch(session, {event.id_cliente} if event.id_cliente else set())
    nome, cognome, telefono = names.get(event.id_cliente, (None, None, None)) if event.id_cliente else (None, None, None)

    return _to_response(event, nome, cognome, telefono)


# --- POST: Crea evento ---

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Crea un nuovo evento per il trainer autenticato.

    Bouncer chain (early returns):
    1. Se id_cliente fornito -> verifica ownership (Relational IDOR)
    2. Check sovrapposizione temporale -> 409 se conflitto
    3. Salva con trainer_id iniettato dal JWT
    """
    # Bouncer 1: Relational IDOR — il cliente e' mio?
    if data.id_cliente:
        _check_client_ownership(session, data.id_cliente, trainer.id)

    # Bouncer 2: Validazione id_contratto esplicito (ownership + chiuso)
    if data.id_contratto:
        contract = session.exec(
            select(Contract).where(
                Contract.id == data.id_contratto,
                Contract.trainer_id == trainer.id,
                Contract.deleted_at == None,
            )
        ).first()
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contratto non trovato",
            )
        if contract.chiuso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossibile assegnare eventi a un contratto chiuso",
            )

        # Bouncer 2b: Cross-validation cliente ↔ contratto
        if data.id_cliente and contract.id_cliente != data.id_cliente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Il contratto non appartiene al cliente selezionato",
            )

        # Bouncer 2c: Credit guard — crediti esauriti?
        if contract.crediti_totali and contract.crediti_totali > 0:
            crediti_usati = session.exec(
                select(func.count(Event.id)).where(
                    Event.id_contratto == contract.id,
                    Event.categoria == "PT",
                    # G7.8: Rinviato libera il credito (ADR-017) → riprenotabile (D-GUARD)
                    Event.stato.in_(STATI_OCCUPAZIONE_CREDITO),
                    Event.deleted_at == None,
                )
            ).one()
            if crediti_usati >= contract.crediti_totali:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Crediti esauriti per questo contratto",
                )

    # Bouncer 3: Anti-Overlapping — ho gia' un evento in questo slot?
    _check_overlap(session, trainer.id, data.data_inizio, data.data_fine)

    # Auto-FIFO: assegna contratto per eventi PT senza contratto esplicito
    assigned_contract_id = data.id_contratto
    if data.categoria == "PT" and data.id_cliente and not data.id_contratto:
        assigned_contract_id = _auto_assign_contract(
            session, data.id_cliente, trainer.id
        )

    # Tutto ok: salva
    event = Event(
        trainer_id=trainer.id,
        data_inizio=data.data_inizio,
        data_fine=data.data_fine,
        categoria=data.categoria,
        titolo=data.titolo,
        id_cliente=data.id_cliente,
        id_contratto=assigned_contract_id,
        stato=data.stato,
        note=data.note,
    )
    session.add(event)
    session.flush()
    log_audit(session, "event", event.id, "CREATE", trainer.id)

    # Auto-close: se evento PT con contratto, verifica crediti esauriti + saldato
    if event.categoria == "PT" and event.id_contratto:
        _sync_contract_chiuso(session, event.id_contratto)

    session.commit()
    session.refresh(event)

    names = _load_client_names_batch(session, {event.id_cliente} if event.id_cliente else set())
    nome, cognome, telefono = names.get(event.id_cliente, (None, None, None)) if event.id_cliente else (None, None, None)

    return _to_response(event, nome, cognome, telefono)


# --- POST: Assegna contratto a un PT orfano (G9.7.2) ---

@router.post("/{event_id}/assegna-contratto", response_model=EventResponse)
def assegna_contratto(
    event_id: int,
    data: EventAssignContract,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    G9.7.2 (ADR-024 D-RECUPERO-ESPLICITO) — recupero esplicito del PT orfano: l'UNICA via di
    re-parenting (l'`EventUpdate` generico resta chiuso su `id_contratto`, fence ADR-023 intatto).

    Guard chain: bouncer evento 404 → solo PT (400) → solo orfani (400: mai ri-agganciare) →
    contratto: ownership+stesso cliente (404, mai rivelare) → aperto (400) → credit-guard (400,
    solo se lo stato dell'evento OCCUPA credito). Audit UPDATE + auto-close canonico via
    `_sync_contract_chiuso` (i crediti usati salgono) in UN solo commit.

    Guard CP-2 (ADR-025/blocco P, birth-review P0): quando nascerà `prestazioni_singole` (P1),
    QUI entrerà il rifiuto degli eventi CON prestazione singola — le due vie di recupero
    (assegna / promuovi) sono mutuamente esclusive, mai doppio fatto economico.
    """
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    if event.categoria != "PT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo le sedute PT possono essere assegnate a un contratto",
        )
    if event.id_contratto is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'evento è già agganciato a un contratto (il re-parenting non è permesso)",
        )
    if not event.id_cliente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'evento non ha un cliente: assegna prima il cliente ricreando la seduta",
        )

    contract = session.exec(
        select(Contract).where(
            Contract.id == data.id_contratto,
            Contract.trainer_id == trainer.id,
            Contract.deleted_at == None,
        )
    ).first()
    # Cliente diverso → 404 come il non-trovato (mai rivelare l'esistenza di contratti altrui)
    if not contract or contract.id_cliente != event.id_cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contratto non trovato")
    if contract.chiuso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile assegnare eventi a un contratto chiuso",
        )

    # Credit-guard (come create_event): SOLO se lo stato dell'evento occupa credito — assegnare
    # un Rinviato/Cancellato non consuma nulla (ADR-017).
    if event.stato in STATI_OCCUPAZIONE_CREDITO and contract.crediti_totali and contract.crediti_totali > 0:
        crediti_usati = session.exec(
            select(func.count(Event.id)).where(
                Event.id_contratto == contract.id,
                Event.categoria == "PT",
                Event.stato.in_(STATI_OCCUPAZIONE_CREDITO),
                Event.deleted_at == None,
            )
        ).one()
        if crediti_usati >= contract.crediti_totali:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Crediti esauriti per questo contratto",
            )

    event.id_contratto = contract.id
    session.add(event)
    log_audit(
        session, "event", event.id, "UPDATE", trainer.id,
        changes={"id_contratto": {"old": None, "new": contract.id}, "azione": "assegna_contratto_orfano"},
    )
    # I crediti usati salgono → il contratto può auto-chiudersi (regola #4: MAI toccare
    # crediti_usati senza _sync_contract_chiuso)
    _sync_contract_chiuso(session, contract.id)
    session.commit()
    session.refresh(event)

    names = _load_client_names_batch(session, {event.id_cliente})
    nome, cognome, telefono = names.get(event.id_cliente, (None, None, None))
    return _to_response(event, nome, cognome, telefono)


# --- PUT: Aggiorna evento (partial update) ---

@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    data: EventUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Aggiorna un evento esistente (scheduling only).

    Bouncer chain (early returns):
    1. Verifica ownership trainer_id -> 404 se non mio
    2. Se date cambiate -> verifica coerenza temporale con date esistenti
    3. Check sovrapposizione (escludendo se' stesso) -> 409 se conflitto
    4. Applica partial update
    """
    # Bouncer 1: l'evento e' mio? (non eliminato)
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    # Calcola date effettive (merge tra esistenti e nuove)
    new_inizio = data.data_inizio if data.data_inizio is not None else event.data_inizio
    new_fine = data.data_fine if data.data_fine is not None else event.data_fine

    # Bouncer 2: validazione temporale cross-field (una sola data fornita)
    if new_fine <= new_inizio:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_fine deve essere dopo data_inizio",
        )
    duration_hours = (new_fine - new_inizio).total_seconds() / 3600
    if duration_hours > 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La durata massima di un evento e' 12 ore",
        )

    # Bouncer 3: Anti-Overlapping (se le date sono cambiate)
    dates_changed = data.data_inizio is not None or data.data_fine is not None
    if dates_changed:
        _check_overlap(session, trainer.id, new_inizio, new_fine, exclude_event_id=event_id)

    # Tutto ok: applica partial update
    update_data = data.model_dump(exclude_unset=True)

    # Bouncer 4 (G7.8/ADR-017, decisione di dominio): una seduta GIÀ SVOLTA non si rinvia. "Rinviare"
    #   pospone una seduta NON ancora svolta; Completato→Rinviato libererebbe credito E valore (l'unica
    #   transizione che muoverebbe l'asse denaro, fuori dalla tesi G7.8). Per correggere un "done" errato
    #   restano permessi Programmato (riprogramma) e Cancellato (non avvenuta).
    if update_data.get("stato") == "Rinviato" and event.stato == "Completato":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Non puoi rinviare una seduta già svolta: riportala a Programmato o annullala.",
        )

    # Bouncer 5 (G7.8-ter/ADR-023, temporal fence): su contratto LIQUIDATO (chiuso non auto-riapribile)
    #   la base del conguaglio (Completato + penali) è immutabile — 409 che indirizza a POST /reopen.
    #   I Programmato orfani restano ripulibili (D-TF-PULIZIA).
    new_stato = update_data.get("stato")
    if new_stato is not None and new_stato != event.stato:
        _assert_storia_liquidata_intatta(session, event, new_stato)

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(event, field)
        setattr(event, field, value)
        if value != old_val:
            changes[field] = {"old": old_val, "new": value}

    log_audit(session, "event", event.id, "UPDATE", trainer.id, changes or None)
    session.add(event)

    # Auto-close/reopen: se stato cambiato su evento PT con contratto, ricalcola chiuso
    if "stato" in changes and event.categoria == "PT" and event.id_contratto:
        _sync_contract_chiuso(session, event.id_contratto)

    session.commit()
    session.refresh(event)

    names = _load_client_names_batch(session, {event.id_cliente} if event.id_cliente else set())
    nome, cognome, telefono = names.get(event.id_cliente, (None, None, None)) if event.id_cliente else (None, None, None)

    return _to_response(event, nome, cognome, telefono)


# --- DELETE: Elimina evento ---

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Elimina un evento.

    Bouncer: trainer_id filter. 404 se non mio o non esiste.
    """
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.trainer_id == trainer.id, Event.deleted_at == None)
    ).first()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento non trovato")

    # Temporal fence (G7.8-ter/ADR-023): un evento CONTABILIZZATO di un contratto liquidato non si
    # elimina — sparirebbe dalla base del conguaglio già liquidato. Varco: POST /reopen.
    _assert_storia_liquidata_intatta(session, event)

    event.deleted_at = datetime.now(timezone.utc)
    session.add(event)
    log_audit(session, "event", event.id, "DELETE", trainer.id)

    # Auto-reopen: se era PT con contratto, i crediti usati calano → potrebbe riaprirsi
    if event.categoria == "PT" and event.id_contratto:
        _sync_contract_chiuso(session, event.id_contratto)

    session.commit()
