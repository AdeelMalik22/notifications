import pytest
from rest_framework.test import APIClient

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
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


def test_template_version_can_be_published_and_previewed() -> None:
    business = create_business("Acme")
    category = NotificationCategory.objects.create(business=business, key="orders", name="Orders")
    event = EventType.objects.create(
        business=business,
        key="order.shipped",
        name="Order shipped",
        category=category,
        variable_schema=["customer_name"],
    )
    template = Template.objects.create(business=business, event_type=event, channel="email")
    version = TemplateVersion.objects.create(
        template=template,
        version=1,
        body="Hello {{ customer_name }}",
        variables=["customer_name"],
    )
    client = auth_client(business)

    response = client.post(f"/api/v1/template-versions/{version.id}/publish/")
    assert response.status_code == 200
    assert response.json()["status"] == "published"

    response = client.post(
        f"/api/v1/template-versions/{version.id}/preview/",
        {"variables": {"customer_name": "Ada"}},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["body"] == "Hello Ada"
