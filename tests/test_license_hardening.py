"""Test hardening licenza (2026-03-24).

Copre i 4 vettori di attacco chiusi:
1. Embedded public key + integrity hash (anti file-replacement)
2. Enforcement sempre ON in frozen mode (anti env var bypass)
3. Fingerprint fail-closed in frozen mode (anti PowerShell block)
4. Key integrity check (anti bytecode patching)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from api.services.license import (
    LICENSE_ALGORITHM,
    _verify_embedded_key_integrity,
    check_license,
)


def _generate_rsa_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


# --- Hardening #1: Embedded key integrity ---


def test_embedded_key_integrity_passes():
    """La chiave embedded corrisponde all'hash atteso."""
    assert _verify_embedded_key_integrity() is True


def test_embedded_key_integrity_fails_on_tampered_key(monkeypatch):
    """Se la chiave embedded viene alterata, l'integrity check fallisce."""
    monkeypatch.setattr(
        "api.services.license.EMBEDDED_PUBLIC_KEY_PEM",
        "-----BEGIN PUBLIC KEY-----\nTAMPERED\n-----END PUBLIC KEY-----",
    )
    assert _verify_embedded_key_integrity() is False


def test_embedded_key_integrity_fails_on_tampered_hash(monkeypatch):
    """Se l'hash viene alterato, l'integrity check fallisce."""
    monkeypatch.setattr(
        "api.services.license.EMBEDDED_PUBLIC_KEY_HASH",
        "0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert _verify_embedded_key_integrity() is False


# --- Hardening #1b: Frozen mode uses ONLY embedded key ---


def test_frozen_mode_uses_embedded_key_ignores_file(tmp_path, monkeypatch):
    """In frozen mode, la chiave da file viene ignorata — usa solo embedded."""
    # Crea un token firmato con la chiave embedded reale (non possibile senza
    # private key), quindi usiamo una chiave di test e verifichiamo che in
    # frozen mode il file viene ignorato (= invalid perche' firma non corrisponde).
    private_key, fake_public = _generate_rsa_keypair()
    token = jwt.encode(
        {
            "client_id": "test",
            "tier": "pro",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        },
        private_key,
        algorithm=LICENSE_ALGORITHM,
    )
    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    # Metti la chiave pubblica corrispondente nel file — in dev funzionerebbe
    pub_file = tmp_path / "license_public.pem"
    pub_file.write_text(fake_public, encoding="utf-8")
    monkeypatch.setattr("api.services.license.PUBLIC_KEY_FILE", pub_file)

    # Simula frozen mode
    monkeypatch.setattr("api.services.license.sys", type("sys", (), {"frozen": True}))

    # In frozen mode, la chiave embedded (diversa) viene usata → invalid
    result = check_license(token_path=license_file)
    assert result.status == "invalid"


def test_frozen_mode_blocks_on_tampered_embedded_key(tmp_path, monkeypatch):
    """In frozen mode, se la chiave embedded e' stata alterata → unconfigured."""
    private_key, _ = _generate_rsa_keypair()
    token = jwt.encode(
        {
            "client_id": "test",
            "tier": "pro",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        },
        private_key,
        algorithm=LICENSE_ALGORITHM,
    )
    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    # Simula frozen + chiave alterata
    monkeypatch.setattr("api.services.license.sys", type("sys", (), {"frozen": True}))
    monkeypatch.setattr(
        "api.services.license.EMBEDDED_PUBLIC_KEY_PEM",
        "-----BEGIN PUBLIC KEY-----\nTAMPERED\n-----END PUBLIC KEY-----",
    )

    result = check_license(token_path=license_file)
    assert result.status == "unconfigured"


# --- Hardening #2: Enforcement always ON in frozen ---


def test_enforcement_always_on_in_frozen_ignores_env(monkeypatch):
    """In frozen mode, LICENSE_ENFORCEMENT_ENABLED=false viene ignorato."""
    from api.services.system_runtime import is_license_enforcement_enabled

    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "false")
    monkeypatch.setattr(
        "api.services.system_runtime.sys",
        type("sys", (), {"frozen": True}),
    )
    assert is_license_enforcement_enabled() is True


def test_enforcement_respects_env_in_dev(monkeypatch):
    """In dev mode, LICENSE_ENFORCEMENT_ENABLED e' rispettato."""
    from api.services.system_runtime import is_license_enforcement_enabled
    import sys as real_sys

    monkeypatch.setattr("api.services.system_runtime.sys", real_sys)
    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "true")
    assert is_license_enforcement_enabled() is True

    monkeypatch.setenv("LICENSE_ENFORCEMENT_ENABLED", "false")
    assert is_license_enforcement_enabled() is False


# --- Hardening #3: Fingerprint fail-closed in frozen ---


def test_frozen_fingerprint_unavailable_blocks_license(tmp_path, monkeypatch):
    """In frozen mode, fingerprint 'unavailable' = wrong_machine (fail-closed)."""
    private_key, public_key = _generate_rsa_keypair()
    token = jwt.encode(
        {
            "client_id": "test",
            "tier": "pro",
            "machine_id": "aaaa" * 16,
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        },
        private_key,
        algorithm=LICENSE_ALGORITHM,
    )
    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    # Simula frozen mode + fingerprint non disponibile
    monkeypatch.setattr("api.services.license.sys", type("sys", (), {"frozen": True}))
    with patch(
        "api.services.machine_fingerprint.get_machine_fingerprint",
        return_value="unavailable",
    ):
        result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "wrong_machine"
    assert "hardware" in result.message.lower() or "supporto" in result.message.lower()


def test_dev_fingerprint_unavailable_still_allows(tmp_path, monkeypatch):
    """In dev mode, fingerprint 'unavailable' = skip check (backward compat)."""
    private_key, public_key = _generate_rsa_keypair()
    token = jwt.encode(
        {
            "client_id": "test",
            "tier": "pro",
            "machine_id": "aaaa" * 16,
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        },
        private_key,
        algorithm=LICENSE_ALGORITHM,
    )
    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    # Dev mode (non frozen) + fingerprint non disponibile
    import sys as real_sys
    monkeypatch.setattr("api.services.license.sys", real_sys)
    with patch(
        "api.services.machine_fingerprint.get_machine_fingerprint",
        return_value="unavailable",
    ):
        result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "valid"
