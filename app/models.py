"""Typed contracts shared across application boundaries."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DocumentMetadata:
    """Stable metadata retained from ingestion through retrieval."""

    document_id: str
    source: str
    content_hash: str
    mime_type: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentChunk:
    """A retrievable piece of a source document."""

    chunk_id: str
    document_id: str
    text: str
    metadata: DocumentMetadata
    position: int


@dataclass(frozen=True)
class QueryRequest:
    """Input contract for retrieval and answer generation."""

    question: str
    retrieval_k: int | None = None
    use_hybrid: bool = False
    use_reranking: bool = False
    use_hyde: bool = False


@dataclass(frozen=True)
class Citation:
    """Source reference returned with an answer."""

    source: str
    document_id: str
    chunk_id: str
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QueryResponse:
    """Structured answer contract for CLI, API, and MCP consumers."""

    answer: str
    citations: tuple[Citation, ...] = ()
    request_id: str | None = None


@dataclass(frozen=True)
class HealthStatus:
    """Health result for one application dependency or subsystem."""

    name: str
    healthy: bool
    detail: str = ""
    checked_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class IngestionResult:
    """Outcome for one source discovered by the ingestion service."""

    source: str
    document_id: str
    content_hash: str
    status: str
    chunks: tuple[DocumentChunk, ...] = ()
    detail: str = ""
