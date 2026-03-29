# api/models/workout_log.py
"""
Modello WorkoutLog — log di esecuzione sessione di allenamento.

Registra QUANDO una sessione e' stata eseguita + feedback soggettivo del cliente.
I dati per-esercizio (serie/reps/kg effettivi) sono in ExerciseLog (child table).

Feedback sessione (compilato dal cliente in 10 secondi):
  - durata_effettiva_min: quanto e' durata davvero
  - energia_pre/post: come stava prima e dopo (1-5)
  - soddisfazione: quanto e' soddisfatto della sessione (1-5)
  - difficolta_percepita: quanto l'ha trovata difficile (1-5)

Multi-tenancy: trainer_id FK diretta (stessa strategia di ClientMeasurement).
Deep IDOR: id_scheda -> WorkoutPlan.trainer_id | id_cliente -> Client.trainer_id
"""

from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class WorkoutLog(SQLModel, table=True):
    """Log di esecuzione sessione allenamento + feedback soggettivo."""

    __tablename__ = "allenamenti_eseguiti"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_scheda: int = Field(foreign_key="schede_allenamento.id", index=True)
    id_sessione: int = Field(foreign_key="sessioni_scheda.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    data_esecuzione: date
    id_evento: Optional[int] = Field(default=None, foreign_key="agenda.id")
    note: Optional[str] = None

    # Feedback soggettivo sessione (compilato dal cliente via portale)
    durata_effettiva_min: Optional[int] = None          # minuti effettivi
    energia_pre: Optional[int] = None                    # 1-5
    energia_post: Optional[int] = None                   # 1-5
    soddisfazione: Optional[int] = None                  # 1-5
    difficolta_percepita: Optional[int] = None           # 1-5

    # Source: chi ha creato il log
    source: Optional[str] = None                         # client_portal | trainer

    created_at: Optional[str] = None
    deleted_at: Optional[datetime] = None
