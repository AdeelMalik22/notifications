from django.urls import path

from apps.notifications.views import NotificationHistoryView, NotificationTriggerView

urlpatterns = [
    path("notifications/", NotificationTriggerView.as_view(), name="notification-trigger"),
    path("notifications/history/", NotificationHistoryView.as_view(), name="notification-history"),
    path(
        "notifications/<uuid:notification_id>/",
        NotificationHistoryView.as_view(),
        name="notification-detail",
    ),
]
