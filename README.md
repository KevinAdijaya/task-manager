# Task Manager API

A production-ready Task Manager REST API built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0**, and **JWT Authentication**. Includes a clean vanilla JavaScript frontend for demonstration.

[![CI/CD](https://github.com/KevinAdijaya/task-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/KevinAdijaya/task-manager/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ Features

### Backend API
- **Full CRUD** for tasks with title, description, status, priority, category, due dates
- **JWT Authentication** with access/refresh tokens, bcrypt password hashing
- **User Registration & Login** with validation
- **Advanced Filtering** by status, priority, category, search query
- **Pagination** with configurable page size
- **Statistics Endpoint** for dashboard metrics (counts by status/priority, overdue)
- **Auto-generated API Docs** (Swagger UI at `/docs`, ReDoc at `/redoc`)
- **Database Migrations** with Alembic
- **Comprehensive Test Suite** (unit + integration, ≥80% coverage)
- **Type Safety** with Pydantic v2, SQLModel, mypy
- **Code Quality** with Ruff linting/formatting

### Frontend (Vanilla JS)
- **Zero dependencies** — no React, Vue, or build step
- **Clean, responsive UI** with CSS custom properties (dark mode support)
- **Modal-based forms** for auth and task management
- **Real-time filtering** with debounced search
- **Toast notifications** for user feedback
- **Accessible** (ARIA labels, keyboard navigation, focus management)

---

## 🏗 Architecture

```
task-manager/
├── app/
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py            # Pydantic Settings (.env)
│   ├── database.py          # SQLAlchemy async engine/session
│   ├── models/              # SQLModel models (User, Task)
│   ├── schemas/             # Pydantic schemas (request/response)
│   ├── core/
│   │   └── security.py      # JWT, password hashing
│   ├── api/
│   │   ├── deps.py          # FastAPI dependencies (auth, DB)
│   │   └── routes/
│   │       ├── auth.py      # /auth endpoints
│   │       └── tasks.py     # /tasks endpoints
│   └── services/            # Business logic layer
├── tests/                   # pytest + httpx tests
├── alembic/                 # Database migrations
├── frontend/                # Vanilla JS frontend
├── docker-compose.yml       # Local dev stack (PostgreSQL + app)
├── Dockerfile               # Multi-stage production build
├── render.yaml              # One-click Render.com deploy
└── .github/workflows/ci.yml # GitHub Actions CI/CD
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for local PostgreSQL)
- Or local PostgreSQL 14+

### 1. Clone & Configure

```bash
git clone https://github.com/KevinAdijaya/task-manager.git
cd task-manager

# Copy environment template
cp .env.example .env
# Edit .env with your settings (SECRET_KEY, DATABASE_URL, etc.)
```

### 2. Start with Docker Compose (Recommended)

```bash
# Start PostgreSQL + API with hot reload
docker-compose up --build

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
# pgAdmin at http://localhost:5050 (profile: tools)
```

### 3. Or Run Locally

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL (or use local)
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=task_manager \
  -p 5432:5432 postgres:16-alpine

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open Frontend

Open `frontend/index.html` directly in browser, or serve it:

```bash
cd frontend && python -m http.server 8080
# Then visit http://localhost:8080
```

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All task endpoints require `Authorization: Bearer <access_token>` header.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | Login with `email` + `password`, returns access + refresh tokens |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/me` | GET | Get current user profile |

### Tasks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks/` | POST | Create task |
| `/tasks/` | GET | List tasks (with filters, pagination) |
| `/tasks/stats/summary` | GET | Get task statistics |
| `/tasks/{id}` | GET | Get single task |
| `/tasks/{id}` | PATCH | Update task (partial) |
| `/tasks/{id}` | DELETE | Delete task |

### Query Parameters (List Tasks)
| Param | Type | Description |
|-------|------|-------------|
| `status` | enum | `pending`, `in_progress`, `done` |
| `priority` | enum | `low`, `medium`, `high` |
| `category` | string | Partial match |
| `search` | string | Search title & description |
| `page` | int | Page number (≥1) |
| `page_size` | int | Items per page (1-100) |

### Example Requests

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "john", "password": "securepass123"}'

# Login (email + password only)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'

# Create task (with token)
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "priority": "high", "category": "Learning"}'

# List tasks with filters
curl -G http://localhost:8000/api/v1/tasks/ \
  -H "Authorization: Bearer <access_token>" \
  -d status=pending \
  -d priority=high \
  -d page=1 \
  -d page_size=10
```

---

## 🧪 Testing

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run with watched mode (requires pytest-watch)
ptw
```

### Test Structure
- `tests/conftest.py` — Fixtures (DB, client, auth headers, test data)
- `tests/test_auth.py` — Auth flow tests (register, login, refresh, me)
- `tests/test_tasks.py` — Task CRUD, filtering, pagination, stats

---

## 🐳 Docker

### Development
```bash
docker-compose up --build
# App: http://localhost:8000 (hot reload enabled)
# DB:  localhost:5432
```

### Production Build
```bash
docker build --target production -t task-manager:latest .
docker run -d -p 8000:8000 --env-file .env task-manager:latest
```

---

## 📦 Deployment

### Render.com (Free Tier)
1. Push to GitHub
2. Connect repo at [render.com](https://render.com)
3. Use `render.yaml` for automatic setup:
   - Web Service (Docker)
   - PostgreSQL Database
4. `DATABASE_URL` is injected automatically by Render — no manual config needed.
5. *(Optional)* Enable auto-deploy from CI: create a **Deploy Hook** in
   Render (Service → Settings → Deploy) and add it as a repository secret
   named `RENDER_DEPLOY_HOOK_URL`. Until then, the deploy job is skipped
   gracefully and CI stays green.

### Fly.io
```bash
flyctl launch --dockerfile Dockerfile
flyctl secrets set SECRET_KEY=$(openssl rand -base64 32)
flyctl deploy
```

### Railway
```bash
railway login
railway init
railway add postgresql
railway up
```

### Environment Variables (Production)
```env
APP_ENV=production
DEBUG=false
SECRET_KEY=your-32-char-min-secret-key
# Option A: full URL (Render/Railway set this automatically)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
# Option B: individual vars (docker-compose & CI)
POSTGRES_HOST=your-db-host
POSTGRES_PASSWORD=secure-password
BACKEND_CORS_ORIGINS=["https://your-frontend.com"]
```

---

## 🛠 Development

### Code Quality
```bash
# Format & lint
ruff check . --fix
ruff format .

# Type check
mypy app

# Pre-commit hooks (install once)
pre-commit install
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Project Structure Guidelines
- **Routes** → Thin, only HTTP concerns
- **Services** → Business logic, DB operations
- **Schemas** → Request/response validation
- **Models** → Database tables only
- **Dependencies** → Auth, DB session, common params

---

## 📄 License

MIT License — feel free to use for learning or production.

---

## 🙋‍♂️ Author

Built as a portfolio project demonstrating:
- Modern FastAPI patterns
- Clean architecture
- Testing & CI/CD
- Docker & deployment
- Vanilla JS frontend

**Star ⭐ this repo if you found it helpful!**