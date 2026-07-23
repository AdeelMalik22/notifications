"""ASGI config for NotificationOS."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notifications.settings.local")

application = get_asgi_application()
