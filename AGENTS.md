# Local AI Project Agent Guide

## Scope

This is a small Python prototype combining a local Ollama LLM, a PDF-based RAG pipeline, and a separate LangChain tool-calling agent. Keep changes focused and preserve the existing public helper functions unless a migration is intentional.

## Repository Map

- `rag_local.py`: PDF loading from `data/llama2.pdf`, recursive character chunking, Ollama embeddings, Chroma persistence in `chroma_db/`, similarity retrieval, and a `ChatOllama` RAG chain.
- `agent_local.py`: Ollama-backed LangChain agent construction, the `get_current_datetime` tool, and example CLI execution under `__main__`.
- `requirements.txt`: Python dependencies for LangChain, Ollama, Chroma, PDF parsing, and environment loading.
- `data/`: source documents for ingestion.
- `chroma_db/`: generated persistent vector-store state; treat it as runtime data, not source code.

## Running Locally

1. Create or activate the project virtual environment and install `requirements.txt`.
2. Start Ollama separately with the required models available: `qwen3:8b` for chat and `nomic-embed-text` for embeddings.
3. Run `python rag_local.py` to ingest `data/llama2.pdf`, rebuild/load Chroma, and execute sample RAG queries.
4. Run `python agent_local.py` to exercise the datetime tool and basic agent responses.

There is no test suite, package entry point, configuration schema, or API server yet. Validate Python changes by compiling the touched module and, when Ollama is available, running the relevant script end to end.

## Current Data Flow

RAG flow: PDF path -> `PyPDFLoader` -> `RecursiveCharacterTextSplitter` -> `OllamaEmbeddings` -> Chroma -> similarity retriever (`k=3`) -> prompt containing retrieved context -> `ChatOllama` -> string output.

Agent flow: user message -> `ChatOllama` -> LangChain `create_agent` with registered tools -> compiled agent invocation -> final message printed by the script.

## Implementation Conventions

- Keep model names, paths, chunking settings, retrieval settings, and context limits configurable rather than scattering new literals.
- Prefer small composable functions that separate loading, indexing, retrieval, generation, and orchestration.
- Preserve document metadata through ingestion and expose citations or source metadata before adding business features.
- Do not silently re-index an unchanged corpus. Add collection/version or document-hash handling before treating indexing as a production workflow.
- Keep CLI printing at the boundary; reusable functions should return values and structured results.
- Use structured outputs and explicit error handling when adding tools or workflows. Tool failures must be observable and must not be presented as successful business results.
- Add focused tests around deterministic logic first, then mocked tests for retrieval and agent orchestration. Keep live Ollama tests separate from the default test run.

## Known Limitations and Extension Priorities

- `rag_local.py` currently indexes on every main-script run, uses one hard-coded PDF, and has no deduplication, document IDs, source citations, retrieval evaluation, or reranking.
- `agent_local.py` has a single example tool, no memory, no durable state, no timeout/retry policy, and no API boundary.
- Both scripts construct infrastructure directly and log with `print`, which makes dependency injection, observability, and deployment difficult.
- For business use, introduce configuration/settings, typed request/response models, document-ingestion and query services, tool interfaces with authorization, structured logging/tracing, health checks, evaluation datasets, and an API or worker boundary incrementally.
- Treat `chroma_db/` as local generated state. Do not hand-edit or rely on its internal SQLite layout; use Chroma APIs and make persistence paths explicit.

## Change Validation

- Syntax check: `python -m py_compile rag_local.py agent_local.py`
- Live checks require a running Ollama service and the named models.
- When adding behavior, include a focused automated test or a deterministic seam that can be tested without Ollama.