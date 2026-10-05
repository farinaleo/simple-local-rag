"""App configuration for accounts."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration of the accounts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Ensure every user has a profile row (roles v4)."""
        from accounts import signals  # noqa: F401
