# Tasks: OpenAI Agents SDK Integration with MCP Server (Phase 5)

**Branch**: `005-openai-agents-p5` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Input**: Design documents from `/specs/005-openai-agents-p5/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓
**Approach**: Test-Driven Development (Red → Green → Refactor); TDD tasks included
**Total Tasks**: 38 | **Estimated Duration**: 2-3 weeks (1-2 sprints)

---

## Task Organization & Dependencies

**By User Story Priority**:
- **P1 Stories (MVP)**: US1 (Add Inventory via NL), US2 (Create Bill via NL) - **Must complete both for MVP**
- **P2 Stories**: US3 (Query Inventory via NL), US4 (Update Stock via NL) - **Secondary features**
- **Parallel Opportunities**:
  - T004-T009: Setup phase (all parallelizable)
  - T010-T019: Foundational components (all parallelizable)
  - T020-T033: US1 & US2 (can run in parallel after foundational phase)
  - T034-T038: Polish & cross-cutting (sequential after stories complete)

**Dependency Graph**:
```
Setup (T001-T003)
  ↓
Foundational (T004-T019)
  ├─ US1 (T020-T025) ────┐
  ├─ US2 (T026-T031) ────┤ (Can run in parallel)
  ├─ US3 (T032-T034) ────┤
  └─ US4 (T035-T037) ────┘
  ↓
Polish (T038)
```

**MVP Scope** (minimum viable): Setup + Foundational + US1 + US2
**Full Scope**: Setup + Foundational + US1 + US2 + US3 + US4 + Polish

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and .env/dependency configuration

- [X] T001 Create `backend/app/agents/` directory structure with `__init__.py` files
- [X] T002 [P] Update `backend/requirements.txt` with: `openai-agents-sdk`, `httpx`, `python-dotenv`, `psycopg2-binary`
- [X] T003 [P] Create `.env.example` template with `OPENAI_API_KEY`, `MCP_SERVER_URL`, `DATABASE_URL`, `SESSION_CONTEXT_SIZE`
- [X] T004 [P] Add `.env` to `.gitignore` (never commit secrets)

**Checkpoint**: Project structure ready; dependencies installable

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core agent infrastructure that must be complete before user stories begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Setup

- [X] T005 Create Alembic database migration file `backend/migrations/versions/005_add_agent_sessions_table.py`
- [X] T006 [P] Add `AgentSession` SQLAlchemy model to `backend/app/models.py` with fields: id (UUID), session_id (TEXT unique), conversation_history (JSON), metadata (JSON), created_at, updated_at
- [X] T007 Run migration: `alembic upgrade head` to create `agent_sessions` table in PostgreSQL

### MCP HTTP Client (Foundation for All Stories)

- [X] T008 [P] Create `backend/app/agents/tools_client.py` with `MCPClient` class:
  - `__init__(base_url="http://localhost:8001")`
  - `discover_tools()` → calls `GET http://localhost:8001/mcp/tools`, returns list of tool schemas
  - `call_tool(tool_name, arguments)` → calls `POST http://localhost:8001/mcp/call`, returns result
  - Includes error handling (connection timeout, tool not found, tool execution failure)
  - Includes 5-minute cache for discovered tools (TTL)

- [ ] T009 [P] Create unit tests for MCP client in `backend/tests/mcp/agent/test_mcp_client.py`:
  - Test: `discover_tools()` returns tool list from HTTP response
  - Test: `call_tool()` sends correct request and parses response
  - Test: Timeout when MCP server unreachable (should raise with helpful message)
  - Test: Tool execution failure handled gracefully (return error dict)
  - Test: Tool cache works (second call within 5 min returns cached result)

**Write tests first (RED); implement MCPClient (GREEN); refactor (ensure tests pass)**

### Session Manager (PostgreSQL Persistence)

- [X] T010 [P] Create `backend/app/agents/session_manager.py` with `SessionManager` class:
  - `create_session(session_id=None, metadata={})` → creates new row in agent_sessions, returns session object
  - `get_session(session_id)` → retrieves session from DB, returns conversation history (list of recent 5 exchanges)
  - `save_session(session_id, conversation_history, metadata)` → updates conversation_history JSONB in DB
  - `delete_old_sessions(days=30)` → deletes sessions older than N days (for cleanup)

