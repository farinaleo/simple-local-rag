"""Retrieval: embed a question and search the closest chunks."""

import os

from documents.retrieval import search_similar_chunks
from ingestion import embedding as embedding_module


def retrieve_chunks(question, top_k=None, user=None):
    """Retrieve the chunks most relevant to a question.

    Args:
        question: The user question.
        top_k: Number of chunks to retrieve (defaults to the
            ``TOP_K`` environment variable or 3).
        user: The requesting user; authenticated users only search
            their own documents plus shared ones.

    Returns:
        The list of matching chunks, closest first.
    """
    if top_k is None:
        top_k = int(os.environ.get("TOP_K", "3"))
    model = embedding_module.get_embedding_model()
    query_embedding = model.encode(question, normalize_embeddings=True)
    return search_similar_chunks(list(query_embedding), top_k=top_k, user=user)
