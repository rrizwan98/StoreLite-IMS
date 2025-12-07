# Implementation Plan: Console-Based Inventory & Billing System (Phase 1)

**Branch**: `001-console-ims-p1` | **Date**: 2025-12-07 | **Spec**: `/specs/001-console-ims-p1/spec.md`
**Input**: Feature specification from `/specs/001-console-ims-p1/spec.md`

## Summary

Phase 1 delivers a console-based Python inventory and billing system with PostgreSQL persistence. Users can add/search/update products, create invoices with automatic stock management, and print receipts. The system uses searchable dropdowns for categories/units, validates all input before persistence, and maintains strict ACID transactions for bill operations. This forms the foundation for later FastAPI wrapping and agent integration.

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: SQLAlchemy ORM for database access (abstracted via db.py module)

**Storage**: PostgreSQL (Neon or self-hosted) - DATABASE_URL via environment variable

**Testing**: pytest with pytest-asyncio for integration tests

**Target Platform**: CLI/console-based; Linux/macOS/Windows with Python 3.12+

**Project Type**: Single monolithic console application (foundation for Phase 2 FastAPI wrapping)

**Performance Goals**: Add item <2s, search/update <1s, bill creation <5 min (user-paced)

**Constraints**: <100MB memory footprint; ACID transactions for bill operations; single-user/session scope

**Scale/Scope**: Initial release for single store; 1000+ product inventory supported; no authentication

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Separation of Concerns
- **Status**: PASS with note
- **Justification**: Phase 1 is single console app; NOT yet split into backend/frontend. Constitution allows Phase 1 as monolithic. Phase 2 will extract business logic into FastAPI service and separate console CLI.

### ✅ Test-Driven Development
- **Status**: PASS
- **Requirement**: Minimum 80% test coverage; Red-Green-Refactor cycle enforced
- **Implementation**: pytest suite with unit tests (models, services), integration tests (database operations), contract tests (CLI output)

### ✅ Phased Implementation
- **Status**: PASS
- **Requirement**: Phase 1 = Console + PostgreSQL foundation
- **Implementation**: All Phase 1 logic (inventory, billing) implemented in reusable services that Phase 2 (FastAPI) will wrap without duplication

### ✅ Database-First Design
- **Status**: PASS
- **Requirement**: PostgreSQL as single source of truth; soft deletes; snapshots in bill_items
- **Implementation**: Schema defined in schema.sql; is_active flag for soft deletes; price/name snapshots in bill_items for historical accuracy

### ✅ Contract-First APIs
- **Status**: N/A for Phase 1 (console only)
- **Justification**: No HTTP APIs in Phase 1. Phase 2 will define Pydantic schemas for all endpoints before implementation.

### ✅ Local-First Development
- **Status**: PASS
- **Requirement**: DATABASE_URL via .env; no hardcoded credentials
- **Implementation**: .env loading with example .env.example; connection string from environment

### ✅ Simplicity Over Abstraction
- **Status**: PASS
- **Requirement**: No premature optimization or multi-tenancy
- **Implementation**: Single items table; direct SQL/ORM queries; no repository pattern until Phase 2 justifies it

### ✅ Observability by Default
- **Status**: PASS
- **Requirement**: Structured logging; graceful error handling; user-friendly messages
- **Implementation**: Print-based logging for console (JSON for API phase); all errors caught with context before user sees them

## Key Decisions and Rationale

### Decision 1: Monolithic Console App (Phase 1 Only)
**Options Considered:**
1. Monolithic console app with embedded database logic
2. Separate CLI layer + business logic service from day 1

**Selected**: Option 1 (Monolithic)

**Rationale**: Phase 1 scope is small enough to keep simple; duplication is acceptable here. Phase 2 will refactor to separate layers via FastAPI without losing logic. Faster time to working prototype. No premature abstraction (Principle VII).

**Tradeoffs**: Console and Phase 2 service will have duplicate code initially. Refactoring cost in Phase 2 is acceptable vs complexity now.

---

### Decision 2: Database Library (SQLAlchemy ORM)
**Options Considered:**
1. Raw psycopg2 (lower-level, minimal dependencies)
2. SQLAlchemy ORM (abstraction layer, reusable in Phase 2)

**Selected**: SQLAlchemy ORM for this plan (abstracted via db.py module)

**Rationale**: ORM models become reusable in Phase 2 FastAPI without rewriting. Reduces SQL injection surface area. Aligns with Constitution Principle I (clear separation if we hide DB logic behind service layer).

**Tradeoffs**: Slightly higher initial learning curve. Additional dependency (mitigated by single dependency file).

**Implementation**: Abstraction via `db.py` module; console code calls service functions, services use SQLAlchemy.

---

### Decision 3: Searchable Dropdown Implementation
**Options Considered:**
1. Free-form text entry (rejected - data quality issues per spec)
2. Predefined list, user selects by number (basic but no partial matching)
3. Searchable dropdown (filter suggestions as user types, select exact match)

**Selected**: Option 3 (Searchable dropdown)

