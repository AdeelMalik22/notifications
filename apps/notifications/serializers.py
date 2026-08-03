import json

from django.conf import settings
from rest_framework import serializers

from apps.notifications.models import Delivery, DeliveryAttempt, Notification


class NotificationTriggerSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=120)
    recipient_id = serializers.UUIDField()
    variables = serializers.DictField()

    def validate(self, attrs):
        variables = attrs["variables"]
        if len(variables) > settings.NOTIFICATION_MAX_VARIABLES:
            raise serializers.ValidationError(
                {"variables": f"At most {settings.NOTIFICATION_MAX_VARIABLES} variables are allowed."}
            )
        try:
            payload_size = len(json.dumps(attrs, separators=(",", ":"), default=str).encode())
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError("Variables must contain JSON values.") from exc
        if payload_size > settings.NOTIFICATION_MAX_PAYLOAD_BYTES:
            raise serializers.ValidationError(
                f"Request payload must not exceed {settings.NOTIFICATION_MAX_PAYLOAD_BYTES} bytes."
            )
        return attrs


class DeliveryAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryAttempt
        fields = [
            "id",
            "attempt_number",
            "status",
            "provider_message_id",
            "error_class",
            "created_at",
        ]


class DeliverySerializer(serializers.ModelSerializer):
    attempts = DeliveryAttemptSerializer(many=True, read_only=True)

    class Meta:
        model = Delivery
        fields = ["id", "channel", "status", "preference_reason", "created_at", "attempts"]


class NotificationSerializer(serializers.ModelSerializer):
    deliveries = DeliverySerializer(many=True, read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "event_type",
            "recipient",
            "idempotency_key",
            "status",
            "created_at",
            "deliveries",
        ]
