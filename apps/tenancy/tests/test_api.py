import pytest
from rest_framework.test import APIClient

from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def test_api_key_management_is_tenant_scoped() -> None:
    first = create_business("First")
    second = create_business("Second")
    _, first_secret = create_api_key(
        first, "admin", [APIKey.Scope.API_KEYS_READ, APIKey.Scope.API_KEYS_WRITE]
    )
    second_key, _ = create_api_key(second, "other", [APIKey.Scope.API_KEYS_READ])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {first_secret}")

    response = client.get("/api/v1/api-keys/")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [str(first.api_keys.first().id)]
    assert str(second_key.id) not in response.content.decode()


def test_api_key_creation_returns_secret_once() -> None:
    business = create_business("Acme")
    _, secret = create_api_key(business, "admin", [APIKey.Scope.API_KEYS_WRITE])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")

    response = client.post(
        "/api/v1/api-keys/",
        {"name": "delivery", "scopes": [APIKey.Scope.NOTIFICATIONS_WRITE]},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["secret"].startswith("nos_")
