from unittest.mock import patch

import pytest

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.notifications.models import Delivery, Notification, OutboxEvent
from apps.notifications.tasks import relay_outbox
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
