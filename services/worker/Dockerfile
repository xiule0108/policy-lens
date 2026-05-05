FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/services/worker

WORKDIR /app

COPY packages /app/packages
COPY services/worker /app/services/worker
RUN pip install --no-cache-dir -e /app/services/worker

WORKDIR /app/services/worker

CMD ["python", "-m", "app.main"]
