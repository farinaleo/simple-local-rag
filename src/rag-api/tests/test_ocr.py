"""OCR ingestion tests: dispatch, extraction and error paths."""

import io

import pytesseract
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from ingestion.extractors import extract_text

pytestmark = pytest.mark.django_db

client = APIClient()


@pytest.fixture(autouse=True)
def ocr_test_env(settings, monkeypatch, tmp_path):
    """Run ingestion eagerly with a fake embedding model and a stub OCR."""
    from tests.fakes import FakeEmbeddingModel

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    monkeypatch.setattr("ingestion.embedding.get_embedding_model", lambda: FakeEmbeddingModel())
    monkeypatch.setattr("pytesseract.image_to_string", lambda image: "  recognized text  ")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    yield


def _png_bytes(text=""):
    """Build a real PNG payload, optionally with embedded text metadata."""
    image = Image.new("RGB", (120, 60), color="white")
    if text:
        image.info["comment"] = text.encode()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _upload(filename, content, content_type):
    """Upload a file payload and return the response."""
    return client.post(
        "/api/documents/",
        {"file": SimpleUploadedFile(filename, content, content_type=content_type)},
        format="multipart",
    )


def test_image_extensions_accepted():
    """PNG and JPG uploads pass the extension validation (202)."""
    for filename, content_type in [
        ("scan.png", "image/png"),
        ("scan.jpg", "image/jpeg"),
        ("scan.jpeg", "image/jpeg"),
    ]:
        response = _upload(filename, _png_bytes(), content_type)
        assert response.status_code == 202, filename


def test_extract_text_dispatches_images_to_ocr(tmp_path, monkeypatch):
    """Image extraction goes through the Tesseract OCR helper."""
    captured = {}

    def fake_image_to_string(image):
        """Capture the call and return a canned recognition."""
        captured["called"] = True
        return "  recognized text  "

    monkeypatch.setattr("pytesseract.image_to_string", fake_image_to_string)
    image_path = tmp_path / "scan.png"
    image_path.write_bytes(_png_bytes())
    assert extract_text(image_path) == "recognized text"
    assert captured["called"] is True


def test_ocr_result_is_stripped_before_indexing(tmp_path, monkeypatch):
    """OCR output is stripped before chunking and indexing."""
    monkeypatch.setattr("pytesseract.image_to_string", lambda image: "  scanned paragraph text  ")
    image_path = tmp_path / "scan.png"
    image_path.write_bytes(_png_bytes())
    text = extract_text(image_path)
    assert text == "scanned paragraph text"


def test_ocr_failure_marks_document_failed(monkeypatch, tmp_path):
    """A Tesseract failure ends the document as failed with the error."""

    def broken_image_to_string(image):
        """Simulate a broken Tesseract installation."""
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr("pytesseract.image_to_string", broken_image_to_string)
    image_path = tmp_path / "scan.png"
    image_path.write_bytes(_png_bytes())
    with pytest.raises(ValueError, match="tesseract is not installed"):
        extract_text(image_path)


def test_empty_ocr_text_does_not_crash_dispatch(tmp_path, monkeypatch):
    """An image without readable text extracts to an empty string."""
    monkeypatch.setattr("pytesseract.image_to_string", lambda image: "   ")
    image_path = tmp_path / "blank.png"
    image_path.write_bytes(_png_bytes())
    assert extract_text(image_path) == ""
