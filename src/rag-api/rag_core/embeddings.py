"""Embedding access for the rag_core service (delegates to ingestion)."""

from ingestion import embedding as embedding_module


def embed_chunk(content):
    """Compute the embedding vector of a chunk.

    Args:
        content: The chunk text.

    Returns:
        The embedding as a list of floats (1024 dimensions).
    """
    model = embedding_module.get_embedding_model()
    vector = model.encode(content, normalize_embeddings=True)
    return list(vector)
