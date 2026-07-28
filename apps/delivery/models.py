import uuid

from django.db import models

from apps.tenancy.models import Business


class ProviderConfiguration(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="providers")
    channel = models.CharField(max_length=10, choices=Channel.choices)
    provider_name = models.CharField(max_length=80)
    encrypted_credentials = models.BinaryField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "channel"], name="provider_business_channel"
            )
        ]

    def __str__(self) -> str:
        return f"{self.business_id}:{self.channel}:{self.provider_name}"
