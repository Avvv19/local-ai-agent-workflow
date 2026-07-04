# Multi-Agent Document Automation System

[![CI](https://github.com/Avvv19/local-ai-agent-workflow/actions/workflows/ci.yml/badge.svg)](https://github.com/Avvv19/local-ai-agent-workflow/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Agent pipeline converting document requests into extracted fields, classified summaries, and routed review outputs. Schema-validated at every step, retry-safe, and fully auditable.

---

## Architecture

```mermaid
flowchart TD
    A[Document Input] --> B[FastAPI Endpoint]
    B --> C{Input Validation\nPydantic Schema}
    C -->|Invalid| D[Reject with Error Log]
    C -->|Valid| E[Document Agent\nLangChain + OpenAI]
    E --> F{Output Validation\nPydantic Schema}
    F -->|Invalid| G[Exponential Backoff Retry]
    G -->|Max retries exceeded| H[Dead Letter Queue\nHuman Review]
    G -->|Retry succeeds| F
    F -->|Valid| I[Routing Agent\nClassification]
    I --> J{Confidence Score}
    J -->|Below threshold| H
    J -->|Above threshold| K[Auto Route Output]
    K --> L[SQLite Audit Log]
    K --> M[BigQuery Run Log]
    L --> N[Streamlit Dashboard]
    M --> N
    E --> O[LangSmith Trace]
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full data layer diagram.

---

## Production design

**Pydantic validation at every agent step**
LLM output is unreliable by default. Every agent response is validated against a strict schema before passing to the next step. Invalid outputs are caught before they corrupt downstream systems.

**Exponential backoff retry logic**
API rate limits and transient failures are handled with exponential backoff. The system retries intelligently rather than failing hard on temporary issues.

**SQLite audit logging**
Every document processed, every agent decision made, every output produced is logged with a timestamp and trace ID. Any result can be traced back to its source document.

**LangSmith observability**
LangChain traces are sent to LangSmith in real time. Latency, token usage, and chain execution are visible without instrumenting the code manually.

**Human-review checkpoints**
Documents that score below the confidence threshold are routed to a human review queue. The system never silently passes uncertain outputs.

**GitHub Actions CI pipeline**
Every push runs ruff linting, mypy type checking, and pytest. Container builds are verified on every merge to main.

---

## Tech stack

| Layer | Tool |
|---|---|
| Agent Orchestration | LangChain, OpenAI API |
| API Layer | FastAPI |
| Output Validation | Pydantic v2 |
| Observability | LangSmith |
| Storage | SQLite (audit), GCP BigQuery (run logs) |
| Infrastructure | Docker |
| UI | Streamlit |
| Testing | pytest, GitHub Actions |

---

## Running locally

1. Clone the repo
2. Copy `.env.example` to `.env` and add your API keys
3. `docker-compose up`
4. Open `localhost:8501` for the Streamlit UI

---

## Running tests

```bash
pytest tests/ -v --cov=src
```

---

## Design decisions

**Why LangChain over raw OpenAI API calls**
LangChain provides structured chain execution, built-in retry handling, and LangSmith integration. For a multi-step agent workflow, the abstraction is worth the overhead.

**Why SQLite for local audit logs**
SQLite requires zero infrastructure for local development. Production deployments use GCP BigQuery for structured run logs with partitioned schemas for efficient querying.

**Why Pydantic for output validation**
LLM outputs are strings. Business logic needs typed, validated structures. Pydantic bridges the gap with clear error messages when the model produces malformed output.
