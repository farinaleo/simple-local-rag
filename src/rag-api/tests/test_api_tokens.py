"""API token tests: scopes, bearer auth, pause, revocation, leak safety."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.token_models import ApiToken, Scope, generate_token, hash_token

pytestmark = pytest.mark.django_db

client = APIClient()


def _user(username, password="password123"):
    """Create a user and return it."""
    return User.objects.create_user(username=username, password=password)


def _make_token(user, scopes):
    """Create an ApiToken for a user and return (token, plaintext)."""
    plaintext, token_hash = generate_token()
    token = ApiToken.objects.create(user=user, name="test", token_hash=token_hash, scopes=scopes)
    return token, plaintext


def _bearer_call(plaintext, method, path, *args, **kwargs):
    """Call the API with a Bearer token on a fresh client."""
    token_client = APIClient()
    kwargs["HTTP_AUTHORIZATION"] = f"Bearer {plaintext}"
    return getattr(token_client, method)(path, *args, **kwargs)


def test_create_returns_plaintext_once_and_hashes_it():
    """Creation returns the plaintext once; only the hash is stored."""
    user = _user("leo")
    client.force_authenticate(user=user)
    response = client.post("/api/auth/tokens/", {"name": "cli"}, format="json")
    assert response.status_code == 201
    plaintext = response.json()["token"]
    assert plaintext.startswith("rag_")
    token = ApiToken.objects.get(user=user, name="cli")
    assert token.token_hash == hash_token(plaintext)
    assert plaintext not in token.token_hash
    listing = client.get("/api/auth/tokens/")
    assert all("token" not in entry and "token_hash" not in entry for entry in listing.json())


def test_bearer_token_reaches_documents():
    """A documents:read token lists the owner's documents."""
    user = _user("leo")
    _, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    response = _bearer_call(plaintext, "get", "/api/documents/")
    assert response.status_code == 200


def test_token_cannot_upload_without_write_scope():
    """A read-only token gets 403 on upload."""

    from django.core.files.uploadedfile import SimpleUploadedFile

    user = _user("leo")
    _, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    response = _bearer_call(
        plaintext,
        "post",
        "/api/documents/",
        {"file": SimpleUploadedFile("kb.txt", b"content", content_type="text/plain")},
        format="multipart",
    )
    assert response.status_code == 403


def test_token_cannot_query_without_query_scope():
    """A token without the query scope gets 403 on the chat endpoint."""
    user = _user("leo")
    _, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    response = _bearer_call(plaintext, "post", "/api/query/", {"question": "hi"}, format="json")
    assert response.status_code == 403


def test_paused_token_rejected_immediately():
    """A paused token stops authenticating immediately."""
    user = _user("leo")
    token, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    assert _bearer_call(plaintext, "get", "/api/documents/").status_code == 200
    token.is_active = False
    token.save(update_fields=["is_active"])
    assert _bearer_call(plaintext, "get", "/api/documents/").status_code == 403


def test_revoked_token_rejected_immediately():
    """A deleted token stops authenticating immediately."""
    user = _user("leo")
    token, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    token.delete()
    assert _bearer_call(plaintext, "get", "/api/documents/").status_code == 403


def test_last_used_tracked():
    """A successful authentication updates last_used_at."""
    user = _user("leo")
    token, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    assert token.last_used_at is None
    _bearer_call(plaintext, "get", "/api/documents/")
    token.refresh_from_db()
    assert token.last_used_at is not None


def test_blocked_user_tokens_rejected():
    """Blocking a user immediately rejects their tokens."""
    user = _user("leo")
    _, plaintext = _make_token(user, [Scope.DOCUMENTS_READ])
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert _bearer_call(plaintext, "get", "/api/documents/").status_code == 403


def test_tokens_scoped_to_owner():
    """A token acts as its owner: only their documents are visible."""
    from documents.models import Document

    leo = _user("leo")
    alice = _user("alice")
    Document.objects.create(
        original_filename="leo.pdf",
        storage_path="uploads/leo.pdf",
        mime_type="application/pdf",
        size_bytes=10,
        owner=leo,
    )
    _, plaintext = _make_token(alice, [Scope.DOCUMENTS_READ])
    response = _bearer_call(plaintext, "get", "/api/documents/")
    assert response.status_code == 200
    assert response.json() == []


def test_token_cannot_manage_tokens():
    """A Bearer token cannot create, pause or delete tokens."""
    user = _user("leo")
    _, plaintext = _make_token(user, [Scope.QUERY])
    response = _bearer_call(plaintext, "post", "/api/auth/tokens/", {"name": "evil"}, format="json")
    assert response.status_code == 400
    token = ApiToken.objects.get(user=user)
    response = _bearer_call(plaintext, "patch", f"/api/auth/tokens/{token.pk}/", {}, format="json")
    assert response.status_code == 400
    response = _bearer_call(plaintext, "delete", f"/api/auth/tokens/{token.pk}/")
    assert response.status_code == 400


def test_owner_can_pause_and_revoke():
    """The token owner pauses, resumes and revokes their tokens."""
    user = _user("leo")
    client.force_authenticate(user=user)
    token = ApiToken.objects.create(
        user=user, name="cli", token_hash=hash_token("rag_x"), scopes=["query"]
    )
    response = client.patch(f"/api/auth/tokens/{token.pk}/", {"is_active": False}, format="json")
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    response = client.delete(f"/api/auth/tokens/{token.pk}/")
    assert response.status_code == 204
    assert not ApiToken.objects.filter(pk=token.pk).exists()


def test_invalid_scopes_rejected():
    """Unknown scopes are refused at creation."""
    user = _user("leo")
    client.force_authenticate(user=user)
    response = client.post("/api/auth/tokens/", {"name": "bad", "scopes": ["admin"]}, format="json")
    assert response.status_code == 400
    assert "admin" in response.json()["detail"]
