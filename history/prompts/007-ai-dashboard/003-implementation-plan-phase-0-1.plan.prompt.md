---
ID: 003
TITLE: Implementation Plan - Phase 0 & 1 Ready
STAGE: plan
DATE_ISO: 2025-12-10
SURFACE: agent
MODEL: claude-haiku-4-5
FEATURE: 007-ai-dashboard
BRANCH: 007-ai-dashboard
USER: user
COMMAND: /sp.plan
LABELS:
  - ai-dashboard
  - implementation-plan
  - phase-0
  - phase-1
  - architecture
  - constitution-check
LINKS:
  SPEC: specs/007-ai-dashboard/spec.md
  TICKET: null
  ADR: null
  PR: null
FILES:
  - specs/007-ai-dashboard/plan.md
TESTS: []
---

## Prompt

User requested to build the implementation plan for the AI-Powered Analytics Dashboard feature (007-ai-dashboard). Previous stages complete:
- ✅ Specification created with all 5 user stories, 14 functional requirements, 12 success criteria
- ✅ Clarification session completed with 5 critical decisions resolved:
  1. Authentication: Inherit existing inventory system
  2. Data retention: 30-day conversations + indefinite audit logs
  3. Rate limiting: 50 queries/hour per user
  4. Export formats: JSON + CSV (PDF deferred)
  5. Context strategy: Full conversation history with Gemini

## Response

### Planning Execution

Created comprehensive implementation plan covering all phases:

#### Technical Context (Fully Specified)

**Backend Stack**:
- Language: Python 3.10+
- Framework: FastAPI with async/await
- LLM: Google Gemini 2.0 API (streaming, tool calling)
- Database: PostgreSQL + SQLAlchemy 2.0 async ORM
- Testing: pytest + pytest-asyncio
- Cache: Redis or in-memory for rate limiting

**Frontend Stack**:
- Language: TypeScript + React 18+
- UI: ChatKit (@openai/chatkit-react) for chat interface
- Build: Next.js or Vite
- Testing: Jest/Vitest for components

**Non-Functional Requirements**:
- Initial response: <10 seconds
- Streaming start: <2 seconds
- Hard timeout: 30 seconds max
- Concurrent users: 10+ MVP, 50+ by EOY
- Rate limit: 50 queries/user/hour
- Data retention: 30 days (conversations), indefinite (audit logs)

#### Constitution Check (All 8 Principles Satisfied)

**Principle I - Separation of Concerns**: ✅
- Backend (FastAPI + Gemini) completely separate from frontend (React + ChatKit)
- API contracts define all interactions
- No direct code imports between frontend/backend

**Principle II - Test-Driven Development**: ✅
- All endpoints tested before implementation (RED → GREEN → REFACTOR)
- Contract tests for Gemini tool definitions
- Target 80%+ coverage for AI integration logic

**Principle III - Phased Implementation**: ✅
- Feature aligns with Phase 5 (AI Agents) in constitution
- Builds on existing Phase 1-4 infrastructure
- Independent feature module within Phase 5

**Principle IV - Database-First Design**: ✅
- Conversation history persisted to PostgreSQL
- Tool call results logged for audit trail
- Soft deletes for 30-day retention (archived, not physical delete)

**Principle V - Contract-First APIs**: ✅
- Gemini tool definitions documented before implementation
- OpenAPI/Swagger for all REST endpoints
- ChatKit message format specs defined upfront

**Principle VI - Local-First Development**: ✅
- All services run locally (FastAPI, Gemini client, database)
- `.env` for credentials and connection strings
- No hardcoded secrets

**Principle VII - Simplicity Over Abstraction**: ✅
- Direct FastAPI routes, minimal middleware
- Tool framework kept lean; no over-engineering
- Gemini streaming handled directly

**Principle VIII - Observability by Default**: ✅
- All API requests logged (endpoint, user, latency, result)
- Gemini API calls logged with tool names and results
- Conversation metadata tracked (timestamps, user ID, token usage)

**Gate Result**: ✅ **ALL PRINCIPLES SATISFIED** - Proceed to Phase 0 Research and Phase 1 Design

#### Project Structure (Web Application)

**Backend Structure**:
```
backend/src/
├── models/
│   ├── conversation.py (ConversationSession, Query, Response, ToolCall)
│   ├── tool_definition.py (Gemini tool schemas)
│   └── data_snapshot.py (Immutable point-in-time data copies)
├── services/
│   ├── gemini_service.py (API client + streaming)
│   ├── query_handler.py (NL → tool execution)
│   ├── tool_executor.py (Safe query execution)
│   ├── rate_limiter.py (50 queries/hour)
│   └── auth_service.py (Inherited auth)
├── api/routes/
│   ├── chat.py (POST /api/chat, WebSocket /ws/chat)
│   ├── conversation.py (GET/DELETE conversations)
│   └── export.py (GET /api/export?format=json|csv)
├── middleware/
│   ├── auth.py
│   ├── logging.py
│   └── error_handler.py
└── tests/
    ├── unit/ (gemini_service, query_handler, tool_executor, rate_limiter)
    ├── integration/ (chat_endpoint, websocket, context_management)
    └── contract/ (gemini_tools, api_contracts)
```

