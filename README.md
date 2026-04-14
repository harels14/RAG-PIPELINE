# RAG Pipeline — Siemens AI Document Assistant

A production-grade Retrieval-Augmented Generation (RAG) system for enterprise document Q&A. Upload PDF files (Hebrew and English), then ask questions answered in real-time by GPT-4o-mini, grounded in your documents.

## Features

- **Hybrid Retrieval** — Combines dense vector search with PostgreSQL full-text search, fused via Reciprocal Rank Fusion (RRF)
- **Streaming Responses** — Real-time answer streaming over WebSocket
- **Multi-user Isolation** — Per-user document stores with secure authentication
- **Batch PDF Upload** — Parallel processing of multiple PDFs with pipelined chunking and embedding
- **Retrieval Evaluation** — RAGAS-based quality metrics (faithfulness, relevancy, context precision)

## Architecture

```
frontend/           # Streamlit chat UI
backend/
  main.py           # FastAPI app entry point
  routes/           # HTTP & WebSocket endpoints
    document_route.py
    user_route.py
    rag_route.py
    evaluation_route.py
  services/         # Business logic
    process.py      # PDF parsing & token chunking
    vector_store.py # pgvector operations & batch embedding
    rag.py          # Hybrid retrieval (vector + FTS + RRF)
    stream.py       # GPT-4o-mini streaming responses
    evaluation.py   # RAGAS evaluation pipeline
tests/              # Manual evaluation reports (markdown)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Vector database | PostgreSQL + pgvector |
| Embeddings | OpenAI `text-embedding-3-small` |
| LLM | OpenAI `gpt-4o-mini` |
| RAG framework | LangChain (langchain-postgres, langchain-openai) |
| PDF parsing | PyMuPDF (fitz) |
| Text chunking | LangChain `TokenTextSplitter` (256 tokens, 30 overlap) |
| Full-text search | PostgreSQL native `tsvector` |
| Auth | bcrypt |
| Evaluation | RAGAS |
| Deployment | Railway.app |

## Prerequisites

- Python 3.9+
- PostgreSQL 14+ with the [pgvector](https://github.com/pgvector/pgvector) extension installed
- An OpenAI API key

## Setup

### 1. Clone & install backend

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
export OPENAI_API_KEY="sk-..."
```

### 3. Run the backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The app will create the required pgvector and FTS indexes on startup.

### 4. Run the frontend

```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

> **Note:** For local development, update `API_URL` and `WS_URL` in [frontend/app.py](frontend/app.py) to point to `http://localhost:8000` and `ws://localhost:8000`.

## API Reference

### Authentication

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/users/register` | `{username, password}` | Create a new user |
| `POST` | `/users/login` | `{username, password}` | Authenticate and get user ID |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload a single PDF (`form: userid, file`) |
| `POST` | `/documents/upload-batch` | Upload multiple PDFs in parallel (`form: userid, files[]`) |
| `GET` | `/users/{user_id}/files` | List uploaded files for a user |
| `DELETE` | `/users/{user_id}/files/{file_name}` | Delete a specific file |
| `DELETE` | `/users/{user_id}/files` | Delete all files for a user |

### RAG (WebSocket)

```
WebSocket /rag/ws

Send:    {"userid": "...", "question": "..."}
Receive: {"type": "chunk",   "content": "..."}   # streamed tokens
         {"type": "sources", "content": [...]}    # source file names
         {"type": "error",   "content": "..."}    # on failure
```

### Evaluation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/evaluation/run` | Run RAGAS metrics on a question set |
| `POST` | `/evaluation/compare` | Compare semantic vs. hybrid retrieval side-by-side |

### Health

```
GET /health  →  {"status": "Healthy"}
```

## How Hybrid Retrieval Works

1. **Vector search** — Embeds the query with `text-embedding-3-small` and performs cosine similarity search on stored document chunks.
2. **Full-text search** — Runs a PostgreSQL `tsvector` query on the same chunks using BM25-style `ts_rank` scoring.
3. **RRF fusion** — Merges both ranked lists using Reciprocal Rank Fusion (`k=60`) to produce a single reranked result set.

This approach improves faithfulness compared to pure semantic search — see [tests/](tests/) for evaluation reports.

## Deployment

The backend is deployed on [Railway.app](https://railway.app) using the config in [backend/railway.toml](backend/railway.toml).

```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "on_failure"
```

Set `DATABASE_URL` and `OPENAI_API_KEY` as Railway environment variables.

## Evaluation

Manual RAGAS evaluation reports are in [tests/](tests/). Key findings:

- Hybrid retrieval improves **faithfulness** over pure semantic search (+0.18 in tested Hebrew documents)
- Semantic retrieval performs better on **answer relevancy** and **context precision** in some scenarios
- Evaluation uses `gpt-4o-mini` as the judge model alongside `text-embedding-3-small`

To run an evaluation via the API:

```json
POST /evaluation/run
{
  "userid": "...",
  "questions": ["What is X?", "How does Y work?"],
  "ground_truths": ["X is ...", "Y works by ..."],
  "retriever_type": "hybrid"
}
```
