# api/schemas/workout_schedule.py
"""
Pydantic schemas per workout schedule slots.

Input: ScheduleGenerateRequest (genera N slot da pattern), ScheduleSlotUpdate (modifica singolo).
Output: ScheduleSlotResponse con nomi enriched da JOINs.
Mass Assignment Prevention: trainer_id e id_cliente da JWT + plan ownership.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# INPUT
# ════════════════════════════════════════════════════════════

class ScheduleGenerateRequest(BaseModel):
    """Genera slot dal pattern settimanale. trainer_id + id_cliente da plan."""

    model_config = {"extra": "forbid"}

    # Giorni della settimana (0=Lunedi, 6=Domenica)
    pattern_giorni: List[int] = Field(min_length=1, max_length=7)
    data_inizio: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    settimane: int = Field(ge=1, le=52)


class ScheduleSlotUpdate(BaseModel):
    """Aggiorna singolo slot. Solo campi modificabili."""

    model_config = {"extra": "forbid"}

    data_pianificata: Optional[str] = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    stato: Optional[str] = Field(None, pattern=r"^(pianificato|completato|saltato|parziale)$")
    note: Optional[str] = Field(None, max_length=500)


class ScheduleBulkMoveRequest(BaseModel):
    """Sposta N slot di un offset in giorni."""

    model_config = {"extra": "forbid"}

    slot_ids: List[int] = Field(min_length=1, max_length=100)
    offset_giorni: int = Field(ge=-365, le=365)


# ════════════════════════════════════════════════════════════
# OUTPUT
# ════════════════════════════════════════════════════════════

class ScheduleSlotResponse(BaseModel):
    """Slot pianificato — output enriched con nomi sessione e scheda."""

    id: int
    id_scheda: int
    id_sessione: int
    id_cliente: int
    data_pianificata: str
    stato: str
    id_log: Optional[int] = None
    note: Optional[str] = None
    created_at: Optional[str] = None
    sessione_nome: str
    sessione_numero: int
    focus_muscolare: Optional[str] = None


class ScheduleListResponse(BaseModel):
    """Lista slot pianificati per una scheda."""

    items: List[ScheduleSlotResponse]
    total: int
