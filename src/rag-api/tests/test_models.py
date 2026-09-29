"""Tests for the documents, chunks and query models."""

import pytest
from django.db import IntegrityError

from documents.models import Chunk, Document, DocumentStatus, Query

pytestmark = pytest.mark.django_db


@pytest.fixture
def document():
    """Create a pending document used by the status-transition tests."""
    return Document.objects.create(
        original_filename="demo.txt",
        storage_path="uploads/demo.txt",
        mime_type="text/plain",
        size_bytes=1234,
    )


def test_document_defaults_to_pending(document):
    """A new document starts in the pending status with no error."""
    assert document.status == DocumentStatus.PENDING
    assert document.error_message is None
    assert str(document) == "demo.txt"


def test_document_transition_to_indexed(document):
    """mark_processing then mark_indexed closes a successful ingestion."""
    document.mark_processing()
    document.refresh_from_db()
    assert document.status == DocumentStatus.PROCESSING

    document.mark_indexed()
    document.refresh_from_db()
    assert document.status == DocumentStatus.INDEXED


def test_document_transition_to_failed(document):
    """mark_failed stores the error message and the failed status."""
    document.mark_processing()
    document.mark_failed("boom: unreadable pdf")

    document.refresh_from_db()
    assert document.status == DocumentStatus.FAILED
    assert document.error_message == "boom: unreadable pdf"


def test_mark_indexed_clears_previous_error(document):
    """A successful ingestion clears an error from a previous failure."""
    document.mark_failed("first attempt failed")
    document.mark_indexed()

    document.refresh_from_db()
    assert document.status == DocumentStatus.INDEXED
    assert document.error_message is None


def test_chunk_ordinal_is_unique_per_document(document):
    """Two chunks of a document cannot share the same ordinal."""
    Chunk.objects.create(document=document, ordinal=0, content="first chunk")
    with pytest.raises(IntegrityError):
        Chunk.objects.create(document=document, ordinal=0, content="duplicate")


def test_chunks_are_ordered_by_ordinal(document):
    """Chunk querysets come back ordered by document then ordinal."""
    Chunk.objects.create(document=document, ordinal=1, content="second")
    Chunk.objects.create(document=document, ordinal=0, content="first")

    ordinals = [chunk.ordinal for chunk in Chunk.objects.all()]
    assert ordinals == [0, 1]


def test_document_deletion_cascades_to_chunks(document):
    """Deleting a document deletes its chunks atomically."""
    Chunk.objects.create(document=document, ordinal=0, content="gone with it")

    document.delete()

    assert Chunk.objects.count() == 0


def test_query_sources_link_to_chunks(document):
    """A query references chunks as its sources for the history feature."""
    chunk = Chunk.objects.create(document=document, ordinal=0, content="source text")
    query = Query.objects.create(question="What?", answer="Because.")

    query.sources.add(chunk)
    query.refresh_from_db()

    assert list(query.sources.all()) == [chunk]
    assert str(query) == "What?"
