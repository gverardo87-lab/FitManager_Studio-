# api/routers/public_portal.py
"""
Portale Clienti Self-Service — Anamnesi + Scheda Allenamento Interattiva.

Anamnesi (3 endpoint):
  POST /api/clients/{client_id}/share-anamnesi  [JWT trainer]  — genera token monouso
  GET  /api/public/anamnesi/validate             [pubblico]     — valida token + info form
  POST /api/public/anamnesi/submit               [pubblico]     — salva anamnesi + invalida token

Workout (5 endpoint):
  POST /api/clients/{client_id}/share-workout    [JWT trainer]  — genera token multi-uso
  GET  /api/public/workout/validate              [pubblico]     — valida token + info scheda
  GET  /api/public/workout/sessions              [pubblico]     — lista slot calendario
  GET  /api/public/workout/session/{id}/exercises [pubblico]    — esercizi sessione + log
  POST /api/public/workout/session/{id}/log      [pubblico]     — salva dati effettivi

Architettura sicurezza:
  - Token UUID4 (122 bit entropia)
  - scope=anamnesi: monouso (used_at), 48h scadenza
  - scope=workout: multi-uso (used_at NON settato), scadenza = data_fine scheda + 7gg
  - Endpoint pubblici: rate limiting IP-based in-process (10 req/min, 30 req/h)
  - Nome cliente mascherato: "Marco R." — nessun dato sensibile senza token valido
  - Feature flag: PUBLIC_PORTAL_ENABLED=false → tutti gli endpoint 404
"""

import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlmodel import Session, func, select

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.exercise import Exercise
from api.models.exercise_log import ExerciseLog
from api.models.share_token import ShareToken
from api.models.trainer import Trainer
from api.models.workout import SessionBlock, WorkoutExercise, WorkoutPlan, WorkoutSession
from api.models.workout_log import WorkoutLog
from api.models.workout_schedule import WorkoutScheduleSlot
from api.schemas.public import (
    AnamnesiSubmitRequest,
    AnamnesiSubmitResponse,
    AnamnesiValidateResponse,
    ExerciseLogData,
    ShareTokenResponse,
    WorkoutExerciseItem,
    WorkoutExercisesResponse,
    WorkoutLogRequest,
    WorkoutLogResponse,
    WorkoutSessionsResponse,
    WorkoutSlotItem,
    WorkoutValidateResponse,
)
from api.services.rate_limiter import portal_limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["public-portal"])

# ── Feature flag ────────────────────────────────────────────────────────────

def _is_enabled() -> bool:
    return os.getenv("PUBLIC_PORTAL_ENABLED", "false").strip().lower() in ("true", "1", "yes")


def _require_enabled() -> None:
    if not _is_enabled():
        raise HTTPException(status_code=404, detail="Not Found")


def _check_rate_limit(request: Request) -> None:
    """Rate limiting IP-based via shared RateLimiter (30 req/min, 120 req/h)."""
    portal_limiter.check(request)


# ── Helper: bouncer token pubblico ───────────────────────────────────────────

def _get_valid_token(session: Session, token: str) -> ShareToken:
    """
    Valida token: esiste, non scaduto, non usato, cliente attivo.
    404 in tutti i casi di errore (nessun info leaking).
    """
    share = session.exec(
        select(ShareToken).where(ShareToken.token == token)
    ).first()

    if not share:
        raise HTTPException(404, "Link non valido")

    now = datetime.now(timezone.utc)
    # expires_at potrebbe essere naive (SQLite) — normalizziamo
    expires = share.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        raise HTTPException(404, "Link scaduto")

    if share.used_at is not None:
        raise HTTPException(404, "Link gia' utilizzato")

    # Cliente ancora attivo e non cancellato
    client = session.get(Client, share.client_id)
    if not client or client.deleted_at is not None:
        raise HTTPException(404, "Link non valido")

    return share


# ── ENDPOINT 1: Generazione token (protetto, JWT trainer) ───────────────────

