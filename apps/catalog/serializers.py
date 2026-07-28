from rest_framework import serializers

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion


class TenantSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return self.Meta.model.objects.create(business=self.context["business"], **validated_data)


class CategorySerializer(TenantSerializer):
    class Meta:
        model = NotificationCategory
        fields = ["id", "key", "name", "policy"]


class EventTypeSerializer(TenantSerializer):
    class Meta:
        model = EventType
        fields = ["id", "key", "name", "category", "variable_schema", "is_active"]

    def validate_category(self, value):
        if value.business_id != self.context["business"].id:
            raise serializers.ValidationError("Category is outside the authenticated tenant.")
        return value


class TemplateSerializer(TenantSerializer):
    class Meta:
        model = Template
        fields = ["id", "event_type", "channel", "is_active"]

    def validate_event_type(self, value):
        if value.business_id != self.context["business"].id:
            raise serializers.ValidationError("Event type is outside the authenticated tenant.")
        return value


class TemplateVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateVersion
        fields = [
            "id",
            "template",
            "version",
            "status",
            "subject",
            "body",
            "html_body",
            "variables",
            "created_at",
            "published_at",
        ]
        read_only_fields = ["id", "created_at", "published_at"]

    def validate_template(self, value):
        if value.business_id != self.context["business"].id:
            raise serializers.ValidationError("Template is outside the authenticated tenant.")
        return value

    def validate(self, attrs):
        if attrs.get("version", 0) < 1:
            raise serializers.ValidationError({"version": "Version must be positive."})
        if attrs.get("status") == TemplateVersion.Status.PUBLISHED:
            required = set(attrs["template"].event_type.variable_schema)
            declared = set(attrs.get("variables", []))
            if required != declared:
                raise serializers.ValidationError(
                    {"variables": "Variables must match the event schema exactly."}
                )
        return attrs


class TemplatePreviewSerializer(serializers.Serializer):
    variables = serializers.DictField(child=serializers.CharField(allow_blank=True))
