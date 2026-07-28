from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.limits import allow_recipient, allow_tenant
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer, NotificationTriggerSerializer
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
        if not allow_tenant(
            str(request.tenant_context.business.id), settings.NOTIFICATION_TENANT_RATE_LIMIT
        ):
            return Response({"detail": "Tenant notification rate limit exceeded."}, status=429)
        if not allow_recipient(
            str(request.tenant_context.business.id),
            payload["recipient_id"],
            settings.NOTIFICATION_RECIPIENT_RATE_LIMIT,
        ):
            return Response({"detail": "Recipient notification rate limit exceeded."}, status=429)
        try:
            notification, duplicate = trigger_notification(
                request.tenant_context.business, key, payload
            )
        except OverflowError as exc:
            return Response({"detail": str(exc)}, status=429)
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


class NotificationHistoryView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def get(self, request, notification_id=None):
        queryset = Notification.objects.filter(
            business=request.tenant_context.business
        ).prefetch_related("deliveries__attempts")
        if notification_id is not None:
            notification = get_object_or_404(queryset, id=notification_id)
            return Response(NotificationSerializer(notification).data)
        return Response(NotificationSerializer(queryset[:100], many=True).data)
