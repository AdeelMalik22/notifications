from django.contrib import admin

from apps.audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["created_at", "business", "action", "object_type", "object_id"]
    list_filter = ["action", "object_type"]
    search_fields = ["business__name", "action", "object_type", "object_id"]
    readonly_fields = [
        "business",
        "actor_key",
        "action",
        "object_type",
        "object_id",
        "metadata",
        "created_at",
    ]
