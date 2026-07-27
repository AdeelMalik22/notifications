from rest_framework import serializers

from apps.catalog.models import Channel, NotificationCategory
from apps.recipients.models import Preference, Recipient


class RecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = ["id", "external_id", "email", "phone_number", "is_active"]

    def create(self, validated_data):
        return Recipient.objects.create(business=self.context["business"], **validated_data)


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ["id", "recipient", "category", "channel", "enabled", "updated_at"]
        read_only_fields = ["id", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        if (
            attrs["recipient"].business_id != business.id
            or attrs["category"].business_id != business.id
        ):
            raise serializers.ValidationError(
                "Recipient and category must belong to the authenticated tenant."
            )
        if (
            attrs["category"].policy == NotificationCategory.Policy.MANDATORY
            and not attrs["enabled"]
        ):
            raise serializers.ValidationError("Mandatory categories cannot be disabled.")
        if (
            attrs["category"].policy == NotificationCategory.Policy.MARKETING
            and attrs["enabled"] is not True
        ):
            return attrs
        if attrs["channel"] not in Channel.values:
            raise serializers.ValidationError({"channel": "Unsupported channel."})
        return attrs

    def create(self, validated_data):
        return Preference.objects.create(business=self.context["business"], **validated_data)
