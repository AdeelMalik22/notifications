"""Bearer API-key authentication."""

from rest_framework import authentication, exceptions

from apps.tenancy.context import TenantContext
from apps.tenancy.services import authenticate_key


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header:
            return None
        if not header.startswith("Bearer "):
            raise exceptions.AuthenticationFailed("Invalid authorization header")
        key = authenticate_key(header[7:].strip())
        if key is None:
            raise exceptions.AuthenticationFailed("Invalid or inactive API key")
        request.tenant_context = TenantContext(business=key.business, api_key=key)
        return key, key.business
