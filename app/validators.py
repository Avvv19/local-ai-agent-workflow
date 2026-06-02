"""Rule-based validation layer.

Deliberately *not* an LLM. This is plain Python that checks the structured
output before it is trusted, which is what turns unreliable model text into a
dependable workflow. Returns a ValidationReport; callers decide whether to
retry, accept, or escalate to human review.
"""
from __future__ import annotations

import json
import re

from . import config
from .schemas import ValidationReport, WorkflowResult


def parse_json(raw: str) -> tuple[bool, dict]:
    """Best-effort JSON parse that tolerates code fences and surrounding prose."""
    if not raw:
        return False, {}
    cleaned = raw.strip()
    # strip ```json ... ``` fences if a model added them
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned[cleaned.find("{"):] if "{" in cleaned else cleaned
    # grab the outermost {...} if there is leading/trailing prose
    if "{" in cleaned and "}" in cleaned:
        cleaned = cleaned[cleaned.find("{"): cleaned.rfind("}") + 1]
    try:
        return True, json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return False, {}


def validate_result(result: WorkflowResult) -> ValidationReport:
    """Apply all business rules to a finished WorkflowResult."""
    errors: list[str] = []
    warnings: list[str] = []

    if result.document_type not in config.DOCUMENT_TYPES:
        errors.append(f"Unknown document_type: {result.document_type!r}")

    if result.priority not in config.PRIORITIES:
        errors.append(f"Invalid priority: {result.priority!r}")

    if result.routing_decision not in config.ROUTES:
        errors.append(f"Invalid routing_decision: {result.routing_decision!r}")

    if result.review_status not in config.REVIEW_STATUSES:
        errors.append(f"Invalid review_status: {result.review_status!r}")

    if not result.summary or not result.summary.strip():
        errors.append("Summary is empty")
    elif len(result.summary.strip()) < 15:
        warnings.append("Summary is very short")

    if result.missing_fields:
        warnings.append(f"Missing fields: {', '.join(result.missing_fields)}")

    # ID format check (if applicable): customer_id should look like CUS-1234
    if result.customer_id and not re.match(r"^[A-Za-z]{2,5}-\d{2,}$", result.customer_id):
        warnings.append(f"Customer ID has unexpected format: {result.customer_id!r}")

    if result.classification_confidence == "low":
        warnings.append("Low classification confidence")

    return ValidationReport(ok=not errors, errors=errors, warnings=warnings)
