---
name: rag-agent-testing
description: "Test local Python RAG retrieval and LangChain agent workflows without requiring Ollama. Use for mocked embeddings, fake vector stores, retrieval quality checks, tool-call tests, deterministic orchestration tests, and offline validation."
argument-hint: "Describe the RAG or agent behavior to test"
---

# RAG and Agent Testing

## When to Use

Use this skill when testing:

- RAG document loading, splitting, retrieval, prompting, or response formatting
- LangChain agent construction and tool orchestration
- Retrieval behavior without a running Ollama server
- Agent tool success and failure paths without live model calls
- Deterministic logic in `rag_local.py` or `agent_local.py`

Do not invoke Ollama, download models, rebuild Chroma, or depend on live network services in the default test suite.

## Procedure

1. Inspect the target function and identify its dependency boundaries.
2. Separate deterministic logic from infrastructure:
   - PDF loading
   - text splitting
   - embedding generation
   - vector-store access
   - retriever invocation
   - LLM generation
   - agent tool execution
3. Replace Ollama, Chroma, and external services with fakes or mocks.
4. Test deterministic behavior first:
   - document chunks preserve metadata
   - configured chunk size and overlap are honored
   - the expected number of documents is retrieved
   - prompts contain retrieved context and the user question
   - tool inputs and outputs are propagated correctly
5. Test failure behavior:
   - missing source files
   - unavailable vector stores
   - embedding failures
   - malformed tool arguments
   - tool exceptions
   - empty retrieval results
6. For agent tests, verify:
   - the agent is created with the expected tools
   - relevant requests invoke the correct tool
   - unrelated requests do not invoke unnecessary tools
   - the final response includes the final agent message
   - tool errors are observable and are not reported as successful results
7. Keep live Ollama tests separate and explicitly marked, for example with a `live` pytest marker.
8. Run focused tests first, then the complete offline test suite.
9. Report which tests were offline and whether Ollama-dependent tests were skipped.

## Recommended Test Structure

Use a `tests/` directory with focused modules such as:

- `test_rag_deterministic.py`
- `test_rag_retrieval.py`
- `test_agent_tools.py`
- `test_agent_orchestration.py`

Prefer dependency injection when production code is changed. If injection is not available, patch infrastructure constructors at the module boundary where they are used.

## Offline Test Doubles

Use small fakes with explicit behavior:

- fake documents containing `page_content` and `metadata`
- fake embeddings returning deterministic vectors
- fake vector stores recording indexed documents
- fake retrievers returning selected documents
- fake LLMs returning a predictable answer
- fake agents recording messages and tool calls

Avoid asserting implementation details such as private LangChain internals. Assert observable inputs, outputs, calls, and errors.

## Validation

Run the narrowest available check first:

```text
python -m pytest tests/test_rag_deterministic.py
python -m pytest tests/test_agent_tools.py
```

Then run the offline suite:

```text
python -m pytest -m "not live"
```

Also compile touched modules:

```text
python -m py_compile rag_local.py agent_local.py
```

Live tests should be opt-in:

```text
python -m pytest -m live
```

Only run live tests when Ollama is available with the configured chat and embedding models.

## Completion Criteria

A test change is complete when:

- the default tests run without Ollama
- external services are mocked or replaced with deterministic fakes
- success and failure paths are covered
- tests assert observable behavior rather than framework internals
- live tests are clearly isolated
- the focused tests, offline suite, and syntax check pass
