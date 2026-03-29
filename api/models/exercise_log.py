# api/models/exercise_log.py
"""
Modello ExerciseLog — dati effettivi per-esercizio inseriti dal cliente.

Il piano del trainer (esercizi_sessione) e' sacro e immutabile dal cliente.
ExerciseLog registra cosa il cliente ha REALMENTE eseguito per ogni esercizio
in ogni slot del calendario (workout_schedule).

Relazione:
  1 WorkoutExercise (piano) → N ExerciseLog (1 per ogni slot in cui viene eseguito)
  1 WorkoutScheduleSlot → N ExerciseLog (1 per ogni esercizio della sessione)

Questo permette di confrontare l'evoluzione dello stesso esercizio nel tempo
(es. panca piana settimana 1 vs settimana 4).

Multi-tenancy: trainer_id FK diretta (stessa strategia di WorkoutLog).
Deep IDOR: id_schedule_slot → WorkoutScheduleSlot.trainer_id
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class ExerciseLog(SQLModel, table=True):
    """Dati effettivi per-esercizio inseriti dal cliente via portale pubblico."""

    __tablename__ = "exercise_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relazioni strutturali
    id_schedule_slot: int = Field(
        foreign_key="workout_schedule.id", index=True
    )
    id_esercizio_sessione: int = Field(
        foreign_key="esercizi_sessione.id", index=True
    )

    # Multi-tenancy (stessa strategia di WorkoutLog)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)

    # Dati effettivi (tutti nullable — il cliente compila quello che vuole)
    serie_effettive: Optional[int] = None
    ripetizioni_effettive: Optional[str] = None      # es. "10,10,8" o "10"
    carico_effettivo_kg: Optional[float] = None       # NULL = bodyweight
    rpe: Optional[float] = None                       # 0-10, percezione sforzo
    note_cliente: Optional[str] = None                # feedback libero

    # Source: chi ha inserito i dati
    source: str = Field(default="client_portal")      # client_portal | trainer

    # Timestamps
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: Optional[str] = None
    deleted_at: Optional[datetime] = None
