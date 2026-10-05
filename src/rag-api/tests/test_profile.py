"""Profile page tests: display name, avatar, password change, sessions."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile, Role

pytestmark = pytest.mark.django_db

client = APIClient()


def _user(username, password="password123", role=Role.USER):
    """Create a user with a profile and return it."""
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.update_or_create(user=user, defaults={"role": role})
    return user


def _login(username, password="password123"):
    """Open a session on the shared client."""
    client.post("/api/auth/login/", {"username": username, "password": password}, format="json")


def _png_bytes():
    """Build a minimal valid PNG payload."""
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (40, 40), color="violet").save(buffer, format="PNG")
    return buffer.getvalue()


def test_profile_requires_authentication():
    """Anonymous requests cannot read or update a profile."""
    assert client.get("/api/auth/profile/").status_code == 403
    assert client.patch("/api/auth/profile/", {}).status_code == 403


def test_update_display_name():
    """A user sets their display name; it falls back to the username."""
    _user("leo")
    _login("leo")
    response = client.get("/api/auth/profile/")
    assert response.json()["display_name"] == "leo"
    response = client.patch("/api/auth/profile/", {"display_name": "Léo Farina"}, format="json")
    assert response.status_code == 200
    assert response.json()["display_name"] == "Léo Farina"


def test_upload_avatar():
    """A user uploads a png avatar and gets its URL."""
    _user("leo")
    _login("leo")
    response = client.patch(
        "/api/auth/profile/",
        {"avatar": _png_file()},
        format="multipart",
    )
    assert response.status_code == 200
    assert response.json()["avatar_url"]


def _png_file():
    """Build an uploaded png file part."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile("avatar.png", _png_bytes(), content_type="image/png")


def test_avatar_rejects_non_image():
    """A text file as avatar is refused."""
    _user("leo")
    _login("leo")
    from django.core.files.uploadedfile import SimpleUploadedFile

    response = client.patch(
        "/api/auth/profile/",
        {"avatar": SimpleUploadedFile("evil.txt", b"data", content_type="text/plain")},
        format="multipart",
    )
    assert response.status_code == 400


def test_password_change_requires_old_password():
    """Changing the password without the old one is refused."""
    _user("leo")
    _login("leo")
    response = client.post(
        "/api/auth/password/",
        {"new_password": "brand-new-pass"},
        format="json",
    )
    assert response.status_code == 400


def test_password_change_with_wrong_old_password():
    """A wrong old password is refused."""
    _user("leo")
    _login("leo")
    response = client.post(
        "/api/auth/password/",
        {"old_password": "not-the-one", "new_password": "brand-new-pass"},
        format="json",
    )
    assert response.status_code == 400


def test_password_change_revokes_sessions():
    """A successful change logs out every session of the user."""
    _user("leo")
    other_client = APIClient()
    other_client.post(
        "/api/auth/login/", {"username": "leo", "password": "password123"}, format="json"
    )
    assert other_client.get("/api/auth/me/").status_code == 200
    _login("leo")
    response = client.post(
        "/api/auth/password/",
        {"old_password": "password123", "new_password": "brand-new-pass"},
        format="json",
    )
    assert response.status_code == 204
    leo = User.objects.get(username="leo")
    assert leo.check_password("brand-new-pass")
    assert other_client.get("/api/auth/me/").status_code in (401, 403)


def test_temporary_password_change_skips_old_password():
    """The must-change flag allows changing without the old password."""
    bob = _user("bob")
    bob.profile.must_change_password = True
    bob.profile.save()
    _login("bob")
    response = client.post(
        "/api/auth/password/",
        {"new_password": "my-own-password"},
        format="json",
    )
    assert response.status_code == 204
    bob.refresh_from_db()
    assert bob.profile.must_change_password is False
