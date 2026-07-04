"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.main import app


@pytest.fixture
def client():
    with patch("src.api.main.init_db"):
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestProcessEndpoint:
    @patch("src.api.main.process_document")
    @patch("src.api.main.route_document")
    def test_process_returns_routing_decision(self, mock_route, mock_process, client):
        from src.validation.schemas import DocumentOutput, RoutingDecision

        mock_process.return_value = DocumentOutput(
            document_type="invoice",
            summary="Invoice for professional services rendered in Q1 2024.",
            confidence=0.92,
            trace_id="test-api-001",
        )
        mock_route.return_value = RoutingDecision(
            trace_id="test-api-001",
            document_type="invoice",
            queue="high_confidence",
            reason="Confidence meets threshold",
            confidence=0.92,
        )

        response = client.post("/process", json={
            "content": "Invoice for professional services rendered in Q1 2024.",
            "source": "test",
            "trace_id": "test-api-001",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["queue"] == "high_confidence"
        assert data["document_type"] == "invoice"
        assert data["status"] == "ok"

    def test_process_rejects_empty_content(self, client):
        response = client.post("/process", json={
            "content": "   ",
            "source": "test",
        })
        assert response.status_code == 422

    def test_process_rejects_too_short_content(self, client):
        response = client.post("/process", json={
            "content": "short",
            "source": "test",
        })
        assert response.status_code == 422
