# api/schemas/public.py
"""
Schema Pydantic per il Portale Clienti pubblico.

Endpoint pubblici (no JWT trainer):
  Anamnesi:
    GET  /api/public/anamnesi/validate?token=X  → AnamnesiValidateResponse
    POST /api/public/anamnesi/submit             → AnamnesiSubmitResponse
  Workout:
    GET  /api/public/workout/validate?token=X    → WorkoutValidateResponse
    GET  /api/public/workout/sessions?token=X    → WorkoutSessionsResponse
    GET  /api/public/workout/session/{id}/exercises?token=X → WorkoutExercisesResponse
    POST /api/public/workout/session/{id}/log    → WorkoutLogResponse

Endpoint protetti (JWT trainer):
  POST /api/clients/{id}/share-anamnesi          → ShareTokenResponse
  POST /api/clients/{id}/share-workout           → ShareTokenResponse
"""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════
# SHARED — Token generation response
# ════════════════════════════════════════════════════════════

class ShareTokenResponse(BaseModel):
    """Risposta alla generazione del link (anamnesi o workout)."""
    token: str
    url: str          # path relativo o assoluto (se PUBLIC_BASE_URL)
    expires_at: datetime
    client_name: str  # feedback visivo per il trainer


# ════════════════════════════════════════════════════════════
# ANAMNESI — Portale self-service
# ════════════════════════════════════════════════════════════

class AnamnesiValidateResponse(BaseModel):
    """Info per pre-popolare la pagina pubblica. Nome mascherato: 'Marco R.'"""
    client_name: str    # "Marco R." — cognome troncato per privacy
    trainer_name: str   # "Chiara B." — nome del professionista
    has_existing: bool  # se esiste gia' un'anamnesi (per messaggio contestuale)
    scope: str          # "anamnesi"


class AnamnesiSubmitRequest(BaseModel):
    """Payload invio anamnesi compilata dal cliente."""
    token: str
    anamnesi: dict[str, Any]  # AnamnesiData strutturata (validata lato frontend)


class AnamnesiSubmitResponse(BaseModel):
    """Conferma invio anamnesi."""
    success: bool
    message: str


# ════════════════════════════════════════════════════════════
# WORKOUT — Portale scheda interattiva cliente
# ════════════════════════════════════════════════════════════

class WorkoutValidateResponse(BaseModel):
    """Info iniziali per la pagina scheda pubblica."""
    client_name: str          # "Marco R."
    trainer_name: str         # "Chiara B."
    workout_name: str         # "Full Body 3x Settimana"
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    sessioni_per_settimana: int
    total_slots: int          # totale slot pianificati
    completed_slots: int      # slot completati
    scope: str                # "workout"


class WorkoutSlotItem(BaseModel):
    """Singolo slot nel calendario della scheda."""
    id: int
    data_pianificata: date
    stato: str                        # pianificato | completato | saltato | parziale
    sessione_nome: str                # "Sessione A — Full Body"
    focus_muscolare: Optional[str] = None
    has_log: bool                     # True se ha almeno 1 exercise_log


class WorkoutSessionsResponse(BaseModel):
    """Lista slot del calendario scheda."""
    slots: list[WorkoutSlotItem]


class ExerciseLogData(BaseModel):
    """Dati effettivi di un singolo esercizio (gia' salvato)."""
    serie_effettive: Optional[int] = None
    ripetizioni_effettive: Optional[str] = None
    carico_effettivo_kg: Optional[float] = None
    rpe: Optional[float] = None
    note_cliente: Optional[str] = None


class WorkoutExerciseItem(BaseModel):
    """Singolo esercizio nella sessione, con log opzionale."""
    id: int                           # esercizi_sessione.id
    nome_esercizio: str               # da catalog.db
    gruppo_muscolare: Optional[str] = None  # da catalog.db (muscoli_primari)
    categoria: Optional[str] = None   # da catalog.db (avviamento/stretching/etc → sezione)
    ordine: int
    serie: int
    ripetizioni: str                  # "8-12"
    carico_kg: Optional[float] = None
    tempo_riposo_sec: int
    tempo_esecuzione: Optional[str] = None  # "3-0-1-0"
    note_trainer: Optional[str] = None
    blocco_nome: Optional[str] = None  # null = straight set
    blocco_tipo: Optional[str] = None  # circuit/superset/tabata/amrap/emom
    foto_start: Optional[str] = None  # URL media
    foto_end: Optional[str] = None    # URL media
    # Info esercizio dal catalogo scientifico (killer feature per il cliente)
    setup: Optional[str] = None
    esecuzione: Optional[str] = None
    respirazione: Optional[str] = None
    coaching_cues: Optional[str] = None
    errori_comuni: Optional[str] = None
    log: Optional[ExerciseLogData] = None  # null = non ancora compilato


class WorkoutExercisesResponse(BaseModel):
    """Esercizi di una sessione con log opzionali."""
    slot_id: int
    data_pianificata: date
    stato: str
    sessione_nome: str
    exercises: list[WorkoutExerciseItem]


class ExerciseLogInput(BaseModel):
    """Input per un singolo esercizio dal client portal."""
    model_config = {"extra": "forbid"}

    id_esercizio_sessione: int
    serie_effettive: Optional[int] = None
    ripetizioni_effettive: Optional[str] = None
    carico_effettivo_kg: Optional[float] = None
    rpe: Optional[float] = Field(default=None, ge=0, le=10)
    note_cliente: Optional[str] = Field(default=None, max_length=500)


class SessionFeedback(BaseModel):
    """Feedback soggettivo sessione — 5 quick-tap dal cliente."""
    model_config = {"extra": "forbid"}

    durata_effettiva_min: Optional[int] = Field(default=None, ge=1, le=300)
    energia_pre: Optional[int] = Field(default=None, ge=1, le=5)
    energia_post: Optional[int] = Field(default=None, ge=1, le=5)
    soddisfazione: Optional[int] = Field(default=None, ge=1, le=5)
    difficolta_percepita: Optional[int] = Field(default=None, ge=1, le=5)


class WorkoutLogRequest(BaseModel):
    """Payload per salvare i dati di una sessione."""
    model_config = {"extra": "forbid"}

    token: str
    exercises: list[ExerciseLogInput]
    note_sessione: Optional[str] = Field(default=None, max_length=1000)
    feedback: Optional[SessionFeedback] = None


class WorkoutLogResponse(BaseModel):
    """Conferma salvataggio sessione."""
    success: bool
    message: str
    completion_pct: int  # percentuale completamento scheda
