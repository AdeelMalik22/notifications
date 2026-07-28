from django.contrib import admin

from apps.notifications.models import Delivery, DeliveryAttempt, Notification, OutboxEvent


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "business", "event_type", "recipient", "status", "created_at"]
    list_filter = ["status", "event_type"]
    search_fields = ["id", "business__name", "event_type", "idempotency_key"]
    readonly_fields = [
        "id",
        "business",
        "event_type",
        "recipient",
        "idempotency_key",
        "request_fingerprint",
        "status",
        "payload",
        "created_at",
    ]


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ["id", "business", "notification", "channel", "status", "created_at"]
    list_filter = ["channel", "status"]
    search_fields = ["id", "business__name", "notification__event_type"]
    readonly_fields = [
        "id",
        "business",
        "notification",
        "channel",
        "status",
        "template_snapshot",
        "preference_reason",
        "created_at",
        "next_attempt_at",
        "dead_lettered_at",
    ]


@admin.register(DeliveryAttempt)
class DeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ["delivery", "attempt_number", "status", "error_class", "created_at"]
    list_filter = ["status", "error_class"]
    readonly_fields = [
        "delivery",
        "attempt_number",
        "status",
        "provider_message_id",
        "error_class",
        "created_at",
    ]


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ["id", "business", "delivery", "published_at", "created_at"]
    list_filter = ["published_at"]
    readonly_fields = ["id", "business", "delivery", "published_at", "created_at"]
