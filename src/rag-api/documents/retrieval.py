"""Vector retrieval helpers: top-k cosine similarity search on chunks."""

from pgvector.django import CosineDistance

from documents.models import Chunk, DocumentVisibility


def search_similar_chunks(query_embedding, top_k=3, user=None, max_distance=None):
    """Return the chunks closest to a query embedding by cosine distance.

    Args:
        query_embedding: The query embedding as a list of floats.
        top_k: Number of nearest chunks to return.
        user: The requesting user; authenticated users only search
            their own documents plus shared ones.
        max_distance: Maximum cosine distance for a chunk to qualify;
            farther chunks are dropped even when fewer than top_k
            results remain.

    Returns:
        Up to top_k chunks ordered by ascending cosine distance, each
        annotated with its ``distance``; chunks farther than
        max_distance are excluded when it is provided.
    """
    chunks = Chunk.objects.filter(embedding__isnull=False)
    if user is not None and user.is_authenticated:
        chunks = chunks.filter(document__owner=user) | chunks.filter(
            document__visibility=DocumentVisibility.SHARED
        )
    chunks = chunks.annotate(distance=CosineDistance("embedding", query_embedding)).order_by(
        "distance"
    )[:top_k]
    if max_distance is not None:
        chunks = [chunk for chunk in chunks if chunk.distance <= max_distance]
    else:
        chunks = list(chunks)
    return chunks
