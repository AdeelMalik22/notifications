"""Generate realistic, repeatable multi-tenant demonstration data."""

import hashlib

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.audit.models import AuditEvent
from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.delivery.models import ProviderConfiguration
from apps.notifications.models import Delivery, DeliveryAttempt, Notification, OutboxEvent
from apps.recipients.models import Preference, Recipient
from apps.recipients.privacy import contact_lookup, encrypt_contact
from apps.tenancy.models import APIKey, Business
from apps.tenancy.services import create_api_key

BUSINESSES = [
    ("Apple", "Cupertino"),
    ("Microsoft", "Redmond"),
    ("Amazon", "Seattle"),
    ("Google", "Mountain View"),
    ("Netflix", "Los Gatos"),
    ("Spotify", "Stockholm"),
    ("Shopify", "Ottawa"),
    ("Stripe", "San Francisco"),
    ("Airbnb", "San Francisco"),
    ("Uber", "San Francisco"),
    ("Salesforce", "San Francisco"),
    ("Adobe", "San Jose"),
    ("Atlassian", "Sydney"),
    ("Canva", "Sydney"),
    ("Slack", "San Francisco"),
    ("Dropbox", "San Francisco"),
    ("Zoom", "San Jose"),
    ("GitHub", "San Francisco"),
    ("Notion", "San Francisco"),
    ("Figma", "San Francisco"),
]
CATEGORIES = [
    ("orders", "Orders", "transactional"),
    ("security", "Security", "mandatory"),
    ("product-news", "Product news", "marketing"),
    ("billing", "Billing", "transactional"),
]
EVENTS = [
    ("order.shipped", "Order shipped", "orders"),
    ("order.delivered", "Order delivered", "orders"),
    ("account.login", "Account login", "security"),
    ("invoice.ready", "Invoice ready", "billing"),
]


