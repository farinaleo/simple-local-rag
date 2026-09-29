"""Indexing: embed a document's chunks and store them in pgvector.

The extraction, chunking and embedding building blocks live in the
``ingestion`` app; this module assembles them into the core-facing
indexing pipeline used by the worker.
"""

from django.db import transaction

from documents.models import Chunk
from ingestion.chunking import split_text
from ingestion.extractors import extract_text
from rag_core import embeddings


def index_document(document):
    """Index a document into the vector store.

    Extracts the text, chunks it, embeds the chunks and replaces the
    document chunks (and their vectors) atomically — re-indexing an
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
                embedding=embeddings.embed_chunk(content),
            )
            for ordinal, content in enumerate(chunks)
        )
