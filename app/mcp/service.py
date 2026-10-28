"""Shared MCP application facade backed by existing project services."""

from dataclasses import asdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.health import process_health_check, readiness_health_check
from app.ingestion.service import IngestionService
from app.models import HealthStatus, QueryRequest
from app.retrieval.citations import citations_from_results
from app.retrieval.pipeline import RetrievalPipeline
from app.services.query_service import QueryService


class MCPService:
    """Expose typed operations suitable for MCP tools or another adapter."""

    def __init__(
        self,
        ingestion: IngestionService | None = None,
        retrieval: RetrievalPipeline | None = None,
        query: QueryService | None = None,
    ):
        self.ingestion = ingestion or IngestionService()
        self.retrieval = retrieval
        self.query = query
        self.jobs: dict[str, dict[str, Any]] = {}

    def search_documents(
        self,
        question: str,
        limit: int = 3,
        use_hybrid: bool = True,
        use_reranking: bool = False,
        use_hyde: bool = False,
    ) -> dict[str, Any]:
        """Search indexed chunks and return source-safe results."""
        if self.retrieval is None:
            raise RuntimeError("retrieval service is not configured")
        results = self.retrieval.search(
            question,
            limit=limit,
            use_hybrid=use_hybrid,
            use_reranking=use_reranking,
            use_hyde=use_hyde,
        )
        return {
            "question": question,
            "results": [
                {
                    "chunk_id": result.chunk.chunk_id,
                    "text": result.chunk.text,
                    "score": result.score,
                    "strategy": result.strategy,
                }
                for result in results
            ],
            "citations": [asdict(citation) for citation in citations_from_results(results)],
        }

    def answer_question(self, question: str) -> dict[str, Any]:
        """Answer a question through the shared query service."""
        if self.query is None:
            raise RuntimeError("query service is not configured")
        response = self.query.answer(QueryRequest(question=question))
        return asdict(response)

    def ingest_document(self, source: str) -> dict[str, Any]:
        """Ingest one supported local document and return its job result."""
        job_id = self._start_job("ingest_document")
        try:
            result = self.ingestion.ingest_file(Path(source))
            self._finish_job(job_id, "completed", asdict(result))
        except (OSError, RuntimeError, ValueError) as exc:
            self._finish_job(job_id, "failed", {"error": str(exc)})
        return self.get_job_status(job_id)

    def ingest_directory(self, source: str) -> dict[str, Any]:
        """Ingest all supported documents below a local directory."""
        job_id = self._start_job("ingest_directory")
        try:
            results = self.ingestion.ingest_directory(Path(source))
            self._finish_job(job_id, "completed", {"results": [asdict(item) for item in results]})
        except (OSError, RuntimeError, ValueError) as exc:
            self._finish_job(job_id, "failed", {"error": str(exc)})
        return self.get_job_status(job_id)

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Return a structured job result or a clear not-found error."""
        job = self.jobs.get(job_id)
        if job is None:
            return {"job_id": job_id, "status": "not_found", "error": "unknown job"}
        return dict(job)

    def health_check(self) -> dict[str, Any]:
        """Return process and readiness information for MCP clients."""
        process = process_health_check()
        readiness = readiness_health_check([])
        return {
            "healthy": process.healthy and readiness.healthy,
            "checks": [asdict(process), asdict(readiness)],
        }

    def _start_job(self, operation: str) -> str:
        job_id = str(uuid4())
        self.jobs[job_id] = {"job_id": job_id, "operation": operation, "status": "running"}
        return job_id

    def _finish_job(self, job_id: str, status: str, result: dict[str, Any]) -> None:
        self.jobs[job_id].update({"status": status, "result": result})
