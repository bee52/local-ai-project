"""Conversion from retrieval results to public source citations."""

from collections.abc import Iterable

from app.models import Citation, RetrievalResult


def citations_from_results(results: Iterable[RetrievalResult]) -> tuple[Citation, ...]:
    """Expose ranked source metadata without leaking retrieval internals."""
    return tuple(
        Citation(
            source=result.chunk.metadata.source,
            document_id=result.chunk.document_id,
            chunk_id=result.chunk.chunk_id,
            score=result.score,
            metadata=result.chunk.metadata.attributes,
        )
        for result in results
    )