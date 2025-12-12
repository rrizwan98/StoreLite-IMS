# Implementation Plan: FastMCP Server for Inventory & Billing

**Branch**: `004-fastmcp-server-p4` | **Date**: 2025-12-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-fastmcp-server-p4/spec.md`

---

## Summary

Phase 4 implements a Model Context Protocol (MCP) server that wraps existing FastAPI inventory and billing logic, exposing it as MCP tools for AI agents and local development tools (Claude Code, custom agents).

**Primary Requirement**: Convert 7 existing REST endpoints into 7 MCP tools with identical business logic and data validation.

**Technical Approach**:
1. Reuse existing FastAPI service layer (`services.inventory`, `services.billing`) without modification
2. Create thin MCP adapter layer (`mcp_server/tools_*.py`) that calls services
3. Support both stdio (local/Claude Code) and HTTP localhost transports
4. Maintain API consistency: pessimistic locking, soft deletes, error schema, pagination defaults

---

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastMCP, SQLAlchemy 2.x, PostgreSQL, FastAPI (Phase 2 backend)
**Storage**: PostgreSQL (existing from Phase 2)
**Testing**: pytest with pytest-asyncio, pydantic models
**Target Platform**: Linux server (local development)
**Project Type**: Backend microservice (MCP server)
**Performance Goals**: <500ms per tool call for typical operations
**Constraints**: No breaking changes to FastAPI endpoints; 100% code reuse from Phase 2
**Scale/Scope**: 7 MCP tools, ~500-800 LOC in MCP adapter, 0 new database tables

---

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

| Principle | Requirement | Status | Notes |
|-----------|------------|--------|-------|
| **I. Separation of Concerns** | MCP tools in separate `mcp_server/` folder, reuse service layer only | ✅ PASS | No direct DB access from MCP; services act as adapter |
| **II. Test-Driven Development** | 80% test coverage for MCP tools; unit + integration tests | ✅ PASS | Plan includes unit tests for each tool, integration tests with DB |
| **III. Phased Implementation** | Phase 4 builds on Phase 2 (FastAPI); doesn't modify Phase 2 | ✅ PASS | Soft dependency: reuses Phase 2 services, no changes required |
| **IV. Database-First Design** | Use soft deletes, snapshots; no modifications to schema | ✅ PASS | Clarification Q1 confirms soft delete strategy |
| **V. Contract-First APIs** | MCP tool schemas auto-generated from Pydantic; documented | ✅ PASS | FastMCP auto-generates schemas from type hints |
| **VI. Local-First Development** | MCP server runs locally (stdio + HTTP); .env config only | ✅ PASS | No cloud deps; transports support local dev |
| **VII. Simplicity Over Abstraction** | Minimal adapter layer; direct service reuse | ✅ PASS | No new patterns; existing service logic untouched |
| **VIII. Observability by Default** | Structured logging for tool calls; duration tracking | ✅ PASS | Plan includes logging at tool entry/exit |

**Result**: ✅ **ALL GATES PASS** – No violations or deviations from constitution.

---

## Project Structure

### Documentation (this feature)

```
specs/004-fastmcp-server-p4/
├── spec.md                      # Feature specification (COMPLETED)
├── CLARIFICATION_REPORT.md      # Clarification session (COMPLETED)
├── plan.md                       # This file (IN PROGRESS)
├── research.md                   # Phase 0 output (TO-DO)
├── data-model.md                 # Phase 1 output (TO-DO)
├── quickstart.md                 # Phase 1 output (TO-DO)
├── contracts/                    # Phase 1 output directory (TO-DO)
│   ├── inventory.json            # OpenAPI schema for inventory tools
│   └── billing.json              # OpenAPI schema for billing tools
├── checklists/
│   └── requirements.md           # Quality validation (COMPLETED)
└── tasks.md                      # Phase 2 output - /sp.tasks (TO-DO)
```

### Source Code (backend)

```
backend/
├── app/
│   ├── mcp_server/               # NEW: MCP server implementation
│   │   ├── __init__.py
│   │   ├── server.py             # FastMCP server entry point
│   │   ├── tools_inventory.py    # Inventory tools (4 tools)
│   │   ├── tools_billing.py      # Billing tools (3 tools)
│   │   └── schemas.py            # Pydantic schemas for tool I/O
│   ├── services/                 # EXISTING: Reused as-is
│   │   ├── inventory.py
│   │   └── billing.py
│   ├── models/                   # EXISTING: SQLAlchemy models
│   ├── routers/                  # EXISTING: FastAPI endpoints (unchanged)
│   ├── database.py               # EXISTING: Session factory
│   └── main.py                   # EXISTING: FastAPI app
│
└── tests/
    ├── mcp/                      # NEW: MCP-specific tests
    │   ├── unit/
    │   │   ├── test_tools_inventory.py
    │   │   └── test_tools_billing.py
    │   └── integration/
    │       ├── test_mcp_inventory_e2e.py
    │       └── test_mcp_billing_e2e.py
    ├── integration/              # EXISTING: Updated for consistency tests
    │   └── test_fastapi_vs_mcp.py  # NEW: Consistency validation
    └── contract/                 # EXISTING: OpenAPI schema tests
        └── test_mcp_schemas.py   # NEW: MCP tool schemas
