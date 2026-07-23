"""OpenAPI response serializers for operational endpoints."""

from rest_framework import serializers


class LivenessSerializer(serializers.Serializer[dict[str, object]]):
    """Describe the liveness response."""

    status = serializers.ChoiceField(choices=["ok"])


class ReadinessSerializer(serializers.Serializer[dict[str, object]]):
    """Describe readiness and its safe dependency summary."""

    status = serializers.ChoiceField(choices=["ok", "unavailable"])
    checks = serializers.DictField(child=serializers.ChoiceField(choices=["ok", "failed"]))
