# MealUp

MealUp is a social platform for healthy nutrition, workout planning, and fitness community interaction. Users can create recipes, organize meal and training plans, track progress, and get personalized recommendations.

> **Status**: Active development project. Features being added incrementally.

## Overview

MealUp is a comprehensive social platform combining:

- **Healthy nutrition** – Recipe library with 500+ ingredients, macro tracking, custom recipe creation
- **Workout planning** – Exercise database, training plans by day/type, workout plan builder
- **Community** – Forum with posts, comments, likes, trending algorithm
- **Personal tracking** – User profiles, preferences, progress monitoring (in development)
- **Authentication** – Secure Auth0 integration with JWT tokens
- **AI Assistants** – Conversational AI for guided recipe and workout creation
- **RAG System** – Retrieval-Augmented Generation for intelligent, context-aware recommendations
- **AI Image Generation** – Automatic recipe photo generation via open-source text-to-image model on save

**Built with microservices architecture** for scalability, featuring independent services for recipes, workouts, forum, and user management, all coordinated through a central API Gateway.

## Current Status

### ✅ Fully Implemented
- **API Gateway** (Port 8000) - Microservices proxy with request routing
- **Auth Service** (Port 8001) - Auth0 integration, JWT tokens, session management with Redis
- **User Service** (Port 8002) - User profiles, CRUD operations, Auth0 synchronization
- **Recipe Service** (Port 8003) - Recipe & ingredient management, search & filtering
- **Workout Service** (Port 8004) - Exercise library, training plans, workout plan builder
- **Forum Service** (Port 8007) - Posts, comments, likes, trending algorithm, search
- **Frontend UI** - Complete navigation, dashboard, recipes, workouts, community views
- **Infrastructure** - Docker Compose setup, health checks, request logging

### 🤖 AI Features (In Development)
- **AI Recipe Assistant** - Conversational assistant guiding users through recipe creation step-by-step
- **AI Workout Assistant** - Conversational assistant for building personalized training plans
- **RAG System** - Retrieval-Augmented Generation over recipe & exercise knowledge base for smart suggestions
- **Text-to-Image Generation** - Open-source model (e.g. Stable Diffusion) auto-generates recipe cover photos on database save

### 🔄 Partially Implemented
- Payment Service (Docker setup only, no implementation)
- Analytics Service (Docker setup only, no implementation)
- Notification Service (Docker setup only, no implementation)

### ⏳ Planned Features
- Meal plan generator & tracker
- Progress analytics & tracking
- Fitness integrations (Fitbit, Google Fit)
- Stripe payment processing
- Email & in-app notifications
- Advanced recommendation engine

## System Architecture

```
Frontend (Port 3000) - Next.js UI
    ↓
API Gateway (Port 8000) - Single entry point, routing & auth
    ↓
├── ✅ Auth Service (Port 8001)
│   └── Redis (sessions & tokens)
├── ✅ User Service (Port 8002)
│   └── PostgreSQL (shared)
├── ✅ Recipe Service (Port 8003)
│   ├── MongoDB (shared)
│   ├── 🤖 AI Recipe Assistant (LLM-powered)
│   ├── 🤖 Text-to-Image (auto recipe photo on save)
│   └── 🤖 RAG Engine (vector store + retrieval)
├── ✅ Workout Service (Port 8004)
│   ├── MongoDB (shared)
│   └── 🤖 AI Workout Assistant (LLM-powered)
├── 🔄 Payment Service (Port 8005)
│   └── PostgreSQL (shared)
├── 🔄 Analytics Service (Port 8006)
│   └── MongoDB (shared)
├── ✅ Forum Service (Port 8007)
│   └── PostgreSQL (shared)
└── 🔄 Notification Service (Port 8008)
    └── Redis

✅ = Fully Implemented  |  🔄 = Partial/Docker Only  |  🤖 = AI Feature
```

## Microservices

| Service | Port | Database | Status | Features |
|---------|------|----------|--------|----------|
| **API Gateway** | 8000 | Redis | ✅ | Request routing, proxy, logging, health checks |
| **Auth Service** | 8001 | Redis | ✅ | Auth0 integration, JWT tokens, session management |
| **User Service** | 8002 | PostgreSQL | ✅ | User CRUD, profiles, Auth0 sync, preferences |
| **Recipe Service** | 8003 | MongoDB | ✅ 🤖 | Recipes, ingredients, search, macros; **AI assistant**, **text-to-image**, **RAG** |
| **Workout Service** | 8004 | MongoDB | ✅ 🤖 | Exercises, trainings, workout plans; **AI workout assistant** |
| **Forum Service** | 8007 | PostgreSQL | ✅ | Posts, comments, likes, trending, search |
| **Payment Service** | 8005 | PostgreSQL | 🔄 | Docker setup only (planned: Stripe) |
| **Analytics Service** | 8006 | MongoDB | 🔄 | Docker setup only (planned: tracking) |
| **Notification Service** | 8008 | Redis | 🔄 | Docker setup only (planned: email/push) |

