"""Request-ID middleware contract tests."""

from uuid import UUID

from django.urls import reverse
from rest_framework.test import APIClient

from apps.common.context import get_request_id


def test_request_id_is_generated_and_returned() -> None:
    response = APIClient().get(reverse("health:live"))

    request_id = response.headers["X-Request-ID"]
    assert str(UUID(request_id)) == request_id
    assert get_request_id() is None


def test_valid_caller_request_id_is_echoed() -> None:
    response = APIClient().get(
        reverse("health:live"),
        headers={"X-Request-ID": "customer-request_123"},
    )

    assert response.headers["X-Request-ID"] == "customer-request_123"


def test_invalid_or_oversized_request_id_is_replaced() -> None:
    response = APIClient().get(
        reverse("health:live"),
        headers={"X-Request-ID": "invalid request id" * 20},
    )

    request_id = response.headers["X-Request-ID"]
    assert request_id != "invalid request id" * 20
    assert str(UUID(request_id)) == request_id
