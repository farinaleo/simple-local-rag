"""Data models for the accounts app: user profiles with roles."""

from django.conf import settings
from django.db import models


class Role(models.TextChoices):
    """The two account tiers of the v4 design."""

    ADMIN = "admin", "Admin"
    USER = "user", "User"


class Profile(models.Model):
    """Per-user account tier, one row per user.

    Attributes:
        user: The linked Django user (one-to-one, cascade on delete).
        role: The account tier, ``admin`` or ``user`` (default ``user``).
        must_change_password: Whether the next login must redirect to
            the password-change screen (temporary passwords).

    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    must_change_password = models.BooleanField(default=False)

    class Meta:
        """Meta options for the profile model."""

        verbose_name = "profile"
        verbose_name_plural = "profiles"

    def __str__(self):
        """Return a readable label for admin listings."""
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        """Return True when the profile carries the admin tier."""
        return self.role == Role.ADMIN
