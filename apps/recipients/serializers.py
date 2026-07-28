from rest_framework import serializers

from apps.catalog.models import Channel, NotificationCategory
from apps.recipients.models import Preference, Recipient


class RecipientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Recipient
        fields = ["id", "external_id", "email", "phone_number", "is_active"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        from apps.recipients.privacy import decrypt_contact

        data["email"] = decrypt_contact(instance.email_ciphertext)
        data["phone_number"] = decrypt_contact(instance.phone_ciphertext)
        return data

    def create(self, validated_data):
        return Recipient.objects.create(business=self.context["business"], **validated_data)


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ["id", "recipient", "category", "channel", "enabled", "updated_at"]
        read_only_fields = ["id", "updated_at"]

    def validate(self, attrs):
        business = self.context["business"]
        recipient = attrs.get("recipient", getattr(self.instance, "recipient", None))
        category = attrs.get("category", getattr(self.instance, "category", None))
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        enabled = attrs.get("enabled", getattr(self.instance, "enabled", None))
        if recipient.business_id != business.id or category.business_id != business.id:
            raise serializers.ValidationError(
                "Recipient and category must belong to the authenticated tenant."
            )
        if category.policy == NotificationCategory.Policy.MANDATORY and not enabled:
            raise serializers.ValidationError("Mandatory categories cannot be disabled.")
        if category.policy == NotificationCategory.Policy.MARKETING and enabled is not True:
            return attrs
        if channel not in Channel.values:
            raise serializers.ValidationError({"channel": "Unsupported channel."})
        return attrs

    def create(self, validated_data):
        return Preference.objects.create(business=self.context["business"], **validated_data)
