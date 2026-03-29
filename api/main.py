# api/main.py
"""
FastAPI application — entry point dell'API REST.

Avvia con: uvicorn api.main:app --reload --port 8000
Poi apri: http://localhost:8000/docs (Swagger UI interattiva)

Cosa succede al startup:
1. Crea tabelle SQLModel (trainers, audit_log) — CREATE IF NOT EXISTS
2. Registra tutti i router (auth, clients, agenda, contracts, rates, movements, dashboard, backup)

Migrazioni schema gestite da Alembic: `alembic upgrade head`
"""

import logging
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from sqlmodel import Session

from api import __version__
from api.schemas.system import HealthResponse
from api.database import get_catalog_session, get_session

from api.config import (
    API_PREFIX,
    APP_LOG_BACKUP_COUNT,
    APP_LOG_LEVEL,
    APP_LOG_MAX_BYTES,
    CATALOG_DATABASE_URL,
    DATA_DIR,
    DATABASE_URL,
    NUTRITION_DATABASE_URL,
)
from api.database import create_catalog_tables, create_db_and_tables, create_nutrition_tables, engine, catalog_engine
from api.logging_config import configure_app_logging
from api.seed_exercises import seed_builtin_exercises, seed_exercise_media, seed_exercise_relations
from api.services.license import check_license
from api.auth.router import router as auth_router
from api.routers.clients import router as clients_router
from api.routers.agenda import router as agenda_router
from api.routers.contracts import router as contracts_router
from api.routers.rates import router as rates_router
from api.routers.movements import router as movements_router
from api.routers.recurring_expenses import router as recurring_expenses_router
from api.routers.dashboard import router as dashboard_router
from api.routers.backup import router as backup_router
from api.routers.todos import router as todos_router
from api.routers.exercises import router as exercises_router
from api.routers.workouts import router as workouts_router
from api.routers.measurements import router as measurements_router
from api.routers.goals import router as goals_router
from api.routers.workout_logs import router as workout_logs_router
from api.routers.assistant import router as assistant_router
from api.routers.public_portal import router as public_portal_router
from api.routers.system import router as system_router
from api.routers.training_science import router as training_science_router
from api.routers.training_methodology import router as training_methodology_router
from api.routers.workspace import router as workspace_router
from api.routers.nutrition import router as nutrition_router
from api.routers.client_avatar import router as client_avatar_router
from api.routers.workout_schedule import router as workout_schedule_router
from api.routers.workout_analytics import router as workout_analytics_router
from api.routers.communications import router as communications_router
from api.services.system_runtime import (
    BACKUP_DIR,
    build_health_response,
    is_license_enforcement_enabled,
)

APP_LOG_PATH = configure_app_logging(
    DATA_DIR,
    level_name=APP_LOG_LEVEL,
    max_bytes=APP_LOG_MAX_BYTES,
    backup_count=APP_LOG_BACKUP_COUNT,
)
logger = logging.getLogger("fitmanager.api")

MAX_AUTO_BACKUPS = 5  # solo gli ultimi 5 backup automatici

LICENSE_EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    f"{API_PREFIX}/auth/login",
    f"{API_PREFIX}/auth/register",
    f"{API_PREFIX}/auth/setup-status",
    f"{API_PREFIX}/auth/reset-password",
}
LICENSE_EXEMPT_PREFIXES = ("/media/", "/videos/", f"{API_PREFIX}/public/")


