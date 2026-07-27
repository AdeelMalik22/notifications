from rest_framework import generics

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.catalog.serializers import (
    CategorySerializer,
    EventTypeSerializer,
    TemplateSerializer,
    TemplateVersionSerializer,
)
from apps.tenancy.authentication import APIKeyAuthentication
from apps.tenancy.permissions import HasAPIKey


class TenantCreateListView(generics.ListCreateAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]
    serializer_class = None
    model = None
    scope = "catalog:read"

    def get_queryset(self):
        return self.model.objects.filter(business=self.request.tenant_context.business)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            "business": self.request.tenant_context.business,
        }


class CategoryView(TenantCreateListView):
    model = NotificationCategory
    serializer_class = CategorySerializer


class EventTypeView(TenantCreateListView):
    model = EventType
    serializer_class = EventTypeSerializer


class TemplateView(TenantCreateListView):
    model = Template
    serializer_class = TemplateSerializer


class TemplateVersionView(TenantCreateListView):
    model = TemplateVersion
    serializer_class = TemplateVersionSerializer
