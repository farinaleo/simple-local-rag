"""Retrieval: embed a question and search the closest chunks."""

import os

from documents.retrieval import search_similar_chunks
from ingestion import embedding as embedding_module


def retrieve_chunks(question, top_k=None):
    """Retrieve the chunks most relevant to a question.

    Args:
        question: The user question.
        top_k: Number of chunks to retrieve (defaults to the
            ``TOP_K`` environment variable or 3).

    Returns:
        The list of (chunk, distance) pairs, closest first.
    """
    if top_k is None:
        top_k = int(os.environ.get("TOP_K", "3"))
    model = embedding_module.get_embedding_model()
    query_embedding = model.encode(question, normalize_embeddings=True)
    return search_similar_chunks(list(query_embedding), top_k=top_k)
