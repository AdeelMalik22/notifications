import pytest
from django.utils import timezone

from apps.tenancy.models import APIKey
from apps.tenancy.services import authenticate_key, create_api_key, create_business, revoke_api_key

pytestmark = pytest.mark.django_db


def test_api_key_secret_is_returned_once_and_not_stored() -> None:
    business = create_business("Acme")
    key, plaintext = create_api_key(business, "worker", [APIKey.Scope.NOTIFICATIONS_WRITE])

    assert plaintext.startswith("nos_")
    assert key.secret_digest not in plaintext
    assert authenticate_key(plaintext) == key


def test_revoked_and_expired_keys_cannot_authenticate() -> None:
    business = create_business("Acme")
    key, plaintext = create_api_key(business, "temporary", [APIKey.Scope.API_KEYS_READ])
    revoke_api_key(key)
    assert authenticate_key(plaintext) is None

    key.revoked_at = None
    key.expires_at = timezone.now()
    key.save(update_fields=["revoked_at", "expires_at"])
    assert authenticate_key(plaintext) is None
