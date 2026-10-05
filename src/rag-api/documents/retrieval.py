"""Vector retrieval helpers: top-k cosine similarity search on chunks."""

from pgvector.django import CosineDistance

from documents.models import Chunk, DocumentVisibility


def search_similar_chunks(query_embedding, top_k=3, user=None):
    """Return the chunks closest to a query embedding by cosine distance.

    Args:
        query_embedding: The query embedding as a list of floats.
        top_k: Number of nearest chunks to return.
        user: The requesting user; authenticated users only search
            their own documents plus shared ones.

    Returns:
        A list of the top_k chunks ordered by ascending cosine distance.
    """
    chunks = Chunk.objects.filter(embedding__isnull=False)
    if user is not None and user.is_authenticated:
        chunks = chunks.filter(document__owner=user) | chunks.filter(
            document__visibility=DocumentVisibility.SHARED
        )
    return list(
        chunks.annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )
