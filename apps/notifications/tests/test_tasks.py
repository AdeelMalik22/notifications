from unittest.mock import patch

import pytest

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.notifications.models import Delivery, Notification, OutboxEvent
from apps.notifications.tasks import reconcile_unknown_deliveries, relay_outbox, run_retention
from apps.recipients.models import Recipient
from apps.tenancy.services import create_business

pytestmark = pytest.mark.django_db


def test_relay_publishes_each_outbox_event_once() -> None:
    business = create_business("Acme")
    category = NotificationCategory.objects.create(business=business, key="orders", name="Orders")
    event_type = EventType.objects.create(
        business=business, key="order.shipped", name="Shipped", category=category
    )
    template = Template.objects.create(business=business, event_type=event_type, channel="email")
    version = TemplateVersion.objects.create(
        template=template, version=1, status="published", body="Hi"
    )
    recipient = Recipient.objects.create(business=business, external_id="user")
    notification = Notification.objects.create(
        business=business,
        event_type=event_type.key,
        recipient=recipient,
        idempotency_key="one",
        request_fingerprint="a" * 64,
        status="accepted",
        payload={},
    )
    delivery = Delivery.objects.create(
        business=business,
        notification=notification,
        channel="email",
        status="pending",
        template_snapshot={"version_id": str(version.id)},
    )
    OutboxEvent.objects.create(business=business, delivery=delivery)

    with patch("apps.notifications.tasks.deliver_notification.delay") as send:
        assert relay_outbox() == 1
        assert relay_outbox() == 0
    send.assert_called_once_with(str(delivery.id), str(business.id), "email")
    assert OutboxEvent.objects.get().published_at is not None


def test_reconcile_unknown_deliveries_counts_ambiguous_work() -> None:
    assert reconcile_unknown_deliveries() == 0


def test_retention_clears_old_content_and_anonymizes_recipient(settings) -> None:
    from datetime import timedelta

    from django.utils import timezone

    settings.NOTIFICATION_CONTENT_RETENTION_DAYS = 30
    settings.NOTIFICATION_METADATA_RETENTION_DAYS = 90
    business = create_business("Acme")
    recipient = Recipient.objects.create(
        business=business, external_id="old-user", email="old@example.test", phone_number="+1"
    )
    notification = Notification.objects.create(
        business=business,
        event_type="order.shipped",
        recipient=recipient,
        idempotency_key="retention-1",
        request_fingerprint="c" * 64,
        status="accepted",
        payload={"secret": "content"},
    )
    old_timestamp = timezone.now() - timedelta(days=100)
    Notification.objects.filter(id=notification.id).update(created_at=old_timestamp)
    delivery = Delivery.objects.create(
        business=business,
        notification=notification,
        channel="email",
        status="pending",
        template_snapshot={"body": "secret"},
    )
    Delivery.objects.filter(id=delivery.id).update(created_at=old_timestamp)

    result = run_retention()

    notification.refresh_from_db()
    recipient.refresh_from_db()
    assert result["notifications_cleared"] == 1
    assert notification.payload == {}
    assert recipient.email == ""
    assert recipient.phone_number == ""
    assert recipient.is_active is False
