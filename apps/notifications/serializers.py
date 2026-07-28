from rest_framework import serializers


class NotificationTriggerSerializer(serializers.Serializer):
    event_type = serializers.CharField(max_length=120)
    recipient_id = serializers.UUIDField()
    variables = serializers.DictField()
