from django.contrib import admin

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion


@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ["key", "name", "business", "policy"]
    list_filter = ["policy"]
    search_fields = ["key", "name", "business__name"]


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ["key", "name", "business", "category", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["key", "name", "business__name"]


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ["__str__", "business", "event_type", "channel", "is_active"]
    list_filter = ["channel", "is_active"]
    search_fields = ["event_type__key", "business__name"]


@admin.register(TemplateVersion)
class TemplateVersionAdmin(admin.ModelAdmin):
    list_display = ["template", "version", "status", "created_at", "published_at"]
    list_filter = ["status"]
    search_fields = ["template__event_type__key", "template__business__name"]
    readonly_fields = [
        "template",
        "version",
        "status",
        "subject",
        "body",
        "html_body",
        "variables",
        "created_at",
        "published_at",
    ]
