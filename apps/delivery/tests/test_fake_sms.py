"""Fake SMS provider contract tests."""

import logging
from datetime import UTC, datetime

import pytest

from apps.delivery.providers.base import SMSMessage
from apps.delivery.providers.fake_sms import FakeSMSProvider

FIXED_TIME = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)


def make_message(**overrides: str) -> SMSMessage:
    values = {
        "recipient": "+15555550123",
        "body": "Your test notification is ready.",
        "idempotency_key": "delivery-attempt-123",
    }
    values.update(overrides)
    return SMSMessage(**values)


def test_fake_sms_returns_deterministic_acceptance() -> None:
    provider = FakeSMSProvider(clock=lambda: FIXED_TIME)

    first = provider.send(make_message())
    second = provider.send(make_message())

    assert first == second
    assert first.status == "accepted"
    assert first.provider_message_id.startswith("fake_sms_")
    assert first.accepted_at == FIXED_TIME


def test_fake_sms_changes_id_for_different_delivery() -> None:
    provider = FakeSMSProvider(clock=lambda: FIXED_TIME)

    first = provider.send(make_message())
    second = provider.send(make_message(idempotency_key="delivery-attempt-456"))

    assert first.provider_message_id != second.provider_message_id


@pytest.mark.parametrize("field", ["recipient", "body", "idempotency_key"])
def test_fake_sms_rejects_missing_required_value(field: str) -> None:
    provider = FakeSMSProvider(clock=lambda: FIXED_TIME)

    with pytest.raises(ValueError, match="required"):
        provider.send(make_message(**{field: " "}))


def test_fake_sms_does_not_log_recipient_or_body(caplog: pytest.LogCaptureFixture) -> None:
    provider = FakeSMSProvider(clock=lambda: FIXED_TIME)

    with caplog.at_level(logging.DEBUG):
        provider.send(make_message())

    assert "+15555550123" not in caplog.text
    assert "Your test notification is ready." not in caplog.text
