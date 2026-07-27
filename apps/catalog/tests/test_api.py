import pytest
from rest_framework.test import APIClient

from apps.catalog.models import NotificationCategory
from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def auth_client(business):
    _, secret = create_api_key(business, "catalog", [APIKey.Scope.CATALOG_WRITE])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")
    return client


def test_catalogue_is_tenant_scoped() -> None:
    first = create_business("First")
    second = create_business("Second")
    NotificationCategory.objects.create(business=second, key="marketing", name="Marketing")

    response = auth_client(first).get("/api/v1/categories/")

    assert response.status_code == 200
    assert response.json() == []


def test_category_creation_does_not_accept_business_from_payload() -> None:
    business = create_business("Acme")
    response = auth_client(business).post(
        "/api/v1/categories/",
        {
            "business": "not-the-tenant",
            "key": "security",
            "name": "Security",
            "policy": "mandatory",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["policy"] == NotificationCategory.Policy.MANDATORY
