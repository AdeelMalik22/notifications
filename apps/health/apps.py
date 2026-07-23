"""Application configuration for health endpoints."""

from django.apps import AppConfig


class HealthConfig(AppConfig):
    """Configure dependency health checks."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.health"
