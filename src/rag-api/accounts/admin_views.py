"""Admin API views: user management, temporary passwords, access blocking."""

import secrets

from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile, Role
from accounts.permissions import IsAdmin
from accounts.schema_serializers import (
    _admin_token_response,
    _admin_user_create_request,
    _admin_user_created_response,
    _admin_user_response,
    _admin_user_update_request,
    _admin_user_updated_response,
    _many,
    _token_response,
    _token_update_request,
)
from accounts.token_auth import BearerTokenAuthentication
from accounts.token_models import ApiToken
from accounts.token_views import TOKEN_AUTH_FORBIDDEN, _token_payload

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

    @extend_schema(responses={200: _many(_admin_user_response)})
    def get(self, request):
        """List every account with role, status and password flag."""
        users = User.objects.order_by("id")
        return Response([_user_payload(user) for user in users])

    @extend_schema(
        request=_admin_user_create_request,
        responses={201: _admin_user_created_response, 400: OpenApiResponse()},
    )
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

    @extend_schema(
        request=_admin_user_update_request,
        responses={
            200: _admin_user_updated_response,
            400: OpenApiResponse(),
            404: OpenApiResponse(),
        },
    )
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

    @extend_schema(
        responses={204: OpenApiResponse(), 400: OpenApiResponse(), 404: OpenApiResponse()}
    )
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


class AdminTokenListView(APIView):
    """Admin-only listing of every API token across all accounts."""

    permission_classes = [IsAdmin]

    @extend_schema(responses={200: _many(_admin_token_response)})
    def get(self, request):
        """List all tokens with their owner, never exposing the hash."""
        if isinstance(request.successful_authenticator, BearerTokenAuthentication):
            return Response({"detail": TOKEN_AUTH_FORBIDDEN}, status=400)
        tokens = ApiToken.objects.select_related("user").order_by("id")
        return Response(
            [{**_token_payload(token), "user": token.user.username} for token in tokens]
        )


class AdminTokenDetailView(APIView):
    """Admin-only per-token management: pause, resume, revoke."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=_token_update_request,
        responses={200: _token_response, 404: OpenApiResponse()},
    )
    def patch(self, request, token_id):
        """Pause or resume any user's token.

        Args:
            request: The JSON request with ``is_active``.
            token_id: The id of the managed token.

        Returns:
            200 with the updated token, 404 when the token does not exist.
        """
        if isinstance(request.successful_authenticator, BearerTokenAuthentication):
            return Response({"detail": TOKEN_AUTH_FORBIDDEN}, status=400)
        token = ApiToken.objects.filter(pk=token_id).first()
        if token is None:
            return Response({"detail": "token not found"}, status=404)
        if "is_active" in request.data:
            token.is_active = bool(request.data["is_active"])
            token.save(update_fields=["is_active"])
        return Response(_token_payload(token))

    @extend_schema(responses={204: OpenApiResponse(), 404: OpenApiResponse()})
    def delete(self, request, token_id):
        """Revoke any user's token permanently.

        Args:
            request: The deletion request.
            token_id: The id of the revoked token.

        Returns:
            204 on success, 404 when the token does not exist.
        """
        if isinstance(request.successful_authenticator, BearerTokenAuthentication):
            return Response({"detail": TOKEN_AUTH_FORBIDDEN}, status=400)
        token = ApiToken.objects.filter(pk=token_id).first()
        if token is None:
            return Response({"detail": "token not found"}, status=404)
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
