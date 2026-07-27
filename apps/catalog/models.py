import uuid

from django.core.exceptions import ValidationError
from django.db import models

from apps.tenancy.models import Business


class Channel(models.TextChoices):
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"


class NotificationCategory(models.Model):
    class Policy(models.TextChoices):
        TRANSACTIONAL = "transactional", "Transactional"
        MARKETING = "marketing", "Marketing"
        MANDATORY = "mandatory", "Mandatory"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="categories")
    key = models.SlugField(max_length=80)
    name = models.CharField(max_length=200)
    policy = models.CharField(max_length=20, choices=Policy.choices, default=Policy.TRANSACTIONAL)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business", "key"], name="category_business_key")
        ]

    def __str__(self) -> str:
        return self.key


class EventType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="event_types")
    key = models.CharField(max_length=120)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        NotificationCategory, on_delete=models.PROTECT, related_name="event_types"
    )
    variable_schema = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["business", "key"], name="event_business_key")
        ]

    def __str__(self) -> str:
        return self.key

    def clean(self):
        if self.category.business_id != self.business_id:
            raise ValidationError("Category must belong to the same business.")


class Template(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="templates")
    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT, related_name="templates")
    channel = models.CharField(max_length=10, choices=Channel.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "event_type", "channel"], name="template_business_event_channel"
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_type.key}:{self.channel}"

    def clean(self):
        if self.event_type.business_id != self.business_id:
            raise ValidationError("Event type must belong to the same business.")


class TemplateVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    template = models.ForeignKey(Template, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    subject = models.CharField(max_length=998, blank=True)
    body = models.TextField()
    html_body = models.TextField(blank=True)
    variables = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(fields=["template", "version"], name="template_version_number")
        ]

    def __str__(self) -> str:
        return f"{self.template} v{self.version}"

    def save(self, *args, **kwargs):
        if (
            self.pk
            and TemplateVersion.objects.filter(pk=self.pk).exclude(status=self.status).exists()
        ):
            raise ValidationError("Template versions cannot change after creation.")
        super().save(*args, **kwargs)