```

**Structure Decision**: Phase 4 is a backend microservice (MCP server). Follows existing backend layout by adding `mcp_server/` folder as a sibling to `services/`. No frontend changes required in Phase 4; frontend integration deferred to Phase 6.

---

## Implementation Strategy

### Phase 0: Research & Dependency Analysis

**Outputs**: `research.md` with findings on:

1. **FastMCP best practices** for type hints, error handling, and documentation
2. **MCP transport configuration** (stdio vs HTTP) for local development
3. **Pydantic integration** with FastMCP tool schemas
4. **Transaction handling** in MCP context (pessimistic locking implementation)
5. **Error schema standardization** (FR-009 requirements)

---

### Phase 1: Design & Contracts

#### 1.1 Data Model (`data-model.md`)

**No changes to database schema** – MCP tools operate on existing tables:

Tables (from Phase 2):
- `items`: id, name, category, unit, unit_price, stock_qty, is_active, timestamps
- `bills`: id, customer_name, store_name, total_amount, created_at
- `bill_items`: id, bill_id, item_id, item_name, unit_price, quantity, line_total

**MCP Tool Schemas** (Pydantic models):
- Input/Output models for each tool
- Error response schema: `{"error": "<CODE>", "message": "<text>", "details": {...}}`
- Pagination schema: default page size 20, max 100

#### 1.2 Tool Contracts (`contracts/`)

**OpenAPI-style schemas** auto-generated by FastMCP from Pydantic models.

**7 MCP Tools**:
- `inventory_add_item` – Create item
- `inventory_update_item` – Update item
- `inventory_delete_item` – Deactivate item
- `inventory_list_items` – List/search items (paginated)
- `billing_create_bill` – Create bill with stock validation & locking
- `billing_list_bills` – List bills (paginated, date-filterable)
- `billing_get_bill` – Retrieve bill with all line items

#### 1.3 Quickstart (`quickstart.md`)

**Local MCP Server Setup**:
```bash
# Start MCP server (stdio transport)
python backend/app/mcp_server/server.py

# Test with curl (HTTP transport)
curl -X POST http://localhost:3000/tools/inventory/add_item \
  -H "Content-Type: application/json" \
  -d '{"name": "Sugar", "category": "Grocery", ...}'
```

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Service layer changes break MCP tools | Low | High | Write integration tests comparing FastAPI vs MCP results |
| Pessimistic locking causes timeouts | Medium | High | Test concurrent bill creation; document transaction limits |
| Error schema inconsistency | Low | Medium | Define error codes once in `schemas.py`; use everywhere |
| Transport configuration issues | Medium | Low | Test both stdio and HTTP with example agents |
| Pagination defaults mismatch | Low | Low | Document defaults in quickstart; validate with integration tests |

---

## Success Metrics

✅ **Phase 0 (Research)**: research.md completed with 0 unknowns
✅ **Phase 1 (Design)**: 4 artifacts (data-model.md, contracts/*.json, quickstart.md, agent context)
✅ **Phase 2 (Development)**: All tasks completed, 80% test coverage
✅ **Phase 3 (Validation)**:
- All 7 MCP tools callable via stdio + HTTP
- Consistency tests pass (MCP output = FastAPI output)
- Error responses follow standard JSON schema
- Pagination defaults work (20/100)
- Soft delete works (item marked inactive)
- Bill immutability enforced
- Pessimistic locking prevents over-allocation

---

## Complexity Tracking

No violations to constitution. The design is simple:
- Reuse existing service layer → minimal new code
- Thin MCP adapter layer → ~500-800 LOC
- No new database tables or schema changes
- No new architectural patterns
- Follows Phase 2 patterns (tests, structure, logging)

---

## Next Steps

1. **Phase 0**: `/sp.plan` generates `research.md` with all unknowns resolved
2. **Phase 1**: `/sp.plan` generates `data-model.md`, `contracts/`, `quickstart.md`
3. **Phase 2**: `/sp.tasks` generates `tasks.md` with all development tasks
4. **Begin**: Follow TDD (Red-Green-Refactor) for each task

---

**Status**: ✅ Plan COMPLETE – Ready for Phase 0 Research

**Branch**: `004-fastmcp-server-p4` | **Date**: 2025-12-08
