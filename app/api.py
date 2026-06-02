"""FastAPI backend.

Exposes the workflow as an HTTP API with reliability and observability features:
optional API-key auth, CORS, Prometheus metrics, structured logging, a metrics
summary, role-filtered review queue, and CSV export.
"""
from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from . import config, database
from .auth import require_api_key
from .intake import extract_text
from .logging_config import configure_logging, get_logger
from .orchestrator import run_workflow
from .schemas import ProcessRequest

configure_logging()
log = get_logger("api")

app = FastAPI(
    title="Local AI Agent Workflow Automation System",
    version="0.2.0",
    description="Classifies, extracts, summarizes, routes, scores, validates, "
                "and logs document requests using a local LLM (Ollama / "
                "LangChain) or a deterministic mock backend.",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

database.init_db()

# ---- Prometheus metrics ---------------------------------------------------
DOCS_PROCESSED = Counter("documents_processed_total",
                         "Documents processed", ["document_type", "review_status"])
PROCESS_LATENCY = Histogram("process_seconds", "Workflow latency in seconds")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "backend": config.LLM_BACKEND}


@app.post("/process", dependencies=[Depends(require_api_key)])
def process(req: ProcessRequest) -> dict:
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    with PROCESS_LATENCY.time():
        run = run_workflow(req.text)
    doc_id = database.save_run(run, req.filename or "pasted_text.txt", req.text)
    DOCS_PROCESSED.labels(run.result.document_type, run.result.review_status).inc()
    log.info("processed doc %s -> %s / %s", doc_id, run.result.document_type,
             run.result.review_status)
    return {
        "document_id": doc_id,
        "result": run.result.to_record(),
        "validation": run.validation.model_dump(),
        "logs": [log_.__dict__ for log_ in run.logs],
    }


@app.post("/upload", dependencies=[Depends(require_api_key)])
async def upload(file: UploadFile = File(...)) -> dict:
    raw = extract_text(file.filename or "upload.txt", await file.read())
    if not raw.strip():
        raise HTTPException(status_code=400, detail="file is empty or unreadable")
    with PROCESS_LATENCY.time():
        run = run_workflow(raw)
    doc_id = database.save_run(run, file.filename or "upload.txt", raw)
    DOCS_PROCESSED.labels(run.result.document_type, run.result.review_status).inc()
    return {"document_id": doc_id, "result": run.result.to_record()}


@app.get("/result/{document_id}")
def result(document_id: int) -> dict:
    data = database.get_result(document_id)
    if not data:
        raise HTTPException(status_code=404, detail="document not found")
    return data


@app.get("/history")
def history(limit: int = 50) -> JSONResponse:
    return JSONResponse(database.get_history(limit))


@app.get("/review-queue")
def review_queue(role: str | None = Query(default=None)) -> JSONResponse:
    return JSONResponse(database.get_review_queue(role=role))


@app.post("/review/{review_id}/resolve", dependencies=[Depends(require_api_key)])
def resolve(review_id: int, decision: str = Query(default="resolved")) -> dict:
    """Close a review item. decision: resolved | approved | rejected."""
    if not database.resolve_review(review_id, decision):
        raise HTTPException(status_code=404, detail="review item not found")
    return {"review_id": review_id, "status": decision}


@app.patch("/result/{document_id}/route", dependencies=[Depends(require_api_key)])
def override_route(document_id: int, new_route: str = Query(...)) -> dict:
    """Reviewer override of the routing decision."""
    if not database.update_routing(document_id, new_route):
        raise HTTPException(status_code=400,
                            detail="unknown document or invalid route")
    return {"document_id": document_id, "routing_decision": new_route}


@app.get("/metrics-summary")
def metrics_summary() -> dict:
    return database.get_metrics()


@app.get("/export.csv")
def export_csv(reviewed_only: bool = Query(default=False)) -> PlainTextResponse:
    return PlainTextResponse(database.export_csv(reviewed_only=reviewed_only),
                             media_type="text/csv")


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus exposition format."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
