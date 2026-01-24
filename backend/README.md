# Backend Service

FastAPI application that powers the scheduling platform. It exposes REST APIs, manages the PostgreSQL schema, and handles uploads to an S3-compatible storage (MinIO by default).

## Tech Stack
- FastAPI + Uvicorn (ASGI server)
- SQLAlchemy 2.0 (async) with asyncpg
- Alembic for database migrations
- aioboto3 for S3/MinIO access
- uv for dependency management and scripts

## Requirements
- Python 3.13 (managed through `uv`)
- PostgreSQL 15+ (Docker Compose uses 18-alpine)
- MinIO or any S3-compatible storage for file uploads
- Docker & Docker Compose v2 (optional but recommended for parity)

## Quick Start

### Run inside Docker Compose (recommended)
```bash
cd ..
docker compose up --build backend db minio
```
The backend container runs `scripts/init.sh`, which waits for PostgreSQL, applies Alembic migrations, and then launches Uvicorn on port 8000.

### Run locally with uv
```bash
cd backend
uv sync
touch .env  # fill in the variables listed below
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```
Run PostgreSQL and MinIO locally (Docker, Podman, or your preferred setup) and make sure the `.env` values point to those services.

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | FastAPI Base App | Title exposed in OpenAPI |
| `APP_VERSION` | 1.0.0 | Semantic version shown in docs |
| `DEBUG` | true | Enables verbose SQL logging |
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | `db`, `5432`, `postgres`, `postgres`, `postgres` | Connection settings for PostgreSQL |
| `S3_ENDPOINT_URL` | http://minio:9000 | MinIO endpoint |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | minioadmin / minioadmin | Credentials for MinIO |
| `S3_REGION` | us-east-1 | Fake region for local MinIO |
| `S3_BUCKET_NAME` | default-bucket | Bucket created automatically on startup |
| `S3_USE_SSL` | false | Set to true for AWS S3 |

Place the values inside `.env` at the backend root; `pydantic-settings` loads them automatically.

## Project Structure
```
backend/
├── app/
│   ├── api/routes/ping.py        # Health check endpoint
│   ├── core/config.py            # Settings & env parsing
│   ├── db/                       # SQLAlchemy models and sessions
│   └── storage/s3.py             # MinIO/S3 helper
├── alembic/                      # Migration scripts
├── scripts/                      # Entrypoint & migration helpers
├── tests/                        # Pytest suite
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## Common Commands
- `uv sync` – install/update dependencies declared in `pyproject.toml`
- `uv run uvicorn app.main:app --reload` – start the API locally
- `uv run alembic revision --autogenerate -m "message"` – create a migration
- `uv run alembic upgrade head` – apply migrations
- `uv run pytest` – execute the backend tests

## Database Migrations
Alembic is configured to use the sync database URL exposed via `settings.DATABASE_URL_SYNC`.
1. Make your model changes.
2. Generate a migration: `uv run alembic revision --autogenerate -m "add_teacher_subject"`.
3. Apply it locally: `uv run alembic upgrade head`.
4. When running inside Docker, `scripts/init.sh` calls `scripts/migrate.sh`, so migrations run automatically on container start.

## Testing
Run the lightweight test suite (currently smoke tests) with:
```bash
uv run pytest -q
```
Add new tests under `tests/` and keep them deterministic so they run reliably in CI and Docker.

## API Surface
| Method | Path | Description |
| --- | --- | --- |
| GET | `/ping` | Health check that also verifies database connectivity and returns the PostgreSQL version. |

Future schedule-related endpoints will live under `app/api/v1` once implemented.

## Storage Notes
- `app.storage.s3.S3Storage` ensures the configured bucket exists on startup and exposes helpers to upload/download/delete objects.
- For AWS S3, set `S3_ENDPOINT_URL=https://s3.amazonaws.com` and `S3_USE_SSL=true` and provide IAM credentials through the environment.

## Troubleshooting
- **Database connection failed**: confirm PostgreSQL is reachable and credentials match `.env`.
- **Bucket errors**: remove the local MinIO volume (`docker volume rm cs-project-2025-chessnok_minio_data`) if the bucket state becomes inconsistent.
- **Dependency mismatch**: rerun `uv sync` after changing `pyproject.toml` or pulling new changes.

