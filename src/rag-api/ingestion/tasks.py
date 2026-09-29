"""Celery tasks for document ingestion: status orchestration."""

import logging

from celery import shared_task

from documents.models import Document
from rag_core import indexer

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
        indexer.index_document(document)
    except Exception as error:  # noqa: BLE001 — any failure marks the row
        logger.exception("ingest_document: document %s failed", document_id)
        document.mark_failed(str(error))
        return "failed"

    document.mark_indexed()
    logger.info("ingest_document: document %s indexed", document_id)
    return "indexed"
