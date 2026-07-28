"""HTTP middleware shared across NotificationOS APIs."""

import logging
import re
from collections.abc import Callable
from time import monotonic
from uuid import uuid4

from django.http import HttpRequest, HttpResponseBase

from apps.common.context import bind_request_id, reset_request_id
from apps.health.metrics import increment

logger = logging.getLogger("notificationos.request")

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_META_KEY = "HTTP_X_REQUEST_ID"
VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def normalize_request_id(candidate: str | None) -> str:
    """Return a safe caller ID or generate a UUID when it is missing or invalid."""
    if candidate and VALID_REQUEST_ID.fullmatch(candidate):
        return candidate
    return str(uuid4())


class RequestIDMiddleware:
    """Bind, log, and echo a safe request ID for every HTTP request."""

    sync_capable = True
    async_capable = False

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        request_id = normalize_request_id(request.META.get(REQUEST_ID_META_KEY))
        context_token = bind_request_id(request_id)
        started_at = monotonic()

        try:
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = request_id
            increment(
                "notificationos_http_requests_total",
                {"method": request.method or "-", "status": str(response.status_code)},
            )
            if response.status_code >= 500:
                increment("notificationos_http_errors_total")
            logger.info(
                "request_completed",
                extra={
                    "duration_ms": round((monotonic() - started_at) * 1000, 2),
                    "http_method": request.method,
                    "http_path": request.path,
                    "status_code": response.status_code,
                },
            )
            return response
        finally:
            reset_request_id(context_token)
