from django.urls import path

from apps.tenancy.views import APIKeyListCreateView, APIKeyRevokeView

app_name = "tenancy"

urlpatterns = [
    path("api-keys/", APIKeyListCreateView.as_view(), name="api-keys"),
    path("api-keys/<uuid:key_id>/revoke/", APIKeyRevokeView.as_view(), name="api-key-revoke"),
]

