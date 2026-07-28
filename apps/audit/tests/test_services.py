import pytest

from apps.audit.models import AuditEvent
from apps.audit.services import list_events, record_event
from apps.tenancy.services import create_api_key, create_business

pytestmark = pytest.mark.django_db


def test_audit_service_rejects_cross_tenant_actor() -> None:
    first = create_business("First")
    second = create_business("Second")
    key, _ = create_api_key(second, "operator", [])

    with pytest.raises(ValueError, match="event tenant"):
        record_event(first, "test.action", "Business", first.id, actor_key=key)


def test_audit_events_can_be_filtered_by_action() -> None:
    business = create_business("Acme")
    record_event(business, "key.created", "APIKey", business.id)
    record_event(business, "key.revoked", "APIKey", business.id)

    events = list_events(business, action="key.revoked")

    assert list(events.values_list("action", flat=True)) == ["key.revoked"]
    assert AuditEvent.objects.filter(business=business).count() == 2
