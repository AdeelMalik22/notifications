"""Django Admin registration and safety contract tests."""

from django.contrib import admin

from apps.audit.models import AuditEvent
from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.delivery.models import ProviderConfiguration
from apps.notifications.models import Delivery, DeliveryAttempt, Notification, OutboxEvent
from apps.recipients.models import Preference, Recipient
from apps.tenancy.models import APIKey, Business


def test_all_domain_models_are_registered() -> None:
    expected = {
        AuditEvent,
        Business,
        APIKey,
        NotificationCategory,
        EventType,
        Template,
        TemplateVersion,
        ProviderConfiguration,
        Notification,
        Delivery,
        DeliveryAttempt,
        OutboxEvent,
        Recipient,
        Preference,
    }

    assert expected.issubset(admin.site._registry)


def test_sensitive_and_immutable_records_are_read_only() -> None:
    assert "encrypted_credentials" in admin.site._registry[ProviderConfiguration].readonly_fields
    assert "secret_digest" in admin.site._registry[APIKey].readonly_fields
    assert "payload" in admin.site._registry[Notification].readonly_fields
    assert "template_snapshot" in admin.site._registry[Delivery].readonly_fields
    assert "dead_lettered_at" in admin.site._registry[Delivery].readonly_fields
    assert "metadata" in admin.site._registry[AuditEvent].readonly_fields