- [ ] T011 [P] Create unit tests for session manager in `backend/tests/mcp/agent/test_session_manager.py`:
  - Test: `create_session()` inserts row into agent_sessions and returns session
  - Test: `get_session()` retrieves conversation history correctly
  - Test: `save_session()` updates conversation_history JSONB
  - Test: `delete_old_sessions()` removes old sessions
  - Test: Conversation history is limited to 5 most recent exchanges

**Write tests first (RED); implement SessionManager (GREEN); refactor**

### OpenAI Agent Orchestration (Foundation)

- [X] T012 [P] Create `backend/app/agents/agent.py` with `OpenAIAgent` class:
  - `__init__(api_key, model="gpt-4o-mini", tools_client=None, session_manager=None)`
  - `discover_and_register_tools()` → calls `tools_client.discover_tools()`, registers with OpenAI Agents SDK
  - `process_message(session_id, user_message)` → loads session history, calls OpenAI agent with message + history, returns response
  - Handles tool calling: when agent calls a tool, intercepts, calls `tools_client.call_tool()`, returns result to agent
  - Error handling: MCP failures, invalid inputs, timeouts

- [ ] T013 [P] Create unit tests for agent in `backend/tests/mcp/agent/test_agent_orchestration.py`:
  - Test: Agent discovers tools from MCPClient
  - Test: Agent processes simple request (e.g., "Add 10kg sugar")
  - Test: Agent calls correct MCP tool with correct arguments
  - Test: Agent returns natural language response
  - Test: Agent handles MCP tool errors gracefully (returns user-friendly message)
  - Test: Agent conversation history (from SessionManager) is used in context

**Write tests first (RED); implement OpenAIAgent (GREEN); refactor**

### Confirmation Flow (Foundation)

- [X] T014 [P] Create `backend/app/agents/confirmation_flow.py` with confirmation logic:
  - `is_destructive_action(user_message, agent_intent)` → detects bill creation, item deletion
  - `generate_confirmation_prompt(action_details)` → creates "Are you sure?" message
  - `handle_confirmation_response(user_response)` → parses "yes"/"no", returns confirmation decision
  - Timeout handling: mark pending actions as expired after 5 minutes

- [ ] T015 [P] Create unit tests for confirmation flow in `backend/tests/mcp/agent/test_confirmation_flow.py`:
  - Test: `is_destructive_action()` detects bill creation
  - Test: `is_destructive_action()` detects item deletion
  - Test: `generate_confirmation_prompt()` returns clear message
  - Test: `handle_confirmation_response("yes")` returns True
  - Test: `handle_confirmation_response("no")` returns False
  - Test: `handle_confirmation_response("maybe")` returns error (invalid)

**Write tests first (RED); implement confirmation logic (GREEN); refactor**

### FastAPI Integration Setup

- [X] T016 Create `backend/app/api/routes_agent.py` with route handlers (skeleton only):
  - `POST /agent/chat` → skeleton (will be implemented per user story)
  - `GET /agent/chat/stream` → skeleton (will be implemented per user story)
  - Route structure follows FastAPI patterns used in Phase 2

- [X] T017 [P] Update `backend/app/main.py` to:
  - Import agent routes: `from app.api.routes_agent import router as agent_router`
  - Register agent router: `app.include_router(agent_router, prefix="/api", tags=["agent"])`

- [ ] T018 [P] Create contract/API spec in `backend/contracts/agent-api.yaml`:
  - OpenAPI 3.0 spec for:
    - `POST /api/agent/chat` with request body (session_id, message), response (session_id, response, status, tool_calls)
    - `GET /api/agent/chat/stream` with query params (session_id, message), response (event-stream with SSE events)

**Checkpoint**: Foundation complete. Agent SDK ready, MCP client ready, session persistence ready, confirmation flow ready, FastAPI routes ready.

---

## Phase 3: User Story 1 - Store Admin Adds Inventory via Natural Language (Priority: P1) 🎯 MVP

**Goal**: Admin can say "Add 20kg sugar at 160 per kg to grocery" → Agent calls `inventory_add_item` MCP tool → Item created in DB

**Independent Test**: Send natural language message to `/agent/chat`, verify agent calls MCP tool, verify item persisted in PostgreSQL

### Tests for User Story 1 (TDD: Write First)

