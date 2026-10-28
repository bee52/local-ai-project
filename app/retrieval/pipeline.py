"""Offline-testable dense, lexical, hybrid, reranking, and HyDE retrieval."""

import math
import re
from collections.abc import Callable, Iterable, Sequence

from app.models import DocumentChunk, RetrievalResult


Tokenize = Callable[[str], list[str]]
DenseRetriever = Callable[[str, int], Sequence[tuple[DocumentChunk, float]]]
QueryExpander = Callable[[str], str]
Reranker = Callable[[str, Sequence[DocumentChunk]], Sequence[float]]


def tokenize(text: str) -> list[str]:
    """Tokenize text consistently for lexical retrieval and tests."""
    return re.findall(r"[a-z0-9]+", text.lower())


def lexical_search(
    question: str,
    chunks: Iterable[DocumentChunk],
    limit: int,
    tokenizer: Tokenize = tokenize,
) -> list[RetrievalResult]:
    """Rank chunks with a small BM25 implementation requiring no service."""
    chunk_list = list(chunks)
    if not chunk_list or limit <= 0:
        return []
    query_terms = tokenizer(question)
    documents = [tokenizer(chunk.text) for chunk in chunk_list]
    average_length = sum(len(tokens) for tokens in documents) / len(documents)
    document_frequency: dict[str, int] = {}
    for tokens in documents:
        for term in set(tokens):
            document_frequency[term] = document_frequency.get(term, 0) + 1

    scored: list[RetrievalResult] = []
    for chunk, terms in zip(chunk_list, documents):
        term_frequency: dict[str, int] = {}
        for term in terms:
            term_frequency[term] = term_frequency.get(term, 0) + 1
        score = 0.0
        length_factor = len(terms) / average_length if average_length else 1.0
        for term in query_terms:
            if term not in term_frequency:
                continue
            inverse_frequency = math.log(
                1 + (len(chunk_list) - document_frequency.get(term, 0) + 0.5)
                / (document_frequency.get(term, 0) + 0.5)
            )
            numerator = term_frequency[term] * 2.0
            denominator = term_frequency[term] + 1.5 * (0.75 + 0.25 * length_factor)
            score += inverse_frequency * numerator / denominator
        scored.append(RetrievalResult(chunk=chunk, score=score, strategy="lexical"))
    return sorted(scored, key=lambda result: result.score, reverse=True)[:limit]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[RetrievalResult]],
    weights: Sequence[float] | None = None,
    limit: int = 10,
) -> list[RetrievalResult]:
    """Fuse rankings while preserving each chunk's best available metadata."""
    if weights is None:
        weights = [1.0] * len(rankings)
    if len(weights) != len(rankings):
        raise ValueError("weights must match the number of rankings")
    scores: dict[str, float] = {}
    chunks: dict[str, DocumentChunk] = {}
    for ranking, weight in zip(rankings, weights):
        for position, result in enumerate(ranking, start=1):
            key = result.chunk.chunk_id
            scores[key] = scores.get(key, 0.0) + weight / (60 + position)
            chunks[key] = result.chunk
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [
        RetrievalResult(chunk=chunks[key], score=score, strategy="hybrid")
        for key, score in ordered
    ]


class RetrievalPipeline:
    """Coordinate dense, lexical, hybrid, reranked, and HyDE retrieval modes."""

    def __init__(
        self,
        chunks: Iterable[DocumentChunk],
        dense_retriever: DenseRetriever | None = None,
        reranker: Reranker | None = None,
        query_expander: QueryExpander | None = None,
        dense_weight: float = 0.6,
        lexical_weight: float = 0.4,
    ):
        self.chunks = tuple(chunks)
        self.dense_retriever = dense_retriever
        self.reranker = reranker
        self.query_expander = query_expander
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight

    def search(
        self,
        question: str,
        limit: int = 3,
        use_hybrid: bool = True,
        use_reranking: bool = False,
        use_hyde: bool = False,
    ) -> list[RetrievalResult]:
        """Return ranked results, falling back to lexical search when needed."""
        if not question.strip():
            raise ValueError("question must not be empty")
        candidate_limit = max(limit, 10) if use_reranking else limit
        query = question
        if use_hyde and self.query_expander is not None:
            expanded = self.query_expander(question).strip()
            if expanded:
                query = expanded

        lexical = lexical_search(query, self.chunks, max(limit, 10))
        if self.dense_retriever is None:
            results = lexical[:candidate_limit]
        else:
            dense = [
                RetrievalResult(chunk=chunk, score=score, strategy="dense")
                for chunk, score in self.dense_retriever(query, max(limit, 10))
            ]
            results = (
                reciprocal_rank_fusion(
                    [dense, lexical],
                    [self.dense_weight, self.lexical_weight],
                    candidate_limit,
                )
                if use_hybrid
                else dense[:candidate_limit]
            )
        if use_reranking and self.reranker is not None and results:
            rerank_scores = self.reranker(question, [result.chunk for result in results])
            if len(rerank_scores) != len(results):
                raise ValueError("reranker must return one score per chunk")
            results = [
                RetrievalResult(chunk=result.chunk, score=score, strategy="reranked")
                for result, score in sorted(
                    zip(results, rerank_scores),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ][:limit]
        return results
