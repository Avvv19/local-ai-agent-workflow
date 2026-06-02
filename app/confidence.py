"""Confidence scoring.

Combines several signals into a single 0-1 score so downstream consumers (UI,
metrics, escalation) have one number to reason about. This is a transparent
heuristic, not a model probability — documented as such to avoid overclaiming.
"""
from __future__ import annotations


def compute_confidence(classification_confidence: str, json_valid: bool,
                       missing_fields: list[str], summary: str,
                       validation_ok: bool = True) -> float:
    """Return a confidence score in [0, 1] from transparent workflow checks:
    classification confidence, JSON validity, required-field completion,
    summary completeness, and overall validation (allowed type/priority/route).
    """
    score = 1.0
    if classification_confidence == "low":
        score -= 0.40
    if not json_valid:
        score -= 0.30
    if not validation_ok:
        score -= 0.30
    score -= 0.15 * len(missing_fields)
    if not summary or len(summary.strip()) < 15:
        score -= 0.15
    return round(max(0.0, min(1.0, score)), 3)


def flag_for_score(score: float, threshold: float = 0.6) -> str:
    return "Acceptable" if score >= threshold else "Low"
