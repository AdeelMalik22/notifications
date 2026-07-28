from unittest.mock import Mock, patch

import pytest

from apps.delivery.providers.base import SMSMessage
from apps.delivery.providers.twilio_sms import TwilioSMSProvider


def test_twilio_provider_posts_authenticated_message() -> None:
    response = Mock(status=201)
    response.read.return_value = b'{"sid":"SM123"}'
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    message = SMSMessage("+15555550123", "Hello", "delivery-1")
    with patch("apps.delivery.providers.twilio_sms.urlopen", return_value=response) as send:
        result = TwilioSMSProvider("AC123", "secret", "+15555550000").send(message)
    assert result.provider_message_id == "SM123"
    request = send.call_args.args[0]
    assert request.full_url.endswith("/Accounts/AC123/Messages.json")
    assert request.data == b"To=%2B15555550123&From=%2B15555550000&Body=Hello"


def test_twilio_provider_requires_credentials() -> None:
    with pytest.raises(ValueError, match="credentials"):
        TwilioSMSProvider("", "secret", "+15555550000").send(
            SMSMessage("+1", "Hello", "delivery-1")
        )
