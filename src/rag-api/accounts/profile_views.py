"""Self-service profile views: display name, avatar, password change."""

from django.contrib.auth import authenticate
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile
from accounts.schema_serializers import (
    _password_change_request,
    _profile_response,
    _profile_update_request,
)

AVATAR_MAX_BYTES = 5 * 1024 * 1024
AVATAR_TYPES = {"image/png", "image/jpeg"}


def _profile_payload(user):
    """Build the profile payload for the account page."""
    profile, _ = Profile.objects.get_or_create(user=user)
    avatar_url = None
    if profile.avatar:
        avatar_url = profile.avatar.url
    return {
        "id": user.pk,
        "username": user.username,
        "display_name": profile.display_name or user.username,
        "avatar_url": avatar_url,
        "role": profile.role,
    }


class ProfileView(APIView):
    """Read and update the caller's own profile."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: _profile_response})
    def get(self, request):
        """Return the caller's profile."""
        return Response(_profile_payload(request.user))

    @extend_schema(
        request=_profile_update_request,
        responses={200: _profile_response, 400: OpenApiResponse()},
    )
    def patch(self, request):
        """Update the display name and/or the avatar.

        Args:
            request: The multipart or JSON request with ``display_name``
                and/or an ``avatar`` file part.

        Returns:
            200 with the updated profile, 400 on an oversized or
            non-image avatar.

        """
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if "display_name" in request.data:
            profile.display_name = (request.data.get("display_name") or "").strip()[:100]
            profile.save(update_fields=["display_name"])
        avatar = request.FILES.get("avatar")
        if avatar is not None:
            if avatar.content_type not in AVATAR_TYPES:
                return Response({"detail": "avatar must be a png or jpeg image"}, status=400)
            if avatar.size > AVATAR_MAX_BYTES:
                return Response({"detail": "avatar too large (max 5 MB)"}, status=400)
            if profile.avatar:
                profile.avatar.delete(save=False)
            profile.avatar = avatar
            profile.save(update_fields=["avatar"])
        return Response(_profile_payload(request.user))


class ChangePasswordView(APIView):
    """Self-service password change; the old password is required.

    Exception: a user flagged ``must_change_password`` (temporary
    password) may change without the old one — the temporary password
    is the proof of identity, and other sessions are revoked.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=_password_change_request,
        responses={204: OpenApiResponse(), 400: OpenApiResponse()},
    )
    def post(self, request):
        """Change the caller's password and revoke their other sessions.

        Args:
            request: The JSON request with ``old_password`` and
                ``new_password``.

        Returns:
            204 on success (other sessions revoked), 400 on a missing or
            wrong old password or a too-short new one.

        """
        new_password = request.data.get("new_password") or ""
        if len(new_password) < 8:
            return Response({"detail": "password must be at least 8 characters"}, status=400)
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if not profile.must_change_password:
            old_password = request.data.get("old_password") or ""
            if authenticate(request, username=request.user.username, password=old_password) is None:
                return Response({"detail": "wrong password"}, status=400)
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        profile.must_change_password = False
        profile.save(update_fields=["must_change_password"])
        from accounts.admin_views import _revoke_sessions

        _revoke_sessions(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
