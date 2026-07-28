from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.delivery.errors import AmbiguousProviderError, PermanentProviderError
from apps.delivery.models import ProviderConfiguration
from apps.delivery.providers.base import SMSMessage
from apps.delivery.providers.fake_sms import FakeSMSProvider
from apps.delivery.providers.twilio_sms import TwilioSMSProvider
from apps.delivery.services import load_provider_credentials
from apps.notifications.models import Delivery, DeliveryAttempt, Notification, OutboxEvent
from apps.notifications.services import refresh_notification_status
from apps.recipients.models import Recipient


@shared_task(ignore_result=True, name="notificationos.notifications.relay_outbox")  # type: ignore[untyped-decorator]
def relay_outbox(limit: int = 100) -> int:
    published = 0
    tenants = list(
        OutboxEvent.objects.filter(published_at__isnull=True)
        .values_list("business_id", flat=True)
        .distinct()
    )
    index = 0
    while published < limit and tenants:
        business_id = tenants[index % len(tenants)]
        event = (
            OutboxEvent.objects.filter(business_id=business_id, published_at__isnull=True)
            .select_related("delivery")
            .first()
        )
        index += 1
        if event is None:
            tenants.remove(business_id)
            continue
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
            provider_configuration = ProviderConfiguration.objects.get(
                business_id=business_id, channel="sms", is_active=True
            )
            if provider_configuration.provider_name == "twilio":
                credentials = load_provider_credentials(provider_configuration)
                provider = TwilioSMSProvider(
                    account_sid=credentials["account_sid"],
                    auth_token=credentials["auth_token"],
                    from_number=credentials["from_number"],
                    base_url=credentials.get("base_url", "https://api.twilio.com/2010-04-01"),
                    timeout=float(credentials.get("timeout", "5.0")),
                )
            else:
                provider = FakeSMSProvider()
            result = provider.send(SMSMessage(recipient.phone_number, body, str(delivery.id)))
            provider_id = result.provider_message_id
        else:
            raise PermanentProviderError("Unsupported delivery channel.")
    except (ValueError, PermanentProviderError) as error:
        DeliveryAttempt.objects.create(
            delivery=delivery,
            attempt_number=attempt_number,
            status="failed",
            error_class=error.__class__.__name__,
        )
        delivery.status = "failed"
        delivery.save(update_fields=["status"])
        refresh_notification_status(delivery.notification)
        return
    except Exception as error:  # transient provider errors are retried twice
        if isinstance(error, AmbiguousProviderError):
            DeliveryAttempt.objects.create(
                delivery=delivery,
                attempt_number=attempt_number,
                status="unknown",
                error_class=error.__class__.__name__,
            )
            delivery.status = "unknown"
            delivery.save(update_fields=["status"])
            refresh_notification_status(delivery.notification)
            return
        if self.request.retries >= 2:
            DeliveryAttempt.objects.create(
                delivery=delivery,
                attempt_number=attempt_number,
                status="dead_lettered",
                error_class=error.__class__.__name__,
            )
            delivery.status = "failed"
            delivery.dead_lettered_at = timezone.now()
            delivery.save(update_fields=["status", "dead_lettered_at"])
            refresh_notification_status(delivery.notification)
            return
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
    refresh_notification_status(delivery.notification)


@shared_task(ignore_result=True, name="notificationos.notifications.reconcile_unknown")  # type: ignore[untyped-decorator]
def reconcile_unknown_deliveries() -> int:
    """Leave ambiguous outcomes visible for provider-specific reconciliation."""
    return Delivery.objects.filter(status="unknown").count()


@shared_task(ignore_result=True, name="notificationos.notifications.run_retention")  # type: ignore[untyped-decorator]
def run_retention() -> dict[str, int]:
    """Remove retained content while preserving non-PII delivery metadata."""
    content_cutoff = timezone.now() - timedelta(days=settings.NOTIFICATION_CONTENT_RETENTION_DAYS)
    metadata_cutoff = timezone.now() - timedelta(days=settings.NOTIFICATION_METADATA_RETENTION_DAYS)
    content_rows = Notification.objects.filter(created_at__lt=content_cutoff).exclude(payload={})
    content_count = content_rows.update(payload={})
    Delivery.objects.filter(created_at__lt=content_cutoff).exclude(template_snapshot={}).update(
        template_snapshot={}
    )
    recipient_ids = (
        Recipient.objects.filter(is_active=True, notification__created_at__lt=metadata_cutoff)
        .values_list("id", flat=True)
        .distinct()
    )
    recipient_count = Recipient.objects.filter(id__in=recipient_ids).update(
        email="", phone_number="", is_active=False
    )
    return {"notifications_cleared": content_count, "recipients_anonymized": recipient_count}
