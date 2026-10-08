"""DRF views for the accounts API: register, session auth, profile, roles."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Profile, Role
from accounts.permissions import IsAdmin, other_admins_excluding
from accounts.schema_serializers import (
    _admin_user_response,
    _credentials_request,
    _many,
    _me_response,
    _role_update_request,
    _user_response,
)


class RegisterView(APIView):
    """Create a user and open their session in one call."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=_credentials_request,
        responses={201: _user_response, 400: OpenApiResponse()},
    )
    def post(self, request):
        """Register a user with username and password, then log them in.

        Args:
            request: The JSON request carrying ``username``/``password``.

        Returns:
            201 with the user profile, 400 on a missing or taken username
            or a too-short password.
        """
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        if not username:
            return Response({"detail": "no username provided"}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response(
                {"detail": "password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "username already taken"}, status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return Response({"id": user.pk, "username": user.username}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Open a session for an existing user."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=_credentials_request,
        responses={200: _user_response, 400: OpenApiResponse()},
    )
    def post(self, request):
        """Authenticate with username and password and log the user in.

        Args:
            request: The JSON request carrying ``username``/``password``.

        Returns:
            200 with the user profile, 400 on invalid credentials.
        """
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response({"id": user.pk, "username": user.username})


class LogoutView(APIView):
    """Close the current session."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: OpenApiResponse()})
    def post(self, request):
        """Log the user out and clear the session cookie."""
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """Profile of the logged-in user, used by the frontend session check."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: _me_response})
    def get(self, request):
        """Return the id, username, role and password flag of the user."""
        profile = getattr(request.user, "profile", None)
        role = profile.role if profile is not None else Role.USER
        must_change = profile.must_change_password if profile is not None else False
        return Response(
            {
                "id": request.user.pk,
                "username": request.user.username,
                "role": role,
                "must_change_password": must_change,
            }
        )


class UserListView(APIView):
    """Admin-only listing of all accounts with their role."""

    permission_classes = [IsAdmin]

    @extend_schema(responses={200: _many(_admin_user_response)})
    def get(self, request):
        """Return every user with id, username and role."""
        users = User.objects.select_related("profile").order_by("id")
        data = [
            {
                "id": user.pk,
                "username": user.username,
                "role": user.profile.role if hasattr(user, "profile") else Role.USER,
            }
            for user in users
        ]
        return Response(data)


class UserRoleView(APIView):
    """Admin-only role management for a single account."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=_role_update_request,
        responses={200: _user_response, 400: OpenApiResponse(), 404: OpenApiResponse()},
    )
    def patch(self, request, user_id):
        """Change the role of an account, guarding the last admin.

        Args:
            request: The JSON request carrying ``role``.
            user_id: The id of the user whose role changes.

        Returns:
            200 with the updated profile, 400 on an invalid or unsafe
            change, 404 when the user does not exist.

        """
        role = request.data.get("role", "")
        if role not in Role.values:
            return Response({"detail": "invalid role"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.select_related("profile").filter(pk=user_id).first()
        if user is None:
            return Response({"detail": "user not found"}, status=status.HTTP_404_NOT_FOUND)
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.role == Role.ADMIN and role != Role.ADMIN and other_admins_excluding(user) == 0:
            return Response(
                {"detail": "cannot demote the last admin"}, status=status.HTTP_400_BAD_REQUEST
            )
        profile.role = role
        profile.save(update_fields=["role"])
        return Response({"id": user.pk, "username": user.username, "role": profile.role})

    @extend_schema(
        responses={204: OpenApiResponse(), 400: OpenApiResponse(), 404: OpenApiResponse()},
    )
    def delete(self, request, user_id):
        """Delete an account, guarding the last admin.

        Args:
            request: The deletion request.
            user_id: The id of the user to delete.

        Returns:
            204 on success, 400 when deleting the last admin, 404 when
            the user does not exist.

        """
        user = User.objects.select_related("profile").filter(pk=user_id).first()
        if user is None:
            return Response({"detail": "user not found"}, status=status.HTTP_404_NOT_FOUND)
        profile, _ = Profile.objects.get_or_create(user=user)
        if profile.role == Role.ADMIN and other_admins_excluding(user) == 0:
            return Response(
                {"detail": "cannot delete the last admin"}, status=status.HTTP_400_BAD_REQUEST
            )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
