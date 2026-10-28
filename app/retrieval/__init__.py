"""Retrieval and answer-generation boundary."""

from app.retrieval.citations import citations_from_results
from app.retrieval.evaluation import (
	RetrievalEvaluationCase,
	evaluate_case,
	precision_at_k,
	recall_at_k,
	reciprocal_rank,
)
from app.retrieval.pipeline import (
	RetrievalPipeline,
	lexical_search,
	reciprocal_rank_fusion,
)

__all__ = [
	"RetrievalPipeline",
	"RetrievalEvaluationCase",
	"citations_from_results",
	"evaluate_case",
	"lexical_search",
	"precision_at_k",
	"recall_at_k",
	"reciprocal_rank",
	"reciprocal_rank_fusion",
]
