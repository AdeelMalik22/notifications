import json

from cryptography.fernet import Fernet
from django.conf import settings

from apps.delivery.models import ProviderConfiguration
from apps.tenancy.models import Business


def _fernet() -> Fernet:
    key = getattr(settings, "PROVIDER_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("PROVIDER_ENCRYPTION_KEY must be configured.")
    return Fernet(key.encode())


def save_provider_configuration(
    business: Business, channel: str, provider_name: str, credentials: dict[str, str]
) -> ProviderConfiguration:
    encrypted = _fernet().encrypt(json.dumps(credentials, sort_keys=True).encode())
    configuration, _ = ProviderConfiguration.objects.update_or_create(
        business=business,
        channel=channel,
        defaults={
            "provider_name": provider_name,
            "encrypted_credentials": encrypted,
            "is_active": True,
        },
    )
    return configuration


def load_provider_credentials(configuration: ProviderConfiguration) -> dict[str, str]:
    return json.loads(_fernet().decrypt(bytes(configuration.encrypted_credentials)))
