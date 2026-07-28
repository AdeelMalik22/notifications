from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Delivery, OutboxEvent


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


@shared_task(ignore_result=True, name="notificationos.notifications.deliver")  # type: ignore[untyped-decorator]
def deliver_notification(delivery_id: str, business_id: str, channel: str) -> None:
    delivery = Delivery.objects.get(id=delivery_id, business_id=business_id)
    if delivery.status != "queued":
        return
    # Provider execution is intentionally a later channel-specific slice.
    delivery.status = "processing"
    delivery.save(update_fields=["status"])
