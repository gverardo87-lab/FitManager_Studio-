"""Schema stretti e costanti del formato envelope CRM v1."""

from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

ENVELOPE_FORMAT_VERSION = 1
CIPHER_PROFILE = "sqlcipher-4-defaults"
ENVELOPE_ERROR_MESSAGE = "Envelope non valido o credenziale errata"

DEK_BYTES = 32
SALT_BYTES = 16
NONCE_BYTES = 12
GCM_TAG_BYTES = 16
WRAPPED_DEK_BYTES = DEK_BYTES + GCM_TAG_BYTES
RECOVERY_KEY_BYTES = 32
RECOVERY_INFO = "fitmanager/crm-recovery/v1"

SCRYPT_N = 2**17
SCRYPT_R = 8
SCRYPT_P = 1

MAX_ENVELOPE_BYTES = 16 * 1024


class EnvelopeError(ValueError):
    """Errore pubblico intenzionalmente indistinguibile per parse/unlock."""


def generic_error() -> EnvelopeError:
    return EnvelopeError(ENVELOPE_ERROR_MESSAGE)


def decode_b64(value: str, *, expected_bytes: int) -> bytes:
    try:
        decoded = base64.b64decode(value, altchars=b"-_", validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid base64") from exc
    if len(decoded) != expected_bytes:
        raise ValueError("invalid binary field length")
    if base64.urlsafe_b64encode(decoded).decode("ascii") != value:
        raise ValueError("non-canonical base64")
    return decoded


def encode_b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class ScryptKdf(_StrictModel):
    name: Literal["scrypt"]
    n: Literal[131072]
    r: Literal[8]
    p: Literal[1]
    salt: str

    @field_validator("salt")
    @classmethod
    def validate_salt(cls, value: str) -> str:
        decode_b64(value, expected_bytes=SALT_BYTES)
        return value


class RecoveryKdf(_StrictModel):
    name: Literal["HKDF-SHA256"]
    salt: str
    info: Literal["fitmanager/crm-recovery/v1"]

    @field_validator("salt")
    @classmethod
    def validate_salt(cls, value: str) -> str:
        decode_b64(value, expected_bytes=SALT_BYTES)
        return value


class WrappedDek(_StrictModel):
    name: Literal["AES-256-GCM"]
    nonce: str
    ciphertext: str

    @field_validator("nonce")
    @classmethod
    def validate_nonce(cls, value: str) -> str:
        decode_b64(value, expected_bytes=NONCE_BYTES)
        return value

    @field_validator("ciphertext")
    @classmethod
    def validate_ciphertext(cls, value: str) -> str:
        decode_b64(value, expected_bytes=WRAPPED_DEK_BYTES)
        return value


class PasswordSlot(_StrictModel):
    kdf: ScryptKdf
    wrap: WrappedDek


class RecoverySlot(_StrictModel):
    kdf: RecoveryKdf
    wrap: WrappedDek


class CrmEnvelope(_StrictModel):
    format_version: Literal[1]
    database_id: str
    cipher_profile: Literal["sqlcipher-4-defaults"]
    password_slot: PasswordSlot
    recovery_slot: RecoverySlot

    @field_validator("database_id")
    @classmethod
    def validate_database_id(cls, value: str) -> str:
        try:
            parsed = uuid.UUID(value)
        except (ValueError, AttributeError) as exc:
            raise ValueError("invalid database id") from exc
        if str(parsed) != value or parsed.version != 4:
            raise ValueError("database id must be a canonical UUID4")
        return value


@dataclass(frozen=True)
class EnvelopeMaterial:
    """Materiale iniziale destinato al setup, con repr sempre redatto."""

    envelope: CrmEnvelope
    dek: bytes
    recovery_key: str

    def __repr__(self) -> str:
        return (
            "EnvelopeMaterial(envelope=<metadata>, dek=<redacted>, "
            "recovery_key=<redacted>)"
        )
