"""
LangSmith tracing setup for local-ai-agent-workflow.

Drop this file into app/utils/langsmith_setup.py
Call init_langsmith() once at application startup (e.g., in app/main.py).

Two environment variables required (add to .env):
    LANGCHAIN_API_KEY=ls__...        # from smith.langchain.com -> Settings -> API Keys
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_PROJECT=local-ai-agent-workflow   # optional, groups traces by project
"""

import os
import logging

logger = logging.getLogger(__name__)


def init_langsmith() -> bool:
    """
    Initialise LangSmith tracing.
    Returns True if tracing is active, False if disabled or misconfigured.
    Call once at application startup.
    """
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    if not tracing_enabled:
        logger.info("LangSmith tracing disabled (LANGCHAIN_TRACING_V2 not set to true)")
        return False

    if not api_key:
        logger.warning("LangSmith tracing enabled but LANGCHAIN_API_KEY is missing — tracing will fail")
        return False

    # LangChain reads these env vars automatically — no further code needed.
    # Setting them here confirms they are present at startup.
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "local-ai-agent-workflow")

    logger.info(
        "LangSmith tracing active — project: %s",
        os.environ["LANGCHAIN_PROJECT"]
    )
    return True


def get_run_metadata(document_id: str, document_type: str = "unknown") -> dict:
    """
    Returns metadata dict to pass as langsmith_extra to any LangChain call.
    Attaches document-level context to every trace so you can filter by
    document_id in the LangSmith UI.

    Usage:
        chain.invoke(input, config={"metadata": get_run_metadata(doc_id)})
    """
    return {
        "document_id": document_id,
        "document_type": document_type,
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


# ── Example: how to use in an agent ──────────────────────────────────────────
#
# from app.utils.langsmith_setup import init_langsmith, get_run_metadata
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import ChatPromptTemplate
#
# # In app/main.py (FastAPI startup):
# @app.on_event("startup")
# async def startup():
#     init_langsmith()
#
# # In app/agents/extractor.py:
# def run_extraction(document_id: str, text: str) -> dict:
#     llm = ChatOpenAI(model="gpt-4o", temperature=0)
#     prompt = ChatPromptTemplate.from_template("Extract fields from: {text}")
#     chain = prompt | llm
#     result = chain.invoke(
#         {"text": text},
#         config={"metadata": get_run_metadata(document_id, "contract")}
#     )
#     return result
#
# Every call to chain.invoke() is now traced in LangSmith automatically.
# No other code changes needed.
# ─────────────────────────────────────────────────────────────────────────────
