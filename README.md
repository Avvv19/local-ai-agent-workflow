# Local AI Agent Workflow Automation System

Local AI Agent Workflow Automation System converts unstructured business requests
into classified, extracted, summarized, routed, and review-ready records. It is
designed for document-heavy workflows such as forms, tickets, emails, requests, and
operational notes. The system focuses on reliability through validation checks,
retry handling, SQLite logging, confidence scoring, and human review flags.

It uses an **agentic workflow pattern** where separate steps handle classification,
extraction, summarization, routing, validation, logging, and human review. It runs
locally by default with no paid APIs, paid cloud services, or external credentials.

---

## What it does

This project converts unstructured business requests into classified records,
extracted fields, summaries, routing decisions, validation status, and review-ready
outputs using a local AI workflow. It supports both an **AI Engineer** angle
(agentic workflow, automation, backend APIs, validation, review queue, local AI
execution) and a **Data Scientist** angle (text preprocessing, classification,
structured records, evaluation checks, reporting-ready outputs, decision support).

```
received -> clean -> classify -> extract -> summarize -> route -> score -> validate -> escalate -> log
```

Each step is small, independently testable, and logged. A rule-based validation
gate plus a transparent confidence score decide whether a result is **Ready for
Review** or flagged for **Human Review**.

## Business Problem

Teams still process incoming tickets, forms, emails, and requests by hand: read it,
classify it, pull out fields, summarize, decide where it goes, check for missing
info, prep it for review. Slow, inconsistent, hard to scale. This local AI workflow
automates that loop while keeping a human in the loop for anything low-confidence or
incomplete.

## Document Categories and Routing

Categories: Billing Request · Support Ticket · Customer Complaint · Vendor Request ·
Internal Operations Request · Policy Question · General Inquiry

Routing decisions: Finance Review · Customer Support Review · Operations Review ·
Technical Review · Human Review Required · General Queue

## Document-Specific Required Fields

Different document types expect different fields, so validation is per-type:

| Document type | Required fields |
|---------------|-----------------|
| Billing Request | customer ID, invoice number, requested action, issue summary |
| Support Ticket | issue description, priority, requested action |
| Customer Complaint | customer ID, complaint summary, priority, requested action |
| Vendor Request | vendor name, request type, requested action |
| Policy Question | topic, question |
| Internal Operations Request | requested action |

## Output Schema

```json
{
  "document_type": "Billing Request",
  "priority": "Medium",
  "customer_id": "CUS-1029",
  "request_id": "CUS-1029",
  "invoice_number": "INV-88421",
  "vendor_name": null,
  "topic": null,
  "issue_summary": "Customer was billed twice, a suspected overcharge.",
  "requested_action": "Refund the duplicate charge and reissue the invoice.",
  "summary": "Billing Request: customer reports a duplicate charge and asks for a correction.",
  "routing_decision": "Finance Review",
  "missing_fields": [],
  "validation_status": "pass",
  "review_status": "Ready for Review",
  "confidence_flag": "Acceptable",
  "confidence_score": 1.0
}
```

## Confidence Scoring

Confidence is calculated using transparent workflow checks — not a random LLM score:
JSON validity, required-field completion, allowed document type, allowed routing
decision, summary completeness, and missing-field count. The score starts at 1.0 and
loses points for low classification confidence, invalid JSON, failed validation,
each missing required field, and a weak/empty summary.

## Human Review Rules

A document is routed to human review when any of the following hold:

- required fields are missing
- document type is unclear (low classification confidence)
- routing decision is unsupported / validation fails
- confidence score is below threshold (0.6)
- JSON output is invalid after the retry
- summary is empty or too weak
- input text is too short or ambiguous

## Validation Checks

Valid JSON format · required fields present (per type) · allowed document type ·
allowed priority value · allowed routing decision · missing-field detection · empty
summary detection · customer ID format check · human-review flag when outputs are
incomplete.

## Retry Handling

First attempt generates the normal structured output. If the JSON is invalid or
required fields cannot be parsed, the system retries with stricter instructions. If
the second attempt still fails, the record is saved and routed to human review.

## Audit Logging (Workflow Trace)

Every run writes a step-by-step workflow trace: document received, text cleaned,
classification completed, extraction completed, summary generated, routing selected,
validation passed/failed, confidence scored, review flag created. The trace is
stored and viewable in the UI and via the API.

## SQLite / Database Storage

Stored per document: raw document text, document type, extracted fields (full JSON),
summary, routing decision, validation status, confidence score, review status, team
role, and the workflow logs. This proves the system creates trackable records, not
temporary chat output. SQLite is the default; **PostgreSQL** is supported by setting
`DATABASE_URL`. Schema changes are managed with **Alembic** migrations.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full diagram.

