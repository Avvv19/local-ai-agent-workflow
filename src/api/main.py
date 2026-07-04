"""
FastAPI application entry point.

Endpoints:
  POST /process  — submit a document for agent processing
  GET  /health   — liveness probe
  GET  /docs     — auto-generated OpenAPI docs (dev only)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.validation.schemas import DocumentInput, ProcessResponse, AgentError
from src.agents.document_agent import process_document
from src.agents.routing_agent import route_document
from src.storage.audit_log import init_db, log_event
from src.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent Document Automation System",
    description=(
        "Agent pipeline for document field extraction, classification, "
        "and routing with full audit logging."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    logger.info("Audit DB initialised. Agent pipeline ready.")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
async def process(payload: DocumentInput) -> ProcessResponse:
    """
    Submit a document for agent processing.

    Returns routing decision and extracted fields.
    Routes to human-review queue if confidence < CONFIDENCE_THRESHOLD.
    """
    log_event(trace_id=payload.trace_id, stage="api", status="received", detail=f"source={payload.source}")

    try:
        doc_output = process_document(payload)
    except AgentError as exc:
        logger.error("Agent failed: trace_id=%s error=%s", exc.trace_id, exc.last_error)
        raise HTTPException(status_code=500, detail={
            "error": str(exc),
            "trace_id": exc.trace_id,
            "last_error": exc.last_error,
        })

    routing = route_document(doc_output)

    return ProcessResponse(
        trace_id=routing.trace_id,
        queue=routing.queue,
        document_type=routing.document_type,
        confidence=routing.confidence,
        summary=doc_output.summary,
    )
