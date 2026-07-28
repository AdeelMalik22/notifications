import pytest
from rest_framework.test import APIClient

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.notifications.models import Delivery, Notification, OutboxEvent
from apps.recipients.models import Recipient
from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def test_trigger_creates_transactional_records_and_deduplicates() -> None:
    business = create_business("Acme")
    category = NotificationCategory.objects.create(business=business, key="orders", name="Orders")
    event = EventType.objects.create(
        business=business,
        key="order.shipped",
        name="Shipped",
        category=category,
        variable_schema=["name"],
    )
    template = Template.objects.create(business=business, event_type=event, channel="email")
    TemplateVersion.objects.create(
        template=template, version=1, status="published", body="Hi {{name}}", variables=["name"]
    )
    recipient = Recipient.objects.create(
        business=business, external_id="user-1", email="user@example.test"
    )
    _, secret = create_api_key(business, "sender", [APIKey.Scope.NOTIFICATIONS_WRITE])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")
    payload = {
        "event_type": "order.shipped",
        "recipient_id": str(recipient.id),
        "variables": {"name": "Ada"},
    }

    first = client.post(
        "/api/v1/notifications/", payload, format="json", HTTP_IDEMPOTENCY_KEY="order-1"
    )
    duplicate = client.post(
        "/api/v1/notifications/", payload, format="json", HTTP_IDEMPOTENCY_KEY="order-1"
    )

    assert first.status_code == 202
    assert duplicate.status_code == 200
    assert first.json()["notification_id"] == duplicate.json()["notification_id"]
    assert (
        Notification.objects.count() == Delivery.objects.count() == OutboxEvent.objects.count() == 1
    )


def test_trigger_rejects_idempotency_conflict() -> None:
    business = create_business("Acme")
    recipient = Recipient.objects.create(business=business, external_id="user-1")
    _, secret = create_api_key(business, "sender", [APIKey.Scope.NOTIFICATIONS_WRITE])
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")
    base = {"event_type": "one", "recipient_id": str(recipient.id), "variables": {}}
    assert (
        client.post(
            "/api/v1/notifications/", base, format="json", HTTP_IDEMPOTENCY_KEY="same"
        ).status_code
        == 202
    )
    changed = {**base, "event_type": "two"}
    assert (
        client.post(
            "/api/v1/notifications/", changed, format="json", HTTP_IDEMPOTENCY_KEY="same"
        ).status_code
        == 409
    )
