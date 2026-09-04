"""API pubblica delle primitive envelope password-bound del CRM (S1.1)."""

from api.services.crm_envelope._crypto import (
    create_envelope,
    unwrap_with_password,
    unwrap_with_recovery,
)
from api.services.crm_envelope._models import (
    CIPHER_PROFILE,
    ENVELOPE_ERROR_MESSAGE,
    ENVELOPE_FORMAT_VERSION,
    MAX_ENVELOPE_BYTES,
    SCRYPT_N,
    SCRYPT_P,
    SCRYPT_R,
    CrmEnvelope,
    EnvelopeError,
    EnvelopeMaterial,
)
from api.services.crm_envelope._storage import (
    load_envelope,
    parse_envelope,
    save_envelope_atomic,
    serialize_envelope,
)

__all__ = [
    "CIPHER_PROFILE",
    "ENVELOPE_ERROR_MESSAGE",
    "ENVELOPE_FORMAT_VERSION",
    "MAX_ENVELOPE_BYTES",
    "SCRYPT_N",
    "SCRYPT_P",
    "SCRYPT_R",
    "CrmEnvelope",
    "EnvelopeError",
    "EnvelopeMaterial",
    "create_envelope",
    "load_envelope",
    "parse_envelope",
    "save_envelope_atomic",
    "serialize_envelope",
    "unwrap_with_password",
    "unwrap_with_recovery",
]
