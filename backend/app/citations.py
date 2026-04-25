"""Build source citations from retrieved chunks.

The answer generator receives citations instead of raw chunks so every answer
sentence can point to a stable source marker. The frontend also renders these
objects directly for auditability.
"""

from __future__ import annotations

import re

from .domain import RetrievalHit, SourceCitation


SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?")


def build_citations(
    hits: list[RetrievalHit],
    *,
    max_citations: int = 5,
    max_quote_chars: int = 280,
) -> list[SourceCitation]:
    citations: list[SourceCitation] = []
    seen_chunk_ids: set[str] = set()

    for hit in hits:
        if hit.chunk.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(hit.chunk.chunk_id)

        quote, local_start, local_end = _select_quote(
            hit.chunk.text,
            hit.matched_terms,
            max_quote_chars=max_quote_chars,
        )
        citations.append(
            SourceCitation(
                citation_id=f"[{len(citations) + 1}]",
                document_id=hit.chunk.document_id,
                source_name=hit.chunk.source_name,
                chunk_id=hit.chunk.chunk_id,
                quote=quote,
                start_char=hit.chunk.start_char + local_start,
                end_char=hit.chunk.start_char + local_end,
                score=hit.score,
            )
        )

        if len(citations) >= max_citations:
            break

    return citations


def _select_quote(
    text: str,
    matched_terms: tuple[str, ...],
    *,
    max_quote_chars: int,
) -> tuple[str, int, int]:
    candidate = _best_sentence(text, matched_terms) or (text.strip(), 0, len(text.strip()))
    quote, start, end = candidate
    quote = " ".join(quote.split())

    if len(quote) <= max_quote_chars:
        return quote, start, end

    trimmed = quote[: max_quote_chars - 3].rstrip() + "..."
    return trimmed, start, start + len(trimmed)


def _best_sentence(
    text: str,
    matched_terms: tuple[str, ...],
) -> tuple[str, int, int] | None:
    lowered_terms = tuple(term.lower() for term in matched_terms)
    best: tuple[int, str, int, int] | None = None

    for match in SENTENCE_RE.finditer(text):
        sentence = match.group(0).strip()
        if not sentence:
            continue

        lowered = sentence.lower()
        term_hits = sum(1 for term in lowered_terms if term in lowered)
        if term_hits == 0 and best is not None:
            continue

        score = term_hits
        if best is None or score > best[0]:
            best = (score, sentence, match.start(), match.end())

    if best is None:
        return None

    return best[1], best[2], best[3]

