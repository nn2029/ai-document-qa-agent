"""HTTP API routes for uploads and question answering."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..answer_generation import MockAnswerGenerator, get_answer_generator
from ..chunking import chunk_document
from ..citations import build_citations
from ..config import get_settings
from ..domain import SourceCitation
from ..ingestion import build_source_document
from ..store import document_store


router = APIRouter()


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    top_k: int = Field(5, ge=1, le=10)


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "answer_provider": settings.answer_provider,
        "documents": str(document_store.stats().document_count),
        "chunks": str(document_store.stats().chunk_count),
    }


@router.post("/documents")
async def upload_document(file: UploadFile = File(...)) -> dict[str, object]:
    settings = get_settings()
    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_mb} MB upload limit.",
        )

    try:
        document = build_source_document(file.filename or "uploaded-document", content)
        chunks = chunk_document(document)
        document_store.add_document(document, chunks)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "char_count": len(document.text),
        "chunk_count": len(chunks),
        "store": document_store.stats().to_dict(),
    }


@router.get("/documents")
def list_documents() -> dict[str, object]:
    return {
        "documents": document_store.list_documents(),
        "store": document_store.stats().to_dict(),
    }


@router.get("/stats")
def stats() -> dict[str, object]:
    return document_store.stats().to_dict()


@router.delete("/documents")
def clear_documents() -> dict[str, str]:
    document_store.clear()
    return {"status": "cleared"}


@router.post("/ask")
def ask_question(payload: QuestionRequest) -> dict[str, object]:
    chunks = document_store.all_chunks()
    if not chunks:
        raise HTTPException(status_code=400, detail="Upload at least one document first.")

    hits = document_store.search(payload.question, top_k=payload.top_k)
    citations = build_citations(hits)

    try:
        generator = get_answer_generator(get_settings())
        answer = generator.generate(payload.question, hits, citations)
    except Exception:
        # A missing model key should not break retrieval or citation checks.
        answer = MockAnswerGenerator().generate(payload.question, hits, citations)

    return {
        "question": payload.question,
        "answer": answer,
        "citations": [_citation_to_dict(citation) for citation in citations],
        "matches": [
            {
                "chunk_id": hit.chunk.chunk_id,
                "source_name": hit.chunk.source_name,
                "score": hit.score,
                "matched_terms": list(hit.matched_terms),
            }
            for hit in hits
        ],
    }


def _citation_to_dict(citation: SourceCitation) -> dict[str, object]:
    return {
        "citation_id": citation.citation_id,
        "document_id": citation.document_id,
        "source_name": citation.source_name,
        "chunk_id": citation.chunk_id,
        "quote": citation.quote,
        "start_char": citation.start_char,
        "end_char": citation.end_char,
        "score": citation.score,
    }
