"""Tests for the query API: SSE streaming and history."""

import json

import pytest
from rest_framework.test import APIClient

from documents.models import Chunk, Document, Query
from tests.fakes import FakeEmbeddingModel

pytestmark = pytest.mark.django_db

client = APIClient()


@pytest.fixture
def indexed_document():
    """Create a document with one chunk to be retrieved as a source."""
    document = Document.objects.create(
        original_filename="kb.txt",
        storage_path="uploads/kb.txt",
        mime_type="text/plain",
        size_bytes=10,
        status="indexed",
    )
    Chunk.objects.create(document=document, ordinal=0, content="The tower is tall.")
    return document


def _parse_sse(response):
    """Parse a StreamingHttpResponse into (event, data) pairs."""
    events = []
    for part in response.streaming_content:
        text = part.decode() if isinstance(part, bytes) else part
        for block in text.split("\n\n"):
            if not block.strip():
                continue
            lines = block.strip().split("\n")
            event = lines[0].removeprefix("event: ")
            data = json.loads(lines[1].removeprefix("data: "))
            events.append((event, data))
    return events


def test_query_streams_tokens_then_sources(indexed_document, monkeypatch):
    """The answer streams as token events, sources come last."""
    monkeypatch.setattr(
        "queries.views.retrieve_chunks",
        lambda question, **kw: [
            indexed_document.chunks.first(),
        ],
    )
    monkeypatch.setattr(
        "queries.views.generate_answer",
        lambda question, texts: ("", "The tower is tall and made of iron."),
    )

    response = client.post("/api/query/", {"question": "How tall?"}, format="json")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/event-stream")
    events = _parse_sse(response)
    names = [name for name, _data in events]
    assert names[0] == "token"
    assert names[-1] == "sources"
    assert "token" in names

    tokens = "".join(data["text"] for name, data in events if name == "token")
    assert tokens.strip() == "The tower is tall and made of iron."

    sources_payload = events[-1][1]
    assert sources_payload["query_id"] == Query.objects.first().pk
    assert sources_payload["sources"][0]["content"] == "The tower is tall."
    assert sources_payload["sources"][0]["document"]["original_filename"] == "kb.txt"


def test_query_persists_answer_with_sources(indexed_document, monkeypatch):
    """A successful query is persisted with its chunk sources."""
    monkeypatch.setattr(
        "queries.views.retrieve_chunks",
        lambda question, **kw: [
            indexed_document.chunks.first(),
        ],
    )
    monkeypatch.setattr(
        "queries.views.generate_answer",
        lambda question, texts: ("", "Short grounded answer."),
    )

    response = client.post("/api/query/", {"question": "How tall?"}, format="json")
    list(response.streaming_content)  # consume the SSE stream to completion

    query = Query.objects.get()
    assert query.question == "How tall?"
    assert query.answer == "Short grounded answer."
    assert list(query.sources.all()) == [indexed_document.chunks.first()]


def test_failed_generation_records_query_and_streams_error(monkeypatch):
    """A failed generation emits an error event and records the failure."""

    def _boom(question, texts):
        raise RuntimeError("model exploded")

    monkeypatch.setattr("queries.views.retrieve_chunks", lambda question, **kw: [])
    monkeypatch.setattr("queries.views.generate_answer", _boom)

    response = client.post("/api/query/", {"question": "Anything?"}, format="json")

    assert response.status_code == 200
    events = _parse_sse(response)
    assert events[0][0] == "error"
    assert events[0][1]["detail"] == "generation failed"
    query = Query.objects.get()
    assert query.question == "Anything?"
    assert "[generation failed]" in query.answer


def test_query_without_question_returns_400():
    """A missing or blank question is rejected."""
    response = client.post("/api/query/", {"question": ""}, format="json")
    assert response.status_code == 400

    response = client.post("/api/query/", {}, format="json")
    assert response.status_code == 400


def test_history_returns_queries_newest_first(indexed_document):
    """The history endpoint returns past exchanges newest-first."""
    old_query = Query.objects.create(question="old?", answer="old answer.")
    new_query = Query.objects.create(question="new?", answer="new answer.")
    old_query.sources.set([indexed_document.chunks.first()])
    new_query.sources.set([indexed_document.chunks.first()])

    response = client.get("/api/query/history/")

    assert response.status_code == 200
    results = response.json()
    assert [entry["question"] for entry in results] == ["new?", "old?"]
    assert results[0]["sources"][0]["content"] == "The tower is tall."


def test_query_uses_real_retriever_contract(indexed_document, monkeypatch):
    """The view consumes retrieve_chunks output without tuple unpacking.

    Guards the integration between queries.views and rag_core.retriever:
    retrieve_chunks returns a list of chunks, not (chunk, distance) pairs.
    """
    chunk = indexed_document.chunks.first()
    chunk.embedding = [0.0] * 1024
    chunk.embedding[len("How tall?") % 1024] = 1.0
    chunk.save()
    monkeypatch.setattr(
        "ingestion.embedding.get_embedding_model",
        lambda: FakeEmbeddingModel(),
    )
    monkeypatch.setattr(
        "queries.views.generate_answer",
        lambda question, texts: ("", "Grounded answer."),
    )

    response = client.post("/api/query/", {"question": "How tall?"}, format="json")

    assert response.status_code == 200
    events = _parse_sse(response)
    assert events[-1][0] == "sources"
    assert events[-1][1]["sources"][0]["content"] == "The tower is tall."
