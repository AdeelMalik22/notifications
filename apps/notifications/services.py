import hashlib
import json

from django.db import IntegrityError, transaction

from apps.catalog.models import TemplateVersion
from apps.notifications.models import Delivery, Notification, OutboxEvent
from apps.recipients.models import Preference, Recipient
from apps.tenancy.models import Business


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@transaction.atomic
def trigger_notification(
    business: Business, idempotency_key: str, payload: dict
) -> tuple[Notification, bool]:
    fingerprint = _fingerprint(payload)
    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                business=business,
                event_type=payload["event_type"],
                recipient_id=payload["recipient_id"],
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                status=Notification.Status.ACCEPTED,
                payload=payload,
            )
    except IntegrityError:
        notification = Notification.objects.get(business=business, idempotency_key=idempotency_key)
        if notification.request_fingerprint != fingerprint:
            raise ValueError("Idempotency key was already used with different data.") from None
        return notification, True

    recipient = Recipient.objects.get(id=payload["recipient_id"], business=business, is_active=True)
    versions = TemplateVersion.objects.filter(
        template__business=business,
        template__event_type__key=payload["event_type"],
        status=TemplateVersion.Status.PUBLISHED,
    ).select_related("template")
    for version in versions:
        preference = Preference.objects.filter(
            business=business,
            recipient=recipient,
            category=version.template.event_type.category,
            channel=version.template.channel,
        ).first()
        enabled = (
            preference.enabled
            if preference
            else version.template.event_type.category.policy != "marketing"
        )
        status = Delivery.Status.PENDING if enabled else Delivery.Status.SUPPRESSED
        delivery = Delivery.objects.create(
            business=business,
            notification=notification,
            channel=version.template.channel,
            status=status,
            preference_reason="enabled" if enabled else "preference_suppressed",
            template_snapshot={
                "version_id": str(version.id),
                "subject": version.subject,
                "body": version.body,
                "variables": version.variables,
            },
        )
        if enabled:
            OutboxEvent.objects.create(business=business, delivery=delivery)
    return notification, False
