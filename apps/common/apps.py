"""Application configuration for common platform utilities."""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Configure cross-cutting utilities and task discovery."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
