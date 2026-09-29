"""Celery tasks for document ingestion.

The real extraction/chunking/embedding pipeline lands with the
ingestion pipeline issue; this module owns the task skeleton and the
document status transitions.
"""

import logging

from celery import shared_task

from documents.models import Document

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

    Placeholder for the pipeline issue (extraction, chunking,
    embedding): succeeds as a no-op so the task skeleton reaches the
    ``indexed`` transition; failures raise and mark the row ``failed``.

    Args:
        document: The Document currently in ``processing`` status.
    """
    del document
