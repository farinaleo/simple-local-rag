"""Celery tasks for document ingestion: extraction, chunking, embedding."""

import logging

from celery import shared_task
from django.db import transaction

from documents.models import Chunk, Document
from ingestion.chunking import split_text
from ingestion.extractors import extract_text

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def ingest_document(self, document_id):
    """Process a document asynchronously through the ingestion pipeline.

    Transitions the document to ``processing`` on start, then
    ``indexed`` on success or ``failed`` (error stored on the row) on
    error. Runs after the upload response has already returned (202).

    Args:
        self: The bound task instance (retry control).
        document_id: Primary key of the Document to ingest.

    Returns:
        The document status after processing ("indexed" or "failed").
    """
    try:
        document = Document.objects.get(pk=document_id)
    except Document.DoesNotExist:
        logger.error("ingest_document: document %s does not exist", document_id)
        return "missing"

    document.mark_processing()

    try:
        _run_ingestion_pipeline(document)
    except Exception as error:  # noqa: BLE001 — any failure marks the row
        logger.exception("ingest_document: document %s failed", document_id)
        document.mark_failed(str(error))
        return "failed"

    document.mark_indexed()
    logger.info("ingest_document: document %s indexed", document_id)
    return "indexed"


def _run_ingestion_pipeline(document):
    """Run the ingestion stages for a document.

    Extracts the text, chunks it, embeds the chunks and replaces the
    document chunks (and their vectors) atomically — re-ingesting an
    existing document leaves no orphan chunks.

    Args:
        document: The Document currently in ``processing`` status.

    Raises:
        ValueError: On an unsupported file type.
        OSError: On an unreadable or missing file.
    """
    text = extract_text(document.storage_path)
    chunks = split_text(text)

    with transaction.atomic():
        document.chunks.all().delete()
        Chunk.objects.bulk_create(
            Chunk(
                document=document,
                ordinal=ordinal,
                content=content,
                embedding=_embed_chunk(content),
            )
            for ordinal, content in enumerate(chunks)
        )


def _embed_chunk(content):
    """Compute the embedding vector of a chunk.

    Uses the Qwen3-Embedding-0.6B model via sentence-transformers,
    following the proven POC setup. The model is loaded once per
    worker process.

    Args:
        content: The chunk text.

    Returns:
        The embedding as a list of floats (1024 dimensions).
    """
    from ingestion.embedding import get_embedding_model

    model = get_embedding_model()
    vector = model.encode(content, normalize_embeddings=True)
    return list(vector)
