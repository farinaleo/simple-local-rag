# RAG API image: Django + DRF served by the development server for now.
# A production WSGI server (Gunicorn) replaces it in the v2 deployment issue.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Bake the embedding model into the image (POC patterns): HF_HOME must be
# declared BEFORE the download RUN so the cache is found; at runtime the
# worker runs fully offline.
ENV HF_HOME=/opt/hf_cache
RUN uv run python -c "from ingestion.embedding import get_embedding_model; get_embedding_model()" \
    || echo "warning: embedding model not pre-downloaded (network unavailable)"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000

CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
