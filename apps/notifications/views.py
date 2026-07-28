from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.serializers import NotificationTriggerSerializer
from apps.notifications.services import trigger_notification
from apps.tenancy.authentication import APIKeyAuthentication
from apps.tenancy.permissions import HasAPIKey


class NotificationTriggerView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def post(self, request):
        if not request.tenant_context.has_scope("notifications:write"):
            return Response({"detail": "Insufficient scope."}, status=status.HTTP_403_FORBIDDEN)
        key = request.headers.get("Idempotency-Key")
        if not key:
            return Response({"detail": "Idempotency-Key header is required."}, status=400)
        serializer = NotificationTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        payload["variables"] = dict(payload["variables"])
        payload["recipient_id"] = str(payload["recipient_id"])
        try:
            notification, duplicate = trigger_notification(
                request.tenant_context.business, key, payload
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {
                "notification_id": str(notification.id),
                "status": notification.status,
                "duplicate": duplicate,
            },
            status=status.HTTP_200_OK if duplicate else status.HTTP_202_ACCEPTED,
        )
