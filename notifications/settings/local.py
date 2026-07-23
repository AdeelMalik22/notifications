# ruff: noqa: F403
"""Local development settings."""

from notifications.settings.base import *
from notifications.settings.base import ALLOWED_HOSTS as BASE_ALLOWED_HOSTS
from notifications.settings.base import REST_FRAMEWORK as BASE_REST_FRAMEWORK

DEBUG = True

ALLOWED_HOSTS = BASE_ALLOWED_HOSTS or ["localhost", "127.0.0.1", "0.0.0.0"]

REST_FRAMEWORK = {
    **BASE_REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": [
        *BASE_REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}
