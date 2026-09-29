"""Tests for the ingestion Celery task, in eager mode."""

import pytest

from documents.models import Document, DocumentStatus
from ingestion.tasks import ingest_document
from tests.fakes import FakeEmbeddingModel

pytestmark = pytest.mark.django_db


@pytest.fixture
def eager_celery(settings):
    """Run Celery tasks synchronously in tests."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture
def document(tmp_path):
    """Create a pending document backed by a real stored file."""
    stored = tmp_path / "sample.txt"
    stored.write_text("Some knowledge base content.")
    return Document.objects.create(
        original_filename="sample.txt",
        storage_path=str(stored),
        mime_type="text/plain",
        size_bytes=stored.stat().st_size,
    )


def test_ingest_document_reaches_indexed(eager_celery, document, monkeypatch):
    """A healthy document transitions processing then indexed."""
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    result = ingest_document.delay(document.pk)

    document.refresh_from_db()
    assert result.result == "indexed"
    assert document.status == DocumentStatus.INDEXED


def test_ingest_document_marks_failed_on_error(eager_celery, document, monkeypatch):
    """A failing pipeline leaves the row failed with the error stored."""
    monkeypatch.setattr(
        "ingestion.tasks._run_ingestion_pipeline",
        lambda doc: (_ for _ in ()).throw(RuntimeError("unreadable pdf")),
    )

    result = ingest_document.delay(document.pk)

    document.refresh_from_db()
    assert result.result == "failed"
    assert document.status == DocumentStatus.FAILED
    assert "unreadable pdf" in document.error_message


def test_ingest_document_missing_document(eager_celery):
    """Ingesting an unknown id reports missing without crashing."""
    result = ingest_document.delay(999999)
    assert result.result == "missing"
