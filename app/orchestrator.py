"""Workflow orchestrator.

This is the heart of the system. It runs the steps in order, applies the
validation gate, and makes an explicit escalation decision: a result either is
"Ready for Review" or gets flagged "Needs Human Review". It records a log entry
for every step so the run is fully traceable — that audit trail is what makes
this a workflow rather than a one-shot chatbot call.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import agents, config
from .confidence import compute_confidence, flag_for_score
from .llm_client import LLMClient, get_llm_client
from .schemas import ValidationReport, WorkflowResult
from .validators import validate_result


@dataclass
class StepLog:
    step_name: str
    status: str  # ok | retry | fail | flag
    message: str = ""


@dataclass
class RunOutput:
    result: WorkflowResult
    validation: ValidationReport
    logs: list[StepLog] = field(default_factory=list)
    cleaned_text: str = ""


def run_workflow(text: str, llm: LLMClient | None = None) -> RunOutput:
    """Process a single document end to end."""
    llm = llm or get_llm_client()
    logs: list[StepLog] = []

    # Step 1-2: intake + cleaning
    logs.append(StepLog("received", "ok", f"{len(text or '')} chars received"))
    cleaned = agents.clean_text(text)
    logs.append(StepLog("clean_text", "ok", f"{len(cleaned)} chars after cleaning"))
    if not cleaned:
        result = WorkflowResult(
            document_type="General Inquiry",
            summary="Empty or unreadable document.",
            routing_decision="Human Review Required",
            review_status="Needs Human Review",
            confidence_flag="Low",
            classification_confidence="low",
            confidence_score=0.0,
            missing_fields=["document_text"],
        )
        logs.append(StepLog("intake", "flag", "No usable text"))
        return RunOutput(result, validate_result(result), logs, cleaned)

    # Step 3: classification
    doc_type, confidence = agents.classify(llm, cleaned)
    logs.append(StepLog("classify", "ok", f"{doc_type} (confidence={confidence})"))

    # Step 4: extraction with retry
    fields, json_valid = agents.extract(llm, cleaned, doc_type)
    logs.append(StepLog(
        "extract",
        "ok" if json_valid else "retry",
        "valid JSON" if json_valid else "extraction JSON invalid after retries",
    ))

    # Step 5: summarization
    summary = agents.summarize(llm, cleaned, doc_type)
    logs.append(StepLog("summarize", "ok" if summary else "fail",
                        f"{len(summary)} chars"))

    # Step 6: routing
    routing = agents.route(llm, doc_type, summary, cleaned)
    logs.append(StepLog("route", "ok", routing))

    # Deterministic required-field check (drives escalation, not the LLM)
    missing = agents.compute_missing_fields(doc_type, fields)

    # Assemble result
    result = WorkflowResult(
        document_type=doc_type,
        priority=fields.priority if fields.priority in config.PRIORITIES else "Medium",
        customer_id=fields.customer_id,
        customer_name=fields.customer_name,
        request_id=fields.customer_id or fields.invoice_number,
        invoice_number=fields.invoice_number,
        vendor_name=fields.vendor_name,
        topic=fields.topic,
        issue_summary=fields.issue_description,
        requested_action=fields.requested_action,
        summary=summary,
        routing_decision=routing,
        missing_fields=missing,
        classification_confidence=confidence,
    )

    # Step 7: validation gate
    report = validate_result(result)
    result.validation_status = "pass" if report.ok else "fail"
    logs.append(StepLog(
        "validate",
        "ok" if report.ok else "fail",
        "; ".join(report.errors) or "passed",
    ))

    # Confidence score (transparent heuristic combining the workflow checks:
    # JSON validity, required-field completion, allowed type/route validity,
    # summary completeness, and missing-field count).
    score = compute_confidence(confidence, json_valid, result.missing_fields,
                               summary, report.ok)
    result.confidence_score = score
    logs.append(StepLog("confidence", "ok", f"score={score}"))

    # Step 8-9: escalation decision
    too_short = len(cleaned.split()) < 5
    needs_human = (
        not report.ok
        or not json_valid
        or confidence == "low"
        or bool(result.missing_fields)
        or score < 0.6
        or too_short
    )
    if needs_human:
        result.review_status = "Needs Human Review"
        result.confidence_flag = "Low"
        if result.routing_decision == "General Queue":
            result.routing_decision = "Human Review Required"
        reasons = []
        if not report.ok:
            reasons.append("validation errors")
        if not json_valid:
            reasons.append("invalid extraction JSON after retry")
        if confidence == "low":
            reasons.append("ambiguous document type (low confidence)")
        if result.missing_fields:
            reasons.append(f"missing required fields: {', '.join(result.missing_fields)}")
        if score < 0.6:
            reasons.append(f"confidence score below threshold ({score})")
        if too_short:
            reasons.append("input too short or ambiguous")
        logs.append(StepLog("human_review", "flag", "; ".join(reasons)))
    else:
        result.review_status = "Ready for Review"
        result.confidence_flag = flag_for_score(score)
        logs.append(StepLog("human_review", "ok", "not required"))

    # re-validate after possible route change
    report = validate_result(result)
    result.validation_status = "pass" if report.ok else "fail"
    return RunOutput(result, report, logs, cleaned)
