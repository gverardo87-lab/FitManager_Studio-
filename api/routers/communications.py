# api/routers/communications.py
"""
CRUD comunicazioni — log trasparente delle comunicazioni col cliente.

Endpoint:
- POST /communications          → registra una comunicazione (WhatsApp, tel, email)
- GET  /communications/{client_id} → lista comunicazioni per un cliente
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select
from typing import Optional

from api.database import get_session
from api.dependencies import get_current_trainer
from api.models.trainer import Trainer
from api.models.client import Client
from api.models.communication_log import CommunicationLog

router = APIRouter(prefix="/communications", tags=["communications"])

VALID_CHANNELS = {"whatsapp", "telefono", "email", "nota"}


# ── Schema ──

class CommunicationCreate(BaseModel):
    """Schema per registrare una comunicazione."""
    model_config = {"extra": "forbid"}

    id_cliente: int
    canale: str  # 'whatsapp', 'telefono', 'email', 'nota'
    template_usato: Optional[str] = None
    anteprima: str = ""

    @field_validator("canale")
    @classmethod
    def validate_canale(cls, v: str) -> str:
        if v not in VALID_CHANNELS:
            raise ValueError(f"Canale deve essere uno di: {', '.join(VALID_CHANNELS)}")
        return v

    @field_validator("anteprima")
    @classmethod
    def truncate_anteprima(cls, v: str) -> str:
        return v[:200] if v else ""


class CommunicationResponse(BaseModel):
    """Risposta singola comunicazione."""
    model_config = {"from_attributes": True}

    id: int
    id_cliente: int
    canale: str
    template_usato: Optional[str] = None
    anteprima: str
    created_at: Optional[str] = None


# ── Endpoints ──

@router.post("", status_code=201)
def log_communication(
    payload: CommunicationCreate,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Registra una comunicazione col cliente (log trasparente)."""
    # Bouncer: verifica ownership cliente
    client = session.exec(
        select(Client).where(
            Client.id == payload.id_cliente,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    entry = CommunicationLog(
        trainer_id=trainer.id,
        id_cliente=payload.id_cliente,
        canale=payload.canale,
        template_usato=payload.template_usato,
        anteprima=payload.anteprima,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)

    return {
        "id": entry.id,
        "id_cliente": entry.id_cliente,
        "canale": entry.canale,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.get("/{client_id}")
def get_client_communications(
    client_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
):
    """Lista comunicazioni per un cliente (piu' recenti prima)."""
    # Bouncer: verifica ownership cliente
    client = session.exec(
        select(Client).where(
            Client.id == client_id,
            Client.trainer_id == trainer.id,
            Client.deleted_at == None,
        )
    ).first()
    if not client:
        raise HTTPException(404, "Cliente non trovato")

    logs = session.exec(
        select(CommunicationLog).where(
            CommunicationLog.id_cliente == client_id,
            CommunicationLog.trainer_id == trainer.id,
            CommunicationLog.deleted_at == None,
        ).order_by(CommunicationLog.created_at.desc())  # type: ignore[union-attr]
        .limit(50)
    ).all()

    return {
        "items": [
            {
                "id": log.id,
                "canale": log.canale,
                "template_usato": log.template_usato,
                "anteprima": log.anteprima,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
