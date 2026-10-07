<div align="center">

# 🦙 simple-local-rag

**A fully local, offline-capable RAG service — your data never leaves your machine.**

[![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-managed-de5f00?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![offline](https://img.shields.io/badge/mode-100%25%20offline-2ea44f)](#)

</div>

---

<table>
<tr>
<td width="50%" valign="top">

### 🧠 Stack

| Layer | Tech |
|---|---|
| API | **Django + DRF** |
| Generation | **Qwen3-0.6B** |
| Embeddings | **Qwen3-Embedding-0.6B** |
| Vector store | **PostgreSQL + pgvector** |
| Worker | **Celery + Redis** |
| Packaging | **uv** |
| Runtime | **Docker** |

</td>
<td width="50%" valign="top">

### ✨ Highlights

- 🔒 **Fully offline** after first build
- 🗄️ **Transactional store** — metadata and vectors in one PostgreSQL
- ⚡ **Async ingestion** — uploads return 202, a Celery worker embeds
- 🧩 **Atomic document lifecycle** — delete leaves no orphan vectors
- ⚙️ **Config-driven** via environment variables
- 📦 **Self-contained** Docker images

</td>
</tr>
</table>

---

## 🏗️ Architecture

### End-to-end RAG flow

From document ingestion to the final answer, everything runs locally:

```mermaid
flowchart LR
    subgraph INGEST["📄 Ingestion (async, via Celery)"]
        direction LR
        A[/"upload txt · pdf · docx · md"/] --> B["✂️ extract + chunk"]
        B --> C["🧲 Qwen3-Embedding<br/>encode chunks"]
        C --> D[("🗄️ PostgreSQL + pgvector<br/>HNSW cosine index")]
    end

    subgraph QUERY["🔍 Retrieval (per question)"]
        direction LR
        Q[/"💬 User question"/] --> E["🧲 Qwen3-Embedding<br/>encode query"]
        E --> F["📏 cosine similarity<br/>top-k = 3"]
    end

    subgraph GEN["🧠 Generation (per question)"]
        direction LR
        G["📋 context + question"] --> H["🦙 Qwen3-0.6B"]
        H --> I["✅ Grounded answer"]
    end

    D -."lookup".-> F
    F ==> G

    classDef store fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef model fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef done fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    class D store
    class C,E,H model
    class I done
```

### Storage & runtime model

```mermaid
flowchart TB
    subgraph HOST["🖥️ Host"]
        ENV["⚙️ .env<br/>models · urls · keys"]
        subgraph RUNTIME["⚡ Runtime (RAM / VRAM)"]
            LLM["🦙 Qwen3-0.6B<br/>generator"]
            EMB["🧲 Embedder"]
        end
    end

    subgraph COMPOSE["🐳 docker-compose"]
        API["📦 api<br/>Django + DRF"]
        WORKER["👷 worker<br/>Celery"]
        PG[("🗄️ postgres + pgvector<br/>named volume")]
        REDIS(("📮 redis"))
    end

    HF["☁️ Hugging Face Hub<br/>build time only"] ==>|"weights baked in"| COMPOSE
    ENV -.-> API
    API --> PG
    API --> REDIS
    REDIS --> WORKER
    WORKER --> PG
    WORKER --> EMB

    classDef cloud fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef vol fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    class HF cloud
    class PG,REDIS vol
```

> 🔌 Once built, `HF_HUB_OFFLINE=1` blocks every call to the Hub — the
> pipeline works with the network cable unplugged.

### Project structure

```mermaid
flowchart TD
    ROOT["📁 simple-local-rag/"] --> ORCH["🐳 docker-compose.yml<br/><b>central orchestration</b>"]
    ROOT --> MK["🛠️ Makefile<br/>docker commands by usage"]
    ROOT --> META["📝 README · CHANGELOG<br/>CONTRIBUTING · .gitignore"]
    ROOT --> CI["👷 .github/workflows/ci.yml"]
    ROOT --> SRC["📁 src/"]
    SRC --> API["📁 rag-api/<br/>Django backend (v2)"]
    API --> CORE["🧩 rag_core/<br/>indexer · retriever · generator"]
    API --> ING["📦 ingestion/<br/>extractors · chunking · embedding · tasks"]
    API --> DOCSM["🗃️ documents/<br/>models · retrieval · migrations"]
    API --> CFG["⚙️ config/<br/>settings · urls · celery"]
    SRC --> WEB["📁 rag-web/<br/>React frontend (v2, scaffold)"]

    classDef root fill:#ede7f6,stroke:#5e35b1,stroke-width:2px
    classDef orch fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef pkg fill:#e8eaf6,stroke:#3949ab,stroke-width:2px
    classDef core fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef future fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    class ROOT root
    class ORCH,MK orch
    class API pkg
    class CORE,ING,DOCSM,CFG core
    class WEB future
```

**Design principle:** each module in `src/` owns its `Dockerfile` and config
(specific needs colocated with the business logic), while the root
`docker-compose.yml` orchestrates **all** services in one place.

- **`src/rag-api/`** — Django backend exposing the RAG APIs, backed by
  PostgreSQL + pgvector with a Celery + Redis ingestion worker.
- **`src/rag-web/`** — React + TypeScript SPA (documents management and chat
  interface), scaffolded — initialized in the v2 frontend issues.

---

## 🚀 Getting started

### 🐳 Docker (from the repository root)

```bash
make up            # or: docker compose up -d --build
make migrate       # apply migrations (pgvector extension + HNSW index)
make health        # curl http://localhost:8080/api/health/
```

Once the stack is up, the nginx reverse proxy is the single entrypoint:
the SPA is served on `http://localhost:8080/` and proxies `/api/` to the
Gunicorn-backed Django API.

The root compose file points each service at its module's build context.

> 🔌 The image sets `HF_HUB_OFFLINE=1` and ships the embedding model, so
> once built it runs with no internet access.

### 🧑‍💻 Local development

```bash
# 1 — Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2 — Configure and run the backend
cp .env.example .env   # at the repository root
cd src/rag-api
uv sync
uv run manage.py migrate
uv run manage.py runserver
```

### 🛠️ Makefile shortcuts

A `Makefile` at the repository root wraps the Docker commands, grouped by
usage — run `make help` to list them:

```bash
make up            # build & start the v2 backend stack
make migrate       # apply migrations (pgvector extension + HNSW index)
make db-check      # inspect the extension, embedding column and index
make test          # backend test suite against the compose postgres
make lint          # ruff lint + format checks
make health        # curl the api health endpoint
make down          # stop everything, keep the volumes
```

<details>
<summary><b>⚙️ Configuration reference</b> (all in the root <code>.env</code>, see <code>.env.example</code>)</summary>

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `true` | Django debug mode |
| `SECRET_KEY` | dev key | Django secret key |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/rag` | PostgreSQL connection |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis broker for the worker |
| `HF_HOME` | `~/.cache/huggingface` | HF cache location (local runs) |
| `MODEL_NAME` | `Qwen/Qwen3-0.6B` | Generation model |
| `EMBED_NAME` | `Qwen/Qwen3-Embedding-0.6B` | Embedding model |
| `TOP_K` | `3` | Chunks retrieved per query |
| `CHUNK_SIZE` | `500` | Max characters per chunk |
| `MAX_NEW_TOKENS` | `512` | Generation budget |
| `ENABLE_THINKING` | `false` | Qwen3 thinking mode |
| `RAG_DEVICE` | `auto` | Inference device: `auto`, `cpu` or `cuda` |

Real environment variables override `.env` values.

</details>


### 🖥️ GPU acceleration

The same codebase and image run CPU-only or GPU-accelerated; the torch
wheels shipped from PyPI already bundle the CUDA runtime, so only the
device selection and the GPU reservation change.

1. Install the
   [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
   on the host (Docker restart required).
2. Start with the GPU overlay:

   ```bash
   docker compose -f docker-compose.yml -f compose.gpu.yml up
   ```

   The overlay sets `RAG_DEVICE=cuda` and reserves one NVIDIA GPU for
   both `api` and `worker` (embeddings and generation).
3. Verify from inside the container:

   ```bash
   docker compose exec api uv run python -c "import torch; print(torch.cuda.is_available())"
   ```

Switch back to CPU by starting without the overlay (`RAG_DEVICE`
defaults to `auto`, which falls back to CPU when no GPU is visible).
`make rebuild` keeps working unchanged for the CPU setup.

**Platform notes** — the stack runs on Linux and macOS hosts:

- The default CPU setup works identically on both (uv resolves the
  right torch wheel per platform at build time: CUDA-enabled on Linux,
  CPU-only on macOS).
- The GPU overlay targets **Linux hosts only**: it needs an NVIDIA GPU
  and the nvidia-container-toolkit, neither of which exists on macOS
  (Apple Silicon GPUs are not exposed to containers). On a Mac, keep
  the default setup.
---

## 🔌 External API access

The API is consumable from external tools (CLI, scripts, other apps) with a
Bearer token created on the profile page (`Mon compte` -> Tokens API).

### Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /api/schema/` | OpenAPI 3 schema of the whole API |
| `GET /api/docs/` | Browsable Swagger documentation |
| `POST /api/documents/` | Upload a document (txt, md, pdf, docx) |
| `GET /api/documents/` | List your documents |
| `DELETE /api/documents/{id}/` | Delete a document |
| `POST /api/query/` | Ask a question (SSE-streamed answer) |

### Quick start

1. Log into the web UI, open `Mon compte`, create an API token with the
   scopes you need (`documents:read`, `documents:write`, `query`) and copy
   the one-time plaintext (`rag_...`).
2. Call the API with `Authorization: Bearer <token>`:

```bash
TOKEN="rag_..."
BASE="http://localhost:8080"

# upload a document
curl -s -X POST "$BASE/api/documents/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@notes.txt"

# ask a question (SSE stream)
curl -N -X POST "$BASE/api/query/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key points?"}'
```

Tokens are stored hashed (SHA-256), can be paused or revoked at any time,
and never grant admin endpoints. Invalid tokens are rejected (they never
fall back to anonymous access).

## 📐 ADRs

Architecture decisions are recorded in [`docs/benchmarks/`](docs/benchmarks/)
(lightweight ADR-style notes). Current: [pgvector vs Qdrant](docs/benchmarks/vector_search.md)
(decision: keep pgvector for v3, with explicit migration thresholds).

## 🧪 CI matrix

Every pull request and push to `main` runs the full pipeline
(`.github/workflows/ci.yml`):

| Job | What it runs |
|---|---|
| Backend lint (ruff) | `ruff check` + `ruff format --check` in `src/rag-api/` |
| Backend tests (pytest) | `pytest` against a pgvector PostgreSQL service |
| Frontend lint | ESLint, Prettier check and TypeScript build in `src/rag-web/` |
| Frontend tests (vitest) | `vitest run` in `src/rag-web/` |
| Compose config validation | `docker compose config` on the root compose file |

A failing lint, type check or test on either side blocks the merge.

The backend test suite includes end-to-end scenarios (`tests/test_e2e.py`):
upload → indexed for the four accepted formats, question → streamed
answer citing the uploaded document, deletion → retrieval returns
nothing, and re-upload → chunks replaced without duplicates. ML models
are replaced by deterministic doubles so the suite runs fast and offline.

## 📝 Notes

- `ENABLE_THINKING=false` + `MAX_NEW_TOKENS=512` = fast grounded QA; flip
  both for reasoning-heavy use cases.
- GPU inference needs no code change: start with `compose.gpu.yml` (see
  the GPU acceleration section above).
- Need multi-user serving or heavy metadata filtering? See the v3 roadmap
  (dedicated vector DB evaluation).

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — commit format (gitmoji), changelog
rules, PR checklist, and the **AI agents policy** (branches + pull requests
required) apply to all contributions.
