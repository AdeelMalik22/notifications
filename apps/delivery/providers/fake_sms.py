"""Deterministic, network-free SMS provider for development and tests."""

from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256

from apps.delivery.providers.base import SMSDeliveryResult, SMSMessage


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(UTC)


class FakeSMSProvider:
    """Accept valid messages locally without logging their recipient or content."""

    def __init__(self, clock: Callable[[], datetime] = utc_now) -> None:
        self.clock = clock

    def send(self, message: SMSMessage) -> SMSDeliveryResult:
        """Return a stable fake provider ID without making a network request."""
        if not message.recipient.strip():
            raise ValueError("SMS recipient is required.")
        if not message.body.strip():
            raise ValueError("SMS body is required.")
        if not message.idempotency_key.strip():
            raise ValueError("SMS idempotency key is required.")

        fingerprint = sha256(
            "\0".join((message.idempotency_key, message.recipient, message.body)).encode(),
        ).hexdigest()[:24]

        return SMSDeliveryResult(
            provider_message_id=f"fake_sms_{fingerprint}",
            accepted_at=self.clock(),
        )
