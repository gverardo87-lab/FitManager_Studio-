# api/routers/workout_schedule.py
"""
Endpoint Workout Schedule — pianificazione calendario sessioni allenamento.

Genera slot concreti (data + sessione) da un pattern settimanale.
Supporta completamento (crea WorkoutLog automatico), skip, drag & drop.

Endpoints:
  POST   /workouts/{workout_id}/schedule/generate    — genera slot da pattern
  GET    /workouts/{workout_id}/schedule              — lista slot della scheda
  PUT    /workout-schedule/{slot_id}                  — aggiorna slot (data, stato, note)
  PUT    /workout-schedule/{slot_id}/complete         — completa slot → crea WorkoutLog
  DELETE /workout-schedule/{slot_id}                  — soft-delete slot
  POST   /workouts/{workout_id}/schedule/bulk-move    — sposta N slot di offset giorni
"""

import logging
from datetime import date as date_type, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.workout import WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog
from api.models.workout_schedule import WorkoutScheduleSlot
from api.schemas.workout_schedule import (
    ScheduleGenerateRequest,
    ScheduleSlotUpdate,
    ScheduleBulkMoveRequest,
    ScheduleSlotResponse,
    ScheduleListResponse,
)
from api.routers._audit import log_audit

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workout-schedule"])

VALID_STATI = {"pianificato", "completato", "saltato", "parziale"}


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _bouncer_workout(session: Session, workout_id: int, trainer_id: int) -> WorkoutPlan:
    """Bouncer: verifica ownership scheda. 404 se non trovata."""
    plan = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id == workout_id,
            WorkoutPlan.trainer_id == trainer_id,
            WorkoutPlan.deleted_at == None,
        )
    ).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheda non trovata",
        )
    return plan


def _bouncer_slot(session: Session, slot_id: int, trainer_id: int) -> WorkoutScheduleSlot:
    """Bouncer: verifica ownership slot. 404 se non trovato."""
    slot = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id == slot_id,
            WorkoutScheduleSlot.trainer_id == trainer_id,
            WorkoutScheduleSlot.deleted_at == None,
        )
    ).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot non trovato",
        )
    return slot


def _get_sessions_for_plan(
    session: Session, plan_id: int,
) -> list[WorkoutSession]:
    """Fetch sessioni ordinate per numero."""
    return list(session.exec(
        select(WorkoutSession)
        .where(WorkoutSession.id_scheda == plan_id)
        .order_by(WorkoutSession.numero_sessione)
    ).all())


def _build_slot_response(
    slot: WorkoutScheduleSlot,
    session_map: dict[int, WorkoutSession],
) -> ScheduleSlotResponse:
    """Costruisce response enriched con nomi sessione."""
    ws = session_map.get(slot.id_sessione)
    return ScheduleSlotResponse(
        id=slot.id,
        id_scheda=slot.id_scheda,
        id_sessione=slot.id_sessione,
        id_cliente=slot.id_cliente,
        data_pianificata=str(slot.data_pianificata),
        stato=slot.stato,
        id_log=slot.id_log,
        note=slot.note,
        created_at=slot.created_at,
        sessione_nome=ws.nome_sessione if ws else f"Sessione #{slot.id_sessione}",
        sessione_numero=ws.numero_sessione if ws else 0,
        focus_muscolare=ws.focus_muscolare if ws else None,
    )


# ════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════

