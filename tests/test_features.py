"""Tests for the advanced features: confidence scoring, metrics, CSV export,
role-based review queue, and optional API-key auth."""
import pytest
from fastapi.testclient import TestClient

from app import config, database
from app.confidence import compute_confidence, flag_for_score
from app.orchestrator import run_workflow


# ---- confidence scoring ---------------------------------------------------
def test_confidence_full():
    assert compute_confidence("high", True, [], "a sufficiently long summary") == 1.0


def test_confidence_penalised():
    score = compute_confidence("low", False, ["customer_id"], "")
    assert 0.0 <= score < 0.6
    assert flag_for_score(score) == "Low"


def test_pipeline_sets_confidence_score():
    run = run_workflow("Customer ID: CUS-1 invoice INV-9 refund the duplicate charge")
    assert 0.0 <= run.result.confidence_score <= 1.0
    assert run.result.document_type == "Billing Request"


# ---- DB-backed features (isolated sqlite) ---------------------------------
@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "database_url", f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "out")
    database._engines.clear()
    database.init_db()
    yield database
    database._engines.clear()


def test_metrics_and_csv(db):
    db.save_run(run_workflow("Customer ID: CUS-1 refund duplicate charge invoice"),
                "a.txt", "x")
    db.save_run(run_workflow("vague invoice issue, something seems off"), "b.txt", "y")
    m = db.get_metrics()
    assert m["total_documents"] == 2
    assert m["needs_human_review"] >= 1
    assert m["avg_confidence"] is not None
    csv_text = db.export_csv()
    assert "document_id" in csv_text.splitlines()[0]
    assert len(csv_text.splitlines()) == 3  # header + 2 rows


def test_role_based_queue(db):
    db.save_run(run_workflow("vague invoice issue, something off"), "b.txt", "y")
    finance = db.get_review_queue(role="finance")
    engineering = db.get_review_queue(role="engineering")
    assert len(finance) >= 1
    assert all(item["role"] == "finance" for item in finance)
    assert engineering == []


def test_update_routing_and_resolve_decision(db):
    db.save_run(run_workflow("vague invoice issue, something off"), "b.txt", "y")
    item = db.get_review_queue()[0]
    assert db.update_routing(item["document_id"], "Operations Review") is True
    assert db.update_routing(item["document_id"], "Not A Route") is False
    assert db.resolve_review(item["id"], "approved") is True
    # after approval the open queue is empty
    assert db.get_review_queue() == []


def test_reviewed_only_export(db):
    db.save_run(run_workflow("vague invoice issue, something off"), "b.txt", "y")
    assert len(db.export_csv(reviewed_only=True).splitlines()) == 1  # header only
    item = db.get_review_queue()[0]
    db.resolve_review(item["id"], "resolved")
    assert len(db.export_csv(reviewed_only=True).splitlines()) == 2  # header + 1


# ---- per-type required fields --------------------------------------------
def test_billing_requires_invoice():
    from app.agents import compute_missing_fields
    from app.schemas import ExtractedFields
    f = ExtractedFields(customer_id="CUS-1", requested_action="refund",
                        issue_description="overcharge")  # no invoice_number
    assert "invoice_number" in compute_missing_fields("Billing Request", f)


def test_support_requires_priority():
    from app.agents import compute_missing_fields
    from app.schemas import ExtractedFields
    f = ExtractedFields(issue_description="bug", requested_action="fix")  # no priority
    assert "priority" in compute_missing_fields("Support Ticket", f)


def test_vendor_requires_vendor_name():
    from app.agents import compute_missing_fields
    from app.schemas import ExtractedFields
    f = ExtractedFields(request_type="onboard", requested_action="add us")
    assert "vendor_name" in compute_missing_fields("Vendor Request", f)


# ---- auth -----------------------------------------------------------------
def test_auth_blocks_without_key(tmp_path, monkeypatch):
    monkeypatch.setattr(config.settings, "database_url", f"sqlite:///{tmp_path/'a.db'}")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "o")
    monkeypatch.setattr(config.settings, "enable_auth", True)
    monkeypatch.setattr(config.settings, "api_key", "secret123")
    database._engines.clear()
    database.init_db()
    from app.api import app
    with TestClient(app) as c:
        assert c.post("/process", json={"text": "hello"}).status_code == 401
        ok = c.post("/process", json={"text": "Customer ID: CUS-1 refund invoice"},
                    headers={"X-API-Key": "secret123"})
        assert ok.status_code == 200
    database._engines.clear()
