FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LOG_LEVEL=INFO \
    DB_PATH=/app/data/audit.db \
    LANGCHAIN_TRACING_V2=false

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
