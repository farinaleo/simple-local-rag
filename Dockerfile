FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime
# CPU-only alternative:
#   FROM python:3.11-slim
#   RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag.py .
COPY docs/ ./docs/

# Download both models INTO the image at build time -> fully offline container.
RUN python -c "\
from transformers import AutoModelForCausalLM, AutoTokenizer; \
from sentence_transformers import SentenceTransformer; \
AutoTokenizer.from_pretrained('Qwen/Qwen3-0.6B'); \
AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-0.6B', torch_dtype='auto'); \
SentenceTransformer('Qwen/Qwen3-Embedding-0.6B')"

# No network calls to the Hugging Face Hub at runtime.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HOME=/opt/hf_cache

CMD ["python", "rag.py"]
