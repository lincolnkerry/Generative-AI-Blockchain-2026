"""Encryption utility for masking records.

Uses Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
Key is loaded from MASKING_ENCRYPTION_KEY environment variable.
If not set, a random key is generated at startup (dev mode).

Usage:
    from agents.masker.crypto import encrypt_field, decrypt_field

    encrypted = encrypt_field("901212-1234567")
    original = decrypt_field(encrypted)
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """Get or create the Fernet instance."""
    key = os.environ.get("MASKING_ENCRYPTION_KEY", "")
    if not key:
        # Dev mode: generate ephemeral key (not persisted)
        key = Fernet.generate_key().decode()
        os.environ["MASKING_ENCRYPTION_KEY"] = key
    else:
        key = key.strip()
    return Fernet(key.encode() if isinstance(key, str) else key)


def generate_key() -> str:
    """Generate a new Fernet key. Returns base64-encoded string."""
    return Fernet.generate_key().decode()


def encrypt_field(plaintext: str) -> str:
    """Encrypt a string field. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str) -> str:
    """Decrypt a string field. Returns original plaintext."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
