"""Role and admin bootstrap tests: tiers, permissions, last-admin guard."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile, Role

pytestmark = pytest.mark.django_db

client = APIClient()


def _user(username, role=Role.USER, password="password123"):
    """Create a user with the given role and return it."""
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(user=user, role=role)
    return user


def _login(username, password="password123"):
    """Open a session for the given user on the shared client."""
    client.post("/api/auth/login/", {"username": username, "password": password}, format="json")


def test_me_exposes_role():
    """Me returns the caller's role alongside id and username."""
    _user("alice", role=Role.ADMIN)
    _login("alice")
    response = client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_user_cannot_list_users():
    """A normal user gets 403 on the admin user listing."""
    _user("bob")
    _login("bob")
    response = client.get("/api/auth/users/")
    assert response.status_code == 403


def test_admin_can_list_users():
    """An admin lists every account with its role."""
    admin = _user("root", role=Role.ADMIN)
    _user("bob")
    _login("root")
    response = client.get("/api/auth/users/")
    assert response.status_code == 200
    entries = {entry["username"]: entry["role"] for entry in response.json()}
    assert entries == {"root": "admin", "bob": "user"}
    assert admin.pk in {entry["id"] for entry in response.json()}


def test_admin_can_promote_and_demote():
    """An admin changes another account's role in both directions."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    _login("root")
    response = client.patch(f"/api/auth/users/{bob.pk}/", {"role": "admin"}, format="json")
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    response = client.patch(f"/api/auth/users/{bob.pk}/", {"role": "user"}, format="json")
    assert response.status_code == 200
    assert response.json()["role"] == "user"


def test_user_cannot_change_roles():
    """A normal user gets 403 on role management."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    _login("bob")
    response = client.patch(f"/api/auth/users/{bob.pk}/", {"role": "admin"}, format="json")
    assert response.status_code == 403


def test_last_admin_cannot_be_demoted():
    """The last admin cannot demote themselves."""
    admin = _user("root", role=Role.ADMIN)
    _login("root")
    response = client.patch(f"/api/auth/users/{admin.pk}/", {"role": "user"}, format="json")
    assert response.status_code == 400
    assert "last admin" in response.json()["detail"]


def test_last_admin_cannot_be_deleted():
    """The last admin cannot be deleted, even by themselves."""
    admin = _user("root", role=Role.ADMIN)
    _login("root")
    response = client.delete(f"/api/auth/users/{admin.pk}/")
    assert response.status_code == 400
    assert "last admin" in response.json()["detail"]


def test_admin_can_delete_user():
    """An admin deletes a normal account."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    _login("root")
    response = client.delete(f"/api/auth/users/{bob.pk}/")
    assert response.status_code == 204
    assert not User.objects.filter(username="bob").exists()


def test_invalid_role_rejected():
    """An unknown role value returns 400."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    _login("root")
    response = client.patch(f"/api/auth/users/{bob.pk}/", {"role": "superuser"}, format="json")
    assert response.status_code == 400


def test_bootstrap_migration_creates_admin(monkeypatch):
    """The bootstrap function creates the admin from env variables."""
    from accounts.migrations import _bootstrap_admin as bootstrap_admin

    monkeypatch.setenv("ADMIN_USERNAME", "bootstrap-admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "bootstrap-pass-123")
    bootstrap_admin(None, None)
    user = User.objects.get(username="bootstrap-admin")
    assert user.profile.role == Role.ADMIN
    assert user.check_password("bootstrap-pass-123")
