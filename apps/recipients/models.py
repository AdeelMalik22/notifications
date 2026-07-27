import uuid

from django.db import models

from apps.catalog.models import Channel, NotificationCategory
from apps.tenancy.models import Business


class Recipient(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="recipients")
    external_id = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "external_id"], name="recipient_business_external"
            )
        ]

    def __str__(self) -> str:
        return self.external_id


class Preference(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="preferences")
    recipient = models.ForeignKey(Recipient, on_delete=models.PROTECT, related_name="preferences")
    category = models.ForeignKey(
        NotificationCategory, on_delete=models.PROTECT, related_name="preferences"
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    enabled = models.BooleanField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "recipient", "category", "channel"],
                name="preference_business_recipient_category_channel",
            )
        ]

    def __str__(self) -> str:
        return f"{self.recipient}:{self.category}:{self.channel}"
