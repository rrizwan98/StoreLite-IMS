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

**What this means:** Keep backend and frontend code completely separate. They talk to each other through API contracts only, never by importing code directly.

**Simple Rules:**
- **Backend folder**: Put all Python, FastAPI, and AI/Agent code here
- **Frontend folder**: Put all web app (Next.js/React) code here
- **No shortcuts**: Never import code from one folder into the other
- **Own dependencies**: Each folder manages its own packages separately

**Why this matters:** When code is separated, teams can work on the backend and frontend at the same time without stepping on each other's toes. It's easier to test, deploy, and fix problems when things are organized this way.

### II. Test-Driven Development (NON-NEGOTIABLE)

**What this means:** Write tests BEFORE you write the real code. This catches bugs early and makes your code more reliable.

**The 3-Step Process (Red → Green → Refactor):**

1. **RED** - Write a test that describes what you want the code to do (it will fail because the code doesn't exist yet)
2. **GREEN** - Write the simplest code to make the test pass
3. **REFACTOR** - Clean up the code without breaking the test

**Simple Rules:**
- Always write the test first, code second
- Aim for 80% or more of your code to be covered by tests (this means 80% of your code is tested)
- Don't skip this step to go faster - it actually saves time later

**Example:**
```python
# RED: Write test first (will fail)
def test_add_item():
    item = add_item("Sugar", "Grocery", 150.00)
    assert item.name == "Sugar"

# GREEN: Write code to make it pass
def add_item(name, category, price):
    return Item(name=name, category=category, unit_price=price)

# REFACTOR: Make it cleaner (test still passes)
def add_item(name, category, price):
    validate_inputs(name, category, price)
    item = Item(name=name, category=category, unit_price=price)
    save_to_database(item)
    return item
```

**Why this matters:** Tests are like a safety net. They catch mistakes before your users do. 80% coverage means most of your code is tested - not perfect, but good enough to catch real problems.

### III. Phased Implementation

**What this means:** Build the system in steps, one piece at a time. Each piece is tested before moving to the next.

**The 6 Phases (Build in Order):**
1. **Phase 1**: Command-line app (Python) + Database (PostgreSQL)
   - ✅ COMPLETED: Users can add products, search, create bills, print receipts
   - ✅ 121 tests passing

2. **Phase 2**: Web API (FastAPI) - connects to Phase 1 code
   - 🚀 CURRENT: Building REST API endpoints to let apps talk to Phase 1

3. **Phase 3**: Web Dashboard (Next.js) - pretty interface for people to use

4. **Phase 4**: AI Tools Server - lets AI assistants use the system

5. **Phase 5**: AI Agents - smart assistants that help users

6. **Phase 6**: ChatBot Interface - talk to AI like a chatbot

**Simple Rules:**
- Each phase must work and be tested before starting the next
- Don't repeat code - Phase 2 reuses Phase 1's code, doesn't rewrite it
- Each phase builds on the previous one
- All tests must pass before moving forward

**Why this matters:** Building step-by-step is safer and faster. You catch mistakes early. Each phase is proven to work before the next team member starts building on top of it.

### IV. Database-First Design

**What this means:** The database is the "one source of truth". Everything important gets saved there, not just in memory.

**Simple Rules:**
- **Central database**: All data lives in PostgreSQL (our database)
- **Clear structure**: Data is organized in clearly defined tables (items, bills, bill_items)
- **Snapshots**: When you sell something, save a copy of its name and price in that sale record (for history)
- **Soft deletes**: Don't erase items - just mark them as "inactive" so you can still see what was sold
- **Reversible changes**: Any change to the database structure can be undone if needed

**Example:**
```
Items Table:
- ID: 1, Name: "Sugar", Price: 150.00, Stock: 100, Active: Yes
- ID: 2, Name: "Rice", Price: 50.00, Stock: 0, Active: No  ← marked inactive

Bills Table:
- Bill ID: 101, Customer: "John", Total: 300.00

Bill Items Table:
- Item from Bill 101: Name: "Sugar", Quantity: 2, Price: 150.00 ← snapshot saved
  (Even if the actual Sugar price changed later, the bill record stays the same)
```

**Why this matters:** Having one place where all data lives means nobody has to guess what the real information is. It also means you can see the history of what was sold and when, even if prices changed later.

### V. Contract-First APIs

**What this means:** Decide exactly what data goes in and comes out of each API endpoint BEFORE you write the code. This prevents surprises and lets frontend and backend teams work at the same time.

**Simple Rules:**
- **Contracts first**: Write down what each API endpoint expects and returns
- **Documentation**: Auto-generate pretty docs (Swagger) so everyone sees the same contract
- **Structured data**: Use clear formats for requests and responses
- **No surprises**: If you change an API in a breaking way, bump the version number

**Example:**
```
API: POST /items (Add a new item)

What goes in (Request):
{
  "name": "Sugar",
  "category": "Grocery",
  "price": 150.00,
  "stock_qty": 100
}

What comes back (Response - Success):
{
  "id": 1,
  "name": "Sugar",
  "category": "Grocery",
  "price": "150.00",
  "stock_qty": 100,
  "created_at": "2025-12-08T10:30:00Z"
}

What comes back (Response - Error):
{
  "error": "Validation failed",
  "fields": {
    "price": "Price must be a positive number"
  }
}
```

**Why this matters:** When frontend and backend agree on the contract, they can work independently. Frontend doesn't have to wait for backend, and vice versa. Also, when new team members join, they know exactly how to use the API.

### VI. Local-First Development

**What this means:** Everything runs on your computer (or a local server), not in the cloud during development. This is faster and cheaper.

**Simple Rules:**
- **Run locally**: AI tools, API server, all run on your machine during development
- **Database connection**: Use `DATABASE_URL` in a `.env` file (hidden file with secrets)
- **No hardcoded secrets**: Never put passwords or connection strings in your code
- **Simple setup**: Everything should work on a laptop with just a few commands

**Example Setup:**
```bash
# Create .env file (never commit this!)
echo "DATABASE_URL=postgresql://user:pass@localhost/ims_db" > .env

# Start the app
python backend/main.py

# AI tools run locally too
python backend/mcp_server.py
```

**Why this matters:** Local development is way faster - no waiting for cloud servers. You can work offline. You save money. And if something breaks, it only breaks on your machine, not for everyone.

### VII. Simplicity Over Abstraction

**What this means:** Write code that works today, not code that might be useful someday. Simple is better than clever.

**Simple Rules:**
- **Don't guess the future**: Build for what you need now, not what you might need later
- **Write it simply**: If a simple solution works, use it - don't add fancy patterns
- **Use one items table**: Don't create separate tables for different store types unless you really need to
- **Direct database access**: Query the database directly when it makes sense, don't create extra layers

**What NOT to do:**
```python
# ❌ Too complicated (might be needed someday?)
class AbstractRepositoryPattern:
    def get_by_category(self, filter_strategy, cache_engine):
        # ... 50 lines of code

# ✅ Simple and clear (does the job)
def get_items_by_category(category):
    return db.session.query(Item).filter(Item.category == category).all()
```

**Why this matters:** Simple code is easier to read, test, and fix. Complicated code hides bugs. When you actually need the fancy stuff later, you'll know exactly what you need (not just guessing).

### VIII. Observability by Default

**What this means:** Keep detailed records of what your app is doing. When something breaks, the records help you fix it fast.

**Simple Rules:**
- **Log everything important**: Record when API requests come in, how long they take, and what the result was
- **Smart errors**: When something goes wrong, log enough information to figure out why
- **Readable logs**: When looking at logs, you should understand what happened
- **Track AI interactions**: When AI tools run, record what they did and what they said

**Example Logs:**
```
[2025-12-08 10:30:45] POST /items - Status: 201 - Duration: 45ms - Item "Sugar" created
[2025-12-08 10:31:22] GET /items - Status: 200 - Duration: 12ms - Returned 25 items
[2025-12-08 10:32:10] POST /bills - Status: 400 - Duration: 89ms - Error: Insufficient stock for item ID 5
```

**Why this matters:** Logs are like a security camera for your app. When something goes wrong, you can watch the recording and see exactly what happened. It makes fixing bugs 10x faster.

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

**Version**: 1.1.0 | **Ratified**: 2025-12-07 | **Last Amended**: 2025-12-08
