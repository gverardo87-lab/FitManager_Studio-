# api/routers/training_intelligence.py
"""
Training Intelligence — analisi scientifica post-esecuzione.

Bridge tra dati REALI (ExerciseLog) e Training Science Engine (MEV/MAV/MRV,
balance ratios, intensity zones). Nessun competitor al mondo incrocia piano
scientifico e esecuzione effettiva muscolo-per-muscolo con target NSCA
personalizzati per demografia.

Endpoint:
  GET /api/clients/{id}/training-intelligence → TrainingIntelligenceResponse
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from api.database import get_catalog_session, get_session
from api.dependencies import get_current_trainer
from api.models.client import Client
from api.models.exercise import Exercise
from api.models.exercise_log import ExerciseLog
from api.models.trainer import Trainer
from api.models.workout import WorkoutExercise, WorkoutPlan
from api.models.workout_log import WorkoutLog
from api.models.workout_schedule import WorkoutScheduleSlot
from api.services.training_science.load_model import classify_intensity_zone
from api.services.training_science.muscle_contribution import (
    DB_PATTERN_MAP,
    ISOLATION_INFERENCE,
    compute_hypertrophy_sets,
    get_contribution,
)
from api.services.training_science.types import (
    GruppoMuscolare as M,
    Livello,
    Obiettivo,
    PatternMovimento as P,
)
from api.services.training_science.volume_model import (
    classify_volume,
    get_scaled_volume_target,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["training-intelligence"])


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════


class MuscleAnalysis(BaseModel):
    muscolo: str
    volume_effettivo: float = Field(description="Serie ipertrofiche/settimana reali")
    mev: float
    mav_min: float
    mav_max: float
    mrv: float
    stato: str  # sotto_mev | mev_mav | ottimale | sopra_mav | sopra_mrv
    trend: str = Field(default="stabile", description="crescente | stabile | calante")
    pianificato: Optional[float] = None


class FrequencyAnalysis(BaseModel):
    muscolo: str
    freq_effettiva: float = Field(description="Stimoli/settimana reali")
    freq_target_min: int = 2
    freq_target_max: int = 3


class BalanceRatioAnalysis(BaseModel):
    nome: str
    valore_corrente: float
    target: float
    tolleranza: float
    in_tolleranza: bool
    trend: str = Field(default="stabile")


class IntensityDistribution(BaseModel):
    massimale: float = 0
    sub_massimale: float = 0
    ipertrofia: float = 0
    resistenza: float = 0
    attivazione: float = 0


class RecoveryWarning(BaseModel):
    sessione_a: str
    sessione_b: str
    muscoli_overlap: list[str]


class TonnagePoint(BaseModel):
    data: date
    tonnage_kg: float
    sessione_nome: str | None = None


class DensityPoint(BaseModel):
    data: date
    tonnage_per_min: float
    sessione_nome: str | None = None


class TrainingAlert(BaseModel):
    tipo: str  # sotto_mev | sopra_mrv | squilibrio | recovery
    muscolo: str | None = None
    settimane: int = 0
    severity: str = "warning"  # warning | danger | info
    messaggio: str = ""


class TrainingIntelligenceResponse(BaseModel):
    # Livello 1 — Execution
    tonnage_trend: list[TonnagePoint]
    density_trend: list[DensityPoint]
    tonnage_totale_periodo: float = 0
    densita_media: float = 0

    # Livello 2 — Dose-Response
    muscle_analysis: list[MuscleAnalysis]
    frequency_analysis: list[FrequencyAnalysis]

    # Livello 3 — Predictive
    balance_ratios: list[BalanceRatioAnalysis]
    intensity_distribution: IntensityDistribution
    recovery_warnings: list[RecoveryWarning]
    alerts: list[TrainingAlert]

    # Metadati
    settimane_analizzate: int = 0
    sessioni_completate: int = 0
    obiettivo_cliente: str | None = None
    livello_cliente: str | None = None
    sesso_cliente: str | None = None
    eta_cliente: int | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _resolve_pattern(
    pattern_db: str | None,
    categoria: str | None = None,
    muscolo_primario: str | None = None,
) -> P | None:
    """Risolve pattern DB → PatternMovimento del motore scientifico."""
    if pattern_db and pattern_db in DB_PATTERN_MAP:
        result = DB_PATTERN_MAP[pattern_db]
        if result is not None:
            return result
    if categoria == "isolation" and muscolo_primario:
        return ISOLATION_INFERENCE.get(muscolo_primario)
    return None


def _parse_reps_avg(reps_str: str | None) -> float:
    """Estrae la media reps da stringa tipo '10,10,8' o '8-12'."""
    if not reps_str:
        return 0
    parts = reps_str.strip().split(",")
    nums = []
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
    return sum(nums) / len(nums) if nums else 0


def _livello_from_str(s: str | None) -> Livello:
    """Converte stringa livello (anche inglese) a Livello enum."""
    if not s:
        return Livello.INTERMEDIO
    low = s.lower()
    MAP = {
        "principiante": Livello.PRINCIPIANTE, "beginner": Livello.PRINCIPIANTE,
        "intermedio": Livello.INTERMEDIO, "intermediate": Livello.INTERMEDIO,
        "avanzato": Livello.AVANZATO, "advanced": Livello.AVANZATO,
    }
    return MAP.get(low, Livello.INTERMEDIO)


def _obiettivo_from_str(s: str | None) -> Obiettivo:
    """Converte stringa obiettivo a Obiettivo enum."""
    if not s:
        return Obiettivo.IPERTROFIA
    low = s.lower()
    MAP = {
        "forza": Obiettivo.FORZA, "ipertrofia": Obiettivo.IPERTROFIA,
        "resistenza": Obiettivo.RESISTENZA, "dimagrimento": Obiettivo.DIMAGRIMENTO,
        "tonificazione": Obiettivo.TONIFICAZIONE, "generale": Obiettivo.IPERTROFIA,
    }
    return MAP.get(low, Obiettivo.IPERTROFIA)


def _compute_weekly_muscle_volume(
    weekly_slots: list[tuple[P, int]],
) -> dict[M, float]:
    """Calcola volume ipertrofico settimanale per muscolo da slot (pattern, serie)."""
    return compute_hypertrophy_sets(weekly_slots)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/{client_id}/training-intelligence",
    response_model=TrainingIntelligenceResponse,
    summary="Analisi scientifica post-esecuzione (dose-response, muscolo-per-muscolo)",
)
def get_training_intelligence(
    client_id: int,
    mesi: int = Query(default=3, ge=1, le=12),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
) -> TrainingIntelligenceResponse:
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

    # ── Client demographics ──────────────────────────────────────────────
    sesso = getattr(client, "sesso", None)
    eta = None
    if hasattr(client, "data_nascita") and client.data_nascita:
        try:
            dn = client.data_nascita
            if isinstance(dn, str):
                dn = date.fromisoformat(dn)
            eta = (date.today() - dn).days // 365
        except Exception:
            pass

    # ── Active workout plan → obiettivo + livello ────────────────────────
    active_plan = session.exec(
        select(WorkoutPlan).where(
            WorkoutPlan.id_cliente == client_id,
            WorkoutPlan.trainer_id == trainer.id,
            WorkoutPlan.deleted_at == None,  # noqa: E711
        ).order_by(WorkoutPlan.created_at.desc())  # type: ignore[union-attr]
    ).first()

    obiettivo_str = active_plan.obiettivo if active_plan else None
    livello_str = active_plan.livello if active_plan else None
    obiettivo = _obiettivo_from_str(obiettivo_str)
    livello = _livello_from_str(livello_str)

    # ── Fetch exercise logs ──────────────────────────────────────────────
    logs = session.exec(
        select(ExerciseLog).where(
            ExerciseLog.id_cliente == client_id,
            ExerciseLog.trainer_id == trainer.id,
            ExerciseLog.deleted_at == None,  # noqa: E711
        )
    ).all()

    # ── Fetch schedule slots ─────────────────────────────────────────────
    slots = session.exec(
        select(WorkoutScheduleSlot).where(
            WorkoutScheduleSlot.id_cliente == client_id,
            WorkoutScheduleSlot.trainer_id == trainer.id,
            WorkoutScheduleSlot.data_pianificata >= since,
            WorkoutScheduleSlot.deleted_at == None,  # noqa: E711
        ).order_by(WorkoutScheduleSlot.data_pianificata)
    ).all()

    slot_date: dict[int, date] = {s.id: s.data_pianificata for s in slots}

    # ── Fetch workout logs (session-level feedback) ──────────────────────
    wlogs = session.exec(
        select(WorkoutLog).where(
            WorkoutLog.id_cliente == client_id,
            WorkoutLog.trainer_id == trainer.id,
            WorkoutLog.data_esecuzione >= since,
            WorkoutLog.deleted_at == None,  # noqa: E711
        )
    ).all()
    wlog_by_slot: dict[int, WorkoutLog] = {}
    for wl in wlogs:
        for s in slots:
            if s.id_log == wl.id:
                wlog_by_slot[s.id] = wl

    # ── Map esercizio_sessione → catalog exercise ────────────────────────
    ex_sess_ids = list({log.id_esercizio_sessione for log in logs})
    catalog_id_map: dict[int, int] = {}
    if ex_sess_ids:
        rows = session.exec(
            select(WorkoutExercise.id, WorkoutExercise.id_esercizio).where(
                WorkoutExercise.id.in_(ex_sess_ids)
            )
        ).all()
        catalog_id_map = {r[0]: r[1] for r in rows}

    unique_cat_ids = list(set(catalog_id_map.values()))
    exercises_map: dict[int, Exercise] = {}
    if unique_cat_ids:
        exs = catalog_session.exec(
            select(Exercise).where(Exercise.id.in_(unique_cat_ids))
        ).all()
        exercises_map = {e.id: e for e in exs}

    # ── Session names ────────────────────────────────────────────────────
    from api.models.workout import WorkoutSession
    sess_ids_set = list({s.id_sessione for s in slots})
    sess_name_map: dict[int, str] = {}
    if sess_ids_set:
        ws_list = session.exec(
            select(WorkoutSession).where(WorkoutSession.id.in_(sess_ids_set))
        ).all()
        sess_name_map = {ws.id: ws.nome_sessione for ws in ws_list}
    slot_sessione_name: dict[int, str] = {
        s.id: sess_name_map.get(s.id_sessione, "") for s in slots
    }

    completed_slot_ids = {
        s.id for s in slots if s.stato in ("completato", "parziale")
    }

    # ═════════════════════════════════════════════════════════════════════
    # LIVELLO 1 — Execution Metrics (tonnage + density)
    # ═════════════════════════════════════════════════════════════════════

    tonnage_by_slot: dict[int, float] = defaultdict(float)
    for log in logs:
        if log.id_schedule_slot not in slot_date:
            continue
        serie = log.serie_effettive or 0
        reps = _parse_reps_avg(log.ripetizioni_effettive)
        kg = log.carico_effettivo_kg or 0
        tonnage_by_slot[log.id_schedule_slot] += serie * reps * kg

    tonnage_trend = sorted([
        TonnagePoint(
            data=slot_date[sid],
            tonnage_kg=round(vol, 1),
            sessione_nome=slot_sessione_name.get(sid),
        )
        for sid, vol in tonnage_by_slot.items()
        if slot_date[sid] >= since and vol > 0
    ], key=lambda p: p.data)

    # Density: tonnage / minuti effettivi
    density_trend: list[DensityPoint] = []
    for sid, vol in tonnage_by_slot.items():
        if vol <= 0 or slot_date.get(sid, date.min) < since:
            continue
        wl = wlog_by_slot.get(sid)
        dur = wl.durata_effettiva_min if wl and wl.durata_effettiva_min else None
        if dur and dur > 0:
            density_trend.append(DensityPoint(
                data=slot_date[sid],
                tonnage_per_min=round(vol / dur, 1),
                sessione_nome=slot_sessione_name.get(sid),
            ))
    density_trend.sort(key=lambda p: p.data)

    tonnage_tot = sum(p.tonnage_kg for p in tonnage_trend)
    density_avg = (
        round(sum(d.tonnage_per_min for d in density_trend) / len(density_trend), 1)
        if density_trend else 0
    )

    # ═════════════════════════════════════════════════════════════════════
    # LIVELLO 2 — Dose-Response per muscolo
    # ═════════════════════════════════════════════════════════════════════

    # Accumulate per-week muscle volume from real execution
    # Week key: ISO week number
    week_slots: dict[str, list[tuple[P, int]]] = defaultdict(list)

    for log in logs:
        if log.id_schedule_slot not in slot_date:
            continue
        d = slot_date[log.id_schedule_slot]
        if d < since:
            continue
        cat_id = catalog_id_map.get(log.id_esercizio_sessione)
        if not cat_id:
            continue
        ex = exercises_map.get(cat_id)
        if not ex:
            continue
        import json
        mp_raw = None
        try:
            mp_list = json.loads(ex.muscoli_primari) if ex.muscoli_primari else []
            mp_raw = mp_list[0] if mp_list else None
        except Exception:
            pass
        pattern = _resolve_pattern(ex.pattern_movimento, ex.categoria, mp_raw)
        if not pattern:
            continue
        serie = log.serie_effettive or 0
        if serie <= 0:
            continue
        week_key = f"{d.isocalendar()[0]}-{d.isocalendar()[1]:02d}"
        week_slots[week_key].append((pattern, serie))

    # Average weekly volume per muscle
    if week_slots:
        muscle_weekly: dict[M, list[float]] = defaultdict(list)
        for wk, wk_slots in week_slots.items():
            hyp = compute_hypertrophy_sets(wk_slots)
            for m in M:
                muscle_weekly[m].append(hyp.get(m, 0.0))

        muscle_avg: dict[M, float] = {
            m: round(sum(vals) / len(vals), 1) for m, vals in muscle_weekly.items()
        }
    else:
        muscle_avg = {m: 0.0 for m in M}

    # Trend: compare last 2 weeks vs first 2 weeks
    sorted_weeks = sorted(week_slots.keys())
    muscle_trend: dict[M, str] = {}
    if len(sorted_weeks) >= 4:
        first_2 = sorted_weeks[:2]
        last_2 = sorted_weeks[-2:]
        for m in M:
            early = sum(
                compute_hypertrophy_sets(week_slots[w]).get(m, 0)
                for w in first_2
            ) / 2
            late = sum(
                compute_hypertrophy_sets(week_slots[w]).get(m, 0)
                for w in last_2
            ) / 2
            diff = late - early
            if diff > 1.5:
                muscle_trend[m] = "crescente"
            elif diff < -1.5:
                muscle_trend[m] = "calante"
            else:
                muscle_trend[m] = "stabile"
    else:
        muscle_trend = {m: "stabile" for m in M}

    # Build muscle analysis with MEV/MAV/MRV targets
    muscle_analysis: list[MuscleAnalysis] = []
    for m in M:
        vol = muscle_avg[m]
        target = get_scaled_volume_target(m, livello, obiettivo, sesso, eta)
        stato = classify_volume(vol, target)
        muscle_analysis.append(MuscleAnalysis(
            muscolo=m.value,
            volume_effettivo=vol,
            mev=target.mev,
            mav_min=target.mav_min,
            mav_max=target.mav_max,
            mrv=target.mrv,
            stato=stato,
            trend=muscle_trend.get(m, "stabile"),
        ))

    # ── Frequency analysis ───────────────────────────────────────────────
    muscle_freq: dict[M, list[int]] = defaultdict(list)
    for wk, wk_slots in week_slots.items():
        stimulated: set[M] = set()
        for pattern, serie in wk_slots:
            for m, c in get_contribution(pattern).items():
                if c >= 0.4 and serie > 0:
                    stimulated.add(m)
        for m in M:
            muscle_freq[m].append(1 if m in stimulated else 0)

    frequency_analysis: list[FrequencyAnalysis] = []
    for m in M:
        vals = muscle_freq.get(m, [])
        avg_f = round(sum(vals) / len(vals), 1) if vals else 0
        frequency_analysis.append(FrequencyAnalysis(
            muscolo=m.value,
            freq_effettiva=avg_f,
        ))

    # ═════════════════════════════════════════════════════════════════════
    # LIVELLO 3 — Balance Ratios + Intensity + Recovery + Alerts
    # ═════════════════════════════════════════════════════════════════════

    # Balance ratios from effective volume
    all_slots_flat: list[tuple[P, int]] = []
    for wk_slots_list in week_slots.values():
        all_slots_flat.extend(wk_slots_list)

    # Compute effective sets (full EMG, not hypertrophy-discounted) for ratios
    from api.services.training_science.balance_ratios import (
        BALANCE_RATIOS as BR_LIST,
        _sum_muscle_sets,
        _sum_pattern_sets,
    )
    hyp_all = compute_hypertrophy_sets(all_slots_flat) if all_slots_flat else {}

    balance_ratios: list[BalanceRatioAnalysis] = []
    for ratio in BR_LIST:
        is_pattern = ratio.numeratore[0] in {p.value for p in P}
        if is_pattern:
            num_p = {P(v) for v in ratio.numeratore if v in {p.value for p in P}}
            den_p = {P(v) for v in ratio.denominatore if v in {p.value for p in P}}
            num_val = _sum_pattern_sets(all_slots_flat, num_p)
            den_val = _sum_pattern_sets(all_slots_flat, den_p)
        else:
            num_val = _sum_muscle_sets(hyp_all, ratio.numeratore)
            den_val = _sum_muscle_sets(hyp_all, ratio.denominatore)

        if den_val > 0:
            computed = round(num_val / den_val, 2)
        elif num_val > 0:
            computed = 99.0
        else:
            computed = ratio.target

        balance_ratios.append(BalanceRatioAnalysis(
            nome=ratio.nome,
            valore_corrente=computed,
            target=ratio.target,
            tolleranza=ratio.tolleranza,
            in_tolleranza=abs(computed - ratio.target) <= ratio.tolleranza,
        ))

    # ── Intensity distribution ───────────────────────────────────────────
    zone_counts: dict[str, int] = defaultdict(int)
    total_sets_with_load = 0
    for log in logs:
        if log.id_schedule_slot not in slot_date:
            continue
        if slot_date[log.id_schedule_slot] < since:
            continue
        if not log.carico_effettivo_kg or log.carico_effettivo_kg <= 0:
            continue
        reps = _parse_reps_avg(log.ripetizioni_effettive)
        if reps <= 0:
            continue
        # Estimate 1RM: Epley per 1-15 reps (validato), Brzycki per 16-36 reps
        # (migliore per endurance — Brzycki 1993). Skip reps >= 37 (formula diverge).
        if reps >= 37:
            continue
        if reps <= 15:
            e1rm = log.carico_effettivo_kg * (1 + reps / 30)  # Epley 1985
        else:
            e1rm = log.carico_effettivo_kg * 36 / (37 - reps)  # Brzycki 1993
        pct = log.carico_effettivo_kg / e1rm if e1rm > 0 else 0
        zona, _ = classify_intensity_zone(pct)
        serie = log.serie_effettive or 1
        zone_counts[zona] += serie
        total_sets_with_load += serie

    intensity_distribution = IntensityDistribution()
    if total_sets_with_load > 0:
        intensity_distribution = IntensityDistribution(
            massimale=round(zone_counts.get("massimale", 0) / total_sets_with_load * 100, 1),
            sub_massimale=round(zone_counts.get("sub_massimale", 0) / total_sets_with_load * 100, 1),
            ipertrofia=round(zone_counts.get("ipertrofia", 0) / total_sets_with_load * 100, 1),
            resistenza=round(zone_counts.get("resistenza", 0) / total_sets_with_load * 100, 1),
            attivazione=round(zone_counts.get("attivazione", 0) / total_sets_with_load * 100, 1),
        )

    # ── Recovery warnings (consecutive sessions same day or adjacent) ────
    recovery_warnings: list[RecoveryWarning] = []
    slot_by_date: dict[date, list[int]] = defaultdict(list)
    for s in slots:
        if s.stato in ("completato", "parziale"):
            slot_by_date[s.data_pianificata].append(s.id)

    sorted_dates = sorted(slot_by_date.keys())
    for i in range(len(sorted_dates) - 1):
        d1, d2 = sorted_dates[i], sorted_dates[i + 1]
        if (d2 - d1).days > 1:
            continue
        # Get muscles worked on each day
        muscles_d1: dict[M, float] = defaultdict(float)
        muscles_d2: dict[M, float] = defaultdict(float)
        for log in logs:
            if log.id_schedule_slot in slot_by_date.get(d1, []):
                cat_id = catalog_id_map.get(log.id_esercizio_sessione)
                if cat_id:
                    ex = exercises_map.get(cat_id)
                    if ex:
                        import json as json_mod
                        mp = None
                        try:
                            mp_list = json_mod.loads(ex.muscoli_primari) if ex.muscoli_primari else []
                            mp = mp_list[0] if mp_list else None
                        except Exception:
                            pass
                        pat = _resolve_pattern(ex.pattern_movimento, ex.categoria, mp)
                        if pat:
                            for m, c in get_contribution(pat).items():
                                if c >= 0.4:
                                    muscles_d1[m] += (log.serie_effettive or 0) * c
            if log.id_schedule_slot in slot_by_date.get(d2, []):
                cat_id = catalog_id_map.get(log.id_esercizio_sessione)
                if cat_id:
                    ex = exercises_map.get(cat_id)
                    if ex:
                        import json as json_mod2
                        mp = None
                        try:
                            mp_list = json_mod2.loads(ex.muscoli_primari) if ex.muscoli_primari else []
                            mp = mp_list[0] if mp_list else None
                        except Exception:
                            pass
                        pat = _resolve_pattern(ex.pattern_movimento, ex.categoria, mp)
                        if pat:
                            for m, c in get_contribution(pat).items():
                                if c >= 0.4:
                                    muscles_d2[m] += (log.serie_effettive or 0) * c

        overlap = [
            m.value for m in M
            if muscles_d1.get(m, 0) >= 2 and muscles_d2.get(m, 0) >= 2
            and (muscles_d1.get(m, 0) + muscles_d2.get(m, 0)) >= 5
        ]
        if overlap:
            name_d1 = ""
            name_d2 = ""
            for s in slots:
                if s.data_pianificata == d1:
                    name_d1 = slot_sessione_name.get(s.id, str(d1))
                if s.data_pianificata == d2:
                    name_d2 = slot_sessione_name.get(s.id, str(d2))
            recovery_warnings.append(RecoveryWarning(
                sessione_a=name_d1 or str(d1),
                sessione_b=name_d2 or str(d2),
                muscoli_overlap=overlap,
            ))

    # ── Alerts ───────────────────────────────────────────────────────────
    alerts: list[TrainingAlert] = []

    # Muscle volume alerts
    for ma in muscle_analysis:
        if ma.volume_effettivo <= 0:
            continue
        if ma.stato == "sotto_mev":
            alerts.append(TrainingAlert(
                tipo="sotto_mev",
                muscolo=ma.muscolo,
                severity="warning",
                messaggio=f"{ma.muscolo}: volume effettivo ({ma.volume_effettivo}) sotto MEV ({ma.mev}) — nessuno stimolo ipertrofico",
            ))
        elif ma.stato == "sopra_mrv":
            alerts.append(TrainingAlert(
                tipo="sopra_mrv",
                muscolo=ma.muscolo,
                severity="danger",
                messaggio=f"{ma.muscolo}: volume effettivo ({ma.volume_effettivo}) oltre MRV ({ma.mrv}) — rischio sovrallenamento",
            ))

    # Balance alerts
    for br in balance_ratios:
        if not br.in_tolleranza:
            direction = "alto" if br.valore_corrente > br.target else "basso"
            alerts.append(TrainingAlert(
                tipo="squilibrio",
                messaggio=f"{br.nome}: {br.valore_corrente:.2f} (target {br.target:.2f}, troppo {direction})",
                severity="warning",
            ))

    # Recovery alerts
    for rw in recovery_warnings:
        alerts.append(TrainingAlert(
            tipo="recovery",
            messaggio=f"Recupero insufficiente tra {rw.sessione_a} e {rw.sessione_b}: {', '.join(rw.muscoli_overlap)}",
            severity="warning",
        ))

    return TrainingIntelligenceResponse(
        tonnage_trend=tonnage_trend,
        density_trend=density_trend,
        tonnage_totale_periodo=round(tonnage_tot, 1),
        densita_media=density_avg,
        muscle_analysis=muscle_analysis,
        frequency_analysis=frequency_analysis,
        balance_ratios=balance_ratios,
        intensity_distribution=intensity_distribution,
        recovery_warnings=recovery_warnings,
        alerts=alerts,
        settimane_analizzate=len(week_slots),
        sessioni_completate=len(completed_slot_ids),
        obiettivo_cliente=obiettivo_str,
        livello_cliente=livello_str,
        sesso_cliente=sesso,
        eta_cliente=eta,
    )