class Command(BaseCommand):
    help = "Create named tenants and realistic demo data (idempotent by business name)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--businesses", type=int, default=20)
        parser.add_argument("--records-per-business", type=int, default=2000)
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument("--reset", action="store_true", help="Delete generated tenants first.")

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        count = min(options["businesses"], len(BUSINESSES))
        per_business = options["records_per_business"]
        batch_size = options["batch_size"]
        if per_business < 1:
            self.stderr.write("--records-per-business must be positive")
            return
        for name, city in BUSINESSES[:count]:
            if options["reset"]:
                Business.objects.filter(name=name).delete()
            business, created = Business.objects.get_or_create(
                name=name,
                defaults={"public_id": f"{name.lower()}-demo"},
            )
            existing_recipients = business.recipients.count()
            if not created and existing_recipients >= per_business:
                self.stdout.write(f"Skipping {name}: already seeded")
                continue
            self._seed_business(
                business, city, per_business, batch_size, start_index=existing_recipients
            )
            self.stdout.write(f"Seeded {name} ({city}) with {per_business} records")

    def _seed_business(
        self,
        business: Business,
        city: str,
        total: int,
        batch_size: int,
        start_index: int = 0,
    ) -> None:
        categories = [
            NotificationCategory.objects.get_or_create(
                business=business, key=key, defaults={"name": label, "policy": policy}
            )[0]
            for key, label, policy in CATEGORIES
        ]
        category_map = {category.key: category for category in categories}
        events = [
            EventType.objects.get_or_create(
                business=business,
                key=key,
                defaults={
                    "name": label,
                    "category": category_map[category],
                    "variable_schema": ["customer_name", "reference"],
                },
            )[0]
            for key, label, category in EVENTS
        ]
        templates = []
        for event in events:
            for channel in ("email", "sms"):
                template, _ = Template.objects.get_or_create(
                    business=business, event_type=event, channel=channel
                )
                TemplateVersion.objects.get_or_create(
                    template=template,
                    version=1,
                    defaults={
                        "status": "published",
                        "subject": f"{event.name} from {business.name}",
                        "body": (
                            f"Hello {{customer_name}}, your {event.key} reference is {{reference}}."
                        ),
                        "variables": ["customer_name", "reference"],
                    },
                )
                templates.append((event, template))

        recipients = []
        for index in range(start_index, total):
            email = f"customer{index + 1}@{business.name.lower()}.example"
            phone = f"+1-202-555-{index % 10000:04d}"
            recipients.append(
                Recipient(
                    business=business,
                    external_id=f"{business.name.lower()}-customer-{index + 1}",
                    email_ciphertext=encrypt_contact(email),
                    phone_ciphertext=encrypt_contact(phone),
                    email_lookup=contact_lookup(email),
                    phone_lookup=contact_lookup(phone),
                )
            )
        Recipient.objects.bulk_create(recipients, batch_size=batch_size, ignore_conflicts=True)
        recipients = list(
            Recipient.objects.filter(business=business).order_by("external_id")[:total]
        )
        preferences = [
            Preference(
                business=business,
                recipient=recipient,
                category=category,
                channel=channel,
                enabled=category.policy != "marketing",
            )
            for recipient in recipients
            for category in categories[:2]
            for channel in ("email", "sms")
        ]
        Preference.objects.bulk_create(preferences, batch_size=batch_size, ignore_conflicts=True)

        event = events[0]
        template = next(
            template
            for current_event, template in templates
            if current_event.id == event.id and template.channel == "email"
        )
        version = template.versions.get(version=1)
        notifications = []
        for index, recipient in enumerate(recipients):
            payload = {
                "event_type": event.key,
                "recipient_id": str(recipient.id),
                "variables": {
                    "customer_name": recipient.external_id,
                    "reference": f"{business.name[:3].upper()}-{index + 1000}",
                },
            }
            notifications.append(
                Notification(
                    business=business,
                    event_type=event.key,
                    recipient=recipient,
                    idempotency_key=f"demo-{business.name.lower()}-{index + 1}",
                    request_fingerprint=hashlib.sha256(str(payload).encode()).hexdigest(),
                    status="accepted",
                    payload=payload,
                )
            )
        Notification.objects.bulk_create(
            notifications, batch_size=batch_size, ignore_conflicts=True
        )
        notifications = list(
            Notification.objects.filter(business=business).order_by("created_at")[:total]
        )
        deliveries = [
            Delivery(
                business=business,
                notification=notification,
                channel="email",
                status="pending",
                template_snapshot={
                    "version_id": str(version.id),
                    "subject": version.subject,
                    "body": version.body,
                    "variables": version.variables,
                },
            )
            for notification in notifications
        ]
        Delivery.objects.bulk_create(deliveries, batch_size=batch_size, ignore_conflicts=True)
        deliveries = list(Delivery.objects.filter(business=business).order_by("created_at")[:total])
        OutboxEvent.objects.bulk_create(
            [OutboxEvent(business=business, delivery=delivery) for delivery in deliveries],
            batch_size=batch_size,
            ignore_conflicts=True,
        )
        DeliveryAttempt.objects.bulk_create(
            [
                DeliveryAttempt(delivery=delivery, attempt_number=1, status="queued")
                for delivery in deliveries
            ],
            batch_size=batch_size,
            ignore_conflicts=True,
        )
        self._seed_credentials(business)
        api_key, secret = create_api_key(business, "demo-admin", list(APIKey.Scope.values))
        AuditEvent.objects.get_or_create(
            business=business,
            actor_key=api_key,
            action="demo.seeded",
            object_type="Business",
            object_id=business.id,
            defaults={"metadata": {"city": city, "records": total}},
        )
        self.stdout.write(self.style.SUCCESS(f"Postman API key for {business.name}: {secret}"))

    def _seed_credentials(self, business: Business) -> None:
        for channel in ("email", "sms"):
            ProviderConfiguration.objects.get_or_create(
                business=business,
                channel=channel,
                defaults={
                    "provider_name": "demo",
                    "encrypted_credentials": b"demo-seed",
                    "is_active": True,
                },
            )
