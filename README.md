# Multi-Agent Document Automation System

Production-grade LangChain agent pipeline that converts unstructured document requests into extracted fields and classified summaries. Built for client deployment at an AI automation consultancy — ships with full observability, audit logging, human-review checkpoints, and a CI pipeline.

---

## What it does

Takes a document as input, routes it through a multi-agent pipeline, and returns:
- Extracted structured fields (entities, dates, amounts, parties)
- Document type classification
- Summarised output routed to the appropriate review queue
- Audit log entry for every step

Every agent boundary has Pydantic schema validation. Every failure has exponential backoff retry logic and surfaces in structured logs before reaching any downstream system.

---

## Architecture

```
Input Document
     │
     ▼
[Intake Agent]  ─── Pydantic validation ─── SQLite audit log
     │
     ▼
[Classification Agent]  (XGBoost + TF-IDF fallback for cost efficiency)
     │
     ▼
[Extraction Agent]  ─── Exponential backoff on LLM calls
     │
     ▼
[Routing Agent]  ─── Human-review checkpoint
     │
     ▼
Structured Output + Audit Trail
```

LangSmith tracing is active on every agent call. Each trace captures: input, output, latency, token usage, and any retry events.

---

## Tech stack

| Layer | Technology |
|---|---|
| Agent framework | LangChain |
| LLM | OpenAI API (GPT-4o) |
| API layer | FastAPI |
| Validation | Pydantic v2 |
| Observability | LangSmith |
| Audit storage | SQLite |
| UI | Streamlit |
| Containerisation | Docker |
| Infrastructure | Terraform |
| CI | GitHub Actions |

---

## Quickstart

### Prerequisites
- Python 3.11+
- Docker (optional, for container run)
- OpenAI API key
- LangSmith API key (free tier at smith.langchain.com)

### Run locally

```bash
git clone https://github.com/Avvv19/local-ai-agent-workflow
cd local-ai-agent-workflow
cp .env.example .env          # add your API keys
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the FastAPI interactive docs.

### Run with Docker

```bash
docker build -t local-ai-agent-workflow .
docker run -p 8000:8000 --env-file .env local-ai-agent-workflow
```

### Run Streamlit UI

```bash
streamlit run ui/app.py
```

---

## Environment variables

```
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=ls__...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=local-ai-agent-workflow
DATABASE_URL=sqlite:///audit.db
```

---

## Project structure

```
local-ai-agent-workflow/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── agents/
│   │   ├── intake.py        # Document intake and initial validation
│   │   ├── classifier.py    # XGBoost + LLM classification
│   │   ├── extractor.py     # Field extraction agent
│   │   └── router.py        # Output routing and human-review trigger
│   ├── models/
│   │   └── schemas.py       # Pydantic models for all agent I/O
│   └── utils/
│       ├── retry.py         # Exponential backoff logic
│       ├── audit.py         # SQLite audit logging
│       └── langsmith_setup.py  # LangSmith tracing initialisation
├── ui/
│   └── app.py               # Streamlit interface
├── tests/
│   ├── test_agents.py
│   ├── test_schemas.py
│   └── test_retry.py
├── .github/
│   └── workflows/
│       └── ci.yml           # Lint, test, Docker build on every push
├── Dockerfile
├── requirements.txt
├── terraform/
│   └── main.tf
└── .env.example
```

---

## Observability

Every agent call is traced in LangSmith. To view traces:
1. Open https://smith.langchain.com
2. Navigate to project `local-ai-agent-workflow`
3. Each run shows the full agent chain, token usage, latency, and any retries

The SQLite audit log (`audit.db`) records every document processed with timestamp, classification result, extraction output, routing decision, and any error events. Query it directly:

```sql
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 20;
```

---

## CI pipeline

Every push to `main` or `develop` runs:
1. `ruff check` — lint
2. `ruff format --check` — format check
3. `pytest tests/` — unit tests with coverage
4. `docker build` — container integrity check

See `.github/workflows/ci.yml` for full config.

---

## Runbook

**Q: A document went through but the extraction output looks wrong.**
A: Check `audit.db` for the document's run_id. The full extraction agent input/output is logged. If it was a classification error (wrong document type routed to wrong extractor), check the classifier confidence score in the log — scores below 0.6 fall back to the LLM classifier.

**Q: The agent is retrying repeatedly.**
A: The retry logic caps at 3 attempts with exponential backoff (2s, 4s, 8s). After 3 failures the run is logged as ERROR and routed to the human-review queue. Check the LangSmith trace for the specific error message.

**Q: How do I add a new document type?**
A: Add a new class to `app/models/schemas.py`, update the classifier training data in `data/training/`, retrain (`python scripts/train_classifier.py`), and add extraction logic in `app/agents/extractor.py`.
