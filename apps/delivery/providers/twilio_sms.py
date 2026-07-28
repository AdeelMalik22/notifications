"""Small Twilio-compatible SMS adapter using the provider HTTP API."""

import json
from base64 import b64encode
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from apps.delivery.providers.base import SMSDeliveryResult, SMSMessage


@dataclass(frozen=True, slots=True)
class TwilioSMSProvider:
    account_sid: str
    auth_token: str
    from_number: str
    base_url: str = "https://api.twilio.com/2010-04-01"
    timeout: float = 5.0

    def send(self, message: SMSMessage) -> SMSDeliveryResult:
        if not self.account_sid or not self.auth_token or not self.from_number:
            raise ValueError("Twilio provider credentials are required.")
        if not message.recipient.strip() or not message.body.strip():
            raise ValueError("SMS recipient and body are required.")
        endpoint = f"{self.base_url}/Accounts/{self.account_sid}/Messages.json"
        request = Request(
            endpoint,
            data=urlencode(
                {"To": message.recipient, "From": self.from_number, "Body": message.body}
            ).encode(),
            headers={
                "Authorization": "Basic "
                + b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
            status = response.status
            if status < 200 or status >= 300:
                raise RuntimeError(f"Twilio returned HTTP {status}.")
            provider_id = json.loads(response.read().decode()).get("sid", "")
        if not provider_id:
            raise RuntimeError("Twilio response did not contain a message ID.")
        return SMSDeliveryResult(provider_message_id=provider_id, accepted_at=datetime.now(UTC))
