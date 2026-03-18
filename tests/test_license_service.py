from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from api.services.license import LICENSE_ALGORITHM, check_license


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


def _create_license_token(
    private_key_pem: str,
    expires_at: datetime,
    client_id: str = "gym-roma",
    tier: str = "pro",
    max_clients: int = 50,
) -> str:
    payload = {
        "client_id": client_id,
        "tier": tier,
        "max_clients": max_clients,
        "exp": expires_at,
    }
    return jwt.encode(payload, private_key_pem, algorithm=LICENSE_ALGORITHM)


def test_check_license_missing_file(tmp_path):
    result = check_license(
        token_path=tmp_path / "license.key",
        public_key="dummy-public-key",
    )

    assert result.status == "missing"
    assert result.claims is None
    assert result.expires_at is None


def test_check_license_unconfigured_public_key(tmp_path):
    private_key, _ = _generate_rsa_keypair()
    token = _create_license_token(
        private_key,
        datetime.now(timezone.utc) + timedelta(days=30),
    )

    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    result = check_license(token_path=license_file, public_key="")

    assert result.status == "unconfigured"
    assert result.claims is None
    assert result.expires_at is None


def test_check_license_valid(tmp_path):
    private_key, public_key = _generate_rsa_keypair()
    token = _create_license_token(
        private_key,
        datetime.now(timezone.utc) + timedelta(days=90),
        client_id="fit-roma",
        tier="pro",
        max_clients=120,
    )

    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "valid"
    assert result.claims is not None
    assert result.claims.client_id == "fit-roma"
    assert result.claims.tier == "pro"
    assert result.claims.max_clients == 120
    assert result.expires_at is not None
    assert result.expires_at > datetime.now(timezone.utc)


def test_check_license_expired(tmp_path):
    private_key, public_key = _generate_rsa_keypair()
    token = _create_license_token(
        private_key,
        datetime.now(timezone.utc) - timedelta(days=1),
    )

    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "expired"
    assert result.claims is not None
    assert result.expires_at is not None
    assert result.expires_at < datetime.now(timezone.utc)


def test_check_license_valid_with_matching_machine_id(tmp_path):
    """Licenza con machine_id che corrisponde alla macchina corrente = valid."""
    private_key, public_key = _generate_rsa_keypair()
    machine_fp = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    token = jwt.encode(
        {
            "client_id": "test",
            "tier": "pro",
            "machine_id": machine_fp,
            "exp": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
        },
        private_key,
        algorithm=LICENSE_ALGORITHM,
    )
    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    with patch(
        "api.services.machine_fingerprint.get_machine_fingerprint",
        return_value=machine_fp,
    ):
        result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "valid"


def test_check_license_wrong_machine(tmp_path):
    """Licenza con machine_id diverso dalla macchina corrente = wrong_machine."""
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

    with patch(
        "api.services.machine_fingerprint.get_machine_fingerprint",
        return_value="bbbb" * 16,
    ):
        result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "wrong_machine"
    assert result.message == "Licenza associata a un altro computer"
    assert result.claims is not None


def test_check_license_no_machine_id_backward_compat(tmp_path):
    """Licenza senza machine_id (backward compat) = valid."""
    private_key, public_key = _generate_rsa_keypair()
    token = _create_license_token(
        private_key,
        datetime.now(timezone.utc) + timedelta(days=30),
    )
    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    result = check_license(token_path=license_file, public_key=public_key)
    assert result.status == "valid"


def test_check_license_machine_unavailable_skips_check(tmp_path):
    """Se fingerprint non disponibile, il check machine viene saltato."""
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

    with patch(
        "api.services.machine_fingerprint.get_machine_fingerprint",
        return_value="unavailable",
    ):
        result = check_license(token_path=license_file, public_key=public_key)

    assert result.status == "valid"


def test_check_license_invalid_signature(tmp_path):
    good_private, good_public = _generate_rsa_keypair()
    bad_private, _ = _generate_rsa_keypair()

    # Firma con una chiave diversa da quella usata in verifica.
    token = _create_license_token(
        bad_private,
        datetime.now(timezone.utc) + timedelta(days=7),
    )

    license_file = tmp_path / "license.key"
    license_file.write_text(token, encoding="utf-8")

    result = check_license(token_path=license_file, public_key=good_public)

    assert result.status == "invalid"
    assert result.claims is None
    assert result.expires_at is None
