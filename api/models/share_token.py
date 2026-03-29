# api/models/share_token.py
"""
Modello ShareToken — link per portale clienti self-service.

Un trainer genera un token UUID4 per permettere al proprio cliente
di accedere a funzionalita' senza autenticazione. Il token e':
- monouso (scope=anamnesi: used_at traccia il consumo)
- multi-uso (scope=workout: used_at NON viene settato, il cliente torna ogni giorno)
- temporaneo (expires_at varia per scope: 48h anamnesi, data_fine+7gg workout)
- revocabile (il trainer puo' eliminarlo)
- scope-based (estendibile: "anamnesi", "workout", in futuro "misurazioni", ecc.)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ShareToken(SQLModel, table=True):
    """ORM model per la tabella 'share_tokens'."""

    __tablename__ = "share_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)               # UUID4 opaco
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    client_id: int = Field(foreign_key="clienti.id", index=True)
    scope: str = Field(default="anamnesi")                    # anamnesi | workout
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime                                       # 48h (anamnesi) o data_fine+7gg (workout)
    used_at: Optional[datetime] = None                        # None = non usato (solo scope=anamnesi)

    # Collegamento a scheda allenamento (solo scope=workout)
    id_scheda: Optional[int] = Field(
        default=None, foreign_key="schede_allenamento.id"
    )
