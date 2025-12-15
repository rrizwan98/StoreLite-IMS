# Implementation Plan: OpenAI Agents SDK Integration with MCP Server

**Branch**: `005-openai-agents-p5` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)

---

## Summary

Phase 5 implements an OpenAI Agents SDK orchestration layer that connects to the existing FastMCP server (Phase 4) and FastAPI backend (Phase 2) to enable natural language conversations for inventory and billing operations. Users interact via a `/agent/chat` endpoint that accepts natural language messages, which are processed by an intelligent agent that dynamically discovers and calls MCP tools, maintains multi-turn conversation context (5-message rolling window), and streams responses in real-time via Server-Sent Events (SSE). Critical clarification: Session memory is persisted in PostgreSQL (not in-memory only) for resilience and audit trails.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: OpenAI Agents SDK, FastAPI, psycopg2/SQLAlchemy (PostgreSQL driver), httpx (for MCP HTTP client)
**Storage**: PostgreSQL (agent sessions + conversation history table)
**Testing**: pytest (unit, integration, contract tests)
**Target Platform**: Linux server (FastAPI backend running locally)
**Project Type**: Web application (backend API + agent orchestration)
**Performance Goals**: 3s average response time; 1s for clarification questions
**Constraints**: No authentication in Phase 5; in-memory context (last 5 exchanges) + persistent DB; MCP HTTP client must connect to localhost:8001
**Scale/Scope**: 10 concurrent sessions; 5 MCP tools available; < 500 requests/min during testing

---

## Constitution Check

**GATE: Separation of Concerns** ✅ PASS
- Agent code lives in `backend/app/agents/` (Python/FastAPI backend)
- No frontend code in backend; `/agent/chat` endpoint communicates via HTTP
- Frontend (Phase 6 ChatKit UI) will communicate via `/agent/chat` endpoint, never importing backend code

**GATE: Test-Driven Development** ✅ PASS
- TDD workflow applies: Red → Green → Refactor
- Unit tests for agent logic, MCP client, session management
- Integration tests for `/agent/chat` endpoint
- Target: 80%+ code coverage

**GATE: Phased Implementation** ✅ PASS
- Phase 5 builds on Phase 2 (FastAPI) and Phase 4 (FastMCP server)
- Reuses existing PostgreSQL database and FastAPI app structure
- Does not create new database; adds `agent_sessions` table

**GATE: Session Persistence Clarification** ⚠️ DESIGN DECISION
- **Decision**: PostgreSQL-backed session storage (not in-memory only as spec stated)
- **Rationale**: Production resilience, audit trails, multi-instance support
- **Implication**: New `agent_sessions` table required; session retrieval adds ~50ms latency (acceptable for 3s SLA)

---

## Project Structure

### Documentation (this feature)

```text
specs/005-openai-agents-p5/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions (OpenAI SDK, SSE, PostgreSQL session design)
├── data-model.md        # Phase 1: Agent session schema, database migrations
├── quickstart.md        # Phase 1: Developer setup guide for Phase 5
├── contracts/           # Phase 1: OpenAPI spec for /agent/chat endpoint
│   └── agent-api.yaml   # POST /agent/chat, GET /agent/chat/stream
└── checklists/
    └── requirements.md  # Quality validation checklist (already complete)
```

### Source Code (backend)

```text
backend/
├── app/
│   ├── agents/                          # NEW for Phase 5
│   │   ├── __init__.py
│   │   ├── agent.py                     # OpenAI Agent SDK orchestration
│   │   ├── tools_client.py              # MCP HTTP client for tool discovery/calling
│   │   ├── session_manager.py           # PostgreSQL session persistence
│   │   └── confirmation_flow.py         # Inline yes/no confirmation logic
│   │
│   ├── api/
│   │   ├── routes_agent.py              # NEW: POST /agent/chat, GET /agent/chat/stream routes
│   │   └── [existing routes]
│   │
│   ├── models.py                        # UPDATED: Add AgentSession SQLAlchemy model
│   ├── database.py                      # UPDATED: Add agent_sessions table migration
│   └── main.py                          # UPDATED: Include /agent routes
│
├── migrations/                          # NEW: Alembic migrations for agent_sessions table
│   ├── env.py
│   └── versions/
│       └── 005_add_agent_sessions_table.py
│
├── tests/mcp/
│   ├── agent/                           # NEW: Agent-specific tests
│   │   ├── test_agent_orchestration.py  # Unit tests for OpenAI agent logic
│   │   ├── test_mcp_client.py           # Unit tests for MCP HTTP client
│   │   ├── test_session_manager.py      # Unit tests for PostgreSQL persistence
│   │   ├── test_confirmation_flow.py    # Unit tests for yes/no confirmation
│   │   └── integration/
│   │       ├── test_agent_chat_endpoint.py  # Integration test for /agent/chat
│   │       └── test_mcp_tool_calling.py     # Integration test with real MCP server
│   │
│   └── [existing test structure]
│
└── requirements.txt                     # UPDATED: Add openai-agents-sdk, httpx
```