## Key Features by Service

### 🔐 Authentication & User Management
- **Auth0 Integration**: OAuth 2.0 authentication with JWT tokens
- **Session Management**: Redis-based session storage for fast access
- **User Profiles**: Full CRUD operations, preferences, Auth0 synchronization
- **Protected Routes**: Shared auth guard middleware across all services

### 🍽️ Recipe & Nutrition
- **Recipe Library**: Create, read, update, delete recipes with full metadata
- **Ingredient Database**: 500+ ingredients with macro information (calories, protein, carbs, fats)
- **Search & Filter**: Find recipes by name, author, ingredients, or dietary requirements
- **Macro Tracking**: Automatic calculation of nutritional values
- **🤖 AI Recipe Assistant**: Conversational LLM assistant that guides users through building a recipe step-by-step — suggests ingredients, proportions, and preparation steps based on user preferences
- **🤖 Automatic Recipe Photos**: On every recipe save, an open-source text-to-image model (Stable Diffusion) generates a cover photo automatically from the recipe name and description — no manual upload required
- **🤖 RAG-Powered Suggestions**: A retrieval-augmented generation pipeline indexes the recipe and ingredient knowledge base, enabling the assistant to ground its answers in real data from the platform

### 💪 Workout & Training
- **Exercise Library**: Comprehensive database with body part targeting, advancement levels, categories
- **Training Plans**: Create structured training sessions with exercises, sets, reps, and rest periods
- **Workout Plans**: Organize trainings by day of week and training type (strength, cardio, etc.)
- **Filtering**: Advanced search by body part, difficulty, exercise category
- **🤖 AI Workout Assistant**: Conversational AI assistant that helps users compose personalized training plans — recommends exercises based on goals, fitness level, and available equipment, powered by the same RAG system

### 🤖 AI & Machine Learning
- **AI Assistants**: Two domain-specific chat assistants (recipe & workout) built on top of an LLM, integrated directly into the UI
- **RAG System**: Vector-store retrieval (over recipes, exercises, and nutritional data) feeds context to the LLM, reducing hallucinations and providing accurate, platform-specific answers
- **Text-to-Image Pipeline**: Open-source generative model generates food photography-style images automatically when a recipe is persisted — images are stored alongside recipe metadata in MongoDB
- **Prompt Engineering**: Carefully crafted system prompts and retrieval strategies ensure assistants stay focused on health and fitness topics

### 👥 Community & Social
- **Forum Posts**: Create and browse community posts with rich content
- **Comments**: Threaded discussions on posts
- **Like System**: Engagement tracking for posts
- **Trending Algorithm**: Discover popular content based on engagement coefficient
- **Search**: Find posts and discussions by keywords

