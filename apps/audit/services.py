from collections.abc import Mapping
from uuid import UUID

from django.db.models import QuerySet

from apps.audit.models import AuditEvent
from apps.tenancy.models import APIKey, Business

AuditMetadata = Mapping[str, str | int | bool]


def record_event(
    business: Business,
    action: str,
    object_type: str,
    object_id: UUID,
    *,
    actor_key: APIKey | None = None,
    metadata: AuditMetadata | None = None,
) -> AuditEvent:
    if actor_key is not None and actor_key.business_id != business.id:
        raise ValueError("Audit actor must belong to the event tenant.")
    return AuditEvent.objects.create(
        business=business,
        actor_key=actor_key,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata=dict(metadata or {}),
    )


def list_events(business: Business, *, action: str | None = None) -> QuerySet[AuditEvent]:
    queryset = AuditEvent.objects.filter(business=business).select_related("actor_key")
    if action:
        queryset = queryset.filter(action=action)
    return queryset
