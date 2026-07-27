"""Credential creation and lifecycle operations."""

import hashlib
import hmac
import secrets

from django.conf import settings
from django.utils import timezone

from apps.tenancy.models import APIKey, Business


def _digest(secret: str) -> str:
    key = getattr(settings, "API_KEY_HASH_SECRET", settings.SECRET_KEY).encode()
    return hmac.new(key, secret.encode(), hashlib.sha256).hexdigest()


def create_business(name: str) -> Business:
    return Business.objects.create(name=name, public_id=secrets.token_urlsafe(12))


def create_api_key(
    business: Business, name: str, scopes: list[str], expires_at=None
) -> tuple[APIKey, str]:
    prefix = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:12]
    secret = secrets.token_urlsafe(32)
    key = APIKey.objects.create(
        business=business,
        name=name,
        prefix=prefix,
        secret_digest=_digest(secret),
        scopes=scopes,
        expires_at=expires_at,
    )
    return key, f"nos_{prefix}.{secret}"


def revoke_api_key(api_key: APIKey) -> APIKey:
    api_key.revoked_at = timezone.now()
    api_key.save(update_fields=["revoked_at"])
    return api_key


def authenticate_key(raw_key: str) -> APIKey | None:
    if not raw_key.startswith("nos_") or "." not in raw_key:
        return None
    prefix, secret = raw_key[4:].split(".", 1)
    try:
        key = APIKey.objects.select_related("business").get(prefix=prefix)
    except APIKey.DoesNotExist:
        return None
    if key.is_usable and hmac.compare_digest(key.secret_digest, _digest(secret)):
        key.last_used_at = timezone.now()
        key.save(update_fields=["last_used_at"])
        return key
    return None
