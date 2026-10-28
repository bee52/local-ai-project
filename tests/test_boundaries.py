from fastapi.testclient import TestClient

from app.api.app import create_app
from app.mcp.service import MCPService
from app.workers.service import WorkerService

from conftest import make_chunk
from app.retrieval.pipeline import RetrievalPipeline


def test_mcp_and_api_expose_shared_search_and_health_contracts():
    retrieval = RetrievalPipeline([make_chunk("a", "cats retrieval")])
    service = MCPService(retrieval=retrieval)
    assert service.search_documents("cats")["citations"][0]["chunk_id"] == "a"
    assert service.health_check()["healthy"]

    worker = WorkerService(1)
    try:
        client = TestClient(create_app(service=service, worker=worker))
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200
        assert client.get("/health/live").json()["healthy"]
        response = client.post("/search", json={"question": "cats", "limit": 1})
        assert response.status_code == 200
        assert response.json()["results"][0]["chunk_id"] == "a"
        assert client.get("/jobs/missing").status_code == 404
    finally:
        worker.shutdown()