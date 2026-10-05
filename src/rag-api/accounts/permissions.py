"""Role helpers and DRF permission classes for the account tiers."""

from rest_framework.permissions import BasePermission


def is_admin(user):
    """Return True when the user exists and carries the admin role.

    Args:
        user: The request user (may be anonymous).

    Returns:
        Whether the user is authenticated with an admin profile.

    """
    return bool(user and user.is_authenticated and _safe_is_admin(user))


def _safe_is_admin(user):
    """Read the admin flag on the user profile, tolerating a missing row."""
    profile = getattr(user, "profile", None)
    return profile is not None and profile.role == "admin"


def admin_count():
    """Return the number of admin profiles (used by the last-admin guard)."""
    from accounts.models import Profile, Role

    return Profile.objects.filter(role=Role.ADMIN).count()


def other_admins_excluding(user):
    """Return the number of admins other than the given user."""
    from accounts.models import Profile, Role

    return Profile.objects.filter(role=Role.ADMIN).exclude(user=user).count()


class IsAdmin(BasePermission):
    """Allow access only to authenticated users with the admin role."""

    def has_permission(self, request, view):
        """Return whether the requesting user is an admin."""
        return is_admin(request.user)
