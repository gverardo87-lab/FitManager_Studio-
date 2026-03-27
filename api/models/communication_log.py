# api/models/communication_log.py
"""
Modello CommunicationLog — registra ogni comunicazione col cliente.

Ogni riga rappresenta un messaggio WhatsApp, chiamata, email o nota interna.
Log trasparente: il frontend registra al click del bottone WhatsApp.

Multi-tenancy: trainer_id diretto (chi ha inviato).
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class CommunicationLog(SQLModel, table=True):
    """
    ORM model per la tabella 'communication_log'.

    canale: 'whatsapp', 'telefono', 'email', 'nota'
    template_usato: chiave del template (es. 'birthday', 'checkin', 'free')
    anteprima: primi 200 char del messaggio (per timeline)
    """
    __tablename__ = "communication_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    trainer_id: int = Field(foreign_key="trainers.id", index=True)
    id_cliente: int = Field(foreign_key="clienti.id", index=True)
    canale: str  # 'whatsapp', 'telefono', 'email', 'nota'
    template_usato: Optional[str] = None  # key del template usato
    anteprima: str = ""  # primi 200 char del messaggio
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    deleted_at: Optional[datetime] = None
