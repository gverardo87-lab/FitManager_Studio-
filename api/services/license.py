"""
License service (Phase 1) - verifica RSA offline del file licenza locale.

Questo modulo NON applica enforcement HTTP: espone utility pure per:
1) leggere token da data/license.key
2) validare firma + expiry (RS256)
3) restituire uno stato normalizzato per middleware/health endpoint

HARDENING (2026-03-24):
- Chiave pubblica embedded nel codice (anti file-replacement attack)
- Integrity hash SHA-256 della chiave (anti bytecode patching)
- In frozen mode: SOLO chiave embedded, file/env ignorati
- In frozen mode: fingerprint "unavailable" = blocco (fail-closed)
"""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel, Field, ValidationError

from api.config import DATA_DIR


LICENSE_FILE = DATA_DIR / "license.key"
LICENSE_ALGORITHM = "RS256"

# --- Chiave pubblica embedded (anti file-replacement attack) ---
# In frozen mode (PyInstaller), SOLO questa chiave viene usata.
# In dev mode, la risoluzione file/env resta attiva per flessibilita'.
EMBEDDED_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxPJrJC7U/S5i95FqHSme
WWSu2SMiKNtJmc9LUgQfpB/J5fFv6ZkD4wJEG8MAUD+tKit5+0yz/M9ECcrDQBxG
ZWKroivJ5B2i30bVssCxw20CO+0HM5ahY9qptKePY8N+T+HTfD5jI5ny5PzFBa2q
mOxUAFRfVMfUhGmTFVf5NG7IZPDC7varfpQf4/8rSUM0dGw6r60a/Rsm34/b86lv
PyBWMRboSUNHhoj3EP62g9V6pUzOm8mXpNwbH9WseQEXe4EF0STRrbtVs4szROyA
u+dLcmYiskfUYjHftI1aonbqXrPfA+qzMQVyi6b6Mmbwql8k+IEclClX6DaYxeZV
LQIDAQAB
-----END PUBLIC KEY-----"""

# SHA-256 della chiave pubblica embedded — integrity check anti-tampering.
# Se qualcuno modifica la chiave nel bytecode, l'hash non corrisponde.
EMBEDDED_PUBLIC_KEY_HASH = "967fbcfaac52fa99f9671056a83112bc17c62d1353536c3a54b18ed1bf796705"

# Fallback per dev mode (risoluzione da file)
PUBLIC_KEY_FILE = DATA_DIR / "license_public.pem"


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


LicenseStatus = Literal["valid", "missing", "invalid", "expired", "unconfigured", "wrong_machine"]


class LicenseClaims(BaseModel):
    """Claim minimi richiesti dal token licenza."""

    client_id: str = Field(min_length=1)
    client_name: str | None = None
    client_surname: str | None = None
    client_birthdate: str | None = None  # YYYY-MM-DD
    client_email: str | None = None
    tier: str = Field(min_length=1)
    max_clients: int | None = Field(default=None, ge=1)
    machine_id: str | None = None
    exp: int


class LicenseCheckResult(BaseModel):
    """Esito standardizzato per middleware/health/UI."""

    status: LicenseStatus
    message: str
    expires_at: datetime | None = None
    claims: LicenseClaims | None = None

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"


def _verify_embedded_key_integrity() -> bool:
    """Verifica che la chiave embedded non sia stata alterata nel bytecode."""
    actual_hash = hashlib.sha256(EMBEDDED_PUBLIC_KEY_PEM.strip().encode("utf-8")).hexdigest()
    return actual_hash == EMBEDDED_PUBLIC_KEY_HASH


def _load_public_key(public_key: str | None = None) -> str | None:
    """Risoluzione chiave pubblica.

    Frozen (PyInstaller): SOLO chiave embedded + integrity check.
    Dev/test: parametro > env > file > embedded (flessibile).
    """
    # Parametro esplicito (usato dai test) — sempre prioritario
    if public_key is not None:
        key = public_key.strip()
        return key or None

    # Frozen mode: SOLO chiave embedded, nessun file/env sovrascrivibile
    if _is_frozen():
        if not _verify_embedded_key_integrity():
            return None  # Chiave alterata → unconfigured → blocco
        return EMBEDDED_PUBLIC_KEY_PEM.strip()

    # Dev mode: risoluzione flessibile (env > file > embedded)
    env_key = os.getenv("LICENSE_PUBLIC_KEY", "").strip()
    if env_key:
        return env_key.replace("\\n", "\n")

    if PUBLIC_KEY_FILE.exists():
        file_key = PUBLIC_KEY_FILE.read_text(encoding="utf-8").strip()
        return file_key or None

    embedded = EMBEDDED_PUBLIC_KEY_PEM.strip()
    return embedded or None


def _read_license_token(token_path: Path) -> str | None:
    """Legge token JWT da file (None se assente o vuoto)."""
    if not token_path.exists():
        return None

    token = token_path.read_text(encoding="utf-8").strip()
    return token or None


def _to_utc_datetime(exp: int | float) -> datetime:
    """Converte timestamp unix in datetime UTC aware."""
    return datetime.fromtimestamp(float(exp), tz=timezone.utc)


def _decode_claims(token: str, public_key: str) -> LicenseClaims:
    """Decode con verifica firma + expiry."""
    payload = jwt.decode(
        token,
        public_key,
        algorithms=[LICENSE_ALGORITHM],
        options={"verify_aud": False},
    )
    return LicenseClaims.model_validate(payload)


def _decode_claims_ignore_exp(token: str, public_key: str) -> LicenseClaims | None:
    """Best effort: utile per mostrare expiry anche quando la licenza e' scaduta."""
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=[LICENSE_ALGORITHM],
            options={"verify_aud": False, "verify_exp": False},
        )
        return LicenseClaims.model_validate(payload)
    except (JWTError, ValidationError):
        return None


