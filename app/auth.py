"""Optional API-key authentication.

Disabled by default (ENABLE_AUTH=false) so demos and tests work with no key.
When enabled, protected endpoints require an ``X-API-Key`` header that matches
``API_KEY``.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from . import config


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency. No-op unless ENABLE_AUTH is true."""
    if not config.settings.enable_auth:
        return
    if x_api_key != config.settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key",
        )
