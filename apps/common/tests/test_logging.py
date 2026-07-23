"""Structured logging tests."""

import json
import logging

from apps.common.context import bind_request_id, reset_request_id
from apps.common.logging import JSONFormatter, RequestContextFilter


def test_json_formatter_emits_safe_context() -> None:
    context_token = bind_request_id("request-safe-123")
    try:
        record = logging.LogRecord(
            name="notificationos.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="request_completed",
            args=(),
            exc_info=None,
        )
        record.http_method = "GET"
        record.http_path = "/health/live"
        record.status_code = 200
        RequestContextFilter().filter(record)

        payload = json.loads(JSONFormatter().format(record))
    finally:
        reset_request_id(context_token)

    assert payload["message"] == "request_completed"
    assert payload["request_id"] == "request-safe-123"
    assert payload["http_method"] == "GET"
    assert payload["http_path"] == "/health/live"
    assert payload["status_code"] == 200
    assert "args" not in payload


def test_json_formatter_does_not_serialize_unknown_extras() -> None:
    record = logging.LogRecord(
        name="notificationos.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="safe_event",
        args=(),
        exc_info=None,
    )
    record.recipient_email = "private@example.test"
    RequestContextFilter().filter(record)

    payload = json.loads(JSONFormatter().format(record))

    assert "recipient_email" not in payload
    assert "private@example.test" not in json.dumps(payload)
