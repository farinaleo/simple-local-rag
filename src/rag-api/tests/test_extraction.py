"""Tests for text extraction from the four accepted formats."""

from pathlib import Path

import pytest

from ingestion.extractors import ALLOWED_EXTENSIONS, extract_text

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_allowed_extensions_are_txt_md_pdf_docx():
    """The accepted formats match the v2 decision."""
    assert ALLOWED_EXTENSIONS == {".txt", ".md", ".pdf", ".docx"}


def test_extract_txt():
    """Plain text files are read natively."""
    text = extract_text(FIXTURES_DIR / "sample.txt")
    assert "Eiffel Tower" in text
    assert "wrought iron" in text


def test_extract_md_strips_markup():
    """Markdown is reduced to plain text."""
    text = extract_text(FIXTURES_DIR / "sample.md")
    assert "Demo" in text
    assert "**" not in text
    assert "[" not in text


def test_extract_pdf():
    """PDF text is extracted with pypdf."""
    text = extract_text(FIXTURES_DIR / "sample.pdf")
    assert "Eiffel Tower facts" in text


def test_extract_docx():
    """DOCX paragraphs are extracted with python-docx."""
    text = extract_text(FIXTURES_DIR / "sample.docx")
    assert "Eiffel Tower" in text
    assert "1889" in text


def test_extract_rejects_unsupported_extension(tmp_path):
    """Unsupported formats raise a clear error."""
    file_path = tmp_path / "photo.png"
    file_path.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError, match="unsupported file type"):
        extract_text(file_path)


def test_extract_missing_file_raises(tmp_path):
    """A missing txt file raises (surfaces as ingestion failure)."""
    with pytest.raises(FileNotFoundError):
        extract_text(tmp_path / "ghost.txt")
