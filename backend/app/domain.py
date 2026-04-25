"""Shared domain objects for the RAG pipeline.

These dataclasses are deliberately independent of FastAPI/Pydantic so the
chunking, retrieval, and citation code can be unit-tested without installing
web framework dependencies.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    filename: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    source_name: str
    text: str
    start_char: int
    end_char: int
    ordinal: int


@dataclass(frozen=True)
class RetrievalHit:
    chunk: DocumentChunk
    score: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class SourceCitation:
    citation_id: str
    document_id: str
    source_name: str
    chunk_id: str
    quote: str
    start_char: int
    end_char: int
    score: float

