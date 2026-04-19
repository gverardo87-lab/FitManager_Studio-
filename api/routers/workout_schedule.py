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
from api.models.workout import WorkoutExercise, WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog
from api.models.workout_schedule import WorkoutScheduleSlot
from api.schemas.workout_schedule import (
    ScheduleGenerateRequest,
    ScheduleSlotUpdate,
    ScheduleBulkMoveRequest,
    ScheduleSlotResponse,
    ScheduleListResponse,
)
from api.schemas.workout_log import CompleteSlotRequest
from api.models.exercise_log import ExerciseLog
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

    # ── Rigenerazione: soft-delete vecchi + protezione completati ──
    now = datetime.now(timezone.utc)

    # 1. Soft-delete TUTTI i pianificati di questa scheda (passati E futuri)
    #    Risolve bug: se data_inizio < today, i vecchi slot passati
    #    sopravvivevano e si duplicavano con i nuovi.
    existing_pianificati = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_scheda == workout_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.deleted_at == None,
            WorkoutScheduleSlot.stato == "pianificato",
        )
    ).all()
    for old_slot in existing_pianificati:
        old_slot.deleted_at = now

    # 2. Raccogli date con slot completati/parziali (dati reali, sacri)
    #    I nuovi slot NON sovrascrivono sessioni già eseguite.
    existing_done = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_scheda == workout_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.deleted_at == None,
            WorkoutScheduleSlot.stato.in_(["completato", "parziale"]),
        )
    ).all()
    done_dates: set[date_type] = {s.data_pianificata for s in existing_done}

    # 3. Soft-delete slot saltati (non contengono dati, ripianificabili)
    existing_saltati = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_scheda == workout_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.deleted_at == None,
            WorkoutScheduleSlot.stato == "saltato",
        )
    ).all()
    for old_slot in existing_saltati:
        old_slot.deleted_at = now

    # ── Genera slot round-robin ──
    pattern_sorted = sorted(data.pattern_giorni)
    new_slots: list[WorkoutScheduleSlot] = []
    session_index = 0

    for week in range(data.settimane):
        week_start = start_date + timedelta(weeks=week)
        monday = week_start - timedelta(days=week_start.weekday())

        for day_of_week in pattern_sorted:
            slot_date = monday + timedelta(days=day_of_week)

            if slot_date < start_date:
                continue

            # Skip date con sessioni gia' completate (dati sacri)
            if slot_date in done_dates:
                session_index += 1
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

    # Aggiorna date piano (considerando anche slot completati preservati)
    all_active_dates = [s.data_pianificata for s in new_slots]
    all_active_dates.extend(s.data_pianificata for s in existing_done)
    if all_active_dates:
        all_active_dates.sort()
        plan.data_inizio = all_active_dates[0]
        plan.data_fine = all_active_dates[-1]
        plan.sessioni_per_settimana = len(pattern_sorted)
        plan.durata_settimane = data.settimane

    session.flush()
    for slot in new_slots:
        log_audit(session, "workout_schedule", slot.id, "CREATE", trainer.id)
    session.commit()

    # Refresh per avere gli ID
    for slot in new_slots:
        session.refresh(slot)

    logger.info(
        "Schedule rigenerato per workout %d: %d nuovi slot, %d completati preservati, "
        "%d pianificati rimossi, %d saltati rimossi",
        workout_id, len(new_slots), len(existing_done),
        len(existing_pianificati), len(existing_saltati),
    )

    # Build response (nuovi + completati preservati, per vista completa)
    session_map = {s.id: s for s in sessions_list}
    all_slots = list(existing_done) + new_slots
    all_slots.sort(key=lambda s: s.data_pianificata)
    items = [_build_slot_response(s, session_map) for s in all_slots]
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

        # Riapertura: usare PUT /workout-schedule/{id}/reopen (elimina log + exercise_logs)
        if data.stato == "pianificato" and slot.stato in ("completato", "parziale"):
            raise HTTPException(
                status_code=422,
                detail="Per riaprire una sessione completata usa l'endpoint dedicato /reopen",
            )

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
    body: CompleteSlotRequest | None = None,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Completa slot → crea WorkoutLog + ExerciseLog automaticamente.

    Atomico: aggiorna slot + crea log + exercise_logs in un singolo commit.
    data_esecuzione = oggi (o data_pianificata se nel passato).

    Body opzionale:
    - Assente/null/exercise_data=null → crea ExerciseLog con valori dal piano (source='trainer_assumed')
    - exercise_data=[...] → crea ExerciseLog con dati inseriti dal trainer (source='trainer')
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

    # Crea ExerciseLog per ogni esercizio della sessione
    exercise_data_map: dict[int, object] = {}
    if body and body.exercise_data:
        exercise_data_map = {ed.id_esercizio_sessione: ed for ed in body.exercise_data}

    # Fetch esercizi della sessione (straight + blocchi)
    plan_exercises = session.exec(
        select(WorkoutExercise).where(
            WorkoutExercise.id_sessione == slot.id_sessione,
        )
    ).all()

    for ex in plan_exercises:
        trainer_input = exercise_data_map.get(ex.id)
        if trainer_input:
            # Trainer ha inserito dati effettivi
            el = ExerciseLog(
                id_schedule_slot=slot.id,
                id_esercizio_sessione=ex.id,
                trainer_id=trainer.id,
                id_cliente=slot.id_cliente,
                serie_effettive=trainer_input.serie_effettive,
                ripetizioni_effettive=trainer_input.ripetizioni_effettive,
                carico_effettivo_kg=trainer_input.carico_effettivo_kg,
                rpe=trainer_input.rpe,
                note_cliente=trainer_input.note_cliente,
                source="trainer",
                created_at=now.isoformat(),
            )
        else:
            # Assume piano come valori effettivi
            el = ExerciseLog(
                id_schedule_slot=slot.id,
                id_esercizio_sessione=ex.id,
                trainer_id=trainer.id,
                id_cliente=slot.id_cliente,
                serie_effettive=ex.serie,
                ripetizioni_effettive=ex.ripetizioni,
                carico_effettivo_kg=ex.carico_kg,
                rpe=None,
                note_cliente=None,
                source="trainer_assumed",
                created_at=now.isoformat(),
            )
        session.add(el)

    log_audit(session, "workout_log", log.id, "CREATE", trainer.id)
    log_audit(session, "workout_schedule", slot.id, "UPDATE", trainer.id)
    session.commit()
    session.refresh(slot)

    logger.info(
        "Slot %d completato: %d exercise_logs creati (source=%s)",
        slot_id, len(plan_exercises),
        "trainer" if exercise_data_map else "trainer_assumed",
    )

    # Response
    ws = session.exec(
        select(WorkoutSession).where(WorkoutSession.id == slot.id_sessione)
    ).first()
    session_map = {ws.id: ws} if ws else {}
    return _build_slot_response(slot, session_map)


