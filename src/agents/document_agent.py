"""
Document processing agent.

Takes a raw document string, validates the input schema,
sends to OpenAI for field extraction and classification,
validates the output schema, and returns a structured result.

Retry logic: exponential backoff on LLM failures (3 attempts: 2s, 4s, 8s).
Observability: every call is traced in LangSmith automatically.
"""

import os
import time
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.validation.schemas import DocumentInput, DocumentOutput, AgentError
from src.storage.audit_log import log_event
from src.config import settings

logger = logging.getLogger(__name__)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "document-automation"

_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a document analysis agent. Extract structured fields from the document. "
        "Return ONLY valid JSON matching this schema exactly:\n"
        "{\"document_type\": str, \"summary\": str, \"entities\": [str], "
        "\"key_dates\": [str], \"amounts\": [str], \"confidence\": float (0.0-1.0)}"
    )),
    ("human", "Document:\n\n{document_text}"),
])


def _build_chain() -> Any:
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
    return _EXTRACTION_PROMPT | llm | JsonOutputParser()


def process_document(input_data: DocumentInput) -> DocumentOutput:
    """
    Run the document agent pipeline with exponential backoff retry.

    Args:
        input_data: Validated DocumentInput schema.

    Returns:
        Validated DocumentOutput schema.

    Raises:
        AgentError: After MAX_RETRY_ATTEMPTS failures.
    """
    chain = _build_chain()
    last_error: Exception | None = None

    for attempt in range(1, settings.max_retry_attempts + 1):
        try:
            logger.info("Document agent attempt %d/%d", attempt, settings.max_retry_attempts)
            raw = chain.invoke({"document_text": input_data.content})

            output = DocumentOutput(
                document_type=raw["document_type"],
                summary=raw["summary"],
                entities=raw.get("entities", []),
                key_dates=raw.get("key_dates", []),
                amounts=raw.get("amounts", []),
                confidence=raw["confidence"],
                trace_id=input_data.trace_id,
            )

            log_event(
                trace_id=input_data.trace_id,
                stage="document_agent",
                status="success",
                detail=f"type={output.document_type} confidence={output.confidence:.2f}",
            )
            return output

        except Exception as exc:
            last_error = exc
            backoff = 2 ** attempt
            logger.warning(
                "Document agent attempt %d failed: %s. Retrying in %ds.",
                attempt, exc, backoff,
            )
            log_event(
                trace_id=input_data.trace_id,
                stage="document_agent",
                status=f"retry_{attempt}",
                detail=str(exc),
            )
            if attempt < settings.max_retry_attempts:
                time.sleep(backoff)

    log_event(
        trace_id=input_data.trace_id,
        stage="document_agent",
        status="dead_letter",
        detail=str(last_error),
    )
    raise AgentError(
        message=f"Document agent failed after {settings.max_retry_attempts} attempts",
        trace_id=input_data.trace_id,
        last_error=str(last_error),
    )
