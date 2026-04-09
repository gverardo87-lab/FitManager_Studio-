"""
AES-256-GCM encryption/decryption for read-only catalog databases.

Build-time: encrypt_db() produces salt(16) + nonce(12) + ciphertext.
Runtime: decrypt_db_to_bytes() returns raw SQLite bytes for in-memory loading.

Key derivation: PBKDF2-HMAC-SHA256 from embedded seed + per-file salt.
"""

import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Embedded key material — obfuscated in compiled binary
_EMBEDDED_KEY_SEED = "2f29f8634c9350a7fd53c95f22b7dc682edb3b89faf90b76deaceea2c65989d0"
_EMBEDDED_KEY_HASH = "ba8d1d3afba27a672eb2b2967074f4554af12cc41889788dd8e33290ce2e9933"

_SALT_LEN = 16
_NONCE_LEN = 12
_PBKDF2_ITERATIONS = 100_000


def _verify_seed_integrity() -> bool:
    """Verify embedded seed has not been tampered with."""
    actual = hashlib.sha256(_EMBEDDED_KEY_SEED.encode("utf-8")).hexdigest()
    return actual == _EMBEDDED_KEY_HASH


def _derive_key(salt: bytes) -> bytes:
    """Derive AES-256 key from embedded seed + salt via PBKDF2."""
    if not _verify_seed_integrity():
        raise RuntimeError("DB crypto: seed integrity check failed")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    return kdf.derive(_EMBEDDED_KEY_SEED.encode("utf-8"))


def encrypt_db(db_path: Path, output_path: Path) -> None:
    """Encrypt a SQLite database file (build-time).

    Format: salt(16) + nonce(12) + ciphertext (AES-256-GCM).
    """
    plaintext = db_path.read_bytes()
    salt = os.urandom(_SALT_LEN)
    nonce = os.urandom(_NONCE_LEN)
    key = _derive_key(salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    output_path.write_bytes(salt + nonce + ciphertext)


def decrypt_db_to_bytes(enc_path: Path) -> bytes:
    """Decrypt an encrypted database file to raw SQLite bytes (runtime)."""
    data = enc_path.read_bytes()
    salt = data[:_SALT_LEN]
    nonce = data[_SALT_LEN:_SALT_LEN + _NONCE_LEN]
    ciphertext = data[_SALT_LEN + _NONCE_LEN:]
    key = _derive_key(salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
