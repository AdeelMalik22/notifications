from django.contrib import admin

from apps.tenancy.models import APIKey, Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ["name", "public_id", "is_active", "created_at"]
    search_fields = ["name", "public_id"]


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "business", "prefix", "revoked_at", "expires_at", "last_used_at"]
    list_filter = ["revoked_at"]
    search_fields = ["name", "prefix", "business__name"]
    readonly_fields = ["secret_digest"]
