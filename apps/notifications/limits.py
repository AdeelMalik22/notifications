from django.core.cache import cache

from apps.tenancy.models import Business

PLAN_LIMITS = {
    Business.Plan.FREE: {"monthly_notifications": 1_000, "recipients": 1_000, "tenant_rate": 100},
    Business.Plan.PROFESSIONAL: {
        "monthly_notifications": 100_000,
        "recipients": 100_000,
        "tenant_rate": 1_000,
    },
    Business.Plan.ENTERPRISE: {
        "monthly_notifications": 1_000_000,
        "recipients": 1_000_000,
        "tenant_rate": 10_000,
    },
}


def plan_limits(plan: str) -> dict[str, int]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[Business.Plan.FREE])


def _consume(key: str, limit: int, window: int = 60) -> bool:
    if limit <= 0:
        return True
    if cache.add(key, 1, timeout=window):
        return True
    try:
        return int(cache.incr(key)) <= limit
    except ValueError:
        return False


def allow_tenant(business_id: str, limit: int) -> bool:
    return _consume(f"notification-limit:tenant:{business_id}", limit)


def allow_recipient(business_id: str, recipient_id: str, limit: int) -> bool:
    return _consume(f"notification-limit:recipient:{business_id}:{recipient_id}", limit)
