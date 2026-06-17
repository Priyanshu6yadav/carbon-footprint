# CarbonTrack 🌱

> A full-stack carbon footprint awareness platform — calculate emissions, track eco-habits, get AI-personalized sustainability advice, and stay motivated through gamification.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript, Vite, Tailwind CSS, ShadCN UI, Recharts, Framer Motion |
| Backend | FastAPI (Python 3.12), Pydantic v2 |
| Database | PostgreSQL 16 + SQLAlchemy (async) + Alembic |
| Cache | Redis 7 |
| AI | Groq API (llama-3.3-70b-versatile) |
| Auth | JWT (access + refresh), bcrypt |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.12+ (for local backend dev)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd carbontrack
cp .env.example .env
# Edit .env and fill in the required environment values.
# Generate strong secrets: openssl rand -hex 64
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

Services will be available at:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### 3. Apply Migrations

```bash
# Inside the backend container (first run)
docker compose exec backend alembic upgrade head
```

### Local Development (without Docker)

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # fill in values
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
carbontrack/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app factory
│   │   ├── config.py         # Pydantic Settings
│   │   ├── database.py       # Async SQLAlchemy
│   │   ├── redis_client.py   # Async Redis
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic v2 request/response schemas
│   │   ├── routers/          # FastAPI route handlers
│   │   ├── services/         # Business logic
│   │   └── middleware/       # Security headers, etc.
│   ├── alembic/              # DB migrations
│   ├── data/
│   │   └── emission_factors.json  # EPA/DEFRA emission factors
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Route-level page components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API service layer
│   │   ├── store/            # Zustand state
│   │   └── types/            # TypeScript types
│   └── package.json
├── .github/workflows/ci.yml  # GitHub Actions CI
├── docker-compose.yml
├── .env.example              # Safe to commit — no secrets
└── README.md
```

## Security

- Passwords hashed with bcrypt (12 rounds)
- Separate JWT secrets for access vs refresh tokens
- Refresh tokens rotated on use, stored in DB (invalidated on logout)
- Rate limiting on auth endpoints (5/min per IP, Redis-backed)
- Security headers middleware (HSTS, X-Frame-Options, X-Content-Type-Options)
- All auth events logged to `audit_logs` table
- No raw SQL — ORM only throughout

## Environment Variables

See [`.env.example`](.env.example) for the full list. Required at startup:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_REFRESH_SECRET`

Optional (features degrade gracefully if missing):
- `GROQ_API_KEY` — AI recommendations (Phase 2)

## Render Deployment

For production on Render, configure these Environment Variables instead of storing credentials in source control:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_REFRESH_SECRET`
- `GROQ_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `ENVIRONMENT=production`

Never commit real credentials into `.env.example` or repository files.
