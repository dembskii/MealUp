# Dokumentacja Projektowa — MealUp

---

## Spis treści

1. [Informacje ogólne](#1-informacje-ogólne)
2. [Architektura systemu](#2-architektura-systemu)
3. [Stos technologiczny](#3-stos-technologiczny)
4. [Mikroserwisy — szczegółowy opis](#4-mikroserwisy--szczegółowy-opis)
   - 4.1 [API Gateway](#41-api-gateway-port-8000)
   - 4.2 [Auth Service](#42-auth-service-port-8001)
   - 4.3 [User Service](#43-user-service-port-8002)
   - 4.4 [Recipe Service](#44-recipe-service-port-8003)
   - 4.5 [Workout Service](#45-workout-service-port-8004)
   - 4.6 [Forum Service](#46-forum-service-port-8007)
5. [Frontend](#5-frontend)
6. [Infrastruktura i deployment](#6-infrastruktura-i-deployment)
7. [Zmienne środowiskowe](#7-zmienne-środowiskowe)
8. [Dane inicjalizacyjne (Seeding)](#8-dane-inicjalizacyjne-seeding)
9. [Bezpieczeństwo](#9-bezpieczeństwo)
10. [Testowanie](#10-testowanie)
11. [Dokumentacja API (Swagger)](#11-dokumentacja-api-swagger)
    - 11.1 [User Service API](#111-user-service-api)
    - 11.2 [Recipe Service API](#112-recipe-service-api)
    - 11.3 [Workout Service API](#113-workout-service-api)
    - 11.4 [Forum Service API](#114-forum-service-api)
12. [Roadmap](#12-roadmap)

---

## 1. Informacje ogólne

| Pole | Wartość |
|---|---|
| **Nazwa projektu** | MealUp |
| **Typ** | Projekt zespołowy (5. semestr) |
| **Repozytorium** | Monorepo (frontend + backend) |
| **Status** | Aktywny rozwój |

**MealUp** to platforma społecznościowa łącząca zdrowe odżywianie, planowanie treningów i interakcję w społeczności fitness. Użytkownicy mogą tworzyć przepisy, organizować plany posiłków i treningów, śledzić postępy oraz uzyskiwać spersonalizowane rekomendacje.

---

## 2. Architektura systemu

### 2.1 Diagram wysokopoziomowy

```
┌─────────────────────────────────┐
│     Frontend (Port 3000)        │
│     Next.js 14 + React          │
│     TailwindCSS + Framer Motion │
└──────────────┬──────────────────┘
               │  HTTP (REST)
               ▼
┌─────────────────────────────────┐
│     API Gateway (Port 8000)     │
│     FastAPI + Redis             │
│     Proxy / Routing / Auth      │
└──────────────┬──────────────────┘
               │
    ┌──────────┼──────────┬──────────────┬──────────────┬──────────────┐
    ▼          ▼          ▼              ▼              ▼              ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Auth   │ │ User   │ │ Recipe   │ │ Workout  │ │ Forum    │ │Payment/  │
│ Service│ │ Service│ │ Service  │ │ Service  │ │ Service  │ │Analytics/│
│ :8001  │ │ :8002  │ │ :8003    │ │ :8004    │ │ :8007    │ │Notif.   │
│ Redis  │ │ PgSQL  │ │ MongoDB  │ │ MongoDB  │ │ PgSQL    │ │(planned)│
└────────┘ └────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### 2.2 Przepływ żądania

1. **Frontend** wysyła żądanie HTTP do **API Gateway** (`http://localhost:8000/api/v1/...`)
2. **Gateway** sprawdza sesję w Redis (cookie `session_id`), dołącza nagłówek `X-User-Id`
3. **Gateway** proxuje żądanie do odpowiedniego mikroserwisu
4. **Mikroserwis** przetwarza żądanie, zwraca odpowiedź
5. **Gateway** przekazuje odpowiedź do frontendu

---

## 3. Stos technologiczny

### 3.1 Frontend

| Technologia | Wersja | Zastosowanie |
|---|---|---|
| Next.js | 14 | Framework React SSR/SSG |
| React | 18+ | Biblioteka UI |
| TailwindCSS | 3+ | Stylowanie CSS |
| Framer Motion | — | Animacje |
| Lucide React | — | Ikony |

### 3.2 Backend

| Technologia | Wersja | Zastosowanie |
|---|---|---|
| Python | 3.12 | Język backendu |
| FastAPI | — | Framework REST API |
| Pydantic | 2.12 | Walidacja danych |
| Uvicorn | 0.38 | Serwer ASGI |
| PyJWT | 2.10 | Obsługa tokenów JWT |
| httpx | — | Klient HTTP (proxy) |

### 3.3 Bazy danych

| Baza | Wersja | Serwisy |
|---|---|---|
| PostgreSQL | 16 | User Service, Forum Service |
| MongoDB | 7 | Recipe Service, Workout Service |
| Redis | 7 | Auth Service (sesje), Gateway (cache) |

### 3.4 Infrastruktura

| Narzędzie | Zastosowanie |
|---|---|
| Docker | Konteneryzacja serwisów |
| Docker Compose | Orkiestracja całego stacku |
| Auth0 | Zewnętrzny dostawca uwierzytelniania (OAuth 2.0) |

---

## 4. Mikroserwisy — szczegółowy opis

### 4.1 API Gateway (Port 8000)

**Ścieżka:** `backend/gateway/`

| Parametr | Wartość |
|---|---|
| Framework | FastAPI |
| Baza | Redis (sesje) |
| Plik główny | `src/main.py` |
| Routing | `src/api/routes.py` |
| Konfiguracja | `src/core/config.py` |

**Odpowiedzialności:**
- Jednolity punkt wejścia dla wszystkich mikroserwisów
- Proxy żądań do odpowiednich serwisów
- Uwierzytelnianie na poziomie gateway (odczyt sesji z Redis, dołączanie `X-User-Id`)
- Obsługa CORS
- Logowanie żądań (middleware `X-Process-Time`)
- Health checks
- Timeout handling (connect: 5s, request: 30s)
- Retry logic (max 3 retries)

**Konfiguracja (zmienne środowiskowe):**

| Zmienna | Opis |
|---|---|
| `AUTH_SERVICE_URL` | URL Auth Service |
| `USER_SERVICE_URL` | URL User Service |
| `RECIPE_SERVICE_URL` | URL Recipe Service |
| `WORKOUT_SERVICE_URL` | URL Workout Service |
| `FORUM_SERVICE_URL` | URL Forum Service |
| `REDIS_AUTH_URL` | URL Redis do sesji |
| `REQUEST_TIMEOUT` | Timeout żądania (domyślnie 30s) |
| `CONNECT_TIMEOUT` | Timeout połączenia (domyślnie 5s) |

**Tabela routingu proxy:**

| Ścieżka Gateway | Serwis docelowy | Metody |
|---|---|---|
| `/api/v1/auth/{path}` | Auth Service `:8001` | GET, POST, PUT, DELETE, PATCH |
| `/api/v1/user/{path}` | User Service `:8002` | GET, POST, PUT, DELETE, PATCH |
| `/api/v1/recipes/{path}` | Recipe Service `:8003` | GET, POST, PUT, DELETE, PATCH |
| `/api/v1/workouts/{path}` | Workout Service `:8004` | GET, POST, PUT, DELETE, PATCH |
| `/api/v1/forum/{path}` | Forum Service `:8007` | GET, POST, PUT, DELETE, PATCH |

**Kody błędów Gateway:**

| Kod | Znaczenie |
|---|---|
| 502 | Bad Gateway — błąd komunikacji z mikroserwisem |
| 503 | Service Unavailable — nie można połączyć się z mikroserwisem |
| 504 | Gateway Timeout — przekroczony czas oczekiwania |

---

### 4.2 Auth Service (Port 8001)

**Ścieżka:** `backend/auth-service/`

| Parametr | Wartość |
|---|---|
| Framework | FastAPI |
| Baza | Redis |
| Plik główny | `src/main.py` |
| Routing | `src/api/routes.py` |

**Odpowiedzialności:**
- Integracja z Auth0 (OAuth 2.0)
- Inicjowanie procesu logowania/rejestracji
- Obsługa callback OAuth2
- Zarządzanie sesjami w Redis (TTL 600s dla state)
- Synchronizacja użytkownika z User Service po logowaniu
- Obsługa ról: `user`, `trainer`
- Endpoint `/me` — zwrot danych zalogowanego użytkownika

**Przepływ uwierzytelniania:**

```
1. Frontend → GET /api/v1/auth/login?role=user
2. Gateway → Auth Service → Redirect do Auth0
3. Auth0 → Callback → Auth Service
4. Auth Service → Sync z User Service
5. Auth Service → Zapis sesji w Redis
6. Auth Service → Set cookie session_id → Redirect do Frontend
```

---

### 4.3 User Service (Port 8002)

**Ścieżka:** `backend/user-service/`

| Parametr | Wartość |
|---|---|
| Framework | FastAPI |
| Baza | PostgreSQL (shared) |
| ORM | SQLModel |
| Migracje | Alembic |
| Plik główny | `src/main.py` |
| Prefix | `/user` |
| Wersja API | 1.0.0 |

**Odpowiedzialności:**
- CRUD operacje na profilach użytkowników
- Synchronizacja z Auth0
- Zarządzanie preferencjami użytkownika (parametry ciała, wiek, płeć)
- System polubień treningów (`LikedWorkout`)
- System polubień przepisów (`LikedRecipe`)
- Bulk sprawdzanie statusu polubień
- Śledzenie posiłków (daily meal records)
- Wyszukiwanie użytkowników
- Filtrowanie i paginacja

**Modele danych (SQLModel/PostgreSQL):**

```
User
├── uid (UUID, PK)
├── auth0_sub (str, unique)
├── email (str, max 40)
├── username (str, max 40)
├── first_name (str, max 50)
├── last_name (str, max 50)
├── date_of_birth (date?)
├── role (str: user/trainer)
├── sex (str?: male/female)
├── age (int?)
├── body_params (BodyParamsSchema?)
│   ├── weight (float?, >0)
│   ├── weight_unit (str: kg/lb, default: kg)
│   ├── height (float?, >0)
│   └── height_unit (str: cm/m/ft, default: cm)
├── recipe_ids (List[str]?)
├── meal_records (List[DayRecordSchema]?)
│   ├── id (UUID)
│   ├── records (List[StructRecordSchema])
│   │   ├── recipe_id (str)
│   │   ├── capacity (float, >0)
│   │   ├── time_of_day (enum: breakfast/lunch/dinner/snack)
│   │   ├── created_at (datetime)
│   │   └── updated_at (datetime)
│   ├── total_macro (dict?)
│   ├── created_at (datetime)
│   └── updated_at (datetime)
├── created_at (datetime)
└── updated_at (datetime)

LikedWorkout
├── id (UUID, PK)
├── user_id (UUID, FK → User)
├── workout_id (str)
└── created_at (datetime)

LikedRecipe
├── id (UUID, PK)
├── user_id (UUID, FK → User)
├── recipe_id (str)
└── created_at (datetime)
```

---

### 4.4 Recipe Service (Port 8003)

**Ścieżka:** `backend/recipe-service/`

| Parametr | Wartość |
|---|---|
| Framework | FastAPI |
| Baza | MongoDB (shared) |
| Plik główny | `src/main.py` |
| Konfiguracja | `src/core/config.py` |
| Routing | `src/api/routes.py` |
| Prefix | `/recipes` |
| Wersja API | 1.0.0 |
| Seed data | `src/init_recipes.py` |

**Odpowiedzialności:**
- CRUD operacje na przepisach
- CRUD operacje na składnikach
- Wyszukiwanie i filtrowanie przepisów (po nazwie, tagach, autorze)
- Automatyczne obliczanie makroskładników
- System polubień przepisów (like/unlike z inkrementacją)
- Ochrona endpointów przez Bearer token
- Autoryzacja — modyfikacja/usunięcie tylko przez autora (`X-User-Id`)

**Kolekcje MongoDB:**

| Kolekcja | Opis |
|---|---|
| `recipes` | Przepisy |
| `ingredients` | Składniki z makro |

**Modele danych:**

```
Macro
├── calories (float, ≥0) — per 100g
├── carbs (float, ≥0) — per 100g (g)
├── proteins (float, ≥0) — per 100g (g)
└── fats (float, ≥0) — per 100g (g)

Ingredient
├── _id (UUID)
├── name (str, 1-100 znaków)
├── units (str, 1-20 znaków)
├── image (str?, URL)
├── macro_per_hundred (Macro?)
├── _created_at (datetime)
└── _updated_at (datetime)

CapacityUnit (enum)
├── g, kg, ml, l, tsp, tbsp, cup, oz, lb, pcs

WeightedIngredient
├── ingredient_id (str)
├── capacity (CapacityUnit)
└── quantity (float, >0)

Recipe
├── _id (UUID)
├── name (str, 1-200 znaków)
├── author_id (str — auth0_sub)
├── ingredients (List[WeightedIngredient], min 1)
├── prepare_instruction (List[str], min 1)
├── time_to_prepare (int, >0, sekundy)
├── images (List[str]?)
├── total_likes (int, ≥0, default=0)
├── _created_at (datetime)
└── _updated_at (datetime)
```

---

### 4.5 Workout Service (Port 8004)

**Ścieżka:** `backend/workout-service/`

| Parametr | Wartość |
|---|---|
| Framework | FastAPI |
| Baza | MongoDB (shared) |
| Plik główny | `src/main.py` |
| Routing | `src/api/routes.py` |
| Konfiguracja | `src/core/config.py` (zmienna: `WORKOUT_MONGODB_URL`) |
| Prefix | `/workouts` |
| Wersja API | 1.0.0 |
| Seed data | `src/init_exercises.py` (120+ ćwiczeń) |

**Odpowiedzialności:**
- Zarządzanie biblioteką ćwiczeń (120+ pozycji)
- CRUD na sesjach treningowych
- CRUD na planach treningowych
- Przypisywanie treningów do planów
- Przypisywanie klientów do planów (trener → klient)
- Pobieranie planów „moich" i „przypisanych do mnie"
- System polubień planów (like/unlike)
- Zaawansowane filtrowanie (partia ciała, poziom zaawansowania, kategoria, typ treningu)
- Wyszukiwanie ćwiczeń
- Endpointy enumów (body parts, advancements, categories, training types, days)

**Enumeracje:**

| Enum | Wartości |
|---|---|
| `BodyPart` | chest, back, shoulders, biceps, triceps, forearms, abs, obliques, quadriceps, hamstrings, glutes, calves, full_body, cardio |
| `Advancement` | beginner, intermediate, advanced, expert |
| `ExerciseCategory` | strength, cardio, flexibility, balance, plyometric, calisthenics, olympic_lifting, powerlifting, hiit, yoga, stretching |
| `TrainingType` | push, pull, legs, upper, lower, full_body, cardio, hiit, strength, hypertrophy, endurance, flexibility, custom |
| `SetUnit` | reps, seconds, minutes, meters, km, calories |
| `DayOfWeek` | monday, tuesday, wednesday, thursday, friday, saturday, sunday |

**Modele danych:**

```
Exercise
├── _id (UUID5, deterministyczny z nazwy)
├── name (str, 1-100)
├── body_part (BodyPart)
├── advancement (Advancement)
├── category (ExerciseCategory)
├── description (str?, max 1000)
├── hints (List[str]?)
├── image (str?)
├── video_url (str?)
├── _created_at (datetime)
└── _updated_at (datetime)

StructSet
├── volume (float, >0)
└── units (SetUnit)

TrainingExercise
├── exercise_id (str)
├── sets (List[StructSet], min 1)
├── rest_between_sets (int?, ≥0, default 60s)
└── notes (str?, max 500)

Training
├── _id (UUID)
├── name (str, 1-100)
├── creator_id (str?)
├── exercises (List[TrainingExercise], min 1)
├── est_time (int, >0, sekundy)
├── training_type (TrainingType)
├── description (str?, max 500)
├── _created_at (datetime)
└── _updated_at (datetime)

WorkoutPlan
├── _id (UUID)
├── name (str, 1-100)
├── trainer_id (str)
├── clients (List[str], default=[])
├── trainings (List[str] — Training IDs, default=[])
├── schedule (dict? — mapowanie dni na treningi)
├── description (str?, max 1000)
├── is_public (bool, default=false)
├── total_likes (int, default=0)
├── _created_at (datetime)
└── _updated_at (datetime)
```

**Modele zagregowane:**

```
TrainingWithExercises — Training + pełne dane ćwiczeń (embed)
WorkoutPlanDetailed  — WorkoutPlan + List[TrainingWithExercises]
```

---

### 4.6 Forum Service (Port 8007)

**Ścieżka:** `backend/forum-service/`

| Parametr | Wartość |
|---|---|
| Framework | FastAPI |
| Baza | PostgreSQL (shared) |
| ORM | SQLModel |
| Migracje | Alembic |
| Plik główny | `src/main.py` |
| Prefix | `/forum` |
| Wersja API | 1.0.0 |

**Odpowiedzialności:**
- CRUD operacje na postach
- System komentarzy (wątkowe dyskusje z max depth=10)
- System polubień postów i komentarzy
- Algorytm trendów (trending coefficient)
- Śledzenie wyświetleń postów (z engagement_seconds)
- Wyszukiwanie pełnotekstowe (posty, przepisy, treningi, autorzy)
- Autokompletacja i sugestie
- Linkowanie przepisów i treningów do postów
- System tagów z rankingiem popularności

**Modele danych:**

```
Post
├── _id (UUID)
├── author_id (UUID)
├── title (str, 3-200 znaków)
├── content (str, 10-5000 znaków)
├── tags (List[str]?, max 10)
├── images (List[str]?, max 5)
├── linked_recipes (List[str]?)
├── linked_workouts (List[str]?)
├── total_likes (int, ≥0)
├── views_count (int, ≥0)
├── _created_at (datetime)
└── _updated_at (datetime)

Comment
├── _id (UUID)
├── post_id (UUID)
├── user_id (str)
├── content (str, 1-500 znaków)
├── parent_comment_id (str? — dla odpowiedzi)
├── total_likes (int, ≥0)
├── _created_at (datetime)
└── _updated_at (datetime)

CommentTree (struktura zagnieżdżona)
├── comment (CommentResponse)
└── replies (List[CommentTree], default=[])
```

**Kategorie wyszukiwania (SearchCategory):**

| Kategoria | Opis |
|---|---|
| `all` | Wszystkie kategorie łącznie |
| `posts` | Tylko posty na forum |
| `recipes` | Przepisy z Recipe Service |
| `workouts` | Treningi z Workout Service |
| `authors` | Autorzy postów |

**Opcje sortowania (SearchSortBy):**

| Sortowanie | Opis |
|---|---|
| `relevance` | Najlepsze dopasowanie (domyślne) |
| `newest` | Najnowsze |
| `trending` | Najwyższy trending coefficient |
| `most_liked` | Najwięcej polubień |

---

## 5. Frontend

**Ścieżka:** `frontend/`

### 5.1 Konfiguracja

| Plik | Opis |
|---|---|
| `package.json` | Zależności npm |
| `next.config.mjs` | Konfiguracja Next.js |
| `tsconfig.json` | TypeScript config |
| `postcss.config.mjs` | PostCSS/Tailwind |

### 5.2 Konfiguracja sieciowa

Zdefiniowana w `frontend/app/config/network.js`:

```
Gateway:  http://localhost:8000
API Base: http://localhost:8000/api/v1

Endpoints:
  AUTH:     /api/v1/auth
  USERS:    /api/v1/user
  RECIPES:  /api/v1/recipes
  WORKOUTS: /api/v1/workouts
  FORUM:    /api/v1/forum
```

### 5.3 Warstwa serwisów (API Client)

| Plik | Serwis docelowy | Opis |
|---|---|---|
| `workoutService.js` | Workout Service | Ćwiczenia, treningi, plany |
| `forumService.js` | Forum Service | Posty, komentarze, polubienia |
| `userService.js` | User Service | Profile, polubienia |
| `recipeService.js` | Recipe Service | Przepisy, składniki |
| `geminiService.js` | — (stub) | Mock generatora AI |

Wszystkie serwisy używają `credentials: 'include'` (cookie-based auth).

### 5.4 Komponenty UI

| Komponent | Plik | Opis |
|---|---|---|
| Landing Page | `LandingPage.jsx` | Strona powitalna, CTA |
| Dashboard | `Dashboard.jsx` | Główny widok, planowanie posiłków |
| Workouts | `WorkoutsView.jsx` | Przeglądanie/tworzenie treningów i planów |
| Recipes | `RecipesView.jsx` | Przeglądanie/tworzenie przepisów |
| Community | `Community.jsx` | Forum społeczności |
| Profile | `Profile.jsx` | Profil użytkownika, polubione treningi/przepisy |
| Settings | `Settings.jsx` | Ustawienia konta |
| Navbar | `Navbar.jsx` | Pasek nawigacji |

### 5.5 Funkcje AI (Stub)

Zdefiniowane w `geminiService.js`:

- **`generateRecipe(prompt)`** — generuje mock przepisu AI
- **`generateWorkout(goal)`** — generuje mock treningu AI

Obie funkcje symulują opóźnienie sieciowe (1.5s) i zwracają predefiniowane dane. Docelowo mają być zintegrowane z Google Gemini API.

---

## 6. Infrastruktura i deployment

### 6.1 Docker

Każdy mikroserwis ma własny `Dockerfile` oparty na `python:3.12-slim`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY {service}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY {service}/ .
COPY common/ /app/common/
HEALTHCHECK CMD curl -f http://localhost:{port}/health || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "{port}"]
```

### 6.2 Docker Compose

Plik `docker-compose.yml` orkiestruje cały stos:

| Usługa | Port | Baza danych | Status |
|---|---|---|---|
| Frontend | 3000 | — | ✅ |
| Gateway | 8000 | Redis | ✅ |
| Auth Service | 8001 | Redis | ✅ |
| User Service | 8002 | PostgreSQL | ✅ |
| Recipe Service | 8003 | MongoDB | ✅ |
| Workout Service | 8004 | MongoDB | ✅ |
| Payment Service | 8005 | — | 🔄 Planned |
| Analytics Service | 8006 | — | 🔄 Planned |
| Forum Service | 8007 | PostgreSQL | ✅ |
| Notification Service | 8008 | — | 🔄 Planned |
| PostgreSQL | 5432 | — | ✅ (shared) |
| MongoDB | 27017 | — | ✅ (shared) |
| Redis (Auth) | 6379 | — | ✅ |

**Uruchomienie:**

```bash
docker-compose up --build
```

### 6.3 Współdzielony moduł auth

Plik `backend/common/auth_guard.py` — middleware uwierzytelniania współdzielony między serwisami. Kopiowany do każdego kontenera jako `/app/common/`.

### 6.4 Skrypty pomocnicze

| Skrypt | Opis |
|---|---|
| `venv-conf.sh` | Konfiguracja wirtualnych środowisk Python dla wszystkich serwisów |
| `docker-restart.sh` | Restart kontenerów Docker |
| `backend/scripts/init-db.sh` | Inicjalizacja baz danych |

---

## 7. Zmienne środowiskowe

### 7.1 Workout Service (`.env`)

```env
WORKOUT_MONGODB_URL=mongodb://${MONGO_ROOT_USER}:${MONGO_ROOT_PASSWORD}@shared-mongo-db:27017/workout_db?authSource=admin
```

### 7.2 Wymagane zmienne (główny `.env`)

| Zmienna | Serwis | Opis |
|---|---|---|
| `MONGO_ROOT_USER` | MongoDB | Użytkownik root |
| `MONGO_ROOT_PASSWORD` | MongoDB | Hasło root |
| `AUTH0_DOMAIN` | Auth, Recipe | Domena Auth0 |
| `AUTH0_AUDIENCE` | Auth, Recipe | Audience Auth0 |
| `ALGORITHMS` | Auth, Recipe | Algorytmy JWT |
| `AUTH_REDIS_PASSWORD` | Gateway, Auth | Hasło Redis |
| `REDIS_AUTH_URL` | Gateway | URL Redis |

---

## 8. Dane inicjalizacyjne (Seeding)

| Serwis | Skrypt | Ilość danych |
|---|---|---|
| Workout Service | `src/init_exercises.py` | 120+ ćwiczeń |
| Recipe Service | `src/init_recipes.py` | Wiele przepisów + 500+ składników |

Ćwiczenia mają **deterministyczne UUID-5** generowane z nazwy (namespace: `b4cc290f-9cf0-4999-a013-bdf5e7644103`), co umożliwia stabilne odwoływanie się do nich z innych skryptów seed.

Seeding uruchamiany jest automatycznie przy starcie kontenera (w `CMD` Dockerfile).

---

## 9. Bezpieczeństwo

| Mechanizm | Opis |
|---|---|
| **OAuth 2.0 (Auth0)** | Zewnętrzne uwierzytelnianie |
| **JWT Tokens** | Autoryzacja żądań (Bearer Token) |
| **Session cookies** | `session_id` cookie z Redis |
| **`X-User-Id` header** | Identyfikacja użytkownika wewnątrz systemu |
| **`require_auth` guard** | Dekorator/dependency zabezpieczający endpointy |
| **CORS** | Ograniczone originy (`localhost:3000`, `localhost:8000`) |
| **Ownership validation** | Operacje modyfikacji sprawdzają `trainer_id` / `creator_id` / `author_id` |

---

## 10. Testowanie

### 10.1 Testy Gateway

Plik: `backend/gateway/tests/test_main.py`

```bash
# Uruchomienie testów
pytest

# Z coverage
pytest --cov=src tests/

# Verbose
pytest -v
```

Testy weryfikują:
- Endpoint root (`/`)
- Health check (`/health`)
- Status gateway (`/api/v1/status`)
- Lista serwisów (`/api/v1/services`)

---

## 11. Dokumentacja API (Swagger)

Dostęp do interaktywnej dokumentacji po uruchomieniu:

| Serwis | Swagger UI | ReDoc |
|---|---|---|
| Gateway | http://localhost:8000/docs | http://localhost:8000/redoc |
| Auth Service | http://localhost:8001/docs | http://localhost:8001/redoc |
| User Service | http://localhost:8002/docs | http://localhost:8002/redoc |
| Recipe Service | http://localhost:8003/docs | http://localhost:8003/redoc |
| Workout Service | http://localhost:8004/docs | http://localhost:8004/redoc |
| Forum Service | http://localhost:8007/docs | http://localhost:8007/redoc |

---

### 11.1 User Service API

> **Base URL:** `http://localhost:8002/user`
> **Wersja:** 1.0.0
> **Autoryzacja:** Bearer Token (HTTPBearer)

#### 11.1.1 Użytkownicy

##### `GET /user/users` — Lista użytkowników

Pobiera wszystkich użytkowników z paginacją.

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Ilość rekordów do pominięcia |
| `limit` | integer | ❌ | 10 | Maksymalna liczba wyników |

**Response `200`:**

```json
{
  "total": 42,
  "items": [
    {
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "auth0_sub": "google-oauth2|1234567890",
      "email": "example@mail.com",
      "username": "JohnnyHunter",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "2002-02-02",
      "role": "user",
      "sex": "male",
      "age": 22,
      "body_params": {
        "weight": 80.0,
        "weight_unit": "kg",
        "height": 180.0,
        "height_unit": "cm"
      },
      "recipe_ids": ["id1", "id2"],
      "meal_records": [],
      "created_at": "2026-01-15T10:30:00",
      "update_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

##### `POST /user/users` — Utwórz użytkownika

Tworzy nowego użytkownika.

**Request Body (`UserCreate`):**

```json
{
  "email": "example@mail.com",
  "username": "JohnnyHunter",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "2002-02-02"
}
```

| Pole | Typ | Wymagane | Max | Opis |
|---|---|---|---|---|
| `email` | string (email) | ✅ | 40 | Email użytkownika |
| `username` | string | ✅ | 40 | Nazwa użytkownika |
| `first_name` | string | ✅ | 50 | Imię |
| `last_name` | string | ✅ | 50 | Nazwisko |
| `date_of_birth` | string (date) | ❌ | — | Data urodzenia |

**Response `200`:** `UserResponse`

---

##### `GET /user/users/{uid}` — Pobierz użytkownika

Pobiera użytkownika po UUID.

| Parametr | Typ | Wymagany | Opis |
|---|---|---|---|
| `uid` | string (UUID) | ✅ | UUID użytkownika |

**Response `200`:** `UserResponse`

---

##### `PUT /user/users/{uid}` — Aktualizuj użytkownika

**Request Body (`UserUpdate`):**

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "2002-02-02",
  "sex": "male",
  "age": 22,
  "body_params": {
    "weight": 80.0,
    "weight_unit": "kg",
    "height": 180.0,
    "height_unit": "cm"
  },
  "username": "JohnnyHunter",
  "recipe_ids": ["id1"],
  "meal_records": []
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `first_name` | string? | ❌ | Imię (max 50) |
| `last_name` | string? | ❌ | Nazwisko (max 50) |
| `date_of_birth` | date? | ❌ | Data urodzenia |
| `sex` | enum? | ❌ | `male` / `female` |
| `age` | int? | ❌ | Wiek |
| `body_params` | BodyParamsSchema? | ❌ | Parametry ciała |
| `username` | string? | ❌ | Nazwa (max 40) |
| `recipe_ids` | List[str]? | ❌ | Lista ID przepisów |
| `meal_records` | List[DayRecordSchema]? | ❌ | Rekordy posiłków |

**Response `200`:** `UserResponse`

---

##### `DELETE /user/users/{uid}` — Usuń użytkownika

| Parametr | Typ | Wymagany | Opis |
|---|---|---|---|
| `uid` | string (UUID) | ✅ | UUID użytkownika |

**Response `200`:** pusty obiekt

---

##### `GET /user/users/auth0/{auth0_sub}` — Pobierz po Auth0 sub

| Parametr | Typ | Wymagany | Opis |
|---|---|---|---|
| `auth0_sub` | string | ✅ | Auth0 subject identifier |

**Response `200`:** `UserResponse`

---

##### `POST /user/sync` — Synchronizacja z Auth Service

Synchronizuje dane użytkownika po logowaniu przez Auth0. **Nie wymaga Bearer Token.**

**Request Body:** dowolny obiekt JSON z danymi użytkownika Auth0.

**Response `200`:** `UserResponse`

---

##### `GET /user/users/search` — Wyszukiwanie użytkowników

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string | ✅ | — | Fraza (1-200 znaków) |
| `skip` | integer | ❌ | 0 | Offset (min 0) |
| `limit` | integer | ❌ | 10 | Limit (1-50) |

**Response `200`:** `UserListResponse`

---

#### 11.1.2 Polubione treningi

##### `POST /user/users/{uid}/liked-workouts` — Polub trening

**Request Body:**

```json
{
  "workout_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response `201`:** `LikedWorkoutResponse`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "workout_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-15T10:30:00"
}
```

---

##### `GET /user/users/{uid}/liked-workouts` — Lista polubionych treningów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset (min 0) |
| `limit` | integer | ❌ | 20 | Limit (1-500) |

**Response `200`:** `LikedWorkoutListResponse`

```json
{
  "total": 5,
  "items": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "workout_id": "workout-id",
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

---

##### `DELETE /user/users/{uid}/liked-workouts/{workout_id}` — Cofnij polubienie treningu

**Response `200`:** pusty obiekt

---

##### `GET /user/users/{uid}/liked-workouts/check/{workout_id}` — Sprawdź polubienie

**Response `200`:**

```json
{
  "workout_id": "550e8400-...",
  "is_liked": true
}
```

---

##### `POST /user/users/{uid}/liked-workouts/check-bulk` — Bulk sprawdzenie polubień

**Request Body:**

```json
{
  "workout_ids": ["id1", "id2", "id3"]
}
```

> Lista 1-100 workout IDs.

**Response `200`:**

```json
{
  "results": {
    "id1": true,
    "id2": false,
    "id3": true
  }
}
```

---

##### `GET /user/users/{uid}/liked-workouts/search` — Wyszukaj polubione treningi

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `workout_ids` | string? | ❌ | — | Comma-separated workout IDs |
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |

**Response `200`:** `LikedWorkoutListResponse`

---

#### 11.1.3 Polubione przepisy

##### `POST /user/users/{uid}/liked-recipes` — Polub przepis

**Request Body:**

```json
{
  "recipe_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response `201`:** `LikedRecipeResponse`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "recipe_id": "550e8400-...",
  "created_at": "2026-01-15T10:30:00"
}
```

---

##### `GET /user/users/{uid}/liked-recipes` — Lista polubionych przepisów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-500) |

**Response `200`:** `LikedRecipeListResponse`

---

##### `DELETE /user/users/{uid}/liked-recipes/{recipe_id}` — Cofnij polubienie przepisu

**Response `200`:** pusty obiekt

---

##### `POST /user/users/{uid}/liked-recipes/check-bulk` — Bulk sprawdzenie polubień przepisów

**Request Body:**

```json
{
  "recipe_ids": ["id1", "id2", "id3"]
}
```

> Lista 1-100 recipe IDs.

**Response `200`:**

```json
{
  "results": {
    "id1": true,
    "id2": false
  }
}
```

---

#### 11.1.4 Health Check

##### `GET /user/health` — Health check

**Response `200`:** pusty obiekt

##### `GET /health` — Health check (Docker)

**Response `200`:** pusty obiekt

---

### 11.2 Recipe Service API

> **Base URL:** `http://localhost:8003/recipes`
> **Wersja:** 1.0.0
> **Autoryzacja:** Bearer Token (HTTPBearer)

#### 11.2.1 Składniki (Ingredients)

##### `GET /recipes/ingredients` — Lista składników

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset (min 0) |
| `limit` | integer | ❌ | 100 | Limit (1-500) |
| `search` | string? | ❌ | — | Wyszukiwanie po nazwie |

**Response `200`:** `Array[IngredientResponse]`

```json
[
  {
    "_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Tomato",
    "units": "g",
    "image": "https://example.com/tomato.jpg",
    "macro_per_hundred": {
      "calories": 18,
      "carbs": 3.9,
      "proteins": 0.9,
      "fats": 0.2
    },
    "_created_at": "2026-01-15T10:30:00",
    "_updated_at": "2026-01-15T10:30:00"
  }
]
```

---

##### `POST /recipes/ingredients` — Utwórz składnik

**Request Body (`IngredientCreate`):**

```json
{
  "name": "Tomato",
  "units": "g",
  "image": "https://example.com/tomato.jpg",
  "macro_per_hundred": {
    "calories": 18,
    "carbs": 3.9,
    "fats": 0.2,
    "proteins": 0.9
  }
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `name` | string | ✅ | Nazwa (1-100) |
| `units` | string | ✅ | Jednostka bazowa (1-20) |
| `image` | string? | ❌ | URL obrazka |
| `macro_per_hundred` | Macro? | ❌ | Makroskładniki na 100g |

**Response `201`:** `IngredientResponse`

---

##### `GET /recipes/ingredients/{ingredient_id}` — Szczegóły składnika

**Response `200`:** `IngredientResponse`

---

##### `PUT /recipes/ingredients/{ingredient_id}` — Aktualizuj składnik

**Request Body (`IngredientUpdate`):** Wszystkie pola opcjonalne (name, units, image, macro_per_hundred).

**Response `200`:** `IngredientResponse`

---

##### `DELETE /recipes/ingredients/{ingredient_id}` — Usuń składnik

**Response `204`:** No Content

---

#### 11.2.2 Przepisy (Recipes)

##### `GET /recipes/` — Lista przepisów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset (min 0) |
| `limit` | integer | ❌ | 20 | Limit (1-100) |
| `author_id` | string? | ❌ | — | Filtruj po autorze |

**Response `200`:** `Array[RecipeResponse]`

```json
[
  {
    "_id": "650e8400-e29b-41d4-a716-446655440001",
    "name": "Tomato Pasta",
    "author_id": "google-oauth2|1234567890",
    "ingredients": [
      {
        "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
        "capacity": "g",
        "quantity": 400.0
      }
    ],
    "prepare_instruction": [
      "Wash tomatoes",
      "Cut into pieces",
      "Cook for 20 minutes"
    ],
    "time_to_prepare": 1200,
    "images": ["https://example.com/recipe1.jpg"],
    "total_likes": 42,
    "_created_at": "2026-01-15T10:30:00",
    "_updated_at": "2026-01-15T10:30:00"
  }
]
```

---

##### `POST /recipes/` — Utwórz przepis

**Headers:** `X-User-Id` (opcjonalny — ustawiany przez Gateway)

**Request Body (`RecipeCreate`):**

```json
{
  "name": "Tomato Pasta",
  "ingredients": [
    {
      "ingredient_id": "550e8400-e29b-41d4-a716-446655440000",
      "capacity": "g",
      "quantity": 400.0
    }
  ],
  "prepare_instruction": [
    "Wash tomatoes",
    "Cut into pieces",
    "Cook for 20 minutes"
  ],
  "time_to_prepare": 1200,
  "images": ["https://example.com/recipe.jpg"]
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `name` | string | ✅ | Nazwa (1-200) |
| `ingredients` | List[WeightedIngredient] | ✅ | Lista składników (min 1) |
| `prepare_instruction` | List[str] | ✅ | Kroki przygotowania (min 1) |
| `time_to_prepare` | integer | ✅ | Czas w sekundach (>0) |
| `images` | List[str]? | ❌ | URLe zdjęć |

**Response `201`:** `RecipeResponse`

---

##### `GET /recipes/{recipe_id}` — Szczegóły przepisu

**Response `200`:** `RecipeResponse`

---

##### `PUT /recipes/{recipe_id}` — Aktualizuj przepis

> ⚠️ Tylko autor może modyfikować przepis (weryfikacja przez `X-User-Id`).

**Request Body (`RecipeUpdate`):**

```json
{
  "ingredients": [...],
  "prepare_instruction": "1. Wash\n2. Cut\n3. Cook for 25 minutes",
  "time_to_prepare": 1500,
  "images": [...]
}
```

**Response `200`:** `RecipeResponse`

---

##### `DELETE /recipes/{recipe_id}` — Usuń przepis

> ⚠️ Tylko autor może usunąć przepis (weryfikacja przez `X-User-Id`).

**Response `204`:** No Content

---

##### `POST /recipes/{recipe_id}/like` — Polub przepis

Inkrementuje licznik polubień.

**Response `200`:** `RecipeResponse` (z zaktualizowanym `total_likes`)

---

##### `POST /recipes/{recipe_id}/unlike` — Cofnij polubienie

Dekrementuje licznik polubień.

**Response `200`:** `RecipeResponse`

---

##### `GET /recipes/search` — Wyszukiwanie przepisów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string | ✅ | — | Fraza (1-200) |
| `tags` | List[str]? | ❌ | — | Filtruj po tagach |
| `author_id` | string? | ❌ | — | Filtruj po autorze |
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |

**Response `200`:** `Array[RecipeResponse]`

---

#### 11.2.3 Schematy danych (Recipe Service)

**`Macro`**

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `calories` | float (≥0) | ✅ | Kalorie na 100g |
| `carbs` | float (≥0) | ✅ | Węglowodany na 100g (g) |
| `proteins` | float (≥0) | ✅ | Białko na 100g (g) |
| `fats` | float (≥0) | ✅ | Tłuszcze na 100g (g) |

**`WeightedIngredient`**

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `ingredient_id` | string | ✅ | ID składnika |
| `capacity` | CapacityUnit | ✅ | Jednostka miary |
| `quantity` | float (>0) | ✅ | Ilość |

**`CapacityUnit` (enum):** `g`, `kg`, `ml`, `l`, `tsp`, `tbsp`, `cup`, `oz`, `lb`, `pcs`

---

### 11.3 Workout Service API

> **Base URL:** `http://localhost:8004/workouts`
> **Wersja:** 1.0.0
> **Autoryzacja:** Brak globalnej (per-endpoint, header `X-User-Id`)

#### 11.3.1 Ćwiczenia (Exercises)

##### `GET /workouts/exercises` — Lista ćwiczeń

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset (min 0) |
| `limit` | integer | ❌ | 100 | Limit (1-500) |
| `search` | string? | ❌ | — | Wyszukiwanie po nazwie |
| `body_part` | BodyPart? | ❌ | — | Filtruj po partii ciała |
| `advancement` | Advancement? | ❌ | — | Filtruj po poziomie |
| `category` | ExerciseCategory? | ❌ | — | Filtruj po kategorii |

**Response `200`:** `Array[ExerciseResponse]`

```json
[
  {
    "_id": "uuid",
    "name": "Bench Press",
    "body_part": "chest",
    "advancement": "intermediate",
    "category": "strength",
    "description": "Classic chest exercise",
    "hints": ["Keep shoulders retracted", "Control the weight"],
    "image": "https://example.com/bench.jpg",
    "video_url": "https://youtube.com/watch?v=...",
    "_created_at": "2026-01-15T10:30:00",
    "_updated_at": "2026-01-15T10:30:00"
  }
]
```

---

##### `POST /workouts/exercises` — Utwórz ćwiczenie

**Request Body (`ExerciseCreate`):**

```json
{
  "name": "Bench Press",
  "body_part": "chest",
  "advancement": "intermediate",
  "category": "strength",
  "description": "Classic chest exercise",
  "hints": ["Keep shoulders retracted"],
  "image": "https://example.com/bench.jpg",
  "video_url": "https://youtube.com/watch?v=..."
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `name` | string | ✅ | Nazwa (1-100) |
| `body_part` | BodyPart | ✅ | Partia ciała |
| `advancement` | Advancement | ✅ | Poziom zaawansowania |
| `category` | ExerciseCategory | ✅ | Kategoria |
| `description` | string? | ❌ | Opis (max 1000) |
| `hints` | List[str]? | ❌ | Wskazówki |
| `image` | string? | ❌ | URL obrazka |
| `video_url` | string? | ❌ | URL wideo |

**Response `201`:** `ExerciseResponse`

---

##### `GET /workouts/exercises/{exercise_id}` — Szczegóły ćwiczenia

**Response `200`:** `ExerciseResponse`

---

##### `PUT /workouts/exercises/{exercise_id}` — Aktualizuj ćwiczenie

**Request Body (`ExerciseUpdate`):** Wszystkie pola opcjonalne.

**Response `200`:** `ExerciseResponse`

---

##### `DELETE /workouts/exercises/{exercise_id}` — Usuń ćwiczenie

**Response `204`:** No Content

---

##### `GET /workouts/exercises/search` — Wyszukiwanie ćwiczeń

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string | ✅ | — | Fraza (1-200) |
| `tags` | List[str]? | ❌ | — | Filtruj po tagach |
| `body_part` | BodyPart? | ❌ | — | Filtruj po partii ciała |
| `advancement` | Advancement? | ❌ | — | Filtruj po poziomie |
| `category` | ExerciseCategory? | ❌ | — | Filtruj po kategorii |
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |

**Response `200`:** `Array[ExerciseResponse]`

---

#### 11.3.2 Endpointy enumów

| Endpoint | Metoda | Opis |
|---|---|---|
| `/workouts/enums/body-parts` | GET | Wszystkie partie ciała |
| `/workouts/enums/advancements` | GET | Wszystkie poziomy zaawansowania |
| `/workouts/enums/categories` | GET | Wszystkie kategorie ćwiczeń |
| `/workouts/enums/training-types` | GET | Wszystkie typy treningów |
| `/workouts/enums/days` | GET | Wszystkie dni tygodnia |

---

#### 11.3.3 Treningi (Trainings)

##### `GET /workouts/trainings` — Lista treningów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 100 | Limit (1-500) |
| `training_type` | TrainingType? | ❌ | — | Filtruj po typie |
| `search` | string? | ❌ | — | Wyszukiwanie |

**Response `200`:** `Array[TrainingResponse]`

```json
[
  {
    "_id": "uuid",
    "name": "Push Day A",
    "creator_id": "user-id",
    "exercises": [
      {
        "exercise_id": "550e8400-...",
        "sets": [
          {"volume": 12, "units": "reps"},
          {"volume": 10, "units": "reps"},
          {"volume": 8, "units": "reps"}
        ],
        "rest_between_sets": 90,
        "notes": "Focus on slow eccentric"
      }
    ],
    "est_time": 3600,
    "training_type": "push",
    "description": "Push day focusing on chest and shoulders",
    "_created_at": "2026-01-15T10:30:00",
    "_updated_at": "2026-01-15T10:30:00"
  }
]
```

---

##### `POST /workouts/trainings` — Utwórz trening

**Headers:** `X-User-Id` (opcjonalny)

**Request Body (`TrainingCreate`):**

```json
{
  "name": "Push Day A",
  "exercises": [
    {
      "exercise_id": "550e8400-...",
      "sets": [
        {"volume": 12, "units": "reps"},
        {"volume": 10, "units": "reps"}
      ],
      "rest_between_sets": 90,
      "notes": "Focus on slow eccentric"
    }
  ],
  "est_time": 3600,
  "training_type": "push",
  "description": "Push day focusing on chest"
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `name` | string | ✅ | Nazwa (1-100) |
| `exercises` | List[TrainingExercise] | ✅ | Lista ćwiczeń (min 1) |
| `est_time` | integer | ✅ | Szacowany czas (>0, sek.) |
| `training_type` | TrainingType | ✅ | Typ treningu |
| `description` | string? | ❌ | Opis (max 500) |

**Response `201`:** `TrainingResponse`

---

##### `GET /workouts/trainings/{training_id}` — Szczegóły treningu

**Response `200`:** `TrainingResponse`

---

##### `GET /workouts/trainings/{training_id}/with-exercises` — Trening z pełnymi danymi ćwiczeń

Zwraca trening z zagnieżdżonymi pełnymi obiektami ćwiczeń zamiast samych ID.

**Response `200`:** `TrainingWithExercises`

---

##### `PUT /workouts/trainings/{training_id}` — Aktualizuj trening

**Request Body (`TrainingUpdate`):** Wszystkie pola opcjonalne.

**Response `200`:** `TrainingResponse`

---

##### `DELETE /workouts/trainings/{training_id}` — Usuń trening

**Response `204`:** No Content

---

#### 11.3.4 Plany treningowe (Workout Plans)

##### `GET /workouts/plans` — Lista planów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 100 | Limit (1-500) |
| `search` | string? | ❌ | — | Wyszukiwanie |
| `is_public` | boolean? | ❌ | — | Filtruj publiczne/prywatne |
| `trainer_id` | string? | ❌ | — | Filtruj po trenerze |

**Response `200`:** `Array[WorkoutPlanResponse]`

```json
[
  {
    "_id": "uuid",
    "name": "8-Week Strength Program",
    "trainer_id": "user-id",
    "clients": ["client1-id", "client2-id"],
    "trainings": ["training1-id", "training2-id"],
    "schedule": {
      "monday": "training1-id",
      "wednesday": "training2-id",
      "friday": "training1-id"
    },
    "description": "Progressive overload program",
    "is_public": true,
    "total_likes": 15,
    "_created_at": "2026-01-15T10:30:00",
    "_updated_at": "2026-01-15T10:30:00"
  }
]
```

---

##### `POST /workouts/plans` — Utwórz plan

**Headers:** `X-User-Id` (**wymagany**)

**Request Body (`WorkoutPlanCreate`):**

```json
{
  "name": "8-Week Strength Program",
  "clients": [],
  "trainings": [],
  "schedule": null,
  "description": "Progressive overload program",
  "is_public": false
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `name` | string | ✅ | Nazwa (1-100) |
| `clients` | List[str]? | ❌ | ID klientów (default: []) |
| `trainings` | List[str]? | ❌ | ID treningów (default: []) |
| `schedule` | dict? | ❌ | Harmonogram |
| `description` | string? | ❌ | Opis (max 1000) |
| `is_public` | boolean | ❌ | Publiczny (default: false) |

**Response `201`:** `WorkoutPlanResponse`

---

##### `GET /workouts/plans/my-plans` — Moje plany

**Headers:** `X-User-Id` (**wymagany**)

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 100 | Limit (1-500) |

**Response `200`:** `Array[WorkoutPlanResponse]`

---

##### `GET /workouts/plans/assigned-to-me` — Plany przypisane do mnie

**Headers:** `X-User-Id` (**wymagany**)

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 100 | Limit (1-500) |

**Response `200`:** `Array[WorkoutPlanResponse]`

---

##### `GET /workouts/plans/{plan_id}` — Szczegóły planu

**Response `200`:** `WorkoutPlanResponse`

---

##### `GET /workouts/plans/{plan_id}/detailed` — Plan ze szczegółami treningów

Zwraca plan z pełnymi danymi treningów i ćwiczeń.

**Response `200`:** `WorkoutPlanDetailed`

```json
{
  "_id": "uuid",
  "name": "8-Week Strength Program",
  "trainer_id": "user-id",
  "clients": ["client1-id"],
  "trainings": [
    {
      "_id": "training-uuid",
      "name": "Push Day",
      "creator_id": "user-id",
      "exercises": [
        {
          "exercise_id": "...",
          "name": "Bench Press",
          "body_part": "chest",
          "sets": [...]
        }
      ],
      "est_time": 3600,
      "training_type": "push",
      "description": "...",
      "_created_at": "...",
      "_updated_at": "..."
    }
  ],
  "description": "Progressive overload program",
  "is_public": true,
  "total_likes": 15,
  "_created_at": "...",
  "_updated_at": "..."
}
```

---

##### `PUT /workouts/plans/{plan_id}` — Aktualizuj plan

> ⚠️ Tylko twórca może modyfikować plan (weryfikacja przez `X-User-Id`).

**Headers:** `X-User-Id` (**wymagany**)

**Request Body (`WorkoutPlanUpdate`):** Wszystkie pola opcjonalne.

**Response `200`:** `WorkoutPlanResponse`

---

##### `DELETE /workouts/plans/{plan_id}` — Usuń plan

> ⚠️ Tylko twórca może usunąć plan.

**Headers:** `X-User-Id` (**wymagany**)

**Response `204`:** No Content

---

##### `POST /workouts/plans/{plan_id}/clients/{client_id}` — Dodaj klienta do planu

**Headers:** `X-User-Id` (**wymagany**)

**Response `200`:** `WorkoutPlanResponse`

---

##### `DELETE /workouts/plans/{plan_id}/clients/{client_id}` — Usuń klienta z planu

**Headers:** `X-User-Id` (**wymagany**)

**Response `200`:** `WorkoutPlanResponse`

---

##### `POST /workouts/plans/{plan_id}/trainings/{training_id}` — Dodaj trening do planu

**Headers:** `X-User-Id` (**wymagany**)

**Response `200`:** `WorkoutPlanResponse`

---

##### `DELETE /workouts/plans/{plan_id}/trainings/{training_id}` — Usuń trening z planu

**Headers:** `X-User-Id` (**wymagany**)

**Response `200`:** `WorkoutPlanResponse`

---

##### `POST /workouts/plans/{plan_id}/like` — Polub plan

**Response `200`:** `WorkoutPlanResponse`

---

##### `POST /workouts/plans/{plan_id}/unlike` — Cofnij polubienie planu

**Response `200`:** `WorkoutPlanResponse`

---

#### 11.3.5 Schematy danych (Workout Service)

**`StructSet`**

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `volume` | float (>0) | ✅ | Ilość/objętość |
| `units` | SetUnit | ✅ | Jednostka |

**`TrainingExercise`**

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `exercise_id` | string | ✅ | ID ćwiczenia |
| `sets` | List[StructSet] | ✅ | Serie (min 1) |
| `rest_between_sets` | integer? | ❌ | Przerwa w sek. (default: 60) |
| `notes` | string? | ❌ | Notatki (max 500) |

**Enumeracje:**

| Enum | Wartości |
|---|---|
| **BodyPart** | `chest`, `back`, `shoulders`, `biceps`, `triceps`, `forearms`, `abs`, `obliques`, `quadriceps`, `hamstrings`, `glutes`, `calves`, `full_body`, `cardio` |
| **Advancement** | `beginner`, `intermediate`, `advanced`, `expert` |
| **ExerciseCategory** | `strength`, `cardio`, `flexibility`, `balance`, `plyometric`, `calisthenics`, `olympic_lifting`, `powerlifting`, `hiit`, `yoga`, `stretching` |
| **TrainingType** | `push`, `pull`, `legs`, `upper`, `lower`, `full_body`, `cardio`, `hiit`, `strength`, `hypertrophy`, `endurance`, `flexibility`, `custom` |
| **SetUnit** | `reps`, `seconds`, `minutes`, `meters`, `km`, `calories` |

---

### 11.4 Forum Service API

> **Base URL:** `http://localhost:8007/forum`
> **Wersja:** 1.0.0
> **Autoryzacja:** Bearer Token (HTTPBearer)

#### 11.4.1 Posty (Posts)

##### `GET /forum/posts` — Lista postów

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset (min 0) |
| `limit` | integer | ❌ | 100 | Limit (1-500) |

**Response `200`:** `Array[PostResponse]`

```json
[
  {
    "_id": "550e8400-e29b-41d4-a716-446655440000",
    "author_id": "auth0|1234567890",
    "title": "Best Recipe for Muscle Gain",
    "content": "Here's my favorite recipe for post-workout meal...",
    "tags": ["recipe", "fitness", "nutrition"],
    "images": ["https://example.com/image1.jpg"],
    "linked_recipes": ["recipe-id-1"],
    "linked_workouts": ["workout-id-1"],
    "total_likes": 42,
    "views_count": 156,
    "_created_at": "2026-01-15T10:30:00",
    "_updated_at": "2026-01-15T10:30:00"
  }
]
```

---

##### `POST /forum/posts` — Utwórz post

**Headers:** `X-User-Id` (opcjonalny)

**Request Body (`PostCreate`):**

```json
{
  "title": "Best Recipe for Muscle Gain",
  "content": "Here's my favorite recipe for post-workout meal...",
  "tags": ["recipe", "fitness", "nutrition"],
  "images": ["https://example.com/image1.jpg"],
  "linked_recipes": ["550e8400-e29b-41d4-a716-446655440001"],
  "linked_workouts": ["550e8400-e29b-41d4-a716-446655440002"]
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `title` | string | ✅ | Tytuł (3-200) |
| `content` | string | ✅ | Treść (10-5000) |
| `tags` | List[str]? | ❌ | Tagi (max 10) |
| `images` | List[str]? | ❌ | URLe zdjęć (max 5) |
| `linked_recipes` | List[str]? | ❌ | Linkowane przepisy |
| `linked_workouts` | List[str]? | ❌ | Linkowane treningi |

**Response `201`:** `PostResponse`

---

##### `GET /forum/posts/trending` — Posty trendujące

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |
| `min_coefficient` | float | ❌ | 0.0 | Minimalny współczynnik trendu |

**Response `200`:** `Array[PostResponse]` (posortowane po trending coefficient)

---

##### `GET /forum/posts/{post_id}` — Szczegóły posta

**Response `200`:** `PostResponse`

---

##### `PUT /forum/posts/{post_id}` — Aktualizuj post

> ⚠️ Tylko autor może modyfikować post.

**Headers:** `X-User-Id` (opcjonalny)

**Request Body (`PostUpdate`):**

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `title` | string? | ❌ | Tytuł (3-200) |
| `content` | string? | ❌ | Treść (10-5000) |
| `tags` | List[str]? | ❌ | Tagi (max 10) |
| `images` | List[str]? | ❌ | Zdjęcia (max 5) |
| `linked_recipes` | List[str]? | ❌ | Linkowane przepisy |
| `linked_workouts` | List[str]? | ❌ | Linkowane treningi |

**Response `200`:** `PostResponse`

---

##### `DELETE /forum/posts/{post_id}` — Usuń post

**Headers:** `X-User-Id`

**Response `204`:** No Content

---

#### 11.4.2 Wyświetlenia i trending

##### `POST /forum/posts/{post_id}/view` — Zarejestruj wyświetlenie

| Parametr | Typ | Wymagany | Opis |
|---|---|---|---|
| `engagement_seconds` | integer? | ❌ | Czas zaangażowania (min 0) |
| `X-User-Id` (header) | string? | ❌ | ID użytkownika (anonimowe dozwolone) |

**Response `200`:** pusty obiekt

---

##### `GET /forum/posts/{post_id}/views` — Liczba wyświetleń

| Parametr | Typ | Wymagany | Opis |
|---|---|---|---|
| `hours` | integer? | ❌ | Okno czasowe w godzinach (min 1) |

**Response `200`:** obiekt z liczbą wyświetleń

---

##### `POST /forum/posts/{post_id}/calculate-trending` — Oblicz współczynnik trendu

**Response `200`:** obiekt z obliczonym współczynnikiem

---

##### `POST /forum/posts/recalculate-trending` — Przelicz trending dla wszystkich

Zadanie administracyjne/background — przelicza współczynniki trendów dla wszystkich postów.

**Response `200`:** podsumowanie operacji

---

#### 11.4.3 Polubienia postów

##### `POST /forum/posts/{post_id}/like` — Polub post

**Headers:** `X-User-Id` (opcjonalny)

**Response `200`:** obiekt z aktualizacją

---

##### `DELETE /forum/posts/{post_id}/like` — Cofnij polubienie posta

**Headers:** `X-User-Id` (opcjonalny)

**Response `200`:** obiekt z aktualizacją

---

##### `GET /forum/posts/{post_id}/likes` — Liczba polubień posta

**Response `200`:** obiekt z liczbą polubień

---

##### `GET /forum/posts/{post_id}/like/status` — Status polubienia posta

**Headers:** `X-User-Id` (opcjonalny)

**Response `200`:** obiekt z informacją czy użytkownik polubił post

---

##### `POST /forum/posts/likes/check` — Bulk sprawdzenie polubień postów

**Headers:** `X-User-Id` (opcjonalny)

**Request Body:** obiekt z listą post IDs

**Response `200`:** mapa post_id → is_liked

---

#### 11.4.4 Komentarze (Comments)

##### `POST /forum/posts/{post_id}/comments` — Utwórz komentarz

**Headers:** `X-User-Id` (opcjonalny)

**Request Body (`CommentCreate`):**

```json
{
  "content": "Great post! Thanks for sharing this recipe.",
  "parent_comment_id": null
}
```

| Pole | Typ | Wymagane | Opis |
|---|---|---|---|
| `content` | string | ✅ | Treść (1-500) |
| `parent_comment_id` | string? | ❌ | ID rodzica (dla odpowiedzi) |

**Response `201`:** `CommentResponse`

```json
{
  "_id": "550e8400-e29b-41d4-a716-446655440002",
  "post_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "auth0|1234567890",
  "content": "Great post! Thanks for sharing.",
  "parent_comment_id": null,
  "total_likes": 0,
  "_created_at": "2026-01-15T10:35:00",
  "_updated_at": "2026-01-15T10:35:00"
}
```

---

##### `GET /forum/posts/{post_id}/comments` — Komentarze top-level

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 50 | Limit (1-200) |

**Response `200`:** `Array[CommentResponse]`

---

##### `GET /forum/posts/{post_id}/comments/tree` — Drzewo komentarzy

Zwraca komentarze z zagnieżdżonymi odpowiedziami.

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `max_depth` | integer | ❌ | 3 | Maksymalna głębokość (1-10) |

**Response `200`:** `Array[CommentTreeResponse]`

```json
[
  {
    "comment": {
      "_id": "comment-1",
      "post_id": "post-1",
      "user_id": "auth0|...",
      "content": "Great post!",
      "parent_comment_id": null,
      "total_likes": 15,
      "_created_at": "...",
      "_updated_at": "..."
    },
    "replies": [
      {
        "comment": {
          "_id": "comment-2",
          "content": "Thanks!",
          "parent_comment_id": "comment-1",
          ...
        },
        "replies": []
      }
    ]
  }
]
```

---

##### `GET /forum/posts/{post_id}/comments/count` — Liczba komentarzy

**Response `200`:** obiekt z liczbą komentarzy (włącznie z zagnieżdżonymi)

---

##### `GET /forum/comments/{comment_id}` — Szczegóły komentarza

**Response `200`:** `CommentResponse`

---

##### `PATCH /forum/comments/{comment_id}` — Aktualizuj komentarz

> ⚠️ Tylko autor może modyfikować komentarz.

**Headers:** `X-User-Id` (opcjonalny)

**Request Body (`CommentUpdate`):**

```json
{
  "content": "Updated comment content..."
}
```

**Response `200`:** `CommentResponse`

---

##### `DELETE /forum/comments/{comment_id}` — Usuń komentarz

> ⚠️ Usunięcie komentarza kasuje też wszystkie odpowiedzi.

**Headers:** `X-User-Id`

**Response `204`:** No Content

---

##### `GET /forum/comments/{comment_id}/replies` — Odpowiedzi na komentarz

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 50 | Limit (1-200) |

**Response `200`:** `Array[CommentResponse]`

---

#### 11.4.5 Polubienia komentarzy

##### `POST /forum/comments/{comment_id}/like` — Polub komentarz

**Headers:** `X-User-Id` (opcjonalny)

**Response `200`:** obiekt z aktualizacją

---

##### `DELETE /forum/comments/{comment_id}/like` — Cofnij polubienie komentarza

**Headers:** `X-User-Id` (opcjonalny)

**Response `200`:** obiekt z aktualizacją

---

##### `GET /forum/comments/{comment_id}/likes` — Liczba polubień komentarza

**Response `200`:** obiekt z liczbą polubień

---

##### `GET /forum/comments/{comment_id}/like/status` — Status polubienia komentarza

**Headers:** `X-User-Id` (opcjonalny)

**Response `200`:** obiekt ze statusem polubienia

---

##### `POST /forum/comments/likes/check` — Bulk sprawdzenie polubień komentarzy

**Headers:** `X-User-Id` (opcjonalny)

**Request Body:** obiekt z listą comment IDs

**Response `200`:** mapa comment_id → is_liked

---

#### 11.4.6 Wyszukiwanie (Search)

##### `GET /forum/search` — Wyszukiwanie pełnotekstowe

Przeszukuje forum, przepisy, treningi i autorów.

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string | ✅ | — | Fraza (1-200) |
| `category` | SearchCategory | ❌ | `all` | Kategoria wyszukiwania |
| `tags` | List[str]? | ❌ | — | Filtruj po tagach |
| `author_id` | string? | ❌ | — | Filtruj po autorze |
| `sort_by` | SearchSortBy | ❌ | `relevance` | Sortowanie |
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |

**Response `200`:** `SearchResponse`

```json
{
  "query": "tomato pasta",
  "category": "all",
  "total_results": 42,
  "posts": [
    {
      "id": "uuid",
      "title": "Best Tomato Pasta Recipe",
      "content": "...",
      "author_id": "uuid",
      "author_name": "John Doe",
      "tags": ["recipe", "pasta"],
      "images": [],
      "linked_recipes": [],
      "linked_workouts": [],
      "total_likes": 42,
      "views_count": 500,
      "comments_count": 5,
      "trending_coefficient": 0.85,
      "created_at": "2026-01-10T14:30:00Z",
      "updated_at": "2026-01-15T09:15:00Z",
      "relevance_score": 0.95,
      "result_type": "post"
    }
  ],
  "recipes": [
    {
      "id": "uuid",
      "name": "Tomato Pasta",
      "description": "Classic Italian pasta...",
      "author_id": "uuid",
      "prep_time": 1800,
      "difficulty": "easy",
      "tags": ["healthy", "vegetarian"],
      "image_url": "https://...",
      "result_type": "recipe"
    }
  ],
  "workouts": [
    {
      "id": "uuid",
      "name": "Full Body Strength",
      "description": "...",
      "author_id": "uuid",
      "duration": 3600,
      "difficulty": "intermediate",
      "workout_type": "strength",
      "tags": ["legs", "hypertrophy"],
      "image_url": "https://...",
      "result_type": "workout"
    }
  ],
  "authors": [
    {
      "id": "uuid",
      "name": "John Doe",
      "posts_count": 25,
      "total_likes": 500,
      "result_type": "author"
    }
  ],
  "has_more": true
}
```

---

##### `POST /forum/search` — Wyszukiwanie (body)

Alternatywa do GET z parametrami w body (dla złożonych zapytań).

**Request Body (`SearchQuery`):**

```json
{
  "query": "tomato pasta",
  "category": "all",
  "tags": ["healthy", "quick"],
  "author_id": null,
  "sort_by": "relevance",
  "skip": 0,
  "limit": 20
}
```

**Response `200`:** `SearchResponse`

---

##### `GET /forum/search/suggestions` — Autokompletacja

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string | ✅ | — | Częściowa fraza (2-100) |
| `limit` | integer | ❌ | 10 | Max sugestii (1-20) |

**Response `200`:** `SearchSuggestionsResponse`

```json
{
  "query": "tom",
  "suggestions": ["tomato pasta", "tomato sauce"],
  "tags": [
    {"tag": "tomato", "count": 15}
  ]
}
```

---

##### `GET /forum/search/tags` — Popularne tagi

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string? | ❌ | — | Filtruj tagi (max 50) |
| `limit` | integer | ❌ | 20 | Max tagów (1-50) |

**Response `200`:** `Array[TagSuggestion]`

```json
[
  {"tag": "fitness", "count": 87},
  {"tag": "healthy", "count": 65},
  {"tag": "recipe", "count": 42}
]
```

---

##### `GET /forum/search/by-tag/{tag}` — Posty po tagu

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `tag` | string (path) | ✅ | — | Nazwa tagu |
| `sort_by` | SearchSortBy | ❌ | `newest` | Sortowanie |
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |

**Response `200`:** `Array[PostSearchResult]`

---

##### `GET /forum/search/posts` — Wyszukaj tylko posty

Szybsze niż ogólne wyszukiwanie gdy potrzebne są tylko posty.

| Parametr | Typ | Wymagany | Domyślnie | Opis |
|---|---|---|---|---|
| `q` | string | ✅ | — | Fraza (1-200) |
| `tags` | List[str]? | ❌ | — | Filtruj po tagach |
| `author_id` | string? | ❌ | — | Filtruj po autorze |
| `sort_by` | SearchSortBy | ❌ | `relevance` | Sortowanie |
| `skip` | integer | ❌ | 0 | Offset |
| `limit` | integer | ❌ | 20 | Limit (1-100) |

**Response `200`:** `Array[PostSearchResult]`

---

#### 11.4.7 Schematy danych (Forum Service)

**`SearchCategory` (enum):** `all`, `posts`, `recipes`, `workouts`, `authors`

**`SearchSortBy` (enum):** `relevance`, `newest`, `trending`, `most_liked`

**`PostSearchResult`**

| Pole | Typ | Opis |
|---|---|---|
| `id` | string | ID posta |
| `title` | string | Tytuł |
| `content` | string | Treść/podgląd |
| `author_id` | string | ID autora |
| `author_name` | string? | Nazwa autora |
| `tags` | List[str] | Tagi |
| `images` | List[str] | Zdjęcia |
| `linked_recipes` | List[str] | Linkowane przepisy |
| `linked_workouts` | List[str] | Linkowane treningi |
| `total_likes` | int (≥0) | Polubienia |
| `views_count` | int (≥0) | Wyświetlenia |
| `comments_count` | int (≥0) | Komentarze |
| `trending_coefficient` | float (≥0) | Współczynnik trendu |
| `created_at` | datetime | Data utworzenia |
| `updated_at` | datetime? | Data modyfikacji |
| `relevance_score` | float (0-1) | Trafność wyszukiwania |
| `result_type` | const `"post"` | Typ wyniku |

**`RecipeSearchResult`**

| Pole | Typ | Opis |
|---|---|---|
| `id` | string | ID przepisu |
| `name` | string | Nazwa |
| `description` | string? | Opis |
| `author_id` | string? | ID autora |
| `prep_time` | int? | Czas przygotowania (sek.) |
| `difficulty` | string? | Poziom trudności |
| `tags` | List[str] | Tagi |
| `image_url` | string? | URL obrazka |
| `result_type` | const `"recipe"` | Typ wyniku |

**`WorkoutSearchResult`**

| Pole | Typ | Opis |
|---|---|---|
| `id` | string | ID treningu |
| `name` | string | Nazwa |
| `description` | string? | Opis |
| `author_id` | string? | ID autora |
| `duration` | int? | Czas trwania (sek.) |
| `difficulty` | string? | Poziom trudności |
| `workout_type` | string? | Typ treningu |
| `tags` | List[str] | Tagi |
| `image_url` | string? | URL obrazka |
| `result_type` | const `"workout"` | Typ wyniku |

**`AuthorSearchResult`**

| Pole | Typ | Opis |
|---|---|---|
| `id` | string | ID autora |
| `name` | string | Nazwa |
| `posts_count` | int (≥0) | Liczba postów |
| `total_likes` | int (≥0) | Suma polubień |
| `result_type` | const `"author"` | Typ wyniku |

---

## 12. Roadmap

| Faza | Status | Opis |
|---|---|---|
| Phase 1: Infrastruktura | ✅ | Gateway, Auth0, Redis, Docker |
| Phase 2: User Management | ✅ | Profile, preferencje, parametry ciała |
| Phase 3: Recipes & Nutrition | ✅ | Przepisy, składniki, makra, polubienia |
| Phase 4: Workouts & Training | ✅ | Ćwiczenia, treningi, plany, klienci |
| Phase 5: Community & Forum | ✅ | Posty, komentarze, trending, wyszukiwanie |
| Phase 6: Payments & Premium | 🔄 | Docker setup, Stripe (planned) |
| Phase 7: Analytics & Tracking | 🔄 | Docker setup, metryki (planned) |
| Phase 8: Notifications | ⏳ | Email, in-app, push |
| Phase 9: Integrations | ⏳ | Fitbit, Google Fit, Apple Health |
| Phase 10: AI Features | ⏳ | Google Gemini — generowanie przepisów i treningów |

---

*Dokument wygenerowany: luty 2026*
*Wersja dokumentacji: 1.0.0*