@router.put(
    "/workout-schedule/{slot_id}/reopen",
    response_model=ScheduleSlotResponse,
    summary="Riapri sessione: reset stato + elimina log e dati effettivi",
)
def reopen_slot(
    slot_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """
    Riapre una sessione completata/parziale → stato 'pianificato'.

    Elimina TUTTI i dati associati:
    - ExerciseLog (dati effettivi per-esercizio)
    - WorkoutLog (record esecuzione sessione + feedback)
    - Reset slot: stato='pianificato', id_log=null
    """

    slot = _bouncer_slot(session, slot_id, trainer.id)

    if slot.stato == "pianificato":
        raise HTTPException(422, "La sessione e' gia' in stato pianificato")

    # 1. Elimina exercise_logs per questo slot
    ex_logs = session.exec(
        select(ExerciseLog).where(
            ExerciseLog.id_schedule_slot == slot_id,
            ExerciseLog.deleted_at == None,  # noqa: E711
        )
    ).all()
    for el in ex_logs:
        session.delete(el)

    # 2. Elimina WorkoutLog collegato
    if slot.id_log:
        wl = session.get(WorkoutLog, slot.id_log)
        if wl:
            session.delete(wl)

    # 3. Reset slot
    slot.stato = "pianificato"
    slot.id_log = None

    log_audit(session, "workout_schedule", slot.id, "REOPEN", trainer.id)
    session.commit()
    session.refresh(slot)

    ws = session.exec(
        select(WorkoutSession).where(WorkoutSession.id == slot.id_sessione)
    ).first()
    session_map = {ws.id: ws} if ws else {}

    logger.info("Slot %d riaperto (logs eliminati: %d)", slot_id, len(ex_logs))
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
