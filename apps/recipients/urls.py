from django.urls import path

from apps.recipients.views import PreferenceView, RecipientView

urlpatterns = [
    path("recipients/", RecipientView.as_view(), name="recipients"),
    path("preferences/", PreferenceView.as_view(), name="preferences"),
]
