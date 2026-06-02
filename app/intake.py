"""Document intake helpers.

Turns an uploaded file (bytes) into plain text. Supports .txt and .pdf.
PDF text extraction uses pypdf; scanned/image PDFs (which need OCR) are out of
scope and listed under future improvements.
"""
from __future__ import annotations

import io


def extract_text(filename: str, data: bytes) -> str:
    """Extract plain text from uploaded bytes based on file extension."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _extract_pdf(data)
    # default: treat as text
    return data.decode("utf-8", errors="ignore")


def _extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "pypdf is required for PDF intake. Install it with `pip install pypdf`."
        ) from exc
    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages).strip()
