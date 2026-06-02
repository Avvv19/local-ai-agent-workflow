"""LLM client abstraction.

Two backends implement the same tiny interface:

* ``OllamaClient``  -> talks to a local Ollama server (real Llama 3).
* ``MockLLMClient`` -> deterministic, dependency-free responses derived from
  the document text. It lets the entire pipeline, API, tests, and evaluation
  run on any machine with no model installed, which keeps the project genuinely
  reproducible.

Both return raw strings. Parsing / validation happens downstream, exactly as it
would with a real model.
"""
from __future__ import annotations

import json
import re

from . import config

# Markers the prompt builder uses so the mock can locate the task + document.
TASK_RE = re.compile(r"TASK:\s*(\w+)")
DOC_RE = re.compile(r"<<<DOCUMENT>>>(.*?)<<<END>>>", re.DOTALL)


class LLMClient:
    """Interface. Subclasses implement ``generate``."""

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False) -> str:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Real backend
# --------------------------------------------------------------------------- #
class OllamaClient(LLMClient):
    """Calls a local Ollama server's /api/generate endpoint."""

    def __init__(self, host: str | None = None, model: str | None = None):
        self.host = (host or config.OLLAMA_HOST).rstrip("/")
        self.model = model or config.OLLAMA_MODEL

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False) -> str:
        import requests  # imported lazily so mock-only installs stay slim

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {"temperature": 0.0},
        }
        if json_mode:
            payload["format"] = "json"
        resp = requests.post(
            f"{self.host}/api/generate",
            json=payload,
            timeout=config.OLLAMA_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


# --------------------------------------------------------------------------- #
# Deterministic mock backend
# --------------------------------------------------------------------------- #
_CATEGORY_KEYWORDS = [
    ("Billing Request", ["invoice", "billing", "overcharge", "refund", "charge", "payment"]),
    ("Customer Complaint", ["complaint", "unacceptable", "angry", "disappointed", "terrible", "frustrated"]),
    ("Support Ticket", ["error", "bug", "not working", "broken", "crash", "login", "password", "ticket"]),
    ("Vendor Request", ["vendor", "purchase order", "supplier", "procurement", "po number"]),
    ("Policy Question", ["policy", "exception", "allowed", "permitted", "guideline", "compliance"]),
    ("Internal Operations Request", ["internal", "onboard", "provision", "access request", "setup", "operations request", "equipment request"]),
]


def _detect_category(text: str) -> str:
    low = text.lower()
    best, best_hits = "General Inquiry", 0
    for category, keywords in _CATEGORY_KEYWORDS:
        hits = sum(1 for k in keywords if k in low)
        if hits > best_hits:
            best, best_hits = category, hits
    return best


def _detect_priority(text: str) -> str | None:
    """Return an explicit priority if present, else None (so a genuinely
    missing priority is detectable rather than silently defaulted)."""
    low = text.lower()
    m = re.search(r"priority\s*[:\-]\s*(low|medium|high|urgent)", low)
    if m:
        return m.group(1).capitalize()
    if any(w in low for w in ["urgent", "asap", "immediately", "critical", "emergency"]):
        return "Urgent"
    if "high priority" in low:
        return "High"
    if any(w in low for w in ["low priority", "whenever", "no rush"]):
        return "Low"
    return None


def _grab(text: str, label_pattern: str) -> str | None:
    m = re.search(label_pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


class MockLLMClient(LLMClient):
    """Returns plausible, deterministic outputs parsed from the document."""

    def generate(self, prompt: str, system: str | None = None,
                 json_mode: bool = False) -> str:
        task = (TASK_RE.search(prompt) or [None, ""])[1]
        doc_match = DOC_RE.search(prompt)
        doc = doc_match.group(1).strip() if doc_match else prompt

        if task == "classify":
            return self._classify(doc)
        if task == "extract":
            return self._extract(doc)
        if task == "summarize":
            return self._summarize(doc)
        if task == "route":
            return self._route(prompt, doc)
        return ""

    # -- individual tasks --------------------------------------------------- #
    def _classify(self, doc: str) -> str:
        category = _detect_category(doc)
        # low confidence when nothing matched strongly
        confidence = "low" if category == "General Inquiry" else "high"
        return json.dumps({"document_type": category, "confidence": confidence})

    def _extract(self, doc: str) -> str:
        fields = {
            "customer_name": _grab(doc, r"(?:customer name|name)\s*[:\-]\s*([A-Za-z .'-]{2,60})"),
            "customer_id": _grab(doc, r"(?:customer id|cust(?:omer)? id)\s*[:\-]?\s*([A-Za-z]+-?\d+)")
                            or _grab(doc, r"\b(CUS-\d+)\b"),
            "invoice_number": _grab(doc, r"(?:invoice(?: number)?|inv)\s*[:\-#]?\s*([A-Za-z]*-?\d+)")
                              or _grab(doc, r"\b(INV-\d+)\b"),
            "date": _grab(doc, r"(?:date)\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9/.\- ]{6,12})"),
            "priority": _detect_priority(doc),
            "requested_action": _grab(doc, r"(?:requested action|action requested)\s*[:\-]\s*([^\n]{4,160})"),
            "issue_description": _grab(doc, r"(?:issue|description|problem|complaint|question)\s*[:\-]\s*([^\n]{4,240})"),
            "vendor_name": _grab(doc, r"(?:vendor name|vendor|supplier)\s*[:\-]\s*([A-Za-z0-9 .,'&-]{2,60})"),
            "request_type": _grab(doc, r"(?:request type|type of request)\s*[:\-]\s*([A-Za-z0-9 /-]{2,60})"),
            "topic": _grab(doc, r"(?:topic|subject)\s*[:\-]\s*([A-Za-z0-9 /-]{2,80})"),
        }
        # missing_fields are computed deterministically downstream by the
        # orchestrator (validation concern, not a model concern).
        fields["missing_fields"] = []
        return json.dumps({k: v for k, v in fields.items()})

    def _summarize(self, doc: str) -> str:
        category = _detect_category(doc)
        first = re.sub(r"\s+", " ", doc).strip()
        snippet = first[:160] + ("..." if len(first) > 160 else "")
        return (f"{category}: {snippet} Action requested by the sender; "
                f"routed for the appropriate team to review.")

    def _route(self, prompt: str, doc: str) -> str:
        category = _detect_category(doc)
        route_map = {
            "Billing Request": "Finance Review",
            "Vendor Request": "Finance Review",
            "Support Ticket": "Technical Review",
            "Customer Complaint": "Customer Support Review",
            "Internal Operations Request": "Operations Review",
            "Policy Question": "Operations Review",
            "General Inquiry": "General Queue",
        }
        route = route_map.get(category, "General Queue")
        return json.dumps({"routing_decision": route})


def get_llm_client(backend: str | None = None) -> LLMClient:
    """Factory honouring the LLM_BACKEND setting.

    "mock"      -> deterministic, no model needed (default)
    "ollama"    -> local Llama 3 via Ollama HTTP API
    "langchain" -> same Ollama model, but invoked through a LangChain
                   Runnable pipeline (demonstrates LangChain orchestration)
    """
    backend = (backend or config.LLM_BACKEND).lower()
    if backend == "ollama":
        return OllamaClient()
    if backend == "langchain":
        from .langchain_backend import LangChainClient
        return LangChainClient()
    return MockLLMClient()
