from django.core.cache import cache


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
