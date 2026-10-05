"""Admin API token oversight tests: list, pause, revoke across accounts."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile, Role
from accounts.token_models import ApiToken, generate_token

pytestmark = pytest.mark.django_db

client = APIClient()


def _user(username, role=Role.USER, password="password123"):
    """Create a user with the given role and return it."""
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.update_or_create(user=user, defaults={"role": role})
    return user


def _make_token(user, name="cli"):
    """Create an ApiToken for a user and return it."""
    _, token_hash = generate_token()
    return ApiToken.objects.create(user=user, name=name, token_hash=token_hash)


def test_admin_lists_all_tokens_with_owner():
    """An admin sees every token, including other users', with owner names."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    _make_token(bob)
    _make_token(bob, name="backup")
    client.force_authenticate(user=User.objects.get(username="root"))
    response = client.get("/api/auth/admin/tokens/")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 2
    assert all(entry["user"] == "bob" for entry in entries)
    assert all("token_hash" not in entry and "token" not in entry for entry in entries)


def test_non_admin_gets_403_on_admin_token_endpoints():
    """A normal user is rejected on the admin token endpoints."""
    _user("bob")
    client.force_authenticate(user=User.objects.get(username="bob"))
    assert client.get("/api/auth/admin/tokens/").status_code == 403
    response = client.patch("/api/auth/admin/tokens/1/", {"is_active": False}, format="json")
    assert response.status_code == 403
    assert client.delete("/api/auth/admin/tokens/1/").status_code == 403


def test_bearer_cannot_reach_admin_token_endpoints_even_for_admin():
    """A request authenticated with a Bearer token is rejected on admin endpoints."""
    admin = _user("root", role=Role.ADMIN)
    plaintext, token_hash = generate_token()
    ApiToken.objects.create(
        user=admin, name="cli", token_hash=token_hash, scopes=["documents:read"]
    )
    token_client = APIClient()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {plaintext}"}
    assert token_client.get("/api/auth/admin/tokens/", **headers).status_code == 400
    assert (
        token_client.patch(
            "/api/auth/admin/tokens/1/", {"is_active": False}, format="json", **headers
        ).status_code
        == 400
    )
    assert token_client.delete("/api/auth/admin/tokens/1/", **headers).status_code == 400
    assert ApiToken.objects.filter(name="cli").exists()


def test_admin_pauses_and_revokes_any_token():
    """An admin can pause and revoke another user's token."""
    _user("root", role=Role.ADMIN)
    bob = _user("bob")
    token = _make_token(bob)
    client.force_authenticate(user=User.objects.get(username="root"))
    response = client.patch(
        f"/api/auth/admin/tokens/{token.pk}/", {"is_active": False}, format="json"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "paused"
    token.refresh_from_db()
    assert token.is_active is False
    response = client.delete(f"/api/auth/admin/tokens/{token.pk}/")
    assert response.status_code == 204
    assert not ApiToken.objects.filter(pk=token.pk).exists()


def test_admin_token_detail_404_on_unknown_token():
    """An unknown token id returns 404."""
    _user("root", role=Role.ADMIN)
    client.force_authenticate(user=User.objects.get(username="root"))
    response = client.patch("/api/auth/admin/tokens/999/", {"is_active": False}, format="json")
    assert response.status_code == 404
    assert client.delete("/api/auth/admin/tokens/999/").status_code == 404
