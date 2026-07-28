"""Small, dependency-free Prometheus metrics for the web process."""

from threading import Lock

_lock = Lock()
_counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}


def increment(name: str, labels: dict[str, str] | None = None) -> None:
    """Increment a bounded counter kept local to the current process."""
    normalized = tuple(sorted((labels or {}).items()))
    with _lock:
        key = (name, normalized)
        _counters[key] = _counters.get(key, 0) + 1


def render() -> str:
    """Render counters in Prometheus exposition format."""
    with _lock:
        items = sorted(_counters.items())
    lines = [
        "# HELP notificationos_http_requests_total HTTP requests handled.",
        "# TYPE notificationos_http_requests_total counter",
        "# HELP notificationos_http_errors_total HTTP 5xx responses.",
        "# TYPE notificationos_http_errors_total counter",
        "# HELP notificationos_readiness_failures_total Readiness check failures.",
        "# TYPE notificationos_readiness_failures_total counter",
    ]
    for (name, labels), value in items:
        label_text = ""
        if labels:
            label_text = "{" + ",".join(f'{key}="{value}"' for key, value in labels) + "}"
        lines.append(f"{name}{label_text} {value}")
    return "\n".join(lines) + "\n"


def reset() -> None:
    """Clear counters for isolated tests."""
    with _lock:
        _counters.clear()
