"""
End-to-end smoke test.

Runs the full pipeline against sample documents with a stubbed LLM.
Pass = pipeline completes without exceptions and routing decision is produced.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.schemas import DocumentInput


SAMPLE_DOCUMENTS = [
    {
        "name": "invoice_sample",
        "content": (
            "INVOICE #INV-2024-001\n"
            "Vendor: Acme Solutions LLC\n"
            "Client: Globex Corporation\n"
            "Amount Due: $12,500.00\n"
            "Due Date: 2024-02-15\n"
            "Services: Software development services for Q4 2023 engagement."
        ),
        "expected_type": "invoice",
        "min_confidence": 0.7,
    },
    {
        "name": "contract_sample",
        "content": (
            "SERVICE AGREEMENT\n"
            "This agreement is entered into between Alpha Corp ('Client') and "
            "Beta Services Inc ('Vendor') effective January 1, 2024. "
            "The Vendor agrees to provide software consulting services for a "
            "period of 12 months. Total contract value: $180,000."
        ),
        "expected_type": "contract",
        "min_confidence": 0.7,
    },
]


def run_smoke_test() -> None:
    """Run pipeline smoke test against sample documents."""
    print("=" * 60)
    print("SMOKE TEST: Multi-Agent Document Automation System")
    print("=" * 60)

    passed = 0
    failed = 0

    for sample in SAMPLE_DOCUMENTS:
        print(f"\n[TEST] {sample['name']}")

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {
            "document_type": sample["expected_type"],
            "summary": f"This is a {sample['expected_type']} document summary with sufficient detail.",
            "entities": ["Entity A", "Entity B"],
            "key_dates": ["2024-01-01"],
            "amounts": ["$10,000"],
            "confidence": sample["min_confidence"] + 0.1,
        }

        with patch("src.agents.document_agent._build_chain", return_value=mock_chain):
            with patch("src.storage.audit_log.log_event"):
                try:
                    from src.agents.document_agent import process_document
                    from src.agents.routing_agent import route_document

                    doc_input = DocumentInput(
                        content=sample["content"],
                        source="smoke_test",
                    )
                    doc_output = process_document(doc_input)
                    routing = route_document(doc_output)

                    assert doc_output.document_type == sample["expected_type"], (
                        f"Expected type {sample['expected_type']}, got {doc_output.document_type}"
                    )
                    assert doc_output.confidence >= sample["min_confidence"], (
                        f"Confidence {doc_output.confidence} below {sample['min_confidence']}"
                    )
                    assert routing.queue in ("high_confidence", "needs_review"), (
                        f"Unexpected queue: {routing.queue}"
                    )

                    print(f"  PASS — type={doc_output.document_type} "
                          f"confidence={doc_output.confidence:.2f} "
                          f"queue={routing.queue}")
                    passed += 1

                except Exception as exc:
                    print(f"  FAIL — {exc}")
                    failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_smoke_test()
