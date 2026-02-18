FROM python:3.12-slim

WORKDIR /app

# Ustawiamy PYTHONPATH na /app, aby Python widział pakiety 'src' oraz 'common'
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

    
COPY analytics-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY analytics-service/ .


COPY common/ /app/common/

EXPOSE 8006

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port 8006"]