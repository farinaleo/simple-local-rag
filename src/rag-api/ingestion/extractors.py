"""Text extraction dispatch by file type (txt, md, pdf, docx)."""

from pathlib import Path

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


def extract_text(file_path):
    """Extract the plain text of a document file.

    Dispatches by extension: native read for `.txt` / `.md` (markdown
    stripped to plain text), `pypdf` for PDF, `python-docx` for DOCX.

    Args:
        file_path: Path of the file to extract.

    Returns:
        The extracted plain text.

    Raises:
        ValueError: If the extension is not one of the accepted formats.
    """
    extension = Path(file_path).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(f"unsupported file type: {extension or 'none'}")

    if extension == ".pdf":
        return _extract_pdf(file_path)
    if extension == ".docx":
        return _extract_docx(file_path)

    text = Path(file_path).read_text(encoding="utf-8")
    if extension == ".md":
        return _markdown_to_plain_text(text)
    return text


def _extract_pdf(file_path):
    """Extract the concatenated text of every page of a PDF file.

    Args:
        file_path: Path of the PDF file.

    Returns:
        The extracted text, pages separated by newlines.
    """
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(file_path):
    """Extract the concatenated text of every paragraph of a DOCX file.

    Args:
        file_path: Path of the DOCX file.

    Returns:
        The extracted text, paragraphs separated by newlines.
    """
    from docx import Document

    document = Document(file_path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _markdown_to_plain_text(markdown_text):
    """Reduce markdown text to plain text.

    Args:
        markdown_text: The markdown source.

    Returns:
        The markdown stripped of its most common markup (headers,
        emphasis markers, links, code fences).
    """
    import re

    lines = []
    in_code_fence = False
    for line in markdown_text.splitlines():
        if line.lstrip().startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            lines.append(line)
            continue
        line = line.lstrip("#").strip()
        line = line.replace("**", "").replace("*", "").replace("`", "")
        line = re.sub(r"\[([^]]*)\]\([^)]*\)", r"\1", line)
        lines.append(line)
    return "\n".join(lines)
