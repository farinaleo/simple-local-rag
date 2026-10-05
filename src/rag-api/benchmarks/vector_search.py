"""pgvector vs Qdrant benchmark (issue #22, see docs/benchmarks/vector_search.md).

Measures recall@k, query latency and ingestion throughput on the
project corpus (existing chunks in PostgreSQL, optionally mirrored
into a running Qdrant instance started via compose.qdrant.yml).

Usage (inside the api container):
    uv run python benchmarks/vector_search.py pgvector
    uv run python benchmarks/vector_search.py qdrant
"""

import os
import random
import statistics
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from documents.models import Chunk  # noqa: E402
from documents.retrieval import search_similar_chunks  # noqa: E402
from ingestion.embedding import get_embedding_model  # noqa: E402

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION = "rag_benchmark"
TOP_K = 10
QUERIES = 50


def _query_texts():
    """Return sample query texts from real chunks (grounded questions)."""
    chunks = list(Chunk.objects.filter(embedding__isnull=False)[:QUERIES])
    if not chunks:
        raise SystemExit("No embedded chunks in the database; ingest documents first.")
    return [chunk.text[:200] for chunk in chunks]


def bench_pgvector(query_texts, embeddings):
    """Measure pgvector search: recall vs exact, latency, and report."""
    model = get_embedding_model()
    latencies = []
    recalls = []
    for text in query_texts:
        query_embedding = model.encode(text, normalize_embeddings=True)
        start = time.perf_counter()
        results = search_similar_chunks(list(query_embedding), top_k=TOP_K)
        latencies.append((time.perf_counter() - start) * 1000)
        exact = _exact_top_k(query_embedding)
        recalls.append(len(set(r.id for r in results) & exact) / TOP_K)
    _report("pgvector (HNSW)", latencies, recalls)


def bench_qdrant(query_texts, embeddings):
    """Measure Qdrant search by mirroring chunks into the collection."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = QdrantClient(url=QDRANT_URL)
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    chunks = list(Chunk.objects.filter(embedding__isnull=False))
    start = time.perf_counter()
    points = [
        PointStruct(
            id=chunk.id,
            vector=chunk.embedding.tolist(),
            payload={"chunk_id": chunk.id},
        )
        for chunk in chunks
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    ingest_seconds = time.perf_counter() - start

    model = get_embedding_model()
    latencies = []
    recalls = []
    for text in query_texts:
        query_embedding = model.encode(text, normalize_embeddings=True)
        start = time.perf_counter()
        response = client.query_points(
            collection_name=COLLECTION, query=query_embedding.tolist(), limit=TOP_K
        ).points
        latencies.append((time.perf_counter() - start) * 1000)
        ids = {p.payload["chunk_id"] for p in response}
        exact = _exact_top_k(query_embedding)
        recalls.append(len(ids & exact) / TOP_K)
    _report("qdrant", latencies, recalls, ingest=len(points) / ingest_seconds)


def _exact_top_k(query_embedding):
    """Return the exact top-k chunk ids (brute-force, recall reference)."""
    from pgvector.django import CosineDistance

    return set(
        Chunk.objects.filter(embedding__isnull=False)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")
        .values_list("id", flat=True)[:TOP_K]
    )


def _report(backend, latencies, recalls, ingest=None):
    """Print the benchmark summary for one backend."""
    lat = sorted(latencies)
    print(f"\n=== {backend} (top_k={TOP_K}, {len(latencies)} queries) ===")
    print(f"recall@{TOP_K}: {statistics.mean(recalls):.3f}")
    print(f"p50: {lat[len(lat) // 2]:.2f} ms")
    print(f"p95: {lat[int(len(lat) * 0.95)]:.2f} ms")
    if ingest is not None:
        print(f"ingest throughput: {ingest:.0f} vectors/s")


def main():
    """Run the requested backend benchmark."""
    random.seed(42)
    query_texts = _query_texts()
    embeddings = None
    backend = os.environ.get("BENCH_BACKEND", "pgvector")
    if backend == "qdrant":
        bench_qdrant(query_texts, embeddings)
    else:
        bench_pgvector(query_texts, embeddings)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        os.environ["BENCH_BACKEND"] = sys.argv[1]
    main()
