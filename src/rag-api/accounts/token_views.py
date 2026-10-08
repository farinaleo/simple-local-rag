"""API token management views: create, list, pause, revoke."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.schema_serializers import (
    _many,
    _token_create_request,
    _token_response,
    _token_update_request,
    _token_with_secret_response,
)
from accounts.token_auth import BearerTokenAuthentication
from accounts.token_models import DEFAULT_SCOPES, Scope, generate_token

TOKEN_AUTH_FORBIDDEN = "API tokens cannot manage tokens or accounts"


def _token_payload(token):
    """Build the listing payload for an ApiToken (hash never exposed)."""
    return {
        "id": token.pk,
        "name": token.name,
        "scopes": token.scopes,
        "created_at": token.created_at,
        "last_used_at": token.last_used_at,
        "is_active": token.is_active,
        "expires_at": token.expires_at,
        "expired": not token.usable,
        "status": "active" if token.usable else ("paused" if not token.is_active else "expired"),
    }


class TokenListView(APIView):
    """List and create the caller's own API tokens."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: _many(_token_response)})
    def get(self, request):
        """List the caller's tokens; the plaintext never appears again."""
        tokens = request.user.api_tokens.all()
        return Response([_token_payload(token) for token in tokens])

    @extend_schema(
        request=_token_create_request,
        responses={201: _token_with_secret_response, 400: OpenApiResponse()},
    )
    def post(self, request):
        """Create a token; the plaintext is returned exactly once.

        Args:
            request: The JSON request with ``name`` and ``scopes``.

        Returns:
            201 with the token payload and its one-time plaintext,
            400 on a missing name or invalid scopes.

        """
        if isinstance(request.successful_authenticator, BearerTokenAuthentication):
            return Response({"detail": TOKEN_AUTH_FORBIDDEN}, status=400)
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"detail": "no name provided"}, status=400)
        scopes = request.data.get("scopes", DEFAULT_SCOPES)
        if not isinstance(scopes, list) or not scopes:
            return Response({"detail": "scopes must be a non-empty list"}, status=400)
        invalid = [scope for scope in scopes if scope not in Scope.values]
        if invalid:
            return Response({"detail": f"invalid scopes: {', '.join(invalid)}"}, status=400)
        plaintext, token_hash = generate_token()
        from accounts.token_models import ApiToken

        token = ApiToken.objects.create(
            user=request.user, name=name, token_hash=token_hash, scopes=scopes
        )
        return Response(
            {**_token_payload(token), "token": plaintext},
            status=status.HTTP_201_CREATED,
        )


class TokenDetailView(APIView):
    """Pause, resume or revoke one of the caller's tokens."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=_token_update_request,
        responses={200: _token_response, 404: OpenApiResponse()},
    )
    def patch(self, request, token_id):
        """Pause or resume a token; paused tokens reject immediately.

        Args:
            request: The JSON request with ``is_active``.
            token_id: The id of the managed token.

        Returns:
            200 with the updated token, 404 on a foreign token.

        """
        if isinstance(request.successful_authenticator, BearerTokenAuthentication):
            return Response({"detail": TOKEN_AUTH_FORBIDDEN}, status=400)
        token = request.user.api_tokens.filter(pk=token_id).first()
        if token is None:
            return Response({"detail": "token not found"}, status=404)
        if "is_active" in request.data:
            token.is_active = bool(request.data["is_active"])
            token.save(update_fields=["is_active"])
        return Response(_token_payload(token))

    @extend_schema(responses={204: OpenApiResponse(), 404: OpenApiResponse()})
    def delete(self, request, token_id):
        """Revoke a token permanently.

        Args:
            request: The deletion request.
            token_id: The id of the revoked token.

        Returns:
            204 on success, 404 on a foreign token.

        """
        if isinstance(request.successful_authenticator, BearerTokenAuthentication):
            return Response({"detail": TOKEN_AUTH_FORBIDDEN}, status=400)
        token = request.user.api_tokens.filter(pk=token_id).first()
        if token is None:
            return Response({"detail": "token not found"}, status=404)
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
