# Advanced Local AI Project Plan

This file is the durable source of truth for the planned transformation from the current Ollama RAG and agent demo into a production-oriented local AI application.

## Guiding architecture

The CLI, API, worker, MCP server, and user interface must call shared application services. They must not implement separate retrieval, ingestion, error-handling, or model-integration logic.

## Phases

### 1. Foundation and configuration

- Extract reusable services from `rag_local.py` and `agent_local.py`.
- Add an `app/` package with configuration, typed models, logging, health, ingestion, retrieval, service, API, worker, and MCP boundaries.
- Make model names, paths, retrieval settings, timeouts, retries, and context limits configurable.
- Add structured request and response models.
- Add document IDs, content hashes, metadata, and collection/version handling.
- Preserve existing public helper functions during the transition where practical.

### 2. Multi-format ingestion

- Replace the hard-coded PDF loader with a loader registry.
- Support PDF, Markdown, plain text, HTML, DOCX, JSON, and CSV.
- Add file and directory ingestion, format detection, metadata enrichment, stable chunk IDs, deduplication, deletion, and incremental indexing.
- Track ingestion status: queued, running, completed, and failed.

### 3. Advanced retrieval

- Introduce a configurable retrieval pipeline.
- Add dense vector retrieval through Chroma.
- Add lexical retrieval with BM25 or an equivalent local search component.
- Combine dense and lexical results with reciprocal rank fusion or weighted fusion.
- Add an optional local cross-encoder reranker.
- Add optional HyDE query expansion with a fallback to the original query.
- Return citations, source metadata, and retrieval scores.
- Create a small evaluation dataset and measure recall@k, precision@k, MRR, and answer faithfulness.

### 4. Reliability and operations

- Add structured logging, correlation IDs, latency measurements, and retrieval/generation metrics.
- Add bounded retries with exponential backoff for transient failures.
- Add explicit connect, read, and generation timeouts.
- Add bounded concurrency and fail-fast behavior when dependencies are unavailable.
- Add liveness, readiness, and detailed dependency health checks for Ollama, Chroma, workers, and storage.

### 5. MCP integration

- Add an MCP server backed by the shared application services.
- Expose typed tools for document search, question answering, ingestion, document listing, job status, and health checks.
- Return citations and structured errors from MCP tools.
- Add authorization boundaries for ingestion and deletion.
- Optionally register MCP tools with the LangChain agent.

### 6. API and worker deployment

- Add a FastAPI service with health, query, search, document, and job endpoints.
- Queue long-running ingestion, embedding, re-indexing, deletion, and evaluation jobs.
- Choose and configure a queue implementation such as RQ, Arq, or Celery with Redis.
- Add validation, error contracts, pagination, upload limits, rate limiting, and authentication before non-local exposure.
- Add separate API and worker process configuration plus Docker support.

### 7. Interaction interface

- Build a web interface on top of the API.
- Add chat with streaming responses, conversation history, citations, source previews, and clear loading/failure states.
- Add controls for dense search, hybrid search, reranking, and HyDE.
- Add document upload, ingestion actions, job status, failure display, retry actions, and document search.
- Keep frontend code independent from Chroma, Ollama, and ingestion internals.

### 8. Evaluation and delivery

- Add deterministic tests for hashing, loader selection, metadata, chunking, rank fusion, HyDE fallback, reranking, retries, timeouts, health checks, API validation, worker state transitions, and MCP contracts.
- Keep live Ollama tests separate from the default test run.
- Add Docker and local development documentation.
- Update the README with setup, architecture, API, MCP, worker, interface, evaluation, and deployment instructions.

## Recommended execution order

1. Foundation, settings, models, and logging.
2. Multi-format ingestion and deduplication.
3. Retrieval abstractions and evaluation fixtures.
4. Hybrid search.
5. Reranking.
6. Optional HyDE.
7. Reliability and health checks.
8. Worker execution.
9. MCP server and agent integration.
10. API surface.
11. Web interface.
12. Evaluation, packaging, deployment, and documentation.

## Progress tracking

- [x] Phase 1: Foundation and configuration
- [x] Phase 2: Multi-format ingestion
- [ ] Phase 3: Advanced retrieval
- [ ] Phase 4: Reliability and operations
- [ ] Phase 5: MCP integration
- [ ] Phase 6: API and worker deployment
- [ ] Phase 7: Interaction interface
- [ ] Phase 8: Evaluation and delivery

## Definition of done

- All entry points use shared services.
- Unchanged documents are not silently re-indexed.
- Query responses include source citations.
- Retrieval modes are measurable and configurable.
- Dependency failures are observable and bounded by timeouts and retries.
- API, worker, MCP, and interface paths have focused automated tests.
- The project can be run locally without requiring cloud APIs, while live Ollama checks remain explicitly identified.