# Implementation Plan: FastAPI Backend (Phase 2) - IMS REST API

**Branch**: `002-fastapi-backend-p2` | **Date**: 2025-12-08 | **Spec**: [specs/002-fastapi-backend-p2/spec.md](spec.md)
**Input**: Feature specification from `/specs/002-fastapi-backend-p2/spec.md`
**Status**: Ready for Phase 0 Research → Phase 1 Design → Phase 2 Implementation

## Summary

Phase 2 converts the Phase 1 console-based IMS (already complete) into a production-ready FastAPI REST API backend. **Key advantage: Phase 1 business logic (inventory management, billing calculations, stock updates) is already implemented and tested.** Phase 2 focuses on wrapping this logic with a FastAPI layer, SQLAlchemy ORM integration, and comprehensive API contracts.

**Primary Requirement**: Build FastAPI endpoints that expose Phase 1 functionality with:
- ✅ Inventory CRUD: `/items` (POST, GET, GET/{id}, PUT, DELETE)
- ✅ Billing workflows: `/bills` (POST, GET, GET/{id})
- ✅ Stock management: Atomic updates during bill creation
- ✅ Error handling: Custom JSON format with field-level validation
- ✅ Decimal precision: Strings for prices, numbers for quantities
- ✅ PostgreSQL persistence: Using SQLAlchemy ORM

**Technical Approach**:
1. Create SQLAlchemy ORM models (Item, Bill, BillItem) mapping to existing Phase 1 schema
2. Create Pydantic request/response schemas with validation rules from spec
3. Build FastAPI routers wrapping Phase 1 service layer (no logic duplication)
4. Implement error handlers for custom response formats (422 validation, 400 business logic)
5. Write 60+ pytest tests covering all endpoints + edge cases
6. Verify all endpoints pass Postman testing without errors

## Technical Context

**Language/Version**: Python 3.12+ (aligns with Phase 1)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.x, Pydantic v2, Uvicorn
**Storage**: PostgreSQL (Neon) via `DATABASE_URL` from Phase 1
**Testing**: pytest with pytest-asyncio (async endpoint testing)
**Target Platform**: Linux server (localhost:8000 during dev, deployable to cloud)
**Project Type**: Web API (backend only; Phase 3 adds Next.js frontend)
**Performance Goals**: <200ms for GET /items (list), <500ms for POST /bills (create) with 1000+ items
**Constraints**: No authentication (Phase 2 MVP); no pagination (return all results); atomic transactions for bill creation
**Scale/Scope**: Small dataset (<10k items, <100k bills in Phase 2); ready to scale in Phase 3+
**Key Dependency**: Phase 1 console code (already complete) provides business logic foundation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Gate 1: Separation of Concerns ✅ PASS
- **Requirement**: Backend in `/backend` directory; frontend in `/frontend` directory
- **Status**: Phase 1 code in `/backend`; Phase 2 will add FastAPI to `/backend/app` (no frontend yet)
- **Verification**: ✅ No cross-directory imports; communication via API contracts only

### Gate 2: Test-Driven Development ✅ PASS
- **Requirement**: Tests written BEFORE implementation; minimum 80% coverage
- **Status**: Phase 2 plan includes 60+ pytest tests (exceeds 80% coverage target); red-green-refactor enforced
- **Verification**: ✅ Test-first approach mandatory for all 32 FRs

### Gate 3: Phased Implementation ✅ PASS
- **Requirement**: Phase 2 must NOT duplicate Phase 1 logic
- **Status**: Plan explicitly wraps Phase 1 service layer; FastAPI routers call existing inventory/billing services
- **Verification**: ✅ No code duplication; reuses Phase 1 logic

### Gate 4: Database-First Design ✅ PASS
- **Requirement**: PostgreSQL is single source of truth; schema versioned
- **Status**: Using existing Phase 1 schema (items, bills, bill_items); SQLAlchemy ORM provides type-safe access
- **Verification**: ✅ Soft-delete via `is_active`; snapshots in `bill_items` for historical accuracy

### Gate 5: Contract-First APIs ✅ PASS
- **Requirement**: Pydantic schemas + OpenAPI/Swagger documentation
- **Status**: Pydantic schemas defined for all request/response bodies; Swagger auto-generated at `/docs`
- **Verification**: ✅ 32 FRs map to explicit API contracts

### Gate 6: Local-First Development ✅ PASS
- **Requirement**: All services run locally; `.env` for credentials
- **Status**: FastAPI runs on localhost:8000; PostgreSQL via `DATABASE_URL` env var
- **Verification**: ✅ No external dependencies beyond Phase 1 PostgreSQL

### Gate 7: Simplicity Over Abstraction ✅ PASS
- **Requirement**: Direct ORM queries; no premature patterns
- **Status**: Using SQLAlchemy directly; no repository pattern; single items table for all store types
- **Verification**: ✅ Minimal code; maximum clarity

