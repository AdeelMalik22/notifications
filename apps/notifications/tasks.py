from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.delivery.providers.base import SMSMessage
from apps.delivery.providers.fake_sms import FakeSMSProvider
from apps.notifications.models import Delivery, DeliveryAttempt, OutboxEvent


@shared_task(ignore_result=True, name="notificationos.notifications.relay_outbox")  # type: ignore[untyped-decorator]
def relay_outbox(limit: int = 100) -> int:
    published = 0
    for event in OutboxEvent.objects.filter(published_at__isnull=True).select_related("delivery")[
        :limit
    ]:
        with transaction.atomic():
            claimed = OutboxEvent.objects.filter(id=event.id, published_at__isnull=True).update(
                published_at=timezone.now()
            )
            if not claimed:
                continue
            event.delivery.status = "queued"
            event.delivery.save(update_fields=["status"])
        deliver_notification.delay(
            str(event.delivery_id), str(event.business_id), event.delivery.channel
        )
        published += 1
    return published


@shared_task(
    bind=True,
    ignore_result=True,
    name="notificationos.notifications.deliver",
    max_retries=2,
    default_retry_delay=60,
)  # type: ignore[untyped-decorator]
def deliver_notification(self, delivery_id: str, business_id: str, channel: str) -> None:
    delivery = Delivery.objects.get(id=delivery_id, business_id=business_id)
    if delivery.status not in {"queued", "retry_scheduled"}:
        return
    delivery.status = "processing"
    delivery.save(update_fields=["status"])
    attempt_number = delivery.attempts.count() + 1
    try:
        recipient = delivery.notification.recipient
        snapshot = delivery.template_snapshot
        variables = delivery.notification.payload.get("variables", {})
        body = snapshot["body"]
        for name, value in variables.items():
            body = body.replace("{{" + name + "}}", str(value)).replace(
                "{{ " + name + " }}", str(value)
            )
        if channel == "email":
            send_mail(snapshot.get("subject", "Notification"), body, None, [recipient.email])
            provider_id = "smtp-accepted"
        elif channel == "sms":
            result = FakeSMSProvider().send(
                SMSMessage(recipient.phone_number, body, str(delivery.id))
            )
            provider_id = result.provider_message_id
        else:
            raise ValueError("Unsupported delivery channel.")
    except ValueError as error:
        DeliveryAttempt.objects.create(
            delivery=delivery,
            attempt_number=attempt_number,
            status="failed",
            error_class=error.__class__.__name__,
        )
        delivery.status = "failed"
        delivery.save(update_fields=["status"])
        return
    except Exception as error:  # transient provider errors are retried twice
        DeliveryAttempt.objects.create(
            delivery=delivery,
            attempt_number=attempt_number,
            status="retry_scheduled",
            error_class=error.__class__.__name__,
        )
        delivery.status = "retry_scheduled"
        delivery.next_attempt_at = timezone.now() + timedelta(seconds=60)
        delivery.save(update_fields=["status", "next_attempt_at"])
        raise self.retry(exc=error, countdown=60) from error
    DeliveryAttempt.objects.create(
        delivery=delivery,
        attempt_number=attempt_number,
        status="sent",
        provider_message_id=provider_id,
    )
    delivery.status = "sent"
    delivery.save(update_fields=["status"])
