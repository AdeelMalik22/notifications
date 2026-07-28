from django.contrib import admin

from apps.recipients.models import Preference, Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ["external_id", "business", "email", "phone_number", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["external_id", "business__name", "email"]


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ["recipient", "category", "channel", "enabled", "updated_at"]
    list_filter = ["channel", "enabled"]
    search_fields = ["recipient__external_id", "business__name"]
