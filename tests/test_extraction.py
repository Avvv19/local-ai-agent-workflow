"""Tests for extraction steps and the end-to-end pipeline (mock backend)."""
from app import agents
from app.llm_client import MockLLMClient
from app.orchestrator import run_workflow

BILLING = """Customer ID: CUS-1029
Invoice Number: INV-88421
Issue: billed twice for my subscription, suspected overcharge.
Requested Action: refund the duplicate charge."""

SUPPORT = """Support Ticket
Customer ID: CUS-4471
Issue: I cannot log in, the page shows an error after my password.
Requested Action: fix my login access. This is high priority."""


def test_clean_text_collapses_whitespace():
    messy = "line1   \n\n\n\n  line2\t\tend"
    out = agents.clean_text(messy)
    assert "\n\n\n" not in out
    assert "  " not in out


def test_classify_billing():
    llm = MockLLMClient()
    doc_type, conf = agents.classify(llm, BILLING)
    assert doc_type == "Billing Request"
    assert conf in ("high", "low")


def test_extract_returns_fields():
    llm = MockLLMClient()
    fields, valid = agents.extract(llm, BILLING, "Billing Request")
    assert valid
    assert fields.customer_id == "CUS-1029"
    assert fields.invoice_number == "INV-88421"


def test_pipeline_billing_ready():
    run = run_workflow(BILLING)
    assert run.result.document_type == "Billing Request"
    assert run.result.routing_decision == "Finance Review"
    assert run.validation.ok


def test_pipeline_support_routes_technical():
    run = run_workflow(SUPPORT)
    assert run.result.document_type == "Support Ticket"
    assert run.result.routing_decision == "Technical Review"
    assert run.result.priority == "High"


def test_pipeline_empty_text_flags_human_review():
    run = run_workflow("   ")
    assert run.result.review_status == "Needs Human Review"


def test_pipeline_vague_text_flags_human_review():
    run = run_workflow("Please look into my invoice, something seems off.")
    # missing customer_id / requested action -> should escalate
    assert run.result.review_status == "Needs Human Review"
    assert run.result.missing_fields
