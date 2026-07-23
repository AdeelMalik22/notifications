"""NotificationOS Django project."""

from notifications.celery import app as celery_app

__all__ = ("celery_app",)
