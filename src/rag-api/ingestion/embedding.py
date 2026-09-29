"""Qwen3 embedding model access, loaded lazily and cached per process."""

import os

_MODEL = None


def get_embedding_model():
    """Return the embedding model, loading it on first call.

    Follows the POC configuration: model name from the
    ``EMBED_NAME`` environment variable, HF cache location from
    ``HF_HOME`` (must be set before importing the model).

    Returns:
        The cached sentence-transformers model instance.
    """
    global _MODEL
    if _MODEL is None:
        os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
        from sentence_transformers import SentenceTransformer

        model_name = os.environ.get("EMBED_NAME", "Qwen/Qwen3-Embedding-0.6B")
        _MODEL = SentenceTransformer(model_name)
    return _MODEL
