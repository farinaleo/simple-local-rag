"""Text extraction dispatch by file type (txt, md, pdf, docx)."""

from pathlib import Path

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".png", ".jpg", ".jpeg"}


def extract_text(file_path):
    """Extract the plain text of a document file.

    Dispatches by extension: native read for `.txt` / `.md` (markdown
    stripped to plain text), `pypdf` for PDF, `python-docx` for DOCX,
    Tesseract OCR for images (png, jpg).

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
    if extension in {".png", ".jpg", ".jpeg"}:
        return _extract_image(file_path)

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


def _extract_image(file_path):
    """Extract the text of an image file via Tesseract OCR.

    Args:
        file_path: Path of the image file (png, jpg, jpeg).

    Returns:
        The recognized text; empty string when nothing is readable.

    Raises:
        ValueError: If Tesseract is not installed on the worker.
    """
    import pytesseract
    from PIL import Image

    try:
        with Image.open(file_path) as image:
            return pytesseract.image_to_string(image).strip()
    except pytesseract.TesseractNotFoundError as error:
        raise ValueError("tesseract is not installed on the worker") from error


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
