"""Tests for agent logic — mocked LLM calls."""
import pytest
from unittest.mock import patch, MagicMock
from src.validation.schemas import DocumentInput, DocumentOutput, AgentError


class TestDocumentAgentRetryLogic:
    """Tests that retry + dead-letter logic works without hitting the API."""

    @patch("src.agents.document_agent._build_chain")
    def test_success_on_first_attempt(self, mock_build):
        from src.agents.document_agent import process_document

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {
            "document_type": "invoice",
            "summary": "Invoice for professional services rendered in Q1 2024.",
            "entities": ["Acme Corp", "Vendor LLC"],
            "key_dates": ["2024-01-31"],
            "amounts": ["$5,000"],
            "confidence": 0.95,
        }
        mock_build.return_value = mock_chain

        doc = DocumentInput(content="Invoice for services.", trace_id="test-001")
        result = process_document(doc)

        assert result.document_type == "invoice"
        assert result.confidence == 0.95
        mock_chain.invoke.assert_called_once()

    @patch("src.agents.document_agent._build_chain")
    @patch("src.agents.document_agent.time.sleep")
    def test_retries_on_failure_then_succeeds(self, mock_sleep, mock_build):
        from src.agents.document_agent import process_document

        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Timeout"),
            {
                "document_type": "contract",
                "summary": "Service agreement between two parties for ongoing work.",
                "entities": [],
                "key_dates": [],
                "amounts": [],
                "confidence": 0.88,
            },
        ]
        mock_build.return_value = mock_chain

        doc = DocumentInput(content="Contract document text.", trace_id="test-002")
        result = process_document(doc)

        assert result.document_type == "contract"
        assert mock_chain.invoke.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.agents.document_agent._build_chain")
    @patch("src.agents.document_agent.time.sleep")
    def test_raises_agent_error_after_max_retries(self, mock_sleep, mock_build):
        from src.agents.document_agent import process_document

        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = Exception("Persistent failure")
        mock_build.return_value = mock_chain

        doc = DocumentInput(content="Some document content here.", trace_id="test-003")
        with pytest.raises(AgentError) as exc_info:
            process_document(doc)

        assert exc_info.value.trace_id == "test-003"
        assert mock_chain.invoke.call_count == 3


class TestRoutingAgent:
    def test_routes_high_confidence(self):
        from src.agents.routing_agent import route_document
        from src.validation.schemas import DocumentOutput

        output = DocumentOutput(
            document_type="invoice",
            summary="Invoice for professional services rendered in Q1 2024.",
            confidence=0.95,
            trace_id="test-routing-001",
        )
        decision = route_document(output)
        assert decision.queue == "high_confidence"

    def test_routes_to_review_below_threshold(self):
        from src.agents.routing_agent import route_document
        from src.validation.schemas import DocumentOutput

        output = DocumentOutput(
            document_type="unknown",
            summary="Unclear document that could not be confidently classified.",
            confidence=0.40,
            trace_id="test-routing-002",
        )
        decision = route_document(output)
        assert decision.queue == "needs_review"
