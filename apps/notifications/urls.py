from django.urls import path

from apps.notifications.views import NotificationTriggerView

urlpatterns = [
    path("notifications/", NotificationTriggerView.as_view(), name="notification-trigger")
]
