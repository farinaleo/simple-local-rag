"""drf-spectacular OpenAPI extensions for the accounts API."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object

from accounts.token_auth import BearerTokenAuthentication


class BearerTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    """Describe the Bearer token scheme in the OpenAPI schema."""

    target_class = BearerTokenAuthentication
    name = "bearerAuth"

    def get_security_definition(self, auto_schema):
        """Return the security scheme object for ``Authorization: Bearer``.

        Args:
            auto_schema: The AutoSchema generating the current operation.

        Returns:
            The OpenAPI security scheme for bearer tokens.
        """
        return build_bearer_security_scheme_object(
            "bearerAuth", "Bearer token created on the profile page"
        )
