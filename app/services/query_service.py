"""Reusable query service for CLI, API, worker, and MCP callers."""

from collections.abc import Callable
import logging

from app.models import QueryRequest, QueryResponse


logger = logging.getLogger(__name__)


class QueryService:
    """Invoke a prepared RAG chain without coupling callers to LangChain."""

    def __init__(self, chain: object, invoke: Callable[[object, str], str] | None = None):
        self._chain = chain
        self._invoke = invoke or self._default_invoke

    @staticmethod
    def _default_invoke(chain: object, question: str) -> str:
        response = chain.invoke(question)
        return str(response)

    def answer(self, request: QueryRequest) -> QueryResponse:
        """Generate an answer while keeping the public result structured."""
        if not request.question.strip():
            raise ValueError("question must not be empty")
        answer = self._invoke(self._chain, request.question)
        logger.info("Query completed")
        return QueryResponse(answer=answer)
