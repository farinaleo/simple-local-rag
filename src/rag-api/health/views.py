"""Views for the health app."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response


class HealthSerializer(serializers.Serializer):
    """Body of the liveness response."""

    status = serializers.CharField(read_only=True, default="ok")


@extend_schema(responses=HealthSerializer)
@api_view(["GET"])
def health_check(request):
    """Return a liveness indicator for the API.

    Args:
        request: The incoming HTTP request (unused, GET only).

    Returns:
        A JSON response with the API status.
    """
    return Response({"status": "ok"})
