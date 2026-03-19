# api/routers/exercises.py
"""
Catalogo esercizi — read-only da catalog.db + tassonomia scientifica.

v3: esercizi builtin migrati in catalog.db (read-only, shipped con installer).
    Pattern identico a nutrition.db: catalogo separato da crm.db.
    Esercizi custom del trainer in crm.db = feature futura.

Tutte le query esercizi usano catalog_session (catalog.db).
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select, func, or_

from api.dependencies import get_current_trainer
from api.database import get_catalog_session, get_session
from api.models.exercise import Exercise
from api.models.exercise_media import ExerciseMedia
from api.models.exercise_relation import ExerciseRelation
from api.models.trainer import Trainer
from api.models.muscle import Muscle, ExerciseMuscle
from api.models.joint import Joint, ExerciseJoint
from api.models.medical_condition import MedicalCondition, ExerciseCondition
from api.schemas.exercise import (
    ExerciseCreate,
    ExerciseListResponse,
    ExerciseMediaResponse,
    ExerciseRelationCreate,
    ExerciseRelationResponse,
    ExerciseResponse,
    ExerciseUpdate,
    TaxonomyConditionResponse,
    TaxonomyJointResponse,
    TaxonomyMuscleResponse,
)

logger = logging.getLogger("fitmanager.api")

router = APIRouter(prefix="/exercises", tags=["exercises"])


# NOTE: media upload disabilitato (catalog.db e' read-only).
# Media builtin gestiti via seed_exercise_media.json.


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _bouncer_exercise(catalog_session: Session, exercise_id: int) -> Exercise:
    """Trova esercizio builtin in catalog.db. 404 se non trovato."""
    exercise = catalog_session.exec(
        select(Exercise).where(
            Exercise.id == exercise_id,
            Exercise.deleted_at == None,  # noqa: E711
        )
    ).first()
    if not exercise:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esercizio non trovato")
    return exercise


def _guard_custom(exercise: Exercise) -> None:
    """Blocca modifica/eliminazione su builtin."""
    if exercise.is_builtin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Esercizio builtin non modificabile")


def _to_response(
    exercise: Exercise,
    media: list | None = None,
    relazioni: list | None = None,
    muscoli_dettaglio: list | None = None,
    articolazioni: list | None = None,
    condizioni: list | None = None,
    thumbnail_url: str | None = None,
) -> ExerciseResponse:
    resp = ExerciseResponse.model_validate(exercise)
    if thumbnail_url is not None:
        resp.thumbnail_url = thumbnail_url
    if media is not None:
        resp.media = [ExerciseMediaResponse.model_validate(m) for m in media]
    if relazioni is not None:
        resp.relazioni = relazioni
    if muscoli_dettaglio is not None:
        resp.muscoli_dettaglio = muscoli_dettaglio
    if articolazioni is not None:
        resp.articolazioni = articolazioni
    if condizioni is not None:
        resp.condizioni = condizioni
    return resp


def _get_media(catalog_session: Session, exercise_id: int) -> list[ExerciseMedia]:
    return list(catalog_session.exec(
        select(ExerciseMedia)
        .where(ExerciseMedia.exercise_id == exercise_id)
        .order_by(ExerciseMedia.ordine, ExerciseMedia.id)
    ).all())


def _get_taxonomy_muscles(catalog_session: Session, exercise_id: int) -> list[TaxonomyMuscleResponse]:
    rows = catalog_session.exec(
        select(ExerciseMuscle, Muscle)
        .join(Muscle, ExerciseMuscle.id_muscolo == Muscle.id)
        .where(ExerciseMuscle.id_esercizio == exercise_id)
    ).all()
    return [
        TaxonomyMuscleResponse(
            id=m.id, nome=m.nome, nome_en=m.nome_en, gruppo=m.gruppo,
            ruolo=em.ruolo, attivazione=em.attivazione,
        )
        for em, m in rows
    ]


def _get_taxonomy_joints(catalog_session: Session, exercise_id: int) -> list[TaxonomyJointResponse]:
    rows = catalog_session.exec(
        select(ExerciseJoint, Joint)
        .join(Joint, ExerciseJoint.id_articolazione == Joint.id)
        .where(ExerciseJoint.id_esercizio == exercise_id)
    ).all()
    return [
        TaxonomyJointResponse(
            id=j.id, nome=j.nome, nome_en=j.nome_en, tipo=j.tipo,
            ruolo=ej.ruolo, rom_gradi=ej.rom_gradi,
        )
        for ej, j in rows
    ]


def _get_taxonomy_conditions(catalog_session: Session, exercise_id: int) -> list[TaxonomyConditionResponse]:
    rows = catalog_session.exec(
        select(ExerciseCondition, MedicalCondition)
        .join(MedicalCondition, ExerciseCondition.id_condizione == MedicalCondition.id)
        .where(ExerciseCondition.id_esercizio == exercise_id)
    ).all()
    return [
        TaxonomyConditionResponse(
            id=mc.id, nome=mc.nome, nome_en=mc.nome_en, categoria=mc.categoria,
            severita=ec.severita, nota=ec.nota,
        )
        for ec, mc in rows
    ]


def _get_relazioni(catalog_session: Session, exercise_id: int) -> list[ExerciseRelationResponse]:
    rows = catalog_session.exec(
        select(ExerciseRelation, Exercise)
        .join(Exercise, ExerciseRelation.related_exercise_id == Exercise.id)
        .where(
            ExerciseRelation.exercise_id == exercise_id,
            Exercise.deleted_at == None,  # noqa: E711
        )
    ).all()
    return [
        ExerciseRelationResponse(
            id=rel.id,
            related_exercise_id=rel.related_exercise_id,
            related_exercise_nome=ex.nome,
            tipo_relazione=rel.tipo_relazione,
        )
        for rel, ex in rows
    ]


# JSON serialization helpers per campi v2
JSON_LIST_FIELDS = {
    "muscoli_primari", "muscoli_secondari", "controindicazioni",
    "coaching_cues", "errori_comuni",
}
def _serialize_field(field: str, value):
    """Serializza campi JSON list/dict per storage TEXT."""
    if field in JSON_LIST_FIELDS:
        return json.dumps(value or [], ensure_ascii=False)
    return value


# ═══════════════════════════════════════════════════════════════
# VALIDAZIONE POST-MODIFICA (informativa, mai bloccante)
# ═══════════════════════════════════════════════════════════════

# Mapping pattern -> force_type atteso
_PATTERN_FORCE = {
    "push_h": "push", "push_v": "push", "pull_h": "pull", "pull_v": "pull",
    "squat": "push", "hinge": "pull", "core": "static", "rotation": "pull",
    "carry": "static", "warmup": "static", "stretch": "static", "mobility": "static",
}
# Muscoli tipicamente "pull"
_PULL_MUSCLES = {"back", "lats", "biceps"}
# Muscoli tipicamente "push"
_PUSH_MUSCLES = {"chest", "triceps"}


def _validate_exercise(exercise: Exercise) -> list[str]:
    """Genera suggerimenti di coerenza post-modifica. Informativi, mai bloccanti."""
    hints: list[str] = []
    pat = exercise.pattern_movimento or ""

    # 1. Pattern vs force_type
    expected_ft = _PATTERN_FORCE.get(pat)
    if expected_ft and exercise.force_type and exercise.force_type != expected_ft:
        hints.append(
            f"force_type '{exercise.force_type}' diverso da atteso '{expected_ft}' "
            f"per pattern '{pat}'. Potrebbe essere corretto (es. Croci = push_h/pull)."
        )

    # 2. Pattern vs muscoli primari
    try:
        muscles = set(json.loads(exercise.muscoli_primari)) if exercise.muscoli_primari else set()
    except (json.JSONDecodeError, TypeError):
        muscles = set()

    if pat in ("push_h", "push_v") and muscles & _PULL_MUSCLES:
        overlap = muscles & _PULL_MUSCLES
        hints.append(
            f"Pattern push con muscoli primari pull ({', '.join(overlap)}). "
            f"Verificare classificazione."
        )
    if pat in ("pull_h", "pull_v") and muscles & _PUSH_MUSCLES:
        overlap = muscles & _PUSH_MUSCLES
        hints.append(
            f"Pattern pull con muscoli primari push ({', '.join(overlap)}). "
            f"Verificare classificazione."
        )

    # 3. Campi critici mancanti (per subset)
    if exercise.in_subset:
        missing = []
        for field in ("esecuzione", "note_sicurezza", "controindicazioni",
                       "force_type", "piano_movimento", "catena_cinetica"):
            val = getattr(exercise, field, None)
            if not val or val in ("", "[]"):
                missing.append(field)
        if missing:
            hints.append(
                f"Campi obbligatori mancanti per il subset: {', '.join(missing)}."
            )

    return hints


# ═══════════════════════════════════════════════════════════════
# ARCHIVE STATS
# ═══════════════════════════════════════════════════════════════

@router.get("/archive-stats")
def get_archive_stats(
    trainer: Trainer = Depends(get_current_trainer),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Statistiche esercizi archiviati (in_subset=False). Solo informativo."""
    rows = catalog_session.exec(
        select(Exercise.categoria, func.count(Exercise.id))
        .where(
            Exercise.in_subset == False,  # noqa: E712
            Exercise.deleted_at == None,  # noqa: E711
        )
        .group_by(Exercise.categoria)
    ).all()
    by_categoria = {cat: count for cat, count in rows}
    active_count = catalog_session.exec(
        select(func.count(Exercise.id)).where(
            Exercise.in_subset == True,  # noqa: E712
            Exercise.deleted_at == None,  # noqa: E711
        )
    ).one()
    return {
        "archived_count": sum(by_categoria.values()),
        "active_count": active_count,
        "by_categoria": by_categoria,
    }


