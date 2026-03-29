# api/routers/workout_analytics.py
"""
Workout Analytics — metriche derivate dai dati effettivi del cliente.

Tutto calcolato on-the-fly da exercise_logs + allenamenti_eseguiti.
Zero tabelle aggiuntive. Il Training Science Engine ha i dati pianificati,
qui abbiamo i dati REALI.

Endpoint:
  GET /api/clients/{id}/workout-analytics  → WorkoutAnalyticsResponse
    - volume_per_sessione: volume totale (serie×reps×kg) per sessione nel tempo
    - progressione: carico per esercizio nel tempo (curva di forza)
    - personal_records: PR (max carico) per esercizio
    - rpe_trend: RPE medio per sessione nel tempo
    - aderenza: completate/pianificate + streak
    - feedback_trend: soddisfazione/energia/difficolta nel tempo
"""

import logging
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.exercise import Exercise
from api.models.exercise_log import ExerciseLog
from api.models.trainer import Trainer
from api.models.workout_log import WorkoutLog
from api.models.workout_schedule import WorkoutScheduleSlot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["workout-analytics"])


# ── Response schemas ──────────────────────────────────────────────────────────

class VolumePoint(BaseModel):
    data: date
    volume_kg: float         # serie × reps × kg sommato
    sessione_nome: str | None = None


class ProgressionPoint(BaseModel):
    data: date
    carico_kg: float
    serie: int
    ripetizioni: str


class ExerciseProgression(BaseModel):
    id_esercizio: int
    nome_esercizio: str
    punti: list[ProgressionPoint]


class PersonalRecord(BaseModel):
    id_esercizio: int
    nome_esercizio: str
    max_carico_kg: float
    data_pr: date
    estimated_1rm: float | None = None  # Epley: peso × (1 + reps/30)


class RPEPoint(BaseModel):
    data: date
    rpe_medio: float
    sessione_nome: str | None = None


class FeedbackPoint(BaseModel):
    data: date
    soddisfazione: int | None = None
    energia_pre: int | None = None
    energia_post: int | None = None
    difficolta_percepita: int | None = None


class AderenzaStats(BaseModel):
    totale_pianificate: int
    totale_completate: int
    totale_parziali: int
    totale_saltate: int
    percentuale: float              # (completate+parziali) / pianificate × 100
    streak_corrente: int            # sessioni consecutive completate
    streak_massimo: int


class WorkoutAnalyticsResponse(BaseModel):
    volume: list[VolumePoint]
    progressione: list[ExerciseProgression]
    personal_records: list[PersonalRecord]
    rpe_trend: list[RPEPoint]
    feedback_trend: list[FeedbackPoint]
    aderenza: AderenzaStats


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_first_rep(ripetizioni: str | None) -> int:
    """Estrae il primo numero da una stringa reps (es. '10,10,8' → 10, '8-12' → 10)."""
    if not ripetizioni:
        return 0
    clean = ripetizioni.strip().split(",")[0].strip()
    if "-" in clean:
        parts = clean.split("-")
        try:
            return round((int(parts[0]) + int(parts[1])) / 2)
        except (ValueError, IndexError):
            return 0
    try:
        return int(clean)
    except ValueError:
        return 0


