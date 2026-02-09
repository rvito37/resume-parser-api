import io
import logging

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except PdfReadError:
        raise ValueError("Corrupted or encrypted PDF file")

    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    text_parts = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)
    return "\n".join(text_parts)


def extract_text(file_bytes: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(file_bytes)
    elif content_type == "text/plain":
        text = file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported content type: {content_type}")

    logger.info(f"Extracted {len(text)} chars from {content_type}")
    return text
