"""S1.2 — integrazione fail-closed e guard dell'accessor CRM."""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, text

import api.database as database
from api.auth.service import create_access_token
from api.database import get_session
from api.services.business_database import (
    BUSINESS_DATABASE_UNAVAILABLE_DETAIL,
    BusinessDatabaseController,
    BusinessDatabaseState,
    BusinessDatabaseStorageMode,
    BusinessDatabaseUnavailableError,
)


def _engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_compiled_mode_cannot_initialize_plaintext_business_engine(monkeypatch):
    locked = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    plaintext_opener = MagicMock()
    monkeypatch.setattr(database, "business_db_controller", locked)
    monkeypatch.setattr(database, "is_compiled", lambda: True)
    monkeypatch.setattr(database, "_create_plaintext_business_engine", plaintext_opener)

    with pytest.raises(BusinessDatabaseUnavailableError) as error:
        database.initialize_development_business_database()

    assert str(error.value) == BUSINESS_DATABASE_UNAVAILABLE_DETAIL
    assert locked.state is BusinessDatabaseState.LOCKED
    plaintext_opener.assert_not_called()
    with pytest.raises(BusinessDatabaseUnavailableError):
        locked.initialize_plaintext_development_engine(plaintext_opener)
    plaintext_opener.assert_not_called()


def test_compiled_mode_keeps_legacy_plaintext_backup_router_disabled(monkeypatch):
    from api.routers import backup

    monkeypatch.setattr(backup, "is_compiled", lambda: True)

    with pytest.raises(HTTPException) as error:
        backup._require_safe_backup_runtime()

    assert error.value.status_code == 503
    assert error.value.detail == BUSINESS_DATABASE_UNAVAILABLE_DETAIL


def test_encrypted_test_seam_keeps_legacy_plaintext_backup_disabled(monkeypatch):
    from api.routers import backup

    encrypted = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    candidate = _engine()
    encrypted.unlock_candidate(
        open_candidate=lambda: candidate,
        verify_candidate=lambda _engine: "owner",
        prepare_candidate=lambda _engine: None,
    )
    monkeypatch.setattr(database, "business_db_controller", encrypted)
    monkeypatch.setattr(backup, "is_compiled", lambda: False)

    with pytest.raises(HTTPException) as error:
        backup._require_safe_backup_runtime()

    assert encrypted.storage_mode is BusinessDatabaseStorageMode.ENCRYPTED
    assert error.value.status_code == 503
    assert error.value.detail == BUSINESS_DATABASE_UNAVAILABLE_DETAIL


def test_plaintext_development_mode_preserves_legacy_backup_until_s1_5(monkeypatch):
    from api.routers import backup

    development = BusinessDatabaseController(
        BusinessDatabaseState.UNINITIALIZED,
        allow_plaintext_development=True,
    )
    development.initialize_plaintext_development_engine(_engine)
    monkeypatch.setattr(database, "business_db_controller", development)
    monkeypatch.setattr(backup, "is_compiled", lambda: False)

    backup._require_safe_backup_runtime()

    assert development.storage_mode is BusinessDatabaseStorageMode.PLAINTEXT_DEVELOPMENT


def test_fastapi_dependency_override_bypasses_locked_controller_for_tests(monkeypatch):
    locked = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    test_engine = _engine()
    monkeypatch.setattr(database, "business_db_controller", locked)
    test_app = FastAPI()

    @test_app.get("/probe")
    def probe(session: Session = Depends(get_session)):
        return {"value": session.exec(text("SELECT 1")).one()[0]}

    def override_session():
        with Session(test_engine) as session:
            yield session

    test_app.dependency_overrides[get_session] = override_session
    response = TestClient(test_app).get("/probe")

    assert response.status_code == 200
    assert response.json() == {"value": 1}


def test_real_surfaces_and_residual_jwt_fail_closed_while_health_stays_available(
    monkeypatch,
    test_engine,
):
    from api.database import get_catalog_session
    from api.main import app

    locked = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    monkeypatch.setattr(database, "business_db_controller", locked)
    monkeypatch.setenv("PUBLIC_PORTAL_ENABLED", "true")

    def override_catalog():
        with Session(test_engine) as session:
            yield session

    previous_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_catalog_session] = override_catalog
    jwt = create_access_token(999, "owner@example.com")
    headers = {"Authorization": f"Bearer {jwt}"}
    client = TestClient(app, raise_server_exceptions=False)
    try:
        for method, path, kwargs in [
            ("get", "/api/clients", {"headers": headers}),
            ("get", "/api/backup/list", {"headers": headers}),
            ("get", "/api/public/anamnesi/validate", {"params": {"token": "a" * 36}}),
        ]:
            response = getattr(client, method)(path, **kwargs)
            assert response.status_code == 503
            assert response.json() == {"detail": BUSINESS_DATABASE_UNAVAILABLE_DETAIL}

        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["db"] == "disconnected"
        setup = client.get("/api/auth/setup-status")
        assert setup.status_code == 200
        assert setup.json() == {"needs_setup": False}
    finally:
        app.dependency_overrides = previous_overrides
        client.close()


def test_no_module_imports_the_removed_business_engine_singleton():
    root = Path(__file__).resolve().parents[1]
    violations: list[str] = []
    for base in (root / "api", root / "tools"):
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "api.database":
                    if any(alias.name == "engine" for alias in node.names):
                        violations.append(str(path.relative_to(root)))

    assert violations == []
