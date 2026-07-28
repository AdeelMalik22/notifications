"""Recipient contact privacy contracts."""

import pytest

from apps.recipients.models import Recipient
from apps.recipients.privacy import contact_lookup, decrypt_contact
from apps.tenancy.services import create_business

pytestmark = pytest.mark.django_db


def test_contacts_are_encrypted_and_lookup_is_keyed() -> None:
    recipient = Recipient.objects.create(
        business=create_business("Acme"),
        external_id="user-1",
        email="User@example.test",
        phone_number="+1 555 0100",
    )
    recipient.refresh_from_db()

    assert recipient.email == ""
    assert recipient.phone_number == ""
    assert decrypt_contact(recipient.email_ciphertext) == "User@example.test"
    assert decrypt_contact(recipient.phone_ciphertext) == "+1 555 0100"
    assert recipient.email_lookup == contact_lookup("user@example.test")
    assert recipient.phone_lookup == contact_lookup("+1 555 0100")
    assert "User@example.test" not in str(recipient.email_ciphertext)
