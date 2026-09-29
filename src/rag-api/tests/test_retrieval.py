"""Tests for pgvector top-k cosine similarity retrieval."""

import pytest

from documents.models import Chunk, Document
from documents.retrieval import search_similar_chunks

pytestmark = pytest.mark.django_db

EMBEDDING_DIMENSIONS = 1024


def _vector(unit_index):
    """Build a 1024-dimension one-hot vector with 1.0 at the given index."""
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[unit_index] = 1.0
    return vector


@pytest.fixture
def document():
    """Create a document holding the chunks used by the retrieval tests."""
    return Document.objects.create(
        original_filename="vectors.txt",
        storage_path="uploads/vectors.txt",
        mime_type="text/plain",
        size_bytes=10,
    )


def _make_chunk(document, ordinal, content, vector):
    """Create a chunk with the given embedding vector."""
    return Chunk.objects.create(
        document=document, ordinal=ordinal, content=content, embedding=vector
    )


def test_search_returns_nearest_chunks_first(document):
    """The closest vectors by cosine distance come back first."""
    _make_chunk(document, 0, "near", _vector(0))
    _make_chunk(document, 1, "orthogonal", _vector(1))
    _make_chunk(document, 2, "opposite", [-value for value in _vector(0)])

    results = search_similar_chunks(_vector(0), top_k=3)

    assert [chunk.content for chunk in results] == ["near", "orthogonal", "opposite"]


def test_search_respects_top_k(document):
    """Only the top_k closest chunks are returned."""
    for ordinal in range(5):
        vector = [0.0] * EMBEDDING_DIMENSIONS
        vector[0] = 1.0
        vector[ordinal] = 1.0
        _make_chunk(document, ordinal, f"chunk {ordinal}", vector)

    results = search_similar_chunks(_vector(0), top_k=2)

    assert len(results) == 2
    assert results[0].content == "chunk 0"
    assert results[1].content == "chunk 1"


def test_search_skips_chunks_without_embedding(document):
    """Chunks whose embedding is still pending are excluded."""
    _make_chunk(document, 0, "embedded", _vector(0))
    Chunk.objects.create(document=document, ordinal=1, content="not yet embedded")

    results = search_similar_chunks(_vector(0), top_k=5)

    assert [chunk.content for chunk in results] == ["embedded"]


def test_search_with_no_matches_returns_empty_list():
    """A query against an empty knowledge base returns an empty list."""
    assert search_similar_chunks(_vector(0), top_k=3) == []
