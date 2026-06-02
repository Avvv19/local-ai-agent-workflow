"""Logging configuration.

Plain text by default, or single-line JSON logs when LOG_JSON=true (useful for
log aggregation in production). Call ``configure_logging`` once at startup.
"""
from __future__ import annotations

import json
import logging
import sys

from . import config


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    if config.settings.log_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-7s %(name)s | %(message)s",
            "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(config.settings.log_level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
