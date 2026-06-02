"""Evaluation harness.

Runs the workflow over the labelled sample set and reports simple, defensible
metrics — no invented accuracy claims. The workflow was tested on a labelled
sample set to validate JSON structure, required-field completion, classification
and routing consistency, and human-review flag behaviour.

Usage:  python run_eval.py
"""
from __future__ import annotations

import json

from app import config
from app.agents import compute_missing_fields
from app.orchestrator import run_workflow

LABELS = json.loads((config.DATA_DIR / "eval_labels.json").read_text())


def main() -> None:
    total = json_valid = class_correct = route_correct = 0
    required_complete = 0  # docs with all required fields present
    flag_tp = flag_fp = flag_fn = flag_tn = 0

    print(f"Backend: {config.LLM_BACKEND}\n")
    print(f"{'file':<34}{'pred type':<30}{'route':<24}{'review'}")
    print("-" * 100)

    for fname, expected in LABELS.items():
        path = config.SAMPLE_DIR / fname
        if not path.exists():
            continue
        total += 1
        run = run_workflow(path.read_text())
        r = run.result

        extract_ok = any(
            log.step_name == "extract" and log.status == "ok" for log in run.logs)
        json_valid += int(extract_ok)
        class_correct += int(r.document_type == expected["document_type"])
        route_correct += int(r.routing_decision == expected["routing_decision"])
        required_complete += int(not r.missing_fields)

        flagged = r.review_status == "Needs Human Review"
        exp = expected["expect_human_review"]
        flag_tp += int(flagged and exp)
        flag_fp += int(flagged and not exp)
        flag_fn += int(not flagged and exp)
        flag_tn += int(not flagged and not exp)

        print(f"{fname:<34}{r.document_type:<30}{r.routing_decision:<24}{r.review_status}")

    pct = lambda n: f"{100*n/total:5.1f}%" if total else "n/a"
    print("\n" + "=" * 48)
    print(f"Metrics (labelled sample set, n={total})")
    print("=" * 48)
    print(f"JSON validity rate ............. {pct(json_valid)} ({json_valid}/{total})")
    print(f"Classification match ........... {pct(class_correct)} ({class_correct}/{total})")
    print(f"Routing match .................. {pct(route_correct)} ({route_correct}/{total})")
    print(f"Required-field completion ...... {pct(required_complete)} ({required_complete}/{total})")
    print(f"Human-review flag behaviour .... TP={flag_tp} FP={flag_fp} "
          f"FN={flag_fn} TN={flag_tn}")
    prec = flag_tp / (flag_tp + flag_fp) if (flag_tp + flag_fp) else 1.0
    rec = flag_tp / (flag_tp + flag_fn) if (flag_tp + flag_fn) else 1.0
    print(f"Human-review precision/recall .. {prec:.2f} / {rec:.2f}")


if __name__ == "__main__":
    main()
