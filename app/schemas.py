"""Pydantic schemas describing the structured workflow output.

These models are the contract between the LLM layer and the rest of the
system. Anything that reaches the database has already been coerced into one
of these shapes, which is what makes the output reliable rather than free-form
chat text.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedFields(BaseModel):
    """Fields pulled out of a document by the extraction step."""

    customer_name: str | None = None
    customer_id: str | None = None
    request_type: str | None = None
    date: str | None = None
    priority: str | None = None
    issue_description: str | None = None
    requested_action: str | None = None
    invoice_number: str | None = None
    vendor_name: str | None = None
    topic: str | None = None
    missing_fields: list[str] = Field(default_factory=list)


class WorkflowResult(BaseModel):
    """The final, review-ready record produced by the pipeline."""

    document_type: str
    priority: str = "Medium"
    customer_id: str | None = None
    customer_name: str | None = None
    request_id: str | None = None
    invoice_number: str | None = None
    vendor_name: str | None = None
    topic: str | None = None
    issue_summary: str | None = None
    requested_action: str | None = None
    summary: str = ""
    routing_decision: str = "General Queue"
    missing_fields: list[str] = Field(default_factory=list)
    validation_status: str = "pass"  # pass | fail
    review_status: str = "Ready for Review"
    confidence_flag: str = "Acceptable"  # Acceptable | Low
    confidence_score: float = 1.0  # 0-1 transparent heuristic score
    classification_confidence: str = "high"  # high | low

    def to_record(self) -> dict:
        """Flat dict suitable for display and JSON export."""
        return self.model_dump()


class ProcessRequest(BaseModel):
    """Incoming request body for the /process endpoint."""

    text: str
    filename: str | None = "pasted_text.txt"


class ValidationReport(BaseModel):
    """Outcome of the rule-based validation layer."""

    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
