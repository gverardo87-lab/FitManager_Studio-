"""S1.2 — regressioni per engine CRM late-bound e boundary locked."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from unittest.mock import MagicMock

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from api.auth.candidate import (
    CandidateOwnerVerificationError,
    verify_candidate_owner,
)
from api.auth.service import hash_password
from api.models.trainer import Trainer
from api.services.business_database import (
    BUSINESS_DATABASE_UNAVAILABLE_DETAIL,
    BusinessDatabaseController,
    BusinessDatabaseState,
    BusinessDatabaseTransitionError,
    BusinessDatabaseUnavailableError,
    BusinessDatabaseUnlockError,
)


def _engine() -> Engine:
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _seed_owner(
    engine: Engine,
    *,
    email: str = "owner@example.com",
    password: str = "correct horse battery staple",
    active: bool = True,
) -> Trainer:
    SQLModel.metadata.create_all(engine, tables=[Trainer.__table__])
    with Session(engine) as session:
        owner = Trainer(
            email=email,
            nome="Ada",
            cognome="Lovelace",
            hashed_password=hash_password(password),
            is_active=active,
        )
        session.add(owner)
        session.commit()
        session.refresh(owner)
        return owner


def test_locked_controller_denies_engine_and_session_without_state_leak():
    controller = BusinessDatabaseController(BusinessDatabaseState.LOCKED)

    with pytest.raises(BusinessDatabaseUnavailableError) as engine_error:
        controller.require_engine()
    with pytest.raises(BusinessDatabaseUnavailableError) as session_error:
        with controller.session():
            pass

    assert str(engine_error.value) == BUSINESS_DATABASE_UNAVAILABLE_DETAIL
    assert str(session_error.value) == BUSINESS_DATABASE_UNAVAILABLE_DETAIL
    assert controller.state is BusinessDatabaseState.LOCKED


def test_candidate_is_published_only_after_owner_check_and_maintenance():
    controller = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    candidate = _engine()
    observations: list[str] = []

    def verify(engine: Engine) -> str:
        assert engine is candidate
        assert controller.state is BusinessDatabaseState.UNLOCKING
        with pytest.raises(BusinessDatabaseUnavailableError):
            controller.require_engine()
        observations.append("owner")
        return "verified-owner"

    def maintain(engine: Engine) -> None:
        assert engine is candidate
        with pytest.raises(BusinessDatabaseUnavailableError):
            controller.require_engine()
        observations.append("maintenance")

    result = controller.unlock_candidate(
        open_candidate=lambda: candidate,
        verify_candidate=verify,
        prepare_candidate=maintain,
    )

    assert result == "verified-owner"
    assert observations == ["owner", "maintenance"]
    assert controller.state is BusinessDatabaseState.UNLOCKED
    assert controller.require_engine() is candidate


@pytest.mark.parametrize("failure_phase", ["open", "owner", "maintenance"])
def test_candidate_failure_is_generic_disposed_and_returns_locked(failure_phase: str):
    controller = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    candidate = MagicMock(spec=Engine)

    def open_candidate():
        if failure_phase == "open":
            raise RuntimeError("driver detail must not escape")
        return candidate

    def verify_candidate(_engine):
        if failure_phase == "owner":
            raise RuntimeError("owner detail must not escape")
        return "owner"

    def prepare_candidate(_engine):
        if failure_phase == "maintenance":
            raise RuntimeError("schema detail must not escape")

    with pytest.raises(BusinessDatabaseUnlockError) as error:
        controller.unlock_candidate(
            open_candidate=open_candidate,
            verify_candidate=verify_candidate,
            prepare_candidate=prepare_candidate,
        )

    assert str(error.value) == BUSINESS_DATABASE_UNAVAILABLE_DETAIL
    assert controller.state is BusinessDatabaseState.LOCKED
    if failure_phase == "open":
        candidate.dispose.assert_not_called()
    else:
        candidate.dispose.assert_called_once_with()


def test_concurrent_unlock_opens_and_publishes_exactly_one_candidate():
    controller = BusinessDatabaseController(BusinessDatabaseState.LOCKED)
    candidate = MagicMock(spec=Engine)
    opener_started = Event()
    release_opener = Event()
    count_lock = Lock()
    open_count = 0

    def open_candidate():
        nonlocal open_count
        with count_lock:
            open_count += 1
        opener_started.set()
        assert release_opener.wait(timeout=5)
        return candidate

    def unlock():
        return controller.unlock_candidate(
            open_candidate=open_candidate,
            verify_candidate=lambda _engine: "owner",
            prepare_candidate=lambda _engine: None,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(unlock)
        assert opener_started.wait(timeout=5)
        second = pool.submit(unlock)
        assert controller.state is BusinessDatabaseState.UNLOCKING
        with pytest.raises(BusinessDatabaseUnavailableError):
            controller.require_engine()
        release_opener.set()
        assert first.result(timeout=5) == "owner"
        with pytest.raises(BusinessDatabaseTransitionError):
            second.result(timeout=5)

    assert open_count == 1
    assert controller.require_engine() is candidate
    candidate.dispose.assert_not_called()


def test_candidate_owner_requires_exactly_one_active_matching_owner():
    engine = _engine()
    owner = _seed_owner(engine)

    verified = verify_candidate_owner(
        engine,
        email=" OWNER@example.com ",
        password="correct horse battery staple",
    )

    assert verified.id == owner.id
    assert verified.email == "owner@example.com"
    assert not hasattr(verified, "hashed_password")


@pytest.mark.parametrize("case", ["wrong-email", "wrong-password", "inactive", "multiple"])
def test_candidate_owner_rejections_are_indistinguishable(case: str):
    engine = _engine()
    _seed_owner(engine, active=case != "inactive")
    if case == "multiple":
        with Session(engine) as session:
            session.add(Trainer(
                email="second@example.com",
                nome="Grace",
                cognome="Hopper",
                hashed_password=hash_password("another secure password"),
            ))
            session.commit()

    email = "wrong@example.com" if case == "wrong-email" else "owner@example.com"
    password = "wrong password" if case == "wrong-password" else "correct horse battery staple"

    with pytest.raises(CandidateOwnerVerificationError) as error:
        verify_candidate_owner(engine, email=email, password=password)

    assert str(error.value) == BUSINESS_DATABASE_UNAVAILABLE_DETAIL
