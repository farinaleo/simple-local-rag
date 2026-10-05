"""Bearer token authentication and scope permissions for external clients."""

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission

from accounts.token_models import ApiToken


class BearerTokenAuthentication(BaseAuthentication):
    """Authenticate external clients via ``Authorization: Bearer <token>``.

    Session auth keeps working; this class only activates when the
    Bearer header is present. The plaintext token is never logged and
    never persisted — only its SHA-256 hash exists in the database.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        """Return the (user, token) pair when the Bearer token is valid.

        Args:
            request: The incoming request.

        Returns:
            None without a Bearer header; the (user, token) pair on a
            valid, active, unexpired token; None on an invalid one
            (DRF then rejects unauthenticated requests).

        """
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.startswith(f"{self.keyword} "):
            return None
        plaintext = header[len(self.keyword) + 1 :].strip()
        if not plaintext:
            return None
        from accounts.token_models import hash_token

        token = (
            ApiToken.objects.select_related("user", "user__profile")
            .filter(token_hash=hash_token(plaintext))
            .first()
        )
        if token is None or not token.usable:
            return None
        if not token.user.is_active:
            return None
        token.last_used_at = timezone.now()
        token.save(update_fields=["last_used_at"])
        return (token.user, token)

    def authenticate_header(self, request):
        """Advertise the Bearer scheme on 401 responses."""
        return self.keyword


def _token_of(request):
    """Return the ApiToken when the request was token-authenticated."""
    return (
        getattr(request, "auth", None)
        if isinstance(getattr(request, "auth", None), ApiToken)
        else None
    )


def has_scope(request, scope):
    """Check a scope for the current authentication.

    Session-authenticated users have every scope; token-authenticated
    requests are limited to the token's scopes.

    Args:
        request: The incoming request.
        scope: The required Scope value.

    Returns:
        Whether the request may proceed.

    """
    if request.user is None or not request.user.is_authenticated:
        return False
    token = _token_of(request)
    if token is None:
        return True
    return token.has_scope(scope)


class TokenScopePermission(BasePermission):
    """Scope-aware permission for token-authenticated RAG endpoints.

    Only Bearer-token requests are scope-limited; session and
    anonymous requests keep the v3 behaviour (auth off by default,
    anonymous access stays open).
    """

    required_scope = None

    def has_permission(self, request, view):
        """Return whether the caller carries the required scope."""
        token = _token_of(request)
        if token is None:
            return True
        return token.has_scope(self.required_scope)


class DocumentsReadPermission(TokenScopePermission):
    """Require ``documents:read`` for token callers on document reads."""

    required_scope = "documents:read"


class DocumentsWritePermission(TokenScopePermission):
    """Require ``documents:write`` for token callers on document writes."""

    required_scope = "documents:write"


class QueryPermission(TokenScopePermission):
    """Require ``query`` for token callers on chat queries."""

    required_scope = "query"