@router.post(
    "/workouts/{workout_id}/schedule/generate",
    response_model=ScheduleListResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_schedule(
    workout_id: int,
    data: ScheduleGenerateRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Genera slot calendario da pattern settimanale.

    Round-robin: le sessioni vengono distribuite ciclicamente sui giorni.
    Es. sessioni=[A,B,C], pattern=[Lun,Mer,Ven], 2 settimane:
      Sett1: Lun=A, Mer=B, Ven=C
      Sett2: Lun=A, Mer=B, Ven=C

    Elimina (soft-delete) slot futuri esistenti prima di rigenerare.
    """
    plan = _bouncer_workout(session, workout_id, trainer.id)

    if not plan.id_cliente:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La scheda deve essere assegnata a un cliente",
        )

    # Verifica client ownership
    client = session.exec(
        select(Client).where(
            Client.id == plan.id_cliente,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,
        )
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")

    # Valida pattern_giorni (0-6)
    for day in data.pattern_giorni:
        if day < 0 or day > 6:
            raise HTTPException(
                status_code=422,
                detail=f"Giorno non valido: {day}. Usa 0=Lunedi..6=Domenica",
            )

    # Fetch sessioni
    sessions_list = _get_sessions_for_plan(session, workout_id)
    if not sessions_list:
        raise HTTPException(
            status_code=422,
            detail="La scheda non ha sessioni",
        )

    # Parse data inizio
    try:
        start_date = date_type.fromisoformat(data.data_inizio)
    except ValueError:
        raise HTTPException(status_code=422, detail="Data inizio non valida")

    # Soft-delete slot futuri esistenti (rigenerazione)
    now = datetime.now(timezone.utc)
    today = date_type.today()
    existing_future = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_scheda == workout_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.deleted_at == None,
            WorkoutScheduleSlot.stato == "pianificato",
            WorkoutScheduleSlot.data_pianificata >= today,
        )
    ).all()
    for old_slot in existing_future:
        old_slot.deleted_at = now

    # Genera slot round-robin
    pattern_sorted = sorted(data.pattern_giorni)
    new_slots: list[WorkoutScheduleSlot] = []
    session_index = 0

    for week in range(data.settimane):
        week_start = start_date + timedelta(weeks=week)
        # Trova il lunedi della settimana
        monday = week_start - timedelta(days=week_start.weekday())

        for day_of_week in pattern_sorted:
            slot_date = monday + timedelta(days=day_of_week)

            # Skip date prima della data inizio
            if slot_date < start_date:
                continue

            ws = sessions_list[session_index % len(sessions_list)]
            session_index += 1

            new_slot = WorkoutScheduleSlot(
                id_scheda=workout_id,
                id_sessione=ws.id,
                id_cliente=plan.id_cliente,
                trainer_id=trainer.id,
                data_pianificata=slot_date,
                stato="pianificato",
                created_at=now.isoformat(),
            )
            session.add(new_slot)
            new_slots.append(new_slot)

    # Aggiorna date piano
    if new_slots:
        plan.data_inizio = new_slots[0].data_pianificata
        plan.data_fine = new_slots[-1].data_pianificata
        plan.sessioni_per_settimana = len(pattern_sorted)
        plan.durata_settimane = data.settimane

    session.flush()
    for slot in new_slots:
        log_audit(session, "workout_schedule", slot.id, "CREATE", trainer.id)
    session.commit()

    # Refresh per avere gli ID
    for slot in new_slots:
        session.refresh(slot)

    # Build response
    session_map = {s.id: s for s in sessions_list}
    items = [_build_slot_response(s, session_map) for s in new_slots]
    return ScheduleListResponse(items=items, total=len(items))


@router.get(
    "/workouts/{workout_id}/schedule",
    response_model=ScheduleListResponse,
)
def list_schedule(
    workout_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Lista tutti gli slot pianificati per una scheda, ordinati per data."""
    _bouncer_workout(session, workout_id, trainer.id)

    slots = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_scheda == workout_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.deleted_at == None,
        ).order_by(WorkoutScheduleSlot.data_pianificata)
    ).all()

    if not slots:
        return ScheduleListResponse(items=[], total=0)

    # Batch fetch sessions (anti-N+1)
    session_ids = list({s.id_sessione for s in slots})
    ws_list = session.exec(
        select(WorkoutSession).where(WorkoutSession.id.in_(session_ids))
    ).all()
    session_map = {s.id: s for s in ws_list}

    items = [_build_slot_response(s, session_map) for s in slots]
    return ScheduleListResponse(items=items, total=len(items))