---

## Technical Design Decisions

### 1. Agent Session Persistence (PostgreSQL)

**Decision**: Use PostgreSQL `agent_sessions` table to persist:
- `session_id` (UUID primary key)
- `user_id` (optional, for future auth)
- `created_at`, `updated_at` (timestamps)
- `conversation_history` (JSONB column: list of recent 5 messages)
- `metadata` (JSONB: user context, store_name, etc.)

**Why**: Enables multi-instance deployments, audit trails, session recovery across server restarts.

**Schema**:
```sql
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    conversation_history JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_session_id (session_id)
);
```

### 2. MCP Tool Discovery & HTTP Client

**Decision**: Implement HTTP client that:
- Calls FastMCP server at startup: `GET http://localhost:8001/tools` (or equivalent endpoint)
- Parses available tools and their schemas
- Caches tool list in memory (with 5-minute TTL)
- For each tool call: `POST http://localhost:8001/call` with tool name + arguments

**Why**: Dynamic discovery prevents hardcoding; HTTP transport is standard; caching avoids repeated discovery.

**Schema** (sample MCP response):
```json
{
  "tools": [
    {"name": "inventory_add_item", "description": "...", "schema": {...}},
    {"name": "inventory_list_items", "description": "...", "schema": {...}},
    ...
  ]
}
```

### 3. Session Context: Recent 5 Messages

**Decision**: For each session, retain only the last 5 user-agent message pairs in `conversation_history` JSONB.

**Why**: Reduces API cost (fewer tokens to OpenAI), keeps context focused, prevents token overflow.

**Structure**:
```json
[
  {"role": "user", "content": "Add 10kg sugar", "timestamp": "2025-12-09T10:00:00Z"},
  {"role": "assistant", "content": "Added 10kg sugar...", "timestamp": "2025-12-09T10:00:02Z"},
  ...
]
```

### 4. Confirmation Flow: Inline Yes/No

**Decision**: Agent detects destructive actions (bill creation, item deletion) and pauses:
- Agent response: "Are you sure you want to create this bill for $320? Reply 'yes' to confirm."
- User must send follow-up message with "yes" or "no"
- On "yes": Agent calls MCP tool; on "no": Agent cancels action

**Why**: Prevents accidental operations; conversational UX; no special syntax needed.

### 5. Response Streaming: Server-Sent Events (SSE)

**Decision**: Implement two endpoint modes:
- `POST /agent/chat` (non-streaming): Return full response as JSON (for testing, simple clients)
- `GET /agent/chat/stream` (streaming): Return SSE stream with real-time chunks

**SSE Message Format**:
```
event: token
data: {"chunk": "I've", "type": "text"}

event: token
data: {"chunk": " added", "type": "text"}

event: done
data: {"session_id": "abc123", "total_tokens": 42}
```

**Why**: SSE is simple (HTTP, no WebSocket), standard for real-time; supports polling clients.

### 6. Environment Variables

**Decision**: `.env` file stores:
```
OPENAI_API_KEY=sk-...
MCP_SERVER_URL=http://localhost:8001
DATABASE_URL=postgresql://user:pass@localhost/storelite_ims
AGENT_MODEL=gpt-4o-mini  # or gemini-2.5-flash-lite if using Gemini
SESSION_CONTEXT_SIZE=5
MCP_TOOL_CACHE_TTL_SECONDS=300
```

---

## Data Model

### New Entities

**AgentSession**
- `id` (UUID, PK)
- `session_id` (TEXT, unique, user-provided or generated)
- `conversation_history` (JSONB: list of {role, content, timestamp})
- `metadata` (JSONB: user context, store_name, timestamp)
- `created_at`, `updated_at` (TIMESTAMPTZ)

**Related**: Uses existing `items`, `bills`, `bill_items` tables via MCP tool calls (no direct agent access to DB).

---

## API Contracts

### Endpoint 1: POST /agent/chat (Non-streaming)

**Request**:
```json
{
  "session_id": "user-123-session-abc",  // optional; generated if not provided
  "message": "Add 10kg sugar at 160 per kg under grocery"
}
```

