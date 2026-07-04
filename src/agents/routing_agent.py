"""
Routing agent.

Receives a validated DocumentOutput and decides which queue to route it to:
- high_confidence: auto-processed, no human review needed
- needs_review: routed to human review queue (confidence below threshold)
- dead_letter: processing failed, requires manual intervention
"""

import logging
from src.validation.schemas import DocumentOutput, RoutingDecision
from src.storage.audit_log import log_event
from src.config import settings

logger = logging.getLogger(__name__)


def route_document(output: DocumentOutput) -> RoutingDecision:
    """
    Classify a document output into a routing queue.

    Args:
        output: Validated DocumentOutput from the document agent.

    Returns:
        RoutingDecision with queue assignment and reason.
    """
    if output.confidence >= settings.confidence_threshold:
        queue = "high_confidence"
        reason = f"Confidence {output.confidence:.2f} meets threshold {settings.confidence_threshold}"
    else:
        queue = "needs_review"
        reason = (
            f"Confidence {output.confidence:.2f} below threshold "
            f"{settings.confidence_threshold} — routed to human review"
        )

    decision = RoutingDecision(
        trace_id=output.trace_id,
        document_type=output.document_type,
        queue=queue,
        reason=reason,
        confidence=output.confidence,
    )

    log_event(
        trace_id=output.trace_id,
        stage="routing_agent",
        status="routed",
        detail=f"queue={queue} confidence={output.confidence:.2f}",
    )

    logger.info(
        "Routed trace_id=%s to queue=%s (confidence=%.2f)",
        output.trace_id, queue, output.confidence,
    )

    return decision
