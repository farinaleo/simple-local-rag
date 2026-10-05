# pgvector vs Qdrant evaluation (v3, issue #22)

## Context

The v2 retrieval layer stores chunk embeddings in PostgreSQL via
pgvector (1024-dim, HNSW index, cosine distance) and filters by
document owner/visibility for multi-user scoping. At the current
single-user/small-corpus scale this is sufficient. The v3 roadmap
asks for an explicit, benchmark-backed decision before any migration.

## Decision

**Keep pgvector as the vector store for v3.** Re-evaluate when the
migration thresholds below are crossed.

## Rationale

- **Scale**: pgvector + HNSW handles hundreds of thousands of vectors
  comfortably; the project targets thousands of documents, i.e. tens
  of thousands of chunks — an order of magnitude below that.
- **Operational cost**: the stack is deliberately small (api, worker,
  postgres, redis, nginx, web). A dedicated Qdrant service adds a
  stateful component, another volume, another healthcheck and
  backup path for a gain the current scale cannot materialise.
- **Scoping**: multi-user filtering (`owner` / `visibility`) is
  expressed as plain SQL predicates next to the vector search —
  one query, one index, no cross-store consistency concerns.
- **The models, not the index, are the bottleneck**: at this scale,
  embedding (Qwen3-Embedding-0.6B) and generation (Qwen3-0.6B)
  dominate latency; sub-millisecond vs single-digit-millisecond
  vector search is invisible end-to-end.

## Benchmark protocol

Run `src/rag-api/benchmarks/vector_search.py` on a realistic corpus
(project documents + synthetic chunks sized to the target scale):

```bash
# pgvector: inside the running stack
docker compose exec api uv run python benchmarks/vector_search.py pgvector

# qdrant: start the overlay first
docker compose -f docker-compose.yml -f compose.qdrant.yml up -d
docker compose exec api uv run python benchmarks/vector_search.py qdrant
```

The script reports recall@10 against exact search, p50/p95 query
latency and ingestion throughput. Record results here:

| Backend | Corpus | recall@10 | p50 | p95 | ingest docs/s |
|---|---|---|---|---|---|
| pgvector (HNSW) | TBD | TBD | TBD | TBD | TBD |
| Qdrant (default) | TBD | TBD | TBD | TBD | TBD |

(Numbers to be filled from an actual run on target hardware; the
script produces the exact figures.)

## Migration thresholds

Re-open this decision when any of these holds:

- More than ~1M chunks or sustained ingestion where pgvector HNSW
  build times degrade ingestion throughput.
- p95 retrieval latency above ~50 ms on the target corpus.
- A need for Qdrant-native features (payload indexes beyond SQL,
  quantization for memory-constrained hosts, multi-tenant sharding).

Migration path if triggered: the retrieval layer is confined to
`documents/retrieval.py` (`search_similar_chunks`) — swapping it for
a Qdrant client behind the same signature keeps the retriever,
queries API and worker untouched; a backfill script would re-embed
or stream existing chunk vectors into the collection.

## References

- Issue #22, v3 roadmap.
- Retrieval implementation: `src/rag-api/documents/retrieval.py`.
- Compose overlay: `compose.qdrant.yml` (evaluation only).
