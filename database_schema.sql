-- Local AI Agent Workflow Automation System - reference SQLite schema.
-- The app manages this via SQLAlchemy models (app/db_models.py) and Alembic
-- migrations (migrations/). This file documents the equivalent DDL.

CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT,
    raw_text    TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS extractions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id        INTEGER NOT NULL REFERENCES documents(id),
    document_type      TEXT,
    priority           TEXT,
    summary            TEXT,
    routing_decision   TEXT,
    review_status      TEXT,
    confidence_flag    TEXT,
    confidence_score   REAL,
    json_output        TEXT,         -- full structured record
    validation_status  TEXT,         -- pass | fail
    created_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_queue (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER NOT NULL REFERENCES documents(id),
    reason       TEXT,               -- why it was flagged
    role         TEXT,               -- team role for routing (finance, support, ...)
    status       TEXT DEFAULT 'open',-- open | resolved | approved | rejected
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER NOT NULL REFERENCES documents(id),
    step_name    TEXT,               -- received, classify, extract, ...
    status       TEXT,               -- ok | retry | fail | flag
    message      TEXT,
    created_at   TEXT NOT NULL
);
