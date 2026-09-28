# simple-local-rag

A fully local, offline-capable RAG pipeline built on:

- **Qwen3-0.6B** — generation (chat, thinking-capable)
- **Qwen3-Embedding-0.6B** — retrieval embeddings
- **ChromaDB** — persistent vector store (no external DB server)
- **Docker** — self-contained image with both models baked in

## How it works

```
docs/*.txt -> chunk -> embed -> ChromaDB
                                  |
question -> embed -> top-k search -+
                                  |
        prompt = context + question -> Qwen3-0.6B -> answer
```

## Quick start (local, no Docker)

```bash
pip install -r requirements.txt
python rag.py
```

Put your documents as `.txt` files in `docs/`. The vector index persists in
`chroma_db/` and only new chunks are indexed on subsequent runs.

## Docker

```bash
docker compose build          # ~15 min the first time (downloads models into the image)
docker compose up -d
docker compose exec rag python rag.py
```

The image sets `HF_HUB_OFFLINE=1` and ships both models, so once built it runs
with no internet access. Test it: `docker compose down`, disconnect the
network, `docker compose up` — it still answers.

## Files

| File | Role |
|---|---|
| `rag.py` | Full pipeline: chunking, embedding, ChromaDB retrieval, Qwen3 generation |
| `Dockerfile` | Image with PyTorch + both models pre-downloaded |
| `docker-compose.yml` | Volumes for `chroma_db` and `docs`, optional GPU |
| `docs/` | Your knowledge base (.txt) |

## Notes

- `enable_thinking=False` and `max_new_tokens=512` are set for fast grounded
  QA; flip them for reasoning-heavy use cases.
- Image is ~8–10 GB with CUDA PyTorch; use the CPU base in the Dockerfile for
  a ~4 GB image.
- Swap ChromaDB for Qdrant if you later need multi-user serving or heavy
  metadata filtering.
