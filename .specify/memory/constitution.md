<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0 (MAJOR - Initial constitution ratification)

Modified principles: N/A (initial version)

Added sections:
- Core Principles (8 principles)
- Technology Stack section
- Development Workflow section
- Governance section

Removed sections: N/A

Templates requiring updates:
- ✅ plan-template.md - Aligned (Constitution Check gates match principles)
- ✅ spec-template.md - Aligned (User stories structure compatible)
- ✅ tasks-template.md - Aligned (TDD phases and user story organization match)
- ✅ phr-template.prompt.md - No changes needed

Follow-up TODOs: None
-->

# StoreLite IMS Constitution

## Core Principles

### I. Separation of Concerns (NON-NEGOTIABLE)

Backend and frontend code MUST reside in separate directories at the repository root.

**Rules:**
- `backend/` directory for all Python/FastAPI/MCP/Agent code
- `frontend/` directory for all Next.js/React code
- No cross-directory imports; communication via API contracts only
- Each directory maintains its own dependency management

**Rationale:** Clear boundaries enable independent development, testing, and deployment cycles. Teams can work in parallel without merge conflicts on unrelated code.

### II. Test-Driven Development (NON-NEGOTIABLE)

All backend code (console, FastAPI, MCP tools, agent logic) MUST follow TDD methodology.

**Rules:**
- Red-Green-Refactor cycle strictly enforced for all backend modules
- Tests MUST be written before implementation code
- Tests MUST fail before implementation begins (Red phase)
- Implementation MUST make tests pass without modifying test assertions (Green phase)
- Refactoring MUST NOT break existing tests (Refactor phase)
- Minimum test coverage: 80% for all backend code
- Test categories: unit, integration, contract (for API endpoints)

**Rationale:** TDD ensures correctness, prevents regressions, and produces maintainable code. The 80% threshold balances thoroughness with practical velocity.

### III. Phased Implementation

Features MUST be implemented in the defined 6-phase progression.

**Phases:**
1. Phase 1: Console Python + PostgreSQL (CLI inventory/billing)
2. Phase 2: FastAPI Backend (REST API over same logic)
3. Phase 3: Next.js Frontend (admin + POS pages)
4. Phase 4: FastMCP Server (MCP tools wrapping business logic)
5. Phase 5: OpenAI Agents SDK (Gemini-lite + local MCP tools)
6. Phase 6: ChatKit Frontend (agent UI integration)

**Rules:**
- Each phase MUST have passing tests before proceeding to next
- Console logic (Phase 1) forms the foundation; later phases reuse it
- FastAPI (Phase 2) wraps Phase 1 logic; does not duplicate it
- MCP tools (Phase 4) call FastAPI services; no direct DB access from tools

**Rationale:** Incremental delivery reduces risk, allows early validation, and ensures each layer is stable before building upon it.

### IV. Database-First Design

PostgreSQL (Neon) is the single source of truth for all application state.

**Rules:**
- All data models MUST be defined with explicit schemas
- Schema migrations MUST be versioned and reversible
- No in-memory state that bypasses the database for persistent data
- Snapshots of item name/price in `bill_items` for historical accuracy
- `is_active` soft-delete pattern for items; no hard deletes

**Rationale:** A single database ensures consistency across phases and prevents data synchronization issues between console, API, and agent interfaces.

### V. Contract-First APIs

All API endpoints MUST have defined contracts before implementation.

**Rules:**
- Pydantic schemas for all request/response bodies
- OpenAPI/Swagger documentation auto-generated and maintained
- Breaking changes require MAJOR version bump
- MCP tool schemas derived from type hints and docstrings
- Frontend MUST consume only documented API contracts

**Rationale:** Contract-first prevents integration surprises and enables parallel frontend/backend development.

### VI. Local-First Development

All services MUST run locally without external dependencies beyond the database.

**Rules:**
- MCP servers run via `stdio` or `localhost` HTTP only
- No hosted MCP tools (agent uses local MCP server)
- Agent model: `gemini-2.5-flash-lite` (not OpenAI models)
- Environment variables via `.env` files; never hardcode credentials
- Neon PostgreSQL connection string via `DATABASE_URL` env var

**Rationale:** Local-first enables offline development, faster iteration, and avoids vendor lock-in during the testing phase.

### VII. Simplicity Over Abstraction

Start with the simplest solution; add complexity only when justified.

**Rules:**
- No premature optimization or speculative features
- Prefer direct SQL/ORM queries over repository patterns initially
- Single `items` table serves all store types (no premature multi-tenancy)
- Agent tools call services directly; no additional abstraction layers
- YAGNI: Do not build for hypothetical future requirements