```mermaid
flowchart LR
    IN[Intake txt/pdf] --> CLEAN[Clean] --> CLS[Classify] --> EXT[Extract +retry] --> SUM[Summarize] --> RTE[Route] --> SCO[Score] --> VAL[Validate] --> ESC{Reliable?}
    ESC -->|yes| RR[Ready for Review]
    ESC -->|no| HR[Needs Human Review]
    RR --> DB[(SQLite / Postgres)]
    HR --> DB
    CLS -. prompt .-> LLM[(Mock / Ollama / LangChain)]
    EXT -. prompt .-> LLM
    SUM -. prompt .-> LLM
    RTE -. prompt .-> LLM
```

| Layer | Component |
|-------|-----------|
| Frontend | Streamlit UI (process, role-filtered review queue, history, dashboard) |
| Backend | FastAPI (optional API-key auth, CORS, Prometheus `/metrics`, CSV export) |
| Orchestration | Plain-Python step orchestrator with validation gate + confidence scoring |
| Model | Ollama + Llama 3 (optionally via LangChain) — or a deterministic mock |
| Validation | Rule-based Python checks + transparent confidence scoring |
| Data | SQLAlchemy ORM -> SQLite or PostgreSQL; Alembic migrations |
| Observability | Structured logging + Prometheus metrics |

## Local-First Design

The project runs locally by default so it can be tested without paid APIs, paid
cloud services, or external credentials. Ollama and Llama 3 can be used for local
model execution, while the mock backend keeps the project reproducible for
evaluation. Local free execution is a strength, not a weakness.

## LangChain

LangChain is supported as an **optional** orchestration backend for local Ollama
execution (`LLM_BACKEND=langchain`). The default demo uses the deterministic mock
backend; the core orchestration is plain Python, so LangChain is not required.

## Tech Stack

Python, FastAPI, Pydantic + pydantic-settings, SQLAlchemy, Alembic, Streamlit,
Pandas, Prometheus, Ollama + Llama 3, LangChain (optional), Docker / docker-compose,
pytest + coverage, ruff, pre-commit, GitHub Actions.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/health` | health + active backend |
| POST | `/process` | run workflow on pasted text |
| POST | `/upload` | run workflow on a `.txt`/`.pdf` |
| GET  | `/result/{id}` | full record + workflow trace |
| GET  | `/history` | recent processed documents |
| GET  | `/review-queue?role=` | open review items, optional role filter |
| POST | `/review/{id}/resolve?decision=` | resolve / approve / reject |
| PATCH | `/result/{id}/route?new_route=` | reviewer routing override |
| GET  | `/metrics-summary` | aggregate counts (JSON) |
| GET  | `/export.csv?reviewed_only=` | history (or reviewed-only) as CSV |
| GET  | `/metrics` | Prometheus exposition format |

## How to Run Locally

```bash
pip install -r requirements.txt
make migrate        # or the app auto-creates tables
make api            # http://localhost:8000/docs
make ui             # http://localhost:8501  (separate terminal)
make test           # pytest + coverage
make lint           # ruff
make eval           # metrics over the labelled sample set
```

Real local model:

```bash
ollama pull llama3
export LLM_BACKEND=ollama          # or "langchain" (pip install langchain-ollama)
python scripts/check_ollama.py     # verify connectivity first
python -m app.main
```

PostgreSQL / Docker:

```bash
export DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/workflow
docker compose up --build                # mock backend, API + UI
docker compose --profile ollama up        # add a local Ollama service
docker compose --profile postgres up      # add a PostgreSQL service
```

## Evaluation

The workflow was tested on a labelled sample set to validate JSON structure,
required-field completion, classification and routing consistency, and review-flag
behaviour. No production-accuracy claims are made.

Sample set: 28 documents across 7 categories, including 6 incomplete examples and
4 ambiguous/short examples, with 10 documents that should trigger human review.

```
JSON validity rate ............. 100.0% (28/28)
Classification match ........... 100.0% (28/28)
Routing match .................. 100.0% (28/28)
Required-field completion ......  78.6% (22/28)
Human-review flag behaviour .... TP=10 FP=0 FN=0 TN=18
Human-review precision/recall .. 1.00 / 1.00
```

(On the bundled sample set using the deterministic mock backend. These reflect that
the backend and labels are aligned and that the escalation logic behaves as intended
— not a claim about real-world model accuracy.)

## Limitations

- The default backend uses deterministic mock logic for reproducibility.
- Ollama and Llama 3 require local model setup; those backends are not exercised by the bundled tests.
- The sample evaluation set is small.
- Scanned PDFs require OCR, which is not included yet (text-based PDFs work).
- This is a local portfolio workflow, not an enterprise production system.

## Future Improvements

OCR for scanned PDFs · document-type-specific extraction schemas · per-user
authentication and audit · alerting on the metrics · model-based confidence ·
multi-tenant review queues · deployment automation · evaluation dashboard with
historical tracking.
