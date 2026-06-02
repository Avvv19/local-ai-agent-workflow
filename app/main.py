"""Entry point: ``python -m app.main`` starts the API server."""
from __future__ import annotations

import uvicorn

from . import config, database
from .logging_config import configure_logging


def main() -> None:
    configure_logging()
    config.ensure_dirs()
    database.init_db()
    uvicorn.run("app.api:app", host=config.API_HOST, port=config.API_PORT,
                reload=False)


if __name__ == "__main__":
    main()
