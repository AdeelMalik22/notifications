import uuid

from django.db import models

from apps.catalog.models import Channel
from apps.tenancy.models import Business


class Notification(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        SUPPRESSED = "suppressed", "Suppressed"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="notifications")
    event_type = models.CharField(max_length=120)
    recipient = models.ForeignKey("recipients.Recipient", on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=255)
    request_fingerprint = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=Status.choices)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "idempotency_key"], name="notification_business_idempotency"
            )
        ]

    def __str__(self) -> str:
        return str(self.id)


class Delivery(models.Model):
    class Status(models.TextChoices):
        SUPPRESSED = "suppressed", "Suppressed"
        PENDING = "pending", "Pending"
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        RETRY_SCHEDULED = "retry_scheduled", "Retry scheduled"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="deliveries")
    notification = models.ForeignKey(
        Notification, on_delete=models.PROTECT, related_name="deliveries"
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    template_snapshot = models.JSONField(default=dict)
    preference_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "notification", "channel"],
                name="delivery_business_notification_channel",
            )
        ]

    def __str__(self) -> str:
        return str(self.id)


class DeliveryAttempt(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    delivery = models.ForeignKey(Delivery, on_delete=models.PROTECT, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20)
    provider_message_id = models.CharField(max_length=200, blank=True)
    error_class = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["delivery", "attempt_number"], name="delivery_attempt_number"
            )
        ]

    def __str__(self) -> str:
        return f"{self.delivery_id}:{self.attempt_number}"


class OutboxEvent(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT)
    delivery = models.OneToOneField(Delivery, on_delete=models.PROTECT, related_name="outbox_event")
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.id)