def check_license(
    token_path: Path = LICENSE_FILE,
    public_key: str | None = None,
) -> LicenseCheckResult:
    """
    Valida la licenza locale.

    Stati:
    - missing: file licenza assente/vuoto
    - unconfigured: chiave pubblica non configurata
    - invalid: firma/claims non validi
    - expired: token valido ma scaduto
    - valid: licenza valida
    """
    token = _read_license_token(token_path)
    if token is None:
        return LicenseCheckResult(
            status="missing",
            message="Licenza non trovata",
        )

    key = _load_public_key(public_key)
    if key is None:
        return LicenseCheckResult(
            status="unconfigured",
            message="Chiave pubblica licenza non configurata",
        )

    try:
        claims = _decode_claims(token, key)

        # Hardware binding: se il JWT contiene machine_id, verifica che
        # corrisponda al fingerprint della macchina corrente.
        if claims.machine_id:
            from api.services.machine_fingerprint import get_machine_fingerprint

            current_fp = get_machine_fingerprint()

            # Frozen mode (fail-closed): se fingerprint non disponibile,
            # blocca invece di saltare il check. Impedisce bypass via
            # PowerShell disabilitato o WMI bloccato.
            if current_fp == "unavailable" and _is_frozen():
                return LicenseCheckResult(
                    status="wrong_machine",
                    message="Impossibile verificare l'hardware — contattare supporto",
                    expires_at=_to_utc_datetime(claims.exp),
                    claims=claims,
                )

            if current_fp != "unavailable" and claims.machine_id != current_fp:
                return LicenseCheckResult(
                    status="wrong_machine",
                    message="Licenza associata a un altro computer",
                    expires_at=_to_utc_datetime(claims.exp),
                    claims=claims,
                )

        return LicenseCheckResult(
            status="valid",
            message="Licenza valida",
            expires_at=_to_utc_datetime(claims.exp),
            claims=claims,
        )
    except ExpiredSignatureError:
        claims = _decode_claims_ignore_exp(token, key)
        return LicenseCheckResult(
            status="expired",
            message="Licenza scaduta",
            expires_at=_to_utc_datetime(claims.exp) if claims else None,
            claims=claims,
        )
    except (JWTError, ValidationError):
        return LicenseCheckResult(
            status="invalid",
            message="Licenza non valida",
        )
