"""SQLAlchemy-backed persistence layer.

Works on SQLite (default) and PostgreSQL (set DATABASE_URL). Public functions
keep the same names used across the app: init_db, save_run, get_result,
get_history, get_review_queue, resolve_review, plus get_metrics and export_csv.
"""
from __future__ import annotations

import csv
import io
import json

from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from . import config
from .db_models import Base, Document, Extraction, ReviewItem, WorkflowLog
from .orchestrator import RunOutput

_engines: dict[str, Engine] = {}


def _resolve_url(db_path: str | None = None) -> str:
    if db_path:
        return f"sqlite:///{db_path}"
    return config.settings.sqlalchemy_url


def get_engine(db_path: str | None = None) -> Engine:
    config.ensure_dirs()
    url = _resolve_url(db_path)
    if url not in _engines:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engines[url] = create_engine(url, connect_args=connect_args, future=True)
    return _engines[url]


def _session(db_path: str | None = None) -> Session:
    return sessionmaker(bind=get_engine(db_path), future=True)()


def init_db(db_path: str | None = None) -> None:
    Base.metadata.create_all(get_engine(db_path))


def save_run(run: RunOutput, filename: str, raw_text: str,
             db_path: str | None = None) -> int:
    r = run.result
    with _session(db_path) as s:
        doc = Document(filename=filename, raw_text=raw_text)
        s.add(doc)
        s.flush()  # assigns doc.id

        s.add(Extraction(
            document_id=doc.id,
            document_type=r.document_type,
            priority=r.priority,
            summary=r.summary,
            routing_decision=r.routing_decision,
            review_status=r.review_status,
            confidence_flag=r.confidence_flag,
            confidence_score=r.confidence_score,
            json_output=json.dumps(r.to_record()),
            validation_status="pass" if run.validation.ok else "fail",
        ))

        for log in run.logs:
            s.add(WorkflowLog(document_id=doc.id, step_name=log.step_name,
                              status=log.status, message=log.message))

        if r.review_status == "Needs Human Review":
            reason = "; ".join(run.validation.warnings) or "Flagged by workflow"
            s.add(ReviewItem(document_id=doc.id, reason=reason,
                             role=config.ROUTE_ROLES.get(r.routing_decision, "operations"),
                             status="open"))
        doc_id = doc.id
        s.commit()

    try:
        out = config.OUTPUT_DIR / f"{doc_id:05d}_{r.document_type.replace(' ', '_')}.json"
        out.write_text(json.dumps(r.to_record(), indent=2))
    except OSError:
        pass
    return doc_id


def get_result(document_id: int, db_path: str | None = None) -> dict | None:
    with _session(db_path) as s:
        doc = s.get(Document, document_id)
        if not doc:
            return None
        ext = s.scalars(
            select(Extraction).where(Extraction.document_id == document_id)
            .order_by(Extraction.id.desc())).first()
        logs = s.scalars(
            select(WorkflowLog).where(WorkflowLog.document_id == document_id)
            .order_by(WorkflowLog.id)).all()
        return {
            "document": {"id": doc.id, "filename": doc.filename,
                         "raw_text": doc.raw_text, "created_at": doc.created_at},
            "result": json.loads(ext.json_output) if ext and ext.json_output else None,
            "logs": [{"step_name": lg.step_name, "status": lg.status,
                      "message": lg.message} for lg in logs],
        }


def get_history(limit: int = 50, db_path: str | None = None) -> list[dict]:
    with _session(db_path) as s:
        rows = s.execute(
            select(Document.id, Document.filename, Document.created_at,
                   Extraction.document_type, Extraction.priority,
                   Extraction.routing_decision, Extraction.review_status,
                   Extraction.confidence_score, Extraction.validation_status)
            .join(Extraction, Extraction.document_id == Document.id, isouter=True)
            .order_by(Document.id.desc()).limit(limit)).all()
        return [{
            "document_id": r[0], "filename": r[1], "created_at": r[2],
            "document_type": r[3], "priority": r[4], "routing_decision": r[5],
            "review_status": r[6], "confidence_score": r[7],
            "validation_status": r[8],
        } for r in rows]


