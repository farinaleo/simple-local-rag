"""Shared test doubles for the ingestion tests."""


class FakeEmbeddingModel:
    """Deterministic fake embedding model (no network, no weights)."""

    def encode(self, content, normalize_embeddings=True):
        """Return a fixed 1024-dimension vector derived from the length."""
        assert normalize_embeddings
        vector = [0.0] * 1024
        vector[len(content) % 1024] = 1.0
        return vector
