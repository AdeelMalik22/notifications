from rest_framework import serializers

from apps.notifications.models import Delivery, DeliveryAttempt, Notification


class NotificationTriggerSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=120)
    recipient_id = serializers.UUIDField()
    variables = serializers.DictField()


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