**Rationale:** Complexity has carrying costs. Simple code is easier to test, debug, and modify.

### VIII. Observability by Default

All components MUST emit structured logs and handle errors gracefully.

**Rules:**
- Structured JSON logging for all backend services
- Each API request MUST log: timestamp, endpoint, duration, status
- Errors MUST include context sufficient for debugging
- Console output MUST be human-readable; JSON for programmatic use
- Agent interactions MUST be traceable (session_id, tool calls, responses)

**Rationale:** Observability enables rapid debugging and supports future analytics features.

## Technology Stack

**Backend (Python 3.12+):**
- Project initialization: `uv` (universal virtualenv)
- Database: Neon PostgreSQL (cloud-hosted Postgres)
- ORM: SQLAlchemy 2.x with async support
- API Framework: FastAPI with Uvicorn
- Testing: pytest with pytest-asyncio
- MCP Server: FastMCP (`mcp.server.fastmcp`)
- Agent SDK: OpenAI Agents SDK with Gemini-lite model

**Frontend (Node.js/TypeScript):**
- Framework: Next.js 14+ (App Router)
- Styling: Tailwind CSS
- HTTP Client: Native fetch or Axios
- Agent UI: OpenAI ChatKit SDK (`@openai/chatkit-react`)

**Database Schema:**
- `items`: Inventory master data (id, name, category, unit, unit_price, stock_qty, is_active, timestamps)
- `bills`: Invoice headers (id, customer_name, store_name, total_amount, created_at)
- `bill_items`: Invoice line items (id, bill_id, item_id, item_name, unit_price, quantity, line_total)

**Project Structure:**
```
backend/
├── src/
│   ├── models/          # SQLAlchemy models
│   ├── services/        # Business logic
│   ├── api/             # FastAPI routers
│   ├── cli/             # Console interface (Phase 1)
│   ├── mcp_server/      # FastMCP tools (Phase 4)
│   └── agents/          # Agent definitions (Phase 5)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── pyproject.toml
└── .env.example

frontend/
├── app/
│   ├── admin/           # Inventory management
│   ├── pos/             # Billing/POS
│   └── agent/           # ChatKit agent UI
├── lib/
│   └── api.ts           # API client
├── package.json
└── .env.local.example
```

## Development Workflow

**Git Branch Strategy:**
- `main`: Stable, deployable code
- `feature/<phase>-<name>`: Feature branches per phase
- PRs require: passing tests, code review, constitution compliance check

**TDD Workflow (Backend):**
1. Write failing test(s) for the feature
2. Verify test fails (Red)
3. Implement minimal code to pass test (Green)
4. Refactor without breaking tests
5. Commit with descriptive message

**Code Review Checklist:**
- [ ] Tests written first and currently passing
- [ ] Coverage >= 80% for changed files
- [ ] No hardcoded secrets or credentials
- [ ] Structured logging present for new endpoints
- [ ] API contracts documented (Pydantic schemas)
- [ ] Frontend uses only documented API endpoints

**Testing Requirements:**
| Component | Test Type | Coverage Target |
|-----------|-----------|-----------------|
| Console (Phase 1) | Unit + Integration | 80% |
| FastAPI (Phase 2) | Unit + Contract + Integration | 80% |
| MCP Tools (Phase 4) | Unit + Integration | 80% |
| Agent (Phase 5) | Unit + Conversation | 80% |
| Frontend | Optional | N/A |

## Governance

**Constitution Authority:**
This constitution supersedes all other project practices. Any conflict between this document and other guidance resolves in favor of the constitution.

**Amendment Process:**
1. Propose change with rationale
2. Document impact on existing code/tests
3. Obtain explicit approval from project maintainer
4. Update constitution with new version number
5. Update affected templates if needed

**Versioning Policy:**
- MAJOR: Principle removals or redefinitions that break existing code
- MINOR: New principles added or existing ones materially expanded
- PATCH: Clarifications, wording improvements, non-breaking refinements

**Compliance Verification:**
- All PRs MUST include constitution compliance check in review
- CI pipeline SHOULD enforce test coverage thresholds
- Complexity additions MUST be justified in PR description

**Runtime Guidance:**
For day-to-day development decisions not covered here, consult:
- `CLAUDE.md` for agent-specific instructions
- `.specify/templates/` for spec/plan/task templates
- `README.md` for project setup and quickstart

**Version**: 1.0.0 | **Ratified**: 2025-12-07 | **Last Amended**: 2025-12-07