def _compute_streaks(slots: list[WorkoutScheduleSlot]) -> tuple[int, int]:
    """Calcola streak corrente e massimo da slot ordinati per data."""
    if not slots:
        return 0, 0
    current = 0
    max_streak = 0
    for s in sorted(slots, key=lambda x: x.data_pianificata):
        if s.stato in ("completato", "parziale"):
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return current, max_streak


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.get(
    "/{client_id}/workout-analytics",
    response_model=WorkoutAnalyticsResponse,
    summary="Metriche derivate dai dati effettivi del cliente",
)
def get_workout_analytics(
    client_id: int,
    mesi: int = Query(default=3, ge=1, le=12, description="Finestra temporale in mesi"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
) -> WorkoutAnalyticsResponse:
    # Bouncer
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    since = date.today() - timedelta(days=mesi * 30)

    # ── Fetch all exercise logs for this client in window ─────────────

    logs = session.exec(
        select(ExerciseLog).where(
            ExerciseLog.id_cliente == client_id,
            ExerciseLog.trainer_id == trainer.id,
            ExerciseLog.deleted_at == None,  # noqa: E711
        )
    ).all()

    # ── Fetch workout logs (session-level) ────────────────────────────

    wlogs = session.exec(
        select(WorkoutLog).where(
            WorkoutLog.id_cliente == client_id,
            WorkoutLog.trainer_id == trainer.id,
            WorkoutLog.data_esecuzione >= since,
            WorkoutLog.deleted_at == None,  # noqa: E711
        ).order_by(WorkoutLog.data_esecuzione)
    ).all()

    # ── Fetch schedule slots ──────────────────────────────────────────

    slots = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_cliente == client_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.data_pianificata >= since,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        ).order_by(WorkoutScheduleSlot.data_pianificata)
    ).all()

    # Map slot_id → data for joining logs to dates
    slot_date_map: dict[int, date] = {s.id: s.data_pianificata for s in slots}
    # Map slot_id → sessione nome (from workout session)
    from api.models.workout import WorkoutSession
    sess_ids = list({s.id_sessione for s in slots})
    sess_map: dict[int, str] = {}
    if sess_ids:
        ws_list = session.exec(
            select(WorkoutSession).where(WorkoutSession.id.in_(sess_ids))
        ).all()
        sess_map = {ws.id: ws.nome_sessione for ws in ws_list}

    slot_sessione_map: dict[int, str] = {}
    for s in slots:
        slot_sessione_map[s.id] = sess_map.get(s.id_sessione, "")

    # ── 1. Volume per sessione ────────────────────────────────────────

    volume_by_slot: dict[int, float] = defaultdict(float)
    for log in logs:
        if log.id_schedule_slot not in slot_date_map:
            continue
        reps = _parse_first_rep(log.ripetizioni_effettive)
        serie = log.serie_effettive or 0
        kg = log.carico_effettivo_kg or 0
        volume_by_slot[log.id_schedule_slot] += serie * reps * kg

    volume_points = sorted([
        VolumePoint(
            data=slot_date_map[sid],
            volume_kg=round(vol, 1),
            sessione_nome=slot_sessione_map.get(sid),
        )
        for sid, vol in volume_by_slot.items()
        if slot_date_map[sid] >= since
    ], key=lambda p: p.data)

    # ── 2. Progressione carico per esercizio ──────────────────────────

    # Map esercizio_sessione.id → id_esercizio (catalog)
    from api.models.workout import WorkoutExercise
    ex_sess_ids = list({log.id_esercizio_sessione for log in logs})
    catalog_id_map: dict[int, int] = {}
    if ex_sess_ids:
        ex_rows = session.exec(
            select(WorkoutExercise.id, WorkoutExercise.id_esercizio).where(
                WorkoutExercise.id.in_(ex_sess_ids)
            )
        ).all()
        catalog_id_map = {row[0]: row[1] for row in ex_rows}

    unique_catalog_ids = list(set(catalog_id_map.values()))
    catalog_names: dict[int, str] = {}
    if unique_catalog_ids:
        cat_rows = catalog_session.exec(
            select(Exercise.id, Exercise.nome).where(
                Exercise.id.in_(unique_catalog_ids)
            )
        ).all()
        catalog_names = {row[0]: row[1] for row in cat_rows}

    # Group logs by catalog exercise id
    prog_data: dict[int, list[tuple[date, float, int, str]]] = defaultdict(list)
    for log in logs:
        if log.id_schedule_slot not in slot_date_map:
            continue
        if log.carico_effettivo_kg is None:
            continue
        cat_id = catalog_id_map.get(log.id_esercizio_sessione)
        if not cat_id:
            continue
        d = slot_date_map[log.id_schedule_slot]
        if d >= since:
            prog_data[cat_id].append((
                d,
                log.carico_effettivo_kg,
                log.serie_effettive or 0,
                log.ripetizioni_effettive or "",
            ))

    progressione = []
    for cat_id, points in prog_data.items():
        sorted_pts = sorted(points, key=lambda x: x[0])
        progressione.append(ExerciseProgression(
            id_esercizio=cat_id,
            nome_esercizio=catalog_names.get(cat_id, f"Esercizio #{cat_id}"),
            punti=[ProgressionPoint(data=p[0], carico_kg=p[1], serie=p[2], ripetizioni=p[3]) for p in sorted_pts],
        ))
    progressione.sort(key=lambda x: x.nome_esercizio)

    # ── 3. Personal Records ───────────────────────────────────────────

    pr_map: dict[int, tuple[float, date, int, str]] = {}  # cat_id → (max_kg, date, serie, reps)
    for log in logs:
        if log.carico_effettivo_kg is None or log.carico_effettivo_kg <= 0:
            continue
        cat_id = catalog_id_map.get(log.id_esercizio_sessione)
        if not cat_id:
            continue
        d = slot_date_map.get(log.id_schedule_slot)
        if not d:
            continue
        curr = pr_map.get(cat_id)
        if not curr or log.carico_effettivo_kg > curr[0]:
            pr_map[cat_id] = (
                log.carico_effettivo_kg, d,
                log.serie_effettive or 0,
                log.ripetizioni_effettive or "",
            )

    personal_records = []
    for cat_id, (kg, d, serie, reps) in pr_map.items():
        rep_count = _parse_first_rep(reps)
        e1rm = round(kg * (1 + rep_count / 30), 1) if rep_count > 0 else None
        personal_records.append(PersonalRecord(
            id_esercizio=cat_id,
            nome_esercizio=catalog_names.get(cat_id, f"Esercizio #{cat_id}"),
            max_carico_kg=kg,
            data_pr=d,
            estimated_1rm=e1rm,
        ))
    personal_records.sort(key=lambda x: x.nome_esercizio)

    # ── 4. RPE trend ──────────────────────────────────────────────────

    rpe_by_slot: dict[int, list[float]] = defaultdict(list)
    for log in logs:
        if log.rpe is not None and log.id_schedule_slot in slot_date_map:
            rpe_by_slot[log.id_schedule_slot].append(log.rpe)

    rpe_trend = sorted([
        RPEPoint(
            data=slot_date_map[sid],
            rpe_medio=round(sum(vals) / len(vals), 1),
            sessione_nome=slot_sessione_map.get(sid),
        )
        for sid, vals in rpe_by_slot.items()
        if slot_date_map[sid] >= since
    ], key=lambda p: p.data)

    # ── 5. Feedback trend ─────────────────────────────────────────────

    feedback_trend = [
        FeedbackPoint(
            data=wl.data_esecuzione,
            soddisfazione=wl.soddisfazione,
            energia_pre=wl.energia_pre,
            energia_post=wl.energia_post,
            difficolta_percepita=wl.difficolta_percepita,
        )
        for wl in wlogs
        if wl.soddisfazione is not None or wl.energia_pre is not None
    ]

    # ── 6. Aderenza ───────────────────────────────────────────────────

    totale = len(slots)
    completate = sum(1 for s in slots if s.stato == "completato")
    parziali = sum(1 for s in slots if s.stato == "parziale")
    saltate = sum(1 for s in slots if s.stato == "saltato")
    pct = round((completate + parziali) / totale * 100, 1) if totale > 0 else 0
    streak_corrente, streak_max = _compute_streaks(slots)

    aderenza = AderenzaStats(
        totale_pianificate=totale,
        totale_completate=completate,
        totale_parziali=parziali,
        totale_saltate=saltate,
        percentuale=pct,
        streak_corrente=streak_corrente,
        streak_massimo=streak_max,
    )

    return WorkoutAnalyticsResponse(
        volume=volume_points,
        progressione=progressione,
        personal_records=personal_records,
        rpe_trend=rpe_trend,
        feedback_trend=feedback_trend,
        aderenza=aderenza,
    )
