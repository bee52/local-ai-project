from app.retrieval import (
    RetrievalEvaluationCase,
    RetrievalPipeline,
    citations_from_results,
    evaluate_case,
)

from conftest import make_chunk


def test_lexical_retrieval_metrics_and_citations():
    chunks = [
        make_chunk("a", "cats and retrieval"),
        make_chunk("b", "dogs and indexing"),
    ]
    results = RetrievalPipeline(chunks).search("cats", limit=1)
    metrics = evaluate_case(
        results,
        RetrievalEvaluationCase("cats", frozenset({"a"})),
        1,
    )
    citations = citations_from_results(results)

    assert results[0].chunk.chunk_id == "a"
    assert metrics == {"recall_at_k": 1.0, "precision_at_k": 1.0, "reciprocal_rank": 1.0}
    assert citations[0].source == "fixture.md"


def test_reranker_can_promote_a_later_candidate_and_hyde_expands_query():
    chunks = [make_chunk("a", "cats"), make_chunk("b", "retrieval cats")]
    observed_queries = []

    def dense(query, limit):
        observed_queries.append(query)
        return [(chunks[0], 0.9), (chunks[1], 0.8)]

    def expand(question):
        return f"{question} retrieval"

    def rerank(question, candidates):
        return [0.1 if candidate.chunk_id == "a" else 1.0 for candidate in candidates]

    results = RetrievalPipeline(
        chunks,
        dense_retriever=dense,
        reranker=rerank,
        query_expander=expand,
    ).search("cats", limit=1, use_reranking=True, use_hyde=True)

    assert observed_queries == ["cats retrieval"]
    assert results[0].chunk.chunk_id == "b"