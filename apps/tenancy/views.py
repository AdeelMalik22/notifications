from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenancy.authentication import APIKeyAuthentication
from apps.tenancy.permissions import HasAPIKey
from apps.tenancy.serializers import APIKeyCreateSerializer, APIKeySerializer
from apps.tenancy.services import create_api_key, revoke_api_key


class APIKeyListCreateView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def get(self, request: Request) -> Response:
        if not request.tenant_context.has_scope("api_keys:read"):
            return Response({"detail": "Insufficient scope."}, status=status.HTTP_403_FORBIDDEN)
        keys = request.tenant_context.business.api_keys.all()
        return Response(APIKeySerializer(keys, many=True).data)

    def post(self, request: Request) -> Response:
        if not request.tenant_context.has_scope("api_keys:write"):
            return Response({"detail": "Insufficient scope."}, status=status.HTTP_403_FORBIDDEN)
        serializer = APIKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key, plaintext = create_api_key(
            request.tenant_context.business, **serializer.validated_data
        )
        return Response(
            {"key": APIKeySerializer(key).data, "secret": plaintext},
            status=status.HTTP_201_CREATED,
        )


class APIKeyRevokeView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasAPIKey]

    def post(self, request: Request, key_id: str) -> Response:
        context = request.tenant_context
        if not context.has_scope("api_keys:write"):
            return Response({"detail": "Insufficient scope."}, status=status.HTTP_403_FORBIDDEN)
        key = context.business.api_keys.get(pk=key_id)
        if key.revoked_at is None:
            revoke_api_key(key)
        return Response(APIKeySerializer(key).data)
