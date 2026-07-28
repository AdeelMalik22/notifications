"""Cross-boundary API and worker integration contracts."""

from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.notifications.models import Delivery, Notification, OutboxEvent
from apps.notifications.tasks import deliver_notification, relay_outbox
from apps.recipients.models import Recipient
from apps.tenancy.models import APIKey, Business
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def _notification_fixture(name: str = "Acme") -> tuple[Business, Recipient, str]:
    business = create_business(name)
    category = NotificationCategory.objects.create(business=business, key="orders", name="Orders")
    event = EventType.objects.create(
        business=business, key="order.shipped", name="Shipped", category=category
    )
    template = Template.objects.create(business=business, event_type=event, channel="email")
    TemplateVersion.objects.create(
        template=template, version=1, status="published", subject="Shipped", body="Hello {{name}}"
    )
    recipient = Recipient.objects.create(
        business=business, external_id="user-1", email="user@example.test"
    )
    _, secret = create_api_key(business, "sender", [APIKey.Scope.NOTIFICATIONS_WRITE])
    return business, recipient, secret


def test_notification_history_is_tenant_isolated() -> None:
    first, recipient, first_secret = _notification_fixture("First")
    _, _, second_secret = _notification_fixture("Second")
    first_client = APIClient()
    first_client.credentials(HTTP_AUTHORIZATION=f"Bearer {first_secret}")
    response = first_client.post(
        "/api/v1/notifications/",
        {
            "event_type": "order.shipped",
            "recipient_id": str(recipient.id),
            "variables": {"name": "Ada"},
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY="integration-1",
    )
    notification_id = response.json()["notification_id"]

    second_client = APIClient()
    second_client.credentials(HTTP_AUTHORIZATION=f"Bearer {second_secret}")
    assert second_client.get("/api/v1/notifications/history/").json() == []
    assert second_client.get(f"/api/v1/notifications/{notification_id}/").status_code == 404
    assert Notification.objects.filter(business=first).count() == 1


def test_end_to_end_trigger_relay_and_email_worker() -> None:
    business, recipient, secret = _notification_fixture()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")

    with patch("apps.notifications.tasks.deliver_notification.delay") as enqueue:
        response = client.post(
            "/api/v1/notifications/",
            {
                "event_type": "order.shipped",
                "recipient_id": str(recipient.id),
                "variables": {"name": "Ada"},
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="integration-2",
        )
        assert response.status_code == 202
        assert relay_outbox() == 1

    delivery = Delivery.objects.get(notification__business=business)
    enqueue.assert_called_once_with(str(delivery.id), str(business.id), "email")
    with patch("apps.notifications.tasks.send_mail") as send_mail:
        deliver_notification(str(delivery.id), str(business.id), "email")

    delivery.refresh_from_db()
    assert delivery.status == Delivery.Status.SENT
    send_mail.assert_called_once()
    assert OutboxEvent.objects.get(delivery=delivery).published_at is not None
