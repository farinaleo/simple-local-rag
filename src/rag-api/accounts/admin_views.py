"""Admin API views: user management, temporary passwords, access blocking."""

import secrets

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile, Role
from accounts.permissions import IsAdmin

TEMP_PASSWORD_ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_temp_password(length=12):
    """Generate a readable temporary password without ambiguous characters.

    Args:
        length: The password length (default 12).

    Returns:
        The generated temporary password string.

    """
    return "".join(secrets.choice(TEMP_PASSWORD_ALPHABET) for _ in range(length))


def _user_payload(user):
    """Build the admin listing payload for a user."""
    profile, _ = Profile.objects.get_or_create(user=user)
    return {
        "id": user.pk,
        "username": user.username,
        "role": profile.role,
        "is_active": user.is_active,
        "must_change_password": profile.must_change_password,
    }


class AdminUserListView(APIView):
    """Admin-only listing and creation of accounts."""

    permission_classes = [IsAdmin]

    def get(self, request):
        """List every account with role, status and password flag."""
        users = User.objects.order_by("id")
        return Response([_user_payload(user) for user in users])

    def post(self, request):
        """Create an account with a temporary password to change at first login.

        Args:
            request: The JSON request carrying ``username`` and an
                optional ``role``.

        Returns:
            201 with the account and its one-time temporary password,
            400 on a missing or taken username or an invalid role.

        """
        username = (request.data.get("username") or "").strip()
        role = request.data.get("role", Role.USER)
        if not username:
            return Response({"detail": "no username provided"}, status=400)
        if role not in Role.values:
            return Response({"detail": "invalid role"}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "username already taken"}, status=400)
        temp_password = _generate_temp_password()
        user = User.objects.create_user(username=username, password=temp_password)
        Profile.objects.update_or_create(
            user=user, defaults={"role": role, "must_change_password": True}
        )
        return Response(
            {**_user_payload(user), "temporary_password": temp_password},
            status=status.HTTP_201_CREATED,
        )


class AdminUserDetailView(APIView):
    """Admin-only per-account management: block, unblock, reset password, delete."""

    permission_classes = [IsAdmin]

    def patch(self, request, user_id):
        """Block or unblock an account, or regenerate a temporary password.

        Args:
            request: The JSON request with ``is_active`` and/or
                ``reset_password`` flags.
            user_id: The id of the managed user.

        Returns:
            200 with the updated account, 400 on the last-admin guard,
            404 when the user does not exist.

        """
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            return Response({"detail": "user not found"}, status=404)
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.role == Role.ADMIN:
            return Response(
                {"detail": "admin accounts are managed through the profile page"},
                status=400,
            )
        payload = {}
        if "is_active" in request.data:
            new_active = bool(request.data["is_active"])
            user.is_active = new_active
            user.save(update_fields=["is_active"])
            if not new_active:
                payload["sessions_revoked"] = _revoke_sessions(user)
        if request.data.get("reset_password"):
            temp_password = _generate_temp_password()
            user.set_password(temp_password)
            user.save(update_fields=["password"])
            profile.must_change_password = True
            profile.save(update_fields=["must_change_password"])
            payload["temporary_password"] = temp_password
        return Response({**_user_payload(user), **payload})

    def delete(self, request, user_id):
        """Delete an account, guarding the last admin.

        Args:
            request: The deletion request.
            user_id: The id of the user to delete.

        Returns:
            204 on success, 400 on the last-admin guard, 404 when the
            user does not exist.

        """
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            return Response({"detail": "user not found"}, status=404)
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.role == Role.ADMIN:
            return Response(
                {"detail": "admin accounts are managed through the profile page"},
                status=400,
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _revoke_sessions(user):
    """Delete every session of a user and return the revoked count.

    Args:
        user: The user whose sessions are revoked.

    Returns:
        The number of deleted sessions.

    """
    from django.contrib.sessions.models import Session

    count = 0
    for session in Session.objects.all():
        decoded = session.get_decoded()
        if decoded.get("_auth_user_id") == str(user.pk):
            session.delete()
            count += 1
    return count


class ChangePasswordView(APIView):
    """Self-service password change, closing the temporary-password flow."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change the caller's password and clear the must-change flag.

        Args:
            request: The JSON request carrying ``new_password``.

        Returns:
            204 on success, 400 on a too-short password.

        """
        new_password = request.data.get("new_password") or ""
        if len(new_password) < 8:
            return Response({"detail": "password must be at least 8 characters"}, status=400)
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.must_change_password = False
        profile.save(update_fields=["must_change_password"])
        return Response(status=status.HTTP_204_NO_CONTENT)
