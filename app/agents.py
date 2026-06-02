"""Individual workflow steps ("agents") plus text cleaning.

Each function does one job and returns structured data. They are deliberately
small and independently testable. The orchestrator wires them together.
"""
from __future__ import annotations

import re

from . import config, prompts
from .llm_client import LLMClient
from .schemas import ExtractedFields
from .validators import parse_json


def clean_text(text: str) -> str:
    """Normalise whitespace and strip obvious noise before processing."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)          # collapse runs of spaces/tabs
    text = re.sub(r"\n{3,}", "\n\n", text)        # collapse blank lines
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(lines).strip()


def classify(llm: LLMClient, text: str) -> tuple[str, str]:
    """Return (document_type, confidence)."""
    raw = llm.generate(prompts.classify_prompt(text), system=prompts.SYSTEM,
                       json_mode=True)
    ok, data = parse_json(raw)
    doc_type = data.get("document_type") if ok else None
    if doc_type not in config.DOCUMENT_TYPES:
        return "General Inquiry", "low"
    return doc_type, data.get("confidence", "high")


def extract(llm: LLMClient, text: str, document_type: str,
            max_retries: int = config.MAX_EXTRACTION_RETRIES
            ) -> tuple[ExtractedFields, bool]:
    """Extract fields with a stricter retry if the JSON is unpar. Returns
    (fields, json_was_valid)."""
    valid = False
    data: dict = {}
    for attempt in range(max_retries + 1):
        raw = llm.generate(
            prompts.extract_prompt(text, document_type, strict=attempt > 0),
            system=prompts.SYSTEM,
            json_mode=True,
        )
        valid, data = parse_json(raw)
        if valid:
            break
    # keep only known schema keys
    allowed = ExtractedFields.model_fields.keys()
    filtered = {k: v for k, v in data.items() if k in allowed}
    return ExtractedFields(**filtered), valid


def summarize(llm: LLMClient, text: str, document_type: str) -> str:
    raw = llm.generate(prompts.summarize_prompt(text, document_type),
                       system=prompts.SYSTEM)
    return raw.strip()


def route(llm: LLMClient, document_type: str, summary: str, text: str) -> str:
    raw = llm.generate(prompts.route_prompt(document_type, summary, text),
                       system=prompts.SYSTEM, json_mode=True)
    ok, data = parse_json(raw)
    decision = data.get("routing_decision") if ok else None
    if decision not in config.ROUTES:
        return "General Queue"
    return decision


def compute_missing_fields(document_type: str, fields: ExtractedFields) -> list[str]:
    """Deterministically check which *required* fields for this document type
    are absent. This is what drives human-review escalation."""
    required = config.REQUIRED_FIELDS_BY_TYPE.get(document_type, [])
    data = fields.model_dump()
    return [f for f in required if not data.get(f)]
