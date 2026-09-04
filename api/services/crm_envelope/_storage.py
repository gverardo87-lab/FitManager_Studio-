"""Parsing bounded e persistenza atomica dell'envelope CRM v1."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

from api.services.crm_envelope._models import (
    MAX_ENVELOPE_BYTES,
    CrmEnvelope,
    generic_error,
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def parse_envelope(data: bytes) -> CrmEnvelope:
    """Valida un documento non fidato senza consentire parametri KDF arbitrari."""
    try:
        if not isinstance(data, bytes) or not data or len(data) > MAX_ENVELOPE_BYTES:
            raise ValueError("invalid envelope size")
        payload = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
        return CrmEnvelope.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, TypeError, ValueError):
        raise generic_error() from None


def serialize_envelope(envelope: CrmEnvelope) -> bytes:
    """Serializza in JSON canonico e newline-terminated."""
    try:
        validated = CrmEnvelope.model_validate(envelope.model_dump())
        encoded = (
            json.dumps(
                validated.model_dump(),
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        if len(encoded) > MAX_ENVELOPE_BYTES:
            raise ValueError("serialized envelope too large")
        return encoded
    except (AttributeError, ValidationError, TypeError, ValueError):
        raise generic_error() from None


def _fsync_directory_best_effort(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def save_envelope_atomic(path: Path, envelope: CrmEnvelope) -> None:
    """Scrive l'envelope con fsync, permessi privati e replace atomico."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = serialize_envelope(envelope)
    temp_path: Optional[str] = None
    try:
        fd, temp_path = tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=str(target.parent),
        )
        with os.fdopen(fd, "wb") as temp_file:
            temp_file.write(data)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        if os.name != "nt":
            os.chmod(temp_path, 0o600)
        os.replace(temp_path, target)
        temp_path = None
        _fsync_directory_best_effort(target.parent)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def load_envelope(path: Path) -> CrmEnvelope:
    """Legge al massimo il budget previsto e valida l'envelope da disco."""
    target = Path(path)
    if target.is_symlink():
        raise generic_error()
    with target.open("rb") as envelope_file:
        data = envelope_file.read(MAX_ENVELOPE_BYTES + 1)
    return parse_envelope(data)
