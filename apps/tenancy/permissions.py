from rest_framework.permissions import BasePermission


class HasScope(BasePermission):
    required_scope = ""

    def has_permission(self, request, view) -> bool:
        context = getattr(request, "tenant_context", None)
        return context is not None and context.has_scope(self.required_scope)


class HasAPIKey(BasePermission):
    def has_permission(self, request, view) -> bool:
        return getattr(request, "tenant_context", None) is not None
