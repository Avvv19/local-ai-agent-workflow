"""Tests for the rule-based validation layer."""
from app.schemas import WorkflowResult
from app.validators import parse_json, validate_result


def test_parse_json_plain():
    ok, data = parse_json('{"a": 1}')
    assert ok and data == {"a": 1}


def test_parse_json_with_code_fence():
    ok, data = parse_json('```json\n{"a": 1}\n```')
    assert ok and data["a"] == 1


def test_parse_json_with_surrounding_prose():
    ok, data = parse_json('Sure! Here you go: {"a": 1} hope that helps')
    assert ok and data["a"] == 1


def test_parse_json_invalid():
    ok, data = parse_json("not json at all")
    assert not ok and data == {}


def test_valid_result_passes():
    r = WorkflowResult(
        document_type="Billing Request",
        priority="Medium",
        summary="Customer requests a review of a duplicate invoice charge.",
        routing_decision="Finance Review",
        review_status="Ready for Review",
    )
    report = validate_result(r)
    assert report.ok
    assert report.errors == []


def test_invalid_route_fails():
    r = WorkflowResult(
        document_type="Billing Request",
        summary="A reasonably long summary string here.",
        routing_decision="Not A Real Route",
    )
    report = validate_result(r)
    assert not report.ok
    assert any("routing_decision" in e for e in report.errors)


def test_empty_summary_fails():
    r = WorkflowResult(
        document_type="Support Ticket",
        summary="",
        routing_decision="Technical Review",
    )
    report = validate_result(r)
    assert not report.ok


def test_missing_fields_warns():
    r = WorkflowResult(
        document_type="Billing Request",
        summary="A reasonably long summary string here for testing.",
        routing_decision="Finance Review",
        missing_fields=["customer_id"],
    )
    report = validate_result(r)
    assert report.ok  # warning, not error
    assert any("Missing fields" in w for w in report.warnings)
