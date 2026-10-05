# RAG API image: Django + DRF served by Gunicorn (v2 deployment).
FROM python:3.12-slim

# Tesseract powers the OCR extraction of image documents (v3).
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

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
# The download is mandatory: a build without a model would ship an
# image that silently fails at runtime once published.
# Optional HF token for build-time downloads: authenticated requests get
# higher rate limits and faster downloads. Pass with:
#   HF_TOKEN=hf_xxx docker compose build
# Never bake the value itself; ARG keeps it out of the final image env.
ARG HF_TOKEN
ENV HF_HOME=/opt/hf_cache
RUN uv run python -c "from ingestion.embedding import get_embedding_model; get_embedding_model()"
RUN uv run python -c "from rag_core.generator import _load_generation_model; _load_generation_model()"
# Sanity check: fail the build if both models are not in the cache.
RUN test "$(find /opt/hf_cache -name config.json -path '*snapshots*' | wc -l)" -ge 2

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "600", "--access-logfile", "-"]
