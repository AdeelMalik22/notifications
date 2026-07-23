"""Baseline project configuration tests."""

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse


class ProjectStructureTests(SimpleTestCase):
    """Protect the root-level Django project layout and base configuration."""

    def test_project_package_is_named_notifications(self) -> None:
        assert settings.ROOT_URLCONF == "notifications.urls"
        assert settings.WSGI_APPLICATION == "notifications.wsgi.application"
        assert settings.ASGI_APPLICATION == "notifications.asgi.application"

    def test_openapi_routes_are_registered(self) -> None:
        assert reverse("api-schema") == "/api/schema/"
        assert reverse("api-docs") == "/api/docs/"

    def test_delivery_state_is_not_stored_in_celery(self) -> None:
        assert settings.CELERY_RESULT_BACKEND is None
        assert settings.CELERY_TASK_IGNORE_RESULT is True
