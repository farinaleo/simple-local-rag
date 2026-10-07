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


class DocumentVisibility(models.TextChoices):
    """Who can read a document besides its owner."""

    PRIVATE = "private", "Private"
    SHARED = "shared", "Shared"


class Document(models.Model):
    """An uploaded knowledge-base file tracked through ingestion."""

    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    visibility = models.CharField(
        max_length=16,
        choices=DocumentVisibility.choices,
        default=DocumentVisibility.PRIVATE,
    )

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

    def is_readable_by(self, user):
        """Whether a user can read this document.

        Args:
            user: The user to check access for.

        Returns:
            True for the owner, shared documents and anonymous access
            (session auth disabled), False for other private documents.
        """
        if user is None or not user.is_authenticated:
            return True
        return self.visibility == DocumentVisibility.SHARED or self.owner_id == user.pk

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


class Conversation(models.Model):
    """A chat thread grouping the exchanges of one discussion.

    The title is derived automatically from the first question asked;
    conversations are owned by a user and deleted with their owner.
    """

    owner = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Newest conversations first for the sidebar listing."""

        ordering = ["-updated_at"]

    def __str__(self):
        """Return the title for admin and logs readability."""
        return self.title


def build_conversation_title(question):
    """Derive a conversation title from its first question.

    Args:
        question: The first question asked in the conversation.

    Returns:
        A truncated, single-line title of at most 120 characters.
    """
    first_line = question.strip().splitlines()[0] if question.strip() else ""
    return (first_line[:117] + "...") if len(first_line) > 120 else first_line


class Query(models.Model):
    """A past exchange powering the chat history feature."""

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="queries",
        null=True,
        blank=True,
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )

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
