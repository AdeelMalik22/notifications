"""Liveness and readiness API views."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.health.checks import run_readiness_checks
from apps.health.serializers import LivenessSerializer, ReadinessSerializer


class PublicHealthView(APIView):
    """Allow unauthenticated probes without session or throttle work."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]
    throttle_classes: list[type] = []


class LivenessView(PublicHealthView):
    """Report whether the web process can serve requests."""

    @extend_schema(responses={status.HTTP_200_OK: LivenessSerializer})
    def get(self, request: Request) -> Response:
        """Return immediately without contacting external dependencies."""
        return Response({"status": "ok"})


class ReadinessView(PublicHealthView):
    """Report whether synchronous API dependencies are ready."""

    @extend_schema(
        responses={
            status.HTTP_200_OK: ReadinessSerializer,
            status.HTTP_503_SERVICE_UNAVAILABLE: ReadinessSerializer,
        }
    )
    def get(self, request: Request) -> Response:
        """Check PostgreSQL and Redis using bounded operations."""
        checks = run_readiness_checks()
        is_ready = all(result == "ok" for result in checks.values())
        response_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "ok" if is_ready else "unavailable"

        return Response(
            {"status": overall_status, "checks": checks},
            status=response_status,
        )
