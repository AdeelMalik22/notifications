import re

from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import EventType, NotificationCategory, Template, TemplateVersion
from apps.catalog.serializers import (
    CategorySerializer,
    EventTypeSerializer,
    TemplatePreviewSerializer,
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


class TemplateVersionPublishView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def post(self, request, version_id):
        business = request.tenant_context.business
        version = TemplateVersion.objects.select_related("template__event_type").get(
            id=version_id, template__business=business
        )
        if version.status != TemplateVersion.Status.DRAFT:
            return Response({"detail": "Only draft versions can be published."}, status=400)
        required = set(version.template.event_type.variable_schema)
        if set(version.variables) != required:
            return Response(
                {"detail": "Variables must match the event schema exactly."}, status=400
            )
        TemplateVersion.objects.filter(id=version.id).update(
            status=TemplateVersion.Status.PUBLISHED, published_at=timezone.now()
        )
        version.refresh_from_db()
        return Response(TemplateVersionSerializer(version, context={"business": business}).data)


class TemplateVersionPreviewView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def post(self, request, version_id):
        business = request.tenant_context.business
        version = TemplateVersion.objects.get(id=version_id, template__business=business)
        payload = TemplatePreviewSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        values = payload.validated_data["variables"]
        names = set(re.findall(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}", version.body))
        unknown = names - set(values)
        if unknown:
            return Response(
                {"detail": f"Missing variables: {', '.join(sorted(unknown))}."}, status=400
            )
        body = re.sub(
            r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}",
            lambda match: values[match.group(1)],
            version.body,
        )
        return Response({"subject": version.subject, "body": body})
