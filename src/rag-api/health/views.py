"""Views for the health app."""

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def health_check(request):
    """Return a liveness indicator for the API.

    Args:
        request: The incoming HTTP request (unused, GET only).

    Returns:
        A JSON response with the API status.
    """
    return Response({"status": "ok"})
