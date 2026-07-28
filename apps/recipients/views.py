from rest_framework import generics

from apps.recipients.models import Preference, Recipient
from apps.recipients.serializers import PreferenceSerializer, RecipientSerializer
from apps.tenancy.authentication import APIKeyAuthentication
from apps.tenancy.permissions import HasAPIKey


class TenantCreateListView(generics.ListCreateAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]
    serializer_class = None
    model = None

    def get_queryset(self):
        return self.model.objects.filter(business=self.request.tenant_context.business)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "business": self.request.tenant_context.business,
        }


class RecipientView(TenantCreateListView):
    model = Recipient
    serializer_class = RecipientSerializer


class PreferenceView(TenantCreateListView):
    model = Preference
    serializer_class = PreferenceSerializer


class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]
    serializer_class = None
    model = None

    def get_queryset(self):
        return self.model.objects.filter(business=self.request.tenant_context.business)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "business": self.request.tenant_context.business,
        }


class RecipientDetailView(TenantDetailView):
    model = Recipient
    serializer_class = RecipientSerializer


class PreferenceDetailView(TenantDetailView):
    model = Preference
    serializer_class = PreferenceSerializer
