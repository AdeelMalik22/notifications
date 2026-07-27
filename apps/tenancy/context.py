"""Explicit request/task tenant context types."""

from dataclasses import dataclass

from apps.tenancy.models import APIKey, Business


@dataclass(frozen=True, slots=True)
class TenantContext:
    business: Business
    api_key: APIKey

    @property
    def business_id(self):
        return self.business.pk

    def has_scope(self, scope: str) -> bool:
        return scope in self.api_key.scopes

