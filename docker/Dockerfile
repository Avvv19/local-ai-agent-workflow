FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LLM_BACKEND=mock \
    DB_PATH=/app/data/workflow.db \
    API_PORT=8000

EXPOSE 8000 8501

# Apply DB migrations, then run API + UI together.
CMD ["sh", "-c", "alembic upgrade head || python -c 'from app import database; database.init_db()'; uvicorn app.api:app --host 0.0.0.0 --port 8000 & streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
