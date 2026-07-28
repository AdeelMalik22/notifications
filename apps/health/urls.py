"""Routes for operational health probes."""

from django.urls import path

from apps.health.views import LivenessView, MetricsView, ReadinessView

app_name = "health"

urlpatterns = [
    path("live", LivenessView.as_view(), name="live"),
    path("ready", ReadinessView.as_view(), name="ready"),
    path("metrics", MetricsView.as_view(), name="metrics"),
]
