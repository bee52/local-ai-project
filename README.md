# Local AI RAG and Agent Prototype

A lightweight Python prototype for a locally hosted AI stack using Ollama, LangChain, Chroma, and PDF-based retrieval. The project demonstrates a retrieval-augmented generation (RAG) workflow and a tool-calling agent that can answer questions from a local document corpus without depending on external cloud APIs.

## What this project demonstrates

- Local LLM usage with Ollama
- PDF ingestion and chunking
- Embedding generation with Ollama embeddings
- Vector storage and similarity search with Chroma
- Retrieval-augmented prompting for grounded responses
- Tool-enabled LangChain agent orchestration
- Offline experimentation and extension into production-ready patterns

## Architecture

### RAG pipeline

`rag_local.py` implements the document Q&A flow:

1. Load PDF content from `data/llama2.pdf`
2. Split the document into chunks using `RecursiveCharacterTextSplitter`
3. Generate embeddings with `OllamaEmbeddings`
4. Store chunks in a local Chroma vector database
5. Retrieve the top 3 matching chunks for each question
6. Inject retrieved context into a prompt and generate a grounded answer with `ChatOllama`

### Agent pipeline

`agent_local.py` implements a basic tool-calling agent:

- Initializes a local Ollama chat model
- Registers a `get_current_datetime` tool
- Invokes the agent using LangChain's `create_agent`
- Prints the tool-based response for user queries

### Ingestion foundation

The shared `app.ingestion` package provides format-aware loading for PDF, Markdown,
plain text, HTML, DOCX, JSON, and CSV sources. It preserves source metadata,
generates stable document and chunk IDs, computes SHA-256 content hashes, and skips
content already seen by an ingestion service instance. The legacy PDF helper remains
available while the application services are being extracted.

### Retrieval foundation

The shared `app.retrieval` package provides offline-testable lexical retrieval,
dense-retriever integration, reciprocal-rank hybrid fusion, optional reranking and
HyDE query expansion seams, retrieval quality metrics, and citation conversion.
The current CLI still uses its original Chroma chain; API and MCP integration will
connect that chain to this pipeline in later phases.

### Reliability foundation

The shared `app.reliability` package provides bounded exponential retries,
operation timeouts, request IDs, latency metrics, and bounded thread pools. The
health module provides process liveness and aggregated dependency readiness checks.
Live Ollama and Chroma checks will be registered by the API and worker entry points.

### MCP foundation

The shared `app.mcp` package exposes search, question answering, document ingestion,
job status, and health operations through `MCPService`. The optional MCP transport
adapter in `app/mcp/server.py` registers these operations as typed tools when the
`mcp` package is installed. It delegates to the same ingestion, retrieval, query,
and health services used by other application boundaries.

### API and worker foundation

The optional FastAPI application in `app/api/app.py` exposes liveness, readiness,
dependency details, search, query, ingestion, and job-status endpoints. Long-running
ingestion is submitted to the bounded in-process `WorkerService`; the worker contract
can later be backed by Redis/RQ, Arq, or Celery without changing the API contracts.
Run the service with `uvicorn app.api.app:create_app --factory` after installing the
requirements.

### Interaction interface

The FastAPI application serves a browser workspace at `/`. It provides a citation-
first chat flow, controls for hybrid search, reranking, and HyDE, source previews,
system readiness status, and document ingestion with job-status feedback. The
interface is intentionally served by the API so local development needs one process:

```bash
uvicorn app.api.app:create_app --factory --reload
```

Then open `http://127.0.0.1:8000/`.

## Repository structure

```text
.
├── agent_local.py          # Tool-calling local agent example
├── rag_local.py            # RAG pipeline and retrieval flow
├── app/                    # Shared settings, contracts, services, and ingestion
├── requirements.txt        # Python package dependencies
├── data/
│   └── llama2.pdf          # Source PDF for local retrieval demo
├── chroma_db/              # Generated Chroma vector store
├── AGENTS.md               # Repo-specific agent guidance
├── .github/skills/         # Workspace skills for custom workflows
└── README.md               # Project overview and usage notes
```

## Local setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start Ollama locally and make sure the required models are available:

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

4. Run the RAG example:

```bash
python rag_local.py
```

5. Run the agent example:

```bash
python agent_local.py
```

6. Run the offline validation suite:

```bash
python -m pytest -q
```

The default suite uses in-memory retrieval, temporary document fixtures, fake
workers, and FastAPI's test client. It does not require Ollama or external cloud
services.

## Notes

- The project is designed as a learning and prototyping foundation.
- `chroma_db/` is generated runtime state and should not be treated as source code.
- The system is intentionally minimal and can be extended with better retrieval, evaluation, session memory, structured outputs, and API interfaces.
- Live end-to-end RAG checks require Ollama running with `qwen3:8b` and `nomic-embed-text`.
- The local worker is intentionally in-process. Use Redis/RQ, Arq, or Celery before deploying across multiple API instances.
- Authentication, rate limiting, upload limits, and durable job storage should be added before exposing the API beyond a trusted local network.

## Validation status

Phase 8 delivery validation currently includes:

- 8 offline automated tests covering ingestion, deduplication, retrieval metrics, reranking, HyDE, retries, timeouts, readiness, workers, MCP, API routes, and the interface assets.
- Python compilation of all application modules and legacy entry points.
- Separate live validation requirement for Ollama-backed embeddings, Chroma persistence, and local model generation.

## Future extension opportunities

- Add document hash/version tracking to avoid silent re-indexing
- Improve retrieval quality with reranking and hybrid search
- Add structured output models for tool responses
- Add evaluation datasets and QA checks for answer quality
- Introduce retries, timeouts, logging, and health checks
- Add API and worker endpoints for production deployment

