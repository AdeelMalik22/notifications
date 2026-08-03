"""Acceptance, failure-injection, and security boundary coverage."""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from django.db import connection, connections
from rest_framework.test import APIClient

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.notifications.models import Delivery, Notification
from apps.notifications.tasks import deliver_notification
from apps.recipients.models import Recipient
from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def _fixture(name: str = "Acme"):
    business = create_business(name)
    category = NotificationCategory.objects.create(business=business, key="ops", name="Ops")
    event = EventType.objects.create(business=business, key="alert", name="Alert", category=category)
    template = Template.objects.create(business=business, event_type=event, channel="email")
    TemplateVersion.objects.create(template=template, version=1, status="published", body="{{x}}")
    recipient = Recipient.objects.create(business=business, external_id="user", email="u@example.test")
    _, secret = create_api_key(business, "sender", [APIKey.Scope.NOTIFICATIONS_WRITE])
    return business, recipient, secret


def test_cross_tenant_trigger_cannot_use_foreign_recipient() -> None:
    _, recipient, secret = _fixture("Tenant A")
    _, _, other_secret = _fixture("Tenant B")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_secret}")

    response = client.post(
        "/api/v1/notifications/",
        {"event_type": "alert", "recipient_id": str(recipient.id), "variables": {"x": "safe"}},
        format="json",
        HTTP_IDEMPOTENCY_KEY="foreign-recipient",
    )

    assert response.status_code == 404, response.data
    assert Notification.objects.count() == 0
    assert secret != other_secret


def test_payload_and_idempotency_limits_are_rejected(settings) -> None:
    _, recipient, secret = _fixture()
    settings.NOTIFICATION_MAX_PAYLOAD_BYTES = 32
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")

    oversized = client.post(
        "/api/v1/notifications/",
        {"event_type": "alert", "recipient_id": str(recipient.id), "variables": {"x": "x" * 100}},
        format="json",
        HTTP_IDEMPOTENCY_KEY="payload-limit",
    )
    long_key = client.post(
        "/api/v1/notifications/",
        {"event_type": "alert", "recipient_id": str(recipient.id), "variables": {}},
        format="json",
        HTTP_IDEMPOTENCY_KEY="k" * 256,
    )

    assert oversized.status_code == 400
    assert long_key.status_code == 400


def test_permanent_provider_failure_is_recorded_without_retry() -> None:
    business, recipient, _ = _fixture()
    notification = Notification.objects.create(
        business=business,
        event_type="alert",
        recipient=recipient,
        idempotency_key="failure-injection",
        request_fingerprint="f" * 64,
        status="accepted",
        payload={"variables": {"x": "bad"}},
    )
    delivery = Delivery.objects.create(
        business=business,
        notification=notification,
        channel="email",
        status="queued",
        template_snapshot={"body": "bad"},
    )

    with patch("apps.notifications.tasks.send_mail", side_effect=ValueError("provider rejected")):
        deliver_notification(str(delivery.id), str(business.id), "email")

    delivery.refresh_from_db()
    assert delivery.status == Delivery.Status.FAILED
    assert delivery.attempts.count() == 1
    assert delivery.attempts.get().error_class == "ValueError"


@pytest.mark.skipif(connection.vendor != "postgresql", reason="requires PostgreSQL row locking")
def test_concurrent_identical_triggers_create_one_notification() -> None:
    _, recipient, secret = _fixture("Concurrency")
    payload = {"event_type": "alert", "recipient_id": str(recipient.id), "variables": {"x": "same"}}

    def send_once(_: int) -> int:
        connections.close_all()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")
        response = client.post(
            "/api/v1/notifications/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="concurrent-key",
        )
        connections.close_all()
        return response.status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(send_once, range(8)))

    assert statuses.count(202) == 1
    assert all(status in {202, 200} for status in statuses)
    assert Notification.objects.filter(idempotency_key="concurrent-key").count() == 1
