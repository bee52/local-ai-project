"""Optional MCP transport registration for the shared application facade."""

from app.mcp.service import MCPService


def create_mcp_server(service: MCPService | None = None) -> object:
    """Create an MCP server when the optional `mcp` package is installed."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "MCP transport requires the optional 'mcp' package"
        ) from exc

    facade = service or MCPService()
    server = FastMCP("local-ai")

    @server.tool()
    def search_documents(
        question: str,
        limit: int = 3,
        use_hybrid: bool = True,
        use_reranking: bool = False,
        use_hyde: bool = False,
    ) -> dict:
        return facade.search_documents(
            question, limit, use_hybrid, use_reranking, use_hyde
        )

    @server.tool()
    def answer_question(question: str) -> dict:
        return facade.answer_question(question)

    @server.tool()
    def ingest_document(source: str) -> dict:
        return facade.ingest_document(source)

    @server.tool()
    def ingest_directory(source: str) -> dict:
        return facade.ingest_directory(source)

    @server.tool()
    def get_job_status(job_id: str) -> dict:
        return facade.get_job_status(job_id)

    @server.tool()
    def health_check() -> dict:
        return facade.health_check()

    return server
