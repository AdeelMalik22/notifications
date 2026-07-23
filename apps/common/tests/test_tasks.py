"""Celery configuration and task discovery tests."""

from django.conf import settings

from apps.common.tasks import health_ping


def test_health_ping_is_deterministic() -> None:
    assert health_ping.run() == "pong"


def test_celery_accepts_json_only() -> None:
    assert settings.CELERY_ACCEPT_CONTENT == ["json"]
    assert settings.CELERY_TASK_SERIALIZER == "json"
    assert settings.CELERY_RESULT_BACKEND is None
