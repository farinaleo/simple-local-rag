"""Access control tests: per-user scoping and document sharing."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from documents.models import Chunk, Document, DocumentVisibility
from tests.fakes import FakeEmbeddingModel

pytestmark = pytest.mark.django_db

client = APIClient()


def _user(username):
    """Create a user with a password and return it."""
    return User.objects.create_user(username=username, password="password123")


def _document(owner, visibility=DocumentVisibility.PRIVATE, name="doc.pdf"):
    """Create an indexed document owned by a user."""
    document = Document.objects.create(
        original_filename=name,
        storage_path=f"uploads/{name}",
        mime_type="application/pdf",
        size_bytes=10,
        owner=owner,
        visibility=visibility,
    )
    Chunk.objects.create(document=document, ordinal=0, content="chunk text")
    return document


@pytest.fixture(autouse=True)
def fake_embedding(monkeypatch):
    """Deterministic embedding double for retrieval calls."""
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr(
        "rag_core.retriever.embedding_module.get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )
    yield


def test_register_login_and_me_flow():
    """Register opens a session; me returns the logged-in user."""
    response = client.post(
        "/api/auth/register/",
        {"username": "leo", "password": "password123"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["username"] == "leo"

    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["username"] == "leo"

    logout = client.post("/api/auth/logout/")
    assert logout.status_code == 204

    me_after = client.get("/api/auth/me/")
    assert me_after.status_code == 403


def test_login_rejects_invalid_credentials():
    """Login with a wrong password returns 400."""
    _user("alice")
    response = client.post(
        "/api/auth/login/",
        {"username": "alice", "password": "wrong"},
        format="json",
    )
    assert response.status_code == 400


def test_document_list_scoped_per_user():
    """A user only sees their own documents plus shared ones."""
    alice, bob = _user("alice"), _user("bob")
    _document(alice, name="alice-private.pdf")
    _document(bob, name="bob-private.pdf")
    _document(bob, DocumentVisibility.SHARED, name="bob-shared.pdf")

    client.force_login(alice)
    response = client.get("/api/documents/")
    names = {document["original_filename"] for document in response.json()}
    assert names == {"alice-private.pdf", "bob-shared.pdf"}


def test_document_detail_hidden_from_other_users():
    """A private document detail returns 404 for another user."""
    alice, bob = _user("alice"), _user("bob")
    document = _document(bob, name="bob-private.pdf")

    client.force_login(alice)
    response = client.get(f"/api/documents/{document.pk}/")
    assert response.status_code == 404


def test_shared_document_detail_readable_by_others():
    """A shared document detail is readable by any logged-in user."""
    alice, bob = _user("alice"), _user("bob")
    document = _document(bob, DocumentVisibility.SHARED, name="bob-shared.pdf")

    client.force_login(alice)
    response = client.get(f"/api/documents/{document.pk}/")
    assert response.status_code == 200


def test_delete_only_by_owner():
    """Deleting another user's document returns 404 and keeps the row."""
    alice, bob = _user("alice"), _user("bob")
    document = _document(bob, name="bob-private.pdf")

    client.force_login(alice)
    response = client.delete(f"/api/documents/{document.pk}/")
    assert response.status_code == 404
    assert Document.objects.filter(pk=document.pk).exists()


def test_visibility_toggle_by_owner_only():
    """Only the owner can toggle visibility; the value must be valid."""
    alice, bob = _user("alice"), _user("bob")
    document = _document(bob, name="bob-private.pdf")

    client.force_login(alice)
    response = client.patch(
        f"/api/documents/{document.pk}/", {"visibility": "shared"}, format="json"
    )
    assert response.status_code == 404

    client.force_login(bob)
    response = client.patch(
        f"/api/documents/{document.pk}/", {"visibility": "shared"}, format="json"
    )
    assert response.status_code == 200
    document.refresh_from_db()
    assert document.visibility == DocumentVisibility.SHARED

    invalid = client.patch(
        f"/api/documents/{document.pk}/", {"visibility": "public"}, format="json"
    )
    assert invalid.status_code == 400


def test_query_history_scoped_per_user():
    """The history endpoint only returns the user's own exchanges."""
    from documents.models import Query

    alice, bob = _user("alice"), _user("bob")
    Query.objects.create(question="alice question", answer="a", user=alice)
    Query.objects.create(question="bob question", answer="b", user=bob)

    client.force_login(alice)
    response = client.get("/api/query/history/")
    questions = [item["question"] for item in response.json()]
    assert questions == ["alice question"]


def test_anonymous_access_keeps_working():
    """Anonymous users still see everything (auth off by default)."""
    response = client.get("/api/documents/")
    assert response.status_code == 200