@router.post(
    "/clients/{client_id}/share-anamnesi",
    response_model=ShareTokenResponse,
    summary="Genera link monouso per anamnesi self-service",
)
def create_share_token(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
) -> ShareTokenResponse:
    _require_enabled()

    # Bouncer: il cliente deve appartenere al trainer (deep IDOR)
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    # Invalida eventuali token precedenti non usati per stesso client+scope
    old_tokens = session.exec(
        select(ShareToken).where(
            ShareToken.trainer_id == trainer.id,
            ShareToken.client_id == client_id,
            ShareToken.scope == "anamnesi",
            ShareToken.used_at == None,  # noqa: E711
        )
    ).all()
    for old in old_tokens:
        session.delete(old)

    now = datetime.now(timezone.utc)
    share = ShareToken(
        token=str(uuid4()),
        trainer_id=trainer.id,
        client_id=client_id,
        scope="anamnesi",
        created_at=now,
        expires_at=now + timedelta(hours=48),
    )
    session.add(share)
    session.commit()
    session.refresh(share)

    logger.info(
        "Share token generato: trainer=%d client=%d scope=anamnesi",
        trainer.id, client_id,
    )

    # Se PUBLIC_BASE_URL è configurato, genera URL assoluto (es. https://nome.ts.net)
    # Altrimenti URL relativo — il frontend prepende window.location.origin
    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    path = f"/public/anamnesi/{share.token}"

    return ShareTokenResponse(
        token=share.token,
        url=f"{base_url}{path}" if base_url else path,
        expires_at=share.expires_at,
        client_name=f"{client.nome} {client.cognome}",
    )


# ── ENDPOINT 2: Validazione token (pubblico) ────────────────────────────────

@router.get(
    "/public/anamnesi/validate",
    response_model=AnamnesiValidateResponse,
    summary="Valida token e ritorna info per il form pubblico",
)
def validate_anamnesi_token(
    token: str = Query(..., min_length=36, max_length=36),
    request: Request = None,
    session: Session = Depends(get_session),
) -> AnamnesiValidateResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_token(session, token)

    client = session.get(Client, share.client_id)
    trainer = session.get(Trainer, share.trainer_id)

    # Mascheramento cognome: "Marco R."
    cognome_iniziale = (client.cognome[0] + ".") if client.cognome else ""
    client_name = f"{client.nome} {cognome_iniziale}".strip()

    trainer_cognome_iniziale = (trainer.cognome[0] + ".") if trainer.cognome else ""
    trainer_name = f"{trainer.nome} {trainer_cognome_iniziale}".strip()

    has_existing = bool(client.anamnesi_json)

    return AnamnesiValidateResponse(
        client_name=client_name,
        trainer_name=trainer_name,
        has_existing=has_existing,
        scope=share.scope,
    )


# ── ENDPOINT 3: Submit anamnesi (pubblico) ───────────────────────────────────

@router.post(
    "/public/anamnesi/submit",
    response_model=AnamnesiSubmitResponse,
    summary="Salva anamnesi compilata dal cliente e invalida il token",
)
def submit_anamnesi(
    body: AnamnesiSubmitRequest,
    request: Request = None,
    session: Session = Depends(get_session),
) -> AnamnesiSubmitResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_token(session, body.token)
    client = session.get(Client, share.client_id)

    # Salva anamnesi sul cliente
    client.anamnesi_json = json.dumps(body.anamnesi, ensure_ascii=False)

    # Invalida token (monouso)
    share.used_at = datetime.now(timezone.utc)

    session.add(client)
    session.add(share)
    session.commit()

    logger.info(
        "Anamnesi self-service ricevuta: client=%d scope=%s",
        share.client_id, share.scope,
    )

    return AnamnesiSubmitResponse(
        success=True,
        message="Grazie! Il tuo questionario e' stato inviato al tuo trainer.",
    )


# ════════════════════════════════════════════════════════════════════════════
# WORKOUT — Portale Scheda Allenamento Interattiva (ADR-009)
# ════════════════════════════════════════════════════════════════════════════


def _mask_name(nome: str, cognome: str | None) -> str:
    """'Marco Rossi' → 'Marco R.'"""
    iniziale = (cognome[0] + ".") if cognome else ""
    return f"{nome} {iniziale}".strip()


