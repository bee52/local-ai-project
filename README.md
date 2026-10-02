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

## Repository structure

```text
.
├── agent_local.py          # Tool-calling local agent example
├── rag_local.py            # RAG pipeline and retrieval flow
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

## Notes

- The project is designed as a learning and prototyping foundation.
- `chroma_db/` is generated runtime state and should not be treated as source code.
- The system is intentionally minimal and can be extended with better retrieval, evaluation, session memory, structured outputs, and API interfaces.

## Future extension opportunities

- Add document hash/version tracking to avoid silent re-indexing
- Improve retrieval quality with reranking and hybrid search
- Add structured output models for tool responses
- Add evaluation datasets and QA checks for answer quality
- Introduce retries, timeouts, logging, and health checks
- Add API and worker endpoints for production deployment

