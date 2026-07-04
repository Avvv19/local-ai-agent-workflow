"""Tests for Pydantic validation schemas."""
import pytest
from pydantic import ValidationError
from src.validation.schemas import DocumentInput, DocumentOutput, RoutingDecision


class TestDocumentInput:
    def test_valid_input(self):
        doc = DocumentInput(content="This is a valid contract document with sufficient text.")
        assert doc.content == "This is a valid contract document with sufficient text."
        assert doc.source == "api"
        assert len(doc.trace_id) == 36  # UUID format

    def test_content_too_short_raises(self):
        with pytest.raises(ValidationError):
            DocumentInput(content="short")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError):
            DocumentInput(content="     ")

    def test_custom_trace_id(self):
        doc = DocumentInput(content="Valid document content here.", trace_id="custom-id-123")
        assert doc.trace_id == "custom-id-123"

    def test_content_is_stripped(self):
        doc = DocumentInput(content="  padded content with spaces  ")
        assert doc.content == "padded content with spaces"


class TestDocumentOutput:
    def test_valid_output(self):
        out = DocumentOutput(
            document_type="invoice",
            summary="Invoice for services rendered in Q1 2024.",
            confidence=0.92,
            trace_id="abc-123",
        )
        assert out.document_type == "invoice"
        assert out.confidence == 0.92

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            DocumentOutput(
                document_type="invoice",
                summary="A summary of the document contents.",
                confidence=1.5,
                trace_id="abc-123",
            )

    def test_summary_too_short_raises(self):
        with pytest.raises(ValidationError):
            DocumentOutput(
                document_type="invoice",
                summary="Short",
                confidence=0.9,
                trace_id="abc-123",
            )


class TestRoutingDecision:
    def test_high_confidence_routing(self):
        decision = RoutingDecision(
            trace_id="abc-123",
            document_type="invoice",
            queue="high_confidence",
            reason="Confidence 0.92 meets threshold",
            confidence=0.92,
        )
        assert decision.queue == "high_confidence"

    def test_invalid_queue_raises(self):
        with pytest.raises(ValidationError):
            RoutingDecision(
                trace_id="abc-123",
                document_type="invoice",
                queue="invalid_queue",
                reason="test",
                confidence=0.9,
            )
