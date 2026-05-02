# Lucknow Water Bowl Distribution Backend

Backend API for managing water bowl distribution drives for animals in Lucknow, India.

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 15+
- [uv](https://docs.astral.sh/uv/) package manager

### Local Development

```bash
# Install dependencies
uv sync

# Copy environment variables
cp .env.example .env

# Run database migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/drives/` | Create a distribution drive |
| `GET` | `/api/v1/drives/` | List all drives |
| `GET` | `/api/v1/drives/{id}` | Get drive details |
| `POST` | `/api/v1/drives/{id}/addresses` | Add addresses to a drive |
| `POST` | `/api/v1/geocode` | Geocode a list of addresses |
| `POST` | `/api/v1/optimize-route` | Compute optimal visit order |
| `POST` | `/api/v1/distributions/` | Record a bowl distribution (multipart form) |
| `GET` | `/api/v1/distributions/` | List all distributions |
| `GET` | `/api/v1/distributions/{id}` | Get distribution details |
| `GET` | `/api/v1/stats` | Get summary statistics |

## Database Migrations

```bash
# Create a new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Settings via pydantic-settings
│   ├── database.py           # SQLAlchemy async engine & session
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── api/
│   │   ├── deps.py           # Dependency injection (DB session)
│   │   └── routes/           # API route handlers
│   └── services/
│       ├── geocoding.py      # Nominatim geocoding with caching
│       └── route_optimizer.py # Nearest-neighbour TSP solver
├── alembic/                  # Database migrations
├── uploads/                  # Uploaded photos
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```