def _get_valid_workout_token(session: Session, token: str) -> ShareToken:
    """Valida token workout: esiste, non scaduto, scope=workout, cliente attivo."""
    share = session.exec(
        select(ShareToken).where(ShareToken.token == token)
    ).first()
    if not share:
        raise HTTPException(404, "Link non valido")

    if share.scope != "workout":
        raise HTTPException(404, "Link non valido")

    now = datetime.now(timezone.utc)
    expires = share.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        raise HTTPException(404, "Link scaduto")

    # Multi-uso: NON controlliamo used_at per scope=workout

    client = session.get(Client, share.client_id)
    if not client or client.deleted_at is not None:
        raise HTTPException(404, "Link non valido")

    return share


# ── ENDPOINT W1: Generazione token workout (protetto, JWT trainer) ────────

@router.post(
    "/clients/{client_id}/share-workout",
    response_model=ShareTokenResponse,
    summary="Genera link multi-uso per scheda allenamento interattiva",
)
def create_workout_share_token(
    client_id: int,
    id_scheda: int = Query(..., description="ID della scheda da condividere"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
) -> ShareTokenResponse:
    _require_enabled()

    # Bouncer: cliente appartiene al trainer
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    # Bouncer: scheda appartiene al trainer e al cliente
    workout = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id == id_scheda,
            WorkoutPlan.trainer_id == trainer.id,
            WorkoutPlan.id_cliente == client_id,
            WorkoutPlan.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not workout:
        raise HTTPException(404, "Scheda non trovata")

    # Verifica: la scheda ha un calendario generato
    slot_count = session.exec(
        select(func.count(WorkoutScheduleSlot.id)).where(
            WorkoutScheduleSlot.id_scheda == id_scheda,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).one()
    if slot_count == 0:
        raise HTTPException(
            400, "La scheda non ha un calendario. Genera il calendario prima di condividerla."
        )

    # Verifica: data_fine esiste
    if not workout.data_fine:
        raise HTTPException(
            400, "La scheda non ha una data di fine. Imposta le date prima di condividerla."
        )

    # Invalida token precedente per stessa scheda
    old_tokens = session.exec(
        select(ShareToken).where(
            ShareToken.trainer_id == trainer.id,
            ShareToken.scope == "workout",
            ShareToken.id_scheda == id_scheda,
        )
    ).all()
    for old in old_tokens:
        session.delete(old)

    now = datetime.now(timezone.utc)
    # Scadenza: data_fine scheda + 7 giorni di grace
    days_until_end = (workout.data_fine - date.today()).days
    grace_days = max(days_until_end + 7, 7)  # minimo 7 giorni anche se scheda quasi finita
    share = ShareToken(
        token=str(uuid4()),
        trainer_id=trainer.id,
        client_id=client_id,
        scope="workout",
        id_scheda=id_scheda,
        created_at=now,
        expires_at=now + timedelta(days=grace_days),
    )
    session.add(share)
    session.commit()
    session.refresh(share)

    logger.info(
        "Workout share token generato: trainer=%d client=%d scheda=%d expires=%s",
        trainer.id, client_id, id_scheda, share.expires_at.isoformat(),
    )

    base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    path = f"/public/scheda/{share.token}"

    return ShareTokenResponse(
        token=share.token,
        url=f"{base_url}{path}" if base_url else path,
        expires_at=share.expires_at,
        client_name=f"{client.nome} {client.cognome}",
    )


# ── ENDPOINT W2: Validazione token workout (pubblico) ────────────────────

@router.get(
    "/public/workout/validate",
    response_model=WorkoutValidateResponse,
    summary="Valida token workout e ritorna info scheda",
)
def validate_workout_token(
    token: str = Query(..., min_length=36, max_length=36),
    request: Request = None,
    session: Session = Depends(get_session),
) -> WorkoutValidateResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_workout_token(session, token)

    client = session.get(Client, share.client_id)
    trainer = session.get(Trainer, share.trainer_id)
    workout = session.get(WorkoutPlan, share.id_scheda)

    if not workout or workout.deleted_at is not None:
        raise HTTPException(404, "Scheda non disponibile")

    total = session.exec(
        select(func.count(WorkoutScheduleSlot.id)).where(
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).one()

    completed = session.exec(
        select(func.count(WorkoutScheduleSlot.id)).where(
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.stato == "completato",
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).one()

    return WorkoutValidateResponse(
        client_name=_mask_name(client.nome, client.cognome),
        trainer_name=_mask_name(trainer.nome, trainer.cognome),
        workout_name=workout.nome,
        data_inizio=workout.data_inizio,
        data_fine=workout.data_fine,
        sessioni_per_settimana=workout.sessioni_per_settimana,
        total_slots=total,
        completed_slots=completed,
        scope="workout",
    )


# ── ENDPOINT W3: Lista sessioni/slot (pubblico) ──────────────────────────

@router.get(
    "/public/workout/sessions",
    response_model=WorkoutSessionsResponse,
    summary="Lista slot del calendario scheda",
)
def get_workout_sessions(
    token: str = Query(..., min_length=36, max_length=36),
    request: Request = None,
    session: Session = Depends(get_session),
) -> WorkoutSessionsResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_workout_token(session, token)

    slots = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        ).order_by(WorkoutScheduleSlot.data_pianificata)
    ).all()

    # Batch fetch sessioni per nomi
    session_ids = list({s.id_sessione for s in slots})
    sessions_map: dict[int, WorkoutSession] = {}
    if session_ids:
        ws_list = session.exec(
            select(WorkoutSession).where(WorkoutSession.id.in_(session_ids))
        ).all()
        sessions_map = {ws.id: ws for ws in ws_list}

    # Batch fetch exercise_log count per slot (per has_log)
    slot_ids = [s.id for s in slots]
    log_counts: dict[int, int] = {}
    if slot_ids:
        log_rows = session.exec(
            select(ExerciseLog.id_schedule_slot, func.count(ExerciseLog.id))
            .where(
                ExerciseLog.id_schedule_slot.in_(slot_ids),
                ExerciseLog.deleted_at == None,  # noqa: E711
            )
            .group_by(ExerciseLog.id_schedule_slot)
        ).all()
        log_counts = {row[0]: row[1] for row in log_rows}

    items = []
    for slot in slots:
        ws = sessions_map.get(slot.id_sessione)
        items.append(WorkoutSlotItem(
            id=slot.id,
            data_pianificata=slot.data_pianificata,
            stato=slot.stato,
            sessione_nome=ws.nome_sessione if ws else f"Sessione {slot.id_sessione}",
            focus_muscolare=ws.focus_muscolare if ws else None,
            has_log=log_counts.get(slot.id, 0) > 0,
        ))

    return WorkoutSessionsResponse(slots=items)


# ── ENDPOINT W4: Esercizi di una sessione (pubblico) ─��───────────────────

@router.get(
    "/public/workout/session/{slot_id}/exercises",
    response_model=WorkoutExercisesResponse,
    summary="Esercizi di una sessione con log opzionali",
)
def get_workout_exercises(
    slot_id: int = Path(...),
    token: str = Query(..., min_length=36, max_length=36),
    request: Request = None,
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
) -> WorkoutExercisesResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_workout_token(session, token)

    # Bouncer: lo slot appartiene alla scheda del token
    slot = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id == slot_id,
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not slot:
        raise HTTPException(404, "Sessione non trovata")

    ws = session.get(WorkoutSession, slot.id_sessione)

    # Fetch esercizi della sessione (ordinati)
    exercises = session.exec(
        select(WorkoutExercise).where(
            WorkoutExercise.id_sessione == slot.id_sessione,
        ).order_by(WorkoutExercise.ordine)
    ).all()

    # Batch fetch nomi esercizi da catalog.db (cross-DB)
    exercise_catalog_ids = list({e.id_esercizio for e in exercises})
    catalog_map: dict[int, Exercise] = {}
    if exercise_catalog_ids:
        catalog_exercises = catalog_session.exec(
            select(Exercise).where(Exercise.id.in_(exercise_catalog_ids))
        ).all()
        catalog_map = {ex.id: ex for ex in catalog_exercises}

    # Batch fetch blocchi per nome
    block_ids = list({e.id_blocco for e in exercises if e.id_blocco})
    blocks_map: dict[int, SessionBlock] = {}
    if block_ids:
        blocks = session.exec(
            select(SessionBlock).where(SessionBlock.id.in_(block_ids))
        ).all()
        blocks_map = {b.id: b for b in blocks}

    # Batch fetch foto esercizi da catalog.db
    # tipo="image", URL contiene exec_start.jpg o exec_end.jpg
    from api.models.exercise_media import ExerciseMedia
    media_map: dict[int, dict[str, str]] = {}
    if exercise_catalog_ids:
        media_rows = catalog_session.exec(
            select(ExerciseMedia).where(
                ExerciseMedia.exercise_id.in_(exercise_catalog_ids),
            )
        ).all()
        for m in media_rows:
            if m.exercise_id not in media_map:
                media_map[m.exercise_id] = {}
            if "exec_start" in (m.url or ""):
                media_map[m.exercise_id]["start"] = m.url
            elif "exec_end" in (m.url or ""):
                media_map[m.exercise_id]["end"] = m.url

    # Batch fetch exercise_logs per questo slot
    exercise_ids = [e.id for e in exercises]
    logs_map: dict[int, ExerciseLog] = {}
    if exercise_ids:
        logs = session.exec(
            select(ExerciseLog).where(
                ExerciseLog.id_schedule_slot == slot_id,
                ExerciseLog.id_esercizio_sessione.in_(exercise_ids),
                ExerciseLog.deleted_at == None,  # noqa: E711
            )
        ).all()
        logs_map = {log.id_esercizio_sessione: log for log in logs}

    items = []
    for ex in exercises:
        cat = catalog_map.get(ex.id_esercizio)
        log = logs_map.get(ex.id)
        block = blocks_map.get(ex.id_blocco) if ex.id_blocco else None
        photos = media_map.get(ex.id_esercizio, {})

        log_data = None
        if log:
            log_data = ExerciseLogData(
                serie_effettive=log.serie_effettive,
                ripetizioni_effettive=log.ripetizioni_effettive,
                carico_effettivo_kg=log.carico_effettivo_kg,
                rpe=log.rpe,
                note_cliente=log.note_cliente,
            )

        items.append(WorkoutExerciseItem(
            id=ex.id,
            nome_esercizio=cat.nome if cat else f"Esercizio #{ex.id_esercizio}",
            gruppo_muscolare=cat.muscoli_primari if cat else None,
            categoria=cat.categoria if cat else None,
            ordine=ex.ordine,
            serie=ex.serie,
            ripetizioni=ex.ripetizioni,
            carico_kg=ex.carico_kg,
            tempo_riposo_sec=ex.tempo_riposo_sec,
            tempo_esecuzione=ex.tempo_esecuzione,
            note_trainer=ex.note,
            blocco_nome=block.nome if block else None,
            blocco_tipo=block.tipo_blocco if block else None,
            foto_start=photos.get("start"),
            foto_end=photos.get("end"),
            setup=cat.setup if cat else None,
            esecuzione=cat.esecuzione if cat else None,
            respirazione=cat.respirazione if cat else None,
            coaching_cues=cat.coaching_cues if cat else None,
            errori_comuni=cat.errori_comuni if cat else None,
            log=log_data,
        ))

    return WorkoutExercisesResponse(
        slot_id=slot.id,
        data_pianificata=slot.data_pianificata,
        stato=slot.stato,
        sessione_nome=ws.nome_sessione if ws else f"Sessione {slot.id_sessione}",
        exercises=items,
    )


# ── ENDPOINT W5: Salva dati effettivi sessione (pubblico) ────────────────

@router.post(
    "/public/workout/session/{slot_id}/log",
    response_model=WorkoutLogResponse,
    summary="Salva dati effettivi per-esercizio dal client portal",
)
def log_workout_session(
    slot_id: int = Path(...),
    body: WorkoutLogRequest = ...,
    request: Request = None,
    session: Session = Depends(get_session),
) -> WorkoutLogResponse:
    _require_enabled()
    _check_rate_limit(request)

    share = _get_valid_workout_token(session, body.token)

    # Bouncer: slot appartiene alla scheda del token
    slot = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id == slot_id,
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not slot:
        raise HTTPException(404, "Sessione non trovata")

    # Time guard: non loggare sessioni future lontane (oggi + 3 giorni max)
    today = date.today()
    if slot.data_pianificata > today + timedelta(days=3):
        raise HTTPException(400, "Non puoi compilare una sessione futura")

    # Fetch esercizi validi della sessione (per validazione)
    valid_exercise_ids = set(
        session.exec(
            select(WorkoutExercise.id).where(
                WorkoutExercise.id_sessione == slot.id_sessione
            )
        ).all()
    )

    # Upsert exercise logs
    for ex_input in body.exercises:
        if ex_input.id_esercizio_sessione not in valid_exercise_ids:
            raise HTTPException(400, f"Esercizio {ex_input.id_esercizio_sessione} non valido")

        existing = session.exec(
            select(ExerciseLog).where(
                ExerciseLog.id_schedule_slot == slot_id,
                ExerciseLog.id_esercizio_sessione == ex_input.id_esercizio_sessione,
                ExerciseLog.deleted_at == None,  # noqa: E711
            )
        ).first()

        if existing:
            # Update
            existing.serie_effettive = ex_input.serie_effettive
            existing.ripetizioni_effettive = ex_input.ripetizioni_effettive
            existing.carico_effettivo_kg = ex_input.carico_effettivo_kg
            existing.rpe = ex_input.rpe
            existing.note_cliente = ex_input.note_cliente
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            session.add(existing)
        else:
            # Insert
            log = ExerciseLog(
                id_schedule_slot=slot_id,
                id_esercizio_sessione=ex_input.id_esercizio_sessione,
                trainer_id=share.trainer_id,
                id_cliente=share.client_id,
                serie_effettive=ex_input.serie_effettive,
                ripetizioni_effettive=ex_input.ripetizioni_effettive,
                carico_effettivo_kg=ex_input.carico_effettivo_kg,
                rpe=ex_input.rpe,
                note_cliente=ex_input.note_cliente,
                source="client_portal",
            )
            session.add(log)

    # Crea/aggiorna WorkoutLog per lo slot
    existing_wl = session.exec(
        select(WorkoutLog).where(
            WorkoutLog.id_sessione == slot.id_sessione,
            WorkoutLog.id_scheda == share.id_scheda,
            WorkoutLog.id_cliente == share.client_id,
            WorkoutLog.deleted_at == None,  # noqa: E711
        )
    ).first()

    # Filtra solo per questo specifico slot usando data_esecuzione = data_pianificata
    wl_for_slot = None
    if existing_wl and existing_wl.data_esecuzione == slot.data_pianificata:
        wl_for_slot = existing_wl

    fb = body.feedback
    if not wl_for_slot:
        wl = WorkoutLog(
            id_scheda=share.id_scheda,
            id_sessione=slot.id_sessione,
            id_cliente=share.client_id,
            trainer_id=share.trainer_id,
            data_esecuzione=slot.data_pianificata,
            note=body.note_sessione,
            source="client_portal",
            durata_effettiva_min=fb.durata_effettiva_min if fb else None,
            energia_pre=fb.energia_pre if fb else None,
            energia_post=fb.energia_post if fb else None,
            soddisfazione=fb.soddisfazione if fb else None,
            difficolta_percepita=fb.difficolta_percepita if fb else None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        session.add(wl)
        session.flush()
        slot.id_log = wl.id
    else:
        if body.note_sessione:
            wl_for_slot.note = body.note_sessione
        if fb:
            wl_for_slot.durata_effettiva_min = fb.durata_effettiva_min
            wl_for_slot.energia_pre = fb.energia_pre
            wl_for_slot.energia_post = fb.energia_post
            wl_for_slot.soddisfazione = fb.soddisfazione
            wl_for_slot.difficolta_percepita = fb.difficolta_percepita
        session.add(wl_for_slot)

    # Determina stato: completato se tutti compilati, parziale se solo alcuni
    logged_count = len(body.exercises)
    total_exercises = len(valid_exercise_ids)
    if logged_count >= total_exercises:
        slot.stato = "completato"
    elif logged_count > 0:
        slot.stato = "parziale"

    session.add(slot)
    session.commit()

    # Calcola completion percentage
    total_slots = session.exec(
        select(func.count(WorkoutScheduleSlot.id)).where(
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).one()

    completed_slots = session.exec(
        select(func.count(WorkoutScheduleSlot.id)).where(
            WorkoutScheduleSlot.id_scheda == share.id_scheda,
            WorkoutScheduleSlot.stato.in_(["completato", "parziale"]),
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        )
    ).one()

    pct = round(completed_slots / total_slots * 100) if total_slots > 0 else 0

    logger.info(
        "Workout log da client portal: client=%d slot=%d exercises=%d/%d",
        share.client_id, slot_id, logged_count, total_exercises,
    )

    return WorkoutLogResponse(
        success=True,
        message="Sessione salvata!",
        completion_pct=pct,
    )
