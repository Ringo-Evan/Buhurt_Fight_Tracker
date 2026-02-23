# Buhurt Fight Tracker

A REST API for indexing and cataloging Buhurt (medieval armored combat) fight videos.
Built as a portfolio project demonstrating TDD/BDD mastery, clean architecture, and production deployment practices.

[![CI](https://github.com/Ringo-Evan/Buhurt_Fight_Tracker/actions/workflows/test.yml/badge.svg)](https://github.com/Ringo-Evan/Buhurt_Fight_Tracker/actions/workflows/test.yml)

**Live API**: https://buhurt-fight-tracker.azurewebsites.net
**API Docs**: https://buhurt-fight-tracker.azurewebsites.net/docs

---

## Problem

Over 20+ years of Buhurt competition history, fight videos have been scattered across personal pages and streaming platforms — often buried in long streams containing dozens of individual fights. There is no central repository for finding specific fights for reference or analysis.

This API solves that by providing structured fight records with participants, formats, and tags.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python 3.13) |
| Database | PostgreSQL (Neon serverless) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Testing | Pytest, pytest-asyncio, pytest-bdd, Testcontainers |
| CI/CD | GitHub Actions |
| Hosting | Azure App Service (B1) |

---

## Architecture

Three-layer architecture with strict separation of concerns:

```
API Layer (FastAPI)       ← Thin controllers, Pydantic validation, HTTP codes
      ↓
Service Layer             ← Business logic, domain rules, custom exceptions
      ↓
Repository Layer          ← Data access only, SQLAlchemy queries
      ↓
Database (PostgreSQL)     ← Constraints, foreign keys, unique indexes
```

Key patterns:
- UUID primary keys on all entities
- Soft delete (`is_deleted` flag) with explicit hard delete endpoints
- Eager loading to prevent N+1 queries
- UTC timestamps throughout

---

## Domain Model

```
Country → Team → Fighter
                    ↓
              Fight ← FightParticipation
                ↓
              Tag (supercategory, category, gender, custom)
               ↑
            TagType
```

---

## API Endpoints

| Resource | Endpoints |
|----------|-----------|
| Countries | `GET/POST /api/v1/countries`, `GET/PATCH/DELETE /api/v1/countries/{id}`, `PATCH /{id}/deactivate` |
| Teams | `GET/POST /api/v1/teams`, `GET/PATCH/DELETE /api/v1/teams/{id}`, `PATCH /{id}/deactivate` |
| Fighters | `GET/POST /api/v1/fighters`, `GET/PATCH/DELETE /api/v1/fighters/{id}`, `PATCH /{id}/deactivate` |
| Fights | `GET/POST /api/v1/fights`, `GET/PATCH/DELETE /api/v1/fights/{id}`, `PATCH /{id}/deactivate` |
| Fight Tags | `POST /api/v1/fights/{id}/tags`, `PATCH /{id}/tags/{tag_id}`, `PATCH /{id}/tags/{tag_id}/deactivate`, `DELETE /{id}/tags/{tag_id}` |
| Tag Types | `GET/POST /api/v1/tag-types`, `GET/PATCH/DELETE /api/v1/tag-types/{id}` |
| Health | `GET /health`, `GET /` |

Full interactive docs: `/docs` (Swagger UI) or `/redoc`

---

## Development Setup

**Prerequisites**: Python 3.13, PostgreSQL

```bash
# Clone and install
git clone https://github.com/Ringo-Evan/Buhurt_Fight_Tracker.git
cd Buhurt_Fight_Tracker
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env: set DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/buhurt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v  # requires Docker for Testcontainers
```

---

## Testing

```
Layer          | Tests  | Coverage
---------------|--------|----------
Repositories   | 76     | 98%+
Services       | 70     | 100%
API            | -      | via integration
Integration    | 75+    | real PostgreSQL
BDD Scenarios  | 98     | Gherkin specs
```

**242 unit tests, 75+ integration tests — all passing in CI.**

Tests use strict TDD discipline: one test at a time, RED → GREEN → REFACTOR.

```bash
# Unit tests only (fast, no Docker)
pytest tests/unit/ -v

# Integration tests (requires PostgreSQL)
pytest tests/integration/ -v

# Full suite with coverage
pytest --cov=app --cov-report=term
```

---

## Deployment

The API is deployed on Azure App Service (B1) with Neon PostgreSQL.

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `AZURE_WEBAPP_NAME` | Azure App Service name |
| `AZURE_WEBAPP_PUBLISH_PROFILE` | Download from Azure portal → App Service → Get publish profile |
| `DATABASE_URL` | Neon connection string: `postgresql+asyncpg://user:pass@host/db?ssl=require` |

### Azure App Service Configuration

In the portal, set these **Application Settings**:
- `DATABASE_URL` — Neon connection string (asyncpg format)
- `APP_NAME` — Buhurt Fight Tracker (optional)

Set the **Startup Command**:
```
bash startup.sh
```

### Cost Management

The app can be stopped when not needed (~$0/hr stopped vs ~$0.018/hr running):

```bash
# Start (when you need the API live)
./scripts/az_start.sh

# Stop (when done)
./scripts/az_stop.sh
```

Requires `az login` first. Edit `RESOURCE_GROUP` and `APP_NAME` in the scripts to match your Azure resources.

### Neon DATABASE_URL Format

Neon provides: `postgresql://user:pass@host/db?sslmode=require`

The app requires asyncpg format:
```
postgresql+asyncpg://user:pass@host/db?ssl=require
```

Note: `sslmode=require` → `ssl=require` (asyncpg parameter name differs from psycopg2).

---

## Project Status

| Phase | Status |
|-------|--------|
| Phase 1: Country, Team, Fighter | ✅ Complete |
| Phase 2: Fight Tracking + CI/CD | ✅ Complete |
| Phase 3: Tag System (supercategory/category/gender/custom) | ✅ Complete |
| Phase 4: Deployment | ✅ Complete |
| Phase 5: Auth (v2) | Planned |
| Phase 6: Frontend (v3) | Planned |

See `PROGRESS.md` for detailed session-by-session history.