- [ ] T019 [P] [US1] Contract test `POST /agent/chat` for inventory add in `backend/tests/contract/test_agent_chat_inventory_add.py`:
  - Test: POST with message "Add 10kg flour at 50 per kg to grocery" returns 200 with response containing "Added"
  - Test: Response includes session_id and tool_calls showing `inventory_add_item` was called
  - Expected fields in response: session_id, response (string), status ("success" or "pending_confirmation"), tool_calls (array)

- [ ] T020 [P] [US1] Integration test for add inventory in `backend/tests/integration/test_agent_inventory_add_e2e.py`:
  - Test: Call `/agent/chat` with add request → verify PostgreSQL items table has new row
  - Test: Verify agent response is natural language confirmation
  - Test: Test error case: negative price → agent returns user-friendly error

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement `POST /agent/chat` endpoint in `backend/app/api/routes_agent.py`:
  - Accept request: `{session_id (optional), message (required)}`
  - Call `SessionManager.get_session(session_id)` to load conversation history
  - Call `OpenAIAgent.process_message(session_id, message)` to get agent response
  - Detect if response indicates destructive action (bill creation) → return with status="pending_confirmation"
  - Otherwise, return response with status="success" and any tool_calls info
  - Call `SessionManager.save_session()` to persist updated conversation history

- [ ] T022 [P] [US1] Implement `POST /agent/chat` error handling:
  - MCP server unreachable → return 503 with message: "Unable to reach the system. Please try again."
  - Database error → return 500 with message: "System error. Please try again."
  - Invalid request (missing message) → return 400 with validation error

- [ ] T023 [US1] Test agent behavior for inventory add with real MCP server (integration):
  - Start FastMCP server on localhost:8001 with inventory tools
  - Call `/agent/chat` with message "Add 20kg sugar at 160 per kg to grocery"
  - Verify agent parses request correctly and calls `inventory_add_item` with correct arguments
  - Verify response is natural language confirmation

- [ ] T024 [US1] Add logging for inventory add operations in `backend/app/agents/agent.py`:
  - Log when agent processes message: level=INFO, message="Processing user message for session {session_id}: {user_message_preview}"
  - Log when agent calls MCP tool: level=DEBUG, message="Calling MCP tool {tool_name} with args {args}"
  - Log tool result: level=DEBUG, message="Tool result: {result_status}"

**Checkpoint**: User Story 1 complete and independently testable. Admin can add inventory via natural language.

---

## Phase 4: User Story 2 - Salesperson Creates a Bill via Natural Language (Priority: P1) 🎯 MVP

**Goal**: Salesperson can say "Create a bill for Ali: 2kg sugar and 1 shampoo" → Agent calls `inventory_list_items` + `billing_create_bill` → Bill created, inventory updated

**Independent Test**: Send natural language bill creation request to `/agent/chat`, verify agent:
1. Searches inventory with `inventory_list_items` (finds matching items)
2. Detects destructive action (bill creation) → asks confirmation
3. On "yes" → calls `billing_create_bill`, returns bill summary with bill_id and total

### Tests for User Story 2 (TDD: Write First)

- [ ] T025 [P] [US2] Contract test `POST /agent/chat` for bill creation in `backend/tests/contract/test_agent_chat_bill_create.py`:
  - Test: POST with message "Create bill for Ali: 2kg sugar and 1 shampoo" returns 200 with status="pending_confirmation"
  - Test: Response includes confirmation prompt (e.g., "Are you sure...")
  - Test: Follow-up POST with session_id and message="yes" returns status="success" with bill_id

- [ ] T026 [P] [US2] Integration test for bill creation in `backend/tests/integration/test_agent_bill_create_e2e.py`:
  - Test: Setup: Create items "Sugar" and "Shampoo" with sufficient stock
  - Test: Call `/agent/chat` with bill request → returns pending_confirmation
  - Test: Follow-up confirmation with "yes" → bill created in DB, stock updated
  - Test: Call `/agent/chat` with insufficient stock (e.g., "5kg sugar" but only 3kg available) → agent warns and offers alternative

- [ ] T027 [P] [US2] Contract test for confirmation flow in `backend/tests/contract/test_agent_chat_confirmation.py`:
  - Test: User says "no" to confirmation → agent cancels action, bill not created
  - Test: User sends invalid confirmation (e.g., "maybe") → agent asks again

