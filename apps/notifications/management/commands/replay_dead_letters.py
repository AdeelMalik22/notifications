"""Safely requeue explicitly selected dead-lettered deliveries."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.notifications.models import Delivery


class Command(BaseCommand):
    help = "Replay explicitly selected dead-lettered deliveries."

    def add_arguments(self, parser):
        parser.add_argument("delivery_ids", nargs="+", help="Delivery UUIDs to replay")
        parser.add_argument(
            "--confirm", action="store_true", help="Required to modify delivery state"
        )

    def handle(self, *args, **options):
        ids = options["delivery_ids"]
        queryset = Delivery.objects.filter(id__in=ids, dead_lettered_at__isnull=False)
        found = set(str(value) for value in queryset.values_list("id", flat=True))
        missing = sorted(set(ids) - found)
        if missing:
            raise CommandError("Not dead-lettered or not found: " + ", ".join(missing))
        if not options["confirm"]:
            self.stdout.write(f"Would replay {len(found)} delivery(ies). Re-run with --confirm.")
            return
        with transaction.atomic():
            queryset.update(status=Delivery.Status.PENDING, dead_lettered_at=None)
            updated = queryset.select_related("outbox_event")
            for delivery in updated:
                delivery.outbox_event.published_at = None
                delivery.outbox_event.save(update_fields=["published_at"])
        self.stdout.write(self.style.SUCCESS(f"Requeued {len(found)} delivery(ies)."))
