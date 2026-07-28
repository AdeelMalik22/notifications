from rest_framework import serializers

from apps.delivery.models import ProviderConfiguration


class ProviderConfigurationSerializer(serializers.ModelSerializer):
    credentials = serializers.DictField(write_only=True, required=False)

    class Meta:
        model = ProviderConfiguration
        fields = [
            "id",
            "channel",
            "provider_name",
            "credentials",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if self.instance is None and not attrs.get("credentials"):
            raise serializers.ValidationError({"credentials": "Credentials are required."})
        return attrs
