"""Models for documents, chunks and query history.

Status transitions
------------------
- ``Document.status``: pending -> processing -> indexed, or
  pending/processing -> failed (error message stored on the row).
- Transitions happen in the ingestion worker; the model only exposes
  the status and error fields plus short helpers.

The ``Chunk.embedding`` pgvector column and its index are added by the
pgvector infrastructure issue; ``Chunk`` stores the text and ordinal
here.
"""

from django.db import models
from pgvector.django import VectorField


class DocumentStatus(models.TextChoices):
    """Lifecycle statuses of an ingested document."""

    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    INDEXED = "indexed", "Indexed"
    FAILED = "failed", "Failed"


class Document(models.Model):
    """An uploaded knowledge-base file tracked through ingestion."""

    original_filename = models.CharField(max_length=255)
    storage_path = models.CharField(max_length=512)
    mime_type = models.CharField(max_length=127)
    size_bytes = models.BigIntegerField()
    status = models.CharField(
        max_length=16, choices=DocumentStatus.choices, default=DocumentStatus.PENDING
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the filename for admin and logs readability."""
        return self.original_filename

    def mark_processing(self):
        """Set the status to processing, starting the ingestion transition."""
        self.status = DocumentStatus.PROCESSING
        self.save(update_fields=["status", "updated_at"])

    def mark_indexed(self):
        """Set the status to indexed, closing a successful ingestion."""
        self.status = DocumentStatus.INDEXED
        self.error_message = None
        self.save(update_fields=["status", "error_message", "updated_at"])

    def mark_failed(self, error_message):
        """Set the status to failed and store the ingestion error.

        Args:
            error_message: The human-readable reason of the failure.
        """
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
        self.save(update_fields=["status", "error_message", "updated_at"])


class Chunk(models.Model):
    """A text chunk of a document, embedding stored via pgvector."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    ordinal = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=1024, null=True, blank=True)

    class Meta:
        """Ordering and uniqueness of chunks within a document."""

        ordering = ["document", "ordinal"]
        constraints = [
            models.UniqueConstraint(fields=["document", "ordinal"], name="unique_document_ordinal")
        ]

    def __str__(self):
        """Return a compact chunk reference for logs."""
        return f"{self.document.original_filename}#{self.ordinal}"


class Query(models.Model):
    """A past exchange powering the chat history feature."""

    question = models.TextField()
    answer = models.TextField()
    sources = models.ManyToManyField(Chunk, related_name="queries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Newest exchanges first for the history endpoint."""

        ordering = ["-created_at"]

    def __str__(self):
        """Return a truncated question for admin and logs readability."""
        return self.question[:60]
