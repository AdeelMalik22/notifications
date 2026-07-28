from django.core.cache import cache

from apps.notifications.limits import allow_recipient, allow_tenant


def test_tenant_limit_is_enforced() -> None:
    cache.clear()
    assert allow_tenant("business-1", 2)
    assert allow_tenant("business-1", 2)
    assert not allow_tenant("business-1", 2)


def test_recipient_limits_are_isolated() -> None:
    cache.clear()
    assert allow_recipient("business-1", "recipient-1", 1)
    assert not allow_recipient("business-1", "recipient-1", 1)
    assert allow_recipient("business-1", "recipient-2", 1)
