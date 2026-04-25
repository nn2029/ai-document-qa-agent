"""Dependency-free lexical retrieval.

This is intentionally simple and transparent for a portfolio MVP. It mimics
the retriever boundary used in larger RAG systems, so swapping to embeddings or
hybrid search later does not change the API response shape.
"""

from __future__ import annotations

from collections import Counter
import math
import re

from .domain import DocumentChunk, RetrievalHit


TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_'-]*")
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "did",
    "do",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def tokenize(text: str) -> list[str]:
    tokens = [_normalize_token(match.group(0)) for match in TOKEN_RE.finditer(text)]
    return [token for token in tokens if token and token not in STOP_WORDS]


def _normalize_token(token: str) -> str:
    token = token.lower().strip("'")
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token


def retrieve(
    question: str,
    chunks: list[DocumentChunk],
    *,
    top_k: int = 5,
    min_score: float = 0.05,
) -> list[RetrievalHit]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    question_terms = Counter(tokenize(question))
    if not question_terms:
        return []

    hits = [
        hit
        for chunk in chunks
        if (hit := _score_chunk(question, question_terms, chunk)).score >= min_score
    ]

    hits.sort(key=lambda hit: (-hit.score, hit.chunk.source_name, hit.chunk.ordinal))
    return hits[:top_k]


def _score_chunk(
    question: str,
    question_terms: Counter[str],
    chunk: DocumentChunk,
) -> RetrievalHit:
    chunk_terms = tokenize(chunk.text)
    chunk_counts = Counter(chunk_terms)
    matched = tuple(sorted(set(question_terms) & set(chunk_counts)))

    if not matched:
        return RetrievalHit(chunk=chunk, score=0.0, matched_terms=())

    capped_frequency = sum(min(chunk_counts[term], 3) * question_terms[term] for term in matched)
    density = capped_frequency / math.sqrt(len(chunk_terms) + 1)
    coverage = len(matched) / len(question_terms)
    phrase_bonus = _phrase_bonus(question, chunk.text)
    score = round((coverage * 2.0) + density + phrase_bonus, 4)

    return RetrievalHit(chunk=chunk, score=score, matched_terms=matched)


def _phrase_bonus(question: str, text: str) -> float:
    normalized_question = " ".join(tokenize(question))
    normalized_text = " ".join(tokenize(text))
    if not normalized_question or normalized_question == normalized_text:
        return 0.0
    if normalized_question in normalized_text:
        return 0.6
    return 0.0