### 🚪 API Gateway
- **Unified Entry Point**: Single endpoint for all microservices (http://localhost:8000)
- **Request Routing**: Automatic proxy to appropriate services
- **Logging**: Comprehensive request/response logging
- **Health Checks**: Monitor service availability
- **CORS Handling**: Configured for frontend integration

## Tech Stack

**Frontend**: Next.js 14, React, TailwindCSS, Framer Motion  
**Backend**: FastAPI (Python 3.11+), microservices architecture  
**Databases**:
- PostgreSQL 16 (User, Forum, Payment services - shared instance)
- MongoDB 7 (Recipe, Workout, Analytics services - shared instance)
- Redis 7 (Auth sessions, Notifications - separate instances)
- Vector Store (RAG pipeline — embeddings index over recipes & exercises)

**Authentication**: Auth0, JWT tokens, session management  
**Infrastructure**: Docker, Docker Compose  
**API**: RESTful APIs, OpenAPI/Swagger documentation  
**Shared Libraries**: Common auth guard module for microservices  
**AI / ML**:
- LLM integration (OpenAI-compatible API) for recipe & workout assistants
- RAG pipeline: embedding model + vector retrieval + prompt augmentation
- Text-to-image: open-source Stable Diffusion model for automatic recipe cover photos
- Prompt engineering & context management for domain-focused assistants

## Quick Start

```bash
# Clone repository
git clone <repo>
cd MealUp

# Start all services (includes setup for all 8 microservices)
docker-compose up --build

# Access points:
# - Frontend UI: http://localhost:3000
# - API Gateway: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - Individual services: ports 8001-8008
```

### What's Working:
- Full authentication flow with Auth0
- User profile management
- Recipe browsing, creation, and search (MongoDB)
- Workout plan creation with exercise library (MongoDB)
- Community forum with posts, comments, and trending (PostgreSQL)
- Complete UI with navigation between all sections

### Environment Setup:
You'll need to configure Auth0 credentials and database passwords in a `.env` file. See docker-compose.yml for required environment variables.

## Project Structure

```
MealUp/
├── frontend/                      # Next.js + React + TailwindCSS
│   ├── app/
│   │   ├── components/           # UI components
│   │   │   ├── Dashboard.jsx     # Main dashboard
│   │   │   ├── RecipesView.jsx   # Recipe browser
│   │   │   ├── WorkoutsView.jsx  # Workout planner
│   │   │   ├── Community.jsx     # Forum interface
│   │   │   ├── Profile.jsx       # User profile
│   │   │   └── Navigation.jsx    # App navigation
│   │   ├── services/             # API service layer
│   │   ├── page.js               # Main app page
│   │   └── layout.js
│   └── package.json
├── backend/
│   ├── common/                   # Shared auth & utilities
│   ├── gateway/                  # ✅ API Gateway (Port 8000)
│   ├── auth-service/             # ✅ Port 8001 (Auth0 + Redis)
│   ├── user-service/             # ✅ Port 8002 (PostgreSQL)
│   ├── recipe-service/           # ✅ Port 8003 (MongoDB)
│   ├── workout-service/          # ✅ Port 8004 (MongoDB)
│   ├── forum-service/            # ✅ Port 8007 (PostgreSQL)
│   └── scripts/                  # Database init scripts
└── docker-compose.yml            # Full stack orchestration
```

**Note:** Payment (8005), Analytics (8006), and Notification (8008) services are defined in Docker Compose but not yet implemented.

## Features Roadmap

### Phase 1: Core Infrastructure ✅ COMPLETED
- ✅ API Gateway with proxy routing
- ✅ Auth0 integration & JWT tokens
- ✅ Session management with Redis
- ✅ Docker Compose orchestration
- ✅ Health checks & monitoring

### Phase 2: User Management ✅ COMPLETED
- ✅ User service with PostgreSQL
- ✅ User profiles & preferences
- ✅ Auth0 user synchronization
- ✅ Profile UI component

### Phase 3: Recipes & Nutrition ✅ COMPLETED
- ✅ Recipe creation & management
- ✅ Ingredient library with macros
- ✅ Recipe search & filtering
- ✅ Recipe browsing UI

### Phase 3b: AI Recipe Features 🔄 IN PROGRESS
- 🔄 AI Recipe Assistant (LLM + RAG)
- 🔄 RAG pipeline over recipe & ingredient knowledge base
- 🔄 Text-to-image recipe photo generation (Stable Diffusion)
- ⏳ Assistant UI integrated into recipe creation flow

### Phase 4: Workouts & Training ✅ COMPLETED
- ✅ Exercise library (body parts, advancement levels)
- ✅ Training plan builder
- ✅ Workout plan management
- ✅ Workout UI component

### Phase 4b: AI Workout Features 🔄 IN PROGRESS
- 🔄 AI Workout Assistant (LLM + shared RAG system)
- ⏳ Assistant UI integrated into workout plan creation flow

### Phase 5: Community & Forum ✅ COMPLETED
- ✅ Forum posts & comments
- ✅ Like system
- ✅ Trending algorithm
- ✅ Search functionality
- ✅ Community UI

### Phase 6: Payments & Premium 🔄 IN PROGRESS
- 🔄 Docker setup for payment service
- ⏳ Stripe integration
- ⏳ Subscription management
- ⏳ Premium features

### Phase 7: Analytics & Tracking 🔄 IN PROGRESS  
- 🔄 Docker setup for analytics service
- ⏳ Progress tracking
- ⏳ Fitness metrics
- ⏳ Data visualization

### Phase 8: Notifications ⏳ PLANNED
- 🔄 Docker setup for notification service
- ⏳ Email notifications
- ⏳ In-app notifications
- ⏳ Push notifications

### Phase 9: Integrations ⏳ PLANNED
- ⏳ Fitbit integration
- ⏳ Google Fit integration
- ⏳ Apple Health integration
- ⏳ Meal plan generator

## Contributing

This is an active project as part of a Bachelor’s Degree for university coursework (Semester 5 - Team Project).
**Current Focus**: 
- 🤖 Building AI Recipe & Workout Assistants with RAG
- 🤖 Integrating text-to-image (Stable Diffusion) for automatic recipe photos
- 🤖 Setting up vector store and embedding pipeline for RAG
- Implementing payment service with Stripe
- Building analytics and tracking features
- Adding notification system
- Developing meal plan generator

**Completed Milestones**:
- ✅ Full microservices infrastructure
- ✅ Authentication & authorization
- ✅ Recipe management system
- ✅ Workout planning system
- ✅ Community forum with trending algorithm
- ✅ Complete frontend UI with all main views
