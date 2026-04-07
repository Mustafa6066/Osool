"""
Field-level encryption for sensitive data at rest.
Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).

The encryption key is derived from FIELD_ENCRYPTION_KEY env var,
or falls back to a deterministic derivation from JWT_SECRET_KEY
so no new env var is strictly required.
"""

import os
import base64
import logging
from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """Get or create the Fernet instance. Cached for process lifetime."""
    key = os.getenv("FIELD_ENCRYPTION_KEY")
    if key:
        # Direct Fernet key (must be 32 url-safe base64-encoded bytes)
        return Fernet(key.encode())

    # Derive from JWT_SECRET_KEY so encryption works without a new env var
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise ValueError("Neither FIELD_ENCRYPTION_KEY nor JWT_SECRET_KEY is set")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"osool-field-enc-v1",  # Static salt — deterministic derivation
        iterations=100_000,
    )
    derived = base64.urlsafe_b64encode(kdf.derive(jwt_secret.encode()))
    return Fernet(derived)


def encrypt_field(plaintext: str | None) -> str | None:
    """Encrypt a string field. Returns None if input is None."""
    if plaintext is None:
        return None
    try:
        f = _get_fernet()
        return f.encrypt(plaintext.encode("utf-8")).decode("ascii")
    except Exception as e:
        logger.error("Field encryption failed: %s", e)
        raise


def decrypt_field(ciphertext: str | None) -> str | None:
    """Decrypt a string field. Returns None if input is None.
    If decryption fails (e.g. unencrypted legacy data), returns the original value."""
    if ciphertext is None:
        return None
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken:
        # Legacy unencrypted data — return as-is for backward compatibility
        logger.debug("Field appears unencrypted (legacy data), returning as-is")
        return ciphertext
    except Exception as e:
        logger.error("Field decryption failed: %s", e)
        return ciphertext
