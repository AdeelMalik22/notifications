import pytest
from cryptography.fernet import Fernet
from rest_framework.test import APIClient

from apps.delivery.models import ProviderConfiguration
from apps.tenancy.models import APIKey
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def test_provider_configuration_api_never_returns_credentials(settings) -> None:
    settings.PROVIDER_ENCRYPTION_KEY = Fernet.generate_key().decode()
    business = create_business("Acme")
    _, secret = create_api_key(
        business, "provider-admin", [APIKey.Scope.PROVIDERS_READ, APIKey.Scope.PROVIDERS_WRITE]
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {secret}")

    response = client.post(
        "/api/v1/provider-configurations/",
        {
            "channel": "sms",
            "provider_name": "twilio",
            "credentials": {"account_sid": "AC123", "auth_token": "secret", "from_number": "+1"},
        },
        format="json",
    )

    assert response.status_code == 201
    assert "credentials" not in response.json()
    assert ProviderConfiguration.objects.get().encrypted_credentials