@router.put(
    "/workout-schedule/{slot_id}",
    response_model=ScheduleSlotResponse,
)
def update_slot(
    slot_id: int,
    data: ScheduleSlotUpdate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Aggiorna slot: data, stato, note. Usato per drag & drop e skip."""
    slot = _bouncer_slot(session, slot_id, trainer.id)

    if data.data_pianificata is not None:
        try:
            slot.data_pianificata = date_type.fromisoformat(data.data_pianificata)
        except ValueError:
            raise HTTPException(status_code=422, detail="Data non valida")

    if data.stato is not None:
        if data.stato not in VALID_STATI:
            raise HTTPException(status_code=422, detail=f"Stato non valido: {data.stato}")

        # Reopen: quando si torna a pianificato da completato, soft-delete il log collegato
        if data.stato == "pianificato" and slot.stato == "completato" and slot.id_log:
            linked_log = session.exec(
                select(WorkoutLog).where(
                    WorkoutLog.id == slot.id_log,
                    WorkoutLog.deleted_at == None,
                )
            ).first()
            if linked_log:
                linked_log.deleted_at = datetime.now(timezone.utc)
                log_audit(session, "workout_log", linked_log.id, "DELETE", trainer.id)
            slot.id_log = None

        slot.stato = data.stato

    if data.note is not None:
        slot.note = data.note

    log_audit(session, "workout_schedule", slot.id, "UPDATE", trainer.id)
    session.commit()
    session.refresh(slot)

    # Fetch session per response
    ws = session.exec(
        select(WorkoutSession).where(WorkoutSession.id == slot.id_sessione)
    ).first()
    session_map = {ws.id: ws} if ws else {}
    return _build_slot_response(slot, session_map)


@router.put(
    "/workout-schedule/{slot_id}/complete",
    response_model=ScheduleSlotResponse,
)
def complete_slot(
    slot_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Completa slot → crea WorkoutLog automaticamente.

    Atomico: aggiorna slot + crea log in un singolo commit.
    data_esecuzione = oggi (o data_pianificata se nel passato).
    """
    slot = _bouncer_slot(session, slot_id, trainer.id)

    if slot.stato == "completato":
        raise HTTPException(
            status_code=422,
            detail="Slot gia' completato",
        )

    # Guard: non si puo' completare una sessione futura
    today = date_type.today()
    if slot.data_pianificata > today:
        raise HTTPException(
            status_code=422,
            detail="Non puoi completare una sessione futura",
        )

    # Data esecuzione: data pianificata per passati, oggi per odierni
    exec_date = slot.data_pianificata if slot.data_pianificata <= today else today

    # Crea WorkoutLog
    now = datetime.now(timezone.utc)
    log = WorkoutLog(
        id_scheda=slot.id_scheda,
        id_sessione=slot.id_sessione,
        id_cliente=slot.id_cliente,
        trainer_id=trainer.id,
        data_esecuzione=exec_date,
        note=slot.note,
        created_at=now.isoformat(),
    )
    session.add(log)
    session.flush()

    # Aggiorna slot
    slot.stato = "completato"
    slot.id_log = log.id

    log_audit(session, "workout_log", log.id, "CREATE", trainer.id)
    log_audit(session, "workout_schedule", slot.id, "UPDATE", trainer.id)
    session.commit()
    session.refresh(slot)

    # Response
    ws = session.exec(
        select(WorkoutSession).where(WorkoutSession.id == slot.id_sessione)
    ).first()
    session_map = {ws.id: ws} if ws else {}
    return _build_slot_response(slot, session_map)


@router.delete(
    "/workout-schedule/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_slot(
    slot_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Soft-delete singolo slot."""
    slot = _bouncer_slot(session, slot_id, trainer.id)
    slot.deleted_at = datetime.now(timezone.utc)
    log_audit(session, "workout_schedule", slot.id, "DELETE", trainer.id)
    session.commit()


@router.post(
    "/workouts/{workout_id}/schedule/bulk-move",
    response_model=ScheduleListResponse,
)
def bulk_move_slots(
    workout_id: int,
    data: ScheduleBulkMoveRequest,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Sposta N slot di un offset in giorni. Usato per ripianificazione."""
    _bouncer_workout(session, workout_id, trainer.id)

    offset = timedelta(days=data.offset_giorni)
    moved_slots: list[WorkoutScheduleSlot] = []

    for slot_id in data.slot_ids:
        slot = session.exec(
            select(WorkoutScheduleSlot).where(
                WorkoutScheduleSlot.id == slot_id,
                WorkoutScheduleSlot.id_scheda == workout_id,
                WorkoutScheduleSlot.trainer_id == trainer.id,
                WorkoutScheduleSlot.deleted_at == None,
            )
        ).first()
        if not slot:
            continue

        slot.data_pianificata = slot.data_pianificata + offset
        log_audit(session, "workout_schedule", slot.id, "UPDATE", trainer.id)
        moved_slots.append(slot)

    session.commit()

    if not moved_slots:
        return ScheduleListResponse(items=[], total=0)

    # Batch fetch sessions
    session_ids = list({s.id_sessione for s in moved_slots})
    ws_list = session.exec(
        select(WorkoutSession).where(WorkoutSession.id.in_(session_ids))
    ).all()
    session_map = {s.id: s for s in ws_list}

    for s in moved_slots:
        session.refresh(s)

    items = [_build_slot_response(s, session_map) for s in moved_slots]
    return ScheduleListResponse(items=items, total=len(items))
