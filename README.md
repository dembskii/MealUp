# MealUp

MealUp is a social platform for healthy nutrition, workout planning, and fitness community interaction. Users can create recipes, organize meal and training plans, track progress, and get personalized recommendations.

> **Status**: Active development project. Features being added incrementally.

## Overview

- **Healthy nutrition** – recipes, calorie tracking, ingredients
- **Workout planning** – exercise library, training plans, trainer recommendations
- **Community** – forum, comments, reputation system
- **Personal goals** – progress tracking, analytics, fitness integrations

## Current Status

### ✅ Implemented
- API Gateway (Port 8000) with microservices proxy
- Auth0 integration
- Session management with Redis
- Frontend navigation & authentication UI
- Docker & Docker Compose setup
- Request logging & error handling
- Health checks and service monitoring

### 🔄 In Progress
- User profiles & management
- Recipe creation & browsing
- Meal plan builder
- Recipe search & filtering

### ⏳ Planned
- Training plans & workout library
- Community forum
- Progress tracking & analytics
- Integrations (Fitbit, Google Fit)
- Stripe payments

## System Architecture

```
API Gateway (Port 8000) - Single entry point
├── Auth Service (Port 8001)
│   └── Redis (sessions)
├── User Service (Port 8002)
│   └── PostgreSQL
├── Recipe Service (Port 8003)
│   └── MongoDB
├── Workout Service (Port 8004)
│   └── MongoDB
├── Payment Service (Port 8005)
│   └── PostgreSQL
├── Analytics Service (Port 8006)
│   └── MongoDB
├── Forum Service (Port 8007)
│   └── PostgreSQL
└── Notification Service (Port 8008)
    └── Redis
```

## Microservices

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| **Auth Service** | 8001 | Redis | User authentication, JWT tokens |
| **User Service** | 8002 | PostgreSQL | User profiles, preferences |
| **Recipe Service** | 8003 | MongoDB | Recipes, ingredients, macros |
| **Workout Service** | 8004 | MongoDB | Training plans, exercises |
| **Payment Service** | 8005 | PostgreSQL | Stripe integration, transactions |
| **Analytics Service** | 8006 | MongoDB | Tracking, metrics, logs |
| **Forum Service** | 8007 | PostgreSQL | Posts, comments, reputation |
| **Notification Service** | 8008 | Redis | Email, in-app notifications |

## Tech Stack

**Frontend**: Next.js, React, TailwindCSS  
**Backend**: FastAPI (Python), microservices architecture  
**Databases**: PostgreSQL, MongoDB, Redis  
**Infrastructure**: Docker, Docker Compose, CI/CD
**Auth**: Auth0, JWT  

## Quick Start

```bash
# Clone and setup
git clone <repo>
cd MealUp

# Start all services
docker-compose up --build

# Frontend: http://localhost:3000
# API Gateway: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Approximate Project Structure

```
MealUp/
├── frontend/                      # Next.js app
│   ├── app/
│   │   ├── components/
│   │   ├── page.js
│   │   └── layout.js
│   └── package.json
├── backend/
│   ├── gateway/                  # API Gateway (FastAPI)
│   ├── auth-service/             # Port 8001
│   ├── user-service/             # Port 8002
│   ├── recipe-service/           # Port 8003
│   ├── workout-service/          # Port 8004
│   ├── payment-service/          # Port 8005
│   ├── analytics-service/        # Port 8006
│   ├── forum-service/            # Port 8007
│   └── notification-service/     # Port 8008
└── docker-compose.yml
```

## Features Roadmap

### Phase 1: Core Infrastructure ✅
- API Gateway with proxy routing
- Auth0 integration
- Basic frontend UI

### Phase 2: Recipes & Meals 🔄
- Recipe creation & management
- Ingredient tracking
- Meal planning interface

### Phase 3: Workouts & Training ⏳
- Workout library
- Training plan builder
- Progress tracking

### Phase 4: Community ⏳
- Forum posts & comments
- Reputation system
- User moderation

### Phase 5: Payments & Analytics ⏳
- Stripe integration
- Advanced tracking
- Fitness integrations

## Contributing

This is an active development project. See implementation roadmap above for current focus areas.
