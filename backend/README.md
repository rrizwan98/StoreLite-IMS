# FastAPI Backend - Inventory Management System (Phase 2)

RESTful API backend for the Inventory Management System, built with FastAPI and PostgreSQL.

## Quick Start

1. Install dependencies: `pip install -e .`
2. Create `.env` file with database configuration
3. Run FastAPI: `uvicorn app.main:app --reload`
4. Access API docs: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app initialization
│   ├── database.py          # Database connection and session management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── exceptions.py        # Custom exception classes
│   └── routers/             # API endpoint routers
│       ├── __init__.py
│       ├── inventory.py     # Inventory endpoints
│       └── billing.py       # Billing endpoints
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── contract/            # API contract tests
│   └── conftest.py          # Pytest configuration and fixtures
└── README.md                # This file
```

## Testing

Run tests: `pytest tests/`
Run with coverage: `pytest --cov=app tests/`

## API Documentation

Interactive API docs available at `/docs` (Swagger UI) after starting the app.
