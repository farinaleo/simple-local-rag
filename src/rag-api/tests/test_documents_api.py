"""Tests for the documents REST API: upload, list, detail, delete."""

import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from documents.models import Chunk, Document

pytestmark = pytest.mark.django_db

client = APIClient()


def _make_file(name, content=b"knowledge base content", content_type="text/plain"):
    """Build an uploaded file payload for the multipart POST."""
    return SimpleUploadedFile(name, content, content_type=content_type)


@pytest.fixture(autouse=True)
def eager_celery(settings, monkeypatch, tmp_path):
    """Run ingestion eagerly with a fake embedding model and temp uploads."""
    from tests.fakes import FakeEmbeddingModel

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def test_upload_returns_202_and_triggers_ingestion():
    """An accepted upload returns 202 and reaches indexed status."""
    response = client.post("/api/documents/", {"file": _make_file("kb.txt")}, format="multipart")

    assert response.status_code == 202
    document_id = response.json()["id"]
    document = Document.objects.get(pk=document_id)
    assert document.status == "indexed"
    assert document.chunks.count() >= 1
    assert os.path.exists(document.storage_path)


@pytest.mark.parametrize(
    "filename",
    ["kb.txt", "kb.md", "kb.pdf", "kb.docx"],
)
def test_upload_accepts_each_format(filename):
    """Every accepted format returns 202."""
    response = client.post("/api/documents/", {"file": _make_file(filename)}, format="multipart")

    assert response.status_code == 202


def test_upload_rejects_unsupported_format():
    """An unsupported upload returns 400 with a clear message."""
    response = client.post(
        "/api/documents/",
        {"file": _make_file("archive.zip", b"PK\x03\x04", "application/zip")},
        format="multipart",
    )

    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"]


def test_upload_without_file_returns_400():
    """A POST without a file part is rejected."""
    response = client.post("/api/documents/", {}, format="multipart")

    assert response.status_code == 400


def test_list_returns_documents_newest_first():
    """The list endpoint returns name, size, status and timestamps."""
    Document.objects.create(
        original_filename="a.txt",
        storage_path="uploads/a.txt",
        mime_type="text/plain",
        size_bytes=1,
    )
    Document.objects.create(
        original_filename="b.txt",
        storage_path="uploads/b.txt",
        mime_type="text/plain",
        size_bytes=2,
    )

    response = client.get("/api/documents/")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert results[0]["original_filename"] == "b.txt"
    assert {"id", "original_filename", "size_bytes", "status", "created_at"} <= set(results[0])


def test_detail_includes_chunks():
    """The detail endpoint includes the document chunks."""
    document = Document.objects.create(
        original_filename="c.txt",
        storage_path="uploads/c.txt",
        mime_type="text/plain",
        size_bytes=3,
    )
    Chunk.objects.create(document=document, ordinal=0, content="chunk zero")

    response = client.get(f"/api/documents/{document.pk}/")

    assert response.status_code == 200
    body = response.json()
    assert body["original_filename"] == "c.txt"
    assert len(body["chunks"]) == 1
    assert body["chunks"][0]["content"] == "chunk zero"


def test_delete_is_atomic_and_removes_file(tmp_path):
    """Deletion removes row, chunks and stored file together."""
    response = client.post("/api/documents/", {"file": _make_file("d.txt")}, format="multipart")
    document_id = response.json()["id"]
    document = Document.objects.get(pk=document_id)
    stored_path = document.storage_path
    assert os.path.exists(stored_path)
    chunk_count = document.chunks.count()
    assert chunk_count >= 1

    response = client.delete(f"/api/documents/{document_id}/")

    assert response.status_code == 204
    assert not Document.objects.filter(pk=document_id).exists()
    assert not Chunk.objects.filter(document_id=document_id).exists()
    assert not os.path.exists(stored_path)


def test_delete_missing_returns_404():
    """Deleting an unknown document returns 404."""
    response = client.delete("/api/documents/999999/")

    assert response.status_code == 404
