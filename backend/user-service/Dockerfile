FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY user-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY user-service/ .

COPY common/ /app/common/

EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

CMD ["sh", "-c", "createdb -h shared-postgres-db -U ${POSTGRES_USER} ${POSTGRES_USER_DB} || true && alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8002"]