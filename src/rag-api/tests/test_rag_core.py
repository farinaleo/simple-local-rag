"""Tests for the rag_core service: retrieval and generation paths."""

import pytest

from documents.models import Chunk, Document
from rag_core.generator import build_messages
from rag_core.indexer import index_document
from rag_core.retriever import retrieve_chunks
from tests.fakes import FakeEmbeddingModel

pytestmark = pytest.mark.django_db


@pytest.fixture
def document(tmp_path):
    """Create a document backed by a real stored file."""
    stored = tmp_path / "kb.txt"
    stored.write_text("The Eiffel Tower is in Paris.")
    return Document.objects.create(
        original_filename="kb.txt",
        storage_path=str(stored),
        mime_type="text/plain",
        size_bytes=stored.stat().st_size,
    )


def test_index_document_creates_chunks(document, monkeypatch):
    """index_document runs the pipeline and creates embedded chunks."""
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    index_document(document)

    assert document.chunks.count() == 1
    assert document.chunks.first().embedding is not None


def test_retrieve_chunks_returns_closest_first(document, monkeypatch):
    """retrieve_chunks embeds the question and ranks chunks by distance."""
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    index_document(document)

    results = retrieve_chunks("Where is the Eiffel Tower?")

    assert len(results) == 1
    chunk = results[0]
    assert isinstance(chunk, Chunk)
    assert "Eiffel Tower" in chunk.content


def test_build_messages_grounded_prompt():
    """The prompt embeds the numbered context and the question."""
    messages = build_messages("What color?", ["The sky is blue.", "Grass is green."])

    assert len(messages) == 1
    content = messages[0]["content"]
    assert "[1] The sky is blue." in content
    assert "[2] Grass is green." in content
    assert "Question: What color?" in content
    assert messages[0]["role"] == "user"