### Gate 8: Observability by Default ✅ PASS
- **Requirement**: Structured logging; error context
- **Status**: Structured logging planned for all endpoints; error responses include field-level details
- **Verification**: ✅ Each request logs: endpoint, duration, status

**Overall**: ✅ **ALL GATES PASS** - Phase 2 plan fully aligns with constitution

---

## Project Structure

### Documentation (this feature)

```text
specs/002-fastapi-backend-p2/
├── spec.md                      # Feature specification ✅
├── checklists/
│   └── requirements.md          # Quality validation ✅
├── plan.md                      # This file (you are here)
├── research.md                  # Phase 0 output (to be created)
├── data-model.md                # Phase 1 output (to be created)
├── quickstart.md                # Phase 1 output (to be created)
└── contracts/                   # Phase 1 output (to be created)
    ├── openapi.json             # OpenAPI schema
    ├── inventory.md             # /items endpoints
    └── billing.md               # /bills endpoints
```

### Source Code (repository root) - Option 2: Web API

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app initialization, routers
│   ├── database.py              # SQLAlchemy engine, session, async support
│   ├── models.py                # Item, Bill, BillItem SQLAlchemy models
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── exceptions.py            # Custom exceptions, error handlers
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── inventory.py         # GET/POST /items, GET /items/{id}, PUT, DELETE
│   │   └── billing.py           # GET/POST /bills, GET /bills/{id}
│   ├── services/                # (from Phase 1, reused)
│   │   ├── inventory.py         # add_item, list_items, update_item, delete_item
│   │   └── billing.py           # create_bill, get_bill, calculate_totals
│   ├── cli/                     # (from Phase 1, kept for reference)
│   └── models/                  # (from Phase 1, reused if using SQLAlchemy)
│
├── tests/
│   ├── conftest.py              # pytest fixtures, test database
│   ├── unit/
│   │   ├── test_schemas.py      # Pydantic validation tests
│   │   ├── test_models.py       # SQLAlchemy model tests
│   │   └── test_services.py     # Service layer tests (from Phase 1)
│   ├── integration/
│   │   ├── test_inventory_flow.py    # Full item CRUD flow
│   │   └── test_billing_flow.py      # Bill creation → stock deduction flow
│   └── contract/
│       ├── test_inventory_endpoints.py   # /items endpoints
│       ├── test_billing_endpoints.py     # /bills endpoints
│       └── test_error_responses.py       # Custom error format validation
│
├── pyproject.toml               # Python project config (dependencies, scripts)
├── requirements.txt             # Python dependencies (FastAPI, SQLAlchemy, pytest, etc.)
├── .env.example                 # Example: DATABASE_URL, APP_ENV
├── .env                         # Local (git-ignored): actual DATABASE_URL, etc.
└── README.md                    # Setup & quickstart instructions

