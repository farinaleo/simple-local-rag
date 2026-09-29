"""Deterministic text chunking with a configurable maximum size."""

import os

DEFAULT_CHUNK_SIZE = 500


def split_text(text, max_chunk_size=None):
    """Split text into deterministic chunks.

    Splits on blank lines (paragraphs), then on sentence boundaries,
    packing pieces up to ``max_chunk_size`` characters. A single piece
    longer than the maximum is hard-split at the boundary — the output
    is deterministic for a given input.

    Args:
        text: The plain text to chunk.
        max_chunk_size: Maximum characters per chunk (defaults to the
            ``CHUNK_SIZE`` environment variable or 500).

    Returns:
        The list of chunks (possibly empty for blank input).
    """
    if max_chunk_size is None:
        max_chunk_size = int(os.environ.get("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)))
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be positive")

    text = text.strip()
    if not text:
        return []

    chunks = []
    current = ""
    for paragraph in _split_paragraphs(text, max_chunk_size):
        if not current:
            current = paragraph
        elif len(current) + 1 + len(paragraph) <= max_chunk_size:
            current = f"{current}\n{paragraph}"
        else:
            chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def _split_paragraphs(text, max_chunk_size):
    """Yield paragraphs, hard-splitting any paragraph over the maximum.

    Args:
        text: The stripped, non-empty text.
        max_chunk_size: Maximum characters per yielded piece.

    Yields:
        Paragraph pieces, each at most ``max_chunk_size`` characters.
    """
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        while len(paragraph) > max_chunk_size:
            boundary = _last_sentence_boundary(paragraph, max_chunk_size)
            if boundary <= 0:
                boundary = max_chunk_size
            yield paragraph[:boundary].strip()
            paragraph = paragraph[boundary:].lstrip()
        if paragraph:
            yield paragraph


def _last_sentence_boundary(text, limit):
    """Find the latest sentence-ending position within a limit.

    Args:
        text: The text to scan.
        limit: Maximum position to consider.

    Returns:
        The index just after the latest `.`, `!` or `?` within the
        limit, or 0 when none is found.
    """
    best = 0
    for index, char in enumerate(text[:limit]):
        if char in ".!?":
            best = index + 1
    return best
