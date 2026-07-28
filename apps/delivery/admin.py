from django.contrib import admin

from apps.delivery.models import ProviderConfiguration


@admin.register(ProviderConfiguration)
class ProviderConfigurationAdmin(admin.ModelAdmin):
    list_display = ["business", "channel", "provider_name", "is_active", "updated_at"]
    list_filter = ["channel", "provider_name", "is_active"]
    search_fields = ["business__name", "provider_name"]
    readonly_fields = ["encrypted_credentials", "created_at", "updated_at"]
