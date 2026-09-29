# rag-api — Django backend (v2)

Django + DRF backend of the v2, exposing the RAG APIs over
`/api/` and backed by PostgreSQL + pgvector (models, ingestion and
query endpoints land in the upcoming v2 issues).

## Endpoints

- `GET /api/health/` — liveness indicator, returns `{"status": "ok"}`.

## Local development

```bash
cd src/rag-api
uv sync
cp .env.example .env
uv run manage.py migrate
uv run manage.py runserver
```

## Tests

```bash
uv run pytest
```

## Lint

```bash
uvx ruff check .
uvx ruff format --check .
```

## Docker (from the repository root)

The root compose file starts the v2 backend stack (API + PostgreSQL
with pgvector available):

```bash
docker compose up -d postgres api
curl http://localhost:8000/api/health/        # {"status": "ok"}
docker compose exec api uv run manage.py migrate
docker compose exec api uv run pytest
```

The API image is built from the module's own `Dockerfile` (Django dev
server for now — Gunicorn lands with the v2 deployment issue).
