"""Persistent tenant identity and machine credentials."""

import uuid

from django.db import models


class Business(models.Model):
    """A NotificationOS tenant."""

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=200)
    public_id = models.CharField(max_length=32, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class APIKey(models.Model):
    """A bearer credential; the secret itself is never persisted."""

    class Scope(models.TextChoices):
        API_KEYS_READ = "api_keys:read", "Read API keys"
        API_KEYS_WRITE = "api_keys:write", "Manage API keys"
        NOTIFICATIONS_WRITE = "notifications:write", "Create notifications"
        CATALOG_READ = "catalog:read", "Read catalogue"
        CATALOG_WRITE = "catalog:write", "Manage catalogue"
        PROVIDERS_READ = "providers:read", "Read providers"
        PROVIDERS_WRITE = "providers:write", "Manage providers"

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="api_keys")
    name = models.CharField(max_length=200)
    prefix = models.CharField(max_length=16, unique=True)
    secret_digest = models.CharField(max_length=64)
    scopes = models.JSONField(default=list)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["business", "revoked_at"])]

    def __str__(self) -> str:
        return f"{self.business.name}: {self.name} ({self.prefix})"

    @property
    def is_usable(self) -> bool:
        from django.utils import timezone

        now = timezone.now()
        return self.revoked_at is None and (self.expires_at is None or self.expires_at > now)
