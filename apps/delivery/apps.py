"""Application configuration for delivery primitives."""

from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    """Configure provider adapters and future delivery models."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.delivery"
