"""S1.1 — primitive envelope G1/G5, senza integrazione col database."""

from __future__ import annotations

import base64
import json
import uuid
from pathlib import Path

import pytest

from api.services.crm_envelope import _storage as envelope_storage
from api.services.crm_envelope import (
    CIPHER_PROFILE,
    ENVELOPE_ERROR_MESSAGE,
    ENVELOPE_FORMAT_VERSION,
    MAX_ENVELOPE_BYTES,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
    EnvelopeError,
    create_envelope,
    parse_envelope,
    save_envelope_atomic,
    serialize_envelope,
    unwrap_with_password,
    unwrap_with_recovery,
)


PASSWORD = "Una passphrase robusta 2026"


@pytest.fixture(scope="module")
def material():
    return create_envelope(PASSWORD)


def _payload(material) -> dict:
    return json.loads(serialize_envelope(material.envelope))


def _tamper_base64(value: str) -> str:
    raw = bytearray(base64.b64decode(value, altchars=b"-_", validate=True))
    raw[-1] ^= 1
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _assert_generic_error(callable_) -> None:
    with pytest.raises(EnvelopeError) as exc_info:
        callable_()
    assert str(exc_info.value) == ENVELOPE_ERROR_MESSAGE
    assert exc_info.value.__cause__ is None


def test_create_roundtrip_password_and_recovery(material):
    assert len(material.dek) == 32
    assert unwrap_with_password(material.envelope, PASSWORD) == material.dek
    assert unwrap_with_recovery(material.envelope, material.recovery_key) == material.dek

    envelope = material.envelope
    assert envelope.format_version == ENVELOPE_FORMAT_VERSION == 1
    assert envelope.cipher_profile == CIPHER_PROFILE == "sqlcipher-4-defaults"
    assert envelope.password_slot.kdf.n == SCRYPT_N == 2**17
    assert envelope.password_slot.kdf.r == SCRYPT_R == 8
    assert envelope.password_slot.kdf.p == SCRYPT_P == 1
    assert str(uuid.UUID(envelope.database_id)) == envelope.database_id


def test_same_password_produces_independent_material():
    first = create_envelope(PASSWORD)
    second = create_envelope(PASSWORD)

    assert first.dek != second.dek
    assert first.recovery_key != second.recovery_key
    assert first.envelope.database_id != second.envelope.database_id
    assert serialize_envelope(first.envelope) != serialize_envelope(second.envelope)


def test_serialized_envelope_and_repr_do_not_expose_secrets(material):
    serialized = serialize_envelope(material.envelope)

    assert PASSWORD.encode("utf-8") not in serialized
    assert material.recovery_key.encode("ascii") not in serialized
    assert material.dek not in serialized
    assert material.dek.hex().encode("ascii") not in serialized
    assert PASSWORD not in repr(material)
    assert material.recovery_key not in repr(material)
    assert material.dek.hex() not in repr(material)
    assert "redacted" in repr(material).lower()


def test_wrong_password_and_wrong_recovery_have_same_public_error(material):
    _assert_generic_error(
        lambda: unwrap_with_password(material.envelope, "password deliberatamente errata")
    )
    _assert_generic_error(
        lambda: unwrap_with_recovery(
            material.envelope,
            create_envelope("Altra passphrase robusta").recovery_key,
        )
    )


@pytest.mark.parametrize("slot_name", ["password_slot", "recovery_slot"])
def test_ciphertext_tamper_is_rejected_generically(material, slot_name):
    payload = _payload(material)
    payload[slot_name]["wrap"]["ciphertext"] = _tamper_base64(
        payload[slot_name]["wrap"]["ciphertext"]
    )
    tampered = parse_envelope(json.dumps(payload).encode("utf-8"))

    if slot_name == "password_slot":
        _assert_generic_error(lambda: unwrap_with_password(tampered, PASSWORD))
    else:
        _assert_generic_error(
            lambda: unwrap_with_recovery(tampered, material.recovery_key)
        )


def test_database_id_is_authenticated_as_aad(material):
    payload = _payload(material)
    payload["database_id"] = str(uuid.uuid4())
    rebound = parse_envelope(json.dumps(payload).encode("utf-8"))

    _assert_generic_error(lambda: unwrap_with_password(rebound, PASSWORD))
    _assert_generic_error(
        lambda: unwrap_with_recovery(rebound, material.recovery_key)
    )


def test_recovery_parser_accepts_only_safe_canonical_variants(material):
    readable_variant = material.recovery_key.lower().replace("-", " ")
    assert unwrap_with_recovery(material.envelope, readable_variant) == material.dek

    _assert_generic_error(
        lambda: unwrap_with_recovery(material.envelope, f"{material.recovery_key}!")
    )
    _assert_generic_error(
        lambda: unwrap_with_recovery(material.envelope, material.recovery_key[:-1])
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(format_version=2),
        lambda p: p.update(cipher_profile="sqlcipher-unknown"),
        lambda p: p.update(unexpected="value"),
        lambda p: p["password_slot"]["kdf"].update(n=2**25),
        lambda p: p["password_slot"]["kdf"].update(
            salt=base64.b64encode(b"\xfb" * 16).decode("ascii")
        ),
        lambda p: p["password_slot"]["wrap"].update(nonce="not-base64!"),
        lambda p: p.update(database_id="not-a-uuid"),
        lambda p: p.update(
            password_slot=p["recovery_slot"],
            recovery_slot=p["password_slot"],
        ),
    ],
)
def test_untrusted_envelope_schema_is_strict_and_bounded(material, mutate):
    payload = _payload(material)
    mutate(payload)

    _assert_generic_error(
        lambda: parse_envelope(json.dumps(payload).encode("utf-8"))
    )


def test_truncated_duplicate_and_oversized_documents_are_rejected():
    _assert_generic_error(lambda: parse_envelope(b'{"format_version": 1'))
    _assert_generic_error(
        lambda: parse_envelope(b'{"format_version":1,"format_version":1}')
    )
    _assert_generic_error(lambda: parse_envelope(b"x" * (MAX_ENVELOPE_BYTES + 1)))


def test_atomic_save_roundtrip_and_private_mode(material, tmp_path):
    target = tmp_path / "nested" / "crm-envelope.json"

    save_envelope_atomic(target, material.envelope)
    loaded = envelope_storage.load_envelope(target)

    assert loaded == material.envelope
    assert target.read_bytes() == serialize_envelope(material.envelope)
    assert not list(target.parent.glob(f".{target.name}.*.tmp"))
    if envelope_storage.os.name != "nt":
        assert target.stat().st_mode & 0o777 == 0o600


def test_failed_atomic_replace_preserves_previous_file(monkeypatch, tmp_path):
    target = tmp_path / "crm-envelope.json"
    original = create_envelope("Passphrase originale robusta")
    replacement = create_envelope("Passphrase sostitutiva robusta")
    save_envelope_atomic(target, original.envelope)
    original_bytes = target.read_bytes()

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(envelope_storage.os, "replace", fail_replace)

    with pytest.raises(OSError, match="injected replace failure"):
        save_envelope_atomic(target, replacement.envelope)

    assert target.read_bytes() == original_bytes
    assert not list(tmp_path.glob(f".{target.name}.*.tmp"))
