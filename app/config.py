"""Central configuration using pydantic-settings.

Settings load from environment variables and an optional .env file. Module-level
aliases are kept for backward compatibility with the rest of the codebase.
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample_requests"
OUTPUT_DIR = DATA_DIR / "outputs"


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM backend: "mock" | "ollama" | "langchain"
    llm_backend: str = "mock"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout: int = 120

    # Workflow
    max_extraction_retries: int = 2

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Auth (off by default so demos work without a key)
    enable_auth: bool = False
    api_key: str = "change-me"

    # Database: DATABASE_URL wins (e.g. postgresql+psycopg2://...).
    # Otherwise a local SQLite file at DB_PATH is used.
    database_url: str | None = None
    db_path: str = str(DATA_DIR / "workflow.db")

    # Logging
    log_level: str = "INFO"
    log_json: bool = False

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.db_path}"


settings = Settings()

# ---- backward-compatible module-level aliases -----------------------------
LLM_BACKEND = settings.llm_backend
OLLAMA_HOST = settings.ollama_host
OLLAMA_MODEL = settings.ollama_model
OLLAMA_TIMEOUT = settings.ollama_timeout
MAX_EXTRACTION_RETRIES = settings.max_extraction_retries
API_HOST = settings.api_host
API_PORT = settings.api_port
DB_PATH = settings.db_path

# ---- controlled vocabularies ----------------------------------------------
DOCUMENT_TYPES = [
    "Billing Request", "Support Ticket", "Customer Complaint", "Vendor Request",
    "Internal Operations Request", "Policy Question", "General Inquiry",
]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
ROUTES = [
    "Finance Review", "Customer Support Review", "Operations Review",
    "Technical Review", "Human Review Required", "General Queue",
]
REVIEW_STATUSES = ["Ready for Review", "Needs Human Review"]

# Document-specific required fields. Different document types expect different
# fields, so validation is per-type rather than one-size-fits-all. A missing
# required field escalates the record to human review.
REQUIRED_FIELDS_BY_TYPE = {
    "Billing Request": ["customer_id", "invoice_number", "requested_action", "issue_description"],
    "Support Ticket": ["issue_description", "priority", "requested_action"],
    "Customer Complaint": ["customer_id", "issue_description", "priority", "requested_action"],
    "Vendor Request": ["vendor_name", "request_type", "requested_action"],
    "Policy Question": ["topic", "issue_description"],
    "Internal Operations Request": ["requested_action"],
    "General Inquiry": [],
}

# Role-based routing: each route maps to a team role used by the review queue.
ROUTE_ROLES = {
    "Finance Review": "finance",
    "Customer Support Review": "support",
    "Operations Review": "operations",
    "Technical Review": "engineering",
    "Human Review Required": "supervisor",
    "General Queue": "operations",
}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
