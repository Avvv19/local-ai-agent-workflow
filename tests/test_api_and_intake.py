"""Tests for the retry path, the FastAPI layer, and PDF intake.

These cover the three gaps the core suite missed: that a malformed-JSON
extraction is recovered by the stricter retry, that the API endpoints work end
to end, and that PDF uploads are parsed.
"""

import pytest
from fastapi.testclient import TestClient

from app import agents, config
from app.intake import extract_text
from app.llm_client import LLMClient


# --------------------------------------------------------------------------- #
# Retry path
# --------------------------------------------------------------------------- #
class FlakyExtractLLM(LLMClient):
    """Returns broken JSON on the first extract call, valid JSON after that."""

    def __init__(self):
        self.extract_calls = 0

    def generate(self, prompt, system=None, json_mode=False):
        if "TASK: extract" in prompt:
            self.extract_calls += 1
            if self.extract_calls == 1:
                return "Sorry, here is the data but not as json"  # invalid
            return '{"customer_id": "CUS-1", "priority": "Medium"}'
        return "{}"


def test_extract_retries_on_bad_json():
    llm = FlakyExtractLLM()
    fields, valid = agents.extract(llm, "some doc", "Billing Request", max_retries=2)
    assert valid is True
    assert llm.extract_calls == 2          # retried exactly once
    assert fields.customer_id == "CUS-1"


def test_extract_gives_up_after_retries():
    class AlwaysBad(LLMClient):
        def generate(self, prompt, system=None, json_mode=False):
            return "never valid json"
    fields, valid = agents.extract(AlwaysBad(), "doc", "Support Ticket", max_retries=2)
    assert valid is False                  # reported as invalid, not crashed


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@pytest.fixture
def client(tmp_path, monkeypatch):
    # isolate the DB + outputs for the test
    from app import database
    monkeypatch.setattr(config.settings, "database_url", f"sqlite:///{tmp_path/'test.db'}")
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "outputs")
    database._engines.clear()
    database.init_db()
    from app.api import app
    with TestClient(app) as c:
        yield c
    database._engines.clear()


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "backend" in body


def test_process_and_retrieve(client):
    doc = "Customer ID: CUS-9 Invoice: INV-7 please refund the duplicate charge"
    r = client.post("/process", json={"text": doc, "filename": "t.txt"}).json()
    assert r["document_id"] >= 1
    assert r["result"]["document_type"] == "Billing Request"
    got = client.get(f"/result/{r['document_id']}").json()
    steps = [x["step_name"] for x in got["logs"]]
    assert "classify" in steps and "validate" in steps


def test_process_rejects_empty(client):
    assert client.post("/process", json={"text": "   "}).status_code == 400


def test_history_and_queue(client):
    client.post("/process", json={"text": "vague invoice issue, something off"})
    assert isinstance(client.get("/history").json(), list)
    assert isinstance(client.get("/review-queue").json(), list)


# --------------------------------------------------------------------------- #
# PDF intake
# --------------------------------------------------------------------------- #
def test_extract_text_from_txt():
    assert extract_text("a.txt", b"hello world") == "hello world"


def test_extract_text_from_pdf():
    pdf_bytes = _make_pdf("Customer ID: CUS-555 billing refund please")
    text = extract_text("a.pdf", pdf_bytes)
    assert "CUS-555" in text


def _make_pdf(text: str) -> bytes:
    """Build a tiny 1-page PDF with extractable text (no extra deps)."""
    content = ("BT /F1 12 Tf 72 720 Td (%s) Tj ET" % text).encode()
    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                 b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>")
    objs.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content))
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (i, obj)
    xref_pos = len(pdf)
    pdf += b"xref\n0 %d\n" % (len(objs) + 1)
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += b"%010d 00000 n \n" % off
    pdf += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF"
            % (len(objs) + 1, xref_pos))
    return pdf
