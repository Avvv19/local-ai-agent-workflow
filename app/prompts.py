"""Prompt builders for each workflow step.

Every prompt embeds a ``TASK:`` tag and wraps the document in
``<<<DOCUMENT>>> ... <<<END>>>`` markers. Real models simply read these as part
of the instructions; the mock backend uses them to locate the task and text.
Keeping prompts here (not inline) makes them easy to tune and review.
"""
from __future__ import annotations

from . import config

SYSTEM = (
    "You are a precise document-processing assistant for a business operations "
    "team. You only output what is asked for. When asked for JSON, output a "
    "single valid JSON object and nothing else."
)


def classify_prompt(text: str) -> str:
    categories = "\n".join(f"- {c}" for c in config.DOCUMENT_TYPES)
    return f"""TASK: classify

Classify the following document into exactly one of these categories:
{categories}

Return a JSON object: {{"document_type": "<category>", "confidence": "high|low"}}
Use "low" confidence if the document does not clearly fit a category.

<<<DOCUMENT>>>
{text}
<<<END>>>
"""


def extract_prompt(text: str, document_type: str, strict: bool = False) -> str:
    strict_note = ""
    if strict:
        strict_note = (
            "\nIMPORTANT: Your previous output was not valid JSON. Respond with "
            "ONLY a single valid JSON object. No prose, no markdown, no code "
            "fences.\n"
        )
    return f"""TASK: extract
{strict_note}
The document has been classified as: {document_type}

Extract these fields. Use null when a value is not present.
- customer_name
- customer_id
- invoice_number
- date
- priority (one of: {", ".join(config.PRIORITIES)})
- requested_action
- issue_description
- missing_fields (list of important fields that are absent)

Return a single JSON object with exactly those keys.

<<<DOCUMENT>>>
{text}
<<<END>>>
"""


def summarize_prompt(text: str, document_type: str) -> str:
    return f"""TASK: summarize

Write a concise 1-2 sentence operational summary of this {document_type}.
Answer: what is the request, who is affected, and what action is needed.
Return plain text only.

<<<DOCUMENT>>>
{text}
<<<END>>>
"""


def route_prompt(document_type: str, summary: str, text: str) -> str:
    routes = ", ".join(config.ROUTES)
    return f"""TASK: route

Given a {document_type} with this summary:
"{summary}"

Choose the single best routing destination from: {routes}
Return a JSON object: {{"routing_decision": "<route>"}}

<<<DOCUMENT>>>
{text}
<<<END>>>
"""
