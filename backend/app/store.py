"""Bounded document store and retrieval index."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock

from .config import get_settings
from .domain import DocumentChunk, RetrievalHit, SourceDocument
from .retrieval import RetrievalIndex


@dataclass(frozen=True)
class StoreStats:
    document_count: int
    chunk_count: int
    max_documents: int
    max_chunks: int

    def to_dict(self) -> dict[str, int]:
        return {
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "max_documents": self.max_documents,
            "max_chunks": self.max_chunks,
        }


class DocumentStore:
    def __init__(self, max_documents: int = 50, max_chunks: int = 3000) -> None:
        self.max_documents = max(1, max_documents)
        self.max_chunks = max(1, max_chunks)
        self._documents: dict[str, SourceDocument] = {}
        self._chunks: dict[str, list[DocumentChunk]] = {}
        self._order: deque[str] = deque()
        self._index = RetrievalIndex()
        self._lock = Lock()

    def add_document(self, document: SourceDocument, chunks: list[DocumentChunk]) -> None:
        if len(chunks) > self.max_chunks:
            raise ValueError(
                f"Document creates {len(chunks)} chunks, above the {self.max_chunks} chunk limit."
            )

        with self._lock:
            if document.document_id in self._documents:
                self._order.remove(document.document_id)
                self._index.remove_document(document.document_id)

            self._documents[document.document_id] = document
            self._chunks[document.document_id] = chunks
            self._order.append(document.document_id)
            self._index.add_chunks(chunks)
            self._prune_locked()

    def list_documents(self) -> list[dict[str, object]]:
        with self._lock:
            return [
                {
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "char_count": len(document.text),
                    "chunk_count": len(self._chunks.get(document.document_id, [])),
                }
                for document_id in self._order
                if (document := self._documents.get(document_id))
            ]

    def all_chunks(self) -> list[DocumentChunk]:
        with self._lock:
            return self._index.all_chunks()

    def search(self, question: str, *, top_k: int) -> list[RetrievalHit]:
        with self._lock:
            return self._index.search(question, top_k=top_k)

    def stats(self) -> StoreStats:
        with self._lock:
            return StoreStats(
                document_count=len(self._documents),
                chunk_count=sum(len(chunks) for chunks in self._chunks.values()),
                max_documents=self.max_documents,
                max_chunks=self.max_chunks,
            )

    def clear(self) -> None:
        with self._lock:
            self._documents.clear()
            self._chunks.clear()
            self._order.clear()
            self._index.clear()

    def _prune_locked(self) -> None:
        while self._must_prune():
            oldest_id = self._order.popleft()
            self._documents.pop(oldest_id, None)
            self._chunks.pop(oldest_id, None)
            self._index.remove_document(oldest_id)

    def _must_prune(self) -> bool:
        return (
            len(self._documents) > self.max_documents
            or sum(len(chunks) for chunks in self._chunks.values()) > self.max_chunks
        )


settings = get_settings()
document_store = DocumentStore(
    max_documents=settings.max_documents,
    max_chunks=settings.max_chunks,
)
