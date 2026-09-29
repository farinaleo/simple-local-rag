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
