"""Provider-neutral SMS delivery types."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class SMSMessage:
    """The minimum data an SMS provider needs for one attempt."""

    recipient: str
    body: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class SMSDeliveryResult:
    """A provider's accepted response."""

    provider_message_id: str
    accepted_at: datetime
    status: Literal["accepted"] = "accepted"


class SMSProvider(Protocol):
    """Contract implemented by every SMS provider adapter."""

    def send(self, message: SMSMessage) -> SMSDeliveryResult:
        """Submit one SMS message and return the provider acceptance."""
        ...
