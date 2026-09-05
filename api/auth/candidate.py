"""Verifica dell'owner confinata all'engine CRM candidato."""

from __future__ import annotations

from dataclasses import dataclass
from hmac import compare_digest

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from api.auth.service import verify_password
from api.models.trainer import Trainer
from api.services.business_database import BUSINESS_DATABASE_UNAVAILABLE_DETAIL


_DUMMY_BCRYPT_HASH = "$2b$12$LJ3m4ys3Lp0Ab5XGJkPbXeDMDjCiOC2JIHbVf5a5e5e5e5e5e5e5e"


class CandidateOwnerVerificationError(RuntimeError):
    """Errore pubblico uniforme per ogni fallimento della verifica owner."""


@dataclass(frozen=True, slots=True)
class VerifiedOwner:
    """Snapshot minimo e privo di hash dell'owner verificato."""

    id: int
    email: str
    nome: str
    cognome: str


def verify_candidate_owner(engine: Engine, *, email: str, password: str) -> VerifiedOwner:
    """Richiede esattamente un owner attivo con email e bcrypt validi."""
    try:
        with Session(engine) as session:
            owners = list(session.exec(select(Trainer).limit(2)).all())
    except Exception:
        raise CandidateOwnerVerificationError(
            BUSINESS_DATABASE_UNAVAILABLE_DETAIL
        ) from None

    owner = owners[0] if len(owners) == 1 else None
    password_hash = owner.hashed_password if owner is not None else _DUMMY_BCRYPT_HASH
    try:
        password_valid = verify_password(password, password_hash)
    except Exception:
        password_valid = False

    normalized_email = email.strip().lower()
    owner_email = owner.email.strip().lower() if owner is not None else ""
    email_valid = compare_digest(normalized_email, owner_email)
    if (
        owner is None
        or owner.id is None
        or not owner.is_active
        or not email_valid
        or not password_valid
    ):
        raise CandidateOwnerVerificationError(
            BUSINESS_DATABASE_UNAVAILABLE_DETAIL
        ) from None

    return VerifiedOwner(
        id=owner.id,
        email=owner_email,
        nome=owner.nome,
        cognome=owner.cognome,
    )
