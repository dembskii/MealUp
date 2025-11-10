# API Gateway - MealUp

Gateway dla mikroserwisów MealUp z automatycznym proxy, timeout i obsługą błędów.

## 🚀 Funkcje

- ✅ **Automatyczne Proxy** - Przekazywanie requestów do mikroserwisów
- ⏱️ **Timeout** - Konfigurowalny timeout dla requestów (30s domyślnie)
- 🔄 **Retry Logic** - Automatyczne ponawianie nieudanych requestów
- 📊 **Logging** - Szczegółowe logowanie wszystkich requestów
- 🛡️ **Error Handling** - Obsługa błędów połączenia i timeoutów
- 🌐 **CORS** - Skonfigurowane CORS dla frontend
- 🏥 **Health Check** - Endpoint do monitorowania

## 📦 Instalacja

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Skopiuj przykładowy plik .env
cp .env.example .env

# Edytuj .env i ustaw adresy swoich mikroserwisów
```

## 🎯 Użycie

### Uruchomienie lokalne

```bash
# Z głównego katalogu gateway
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Zbuduj i uruchom
docker-compose up --build

# W tle
docker-compose up -d

# Zatrzymaj
docker-compose down
```

## 🔗 Endpointy

### Gateway Status
```bash
GET http://localhost:8000/
GET http://localhost:8000/health
GET http://localhost:8000/api/v1/status
GET http://localhost:8000/api/v1/services
```

### Auth Service (proxy)
```bash
POST http://localhost:8000/api/v1/auth/login
POST http://localhost:8000/api/v1/auth/register
POST http://localhost:8000/api/v1/auth/refresh
GET  http://localhost:8000/api/v1/auth/verify
```

### User Service (proxy)
```bash
GET    http://localhost:8000/api/v1/users
GET    http://localhost:8000/api/v1/users/{user_id}
POST   http://localhost:8000/api/v1/users
PUT    http://localhost:8000/api/v1/users/{user_id}
DELETE http://localhost:8000/api/v1/users/{user_id}
```

### Recipe Service (proxy)
```bash
GET    http://localhost:8000/api/v1/recipes
GET    http://localhost:8000/api/v1/recipes/{recipe_id}
POST   http://localhost:8000/api/v1/recipes
PUT    http://localhost:8000/api/v1/recipes/{recipe_id}
DELETE http://localhost:8000/api/v1/recipes/{recipe_id}
```

### Meal Plan Service (proxy)
```bash
GET    http://localhost:8000/api/v1/meal-plans
GET    http://localhost:8000/api/v1/meal-plans/{plan_id}
POST   http://localhost:8000/api/v1/meal-plans
PUT    http://localhost:8000/api/v1/meal-plans/{plan_id}
DELETE http://localhost:8000/api/v1/meal-plans/{plan_id}
```

## ⚙️ Konfiguracja

Edytuj plik `.env`:

```env
# Podstawowe ustawienia
PROJECT_NAME=API Gateway
VERSION=1.0.0

# CORS - dozwolone originy
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Adresy mikroserwisów
AUTH_SERVICE_URL=http://localhost:8001
USER_SERVICE_URL=http://localhost:8002
RECIPE_SERVICE_URL=http://localhost:8003
MEAL_PLAN_SERVICE_URL=http://localhost:8004

# Timeouty (w sekundach)
REQUEST_TIMEOUT=30.0    # Całkowity czas na request
CONNECT_TIMEOUT=5.0     # Czas na połączenie

# Retry
MAX_RETRIES=3
```

## 🏗️ Struktura Projektu

```
gateway/
├── src/
│   ├── main.py              # Główna aplikacja FastAPI
│   ├── api/
│   │   ├── routes.py        # Definicje routingu i proxy
│   ├── core/
│   │   ├── config.py        # Konfiguracja (Pydantic Settings)
│   │   └── proxy.py         # Logika proxy z timeout
│   ├── middleware/
│   │   └── logging.py       # Middleware do logowania
│   └── schemas/
├── tests/
│   └── test_main.py         # Testy
├── .env                     # Zmienne środowiskowe
├── .env.example             # Przykładowa konfiguracja
├── requirements.txt         # Zależności Python
├── Dockerfile               # Definicja obrazu Docker
└── docker-compose.yml       # Konfiguracja Docker Compose
```

## 🔧 Proxy Features

### Timeout Handling
Gateway automatycznie obsługuje timeouty:
- **Connect Timeout**: 5s - czas na nawiązanie połączenia
- **Request Timeout**: 30s - całkowity czas na wykonanie requestu

Jeśli mikroserwis nie odpowie w czasie, zwróci błąd 504 (Gateway Timeout).

### Error Handling
Gateway zwraca odpowiednie kody błędów:
- **503 Service Unavailable** - nie można połączyć się z mikroserwisem
- **504 Gateway Timeout** - timeout podczas czekania na odpowiedź
- **502 Bad Gateway** - błąd komunikacji z mikroserwisem
- **500 Internal Server Error** - nieoczekiwany błąd

### Request Logging
Wszystkie requesty są logowane z:
- Metodą HTTP
- Ścieżką
- Kodem statusu
- Czasem wykonania
- Ewentualnymi błędami

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}
```

### Service Status
```bash
curl http://localhost:8000/api/v1/services
# Zwraca adresy wszystkich mikroserwisów
```

### Process Time Header
Każda odpowiedź zawiera header `X-Process-Time` z czasem przetwarzania w sekundach.

## 🧪 Testy

```bash
# Uruchom testy
pytest

# Z coverage
pytest --cov=src tests/

# Verbose
pytest -v
```

## 📝 Przykłady

### Przykład 1: Login przez gateway
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}'
```

### Przykład 2: Pobranie użytkownika
```bash
curl http://localhost:8000/api/v1/users/123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Przykład 3: Dodanie przepisu
```bash
curl -X POST http://localhost:8000/api/v1/recipes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "Pizza", "ingredients": ["flour", "tomato", "cheese"]}'
```

## 🐛 Troubleshooting

### Problem: Timeout przy długich requestach
**Rozwiązanie**: Zwiększ `REQUEST_TIMEOUT` w `.env`

### Problem: Nie można połączyć z mikroserwisem
**Rozwiązanie**: Sprawdź czy mikroserwis działa i czy URL w `.env` jest prawidłowy

### Problem: CORS error
**Rozwiązanie**: Dodaj origin frontendu do `ALLOWED_ORIGINS` w `.env`

## 📚 Dokumentacja API

Po uruchomieniu dostępna pod:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT