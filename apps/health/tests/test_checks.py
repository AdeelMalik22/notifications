"""Readiness dependency-check tests."""

from unittest.mock import Mock, patch

from apps.health.checks import run_readiness_checks


def test_readiness_runs_every_check() -> None:
    database_check = Mock()
    cache_check = Mock()

    with patch(
        "apps.health.checks.READINESS_CHECKS",
        (("database", database_check), ("cache", cache_check)),
    ):
        results = run_readiness_checks()

    assert results == {"database": "ok", "cache": "ok"}
    database_check.assert_called_once_with()
    cache_check.assert_called_once_with()


def test_readiness_converts_failures_to_safe_status() -> None:
    failing_check = Mock(side_effect=ConnectionError("contains-sensitive-host"))
    passing_check = Mock()

    with patch(
        "apps.health.checks.READINESS_CHECKS",
        (("database", failing_check), ("cache", passing_check)),
    ):
        results = run_readiness_checks()

    assert results == {"database": "failed", "cache": "ok"}
    assert "contains-sensitive-host" not in str(results)
