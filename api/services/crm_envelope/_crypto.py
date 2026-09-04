"""Generazione, wrapping e unwrapping dell'envelope CRM v1."""

from __future__ import annotations

import base64
import json
import re
import secrets
import uuid
from typing import Literal

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pydantic import ValidationError

from api.services.crm_envelope._models import (
    CIPHER_PROFILE,
    DEK_BYTES,
    ENVELOPE_FORMAT_VERSION,
    NONCE_BYTES,
    RECOVERY_INFO,
    RECOVERY_KEY_BYTES,
    SALT_BYTES,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
    WRAPPED_DEK_BYTES,
    CrmEnvelope,
    EnvelopeError,
    EnvelopeMaterial,
    PasswordSlot,
    RecoveryKdf,
    RecoverySlot,
    ScryptKdf,
    WrappedDek,
    decode_b64,
    encode_b64,
    generic_error,
)

_RECOVERY_ALPHABET = re.compile(r"^[A-Za-z2-7 -]+$")


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str) or not password:
        raise generic_error()
    try:
        return password.encode("utf-8")
    except UnicodeEncodeError:
        raise generic_error() from None


def _format_recovery_key(raw_key: bytes) -> str:
    encoded = base64.b32encode(raw_key).decode("ascii").rstrip("=")
    return "-".join(
        encoded[index:index + 4] for index in range(0, len(encoded), 4)
    )


def _parse_recovery_key(recovery_key: str) -> bytes:
    try:
        if not isinstance(recovery_key, str) or not _RECOVERY_ALPHABET.fullmatch(
            recovery_key
        ):
            raise ValueError("invalid recovery alphabet")
        normalized = recovery_key.replace("-", "").replace(" ", "").upper()
        padding = "=" * (-len(normalized) % 8)
        decoded = base64.b32decode(normalized + padding, casefold=False)
        if len(decoded) != RECOVERY_KEY_BYTES:
            raise ValueError("invalid recovery length")
        return decoded
    except (ValueError, TypeError):
        raise generic_error() from None


def _derive_password_kek(password: bytes, salt: bytes) -> bytes:
    return Scrypt(
        salt=salt,
        length=DEK_BYTES,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    ).derive(password)


def _derive_recovery_kek(recovery_key: bytes, salt: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=DEK_BYTES,
        salt=salt,
        info=RECOVERY_INFO.encode("ascii"),
    ).derive(recovery_key)


def _aad(database_id: str, slot_type: Literal["password", "recovery"]) -> bytes:
    fields = {
        "cipher_profile": CIPHER_PROFILE,
        "database_id": database_id,
        "format_version": ENVELOPE_FORMAT_VERSION,
        "slot_type": slot_type,
    }
    return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("ascii")


def _wrap_dek(dek: bytes, kek: bytes, nonce: bytes, aad: bytes) -> WrappedDek:
    ciphertext = AESGCM(kek).encrypt(nonce, dek, aad)
    return WrappedDek(
        name="AES-256-GCM",
        nonce=encode_b64(nonce),
        ciphertext=encode_b64(ciphertext),
    )


def create_envelope(password: str) -> EnvelopeMaterial:
    """Genera DEK, recovery key e due slot indipendenti per un nuovo CRM."""
    password_bytes = _password_bytes(password)
    database_id = str(uuid.uuid4())
    dek = secrets.token_bytes(DEK_BYTES)

    password_salt = secrets.token_bytes(SALT_BYTES)
    password_nonce = secrets.token_bytes(NONCE_BYTES)
    password_kek = _derive_password_kek(password_bytes, password_salt)

    recovery_raw = secrets.token_bytes(RECOVERY_KEY_BYTES)
    recovery_key = _format_recovery_key(recovery_raw)
    recovery_salt = secrets.token_bytes(SALT_BYTES)
    recovery_nonce = secrets.token_bytes(NONCE_BYTES)
    recovery_kek = _derive_recovery_kek(recovery_raw, recovery_salt)

    envelope = CrmEnvelope(
        format_version=ENVELOPE_FORMAT_VERSION,
        database_id=database_id,
        cipher_profile=CIPHER_PROFILE,
        password_slot=PasswordSlot(
            kdf=ScryptKdf(
                name="scrypt",
                n=SCRYPT_N,
                r=SCRYPT_R,
                p=SCRYPT_P,
                salt=encode_b64(password_salt),
            ),
            wrap=_wrap_dek(
                dek,
                password_kek,
                password_nonce,
                _aad(database_id, "password"),
            ),
        ),
        recovery_slot=RecoverySlot(
            kdf=RecoveryKdf(
                name="HKDF-SHA256",
                salt=encode_b64(recovery_salt),
                info=RECOVERY_INFO,
            ),
            wrap=_wrap_dek(
                dek,
                recovery_kek,
                recovery_nonce,
                _aad(database_id, "recovery"),
            ),
        ),
    )
    return EnvelopeMaterial(envelope=envelope, dek=dek, recovery_key=recovery_key)


def _validated(envelope: CrmEnvelope) -> CrmEnvelope:
    try:
        return CrmEnvelope.model_validate(envelope.model_dump())
    except (AttributeError, ValidationError, TypeError, ValueError):
        raise generic_error() from None


def _unwrap(wrap: WrappedDek, kek: bytes, aad: bytes) -> bytes:
    try:
        nonce = decode_b64(wrap.nonce, expected_bytes=NONCE_BYTES)
        ciphertext = decode_b64(
            wrap.ciphertext,
            expected_bytes=WRAPPED_DEK_BYTES,
        )
        dek = AESGCM(kek).decrypt(nonce, ciphertext, aad)
        if len(dek) != DEK_BYTES:
            raise ValueError("invalid DEK length")
        return dek
    except (InvalidTag, ValueError, TypeError):
        raise generic_error() from None


def unwrap_with_password(envelope: CrmEnvelope, password: str) -> bytes:
    """Restituisce la DEK solo se password, metadati e AAD sono autentici."""
    validated = _validated(envelope)
    try:
        salt = decode_b64(
            validated.password_slot.kdf.salt,
            expected_bytes=SALT_BYTES,
        )
        kek = _derive_password_kek(_password_bytes(password), salt)
        return _unwrap(
            validated.password_slot.wrap,
            kek,
            _aad(validated.database_id, "password"),
        )
    except EnvelopeError:
        raise
    except (TypeError, ValueError):
        raise generic_error() from None


def unwrap_with_recovery(envelope: CrmEnvelope, recovery_key: str) -> bytes:
    """Restituisce la DEK solo se recovery key, metadati e AAD sono autentici."""
    validated = _validated(envelope)
    try:
        salt = decode_b64(
            validated.recovery_slot.kdf.salt,
            expected_bytes=SALT_BYTES,
        )
        kek = _derive_recovery_kek(_parse_recovery_key(recovery_key), salt)
        return _unwrap(
            validated.recovery_slot.wrap,
            kek,
            _aad(validated.database_id, "recovery"),
        )
    except EnvelopeError:
        raise
    except (TypeError, ValueError):
        raise generic_error() from None
