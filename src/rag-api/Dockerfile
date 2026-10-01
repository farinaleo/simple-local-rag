# RAG API image: Django + DRF served by the development server for now.
# A production WSGI server (Gunicorn) replaces it in the v2 deployment issue.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Bake the embedding and generation models into the image (POC patterns):
# HF_HOME must be declared BEFORE the download RUNs so the cache is
# found; at runtime both api and worker run fully offline. The api
# serves chat queries so it needs the generation model too.
ENV HF_HOME=/opt/hf_cache
RUN uv run python -c "from ingestion.embedding import get_embedding_model; get_embedding_model()" \
    || echo "warning: embedding model not pre-downloaded (network unavailable)"
RUN uv run python -c "from rag_core.generator import _load_generation_model; _load_generation_model()" \
    || echo "warning: generation model not pre-downloaded (network unavailable)"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000

CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
