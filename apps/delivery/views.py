from rest_framework import generics
from rest_framework.response import Response

from apps.delivery.models import ProviderConfiguration
from apps.delivery.serializers import ProviderConfigurationSerializer
from apps.delivery.services import save_provider_configuration
from apps.tenancy.authentication import APIKeyAuthentication
from apps.tenancy.permissions import HasAPIKey


class ProviderConfigurationListCreateView(generics.ListCreateAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]
    serializer_class = ProviderConfigurationSerializer

    def get_queryset(self):
        return ProviderConfiguration.objects.filter(business=self.request.tenant_context.business)

    def list(self, request, *args, **kwargs):
        if not request.tenant_context.has_scope("providers:read"):
            return Response({"detail": "Insufficient scope."}, status=403)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not request.tenant_context.has_scope("providers:write"):
            return Response({"detail": "Insufficient scope."}, status=403)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        configuration = save_provider_configuration(
            request.tenant_context.business,
            data["channel"],
            data["provider_name"],
            data["credentials"],
        )
        return Response(self.get_serializer(configuration).data, status=201)


class ProviderConfigurationDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]
    serializer_class = ProviderConfigurationSerializer

    def get_queryset(self):
        return ProviderConfiguration.objects.filter(business=self.request.tenant_context.business)

    def retrieve(self, request, *args, **kwargs):
        if not request.tenant_context.has_scope("providers:read"):
            return Response({"detail": "Insufficient scope."}, status=403)
        return super().retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        if not self.request.tenant_context.has_scope("providers:write"):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Insufficient scope.")
        data = serializer.validated_data
        if "credentials" in data:
            save_provider_configuration(
                self.request.tenant_context.business,
                data.get("channel", serializer.instance.channel),
                data.get("provider_name", serializer.instance.provider_name),
                data["credentials"],
            )
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if not self.request.tenant_context.has_scope("providers:write"):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Insufficient scope.")
        instance.delete()