**Rationale**: Spec explicitly requires "Searchable dropdown with suggestions"; "user can only select from filtered list". Prevents invalid categories/units; ensures data consistency. Matches modern UX expectations.

**Implementation**: Simple loop: display suggestions as user types, validate final selection.

---

### Decision 4: Bill Atomicity (All-or-Nothing Stock Decrement)
**Options Considered:**
1. Decrement stock item-by-item during bill creation (risky if one fails)
2. Validate all stock first, then decrement all together (atomic)
3. Soft transactions with rollback (overengineered for Phase 1)

**Selected**: Option 2 (Batch validate, then atomic decrement)

**Rationale**: Spec requirement FR-014: "atomically decrement inventory stock". Prevents partial bill updates corrupting inventory. Simple with PostgreSQL transactions (BEGIN/COMMIT).

**Implementation**: Database transaction at service layer; all decrements in single COMMIT.

---

### Decision 5: CLI Input Validation & Error Handling
**Options Considered:**
1. Validate at input, re-prompt in same context (spec requirement FR-001a)
2. Return to main menu on invalid input (breaks user context)
3. Silent ignore + retry (confusing)

**Selected**: Option 1 (re-prompt in context)

**Rationale**: Spec explicitly requires: "Invalid choice. Please select from the menu above. ... remains in current menu context". Reduces user frustration; maintains workflow.

**Implementation**: Menu loop with explicit validation; on error, print message and re-prompt same menu.

---

## Project Structure

### Documentation (this feature)

```
specs/001-console-ims-p1/
├── plan.md                         # This file (architecture & decisions)
├── research.md                     # Phase 0 output (resolved unknowns)
├── data-model.md                   # Phase 1 output (entities & schema)
├── contracts/                      # Phase 1 output (NOTE: N/A for console; prepared for Phase 2)
├── quickstart.md                   # Phase 1 output (local dev setup)
└── tasks.md                        # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root) - Phase 1 Structure

```
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── item.py                  # Item ORM model & validation
│   │   ├── bill.py                  # Bill & BillItem ORM models
│   │   └── schemas.py               # Pydantic schemas (for Phase 2 API)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── inventory_service.py     # Add, search, list, update items
│   │   ├── billing_service.py       # Create bill, calculate totals, print invoice
│   │   └── database.py              # DB connection, transaction management
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py                  # Main menu loop & entry point
│   │   ├── inventory_menu.py        # Manage Inventory submenu
│   │   ├── billing_menu.py          # Create New Bill submenu
│   │   └── ui_utils.py              # Shared UI helpers (dropdowns, error messages)
│   │
│   └── db.py                        # Abstraction: connection pool, session mgmt
│
├── tests/
│   ├── unit/
│   │   ├── test_inventory_service.py
│   │   ├── test_billing_service.py
│   │   ├── test_models.py
│   │   └── test_ui_utils.py
│   │
│   ├── integration/
│   │   ├── test_inventory_flow.py
│   │   ├── test_billing_flow.py
│   │   └── conftest.py
│   │
│   └── contract/
│       └── test_cli_output.py
│
├── pyproject.toml                   # Python dependencies (uv)
├── .env.example                     # Template for DATABASE_URL
└── schema.sql                       # DDL for items, bills, bill_items tables
```

**Structure Decision**: Single backend monolithic console app (Option 1 from template) for Phase 1. Frontend directory reserved for Phase 3 (Next.js). Phase 2 will extract business logic into backend/api/ without moving or duplicating services.

## Complexity Tracking

> No violations of Constitution principles detected; no justification required.

---

## Phase 0: Research (To Be Generated)

**Status**: No research needed — all Technical Context resolved.

---

## Phase 1: Design & Contracts (To Be Generated)

**Outputs**:
1. `data-model.md` — Entity definitions, validation rules, relationships
2. `quickstart.md` — Local dev setup, example .env, how to run

**Key Entities**:

**Item**: id (auto), name (text), category (Grocery|Garments|Beauty|Utilities|Other), unit (kg|g|liter|ml|piece|box|pack|other), unit_price (≥0), stock_qty (≥0), is_active (boolean), timestamps

**Bill**: id (auto), customer_name (optional), store_name (optional), total_amount, created_at

**BillItem**: id (auto), bill_id (FK), item_id (FK), item_name (snapshot), unit_price (snapshot), quantity, line_total

---

## Success Criteria for Phase 1

1. ✅ All three user stories independently testable and working
2. ✅ Inventory operations (add/list/search/update) validated & persisted
3. ✅ Bill creation calculates totals, validates stock, updates inventory atomically
4. ✅ Console UI clear with helpful error messages (no stack traces to user)
5. ✅ All code passes 80%+ test coverage
6. ✅ Data persists in PostgreSQL across app restarts
7. ✅ Invalid input rejected before DB (validation in application layer)

---

## Next Steps

1. Finalize Phase 1 design documents (research.md, data-model.md, quickstart.md)
2. Generate tasks.md via /sp.tasks command
3. Begin Red-Green-Refactor cycle on first task
