"""DRF views for the accounts API: register, session auth, profile."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class RegisterView(APIView):
    """Create a user and open their session in one call."""

    permission_classes = [AllowAny]

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

    def post(self, request):
        """Log the user out and clear the session cookie."""
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """Profile of the logged-in user, used by the frontend session check."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the id and username of the authenticated user."""
        return Response({"id": request.user.pk, "username": request.user.username})
