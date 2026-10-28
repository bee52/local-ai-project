"""Small deterministic retrieval quality metrics."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from app.models import RetrievalResult


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    """One question and its expected relevant chunk IDs."""

    question: str
    relevant_chunk_ids: frozenset[str]


def recall_at_k(results: Sequence[RetrievalResult], relevant_chunk_ids: Iterable[str], k: int) -> float:
    """Return the fraction of relevant IDs present in the first k results."""
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0
    found = {result.chunk.chunk_id for result in results[:k]}
    return len(found & relevant) / len(relevant)


def precision_at_k(results: Sequence[RetrievalResult], relevant_chunk_ids: Iterable[str], k: int) -> float:
    """Return the fraction of the first k results that are relevant."""
    if k <= 0:
        return 0.0
    relevant = set(relevant_chunk_ids)
    selected = results[:k]
    if not selected:
        return 0.0
    return sum(result.chunk.chunk_id in relevant for result in selected) / len(selected)


def reciprocal_rank(results: Sequence[RetrievalResult], relevant_chunk_ids: Iterable[str]) -> float:
    """Return reciprocal rank of the first relevant result."""
    relevant = set(relevant_chunk_ids)
    for position, result in enumerate(results, start=1):
        if result.chunk.chunk_id in relevant:
            return 1.0 / position
    return 0.0


def evaluate_case(
    results: Sequence[RetrievalResult],
    case: RetrievalEvaluationCase,
    k: int,
) -> dict[str, float]:
    """Calculate core retrieval metrics for one evaluation case."""
    return {
        "recall_at_k": recall_at_k(results, case.relevant_chunk_ids, k),
        "precision_at_k": precision_at_k(results, case.relevant_chunk_ids, k),
        "reciprocal_rank": reciprocal_rank(results, case.relevant_chunk_ids),
    }