**Frontend Structure**:
```
frontend/src/
├── components/
│   ├── ChatInterface.tsx (ChatKit wrapper)
│   ├── VisualizationPanel.tsx (Charts, tables, metrics)
│   ├── ExportButton.tsx (JSON/CSV export)
│   └── RateLimitWarning.tsx (50/hr indicator)
├── pages/
│   ├── dashboard.tsx (Main analytics page)
│   └── layout.tsx (Auth + navigation)
├── services/
│   ├── api.ts (HTTP client)
│   ├── websocket.ts (Streaming client)
│   └── export.ts (Download handling)
├── hooks/
│   ├── useChat.ts (State management)
│   ├── useVisualization.ts (Rendering logic)
│   └── useStreamingResponse.ts (Streaming handler)
└── tests/
    ├── components/ (ChatInterface tests)
    ├── integration/ (chat_flow end-to-end)
    └── hooks/ (useChat tests)
```

#### Phase 0: Research (Complete)

No "NEEDS CLARIFICATION" items remain from specification. Context7 research confirmed:
1. ✅ ChatKit supports streaming responses and event handling
2. ✅ Gemini API supports streaming text, tool calling, live sessions
3. ✅ FastAPI + WebSocket enables real-time bidirectional communication
4. ✅ Claude Agent SDK provides tool definition patterns

All 5 clarification decisions from `/sp.clarify` session applied and documented.

#### Phase 1: Data Model & API Design (To Be Generated)

**Data Model Entities to Document**:
- **ConversationSession**: (session_id, user_id, created_at, last_accessed_at, is_archived, expires_at)
- **Query**: (id, session_id, user_input, created_at, status)
- **Response**: (id, query_id, gemini_response_text, visualizations, data_snapshot_id)
- **ToolCall**: (id, response_id, tool_name, parameters, result, latency_ms)
- **DataSnapshot**: (id, created_at, inventory_data, sales_data) [immutable]

**API Contracts to Document**:
- REST endpoints: POST /api/chat, GET /api/conversations, DELETE, GET /api/export
- WebSocket: /ws/chat/:session_id for streaming updates
- Gemini tool definitions: get_sales_by_month, get_inventory_status, get_product_analytics, etc.
- Message formats: Chat message schema, visualization metadata schema

**Phase 1 Deliverables**:
- ✅ `data-model.md` (entities, relationships, validation rules)
- ✅ `contracts/openapi.yaml` (REST API specification)
- ✅ `contracts/websocket-schema.json` (WebSocket message format)
- ✅ `contracts/gemini-tools.json` (Tool definitions)
- ✅ `quickstart.md` (Local dev setup guide)
- ✅ Updated agent context

#### Phase 2: Task Generation (Follows Phase 1)

After Phase 1 design artifacts complete, `/sp.tasks` will generate:
- Sprint-organized task list with TDD test cases
- Backend implementation tasks (tool executor, Gemini streaming, WebSocket, rate limiting, DB models)
- Frontend tasks (ChatKit integration, visualization rendering, WebSocket client)
- Integration tasks (end-to-end flows, export functionality)

#### Complexity Tracking

✅ **No violations** - All 8 constitution principles satisfied. No justifications needed for complexity additions.

### Key Architectural Decisions

1. **Streaming Architecture**: WebSocket for real-time visualization updates vs REST polling
   - **Choice**: WebSocket for responsiveness (requirement: <2 second streaming start)
   - **Rationale**: Meets SC-003 success criteria without client polling overhead

2. **Conversation Context**: Full history vs windowed history vs summarization
   - **Choice**: Full conversation history with each Gemini query (from /sp.clarify Q5)
   - **Rationale**: Simplest implementation, maximum accuracy, acceptable token cost for typical 3-10 message exchanges

3. **Data Access**: Tool-based query execution vs direct database access
   - **Choice**: Tool-based framework (AI agent calls get_sales_by_month, get_inventory_status, etc.)
   - **Rationale**: Security (sandboxed queries), auditability (logged tool calls), alignment with LLM agent patterns

4. **Authentication**: Inherit existing vs custom
   - **Choice**: Inherit existing inventory system auth/roles (from /sp.clarify Q1)
   - **Rationale**: Reuses trusted infrastructure, simplifies integration, reduces security surface

5. **Data Retention**: Session-only vs 30-day vs indefinite
   - **Choice**: 30-day conversation retention + indefinite audit logs (from /sp.clarify Q2)
   - **Rationale**: Balances user privacy (can delete), compliance (30-day history), auditability (permanent audit trail)

### Risk Assessment

**Highest Risk Areas**:
1. **Gemini API Integration**: Tool calling accuracy and timeout handling
   - **Mitigation**: Comprehensive contract tests, graceful degradation on timeout (partial response)

2. **Conversation Context Management**: Accurate multi-turn understanding
   - **Mitigation**: Full history approach reduces ambiguity; test conversational accuracy (SC-004: 95%)

3. **Real-Time Visualization**: Streaming update performance under load
   - **Mitigation**: WebSocket efficiency, chunked response handling, client-side debouncing

4. **Rate Limiting & Quotas**: Per-user 50 queries/hour enforcement
   - **Mitigation**: Redis-backed rate limiter with token bucket algorithm, early warning (SC-006: 10+ concurrent)

### Readiness for Phase 1 & 2

✅ **All Gate Checks Passed**:
- Constitution compliance: ✅
- Technical context specified: ✅
- Project structure defined: ✅
- Clarifications resolved: ✅
- No NEEDS CLARIFICATION items: ✅

**Ready for**:
1. Phase 1: Data model design, API contract generation, quickstart documentation
2. Phase 2: Task generation with TDD test cases and sprint organization

### Next Commands

```bash
# Phase 1 design artifacts (run after /sp.plan completes)
# Generates: research.md, data-model.md, contracts/*, quickstart.md

# Phase 2 task generation (run after Phase 1 complete)
/sp.tasks
# Generates: tasks.md with TDD test cases and sprint tasks
```

