"""SQLAlchemy ORM models (SQLAlchemy 2.0 typed style).

These map the four workflow tables. The same models work on SQLite (default)
and PostgreSQL (set DATABASE_URL), which is what makes the storage layer
portable across environments rather than tied to a local file.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str | None] = mapped_column(String(255))
    raw_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default=_utcnow)

    extractions: Mapped[list[Extraction]] = relationship(
        back_populates="document", cascade="all, delete-orphan")
    logs: Mapped[list[WorkflowLog]] = relationship(
        back_populates="document", cascade="all, delete-orphan")
    reviews: Mapped[list[ReviewItem]] = relationship(
        back_populates="document", cascade="all, delete-orphan")


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    document_type: Mapped[str | None] = mapped_column(String(64))
    priority: Mapped[str | None] = mapped_column(String(16))
    summary: Mapped[str | None] = mapped_column(Text)
    routing_decision: Mapped[str | None] = mapped_column(String(64))
    review_status: Mapped[str | None] = mapped_column(String(32))
    confidence_flag: Mapped[str | None] = mapped_column(String(16))
    confidence_score: Mapped[float | None] = mapped_column()
    json_output: Mapped[str | None] = mapped_column(Text)
    validation_status: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[str] = mapped_column(String(40), default=_utcnow)

    document: Mapped[Document] = relationship(back_populates="extractions")


class ReviewItem(Base):
    __tablename__ = "review_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    reason: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[str] = mapped_column(String(40), default=_utcnow)

    document: Mapped[Document] = relationship(back_populates="reviews")


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    step_name: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str | None] = mapped_column(String(16))
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40), default=_utcnow)

    document: Mapped[Document] = relationship(back_populates="logs")
