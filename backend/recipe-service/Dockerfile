FROM python:3.12-slim

WORKDIR /app

# Ustawiamy PYTHONPATH na /app, aby Python widział pakiety 'src' oraz 'common'
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 1. Kopiujemy requirements.txt
# Ścieżka 'recipe-service/' jest wymagana, bo jesteśmy w kontekście folderu 'backend'
COPY recipe-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Kopiujemy kod źródłowy serwisu
# Zamiast 'COPY . .' używamy konkretnej ścieżki, aby wziąć tylko pliki tego serwisu
# Zawartość folderu 'recipe-service' (np. src/) trafi bezpośrednio do /app
COPY recipe-service/ .

# 3. Kopiujemy wspólny moduł autoryzacji
# To pozwoli na importowanie: from common.auth_guard import ...
COPY common/ /app/common/

EXPOSE 8003

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

CMD ["sh", "-c", "python src/init_ingredients.py && uvicorn src.main:app --host 0.0.0.0 --port 8003"]