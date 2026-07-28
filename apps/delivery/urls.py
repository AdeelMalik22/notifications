from django.urls import path

from apps.delivery.views import ProviderConfigurationDetailView, ProviderConfigurationListCreateView

urlpatterns = [
    path(
        "provider-configurations/",
        ProviderConfigurationListCreateView.as_view(),
        name="provider-configurations",
    ),
    path(
        "provider-configurations/<uuid:pk>/",
        ProviderConfigurationDetailView.as_view(),
        name="provider-configuration-detail",
    ),
]
