# api/seed_metrics.py
"""
Seed 22 metriche standard in catalog.db.

Idempotente: INSERT OR IGNORE per ID (non sovrascrive metriche esistenti).
Chiamato al startup da main.py lifespan, stesso pattern di seed_exercises.py.
"""

import logging

from sqlmodel import Session, text

logger = logging.getLogger(__name__)

# (id, nome, nome_en, unita_misura, categoria, ordinamento)
METRICS_DATA = [
    (1, "Peso Corporeo", "Body Weight", "kg", "antropometrica", 1),
    (2, "Altezza", "Height", "cm", "antropometrica", 2),
    (3, "Massa Grassa", "Body Fat", "%", "composizione", 1),
    (4, "Massa Magra", "Lean Mass", "kg", "composizione", 2),
    (5, "BMI", "BMI", "kg/m²", "composizione", 3),
    (6, "Acqua Corporea", "Body Water", "%", "composizione", 4),
    (7, "Collo", "Neck", "cm", "circonferenza", 1),
    (8, "Petto", "Chest", "cm", "circonferenza", 2),
    (9, "Vita", "Waist", "cm", "circonferenza", 3),
    (10, "Fianchi", "Hips", "cm", "circonferenza", 4),
    (11, "Braccio Destro", "Right Arm", "cm", "circonferenza", 5),
    (12, "Braccio Sinistro", "Left Arm", "cm", "circonferenza", 6),
    (13, "Coscia Destra", "Right Thigh", "cm", "circonferenza", 7),
    (14, "Coscia Sinistra", "Left Thigh", "cm", "circonferenza", 8),
    (15, "Polpaccio Destro", "Right Calf", "cm", "circonferenza", 9),
    (16, "Polpaccio Sinistro", "Left Calf", "cm", "circonferenza", 10),
    (17, "FC Riposo", "Resting HR", "bpm", "cardiovascolare", 1),
    (18, "PA Sistolica", "Systolic BP", "mmHg", "cardiovascolare", 2),
    (19, "PA Diastolica", "Diastolic BP", "mmHg", "cardiovascolare", 3),
    (20, "Squat 1RM", "Squat 1RM", "kg", "forza", 1),
    (21, "Panca Piana 1RM", "Bench Press 1RM", "kg", "forza", 2),
    (22, "Stacco da Terra 1RM", "Deadlift 1RM", "kg", "forza", 3),
]


def seed_metrics(session: Session) -> None:
    """Seed 22 metriche standard in catalog.db. Idempotente."""
    existing = session.exec(text("SELECT COUNT(*) FROM metriche")).one()[0]
    if existing >= len(METRICS_DATA):
        logger.info("Seed metriche: %d gia' presenti, skip", existing)
        return

    for mid, nome, nome_en, unita, categoria, ordine in METRICS_DATA:
        session.exec(
            text(
                "INSERT OR IGNORE INTO metriche "
                "(id, nome, nome_en, unita_misura, categoria, ordinamento) "
                "VALUES (:id, :nome, :nome_en, :unita, :cat, :ord)"
            ),
            params={
                "id": mid,
                "nome": nome,
                "nome_en": nome_en,
                "unita": unita,
                "cat": categoria,
                "ord": ordine,
            },
        )
    session.commit()
    logger.info("Seed metriche: %d metriche inserite in catalog.db", len(METRICS_DATA))
