"""Document ingestion and text extraction.

The API layer deals with uploaded files; this module turns bytes into a
SourceDocument. PDF parsing is optional at import time and only required when
the user uploads a PDF.
"""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path

from .domain import SourceDocument


TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".log"}
PDF_EXTENSIONS = {".pdf"}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | PDF_EXTENSIONS


def extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension in TEXT_EXTENSIONS:
        return _decode_text(content)

    if extension in PDF_EXTENSIONS:
        return _extract_pdf_text(content)

    supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
    raise ValueError(f"Unsupported file type '{extension}'. Supported: {supported}")


def build_source_document(filename: str, content: bytes) -> SourceDocument:
    text = extract_text(filename, content).strip()
    if not text:
        raise ValueError("No readable text was found in the uploaded document.")

    digest = sha256(content + filename.encode("utf-8")).hexdigest()[:16]
    return SourceDocument(
        document_id=digest,
        filename=Path(filename).name,
        text=text,
        metadata={"byte_size": len(content)},
    )


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF support requires pypdf. Install backend/requirements.txt first."
        ) from exc

    reader = PdfReader(BytesIO(content))
    pages: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(f"[Page {page_number}]\n{page_text.strip()}")

    return "\n\n".join(pages)