### Implementation for User Story 2

- [ ] T028 [US2] Update `backend/app/agents/agent.py` to handle confirmation flow:
  - After agent generates response, check `confirmation_flow.is_destructive_action(user_message, agent_intent)`
  - If destructive: set status="pending_confirmation", store pending action in session metadata
  - On next message: if action pending and user says "yes", execute the action; if "no", cancel

- [ ] T029 [P] [US2] Enhance confirmation prompt generation:
  - When bill is about to be created, agent generates specific prompt: "Are you sure you want to create a bill for {customer}: {items_summary} (Total: ${amount})? Reply 'yes' to confirm."

- [ ] T030 [P] [US2] Handle stock insufficient scenarios:
  - Agent detects when user requests more stock than available
  - Agent response: "Only {available} {unit} of {item} in stock. Would you like to add {available} instead?"
  - This is a clarification, not a destructive action, so no confirmation needed

- [ ] T031 [US2] Add logging for bill creation in `backend/app/agents/agent.py`:
  - Log when agent detects destructive action: level=INFO, message="Destructive action detected: {action_type} for session {session_id}"
  - Log when user confirms action: level=INFO, message="User confirmed {action_type}, proceeding"
  - Log bill creation result: level=INFO, message="Bill created: id={bill_id}, total={total}"

**Checkpoint**: User Story 2 complete and independently testable. Salesperson can create bills via natural language with confirmation.

---

## Phase 5: User Story 3 - Admin Queries Inventory via Natural Language (Priority: P2)

**Goal**: Admin can say "Show items with low stock under 5 units" → Agent calls `inventory_list_items` with filters → Agent summarizes results in natural language

**Independent Test**: Send query request to `/agent/chat`, verify agent calls `inventory_list_items` with correct filters, returns formatted list

### Tests for User Story 3 (TDD: Write First)

- [ ] T032 [P] [US3] Contract test for inventory query in `backend/tests/contract/test_agent_chat_query.py`:
  - Test: POST /agent/chat with message "Show items with low stock under 5" returns 200 with formatted list
  - Test: Response includes item names, prices, stock quantities
  - Test: Category filter works: "What's in the beauty category?"

- [ ] T033 [P] [US3] Integration test for inventory query in `backend/tests/integration/test_agent_inventory_query_e2e.py`:
  - Test: Setup: Create items with varying stock levels
  - Test: Query for low stock → agent returns correct items
  - Test: Query by category → agent filters correctly

### Implementation for User Story 3

- [ ] T034 [US3] Enhance agent to handle query requests (no destructive actions):
  - Agent recognizes query intent (e.g., "Show", "List", "What's")
  - Agent calls `inventory_list_items` with appropriate filters (stock_qty < X, category=Y)
  - Agent formats results as readable text summary
  - No confirmation needed for queries

**Checkpoint**: User Story 3 complete. Admin can query inventory via natural language.

---

## Phase 6: User Story 4 - Update Inventory Stock via Natural Language (Priority: P2)

**Goal**: Admin can say "Increase flour stock by 25kg" → Agent calls `inventory_update_item` → Stock updated in DB

**Independent Test**: Send stock update request to `/agent/chat`, verify agent calls `inventory_update_item`, verifies updated stock in PostgreSQL

### Implementation for User Story 4

- [ ] T035 [P] [US4] Create unit test for stock update in `backend/tests/agent/test_agent_stock_update.py`:
  - Test: Agent parses "Increase flour stock by 25kg"
  - Test: Agent calls `inventory_update_item` with new quantity (old + 25)
  - Test: Agent returns confirmation

- [ ] T036 [P] [US4] Implement stock update handling in `backend/app/agents/agent.py`:
  - Agent recognizes stock update intent (e.g., "Increase", "Decrease", "Update")
  - Agent looks up item (calls `inventory_list_items` to find match)
  - If multiple matches, ask user to clarify
  - Call `inventory_update_item` with new quantity
  - Return confirmation message

- [ ] T037 [US4] Add logging for stock updates:
  - Log item lookup: level=DEBUG
  - Log inventory update call: level=INFO

**Checkpoint**: User Story 4 complete. Admin can update stock via natural language.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final testing, documentation, edge case handling

