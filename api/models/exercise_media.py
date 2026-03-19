# api/models/exercise_media.py
"""
Modello ExerciseMedia — galleria media per esercizi in catalog.db.

Ogni esercizio puo' avere N immagini/video, ordinati per 'ordine'.
Catalogo scientifico read-only (shipped con installer, come nutrition.db).

v3: migrato da crm.db a catalog.db. Nessun trainer_id (catalogo globale).
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class ExerciseMedia(SQLModel, table=True):
    __tablename__ = "esercizi_media"

    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="esercizi.id", index=True)
    tipo: str                  # "image" | "video"
    url: str                   # path relativo: /media/exercises/42/img_001.jpg
    ordine: int = Field(default=0)
    descrizione: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
