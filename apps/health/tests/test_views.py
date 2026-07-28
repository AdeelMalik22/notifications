"""Health endpoint contract tests."""

from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def test_liveness_returns_ok_without_dependency_checks() -> None:
    client = APIClient()

    with patch("apps.health.views.run_readiness_checks") as readiness_checks:
        response = client.get(reverse("health:live"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}
    readiness_checks.assert_not_called()


def test_readiness_returns_ok_when_dependencies_are_available() -> None:
    client = APIClient()

    with patch(
        "apps.health.views.run_readiness_checks",
        return_value={"database": "ok", "cache": "ok"},
    ):
        response = client.get(reverse("health:ready"))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "cache": "ok"},
    }


def test_readiness_returns_safe_503_when_a_dependency_fails() -> None:
    client = APIClient()

    with patch(
        "apps.health.views.run_readiness_checks",
        return_value={"database": "failed", "cache": "ok"},
    ):
        response = client.get(reverse("health:ready"))

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        "status": "unavailable",
        "checks": {"database": "failed", "cache": "ok"},
    }


def test_metrics_exposes_prometheus_counters() -> None:
    from apps.health.metrics import increment, reset

    reset()
    increment("notificationos_http_requests_total", {"method": "GET", "status": "200"})

    response = APIClient().get(reverse("health:metrics"))

    assert response.status_code == status.HTTP_200_OK
    assert b"notificationos_http_requests_total" in response.content
    reset()
