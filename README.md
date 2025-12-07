# StoreLite IMS – Simple Inventory & Billing System

A minimal, extensible inventory and billing system designed for multi-phase implementation. Supports multiple store types (grocery, utilities, beauty, garments, etc.) with separate workflows for inventory management and billing/POS operations.

## Quick Start

### Prerequisites
- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **PostgreSQL** (via Neon cloud)
- `uv` (Python virtual environment manager)
- Git

### Setup (All Phases)

1. Clone the repository:
   ```bash
   git clone https://github.com/rrizwan98/StoreLite-IMS.git
   cd StoreLite-IMS
   ```

2. Copy environment templates:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.local.example frontend/.env.local
   ```

3. Update `.env` files with your Neon PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://user:password@neon-host/storelite
   ```

## Architecture

### Directory Structure
```
StoreLite-IMS/
├── backend/                    # Python backend (all phases)
│   ├── src/
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   ├── api/               # FastAPI routers (Phase 2+)
│   │   ├── cli/               # Console interface (Phase 1)
│   │   ├── mcp_server/        # MCP tools (Phase 4+)
│   │   └── agents/            # Agent definitions (Phase 5+)
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/                   # Next.js frontend (Phase 3+)
│   ├── app/
│   │   ├── admin/             # Inventory management
│   │   ├── pos/               # Billing/POS screen
│   │   └── agent/             # ChatKit UI (Phase 6+)
│   ├── lib/
│   │   └── api.ts             # API client
│   ├── package.json
│   └── .env.local.example
│
├── docs/                       # Project documentation
│   ├── phases/                # Phase-specific docs
│   └── architecture/          # Architecture decisions
│
├── .specify/                   # Spec-driven development templates
│   ├── memory/
│   │   └── constitution.md    # Project constitution
│   └── templates/
│
└── README.md
```

## Implementation Phases

### Phase 1: Console Python + PostgreSQL (Foundation)
**Goal**: CLI-based inventory management and billing system

**Features**:
- Add/update/list items in PostgreSQL
- Search items by name or category
- Create bills with line items
- Automatic stock deduction
- Invoice printing to console/file

**Tech Stack**:
- Python 3.12+
- PostgreSQL (Neon)
- SQLAlchemy or psycopg2
- Click/Typer for CLI

**Testing**: Unit + Integration tests (80% coverage)

---

### Phase 2: FastAPI Backend (REST API)
**Goal**: Wrap Phase 1 logic in a production REST API

**Features**:
- `GET /items` – List items with filters (name, category)
- `POST /items` – Create new item
- `PUT /items/{id}` – Update item (price, stock)
- `GET /items/{id}` – Get single item
- `POST /bills` – Create invoice with line items
- `GET /bills/{id}` – Fetch bill details
- `GET /bills` – List bills with filters
- Auto-generated Swagger/OpenAPI docs

**Tech Stack**:
- FastAPI + Uvicorn
- SQLAlchemy 2.x (ORM)
- Pydantic (request/response schemas)
- pytest for testing

**Testing**: Unit + Contract + Integration tests (80% coverage)

---

### Phase 3: Next.js Frontend (Web UI)
**Goal**: Web-based inventory management and POS interface

**Pages**:
- `/admin` – Inventory management
  - Add new items (form)
  - Search/list items (table)
  - Edit price/stock (inline or dialog)
  - Soft delete items

- `/pos` – Billing/POS interface
  - Search items (dropdown/autocomplete)
  - Add items to cart
  - Adjust quantities
  - Display totals
  - Generate bill (calls FastAPI)
  - Print invoice

**Tech Stack**:
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- React hooks for state management

---

### Phase 4: FastMCP Server (MCP Tools)
**Goal**: Expose business logic as MCP tools for agents

**Tools**:
- `inventory_add_item` – Create item
- `inventory_list_items` – List/search items
- `inventory_update_item` – Update item
- `billing_create_bill` – Create invoice
- `billing_get_bill` – Fetch bill details

**Tech Stack**:
- FastMCP (Python)
- Runs locally via `stdio` or `http://localhost:<port>`
- Reuses services from Phase 2

---

### Phase 5: OpenAI Agents SDK (Agent Logic)
**Goal**: Natural language interface for inventory/billing operations

**Capabilities**:
- Add inventory via chat: *"Add 10kg sugar at 160 per kg"*
- Create bills via chat: *"Bill for Ali: 2kg sugar, 1 shampoo"*
- Query stock: *"Show low stock items in beauty"*
- Generate reports: *"Top 10 items this month"*

**Tech Stack**:
- OpenAI Agents SDK
- Gemini 2.5 Flash Lite (LLM)
- Local MCP server (Phase 4)
- FastAPI `/agent/chat` endpoint

**Testing**: Unit + Conversation simulation tests (80% coverage)

---

### Phase 6: ChatKit Frontend (Agent UI)
**Goal**: Ready-made chat interface for agent

**Features**:
- Chat-based inventory/billing
- OpenAI ChatKit SDK (React)
- Self-hosted backend mode
- Minimal custom UI

