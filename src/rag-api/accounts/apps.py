"""App configuration for accounts."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration of the accounts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Register app signals and OpenAPI schema extensions."""
        from accounts import (
            schema,  # noqa: F401  register OpenAPI extensions
            signals,  # noqa: F401
        )
