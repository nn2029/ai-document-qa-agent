"""In-memory document store for the MVP."""

from __future__ import annotations

from threading import Lock

from .domain import DocumentChunk, SourceDocument


class DocumentStore:
    def __init__(self) -> None:
        self._documents: dict[str, SourceDocument] = {}
        self._chunks: dict[str, list[DocumentChunk]] = {}
        self._lock = Lock()

    def add_document(self, document: SourceDocument, chunks: list[DocumentChunk]) -> None:
        with self._lock:
            self._documents[document.document_id] = document
            self._chunks[document.document_id] = chunks

    def list_documents(self) -> list[dict[str, object]]:
        with self._lock:
            return [
                {
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "char_count": len(document.text),
                    "chunk_count": len(self._chunks.get(document.document_id, [])),
                }
                for document in self._documents.values()
            ]

    def all_chunks(self) -> list[DocumentChunk]:
        with self._lock:
            chunks: list[DocumentChunk] = []
            for document_chunks in self._chunks.values():
                chunks.extend(document_chunks)
            return chunks

    def clear(self) -> None:
        with self._lock:
            self._documents.clear()
            self._chunks.clear()


document_store = DocumentStore()

