"""Generation: Qwen3-0.6B prompt building, completion and parsing.

Ported from the v1 POC (`produce_model_input`, `text_completion`,
`parse_output`) with the proven local/offline model setup.
"""

import os

_THINKING_TOKEN_ID = 151668


def _load_generation_model():
    """Load the Qwen3 tokenizer and model, cached per process.

    Model name from the ``MODEL_NAME`` environment variable
    (default: Qwen3-0.6B); HF_HOME is expected to be set before the
    first import, as in the POC.

    Returns:
        The (tokenizer, model) pair.
    """
    global _TOKENIZER, _MODEL
    if _MODEL is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
        model_name = os.environ.get("MODEL_NAME", "Qwen/Qwen3-0.6B")
        _TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        _MODEL = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype="auto", device_map="auto"
        )
    return _TOKENIZER, _MODEL


_TOKENIZER = None
_MODEL = None


def build_messages(question, retrieved_chunks):
    """Build the chat messages for a grounded question.

    Args:
        question: The user question.
        retrieved_chunks: The chunk texts providing the context.

    Returns:
        The messages list for the chat template.
    """
    context = "\n\n".join(f"[{index + 1}] {chunk}" for index, chunk in enumerate(retrieved_chunks))
    content = (
        "Answer the question using only the context below. "
        "If the context is not sufficient, say so explicitly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    return [{"role": "user", "content": content}]


def produce_model_input(messages):
    """Tokenize chat messages into model inputs.

    Args:
        messages: The messages list from ``build_messages``.

    Returns:
        The tokenized model inputs, on the model device.
    """
    tokenizer, model = _load_generation_model()
    enable_thinking = os.environ.get("ENABLE_THINKING", "false").lower() == "true"
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=enable_thinking,
    )
    return tokenizer([text], return_tensors="pt").to(model.device)


def text_completion(model_inputs):
    """Run the model on the inputs and return the new token ids.

    Args:
        model_inputs: Tokenized inputs from ``produce_model_input``.

    Returns:
        The list of generated token ids (prompt excluded).
    """
    _, model = _load_generation_model()
    max_new_tokens = int(os.environ.get("MAX_NEW_TOKENS", "512"))
    generated_ids = model.generate(**model_inputs, max_new_tokens=max_new_tokens)
    return generated_ids[0][len(model_inputs.input_ids[0]) :].tolist()


def parse_output(output_ids):
    """Decode generated token ids, splitting thinking from content.

    Args:
        output_ids: Generated token ids from ``text_completion``.

    Returns:
        The (thinking_content, content) pair, newlines stripped.
    """
    tokenizer, _ = _load_generation_model()
    try:
        index = len(output_ids) - output_ids[::-1].index(_THINKING_TOKEN_ID)
    except ValueError:
        index = 0
    thinking = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
    return thinking, content


def generate_answer(question, retrieved_chunks):
    """Answer a question from retrieved chunks, POC-equivalent.

    Args:
        question: The user question.
        retrieved_chunks: The chunk texts providing the context.

    Returns:
        The (thinking_content, content) pair.
    """
    messages = build_messages(question, retrieved_chunks)
    model_inputs = produce_model_input(messages)
    output_ids = text_completion(model_inputs)
    return parse_output(output_ids)
