"""Tests for the end-to-end ingestion pipeline (embedding mocked)."""

from pathlib import Path

import pytest

from documents.models import Chunk, Document, DocumentStatus
from ingestion.tasks import ingest_document
from tests.fakes import FakeEmbeddingModel

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def eager_celery(settings, monkeypatch):
    """Run Celery tasks eagerly and stub the embedding model."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())


@pytest.fixture
def uploaded_document(tmp_path):
    """Copy the txt fixture to storage and create its Document row."""
    stored = tmp_path / "sample.txt"
    stored.write_text((FIXTURES_DIR / "sample.txt").read_text())
    return Document.objects.create(
        original_filename="sample.txt",
        storage_path=str(stored),
        mime_type="text/plain",
        size_bytes=stored.stat().st_size,
    )


def test_txt_ingestion_creates_indexed_chunks(uploaded_document):
    """A txt file goes end-to-end to indexed with embedded chunks."""
    result = ingest_document.delay(uploaded_document.pk)

    uploaded_document.refresh_from_db()
    assert result.result == "indexed"
    assert uploaded_document.status == DocumentStatus.INDEXED
    assert uploaded_document.chunks.count() > 0
    assert all(chunk.embedding is not None for chunk in uploaded_document.chunks.all())


@pytest.mark.parametrize("filename", ["sample.txt", "sample.md", "sample.docx"])
def test_each_accepted_format_ingests(tmp_path, filename):
    """Every accepted format is ingested end-to-end."""
    stored = tmp_path / filename
    stored.write_bytes((FIXTURES_DIR / filename).read_bytes())
    document = Document.objects.create(
        original_filename=filename,
        storage_path=str(stored),
        mime_type="application/octet-stream",
        size_bytes=stored.stat().st_size,
    )

    result = ingest_document.delay(document.pk)

    document.refresh_from_db()
    assert result.result == "indexed"
    assert document.chunks.count() >= 1


def test_reingestion_replaces_chunks_without_orphans(tmp_path):
    """Re-ingesting a document replaces its chunks atomically."""
    stored = tmp_path / "reingest.txt"
    stored.write_text("First version of the content.")
    document = Document.objects.create(
        original_filename="reingest.txt",
        storage_path=str(stored),
        mime_type="text/plain",
        size_bytes=stored.stat().st_size,
    )
    ingest_document.delay(document.pk)
    first_count = document.chunks.count()
    assert first_count > 0

    stored.write_text("Completely different second version with more text.")
    ingest_document.delay(document.pk)

    assert document.chunks.count() == Chunk.objects.filter(document=document).count()
    assert document.chunks.count() > 0
    orphans = Chunk.objects.filter(document=document, content__contains="First version").count()
    assert orphans == 0


def test_failed_document_marks_row(tmp_path):
    """A corrupt file leaves the row failed with the error stored."""
    stored = tmp_path / "corrupt.pdf"
    stored.write_bytes(b"not a real pdf")
    document = Document.objects.create(
        original_filename="corrupt.pdf",
        storage_path=str(stored),
        mime_type="application/pdf",
        size_bytes=stored.stat().st_size,
    )

    result = ingest_document.delay(document.pk)

    document.refresh_from_db()
    assert result.result == "failed"
    assert document.status == DocumentStatus.FAILED
    assert document.error_message