# ═══════════════════════════════════════════════════════════════
# SAFETY MAP (anamnesi × condizioni mediche)
# ═══════════════════════════════════════════════════════════════

@router.get("/safety-map")
def get_safety_map(
    client_id: int = Query(..., description="ID cliente per cui calcolare la safety map"),
    trainer: Trainer = Depends(get_current_trainer),
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Mappa sicurezza esercizi per un cliente specifico.

    Incrocia anamnesi cliente con esercizi_condizioni.
    Informativo, mai bloccante — il trainer decide SEMPRE.
    """
    from api.services.safety_engine import build_safety_map

    return build_safety_map(session, catalog_session, client_id, trainer.id)


# ═══════════════════════════════════════════════════════════════
# LIST
# ═══════════════════════════════════════════════════════════════

@router.get("", response_model=ExerciseListResponse)
def list_exercises(
    trainer: Trainer = Depends(get_current_trainer),
    catalog_session: Session = Depends(get_catalog_session),
    search: Optional[str] = Query(None, description="Ricerca per nome"),
    categoria: Optional[str] = Query(None),
    attrezzatura: Optional[str] = Query(None),
    difficolta: Optional[str] = Query(None),
    pattern_movimento: Optional[str] = Query(None),
    muscolo: Optional[str] = Query(None, description="Filtra per muscolo primario"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=1200, ge=1, le=2000),
):
    """Lista esercizi dal catalogo scientifico (catalog.db).
    Database attivo: solo esercizi con in_subset=True sono visibili.
    """
    query = select(Exercise).where(
        Exercise.deleted_at == None,  # noqa: E711
        Exercise.in_subset == True,  # noqa: E712
    )

    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(Exercise.nome.ilike(pattern), Exercise.nome_en.ilike(pattern))
        )
    if categoria:
        query = query.where(Exercise.categoria == categoria)
    if attrezzatura:
        query = query.where(Exercise.attrezzatura == attrezzatura)
    if difficolta:
        query = query.where(Exercise.difficolta == difficolta)
    if pattern_movimento:
        query = query.where(Exercise.pattern_movimento == pattern_movimento)
    if muscolo:
        query = query.where(Exercise.muscoli_primari.ilike(f'%"{muscolo}"%'))

    count_query = select(func.count()).select_from(query.subquery())
    total = catalog_session.exec(count_query).one()

    offset = (page - 1) * page_size
    exercises = catalog_session.exec(
        query.order_by(Exercise.nome).offset(offset).limit(page_size)
    ).all()

    # Batch fetch thumbnail: first "fdb:exec_start" image per exercise
    exercise_ids = [e.id for e in exercises if e.id is not None]
    thumbnail_map: dict[int, str] = {}
    if exercise_ids:
        all_media = catalog_session.exec(
            select(ExerciseMedia)
            .where(
                ExerciseMedia.exercise_id.in_(exercise_ids),
                ExerciseMedia.tipo == "image",
            )
            .order_by(ExerciseMedia.exercise_id, ExerciseMedia.ordine)
        ).all()
        for m in all_media:
            eid = m.exercise_id
            if eid in thumbnail_map:
                if m.descrizione and "exec_start" in m.descrizione:
                    thumbnail_map[eid] = m.url
            else:
                thumbnail_map[eid] = m.url

    return ExerciseListResponse(
        items=[
            _to_response(e, thumbnail_url=thumbnail_map.get(e.id))
            for e in exercises
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# ═══════════════════════════════════════════════════════════════
# GET SINGLE (enriched: media + relazioni)
# ═══════════════════════════════════════════════════════════════

@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Singolo esercizio per ID — enriched con media, relazioni e tassonomia.
    Tutto da catalog.db (esercizi + tassonomia nella stessa sessione).
    """
    exercise = _bouncer_exercise(catalog_session, exercise_id)
    media = _get_media(catalog_session, exercise_id)
    relazioni = _get_relazioni(catalog_session, exercise_id)
    muscoli = _get_taxonomy_muscles(catalog_session, exercise_id)
    joints = _get_taxonomy_joints(catalog_session, exercise_id)
    conditions = _get_taxonomy_conditions(catalog_session, exercise_id)
    return _to_response(exercise, media=media, relazioni=relazioni,
                        muscoli_dettaglio=muscoli, articolazioni=joints,
                        condizioni=conditions)


# ═══════════════════════════════════════════════════════════════
# CREATE
# ═══════════════════════════════════════════════════════════════

@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_exercise(
    data: ExerciseCreate,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Esercizi custom — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Creazione esercizi custom non ancora disponibile. "
        "Il catalogo scientifico contiene 500 esercizi builtin.",
    )


# ═══════════════════════════════════════════════════════════════
# UPDATE
# ═══════════════════════════════════════════════════════════════

@router.put("/{exercise_id}", response_model=ExerciseResponse)
def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Modifica esercizi custom — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Modifica esercizi non ancora disponibile. Il catalogo scientifico e' read-only.",
    )


