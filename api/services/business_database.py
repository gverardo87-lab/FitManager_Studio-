"""Boundary late-bound per l'engine CRM business.

Il controller possiede l'unico riferimento pubblicabile all'engine. Una candidate
resta confinata alla transizione finché verifica owner e manutenzione non terminano.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from contextlib import contextmanager
from enum import Enum
from threading import Lock, RLock
from typing import TypeVar

from sqlalchemy.engine import Engine
from sqlmodel import Session


BUSINESS_DATABASE_UNAVAILABLE_DETAIL = "Servizio dati temporaneamente non disponibile"


class BusinessDatabaseState(str, Enum):
    """State machine prescritta dalla SPEC S1 G1/G5."""

    UNINITIALIZED = "UNINITIALIZED"
    SETUP_RECOVERY_PENDING = "SETUP_RECOVERY_PENDING"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    MIGRATING = "MIGRATING"
    LOCKED = "LOCKED"
    UNLOCKING = "UNLOCKING"
    UNLOCKED = "UNLOCKED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    ERROR = "ERROR"


class BusinessDatabaseStorageMode(str, Enum):
    """Distingue il solo seam plaintext dev dal percorso cifrato di produzione."""

    PLAINTEXT_DEVELOPMENT = "PLAINTEXT_DEVELOPMENT"
    ENCRYPTED = "ENCRYPTED"


class BusinessDatabaseUnavailableError(RuntimeError):
    """Accesso negato quando nessun engine business è pubblicato."""


class BusinessDatabaseUnlockError(BusinessDatabaseUnavailableError):
    """Apertura candidata fallita senza esporre la fase interna."""


class BusinessDatabaseTransitionError(BusinessDatabaseUnavailableError):
    """Transizione incompatibile con lo stato corrente."""


VerifiedResult = TypeVar("VerifiedResult")


class BusinessDatabaseController:
    """Serializza le transizioni e pubblica un engine solo dopo tutti i gate."""

    def __init__(
        self,
        initial_state: BusinessDatabaseState,
        *,
        allow_plaintext_development: bool = False,
    ) -> None:
        self._state = initial_state
        self._engine: Engine | None = None
        self._storage_mode: BusinessDatabaseStorageMode | None = None
        self._allow_plaintext_development = allow_plaintext_development
        self._state_lock = RLock()
        self._transition_lock = Lock()

    @property
    def state(self) -> BusinessDatabaseState:
        with self._state_lock:
            return self._state

    @property
    def is_unlocked(self) -> bool:
        with self._state_lock:
            return self._state is BusinessDatabaseState.UNLOCKED and self._engine is not None

    @property
    def storage_mode(self) -> BusinessDatabaseStorageMode | None:
        with self._state_lock:
            return self._storage_mode

    def require_engine(self) -> Engine:
        """Ritorna l'engine pubblicato o fallisce senza rivelare lo stato."""
        with self._state_lock:
            if self._state is not BusinessDatabaseState.UNLOCKED or self._engine is None:
                raise BusinessDatabaseUnavailableError(
                    BUSINESS_DATABASE_UNAVAILABLE_DETAIL
                ) from None
            return self._engine

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Apre una sessione soltanto sull'engine già pubblicato."""
        engine = self.require_engine()
        with Session(engine) as session:
            yield session

    def initialize_plaintext_development_engine(
        self,
        open_engine: Callable[[], Engine],
    ) -> Engine:
        """Seam esplicito per dev/test; il wrapper produttivo lo vieta in compiled mode."""
        with self._transition_lock:
            if not self._allow_plaintext_development:
                raise BusinessDatabaseTransitionError(
                    BUSINESS_DATABASE_UNAVAILABLE_DETAIL
                ) from None
            with self._state_lock:
                if self._state is BusinessDatabaseState.UNLOCKED and self._engine is not None:
                    return self._engine
                previous_state = self._state
                self._state = BusinessDatabaseState.UNLOCKING

            candidate: Engine | None = None
            try:
                candidate = open_engine()
                with self._state_lock:
                    self._engine = candidate
                    self._storage_mode = BusinessDatabaseStorageMode.PLAINTEXT_DEVELOPMENT
                    self._state = BusinessDatabaseState.UNLOCKED
                return candidate
            except Exception:
                self._dispose_candidate(candidate)
                with self._state_lock:
                    self._engine = None
                    self._storage_mode = None
                    self._state = previous_state
                raise BusinessDatabaseUnlockError(
                    BUSINESS_DATABASE_UNAVAILABLE_DETAIL
                ) from None

    def unlock_candidate(
        self,
        *,
        open_candidate: Callable[[], Engine],
        verify_candidate: Callable[[Engine], VerifiedResult],
        prepare_candidate: Callable[[Engine], None],
    ) -> VerifiedResult:
        """Apre, verifica e prepara una candidate prima della pubblicazione atomica."""
        with self._transition_lock:
            with self._state_lock:
                if self._state is not BusinessDatabaseState.LOCKED:
                    raise BusinessDatabaseTransitionError(
                        BUSINESS_DATABASE_UNAVAILABLE_DETAIL
                    ) from None
                self._state = BusinessDatabaseState.UNLOCKING

            candidate: Engine | None = None
            try:
                candidate = open_candidate()
                verified = verify_candidate(candidate)
                prepare_candidate(candidate)
                with self._state_lock:
                    self._engine = candidate
                    self._storage_mode = BusinessDatabaseStorageMode.ENCRYPTED
                    self._state = BusinessDatabaseState.UNLOCKED
                return verified
            except Exception:
                self._dispose_candidate(candidate)
                with self._state_lock:
                    self._engine = None
                    self._storage_mode = None
                    self._state = BusinessDatabaseState.LOCKED
                raise BusinessDatabaseUnlockError(
                    BUSINESS_DATABASE_UNAVAILABLE_DETAIL
                ) from None

    @staticmethod
    def _dispose_candidate(candidate: Engine | None) -> None:
        if candidate is None:
            return
        try:
            candidate.dispose()
        except Exception:
            pass
