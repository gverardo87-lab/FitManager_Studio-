# api/schemas/workout_log.py
"""
Pydantic schemas per workout execution logs.

Input: WorkoutLogCreate (body per POST).
Output: WorkoutLogResponse con nomi enriched da JOINs.
Mass Assignment Prevention: trainer_id e id_cliente da JWT + path param.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# INPUT
# ════════════════════════════════════════════════════════════

class WorkoutLogCreate(BaseModel):
    """Crea log esecuzione sessione. trainer_id + id_cliente da JWT/path."""

    model_config = {"extra": "forbid"}

    id_scheda: int = Field(gt=0)
    id_sessione: int = Field(gt=0)
    data_esecuzione: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    id_evento: Optional[int] = Field(None, gt=0)
    note: Optional[str] = Field(None, max_length=500)


# ════════════════════════════════════════════════════════════
# OUTPUT
# ════════════════════════════════════════════════════════════

class WorkoutLogResponse(BaseModel):
    """Log esecuzione — output enriched con nomi scheda e sessione."""

    id: int
    id_scheda: int
    id_sessione: int
    id_cliente: int
    data_esecuzione: str
    id_evento: Optional[int] = None
    note: Optional[str] = None
    created_at: Optional[str] = None
    scheda_nome: str
    sessione_nome: str


class WorkoutLogListResponse(BaseModel):
    """Lista log esecuzione."""

    items: List[WorkoutLogResponse]
    total: int


# ════════════════════════════════════════════════════════════
# SCHEDULE COMPLETION (body opzionale per complete_slot)
# ════════════════════════════════════════════════════════════

class ExerciseLogTrainerInput(BaseModel):
    """Dati effettivi per singolo esercizio inseriti dal trainer."""

    model_config = {"extra": "forbid"}

    id_esercizio_sessione: int = Field(gt=0)
    serie_effettive: Optional[int] = Field(None, ge=1)
    ripetizioni_effettive: Optional[str] = Field(None, max_length=50)
    carico_effettivo_kg: Optional[float] = Field(None, ge=0)
    rpe: Optional[float] = Field(None, ge=0, le=10)
    note_cliente: Optional[str] = Field(None, max_length=500)


class CompleteSlotRequest(BaseModel):
    """Body opzionale per PUT /workout-schedule/{id}/complete.

    - exercise_data = None → assume piano (source = 'trainer_assumed')
    - exercise_data = [...] → dati inseriti dal trainer (source = 'trainer')
    """

    model_config = {"extra": "forbid"}

    exercise_data: Optional[List[ExerciseLogTrainerInput]] = None
