# AI Document Retrieval Assistant

Production-style multimodal document retrieval assistant with role-based access control, metadata-aware Qdrant retrieval, guardrails, FastAPI serving, and evaluation hooks.

**Author:** Maneesh Chintalapudi

## Frontend

The Next.js frontend provides role selection, authenticated chat, grounded answers, source references, and access-denied states.

![AI Document Retrieval Assistant frontend](assets/rag-rbac-dashboard.png)

## Architecture

```mermaid
flowchart LR
    U[User] --> W[Next.js frontend]
    W -->|Bearer mock JWT + query| A[FastAPI /chat]
    A --> G[Guardrails]
    A --> R[RBAC user context]
    G -->|Allowed| F[Metadata filter]
    R --> F
    I[PDFs, tables, audio] --> C[Chunking]
    C --> E[OpenAI embeddings]
    E --> Q[Qdrant vector store]
    Q --> F
    F --> L[Grounded LLM answer]
    G -->|Blocked| D[Access denied response]
    L --> S[Sources + confidence]
    D --> W
    S --> W
```

## What is included

- Multimodal ingestion for PDFs, tables, and audio transcripts
- Text and Markdown ingestion for the bundled document corpus
- Config-backed chunking with preserved metadata
- OpenAI embedding pipeline for Qdrant insertion
- Deterministic local embeddings when `OPENAI_API_KEY` is not configured
- RBAC-aware retrieval using pre-search Qdrant filters
- Guardrail checks for salary, prompt injection, and off-topic prompts
- FastAPI `/chat` endpoint with mock JWT verification
- Ragas evaluation script and CSV reporting
- Docker, Docker Compose, and CI coverage checks

## How to run

1. Create and activate a Python environment.
1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Copy the example env file and set your keys:

```bash
copy .env.example .env
```

1. Start Qdrant and the API with Docker:

```bash
docker compose up --build
```

On Windows with Docker Desktop versions that require an older Engine API, run:

```powershell
$env:DOCKER_API_VERSION = "1.52"
docker compose up --build
```

1. Index the bundled documents:

```powershell
docker compose exec api python -m src.ingest_documents --reset
```

The command loads `data/documents/` into the `enterprise_docs` Qdrant collection. Set `OPENAI_API_KEY` in `.env` for OpenAI embeddings; without it, the local deterministic fallback keeps the demo searchable.

1. Or run the API locally:

```bash
uvicorn src.main:app --reload
```

1. Run the test suite:

```bash
pytest
```

1. Generate the evaluation report:

```bash
python -m src.evaluation
```

## Environment variables

- `OPENAI_API_KEY`
- `QDRANT_URL`
- `QDRANT_HOST`
- `QDRANT_PORT`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME`
- `GUARDRAILS_CONFIG_DIR`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`

## Results

The evaluation script writes per-question scores to `reports/eval_report.csv` and prints a summary to the terminal.

| Metric | Value |
| --- | --- |
| Average faithfulness | Run `python -m src.evaluation` and read the summary output |
| Estimated hallucination rate | `100% - average faithfulness` |
| Unauthorized queries correctly blocked | Run the manual RBAC checks across HR, Engineering, Finance, and Admin users |

For resume use, copy the final numbers from the generated CSV and terminal summary after running the evaluation script against your configured model.

## Project structure

- `src/` application code
- `configs/guardrails/` NeMo Guardrails config
- `data/` evaluation samples
- `reports/` generated metrics
- `tests/` unit and integration tests

## Frontend development

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` after starting the API at `http://localhost:8000`.
