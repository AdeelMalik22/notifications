"""Safe structured logging primitives."""

import json
import logging
from datetime import UTC, datetime

from apps.common.context import get_request_id

SAFE_EXTRA_FIELDS = (
    "dependency",
    "duration_ms",
    "error_type",
    "http_method",
    "http_path",
    "status_code",
)


class RequestContextFilter(logging.Filter):
    """Attach request context to every emitted record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add a bounded request identifier for the JSON formatter."""
        record.request_id = get_request_id() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """Emit one JSON object per line without serializing request payloads."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a stable, intentionally small set of safe fields."""
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for field in SAFE_EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info and record.exc_info[0]:
            payload["error_type"] = record.exc_info[0].__name__

        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
