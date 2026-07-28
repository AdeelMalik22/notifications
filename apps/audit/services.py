from apps.audit.models import AuditEvent
from apps.tenancy.models import APIKey, Business


def record_event(
    business: Business,
    action: str,
    object_type: str,
    object_id,
    *,
    actor_key: APIKey | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        business=business,
        actor_key=actor_key,
        action=action,
        object_type=object_type,
        object_id=object_id,
        metadata=metadata or {},
    )
