"""Encryption and keyed lookup helpers for recipient contact data."""

import hashlib
import hmac

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    key = settings.CONTACT_ENCRYPTION_KEY
    if not key:
        raise ValueError("CONTACT_ENCRYPTION_KEY must be configured before storing contacts.")
    return Fernet(key.encode() if isinstance(key, str) else key)


def _lookup_key() -> bytes:
    key = settings.CONTACT_LOOKUP_KEY
    if not key:
        raise ValueError("CONTACT_LOOKUP_KEY must be configured before storing contacts.")
    return key.encode() if isinstance(key, str) else key


def encrypt_contact(value: str) -> bytes:
    return _fernet().encrypt(value.encode())


def decrypt_contact(value: bytes | memoryview | None) -> str:
    if not value:
        return ""
    return _fernet().decrypt(bytes(value)).decode()


def contact_lookup(value: str) -> str:
    return hmac.new(_lookup_key(), value.strip().lower().encode(), hashlib.sha256).hexdigest()
