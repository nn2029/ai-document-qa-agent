"""Answer synthesis strategies for retrieved context."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .config import Settings
from .domain import RetrievalHit, SourceCitation


class AnswerGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        question: str,
        hits: list[RetrievalHit],
        citations: list[SourceCitation],
    ) -> str:
        """Return a user-facing answer grounded in the supplied citations."""


class MockAnswerGenerator(AnswerGenerator):
    """Deterministic generator for local runs and repeatable tests."""

    def generate(
        self,
        question: str,
        hits: list[RetrievalHit],
        citations: list[SourceCitation],
    ) -> str:
        if not hits or not citations:
            return (
                "I could not find enough supporting context in the uploaded "
                "documents to answer that question."
            )

        evidence = []
        for citation in citations[:3]:
            evidence.append(f"{citation.quote} {citation.citation_id}")

        return (
            "Based on the most relevant uploaded source chunks: "
            + " ".join(evidence)
        )


class OpenAIAnswerGenerator(AnswerGenerator):
    """Optional OpenAI-backed synthesis while retaining local citations."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        question: str,
        hits: list[RetrievalHit],
        citations: list[SourceCitation],
    ) -> str:
        if not citations:
            return MockAnswerGenerator().generate(question, hits, citations)

        context = "\n\n".join(
            f"{citation.citation_id} {citation.source_name} "
            f"(chunk {citation.chunk_id}, score {citation.score}): {citation.quote}"
            for citation in citations
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "Answer only from the provided context. Include citation "
                    "markers like [1] after claims. If the context is "
                    "insufficient, say so."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context}",
            },
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()


def get_answer_generator(settings: Settings) -> AnswerGenerator:
    provider = settings.answer_provider
    if provider == "auto":
        provider = "openai" if settings.openai_api_key else "mock"

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("ANSWER_PROVIDER=openai requires OPENAI_API_KEY.")
        return OpenAIAnswerGenerator(settings.openai_api_key, settings.openai_model)

    return MockAnswerGenerator()
