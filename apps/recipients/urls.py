from django.urls import path

from apps.recipients.views import (
    PreferenceDetailView,
    PreferenceView,
    RecipientDetailView,
    RecipientView,
)

urlpatterns = [
    path("recipients/", RecipientView.as_view(), name="recipients"),
    path("recipients/<uuid:pk>/", RecipientDetailView.as_view(), name="recipient-detail"),
    path("preferences/", PreferenceView.as_view(), name="preferences"),
    path("preferences/<uuid:pk>/", PreferenceDetailView.as_view(), name="preference-detail"),
]