def _auto_backup_on_startup(database_url: str) -> None:
    """
    Backup automatico del DB business al startup (solo prod).

    Usa sqlite3.backup() per copia atomica. Mantiene max 5 backup auto.
    Non blocca se fallisce (best-effort, log error).
    """
    db_path = database_url.replace("sqlite:///", "")
    if not Path(db_path).exists():
        return

    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = BACKUP_DIR / f"auto_{timestamp}.sqlite"

        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(str(dest))
        try:
            source.backup(backup)
        finally:
            backup.close()
            source.close()

        size = dest.stat().st_size
        logger.info(f"Auto-backup: {dest.name} ({size:,} bytes)")

        # Retention: solo ultimi MAX_AUTO_BACKUPS
        auto_files = sorted(
            BACKUP_DIR.glob("auto_*.sqlite"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in auto_files[MAX_AUTO_BACKUPS:]:
            old.unlink(missing_ok=True)
            old.with_suffix(".sha256").unlink(missing_ok=True)
    except Exception as e:
        logger.error(f"Auto-backup fallito (non bloccante): {e}")


def _integrity_check_on_startup(business_url: str, catalog_url: str) -> None:
    """
    PRAGMA integrity_check su entrambi i DB al startup.

    Se fallisce, log CRITICAL ma NON blocca (l'app parte comunque).
    L'operatore deve intervenire con restore.
    """
    for label, url in [("business", business_url), ("catalog", catalog_url)]:
        if not url.startswith("sqlite"):
            continue
        db_path = url.replace("sqlite:///", "")
        if not Path(db_path).exists():
            continue
        try:
            conn = sqlite3.connect(db_path)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if result and result[0] == "ok":
                logger.info(f"  {label} DB integrity: OK")
            else:
                logger.critical(f"  {label} DB integrity: FALLITO — {result}")
        except Exception as e:
            logger.critical(f"  {label} DB integrity check error: {e}")


def _purge_stale_wal(db_path: str, label: str) -> None:
    """
    Elimina file WAL/SHM stale per cataloghi read-only (catalog.db, nutrition.db).

    Questi DB vengono shippati pre-costruiti dall'installer. Se una versione
    precedente li ha aperti in WAL mode, i file -wal/-shm persistono nella
    cartella data/ (protetta da uninsneveruninstall). L'installer sovrascrive
    il .db ma NON i file WAL/SHM — SQLite legge il WAL stale e i dati
    risultano corrotti o vuoti.

    Sicuro perche' cataloghi e nutrition sono read-only: qualsiasi WAL
    residuo e' spazzatura di una versione precedente.
    """
    for suffix in ("-wal", "-shm"):
        wal_file = Path(db_path + suffix)
        if wal_file.exists():
            try:
                wal_file.unlink()
                logger.info(f"  {label}: rimosso WAL stale {wal_file.name}")
            except OSError as e:
                logger.warning(f"  {label}: impossibile rimuovere {wal_file.name}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle dell'app.

    Startup sequence:
    1. Auto-backup (solo prod, non dev — protegge dati reali)
    2. Crea tabelle business (CREATE IF NOT EXISTS)
    3. Inizializza catalog DB
    4. Seed esercizi builtin
    5. Integrity check
    """
    db_label = "DEV (crm_dev.db)" if "crm_dev" in DATABASE_URL else "PROD (crm.db)"
    is_dev = "crm_dev" in DATABASE_URL
    logger.info(f"API startup: database {db_label}")
    logger.info(f"  LOG_FILE = {APP_LOG_PATH}")
    logger.info(
        "  LOG_POLICY = level=%s max_bytes=%s backup_count=%s",
        APP_LOG_LEVEL,
        APP_LOG_MAX_BYTES,
        APP_LOG_BACKUP_COUNT,
    )
    # Maschera credenziali per PostgreSQL (user:pass@host)
    safe_url = DATABASE_URL
    if "@" in DATABASE_URL:
        safe_url = DATABASE_URL.split("@", 1)[0].rsplit(":", 1)[0] + ":***@" + DATABASE_URL.split("@", 1)[1]
    logger.info(f"  DATABASE_URL = {safe_url}")

    # ── 1. Auto-backup (solo prod) ──
    if not is_dev and DATABASE_URL.startswith("sqlite"):
        _auto_backup_on_startup(DATABASE_URL)

    # ── 2. Business tables ──
    create_db_and_tables()

    # ── 2b. Schema sync: aggiunge colonne mancanti dopo upgrade/restore ──
    from api.services.schema_sync import sync_schema
    sync_schema(engine)

    # ── 3. Catalog DB ──
    catalog_path = CATALOG_DATABASE_URL.replace("sqlite:///", "")
    if not Path(catalog_path).exists():
        logger.warning("catalog.db non trovato — creo tabelle vuote. "
                       "Eseguire: python -m tools.admin_scripts.build_catalog")
    _purge_stale_wal(catalog_path, "catalog")
    create_catalog_tables()
    logger.info(f"  CATALOG_DB = {catalog_path}")

    # ── 3b. Nutrition DB ──
    nutrition_path = NUTRITION_DATABASE_URL.replace("sqlite:///", "")
    if not Path(nutrition_path).exists():
        logger.warning("nutrition.db non trovato — creo tabelle vuote. "
                       "Eseguire: python -m tools.admin_scripts.build_nutrition")
    _purge_stale_wal(nutrition_path, "nutrition")
    create_nutrition_tables()
    logger.info(f"  NUTRITION_DB = {nutrition_path}")

    # ── 4. Seed esercizi builtin + relazioni in CATALOG DB (idempotente) ──
    # Pattern identico a nutrition.db: catalogo scientifico separato da crm.db
    from sqlmodel import Session as SyncSession
    with SyncSession(catalog_engine) as catalog_seed_session:
        seed_builtin_exercises(catalog_seed_session)
        seed_exercise_relations(catalog_seed_session)
        seed_exercise_media(catalog_seed_session)

    # ── 4b. Nutrition template check (warning, non bloccante) ──
    if Path(nutrition_path).exists():
        try:
            conn = sqlite3.connect(nutrition_path)
            template_count = conn.execute(
                "SELECT COUNT(*) FROM plan_templates WHERE is_active = 1"
            ).fetchone()[0]
            conn.close()
            if template_count < 8:
                logger.warning(
                    f"nutrition.db ha solo {template_count} template attivi (attesi >= 8). "
                    "I piani alimentari LARN potrebbero non essere generabili."
                )
            else:
                logger.info(f"  NUTRITION_TEMPLATES = {template_count} attivi")
        except Exception as e:
            logger.warning(f"Impossibile verificare template nutrizione: {e}")

    # ── 5. Integrity check ──
    _integrity_check_on_startup(DATABASE_URL, CATALOG_DATABASE_URL)
    # Integrity check nutrition.db (separato, non blocca se mancante)
    if Path(nutrition_path).exists():
        _integrity_check_on_startup(NUTRITION_DATABASE_URL, NUTRITION_DATABASE_URL)

    logger.info("API pronta")
    yield
    logger.info("API shutdown")


# --- App FastAPI ---

app = FastAPI(
    title="FitManager Studio+ API",
    version=__version__,
    description="REST API per il CRM fitness. Multi-tenant, JWT auth, database-agnostic.",
    lifespan=lifespan,
)

def _is_license_exempt_path(path: str) -> bool:
    if path in LICENSE_EXEMPT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in LICENSE_EXEMPT_PREFIXES)


class LicenseMiddleware(BaseHTTPMiddleware):
    """Middleware licenza (gated): enforcement opzionale via env.

    Registrato con add_middleware PRIMA di CORSMiddleware, cosi' Starlette
    lo esegue DENTRO il layer CORS (CORS = outermost). Senza questo,
    le response 403 non avrebbero header CORS e il browser bloccherebbe
    il body — impedendo al frontend di leggere license_status e fare redirect.
    """

    async def dispatch(self, request: Request, call_next):
        if not is_license_enforcement_enabled():
            return await call_next(request)

        path = request.url.path
        if _is_license_exempt_path(path):
            return await call_next(request)

        result = check_license()
        request.state.license_status = result.status

        if result.is_valid:
            return await call_next(request)

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": result.message,
                "license_status": result.status,
            },
        )


# IMPORTANTE: ordine add_middleware conta. Starlette usa insert(0, ...) quindi
# l'ULTIMO add_middleware diventa il layer PIU' ESTERNO nella catena middleware.
# Registrare LicenseMiddleware PRIMA di CORSMiddleware garantisce che CORS
# avvolga License — cosi' le response 403 del license check hanno header CORS
# e il browser puo' leggere il body (license_status) per fare redirect a /licenza.
app.add_middleware(LicenseMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|100\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# Security headers middleware — previene MIME-sniffing e clickjacking
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# Static files: serve media (immagini/video esercizi)
# Usa DATA_DIR da config.py (gestisce PyInstaller frozen correttamente)
_media_dir = DATA_DIR / "media"
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")

# Static files: video (tutorial, demo)
_videos_dir = DATA_DIR / "videos"
_videos_dir.mkdir(parents=True, exist_ok=True)
app.mount("/videos", StaticFiles(directory=str(_videos_dir)), name="videos")

# Registra router
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(clients_router, prefix=API_PREFIX)
app.include_router(agenda_router, prefix=API_PREFIX)
app.include_router(contracts_router, prefix=API_PREFIX)
app.include_router(rates_router, prefix=API_PREFIX)
app.include_router(movements_router, prefix=API_PREFIX)
app.include_router(recurring_expenses_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(backup_router, prefix=API_PREFIX)
app.include_router(todos_router, prefix=API_PREFIX)
app.include_router(exercises_router, prefix=API_PREFIX)
app.include_router(workouts_router, prefix=API_PREFIX)
app.include_router(measurements_router, prefix=API_PREFIX)
app.include_router(goals_router, prefix=API_PREFIX)
app.include_router(workout_logs_router, prefix=API_PREFIX)
app.include_router(assistant_router, prefix=API_PREFIX)
app.include_router(public_portal_router, prefix=API_PREFIX)
app.include_router(system_router, prefix=API_PREFIX)
app.include_router(training_science_router, prefix=API_PREFIX)
app.include_router(training_methodology_router, prefix=API_PREFIX)
app.include_router(workspace_router, prefix=API_PREFIX)
app.include_router(nutrition_router, prefix=API_PREFIX)
app.include_router(client_avatar_router, prefix=API_PREFIX)
app.include_router(workout_schedule_router, prefix=API_PREFIX)
app.include_router(workout_analytics_router, prefix=API_PREFIX)
app.include_router(communications_router, prefix=API_PREFIX)


@app.get("/health", response_model=HealthResponse)
def health_check(
    response: Response,
    session: Session = Depends(get_session),
    catalog_session: Session = Depends(get_catalog_session),
):
    """Endpoint di salute — verifica DB + catalog + licenza + versione."""
    health = build_health_response(session, catalog_session)
    if health.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return health
