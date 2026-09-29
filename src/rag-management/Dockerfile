FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
# uv official image: uv is pre-installed, virtualenv managed automatically.

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock* .python-version ./
RUN uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

# Project code + documents
COPY rag.py ./
COPY docs/ ./docs/

# Download both models INTO the image at build time -> fully offline container.
# For gated models, pass the token as a build secret:
#   docker build --secret HF_TOKEN=xxxx src/rag-management
# NOTE: the python -c code must stay on ONE line. A trailing backslash
# inside the quoted string would end the RUN instruction (escaped
# backslash), and the next "from ..." line would be parsed as a FROM.
RUN --mount=type=secret,id=HF_TOKEN \
    export HF_TOKEN="$(cat /run/secrets/HF_TOKEN 2>/dev/null || true)" && \
    uv run python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; from sentence_transformers import SentenceTransformer; AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B'); AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-0.6B', torch_dtype='auto'); SentenceTransformer('Qwen/Qwen3-Embedding-0.6B')"

# No network calls to the Hugging Face Hub at runtime.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HOME=/opt/hf_cache

CMD ["uv", "run", "rag.py"]
