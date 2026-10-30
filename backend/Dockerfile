FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY ai /app/ai
COPY config /app/config
COPY workers /app/workers
COPY data /app/data
COPY knowledge /app/knowledge
COPY .env /app/.env

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
