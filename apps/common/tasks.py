"""Small operational tasks shared by the application."""

from celery import shared_task


@shared_task(  # type: ignore[untyped-decorator]
    name="notificationos.system.health_ping",
    ignore_result=True,
)
def health_ping() -> str:
    """Provide a side-effect-free task for worker discovery smoke checks."""
    return "pong"
