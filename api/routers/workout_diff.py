# api/routers/workout_diff.py
"""
Workout Diff — il "git diff" dell'allenamento.

Per ogni sessione completata, confronta il piano del trainer (WorkoutExercise)
con l'esecuzione reale del cliente (ExerciseLog), producendo delta per ogni
variabile: serie, ripetizioni, carico.

Il dato piu' importante per un PT: cosa il cliente FA REALMENTE
rispetto a cio' che gli e' stato chiesto.

Endpoint:
  GET /api/clients/{id}/workout-diff → WorkoutDiffResponse
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
from api.models.workout import WorkoutExercise, WorkoutSession
from api.models.workout_schedule import WorkoutScheduleSlot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["workout-diff"])


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class ExerciseDiff(BaseModel):
    """Diff di un singolo esercizio: pianificato vs eseguito."""
    id_esercizio: int
    nome_esercizio: str

    # Pianificato (dal trainer)
    serie_piano: int
    reps_piano: str            # "8-12" originale
    reps_piano_avg: float      # media del range
    kg_piano: float | None     # None = bodyweight/non specificato

    # Eseguito (dal cliente)
    serie_fatto: int | None
    reps_fatto: str | None     # "10,10,8" originale
    reps_fatto_avg: float | None
    kg_fatto: float | None
    rpe: float | None

    # Delta (fatto - piano)
    delta_serie: int | None = None
    delta_reps: float | None = None    # media fatto - media piano
    delta_kg: float | None = None

    # Compliance: quanto ha rispettato il piano (0-100)
    compliance_pct: float | None = None
    note_cliente: str | None = None


class SessionDiff(BaseModel):
    """Diff di una sessione completa."""
    data: date
    nome_sessione: str
    stato: str                         # completato | parziale
    esercizi: list[ExerciseDiff]
    compliance_media: float            # media compliance esercizi (0-100)
    esercizi_completati: int           # quanti esercizi hanno log
    esercizi_totali: int               # quanti esercizi nel piano
    durata_effettiva_min: int | None = None
    note_sessione: str | None = None


class ComplianceSummary(BaseModel):
    """Sommario compliance su tutto il periodo."""
    compliance_media_globale: float    # media compliance tutte le sessioni
    sessioni_analizzate: int
    esercizi_sopra_piano: int          # esercizi dove fatto > piano
    esercizi_sotto_piano: int          # esercizi dove fatto < piano
    esercizi_in_linea: int             # esercizi dove fatto ≈ piano (±10%)
    punti_deboli: list[str]            # top 3 esercizi con compliance piu' bassa
    punti_forti: list[str]             # top 3 esercizi con compliance piu' alta


class WorkoutDiffResponse(BaseModel):
    sessioni: list[SessionDiff]
    summary: ComplianceSummary


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _parse_reps_avg(reps_str: str | None) -> float:
    """Media reps da stringa ('10,10,8' → 9.3, '8-12' → 10)."""
    if not reps_str:
        return 0
    parts = reps_str.strip().split(",")
    nums: list[float] = []
    for p in parts:
        p = p.strip()
        if "-" in p:
            ab = p.split("-")
            try:
                nums.append((int(ab[0]) + int(ab[1])) / 2)
            except (ValueError, IndexError):
                pass
        else:
            try:
                nums.append(float(p))
            except ValueError:
                pass
    return round(sum(nums) / len(nums), 1) if nums else 0


def _compute_compliance(
    serie_piano: int,
    reps_piano_avg: float,
    kg_piano: float | None,
    serie_fatto: int | None,
    reps_fatto_avg: float | None,
    kg_fatto: float | None,
) -> float:
    """
    Compliance 0-100: quanto il cliente ha rispettato il piano.

    Formula pesata:
      - Serie: 40% (il piu' importante — hai fatto le serie?)
      - Reps: 35% (hai fatto le ripetizioni?)
      - Carico: 25% (hai usato il peso giusto?)

    Ogni componente e' min(fatto/piano, 1.2) * 100 — capped a 120% (bonus).
    Se il piano non ha carico, redistribuiamo il peso su serie e reps.
    """
    if serie_fatto is None:
        return 0

    serie_ratio = min((serie_fatto / serie_piano), 1.2) if serie_piano > 0 else 1.0
    reps_ratio = min((reps_fatto_avg / reps_piano_avg), 1.2) if reps_piano_avg > 0 and reps_fatto_avg else 1.0

    if kg_piano and kg_piano > 0 and kg_fatto is not None and kg_fatto > 0:
        kg_ratio = min((kg_fatto / kg_piano), 1.2)
        score = (serie_ratio * 0.40 + reps_ratio * 0.35 + kg_ratio * 0.25) * 100
    else:
        # No carico nel piano → redistribuisci su serie e reps
        score = (serie_ratio * 0.55 + reps_ratio * 0.45) * 100

    return round(min(score, 120), 1)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/{client_id}/workout-diff",
    response_model=WorkoutDiffResponse,
    summary="Diff pianificato vs eseguito per ogni sessione completata",
)
def get_workout_diff(
    client_id: int,
    mesi: int = Query(default=3, ge=1, le=12),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
) -> WorkoutDiffResponse:
    # ── Bouncer ──────────────────────────────────────────────────────────
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

    # ── Fetch completed schedule slots ───────────────────────────────────
    slots = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_cliente == client_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.data_pianificata >= since,
            WorkoutScheduleSlot.stato.in_(["completato", "parziale"]),  # type: ignore[union-attr]
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        ).order_by(WorkoutScheduleSlot.data_pianificata.desc())  # type: ignore[union-attr]
    ).all()

    if not slots:
        return WorkoutDiffResponse(
            sessioni=[],
            summary=ComplianceSummary(
                compliance_media_globale=0,
                sessioni_analizzate=0,
                esercizi_sopra_piano=0,
                esercizi_sotto_piano=0,
                esercizi_in_linea=0,
                punti_deboli=[],
                punti_forti=[],
            ),
        )

    slot_ids = [s.id for s in slots]
    sess_ids = list({s.id_sessione for s in slots})

    # ── Fetch workout sessions (nomi) ────────────────────────────────────
    ws_list = session.exec(
        select(WorkoutSession).where(WorkoutSession.id.in_(sess_ids))
    ).all()
    sess_name_map: dict[int, str] = {ws.id: ws.nome_sessione for ws in ws_list}

    # ── Fetch exercise logs for these slots ──────────────────────────────
    logs = session.exec(
        select(ExerciseLog).where(
            ExerciseLog.id_schedule_slot.in_(slot_ids),  # type: ignore[union-attr]
            ExerciseLog.deleted_at == None,  # noqa: E711
        )
    ).all()

    logs_by_slot: dict[int, list[ExerciseLog]] = defaultdict(list)
    for log in logs:
        logs_by_slot[log.id_schedule_slot].append(log)

    # ── Fetch planned exercises for these sessions ───────────────────────
    exercises_plan = session.exec(
        select(WorkoutExercise).where(
            WorkoutExercise.id_sessione.in_(sess_ids)  # type: ignore[union-attr]
        ).order_by(WorkoutExercise.ordine)
    ).all()

    plan_by_session: dict[int, list[WorkoutExercise]] = defaultdict(list)
    for ex in exercises_plan:
        plan_by_session[ex.id_sessione].append(ex)

    # ── Fetch catalog exercise names ─────────────────────────────────────
    cat_ids = list({ex.id_esercizio for ex in exercises_plan})
    cat_names: dict[int, str] = {}
    if cat_ids:
        cat_rows = catalog_session.exec(
            select(Exercise.id, Exercise.nome).where(Exercise.id.in_(cat_ids))
        ).all()
        cat_names = {r[0]: r[1] for r in cat_rows}

    # ── Fetch workout logs (session feedback) ────────────────────────────
    from api.models.workout_log import WorkoutLog
    wlog_ids = [s.id_log for s in slots if s.id_log]
    wlog_map: dict[int, WorkoutLog] = {}
    if wlog_ids:
        wlogs = session.exec(
            select(WorkoutLog).where(WorkoutLog.id.in_(wlog_ids))
        ).all()
        wlog_map = {wl.id: wl for wl in wlogs}

    # ═════════════════════════════════════════════════════════════════════
    # BUILD DIFFS
    # ═════════════════════════════════════════════════════════════════════

    sessioni_diff: list[SessionDiff] = []
    all_exercise_compliance: dict[str, list[float]] = defaultdict(list)

    for slot in slots:
        planned = plan_by_session.get(slot.id_sessione, [])
        slot_logs = logs_by_slot.get(slot.id, [])

        # Map log by esercizio_sessione_id for quick lookup
        log_by_ex_sess: dict[int, ExerciseLog] = {
            log.id_esercizio_sessione: log for log in slot_logs
        }

        esercizi_diff: list[ExerciseDiff] = []
        completati = 0

        for plan_ex in planned:
            nome = cat_names.get(plan_ex.id_esercizio, f"Esercizio #{plan_ex.id_esercizio}")
            reps_piano_avg = _parse_reps_avg(plan_ex.ripetizioni)

            log = log_by_ex_sess.get(plan_ex.id)

            if log:
                completati += 1
                reps_fatto_avg = _parse_reps_avg(log.ripetizioni_effettive)

                delta_serie = (log.serie_effettive - plan_ex.serie) if log.serie_effettive is not None else None
                delta_reps = round(reps_fatto_avg - reps_piano_avg, 1) if reps_fatto_avg else None
                delta_kg = (
                    round(log.carico_effettivo_kg - plan_ex.carico_kg, 1)
                    if log.carico_effettivo_kg is not None and plan_ex.carico_kg is not None
                    else None
                )

                compliance = _compute_compliance(
                    plan_ex.serie, reps_piano_avg, plan_ex.carico_kg,
                    log.serie_effettive, reps_fatto_avg, log.carico_effettivo_kg,
                )
                all_exercise_compliance[nome].append(compliance)

                esercizi_diff.append(ExerciseDiff(
                    id_esercizio=plan_ex.id_esercizio,
                    nome_esercizio=nome,
                    serie_piano=plan_ex.serie,
                    reps_piano=plan_ex.ripetizioni,
                    reps_piano_avg=reps_piano_avg,
                    kg_piano=plan_ex.carico_kg,
                    serie_fatto=log.serie_effettive,
                    reps_fatto=log.ripetizioni_effettive,
                    reps_fatto_avg=reps_fatto_avg,
                    kg_fatto=log.carico_effettivo_kg,
                    rpe=log.rpe,
                    delta_serie=delta_serie,
                    delta_reps=delta_reps,
                    delta_kg=delta_kg,
                    compliance_pct=compliance,
                    note_cliente=log.note_cliente,
                ))
            else:
                # Esercizio nel piano ma non eseguito
                esercizi_diff.append(ExerciseDiff(
                    id_esercizio=plan_ex.id_esercizio,
                    nome_esercizio=nome,
                    serie_piano=plan_ex.serie,
                    reps_piano=plan_ex.ripetizioni,
                    reps_piano_avg=reps_piano_avg,
                    kg_piano=plan_ex.carico_kg,
                    serie_fatto=None,
                    reps_fatto=None,
                    reps_fatto_avg=None,
                    kg_fatto=None,
                    rpe=None,
                    compliance_pct=0,
                ))

        # Session-level data
        wl = wlog_map.get(slot.id_log) if slot.id_log else None
        compliances = [e.compliance_pct for e in esercizi_diff if e.compliance_pct is not None]
        compliance_media = round(sum(compliances) / len(compliances), 1) if compliances else 0

        sessioni_diff.append(SessionDiff(
            data=slot.data_pianificata,
            nome_sessione=sess_name_map.get(slot.id_sessione, ""),
            stato=slot.stato,
            esercizi=esercizi_diff,
            compliance_media=compliance_media,
            esercizi_completati=completati,
            esercizi_totali=len(planned),
            durata_effettiva_min=wl.durata_effettiva_min if wl else None,
            note_sessione=wl.note if wl else None,
        ))

    # ═════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═════════════════════════════════════════════════════════════════════

    sopra = 0
    sotto = 0
    in_linea = 0
    for sd in sessioni_diff:
        for ex in sd.esercizi:
            if ex.compliance_pct is None or ex.serie_fatto is None:
                sotto += 1  # non eseguito = sotto
            elif ex.compliance_pct >= 105:
                sopra += 1
            elif ex.compliance_pct >= 90:
                in_linea += 1
            else:
                sotto += 1

    # Punti deboli e forti: media compliance per esercizio
    ex_avg: list[tuple[str, float]] = [
        (name, round(sum(vals) / len(vals), 1))
        for name, vals in all_exercise_compliance.items()
        if len(vals) >= 2
    ]
    ex_avg.sort(key=lambda x: x[1])
    punti_deboli = [f"{name} ({avg}%)" for name, avg in ex_avg[:3]]
    punti_forti = [f"{name} ({avg}%)" for name, avg in ex_avg[-3:][::-1]]

    all_session_comp = [s.compliance_media for s in sessioni_diff if s.compliance_media > 0]
    compliance_globale = round(sum(all_session_comp) / len(all_session_comp), 1) if all_session_comp else 0

    return WorkoutDiffResponse(
        sessioni=sessioni_diff,
        summary=ComplianceSummary(
            compliance_media_globale=compliance_globale,
            sessioni_analizzate=len(sessioni_diff),
            esercizi_sopra_piano=sopra,
            esercizi_sotto_piano=sotto,
            esercizi_in_linea=in_linea,
            punti_deboli=punti_deboli,
            punti_forti=punti_forti,
        ),
    )
