"""FastAPI application factory for the local AI service."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.config import settings
from app.health import process_health_check, readiness_health_check
from app.mcp.service import MCPService
from app.models import HealthStatus
from app.workers.service import WorkerService


def create_app(
    service: MCPService | None = None,
    worker: WorkerService | None = None,
) -> Any:
    """Create the HTTP API with injectable services for tests and deployments."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError(
            "The HTTP API requires the optional 'fastapi' and 'pydantic' packages"
        ) from exc

    facade = service or MCPService()
    workers = worker or WorkerService(settings.max_workers)
    app = FastAPI(title="Local AI API", version="0.1.0")
    static_directory = Path(__file__).parent / "static"

    @app.get("/", include_in_schema=False)
    def frontend() -> FileResponse:
        return FileResponse(static_directory / "index.html")

    app.mount("/static", StaticFiles(directory=static_directory), name="static")

    class QueryPayload(BaseModel):
        question: str = Field(min_length=1)
        limit: int = Field(default=3, ge=1, le=100)
        use_hybrid: bool = True
        use_reranking: bool = False
        use_hyde: bool = False

    class IngestPayload(BaseModel):
        source: str = Field(min_length=1)

    @app.get("/health/live")
    def live() -> dict[str, Any]:
        return asdict(process_health_check())

    @app.get("/health/ready")
    def ready() -> dict[str, Any]:
        result = readiness_health_check([])
        return asdict(result)

    @app.get("/health/details")
    def details() -> dict[str, Any]:
        return facade.health_check()

    @app.post("/search")
    def search(payload: QueryPayload) -> dict[str, Any]:
        try:
            return facade.search_documents(
                payload.question,
                payload.limit,
                payload.use_hybrid,
                payload.use_reranking,
                payload.use_hyde,
            )
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/query")
    def query(payload: QueryPayload) -> dict[str, Any]:
        try:
            return facade.answer_question(payload.question)
        except (RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/documents/ingest", status_code=202)
    def ingest(payload: IngestPayload) -> dict[str, Any]:
        job_id = workers.submit(
            "ingest_document",
            lambda: facade.ingest_document(payload.source),
        )
        return workers.get_status(job_id)

    @app.post("/documents/ingest-directory", status_code=202)
    def ingest_directory(payload: IngestPayload) -> dict[str, Any]:
        job_id = workers.submit(
            "ingest_directory",
            lambda: facade.ingest_directory(payload.source),
        )
        return workers.get_status(job_id)

    @app.get("/jobs/{job_id}")
    def job_status(job_id: str) -> dict[str, Any]:
        result = workers.get_status(job_id)
        if result["status"] == "not_found":
            raise HTTPException(status_code=404, detail=result["error"])
        return result

    return app
