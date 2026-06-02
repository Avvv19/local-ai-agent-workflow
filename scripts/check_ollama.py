"""Verify the Ollama backend is reachable and runs one document.

Use this on a machine that has Ollama installed to confirm the real-model path
works (the bundled tests use the mock backend).

    ollama pull llama3
    LLM_BACKEND=ollama python scripts/check_ollama.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.llm_client import OllamaClient
from app.orchestrator import run_workflow

SAMPLE = """Customer ID: CUS-1029
Invoice Number: INV-88421
Issue: billed twice for my November subscription, suspected overcharge.
Requested Action: refund the duplicate charge."""


def main() -> int:
    print(f"Host : {config.OLLAMA_HOST}")
    print(f"Model: {config.OLLAMA_MODEL}\n")
    try:
        ping = OllamaClient().generate("Reply with the single word: ok")
        print("Connectivity OK. Model said:", ping.strip()[:80])
    except Exception as exc:  # noqa: BLE001
        print("Could not reach Ollama:", exc)
        print("Is the server running? Try:  ollama serve   and   ollama pull llama3")
        return 1

    print("\nRunning one document through the workflow...\n")
    run = run_workflow(SAMPLE, llm=OllamaClient())
    r = run.result
    print(f"  type   : {r.document_type}")
    print(f"  route  : {r.routing_decision}")
    print(f"  status : {r.review_status}")
    print(f"  summary: {r.summary[:120]}")
    print("\nValidation:", "passed" if run.validation.ok else run.validation.errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
