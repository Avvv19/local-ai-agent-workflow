"""
GCP BigQuery client for production run logs.

Local development uses SQLite (audit_log.py).
Production deployments call log_run_to_bigquery() to append
structured run records to a partitioned BigQuery table.

Table schema (agent_runs.runs):
  run_id        STRING
  trace_id      STRING
  document_type STRING
  queue         STRING
  confidence    FLOAT64
  summary       STRING
  created_at    TIMESTAMP
  partition_dt  DATE  (partition column)
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def log_run_to_bigquery(
    *,
    trace_id: str,
    document_type: str,
    queue: str,
    confidence: float,
    summary: str,
    project_id: str | None = None,
    dataset: str = "agent_runs",
    table: str = "runs",
) -> None:
    """
    Append a processed document run record to BigQuery.

    Skips silently if google-cloud-bigquery is not installed
    (allows local development without GCP credentials).

    Args:
        trace_id: Unique trace ID from DocumentInput.
        document_type: Classified document type.
        queue: Routing queue ("high_confidence" | "needs_review" | "dead_letter").
        confidence: Agent confidence score.
        summary: Extracted document summary.
        project_id: GCP project ID. Falls back to BIGQUERY_PROJECT_ID env var.
        dataset: BigQuery dataset name.
        table: BigQuery table name.
    """
    try:
        from google.cloud import bigquery  # type: ignore
    except ImportError:
        logger.debug("google-cloud-bigquery not installed — skipping BigQuery log.")
        return

    import os
    _project = project_id or os.environ.get("BIGQUERY_PROJECT_ID", "")
    if not _project:
        logger.warning("BIGQUERY_PROJECT_ID not set — skipping BigQuery log.")
        return

    client = bigquery.Client(project=_project)
    table_ref = f"{_project}.{dataset}.{table}"
    now = datetime.now(timezone.utc)

    row: dict[str, Any] = {
        "run_id": trace_id,
        "trace_id": trace_id,
        "document_type": document_type,
        "queue": queue,
        "confidence": confidence,
        "summary": summary[:500],  # truncate for column limit
        "created_at": now.isoformat(),
        "partition_dt": now.date().isoformat(),
    }

    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        logger.error("BigQuery insert errors for trace_id=%s: %s", trace_id, errors)
    else:
        logger.info("BigQuery run logged: trace_id=%s queue=%s", trace_id, queue)
