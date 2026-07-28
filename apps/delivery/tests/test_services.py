import pytest
from cryptography.fernet import Fernet

from apps.delivery.models import ProviderConfiguration
from apps.delivery.services import load_provider_credentials, save_provider_configuration
from apps.tenancy.services import create_business

pytestmark = pytest.mark.django_db


def test_provider_credentials_are_encrypted_at_rest(settings) -> None:
    settings.PROVIDER_ENCRYPTION_KEY = Fernet.generate_key().decode()
    business = create_business("Acme")
    credentials = {"account_sid": "AC123", "auth_token": "secret"}

    configuration = save_provider_configuration(business, "sms", "twilio", credentials)

    assert configuration.encrypted_credentials != str(credentials).encode()
    assert load_provider_credentials(configuration) == credentials
    assert ProviderConfiguration.objects.count() == 1