- [ ] T038 Create `backend/apps/agents/quickstart.md` developer guide:
  - Setup instructions: .env file, install dependencies, run migrations, start MCP server
  - How to test: Example curl commands for `/agent/chat` endpoint
  - Troubleshooting: Common issues (MCP server unreachable, PostgreSQL not set up, invalid API key)
  - Performance testing: How to load test with concurrent sessions

**Checkpoint**: Phase 5 complete and production-ready. All user stories implemented, tested, documented.

---

## Testing Summary

**Total Test Tasks**: 9 (TDD: Red → Green → Refactor)

| Test | Story | Type | File |
|------|-------|------|------|
| T009 | Foundation | Unit (MCP Client) | `test_mcp_client.py` |
| T011 | Foundation | Unit (Session Manager) | `test_session_manager.py` |
| T013 | Foundation | Unit (Agent Orchestration) | `test_agent_orchestration.py` |
| T015 | Foundation | Unit (Confirmation Flow) | `test_confirmation_flow.py` |
| T019 | US1 | Contract | `test_agent_chat_inventory_add.py` |
| T020 | US1 | Integration | `test_agent_inventory_add_e2e.py` |
| T025 | US2 | Contract | `test_agent_chat_bill_create.py` |
| T026 | US2 | Integration | `test_agent_bill_create_e2e.py` |
| T032 | US3 | Contract | `test_agent_chat_query.py` |

**Coverage Target**: 80%+

---

## Implementation Strategy & Execution Order

### MVP Scope (Minimum Viable Product)
**Estimated**: 1-2 weeks

1. Setup (T001-T004) – 1 day
2. Foundational (T005-T024) – 3-4 days (includes TDD for agent, MCP client, session manager, confirmation)
3. User Story 1 (T025-T031) – 2-3 days (includes confirmation flow)
4. User Story 2 (T032-T038) – 2-3 days (bill creation with confirmation)

**At MVP completion**: Users can add inventory and create bills via natural language with confirmation.

### Full Scope
**Estimated**: 2-3 weeks (add 1 week for P2 stories + Polish)

5. User Story 3 (T032-T034) – 1-2 days (queries)
6. User Story 4 (T035-T037) – 1-2 days (stock updates)
7. Polish (T038) – 1 day

### Parallel Execution Opportunities

**During Phase 2 Foundational** (all parallel):
- T005-T007: Database setup
- T008-T009: MCP Client
- T010-T011: Session Manager
- T012-T013: Agent Orchestration
- T014-T015: Confirmation Flow
- T016-T018: FastAPI Integration

**During Phase 3 & 4** (US1 and US2 can run in parallel after foundational complete):
- T019-T024: US1 tests + implementation
- T025-T031: US2 tests + implementation (independent from US1)

**Suggested team structure**:
- Developer 1: MCP Client + Session Manager (T008-T011)
- Developer 2: Agent Orchestration + Confirmation (T012-T015)
- Developer 3: FastAPI Routes (T016-T018)
- Then both join for US1 & US2 (can split work: one on inventory add, one on bill create)

---

## Success Metrics

| Metric | Target | Verification |
|--------|--------|---|
| **All Tests Pass** | 100% | `pytest` runs all tests, all green |
| **Code Coverage** | 80%+ | `pytest --cov` report |
| **API Response Time** | 3s avg | Load test with 100 requests |
| **Clarification Response** | 1s avg | Timeout test for out-of-domain requests |
| **Session Persistence** | 100% | Post-request DB query confirms data saved |
| **Concurrent Sessions** | 10 without degradation | Load test with 10 concurrent clients |
| **Agent Accuracy** | 90% | Manual test cases (20+ scenarios) |

---

## Next Steps

1. ✅ Tasks generated and organized by user story
2. ⏭️ Execute Phase 1 (Setup) – 1 day
3. ⏭️ Execute Phase 2 (Foundational) – 3-4 days
4. ⏭️ Execute Phase 3 (US1) – 2-3 days
5. ⏭️ Execute Phase 4 (US2) – 2-3 days
6. ⏭️ (Optional) Execute Phase 5 (US3), Phase 6 (US4), Phase 7 (Polish)

**Recommended MVP sprint**: Complete Phases 1-4 in 1-2 weeks.

