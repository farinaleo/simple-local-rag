"""Tests for the conversation API: listing, detail, deletion, scoping."""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from documents.models import Conversation, Query, build_conversation_title

pytestmark = pytest.mark.django_db

client = APIClient()


def _make_conversation(owner=None, title="Discussion"):
    """Create a conversation row for tests."""
    return Conversation.objects.create(owner=owner, title=title)


def _make_query(conversation, question, answer):
    """Create a past exchange on a conversation."""
    return Query.objects.create(conversation=conversation, question=question, answer=answer)


def _auth(username):
    """Create a user and return an authenticated client."""
    user = User.objects.create_user(username=username, password="password123")
    auth_client = APIClient()
    auth_client.force_authenticate(user=user)
    return user, auth_client


def test_conversation_title_is_truncated_from_the_question():
    """The title derives from the first line, truncated at 120 chars."""
    short = build_conversation_title("  Combien de documents ?  ")
    assert short == "Combien de documents ?"

    long_question = "a" * 200
    assert len(build_conversation_title(long_question)) == 120

    multiline = build_conversation_title("First line\nsecond line")
    assert multiline == "First line"


def test_conversation_list_returns_own_conversations_only():
    """Each user sees only their own conversations."""
    alice, alice_client = _auth("alice")
    bob, bob_client = _auth("bob")
    _make_conversation(owner=alice, title="Alice chat")
    _make_conversation(owner=bob, title="Bob chat")

    response = alice_client.get("/api/query/conversations/")
    assert response.status_code == 200
    titles = [entry["title"] for entry in response.json()]
    assert titles == ["Alice chat"]

    response = bob_client.get("/api/query/conversations/")
    assert [entry["title"] for entry in response.json()] == ["Bob chat"]


def test_conversation_detail_returns_messages_oldest_first():
    """The detail endpoint lists the conversation messages in order."""
    alice, alice_client = _auth("alice")
    conversation = _make_conversation(owner=alice, title="Thread")
    Query.objects.create(question="Q1", answer="A1", user=alice, conversation=conversation)
    Query.objects.create(question="Q2", answer="A2", user=alice, conversation=conversation)

    response = alice_client.get(f"/api/query/conversations/{conversation.pk}/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Thread"
    assert [message["question"] for message in payload["messages"]] == ["Q1", "Q2"]


def test_conversation_detail_scoped_to_owner():
    """A user cannot read someone else's conversation."""
    alice, _alice_client = _auth("alice")
    bob, bob_client = _auth("bob")
    conversation = _make_conversation(owner=alice, title="Private")

    response = bob_client.get(f"/api/query/conversations/{conversation.pk}/")
    assert response.status_code == 404


def test_conversation_delete_removes_messages():
    """Deleting a conversation removes its messages too."""
    alice, alice_client = _auth("alice")
    conversation = _make_conversation(owner=alice, title="To delete")
    Query.objects.create(question="Q", answer="A", user=alice, conversation=conversation)

    response = alice_client.delete(f"/api/query/conversations/{conversation.pk}/")
    assert response.status_code == 204
    assert not Conversation.objects.exists()
    assert not Query.objects.exists()


def test_conversation_delete_scoped_to_owner():
    """A user cannot delete someone else's conversation."""
    alice, _alice_client = _auth("alice")
    bob, bob_client = _auth("bob")
    conversation = _make_conversation(owner=alice, title="Private")

    response = bob_client.delete(f"/api/query/conversations/{conversation.pk}/")
    assert response.status_code == 404
    assert Conversation.objects.filter(pk=conversation.pk).exists()


def test_query_without_conversation_creates_one_titled_from_question(monkeypatch):
    """A query without conversation id starts a new titled conversation."""
    alice, alice_client = _auth("alice")
    monkeypatch.setattr("queries.views.retrieve_chunks", lambda question, **kw: [])
    monkeypatch.setattr("queries.views.generate_answer", lambda question, texts: ("", "Answer."))

    response = alice_client.post("/api/query/", {"question": "What is the tower?"}, format="json")
    assert response.status_code == 200
    list(response.streaming_content)

    conversation = Conversation.objects.get()
    assert conversation.owner == alice
    assert conversation.title == "What is the tower?"
    query = Query.objects.get()
    assert query.conversation == conversation


def test_query_with_conversation_appends_to_it(monkeypatch):
    """A query with a conversation id appends the exchange to it."""
    alice, alice_client = _auth("alice")
    conversation = _make_conversation(owner=alice, title="Existing")
    monkeypatch.setattr("queries.views.retrieve_chunks", lambda question, **kw: [])
    monkeypatch.setattr("queries.views.generate_answer", lambda question, texts: ("", "Answer."))

    response = alice_client.post(
        "/api/query/",
        {"question": "Follow up?", "conversation_id": conversation.pk},
        format="json",
    )
    assert response.status_code == 200
    list(response.streaming_content)

    assert Conversation.objects.count() == 1
    assert Query.objects.get().conversation == conversation


def test_query_passes_conversation_history_to_generator(monkeypatch):
    """The generator receives the previous exchanges of the conversation."""
    alice, alice_client = _auth("alice")
    conversation = _make_conversation(owner=alice, title="Existing")
    _make_query(conversation=conversation, question="First?", answer="First answer.")
    _make_query(conversation=conversation, question="Second?", answer="Second answer.")
    monkeypatch.setattr("queries.views.retrieve_chunks", lambda question, **kw: [])
    seen = {}

    def fake_generate_answer(question, texts, history=None):
        seen["history"] = history
        return "", "Answer."

    monkeypatch.setattr("queries.views.generate_answer", fake_generate_answer)

    response = alice_client.post(
        "/api/query/",
        {"question": "Third?", "conversation_id": conversation.pk},
        format="json",
    )
    assert response.status_code == 200
    list(response.streaming_content)

    assert seen["history"] == [
        ("First?", "First answer."),
        ("Second?", "Second answer."),
    ]


def test_query_with_foreign_conversation_is_rejected(monkeypatch):
    """A user cannot append to a conversation they do not own."""
    alice, _alice_client = _auth("alice")
    bob, bob_client = _auth("bob")
    conversation = _make_conversation(owner=alice, title="Private")
    monkeypatch.setattr("queries.views.retrieve_chunks", lambda question, **kw: [])

    response = bob_client.post(
        "/api/query/",
        {"question": "Hijack?", "conversation_id": conversation.pk},
        format="json",
    )
    assert response.status_code == 404
    assert Query.objects.count() == 0