**Response** (200 OK):
```json
{
  "session_id": "user-123-session-abc",
  "response": "I've added 10kg Sugar at 160 per kg to Grocery category.",
  "status": "success",
  "tool_calls": [
    {
      "tool": "inventory_add_item",
      "arguments": {"name": "Sugar", "category": "Grocery", "unit": "kg", "unit_price": 160, "stock_qty": 10},
      "result": {"item_id": 42, "status": "created"}
    }
  ]
}
```

**Response** (200 OK, Confirmation Needed):
```json
{
  "session_id": "user-123-session-abc",
  "response": "Are you sure you want to create a bill for Ali: 2kg sugar + 1 shampoo (Total: $820)? Reply 'yes' to confirm.",
  "status": "pending_confirmation",
  "pending_action": "billing_create_bill"
}
```

### Endpoint 2: GET /agent/chat/stream

**Query Parameters**:
```
?session_id=user-123-session-abc&message=Add+10kg+sugar
```

**Response** (200 OK, Content-Type: text/event-stream):
```
event: token
data: {"chunk": "I've", "type": "text"}

event: token
data: {"chunk": " added", "type": "text"}

event: token
data: {"chunk": " 10kg Sugar", "type": "text"}

event: tool_call
data: {"tool": "inventory_add_item", "arguments": {...}}

event: done
data: {"session_id": "user-123-session-abc", "total_tokens": 45}
```

---

## Integration with Existing Systems

### Phase 2 (FastAPI Backend)
- `/agent/chat` endpoint added to existing FastAPI app
- Uses existing FastAPI app instance, database session
- Shares PostgreSQL database

### Phase 4 (FastMCP Server)
- Agent communicates with FastMCP server via HTTP (localhost:8001)
- Discovers tools dynamically at startup
- Calls tools with arguments; parses responses

### Phase 3 (Next.js Frontend) — Future (Phase 6)
- Next.js will call `/agent/chat` or `/agent/chat/stream` endpoint
- ChatKit UI will wrap SSE streaming

---

## Error Handling Strategy

| Scenario | Agent Behavior |
|----------|---|
| MCP server unreachable | Return error: "I'm unable to reach the system. Please try again." |
| MCP tool call fails | Return error: "I couldn't complete that action: [MCP error]. Please try again." |
| Invalid user request | Ask clarifying questions: "I need more details: what item? what quantity?" |
| Ambiguous item name | List options: "Did you mean: Item A or Item B?" |
| Stock insufficient | Warn: "Only 3kg available. Would you like to add 3kg instead?" |
| Empty message | Prompt: "How can I help with inventory or billing?" |
| Invalid confirmation response | Retry: "Please reply 'yes' or 'no'." |

---

## Testing Strategy (TDD)

### Phase 0: Research → research.md
- Validate OpenAI Agents SDK capabilities
- Confirm SSE streaming support in FastAPI
- Verify PostgreSQL JSONB performance for session history

### Phase 1: Design → data-model.md, contracts/
- Design `agent_sessions` table schema
- Define `/agent/chat` OpenAPI contract
- Define MCP HTTP client interface

### Phase 2 (Red): Write Failing Tests
**Unit Tests**:
```python
def test_agent_discovers_mcp_tools():
    agent = OpenAIAgent()
    tools = agent.discover_tools()
    assert len(tools) == 5
    assert "inventory_add_item" in [t["name"] for t in tools]

def test_session_manager_persists_and_retrieves():
    session = SessionManager.create_session()
    SessionManager.save_session(session)
    retrieved = SessionManager.get_session(session.session_id)
    assert retrieved.session_id == session.session_id

def test_agent_asks_confirmation_for_bill_creation():
    user_message = "Create a bill for Ali: 2kg sugar and 1 shampoo"
    response = agent.chat(session_id="test", message=user_message)
    assert response["status"] == "pending_confirmation"
    assert "Are you sure" in response["response"]

def test_confirmation_flow_yes():
    # Previous state: pending_confirmation for bill creation
    response = agent.chat(session_id="test", message="yes")
    assert response["status"] == "success"
    assert "Bill created" in response["response"]

def test_mcp_client_calls_tool():
    client = MCPClient("http://localhost:8001")
    result = client.call_tool("inventory_add_item", {"name": "Sugar", ...})
    assert result["item_id"] == 42
```

