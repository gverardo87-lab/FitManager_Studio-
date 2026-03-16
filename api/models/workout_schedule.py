# api/models/workout_schedule.py
"""
Modello WorkoutScheduleSlot — slot pianificato per sessione allenamento.

Registra QUANDO una sessione DOVREBBE essere eseguita (intenzione).
Collegato opzionalmente a WorkoutLog quando viene completato (fatto).

Gerarchia:
  WorkoutPlan → WorkoutSession → WorkoutScheduleSlot → WorkoutLog (opzionale)

Multi-tenancy: trainer_id FK diretta.
Deep IDOR: id_scheda → WorkoutPlan.trainer_id | id_cliente → Client.trainer_id
"""

from datetime import date as date_type, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class WorkoutScheduleSlot(SQLModel, table=True):
    """Slot pianificato — un giorno specifico in cui una sessione va eseguita."""

    __tablename__ = "workout_schedule"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_scheda: int = Field(foreign_key="schede_allenamento.id", index=True)
    id_sessione: int = Field(foreign_key="sessioni_scheda.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    data_pianificata: date_type
    # pianificato | completato | saltato | parziale
    stato: str = Field(default="pianificato")
    id_log: Optional[int] = Field(default=None, foreign_key="allenamenti_eseguiti.id")
    note: Optional[str] = None
    created_at: Optional[str] = None
    deleted_at: Optional[datetime] = None