def get_review_queue(role: str | None = None,
                     db_path: str | None = None) -> list[dict]:
    with _session(db_path) as s:
        stmt = (select(ReviewItem.id, ReviewItem.document_id, ReviewItem.reason,
                       ReviewItem.role, ReviewItem.status, ReviewItem.created_at,
                       Extraction.document_type, Extraction.summary)
                .join(Extraction, Extraction.document_id == ReviewItem.document_id,
                      isouter=True)
                .where(ReviewItem.status == "open")
                .order_by(ReviewItem.id.desc()))
        if role:
            stmt = stmt.where(ReviewItem.role == role)
        rows = s.execute(stmt).all()
        return [{
            "id": r[0], "document_id": r[1], "reason": r[2], "role": r[3],
            "status": r[4], "created_at": r[5], "document_type": r[6],
            "summary": r[7],
        } for r in rows]


def resolve_review(review_id: int, decision: str = "resolved",
                   db_path: str | None = None) -> bool:
    """Close a review item. decision is one of resolved | approved | rejected."""
    if decision not in {"resolved", "approved", "rejected"}:
        decision = "resolved"
    with _session(db_path) as s:
        item = s.get(ReviewItem, review_id)
        if not item:
            return False
        item.status = decision
        s.commit()
        return True


def update_routing(document_id: int, new_route: str,
                   db_path: str | None = None) -> bool:
    """Reviewer override of the routing decision on the latest extraction."""
    if new_route not in config.ROUTES:
        return False
    with _session(db_path) as s:
        ext = s.scalars(
            select(Extraction).where(Extraction.document_id == document_id)
            .order_by(Extraction.id.desc())).first()
        if not ext:
            return False
        ext.routing_decision = new_route
        for item in s.scalars(select(ReviewItem)
                              .where(ReviewItem.document_id == document_id)):
            item.role = config.ROUTE_ROLES.get(new_route, "operations")
        s.commit()
        return True


def get_metrics(db_path: str | None = None) -> dict:
    """Aggregate counts for the monitoring dashboard / /metrics endpoint."""
    with _session(db_path) as s:
        total = s.scalar(select(func.count(Document.id))) or 0
        ready = s.scalar(select(func.count(Extraction.id))
                         .where(Extraction.review_status == "Ready for Review")) or 0
        flagged = s.scalar(select(func.count(Extraction.id))
                           .where(Extraction.review_status == "Needs Human Review")) or 0
        open_reviews = s.scalar(select(func.count(ReviewItem.id))
                                .where(ReviewItem.status == "open")) or 0
        by_type = dict(s.execute(
            select(Extraction.document_type, func.count(Extraction.id))
            .group_by(Extraction.document_type)).all())
        by_route = dict(s.execute(
            select(Extraction.routing_decision, func.count(Extraction.id))
            .group_by(Extraction.routing_decision)).all())
        avg_conf = s.scalar(select(func.avg(Extraction.confidence_score)))
        return {
            "total_documents": total,
            "ready_for_review": ready,
            "needs_human_review": flagged,
            "open_review_items": open_reviews,
            "avg_confidence": round(avg_conf, 3) if avg_conf is not None else None,
            "by_document_type": by_type,
            "by_route": by_route,
        }


def export_csv(reviewed_only: bool = False, db_path: str | None = None) -> str:
    """Return processing history as CSV text. If reviewed_only, include only
    records that have been actioned in the review queue."""
    rows = get_history(limit=10000, db_path=db_path)
    if reviewed_only:
        with _session(db_path) as s:
            reviewed_ids = {
                r[0] for r in s.execute(
                    select(ReviewItem.document_id)
                    .where(ReviewItem.status.in_(["resolved", "approved", "rejected"]))
                ).all()
            }
        rows = [r for r in rows if r["document_id"] in reviewed_ids]
    buf = io.StringIO()
    cols = ["document_id", "filename", "created_at", "document_type", "priority",
            "routing_decision", "review_status", "confidence_score",
            "validation_status"]
    writer = csv.DictWriter(buf, fieldnames=cols)
    writer.writeheader()
    for row in rows:
        writer.writerow({c: row.get(c) for c in cols})
    return buf.getvalue()
