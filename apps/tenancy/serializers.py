from rest_framework import serializers

from apps.tenancy.models import APIKey


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    scopes = serializers.ListField(
        child=serializers.ChoiceField(choices=APIKey.Scope.values), allow_empty=False
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class APIKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "prefix",
            "scopes",
            "expires_at",
            "revoked_at",
            "last_used_at",
            "created_at",
        ]
