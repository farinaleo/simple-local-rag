import glob
import os

from dotenv import load_dotenv

load_dotenv()  # reads .env if present; real env vars take precedence

# The Hugging Face cache location must be set BEFORE importing transformers
# and sentence-transformers: huggingface_hub resolves HF_HOME once, at import
# time. Configure it in .env (HF_HOME) to reuse an existing local cache.
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))

import chromadb  # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

# --- Configuration (see .env.example) --------------------------------------
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen3-0.6B")
EMBED_NAME = os.environ.get("EMBED_NAME", "Qwen/Qwen3-Embedding-0.6B")
DOCS_DIR = os.environ.get("DOCS_DIR", "docs")
CHROMA_PATH = os.environ.get("CHROMA_PATH", "chroma_db")
TOP_K = int(os.environ.get("TOP_K", "3"))
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "512"))
ENABLE_THINKING = os.environ.get("ENABLE_THINKING", "false").lower() == "true"
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))
# HF_TOKEN: only needed for gated/private models; read from env by huggingface_hub


# ---------------------------------------------------------------------------
# Generation model (Qwen3)
# ---------------------------------------------------------------------------


def initialize_model(model_name: str) -> tuple:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto",
    )
    return tokenizer, model


def produce_model_input(messages: list, tokenizer: AutoTokenizer, model) -> dict:
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=ENABLE_THINKING,  # False = faster grounded QA
    )
    return tokenizer([text], return_tensors="pt").to(model.device)


def text_completion(model_inputs: dict, model) -> list:
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=MAX_NEW_TOKENS,
    )
    return generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()


def parse_output(output_ids: list, tokenizer: AutoTokenizer) -> tuple:
    try:
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0
    thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
    return thinking_content, content


# ---------------------------------------------------------------------------
# Retrieval (embeddings + ChromaDB)
# ---------------------------------------------------------------------------


def initialize_embedder(model_name: str = EMBED_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def load_documents() -> list:
    texts = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.txt"))):
        with open(path, encoding="utf-8") as f:
            texts.append(f.read())
    return texts


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + chunk_size].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]


def build_or_load_store(embedder: SentenceTransformer, chunks: list):
    """Index only new chunks; the index persists across restarts via ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    col = client.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})
    existing = set(col.get()["ids"]) if col.count() else set()
    for c in chunks:
        cid = str(abs(hash(c)))
        if cid in existing:
            continue
        col.add(
            documents=[c],
            ids=[cid],
            embeddings=embedder.encode([c], normalize_embeddings=True).tolist(),
        )
    return col


def retrieve(col, embedder: SentenceTransformer, query: str, top_k: int = TOP_K) -> list:
    q = embedder.encode([query], normalize_embeddings=True).tolist()
    res = col.query(query_embeddings=q, n_results=top_k)
    return res["documents"][0]


def build_rag_message(question: str, retrieved_chunks: list) -> list:
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(retrieved_chunks))
    content = (
        "Answer the question using only the context below. "
        "If the context is not sufficient, say so explicitly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    return [{"role": "user", "content": content}]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Loading Qwen3-0.6B...")
    tokenizer, model = initialize_model(MODEL_NAME)

    print("Loading embedding model and indexing documents...")
    embedder = initialize_embedder()
    chunks = [c for doc in load_documents() for c in chunk_text(doc)]
    col = build_or_load_store(embedder, chunks)
    print(f"Indexed {col.count()} chunks.")

    while True:
        question = input("\nPlease enter your question (or 'quit' to exit): ").strip()
        if question.lower() in {"quit", "exit", "q"} or not question:
            break

        retrieved = retrieve(col, embedder, question)
        print("\n--- Retrieved chunks ---")
        for i, c in enumerate(retrieved, 1):
            print(f"[{i}] {c[:120]}{'...' if len(c) > 120 else ''}")

        messages = build_rag_message(question, retrieved)
        model_inputs = produce_model_input(messages, tokenizer, model)
        output_ids = text_completion(model_inputs, model)
        thinking_content, content = parse_output(output_ids, tokenizer)

        print("\n--- Answer ---")
        print(content)
        if thinking_content:
            print("\n(thinking:", thinking_content[:200] + "...)")


if __name__ == "__main__":
    main()
