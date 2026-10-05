"""Admin API tests: account creation, blocking, temporary passwords."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile, Role

pytestmark = pytest.mark.django_db

client = APIClient()


def _user(username, role=Role.USER, password="password123"):
    """Create a user with the given role and return it."""
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.update_or_create(user=user, defaults={"role": role})
    return user


def _login(username, password="password123"):
    """Open a session for the given user on the shared client."""
    client.post("/api/auth/login/", {"username": username, "password": password}, format="json")


def test_user_gets_403_on_admin_endpoints():
    """A normal user is rejected on every admin endpoint."""
    _user("bob")
    _login("bob")
    assert client.get("/api/auth/admin/users/").status_code == 403
    assert client.post("/api/auth/admin/users/", {"username": "x"}).status_code == 403
    assert client.patch("/api/auth/admin/users/1/", {}).status_code == 403
    assert client.delete("/api/auth/admin/users/1/").status_code == 403


def test_admin_creates_user_with_temporary_password():
    """A created account gets a temp password and the must-change flag."""
    _user("root", role=Role.ADMIN)
    _login("root")
    response = client.post(
        "/api/auth/admin/users/", {"username": "newbie", "role": "user"}, format="json"
    )
    assert response.status_code == 201
    body = response.json()
    temp = body["temporary_password"]
    assert temp and body["must_change_password"] is True
    user = User.objects.get(username="newbie")
    assert user.check_password(temp)
    assert user.profile.role == Role.USER


def test_admin_resets_password():
    """A password reset issues a new temp password and re-arms the flag."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    bob.profile.must_change_password = False
    bob.profile.save()
    _login("root")
    response = client.patch(
        f"/api/auth/admin/users/{bob.pk}/", {"reset_password": True}, format="json"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["temporary_password"]
    assert body["must_change_password"] is True
    bob.refresh_from_db()
    assert bob.check_password(body["temporary_password"])


def test_admin_blocks_user_and_revokes_sessions():
    """Blocking sets is_active False and kills existing sessions."""
    bob = _user("bob")
    _user("root", role=Role.ADMIN)
    bob_client = APIClient()
    bob_client.post(
        "/api/auth/login/",
        {"username": "bob", "password": "password123"},
        format="json",
    )
    assert bob_client.get("/api/auth/me/").status_code == 200
    admin_client = APIClient()
    admin_client.post(
        "/api/auth/login/",
        {"username": "root", "password": "password123"},
        format="json",
    )
    response = admin_client.patch(
        f"/api/auth/admin/users/{bob.pk}/", {"is_active": False}, format="json"
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    bob.refresh_from_db()
    assert bob.is_active is False
    assert bob_client.get("/api/auth/me/").status_code in (401, 403)


def test_last_admin_cannot_be_blocked():
    """An admin account cannot be blocked via the admin API."""
    admin = _user("root", role=Role.ADMIN)
    _login("root")
    response = client.patch(
        f"/api/auth/admin/users/{admin.pk}/", {"is_active": False}, format="json"
    )
    assert response.status_code == 400
    assert "profile page" in response.json()["detail"]


def test_change_password_clears_flag():
    """A self-service change clears the must-change flag."""
    bob = _user("bob")
    bob.profile.must_change_password = True
    bob.profile.save()
    _login("bob")
    response = client.post("/api/auth/password/", {"new_password": "brand-new-pass"}, format="json")
    assert response.status_code == 204
    bob.refresh_from_db()
    assert bob.check_password("brand-new-pass")
    assert bob.profile.must_change_password is False


def test_me_exposes_must_change_password():
    """The me endpoint reports the must-change flag."""
    bob = _user("bob")
    bob.profile.must_change_password = True
    bob.profile.save()
    _login("bob")
    response = client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.json()["must_change_password"] is True
