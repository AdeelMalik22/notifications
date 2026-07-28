"""Root URL configuration for NotificationOS."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", include("apps.health.urls")),
    path("api/v1/", include("apps.tenancy.urls")),
    path("api/v1/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.recipients.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]