# ═══════════════════════════════════════════════════════════════
# DELETE
# ═══════════════════════════════════════════════════════════════

@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Eliminazione esercizi custom — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Eliminazione esercizi non ancora disponibile. Il catalogo scientifico e' read-only.",
    )


# ═══════════════════════════════════════════════════════════════
# MEDIA UPLOAD
# ═══════════════════════════════════════════════════════════════

@router.post("/{exercise_id}/media", response_model=ExerciseMediaResponse, status_code=status.HTTP_201_CREATED)
def upload_exercise_media(
    exercise_id: int,
    file: UploadFile,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Upload media — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Upload media non disponibile. Il catalogo scientifico e' read-only.",
    )


@router.delete("/{exercise_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_media(
    exercise_id: int,
    media_id: int,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Elimina media — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Eliminazione media non disponibile. Il catalogo scientifico e' read-only.",
    )


# ═══════════════════════════════════════════════════════════════
# RELAZIONI (progressioni/regressioni)
# ═══════════════════════════════════════════════════════════════

@router.get("/{exercise_id}/relations", response_model=list[ExerciseRelationResponse])
def get_exercise_relations(
    exercise_id: int,
    trainer: Trainer = Depends(get_current_trainer),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Relazioni di un esercizio (progressioni/regressioni/varianti). Endpoint leggero."""
    _bouncer_exercise(catalog_session, exercise_id)
    return _get_relazioni(catalog_session, exercise_id)


@router.post("/{exercise_id}/relations", response_model=ExerciseRelationResponse, status_code=status.HTTP_201_CREATED)
def create_exercise_relation(
    exercise_id: int,
    data: ExerciseRelationCreate,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Creazione relazioni — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Creazione relazioni non disponibile. Il catalogo scientifico e' read-only.",
    )


@router.delete("/{exercise_id}/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_relation(
    exercise_id: int,
    relation_id: int,
    trainer: Trainer = Depends(get_current_trainer),
):
    """Eliminazione relazioni — feature futura. Catalogo builtin e' read-only."""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Eliminazione relazioni non disponibile. Il catalogo scientifico e' read-only.",
    )
