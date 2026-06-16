"""Extract plain text from PDF / DOCX / TXT inputs.

Used when a request supplies a file (bytes) instead of raw text. Storage-path based parsing
(reading from Supabase Storage) can be layered on top later.
"""

from __future__ import annotations

import io

from app.core.errors import ValidationAppError
from app.core.logging import get_logger

logger = get_logger("app.services.document_parser")

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def parse_bytes(data: bytes, filename: str) -> str:
    """Parse a document's bytes into plain text based on its extension."""
    name = filename.lower()
    if name.endswith(".txt"):
        return _parse_txt(data)
    if name.endswith(".pdf"):
        return _parse_pdf(data)
    if name.endswith(".docx"):
        return _parse_docx(data)
    raise ValidationAppError(
        f"Unsupported file type. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )


def _parse_txt(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip()


def _parse_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()


def _parse_docx(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    return "\n".join(p.text for p in document.paragraphs).strip()
