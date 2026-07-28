"""Bounded checks for dependencies required by synchronous API requests."""

from collections.abc import Callable
from uuid import uuid4

from django.core.cache import cache
from django.db import connection

from apps.health.metrics import increment

DependencyCheck = Callable[[], None]


def check_database() -> None:
    """Confirm PostgreSQL accepts a trivial query."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        row = cursor.fetchone()

    if row != (1,):
        raise RuntimeError("Database readiness query returned an unexpected result.")


def check_cache() -> None:
    """Confirm Redis supports a short write/read/delete round trip."""
    key = f"health:ready:{uuid4().hex}"
    value = uuid4().hex

    cache.set(key, value, timeout=5)
    try:
        if cache.get(key) != value:
            raise RuntimeError("Cache readiness value did not round-trip.")
    finally:
        cache.delete(key)


READINESS_CHECKS: tuple[tuple[str, DependencyCheck], ...] = (
    ("database", check_database),
    ("cache", check_cache),
)


def run_readiness_checks() -> dict[str, str]:
    """Run every synchronous dependency check without leaking exception details."""
    results: dict[str, str] = {}

    for name, check in READINESS_CHECKS:
        try:
            check()
        except Exception:  # noqa: BLE001 - readiness must convert dependency failures to 503
            results[name] = "failed"
            increment("notificationos_readiness_failures_total", {"dependency": name})
        else:
            results[name] = "ok"

    return results
