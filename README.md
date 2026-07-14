# Local AI Agent Workflow

A personal portfolio prototype for structured document processing with validation, review routing, logging, and optional model-provider integrations. It demonstrates implementation patterns; it is not evidence of a client deployment or an independently operated production service.

## Implemented scope

- FastAPI endpoints and Pydantic data contracts
- Document intake and extraction paths
- Validation and confidence-based review routing
- SQLite-backed local run state
- Optional LangSmith configuration
- Optional S3 and BigQuery integration modules
- Docker configuration and GitHub Actions workflow
- pytest suite and evaluation script

The repository contains parallel `app/` and `src/` paths from earlier iterations. The documented runnable path is `app/`; the duplication remains a maintenance limitation.

## Architecture boundary

The default path is local and uses SQLite. A BigQuery logging helper exists, but the reviewed default workflow does not wire that helper into every run. BigQuery must therefore be described as an optional integration, not as a proven deployed logging layer. LangSmith is also optional and depends on configuration.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux
```

Use only the provider and cloud variables needed for the path you intend to test. Never commit `.env` or service-account files.

## Run

```bash
python -m app.main
```

For the Streamlit interface:

```bash
streamlit run ui/streamlit_app.py
```

For containers:

```bash
docker compose up --build
```

## Validate

```bash
pytest --cov=app --cov-report=term-missing
ruff check app tests
python run_eval.py
```

Passing tests validate the exercised local paths only. They do not establish uptime, external adoption, data-governance approval, or cloud operation.

## Limitations and future work

- Consolidate `app/` and `src/` into one supported architecture.
- Wire optional cloud logging explicitly and test it with a disposable project.
- Save versioned evaluation outputs before publishing quality claims.
- Add end-to-end tests for configured provider and storage adapters.
- Document retention and deletion behavior for uploaded files.
