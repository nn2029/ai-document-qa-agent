"""Lexical retrieval with a small in-process inverted index."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
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


@dataclass(frozen=True)
class IndexedChunk:
    chunk: DocumentChunk
    token_counts: Counter[str]
    token_total: int
    normalized_text: str


class RetrievalIndex:
    """Keeps token work off the hot path for repeated questions.

    The first build still costs O(number of chunks), but each question only
    scores chunks that share at least one useful term with the query. That is a
    practical halfway point before adding embeddings or a dedicated search
    service.
    """

    def __init__(self) -> None:
        self._chunks: dict[str, IndexedChunk] = {}
        self._postings: dict[str, set[str]] = {}

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            indexed = IndexedChunk(
                chunk=chunk,
                token_counts=Counter(tokens),
                token_total=len(tokens),
                normalized_text=" ".join(tokens),
            )
            self._chunks[chunk.chunk_id] = indexed
            for token in indexed.token_counts:
                self._postings.setdefault(token, set()).add(chunk.chunk_id)

    def remove_document(self, document_id: str) -> None:
        stale_ids = [
            chunk_id
            for chunk_id, indexed in self._chunks.items()
            if indexed.chunk.document_id == document_id
        ]
        for chunk_id in stale_ids:
            indexed = self._chunks.pop(chunk_id)
            for token in indexed.token_counts:
                posting = self._postings.get(token)
                if not posting:
                    continue
                posting.discard(chunk_id)
                if not posting:
                    self._postings.pop(token, None)

    def all_chunks(self) -> list[DocumentChunk]:
        return [indexed.chunk for indexed in self._chunks.values()]

    def clear(self) -> None:
        self._chunks.clear()
        self._postings.clear()

    def search(
        self,
        question: str,
        *,
        top_k: int = 5,
        min_score: float = 0.05,
    ) -> list[RetrievalHit]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        question_terms = Counter(tokenize(question))
        if not question_terms:
            return []

        candidate_ids: set[str] = set()
        for term in question_terms:
            candidate_ids.update(self._postings.get(term, set()))

        hits = [
            hit
            for chunk_id in candidate_ids
            if (
                hit := _score_indexed_chunk(
                    question_terms,
                    self._chunks[chunk_id],
                )
            ).score
            >= min_score
        ]
        hits.sort(key=lambda hit: (-hit.score, hit.chunk.source_name, hit.chunk.ordinal))
        return hits[:top_k]


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
    index = RetrievalIndex()
    index.add_chunks(chunks)
    return index.search(question, top_k=top_k, min_score=min_score)


def _score_indexed_chunk(
    question_terms: Counter[str],
    indexed: IndexedChunk,
) -> RetrievalHit:
    chunk_counts = indexed.token_counts
    matched = tuple(sorted(set(question_terms) & set(chunk_counts)))

    if not matched:
        return RetrievalHit(chunk=indexed.chunk, score=0.0, matched_terms=())

    capped_frequency = sum(min(chunk_counts[term], 3) * question_terms[term] for term in matched)
    density = capped_frequency / math.sqrt(indexed.token_total + 1)
    coverage = len(matched) / len(question_terms)
    phrase_bonus = _phrase_bonus(" ".join(question_terms), indexed.normalized_text)
    score = round((coverage * 2.0) + density + phrase_bonus, 4)

    return RetrievalHit(chunk=indexed.chunk, score=score, matched_terms=matched)


def _phrase_bonus(normalized_question: str, normalized_text: str) -> float:
    if not normalized_question or normalized_question == normalized_text:
        return 0.0
    if normalized_question in normalized_text:
        return 0.6
    return 0.0
