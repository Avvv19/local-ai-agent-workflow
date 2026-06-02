# Architecture

## System diagram

```mermaid
flowchart TD
    U[User] -->|paste / upload .txt or .pdf| UI[Streamlit UI]
    U -->|HTTP| API[FastAPI backend]

    UI --> ORCH[Workflow Orchestrator]
    API --> ORCH

    subgraph Workflow [Orchestrated pipeline -  app/orchestrator.py]
        direction TB
        C1[1. Clean text] --> C2[2. Classify]
        C2 --> C3[3. Extract fields - JSON, retry on bad JSON]
        C3 --> C4[4. Summarize]
        C4 --> C5[5. Route]
        C5 --> C6[6. Validate - rule based gate]
        C6 --> C7{7. Reliable?}
        C7 -->|yes| RR[Ready for Review]
        C7 -->|low confidence / missing fields / invalid| HR[Needs Human Review]
    end

    ORCH --> Workflow
    C2 -. prompt .-> LLM[(LLM backend)]
    C3 -. prompt .-> LLM
    C4 -. prompt .-> LLM
    C5 -. prompt .-> LLM

    LLM --> MOCK[Mock backend - deterministic]
    LLM --> OLL[Ollama + Llama 3 - local]

    RR --> DB[(SQLite)]
    HR --> DB
    DB --> T1[documents]
    DB --> T2[extractions]
    DB --> T3[review_queue]
    DB --> T4[workflow_logs]
```

## Request lifecycle

1. A document arrives via the Streamlit UI or the `/process` (text) or
   `/upload` (.txt/.pdf) API endpoints.
2. The orchestrator runs the six processing steps, calling the LLM backend for
   the classify/extract/summarize/route steps.
3. Extraction retries with a stricter prompt if the JSON is malformed.
4. The rule-based validation gate checks allowed values, required fields, and a
   non-empty summary.
5. An explicit escalation decision sets the record to *Ready for Review* or
   *Needs Human Review*.
6. The document, structured result, per-step log, and (if flagged) a
   review-queue entry are written to SQLite. The result JSON is also written to
   `data/outputs/`.

## Why these choices

- **Plain-Python orchestration** over an agent framework: deterministic,
  debuggable, and makes the reliability features first-class for a fixed flow.
- **Pluggable LLM backend**: a deterministic mock keeps the project reproducible
  with zero model setup; Ollama provides the real local model.
- **Rule-based validation in Python**, not an LLM: the reliability gate must be
  predictable.
