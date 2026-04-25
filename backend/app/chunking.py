"""Chunk source documents into overlapping spans.

Chunks keep source character offsets because citations are only useful when we
can explain exactly which document region supported the answer.
"""

from __future__ import annotations

import re

from .domain import DocumentChunk, SourceDocument


BOUNDARY_PATTERNS = ("\n\n", ". ", "? ", "! ", "\n", " ")


def chunk_document(
    document: SourceDocument,
    *,
    max_chars: int = 900,
    overlap: int = 150,
    min_chars: int = 80,
) -> list[DocumentChunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars.")

    text = _normalize_document_text(document.text)
    if not text:
        return []

    chunks: list[DocumentChunk] = []
    start = 0

    while start < len(text):
        hard_end = min(start + max_chars, len(text))
        split_at = _best_split(text, start, hard_end, max_chars)

        chunk_text, chunk_start, chunk_end = _trim_span(text, start, split_at)
        if chunk_text:
            if chunks and len(chunk_text) < min_chars:
                chunks[-1] = _merge_with_previous(chunks[-1], text, chunk_end)
            else:
                ordinal = len(chunks) + 1
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}:{ordinal:04d}",
                        document_id=document.document_id,
                        source_name=document.filename,
                        text=chunk_text,
                        start_char=chunk_start,
                        end_char=chunk_end,
                        ordinal=ordinal,
                    )
                )

        if split_at >= len(text):
            break

        next_start = max(0, split_at - overlap)
        if next_start <= start:
            next_start = split_at
        start = _advance_to_content(text, next_start)

    return chunks


def _normalize_document_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _best_split(text: str, start: int, hard_end: int, max_chars: int) -> int:
    if hard_end >= len(text):
        return hard_end

    min_end = start + max(max_chars // 2, 1)
    window = text[start:hard_end]
    for pattern in BOUNDARY_PATTERNS:
        index = window.rfind(pattern)
        if index == -1:
            continue
        candidate = start + index + len(pattern)
        if candidate >= min_end:
            return candidate

    return hard_end


def _trim_span(text: str, start: int, end: int) -> tuple[str, int, int]:
    raw = text[start:end]
    left_trimmed = raw.lstrip()
    leading = len(raw) - len(left_trimmed)
    cleaned = left_trimmed.rstrip()
    trailing = len(left_trimmed) - len(cleaned)
    return cleaned, start + leading, end - trailing


def _advance_to_content(text: str, start: int) -> int:
    while start < len(text) and text[start].isspace():
        start += 1
    return start


def _merge_with_previous(
    previous: DocumentChunk,
    normalized_text: str,
    merged_end: int,
) -> DocumentChunk:
    merged_text = normalized_text[previous.start_char:merged_end].strip()
    return DocumentChunk(
        chunk_id=previous.chunk_id,
        document_id=previous.document_id,
        source_name=previous.source_name,
        text=merged_text,
        start_char=previous.start_char,
        end_char=merged_end,
        ordinal=previous.ordinal,
    )

