import pytest
from rest_framework.test import APIClient

from apps.catalog.models import NotificationCategory
from apps.recipients.models import Recipient
from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def test_recipient_and_preference_are_tenant_scoped() -> None:
    business = create_business("Acme")
    _, secret = create_api_key(business, "recipients", [APIKey.Scope.CATALOG_WRITE])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")
    recipient_response = client.post(
        "/api/v1/recipients/",
        {"external_id": "user-1", "email": "user@example.test"},
        format="json",
    )
    category = NotificationCategory.objects.create(business=business, key="product", name="Product")

    response = client.post(
        "/api/v1/preferences/",
        {
            "recipient": recipient_response.json()["id"],
            "category": str(category.id),
            "channel": "email",
            "enabled": False,
        },
        format="json",
    )

    assert recipient_response.status_code == 201
    assert response.status_code == 201
    assert Recipient.objects.get(external_id="user-1").business_id == business.id


def test_mandatory_category_cannot_be_disabled() -> None:
    business = create_business("Acme")
    _, secret = create_api_key(business, "recipients", [APIKey.Scope.CATALOG_WRITE])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")
    recipient = Recipient.objects.create(business=business, external_id="user-1")
    category = NotificationCategory.objects.create(
        business=business, key="security", name="Security", policy="mandatory"
    )

    response = client.post(
        "/api/v1/preferences/",
        {
            "recipient": str(recipient.id),
            "category": str(category.id),
            "channel": "email",
            "enabled": False,
        },
        format="json",
    )

    assert response.status_code == 400
