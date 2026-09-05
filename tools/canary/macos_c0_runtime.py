"""Source-free C0 runtime for macOS portability evidence.

This executable intentionally exposes only /health and the three auth routes
already exempt from production license enforcement. It is not the production
backend and contains no CRM-protected route or license bypass.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import secrets
import tempfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen


_RUNTIME_TEMP = tempfile.TemporaryDirectory(prefix="fitmanager-c0-", ignore_cleanup_errors=True)
_RUNTIME_ROOT = Path(_RUNTIME_TEMP.name)

# Force an isolated, synthetic runtime before importing api.config/database.
os.environ["DATABASE_URL"] = f"sqlite:///{_RUNTIME_ROOT / 'auth.db'}"
os.environ["CATALOG_DATABASE_URL"] = f"sqlite:///{_RUNTIME_ROOT / 'catalog.db'}"
os.environ["NUTRITION_DATABASE_URL"] = f"sqlite:///{_RUNTIME_ROOT / 'nutrition.db'}"
os.environ["JWT_SECRET"] = secrets.token_hex(32)
os.environ["LICENSE_ENFORCEMENT_ENABLED"] = "true"

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from sqlmodel import SQLModel, Session, create_engine  # noqa: E402

from api import __version__  # noqa: E402
from api.auth.router import router as auth_router  # noqa: E402
from api.database import get_optional_business_session, get_session  # noqa: E402
from api.models.trainer import Trainer  # noqa: E402


_ALLOWED_PATHS = frozenset(
    {
        "/health",
        "/api/auth/setup-status",
        "/api/auth/register",
        "/api/auth/login",
    }
)

engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
SQLModel.metadata.create_all(engine, tables=[Trainer.__table__])

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def _canary_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = _canary_session
app.dependency_overrides[get_optional_business_session] = _canary_session
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router, prefix="/api")


@app.middleware("http")
async def enforce_c0_boundary(request: Request, call_next):  # noqa: ANN001
    """Deny every route outside the already-exempt C0 contract."""
    if request.url.path not in _ALLOWED_PATHS:
        return JSONResponse(status_code=403, content={"detail": "C0 canary boundary"})
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")
    return {"status": "ok", "version": __version__, "database": "connected"}


def _apply_sqlcipher_key(connection, key: bytes) -> None:  # noqa: ANN001
    connection.execute(f"PRAGMA key = \"x'{key.hex()}'\"")


def run_sqlcipher_probe() -> dict[str, bool]:
    """Exercise encrypted create/reopen/wrong-key/plaintext invariants."""
    from sqlcipher3 import dbapi2 as sqlcipher

    db_path = _RUNTIME_ROOT / "sqlcipher-probe.db"
    key = secrets.token_bytes(32)
    wrong_key = secrets.token_bytes(32)
    sentinel = f"c0-sentinel-{secrets.token_hex(16)}"

    connection = sqlcipher.connect(str(db_path))
    try:
        _apply_sqlcipher_key(connection, key)
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("CREATE TABLE probe (value TEXT NOT NULL)")
        connection.execute("INSERT INTO probe(value) VALUES (?)", (sentinel,))
        connection.commit()
    finally:
        connection.close()

    encrypted_bytes = db_path.read_bytes()
    plaintext_absent = (
        not encrypted_bytes.startswith(b"SQLite format 3")
        and sentinel.encode("utf-8") not in encrypted_bytes
    )

    wrong_key_rejected = False
    connection = sqlcipher.connect(str(db_path))
    try:
        _apply_sqlcipher_key(connection, wrong_key)
        connection.execute("SELECT value FROM probe").fetchone()
    except sqlcipher.DatabaseError:
        wrong_key_rejected = True
    finally:
        connection.close()

    connection = sqlcipher.connect(str(db_path))
    try:
        _apply_sqlcipher_key(connection, key)
        row = connection.execute("SELECT value FROM probe").fetchone()
        roundtrip = row is not None and row[0] == sentinel
    finally:
        connection.close()

    db_path.unlink(missing_ok=True)
    return {
        "sqlcipher_plaintext_absent": plaintext_absent,
        "sqlcipher_roundtrip": roundtrip,
        "sqlcipher_wrong_key_rejected": wrong_key_rejected,
    }


def run_fingerprint_probe() -> dict[str, bool]:
    """Read twice and expose booleans only, never identifiers or hashes."""
    from api.services import machine_fingerprint

    first = machine_fingerprint._compute_fingerprint()
    second = machine_fingerprint._compute_fingerprint()
    available = (
        first != machine_fingerprint.UNAVAILABLE
        and second != machine_fingerprint.UNAVAILABLE
    )
    return {
        "fingerprint_available": available,
        "fingerprint_stable": available and first == second,
    }


def run_self_test() -> dict[str, object]:
    checks = {**run_sqlcipher_probe(), **run_fingerprint_probe()}
    return {
        "schema": 1,
        "architecture": platform.machine().lower(),
        "os": platform.system(),
        "os_version": platform.mac_ver()[0] if platform.system() == "Darwin" else platform.release(),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _request_json(method: str, url: str, payload: dict[str, str] | None = None) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = UrlRequest(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - fixed loopback URL in workflow
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def run_auth_smoke(base_url: str) -> dict[str, object]:
    """Validate the exempt auth surface without printing tokens or identities."""
    base_url = base_url.rstrip("/")
    email = f"c0-{secrets.token_hex(8)}@example.invalid"
    password = "C0-only-password-2026"

    health_status, health_body = _request_json("GET", f"{base_url}/health")
    setup_status, setup_body = _request_json("GET", f"{base_url}/api/auth/setup-status")
    register_status, register_body = _request_json(
        "POST",
        f"{base_url}/api/auth/register",
        {"email": email, "nome": "Canary", "cognome": "Synthetic", "password": password},
    )
    login_status, login_body = _request_json(
        "POST",
        f"{base_url}/api/auth/login",
        {"email": email, "password": password},
    )

    checks = {
        "health_redacted": health_status == 200
        and health_body == {"status": "ok", "version": __version__, "database": "connected"},
        "setup_status": setup_status == 200 and setup_body == {"needs_setup": True},
        "register": register_status == 201 and bool(register_body.get("access_token")),
        "login": login_status == 200 and bool(login_body.get("access_token")),
    }
    return {"schema": 1, "checks": checks, "ok": all(checks.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--serve", action="store_true")
    modes.add_argument("--smoke-auth", action="store_true")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    if args.self_test:
        report = run_self_test()
        print(json.dumps(report, sort_keys=True))
        return 0 if report["ok"] else 1
    if args.smoke_auth:
        try:
            report = run_auth_smoke(args.base_url)
        except Exception as exc:  # noqa: BLE001 - sanitized evidence, no response content
            report = {"schema": 1, "ok": False, "error_code": type(exc).__name__}
        print(json.dumps(report, sort_keys=True))
        return 0 if report["ok"] else 1

    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning", access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
