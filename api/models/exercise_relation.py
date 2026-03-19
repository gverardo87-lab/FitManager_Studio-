# api/models/exercise_relation.py
"""
Modello ExerciseRelation — catena progressioni/regressioni tra esercizi.

tipo_relazione:
- "progression" → esercizio piu' difficile
- "regression"  → esercizio piu' facile
- "variation"   → variante equivalente
"""

from typing import Optional
from sqlmodel import SQLModel, Field


class ExerciseRelation(SQLModel, table=True):
    __tablename__ = "esercizi_relazioni"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Intra-catalog refs (tutte le tabelle in catalog.db, no FK per evitare
    # conflitti con Alembic che gestisce solo crm.db)
    exercise_id: int = Field(index=True)
    related_exercise_id: int = Field(index=True)
    tipo_relazione: str  # "progression" | "regression" | "variation"
