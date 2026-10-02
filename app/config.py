"""Application settings loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc


@dataclass(frozen=True)
class Settings:
    """Runtime configuration shared by CLI, API, worker, and MCP entry points."""

    data_path: Path = Path("data")
    chroma_path: Path = Path("chroma_db")
    chat_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"
    ollama_base_url: str = "http://localhost:11434"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 3
    context_window: int = 8192
    request_timeout_seconds: float = 60.0
    max_retries: int = 2
    log_level: str = "INFO"

    @classmethod
    def from_environment(cls) -> "Settings":
        """Build settings from environment variables with development defaults."""
        return cls(
            data_path=Path(os.getenv("LOCAL_AI_DATA_PATH", "data")),
            chroma_path=Path(os.getenv("LOCAL_AI_CHROMA_PATH", "chroma_db")),
            chat_model=os.getenv("LOCAL_AI_CHAT_MODEL", "qwen3:8b"),
            embedding_model=os.getenv(
                "LOCAL_AI_EMBEDDING_MODEL", "nomic-embed-text"
            ),
            ollama_base_url=os.getenv(
                "LOCAL_AI_OLLAMA_BASE_URL", "http://localhost:11434"
            ),
            chunk_size=_get_int("LOCAL_AI_CHUNK_SIZE", 1000),
            chunk_overlap=_get_int("LOCAL_AI_CHUNK_OVERLAP", 200),
            retrieval_k=_get_int("LOCAL_AI_RETRIEVAL_K", 3),
            context_window=_get_int("LOCAL_AI_CONTEXT_WINDOW", 8192),
            request_timeout_seconds=_get_float(
                "LOCAL_AI_REQUEST_TIMEOUT_SECONDS", 60.0
            ),
            max_retries=_get_int("LOCAL_AI_MAX_RETRIES", 2),
            log_level=os.getenv("LOCAL_AI_LOG_LEVEL", "INFO").upper(),
        )


settings = Settings.from_environment()