**Tech Stack**:
- Next.js 14+ (App Router)
- `@openai/chatkit-react`
- Connects to `/agent/chat` endpoint

---

## Constitution & Core Principles

This project follows a **Spec-Driven Development (SDD)** methodology with explicit governance documented in `.specify/memory/constitution.md`.

### Key Principles (NON-NEGOTIABLE):

1. **Separation of Concerns** – Backend/frontend in separate directories
2. **Test-Driven Development** – Red-Green-Refactor with 80% coverage requirement

### Other Core Principles:

3. **Phased Implementation** – 6-phase progression; each phase builds on previous
4. **Database-First Design** – PostgreSQL as single source of truth
5. **Contract-First APIs** – Pydantic schemas, OpenAPI docs
6. **Local-First Development** – All services run locally (stdio/localhost)
7. **Simplicity Over Abstraction** – YAGNI; no speculative features
8. **Observability by Default** – Structured logging, error context

---

## Testing Strategy

All **backend code** follows **Test-Driven Development (TDD)**:

| Phase | Component | Test Types | Coverage Target |
|-------|-----------|-----------|-----------------|
| 1 | Console | Unit + Integration | 80% |
| 2 | FastAPI | Unit + Contract + Integration | 80% |
| 4 | MCP Tools | Unit + Integration | 80% |
| 5 | Agent | Unit + Conversation | 80% |
| 3, 6 | Frontend | Optional | N/A |

### Run Tests

**Backend** (Python):
```bash
cd backend
pytest                    # All tests
pytest -v --cov          # With coverage report
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
```

**Frontend** (Optional):
```bash
cd frontend
npm test
```

---

## Development Workflow

### TDD Workflow (Backend)

1. Write failing test(s)
2. Verify test fails (Red phase)
3. Implement minimal code to pass test (Green phase)
4. Refactor without breaking tests (Refactor phase)
5. Commit with descriptive message

### Git Branch Strategy

- `main` – Stable, deployable code
- `feature/<phase>-<name>` – Feature branches per phase
  - e.g., `feature/phase1-inventory-management`
  - e.g., `feature/phase2-fastapi-setup`

### Code Review Checklist

- [ ] Tests written first and currently passing
- [ ] Coverage >= 80% for changed backend files
- [ ] No hardcoded secrets or credentials
- [ ] Structured logging for new endpoints
- [ ] API contracts documented (Pydantic schemas)
- [ ] Frontend uses only documented API endpoints

---

## Environment Variables

### Backend (`.env`)
```env
DATABASE_URL=postgresql://user:password@neon-host/storelite
DEBUG=false
LOG_LEVEL=info
PYTHONUNBUFFERED=1
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CHATKIT_API_URL=http://localhost:8000/chatkit
```

---

## Running the Application

### Phase 1: Console Only

```bash
cd backend
uv run python -m src.cli.main
```

### Phase 2: FastAPI Backend

```bash
cd backend
uv run uvicorn src.api.main:app --reload
# Open: http://localhost:8000/docs (Swagger UI)
```

### Phase 3: Full Stack (Backend + Next.js Frontend)

Terminal 1 (Backend):
```bash
cd backend
uv run uvicorn src.api.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
# Open: http://localhost:3000
```

### Phase 5: Add Agent Endpoint

Terminal 1 (Backend with agent):
```bash
cd backend
uv run uvicorn src.api.main:app --reload
# Endpoint: POST /agent/chat
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
# Open: http://localhost:3000/agent
```

---

## Useful Commands

**Backend Setup**:
```bash
cd backend
uv sync                  # Install dependencies
uv run pytest           # Run tests
uv run python -m src.cli.main  # Phase 1 console
```

**Frontend Setup**:
```bash
cd frontend
npm install
npm run dev
npm test
```

**Database**:
```bash
# Create tables (Phase 1 or 2)
cd backend
uv run python -m src.cli.setup_db

# View schema
psql $DATABASE_URL -c "\dt"
```

---

## Project Documentation

- **Constitution**: `.specify/memory/constitution.md` – Core principles and governance
- **Phases**: `docs/phases/` – Detailed phase specifications
- **Architecture**: `docs/architecture/` – Technical decisions (ADRs)
- **Spec**: `specs/<feature>/spec.md` – Feature specifications (auto-generated)
- **Plans**: `specs/<feature>/plan.md` – Implementation plans
- **Tasks**: `specs/<feature>/tasks.md` – Breakdown of work items

---

## Deployment

### Production Deployment Checklist

- [ ] All tests passing (80%+ coverage)
- [ ] Constitution compliance verified
- [ ] Security review (no hardcoded secrets)
- [ ] Database migrations applied
- [ ] Environment variables set
- [ ] Logging configured
- [ ] Monitoring/alerts configured

---

## License

[TBD - Add your license here]

## Contact

Project Owner: [Your Name/Organization]

For questions or contributions, open an issue or contact the maintainers.

---

**Last Updated**: 2025-12-07
**Project Version**: 1.0.0 (Constitution Ratified)
