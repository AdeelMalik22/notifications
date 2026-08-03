"""Inspect delivery states that require operator or provider reconciliation."""

from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.notifications.models import Delivery


class Command(BaseCommand):
    help = "Report unknown and dead-lettered deliveries without replaying them."

    def handle(self, *args, **options):
        rows = (
            Delivery.objects.filter(status__in=["unknown", Delivery.Status.FAILED])
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        totals = {row["status"]: row["count"] for row in rows}
        self.stdout.write(f"unknown={totals.get('unknown', 0)}")
        self.stdout.write(
            f"dead_lettered={Delivery.objects.filter(dead_lettered_at__isnull=False).count()}"
        )
        self.stdout.write("No deliveries were changed.")
