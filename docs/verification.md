# End-to-End Verification

Verification was run with `LLM_BACKEND=mock` for reproducible local results.

## Quality gates

```text
ruff check app tests
All checks passed!
```

```text
pytest --cov=app
34 passed, 1 warning in 13.06s
TOTAL 647 73 89%
```

```text
python run_eval.py
JSON validity rate ............. 100.0% (28/28)
Classification match ........... 100.0% (28/28)
Routing match .................. 100.0% (28/28)
Required-field completion ......  78.6% (22/28)
Human-review precision/recall .. 1.00 / 1.00
```

```text
alembic upgrade head
Running upgrade  -> e61b131e06fe, initial schema
```

## API checks

`python -m app.main` started successfully.

`GET /health` returned:

```json
{"status":"ok","backend":"mock"}
```

`GET /metrics-summary` and `GET /metrics` responded successfully. After posting
`data/sample_requests/billing_01.txt` and
`data/sample_requests/billing_05_missing_id.txt` to `/process`, the metrics
summary showed 2 total documents, 1 ready item, 1 human-review item, and 1 open
review item.

## Screenshots

The Streamlit UI was started with:

```text
streamlit run ui/streamlit_app.py
```

Playwright captured these screens:

- [Process result](screenshots/process_result.png)
- [Review queue](screenshots/review_queue.png)
- [History](screenshots/history.png)
- [Dashboard](screenshots/dashboard.png)

The capture helper is `scripts/capture_streamlit_screenshots.py`.
