# simple-local-rag

A fully local, offline-capable RAG pipeline built on:

- **Qwen3-0.6B** — generation (chat, thinking-capable)
- **Qwen3-Embedding-0.6B** — retrieval embeddings
- **ChromaDB** — persistent vector store (no external DB server)
- **uv** — fast Python project & dependency management
- **Docker** — self-contained image with both models baked in

## How it works

```
docs/*.txt -> chunk -> embed -> ChromaDB
                                  |
question -> embed -> top-k search -+
                                  |
        prompt = context + question -> Qwen3-0.6B -> answer
```

## Project structure

```
simple-local-rag/
├── src/rag-management/      # RAG application package
│   ├── rag.py               # full pipeline: chunking, embedding, retrieval, generation
│   ├── pyproject.toml       # project metadata + dependencies (managed by uv)
│   ├── .python-version
│   ├── .env.example         # template of all environment variables
│   ├── Dockerfile           # image with uv + both models pre-downloaded
│   ├── docker-compose.yml   # env_file, volumes for chroma_db and docs, optional GPU
│   ├── .dockerignore
│   └── docs/                # knowledge base (.txt)
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── .gitignore
```

## Quick start (local, with uv)

```bash
# 1. Install uv (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Configure
cd src/rag-management
cp .env.example .env        # then edit .env (HF_TOKEN only needed for gated models)

# 3. Install dependencies and run (uv creates .venv automatically)
uv sync
uv run rag.py
```

Put your documents as `.txt` files in `src/rag-management/docs/`. The vector index
persists in `src/rag-management/chroma_db/` and only new chunks are indexed on
subsequent runs.

## Docker

```bash
cp src/rag-management/.env.example src/rag-management/.env
docker compose -f src/rag-management/docker-compose.yml build   # ~15 min the first time
docker compose -f src/rag-management/docker-compose.yml up -d
docker compose -f src/rag-management/docker-compose.yml exec rag uv run rag.py
```

The image sets `HF_HUB_OFFLINE=1` and ships both models, so once built it runs
with no internet access. Test it: stop the stack, disconnect the network,
start it again — it still answers.

For gated models, pass your token at build time without leaking it:

```bash
docker build --secret HF_TOKEN=hf_xxxx -f src/rag-management/Dockerfile .
```

## Configuration

All settings live in `.env` (see `src/rag-management/.env.example`): model names,
paths, `TOP_K`, `CHUNK_SIZE`, `MAX_NEW_TOKENS`, `ENABLE_THINKING`, and `HF_TOKEN`.
Real environment variables override `.env` values.

## Notes

- `ENABLE_THINKING=false` and `MAX_NEW_TOKENS=512` are set for fast grounded
  QA; flip them for reasoning-heavy use cases.
- The pyproject pins CPU torch via uv's `pytorch-cpu` index — swap for a CUDA
  index if you build with a GPU.
- Swap ChromaDB for Qdrant if you later need multi-user serving or heavy
  metadata filtering.