**Integration Tests**:
```python
def test_agent_chat_endpoint_end_to_end():
    client = TestClient(app)
    response = client.post("/agent/chat", json={
        "session_id": "test-session",
        "message": "Add 10kg flour at 50 per kg to grocery"
    })
    assert response.status_code == 200
    assert response.json()["response"] != ""
    # Verify DB: check agent_sessions table for saved conversation

def test_agent_chat_streaming_sse():
    client = TestClient(app)
    response = client.get("/agent/chat/stream?session_id=test&message=List+items")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = parse_sse_events(response.content)
    assert len(events) > 0
    assert events[-1]["event"] == "done"

def test_mcp_tool_calling_with_real_server():
    # Assumes FastMCP server running on localhost:8001
    response = client.post("/agent/chat", json={
        "message": "Add 20kg rice at 100 per kg to grocery"
    })
    assert response.status_code == 200
    # Verify PostgreSQL items table has new row
    item = db.query(Item).filter(Item.name == "Rice").first()
    assert item.stock_qty == 20
```

### Phase 3 (Green): Implement Minimum Code
- Implement `OpenAIAgent` class with tool discovery
- Implement `SessionManager` for PostgreSQL persistence
- Implement `MCPClient` for HTTP communication
- Implement `/agent/chat` endpoint

### Phase 4 (Refactor): Clean Up
- Extract confirmation logic to separate module
- Add comprehensive error handling
- Optimize session retrieval (caching, indexes)

---

## Phase Breakdown

### Phase 0 (Research)
- [ ] Research OpenAI Agents SDK capabilities, limits, cost model
- [ ] Research FastAPI SSE streaming patterns
- [ ] Research PostgreSQL JSONB performance for session history
- [ ] Validate MCP server HTTP endpoint interface
- [ ] Output: `research.md`

### Phase 1 (Design)
- [ ] Create database migration for `agent_sessions` table
- [ ] Design agent initialization and tool discovery logic
- [ ] Design session management and conversation history retention
- [ ] Design confirmation flow state machine
- [ ] Design `/agent/chat` and `/agent/chat/stream` endpoints
- [ ] Output: `data-model.md`, `contracts/`, `quickstart.md`

### Phase 2 (Implementation & Testing - Red/Green/Refactor)
- [ ] Implement and test MCP HTTP client
- [ ] Implement and test session manager (PostgreSQL)
- [ ] Implement and test OpenAI agent orchestration
- [ ] Implement and test confirmation flow
- [ ] Implement `/agent/chat` endpoint (non-streaming)
- [ ] Implement `/agent/chat/stream` endpoint (SSE)
- [ ] Write comprehensive unit and integration tests
- [ ] Target: 80%+ code coverage

### Phase 3 (Task Generation - `/sp.tasks`)
- Generated as separate step after plan approval
- Breaks Phase 2 into atomic, testable tasks

---

## Success Criteria (from Specification)

| SC | Metric | How Measured |
|----|--------|---|
| SC-001 | 90% accuracy on well-formed requests | Manual test cases (20+ scenarios) |
| SC-002 | 3s average response time | Load test with 100 requests |
| SC-003 | 1s clarification response time | Timeout test for out-of-domain requests |
| SC-004 | Persistence correctness | Post-request DB verification |
| SC-005 | Multi-turn conversations | 5+ back-and-forth test flow |
| SC-006 | 10 concurrent sessions | Concurrent client load test |

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|---|
| MCP server unavailable | Medium | Blocks agent operation | Add retry logic; graceful degradation message |
| OpenAI API rate limit | Medium | Pauses agent | Implement exponential backoff; queue requests |
| PostgreSQL session table grows unbounded | Low | Performance degradation | Add retention policy (e.g., delete sessions > 30 days old) |
| SSE client disconnects mid-stream | Medium | Incomplete response | Client-side retry; session recovery on next message |
| Confirmation timeout | Low | User frustration | Set 5-minute timeout; remind user to confirm |

---

## Environment Setup

**`.env` file** (required for Phase 5):
```
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-... (from OpenAI API dashboard)
OPENAI_MODEL=gpt-4o-mini

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8001

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/storelite_ims

# Agent Configuration
SESSION_CONTEXT_SIZE=5
MCP_TOOL_CACHE_TTL_SECONDS=300
AGENT_CONFIRMATION_TIMEOUT_SECONDS=300
```

---

## Next Steps

1. **Review & Approve Plan**: User reviews and approves this plan
2. **Generate Research** (`/sp.plan` Phase 0): Generate `research.md` with technology decisions
3. **Generate Design** (`/sp.plan` Phase 1): Generate `data-model.md`, `contracts/`, `quickstart.md`
4. **Generate Tasks** (`/sp.tasks`): Break implementation into atomic test-first tasks
5. **Implementation**: Execute tasks following TDD (Red → Green → Refactor)
6. **PR & Merge**: Create PR, obtain review, merge to main

