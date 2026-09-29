"""Vector retrieval helpers: top-k cosine similarity search on chunks."""

from pgvector.django import CosineDistance

from documents.models import Chunk


def search_similar_chunks(query_embedding, top_k=3):
    """Return the chunks closest to a query embedding by cosine distance.

    Args:
        query_embedding: The query embedding as a list of floats.
        top_k: Number of nearest chunks to return.

    Returns:
        A list of the top_k chunks ordered by ascending cosine distance.
    """
    return list(
        Chunk.objects.filter(embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:top_k]
    )
