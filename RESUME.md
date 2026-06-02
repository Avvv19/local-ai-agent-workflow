# Resume & Portfolio Positioning

This project supports two resume angles. Use the version that matches the role.

---

## AI Engineer version

**Local AI Agent Workflow Automation System**

- Built a local agent workflow that transformed document requests into classified
  records, extracted fields, task summaries, and review-ready outputs.
- Added validation gates, confidence scoring, SQLite logging, retry handling, and
  human review flags to improve workflow reliability.
- Tools: Python, FastAPI, SQLAlchemy, Pydantic, Ollama, Llama 3 (LangChain optional),
  Prometheus, Streamlit, Docker.

Emphasize in interviews: the agentic workflow pattern (separate classification,
extraction, summarization, routing, validation, logging, and review steps); how the
validation gate and confidence score drive escalation; structured JSON outputs;
SQLite/Postgres persistence; retry handling; and reproducible local execution with a
deterministic backend.

---

## Data Scientist version

**Document Intelligence Workflow**

- Built a document intelligence workflow that converted unstructured business
  requests into classified records, extracted fields, and analysis-ready outputs.
- Added validation checks, confidence flags, SQLite logging, and review status
  fields to support reporting and decision support.
- Tools: Python, Pandas, SQLAlchemy, scikit-learn-style evaluation, Streamlit, CSV
  reporting export.

Emphasize in interviews: text preprocessing and cleaning; the classification
workflow and document categories; field extraction into structured records; the
labelled evaluation set and transparent metrics (JSON validity, required-field
completion, classification/routing match, human-review behaviour); review flags; and
reporting-ready CSV outputs for downstream analysis.

---

## Portfolio description (either role)

Local AI Agent Workflow Automation System is a local AI workflow that converts
unstructured business requests into classified, extracted, summarized, routed, and
review-ready records. It uses an agentic workflow pattern with a FastAPI backend, a
plain-Python orchestrator, Ollama + Llama 3 (LangChain optional) or a deterministic
mock backend, SQLAlchemy storage (SQLite or PostgreSQL), and a Streamlit review
interface. It focuses on reliability through structured JSON outputs, document-type
validation, retry handling, confidence scoring, audit logging, and human review
flags, and ships with a labelled sample set and transparent evaluation.

## Interview one-liner

I built a local AI workflow that turns messy business documents into structured,
validated, review-ready records. Separate steps handle classification, extraction,
summarization, routing, validation, and human review, and the system logs everything
to a database so it behaves like a real workflow rather than a chatbot. It runs
locally with no paid services, using either a local Llama 3 model or a deterministic
backend that keeps the project reproducible for evaluation.

## Wording to use

local AI workflow · agentic workflow pattern · document automation system ·
validation-focused workflow · review-ready outputs · sample evaluation ·
reproducible local setup.

## Wording to avoid

fully autonomous agent · enterprise ready · production grade · advanced multi-agent
platform · 100 percent accurate · large-scale deployment.
