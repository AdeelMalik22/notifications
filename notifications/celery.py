"""Celery application for NotificationOS."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notifications.settings.local")

app = Celery("notifications")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
