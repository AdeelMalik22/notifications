# ruff: noqa: F403
"""Production settings with fail-closed security defaults."""

from django.core.exceptions import ImproperlyConfigured

from notifications.settings.base import *

DEBUG = False

if SECRET_KEY == INSECURE_SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set in production.")

if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set in production.")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# drf-spectacular cannot infer custom bearer authentication or serializers
# from hand-written APIViews. The schema validation job remains enabled; these
# warnings only prevent deployment checks from failing on discovery hints.
SILENCED_SYSTEM_CHECKS = ["drf_spectacular.W001", "drf_spectacular.W002"]
