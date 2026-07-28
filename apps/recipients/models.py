import uuid

from django.db import models

from apps.catalog.models import Channel, NotificationCategory
from apps.recipients.privacy import contact_lookup, encrypt_contact
from apps.tenancy.models import Business


class Recipient(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="recipients")
    external_id = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    email_ciphertext = models.BinaryField(blank=True, default=bytes)
    phone_ciphertext = models.BinaryField(blank=True, default=bytes)
    email_lookup = models.CharField(max_length=64, blank=True, editable=False)
    phone_lookup = models.CharField(max_length=64, blank=True, editable=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "external_id"], name="recipient_business_external"
            )
        ]

    def __str__(self) -> str:
        return self.external_id

    def save(self, *args, **kwargs):
        if self.email:
            self.email_ciphertext = encrypt_contact(self.email)
            self.email_lookup = contact_lookup(self.email)
            self.email = ""
        elif not self.email_ciphertext:
            self.email_lookup = ""
        if self.phone_number:
            self.phone_ciphertext = encrypt_contact(self.phone_number)
            self.phone_lookup = contact_lookup(self.phone_number)
            self.phone_number = ""
        elif not self.phone_ciphertext:
            self.phone_lookup = ""
        return super().save(*args, **kwargs)


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