frontend/                         # (Phase 3, not part of Phase 2)
└── [to be created in Phase 3]
```

**Structure Decision**: Web API (Option 2) - Backend only
- **Rationale**: Phase 2 focuses on REST API backend; Phase 3 adds Next.js frontend
- **Separation**: Backend in `/backend/app`; tests in `/backend/tests`
- **Reuse**: Phase 1 business logic (services, models) reused as-is
- **Key directories**:
  - `/backend/app/routers/`: FastAPI endpoint handlers
  - `/backend/app/schemas.py`: Pydantic request/response validation
  - `/backend/tests/contract/`: Endpoint-level tests for Postman compatibility
  - `/backend/tests/integration/`: Full workflow tests (e.g., create bill → verify stock deduction)

---

## Complexity Tracking

✅ **No Constitution Violations** - All architecture decisions fully justified within constitution guidelines

| Aspect | Justification |
|--------|---------------|
| Reusing Phase 1 logic | Constitution Principle III: "FastAPI wraps Phase 1 logic; does not duplicate it" |
| SQLAlchemy ORM | Constitution Principle IV: "Database-first design with explicit schemas" |
| Custom error handlers | Constitution Principle V: "Contract-first APIs with defined response formats" |
| 60+ tests required | Constitution Principle II: "Minimum 80% coverage" (60+ tests → >90% coverage) |

---

## Phase 0: Research Agenda

**Status**: No NEEDS CLARIFICATION markers in spec or technical context. Research minimal.

**Research Tasks** (if any unknowns emerge):
- ✅ FastAPI async patterns with SQLAlchemy → Well-documented; use `sessionmaker(class_=AsyncSession)`
- ✅ Pydantic v2 custom validators → Well-documented; use `@field_validator`
- ✅ SQLAlchemy decimal types → Use `Numeric(precision=12, scale=2)` and `Numeric(12, 3)`
- ✅ Custom FastAPI error handlers → Use `@app.exception_handler` for custom formats

**Output**: research.md (minimal - mostly linking to official docs)

---

## Phase 1: Design & Contracts

### 1a. Data Model (data-model.md)

**Entities**:
- **Item** (from Phase 1 schema):
  - Fields: id, name, category, unit, unit_price (NUMERIC 12,2), stock_qty (NUMERIC 12,3), is_active, created_at, updated_at
  - Validation: unit_price >= 0, stock_qty >= 0
  - State: active (is_active=true) vs inactive (is_active=false)

- **Bill** (from Phase 1 schema):
  - Fields: id, customer_name (optional), store_name (optional), total_amount (NUMERIC 12,2), created_at
  - Relationships: 1:N with BillItem

- **BillItem** (from Phase 1 schema):
  - Fields: id, bill_id (FK), item_id (FK), item_name (snapshot), unit_price (snapshot), quantity (NUMERIC 12,3), line_total (NUMERIC 12,2)
  - Calculation: line_total = unit_price × quantity

### 1b. API Contracts (contracts/)

**Contract 1: /items (Inventory)**
- `POST /items`: Create item (201 status, return created item with auto-generated id)
- `GET /items`: List active items (optional filters: name, category)
- `GET /items/{id}`: Get single item (200 or 404)
- `PUT /items/{id}`: Update item (200 with updated data or 404)
- `DELETE /items/{id}`: Soft-delete item (204 or 404)

**Contract 2: /bills (Billing)**
- `POST /bills`: Create bill with items array (201, return bill with line items and calculated totals)
- `GET /bills`: List all bills (optional filters: start_date, end_date; no pagination - return all)
- `GET /bills/{id}`: Get single bill with all line items (200 or 404)

**Error Responses**:
- 422 Validation: `{"error": "Validation failed", "fields": {"field_name": "error message"}}`
- 400 Business Logic: `{"error": "Insufficient stock"}`
- 404 Not Found: `{"error": "Item not found"}`

**Response Formats**:
- Prices/totals as strings: `"unit_price": "160.50"`
- Quantities as numbers: `"quantity": 2.5`

### 1c. Quickstart (quickstart.md)

Steps to set up and run Phase 2:
1. Clone repo and enter `/backend` directory
2. Install dependencies: `pip install -r requirements.txt`
3. Set `DATABASE_URL` in `.env` (from Phase 1)
4. Run FastAPI: `uvicorn app.main:app --reload --port 8000`
5. Visit Swagger: http://localhost:8000/docs
6. Test in Postman: Import OpenAPI schema or manually create requests
7. Run tests: `pytest tests/ -v --cov=app --cov-report=term-missing`

---

## Phase 2: Implementation (Next Phase - Not Part of /sp.plan Output)

After `/sp.plan` completes, use `/sp.tasks` to break down into testable tasks and `/sp.implement` to execute red-green-refactor cycle.

**Implementation Sequence** (following constitution TDD):

1. **Red Phase**: Write failing tests for all 32 FRs
   - Unit tests: Pydantic validation, SQLAlchemy models
   - Contract tests: Endpoint request/response schemas
   - Integration tests: Full workflows (item creation → bill creation → stock deduction)

2. **Green Phase**: Implement minimal code to pass tests
   - SQLAlchemy models mapping to Phase 1 schema
   - Pydantic schemas for request/response validation
   - FastAPI routers wrapping Phase 1 service calls
   - Error handlers for custom response formats

3. **Refactor Phase**: Improve code quality without breaking tests
   - Extract common patterns
   - Optimize database queries
   - Improve logging and error messages

4. **Verification**: All 60+ tests pass; all endpoints work in Postman; no errors

---

## Success Criteria (Ready for Implementation)

**Phase 2 is complete when:**
- ✅ All 32 FRs implemented
- ✅ 60+ pytest tests written and passing (>90% coverage)
- ✅ All endpoints testable and working in Postman (zero errors)
- ✅ Custom error response format implemented (422 validation, 400 business logic)
- ✅ Decimal precision preserved (strings for prices, numbers for quantities)
- ✅ Stock atomically decremented when bill is created
- ✅ Swagger/OpenAPI docs generated at `/docs`
- ✅ All constitution principles verified

---

## Next Steps

1. **Approve Plan**: Review this plan and confirm ready for Phase 0-1
2. **Run Phase 0-1**: Execute `/sp.plan --continue` to generate:
   - `research.md` (Phase 0 findings)
   - `data-model.md` (Phase 1 entity definitions)
   - `contracts/openapi.json` (Phase 1 API specification)
   - `quickstart.md` (Phase 1 setup guide)
3. **Create Tasks**: Run `/sp.tasks` to break down into 30-50 testable tasks
4. **Implement**: Run `/sp.implement` to execute TDD red-green-refactor
5. **Test in Postman**: Verify all endpoints work without errors

---

**Plan Status**: ✅ **READY FOR IMPLEMENTATION**
**Branch**: `002-fastapi-backend-p2` (checked out)
**Estimated Velocity**: Fast (Phase 1 logic already done; Phase 2 = wrapping + tests)
