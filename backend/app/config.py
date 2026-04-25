"""Runtime configuration kept free of framework-specific dependencies."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Document Q&A Agent"
    answer_provider: str = os.getenv("ANSWER_PROVIDER", "mock").lower()
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
    cors_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )


def get_settings() -> Settings:
    return Settings()

