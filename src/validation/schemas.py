"""
Pydantic v2 schemas for all agent inputs and outputs.

Every agent boundary uses these schemas for strict validation.
Invalid data raises ValidationError before reaching any downstream system.
"""

from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, field_validator
import uuid


class DocumentInput(BaseModel):
    """Input schema — validated at the FastAPI boundary before entering the agent pipeline."""

    content: str = Field(..., min_length=10, description="Raw document text")
    source: str = Field(default="api", description="Originating source identifier")
    trace_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique trace ID for audit logging and LangSmith",
    )

    @field_validator("content")
    @classmethod
    def content_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Document content cannot be blank or whitespace only")
        return v.strip()


class DocumentOutput(BaseModel):
    """Output schema — validated after every LLM call before passing to the routing agent."""

    document_type: str = Field(..., description="Classified document type")
    summary: str = Field(..., min_length=10, description="Extracted document summary")
    entities: list[str] = Field(default_factory=list)
    key_dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent confidence score")
    trace_id: str = Field(..., description="Propagated from DocumentInput")


class RoutingDecision(BaseModel):
    """Routing output — produced by the routing agent after confidence scoring."""

    trace_id: str
    document_type: str
    queue: Literal["high_confidence", "needs_review", "dead_letter"]
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AgentError(Exception):
    """Raised when an agent exceeds max retry attempts."""

    def __init__(self, message: str, trace_id: str, last_error: str) -> None:
        super().__init__(message)
        self.trace_id = trace_id
        self.last_error = last_error


class ProcessResponse(BaseModel):
    """HTTP response schema for the /process endpoint."""

    trace_id: str
    queue: str
    document_type: str
    confidence: float
    summary: str
    status: str = "ok"
