"""Tests for deterministic text chunking."""

import pytest

from ingestion.chunking import split_text


def test_empty_text_yields_no_chunks():
    """An empty or blank input produces an empty chunk list."""
    assert split_text("") == []
    assert split_text("   \n\n  ") == []


def test_single_word_file_yields_one_chunk():
    """A single-word file produces exactly one chunk."""
    chunks = split_text("hello")
    assert chunks == ["hello"]


def test_paragraphs_are_packed_up_to_max_size():
    """Small paragraphs are packed together up to the max size."""
    text = "AAAA.\n\nBBBB.\n\nCCCC."
    chunks = split_text(text, max_chunk_size=10)
    assert all(len(chunk) <= 10 for chunk in chunks)
    assert "".join(chunks) == "AAAA.BBBB.CCCC."


def test_long_paragraph_is_hard_split():
    """A paragraph longer than the max is split at sentence boundaries."""
    text = "One sentence here. " * 20
    chunks = split_text(text, max_chunk_size=50)
    assert all(len(chunk) <= 50 for chunk in chunks)
    assert chunks[0].endswith(".")


def test_chunking_is_deterministic():
    """The same input always produces the same chunks."""
    text = "First paragraph.\n\nSecond paragraph with more words.\n\nThird."
    assert split_text(text, max_chunk_size=40) == split_text(text, max_chunk_size=40)


def test_chunk_order_matches_text_order():
    """Chunks come back in the order of the input text."""
    text = "alpha\n\nbeta\n\ngamma"
    chunks = split_text(text, max_chunk_size=6)
    assert chunks == ["alpha", "beta", "gamma"]


def test_invalid_max_size_raises():
    """A non-positive max size is rejected."""
    with pytest.raises(ValueError, match="positive"):
        split_text("text", max_chunk_size=0)
