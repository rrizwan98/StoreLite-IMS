# Implementation Plan: AI-Powered Analytics Dashboard

**Branch**: `007-ai-dashboard` | **Date**: 2025-12-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-ai-dashboard/spec.md`

**Status**: Ready for Phase 0 Research → Phase 1 Design → Phase 2 Task Generation

## Summary

Build an AI-powered analytics dashboard enabling warehouse managers and sales analysts to query inventory and sales data through natural language conversations. Users chat with an AI agent (Gemini) integrated into a ChatKit UI, requesting analyses like "compare last three months' sales" or "show inventory reorder recommendations." The system streams AI responses with real-time visualizations (charts, tables, metrics), maintains multi-turn conversation context, and supports JSON+CSV export. Implements read-only data access via tool-based query execution, inherits authentication from existing inventory system, and enforces 50 queries/hour per user with 30-day conversation retention.

**Core Technology Stack**:
- **Frontend**: React + ChatKit UI for conversational interface
- **Backend**: FastAPI + Python for Gemini integration and query orchestration
- **LLM**: Google Gemini 2.0 for natural language understanding and response generation
- **Data Access**: Tool-based framework for AI-initiated safe queries
- **Streaming**: WebSocket for real-time visualization updates

## Technical Context

**Language/Version**: Python 3.10+ (backend), TypeScript + React 18+ (frontend)

**Primary Dependencies**:
- **Backend**: FastAPI (web framework), google-generativeai (Gemini API), SQLAlchemy 2.0 (async ORM)
- **Frontend**: React + @openai/chatkit-react (ChatKit UI), Next.js or Vite (build)
- **Real-time**: WebSocket support (built into FastAPI via Starlette)
- **LLM Integration**: Google Gemini 2.0 API (streaming, tool calling support)

**Storage**:
- PostgreSQL (conversation history, tool call logs, user queries with 30-day retention)
- Session/Cache: Redis or in-memory for rate limiting and active session tracking

**Testing**:
- **Backend**: pytest + pytest-asyncio (async FastAPI testing)
- **Integration**: Contract tests for Gemini API tool calls
- **Frontend**: Jest/Vitest for ChatKit component tests

**Target Platform**: Web (desktop-primary, responsive for tablets)

**Project Type**: Web application (backend API + frontend SPA)

**Performance Goals**:
- Initial response latency: <10 seconds for first query
- Streaming start: <2 seconds
- Data query execution: <5 seconds (90% of requests)
- Support 10+ concurrent users in MVP, 50+ by end of year

**Constraints**:
- Hard stop: 30-second max response timeout
- Concurrent user limit: Design for 50+ simultaneous sessions
- Rate limit: 50 queries per user per hour
- Security: Read-only queries only, sandboxed AI tool execution

**Scale/Scope**:
- MVP: 5 P1 user stories (3 core, 2 enhancement)
- Dashboard: Multi-turn conversations with 3-10 message exchanges per session
- Data volume: Query existing inventory/sales tables (no data volume restrictions assumed)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Principle I - Separation of Concerns**: ✅ PASS
- Backend (FastAPI + Gemini integration) completely separate from frontend (React + ChatKit)
- API contracts will define frontend-backend interaction
- No code imports between frontend and backend folders

**Principle II - Test-Driven Development**: ✅ PASS
- All backend endpoints require tests written first (RED → GREEN → REFACTOR)
- FastAPI contract tests for Gemini tool definitions
- Frontend optional but encouraged to follow TDD
- Target 80%+ coverage for backend AI integration logic

**Principle III - Phased Implementation**: ✅ PASS
- Feature aligns with Phase 5 (AI Agents) in constitution
- Builds on existing Phase 1-4 infrastructure (inventory API, MCP tools)
- Dashboard is independent feature module within Phase 5

**Principle IV - Database-First Design**: ✅ PASS
- Conversation history persisted to PostgreSQL (not in-memory)
- Tool call results logged for audit trail
- 30-day retention with soft deletes (mark as archived, not physical delete)

**Principle V - Contract-First APIs**: ✅ PASS
- Gemini tool definitions documented before implementation
- OpenAPI/Swagger for REST endpoints
- ChatKit message format specifications defined upfront

**Principle VI - Local-First Development**: ✅ PASS
- All services (FastAPI, Gemini client, database) run locally during dev
- `.env` for API keys and connection strings
- No hardcoded credentials

**Principle VII - Simplicity Over Abstraction**: ✅ PASS
- Direct FastAPI routes, no over-engineered middleware
- Tool framework kept minimal; no complex abstractions
- Gemini streaming handled directly, no custom wrapper abstractions

**Principle VIII - Observability by Default**: ✅ PASS
- All API requests logged (endpoint, user, latency, result)
- Gemini API calls logged with tool names and results
- Conversation metadata (timestamps, user ID, token usage) tracked
- Error states logged with full context for debugging

**Gate Result**: ✅ ALL PRINCIPLES SATISFIED - Proceed to Phase 0 Research

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

**Web Application Structure** - Frontend + Backend separation per Constitution Principle I

```text
backend/
├── src/
│   ├── models/
│   │   ├── conversation.py      # ConversationSession, Query, Response, ToolCall entities
│   │   ├── tool_definition.py   # Gemini tool schemas (get_sales_by_month, etc.)
│   │   └── data_snapshot.py     # Immutable data snapshots for queries
│   ├── services/
│   │   ├── gemini_service.py    # Gemini API client + streaming logic
│   │   ├── query_handler.py     # Natural language → tool execution orchestration
│   │   ├── tool_executor.py     # Safe execution of AI-initiated data queries
│   │   ├── rate_limiter.py      # Per-user 50 queries/hour enforcement
│   │   └── auth_service.py      # Inherited inventory system auth
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py          # POST /api/chat, WebSocket /ws/chat
│   │   │   ├── conversation.py  # GET /api/conversations, DELETE /api/conversations/:id
│   │   │   └── export.py        # GET /api/export/{format} (json, csv)
│   │   └── schemas/             # Pydantic models for API contracts
│   ├── middleware/
│   │   ├── auth.py              # Inherited auth validation
│   │   ├── logging.py           # Request/response logging, duration tracking
│   │   └── error_handler.py     # Gemini errors, query timeouts, graceful degradation
│   └── main.py                  # FastAPI app initialization
├── tests/
│   ├── unit/
│   │   ├── test_gemini_service.py
│   │   ├── test_query_handler.py
│   │   ├── test_tool_executor.py
│   │   └── test_rate_limiter.py
│   ├── integration/
│   │   ├── test_chat_endpoint.py
│   │   ├── test_websocket.py
│   │   └── test_context_management.py
│   └── contract/
│       ├── test_gemini_tools.py  # Verify tool definitions match Gemini schema
│       └── test_api_contracts.py
├── .env.example
├── pyproject.toml
└── alembic/                     # Database migrations for new tables

frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx    # ChatKit UI wrapper + message rendering
│   │   ├── VisualizationPanel.tsx # Charts (line, bar, table) + metric displays
│   │   ├── ExportButton.tsx     # JSON/CSV export triggers
│   │   └── RateLimitWarning.tsx # 50/hr limit indicator
│   ├── pages/
│   │   ├── dashboard.tsx        # Main analytics dashboard page
│   │   └── layout.tsx           # Inherited auth + navigation
│   ├── services/
│   │   ├── api.ts              # HTTP client for backend endpoints
│   │   ├── websocket.ts        # WebSocket client for streaming updates
│   │   └── export.ts           # JSON/CSV download handling
│   ├── hooks/
│   │   ├── useChat.ts          # Chat state management
│   │   ├── useVisualization.ts # Visualization rendering logic
│   │   └── useStreamingResponse.ts # Streaming message handling
│   └── types/
│       └── index.ts            # TypeScript types for API contracts
├── tests/
│   ├── components/
│   │   └── ChatInterface.test.tsx
│   ├── integration/
│   │   └── chat_flow.test.tsx
│   └── hooks/
│       └── useChat.test.ts
├── package.json
└── .env.local.example
```

**Structure Decision**: Web application with backend/frontend separation. Backend handles Gemini integration, rate limiting, authentication, and data access. Frontend consumes chat API via REST/WebSocket and renders visualizations using ChatKit.

## Complexity Tracking

✅ **No complexity violations** - All 8 constitution principles satisfied. No justifications needed.

## Phase 0: Research & Unknowns

> **Resolved via context7 research and specifications clarification**

No "NEEDS CLARIFICATION" items remain. Latest documentation confirms:
1. ✅ ChatKit supports streaming responses and event handling (useChatKit, onResponseStart, onResponseEnd)
2. ✅ Gemini API supports streaming text, tool calling, and live sessions with WebSocket
3. ✅ FastAPI + WebSocket provides real-time bidirectional communication
4. ✅ Claude Agent SDK provides tool definition patterns (@tool decorator, MCP servers)

**Decision outcomes from clarification session**:
- Q1 (Auth): Inherit existing inventory system auth/roles
- Q2 (Retention): 30-day conversation + indefinite audit logs
- Q3 (Rate Limit): 50 queries/hour per user
- Q4 (Export): JSON (full state) + CSV (tables); PDF deferred
- Q5 (Context): Full conversation history with each Gemini query

**Research complete. Phase 0 → Phase 1 ready.**

## Phase 1: Data Model & API Design

### Data Model (data-model.md to be generated)

**Key Entities**:
- **ConversationSession**: session_id, user_id, created_at, last_accessed_at, is_archived, expires_at(30 days)
- **Query**: id, session_id, user_input, created_at, status (pending/completed/error)
- **Response**: id, query_id, gemini_response_text, visualizations (JSON), data_snapshot_id
- **ToolCall**: id, response_id, tool_name, parameters, result, latency_ms (for audit trail)
- **DataSnapshot**: id, created_at, inventory_data (JSON), sales_data (JSON) (immutable point-in-time copy)

### API Contracts (contracts/ to be generated)

**Key Endpoints**:
- `POST /api/chat` - Submit query, return streaming response
- `WebSocket /ws/chat/:session_id` - Real-time visualization updates
- `GET /api/conversations` - List user's conversations
- `DELETE /api/conversations/:id` - User-initiated deletion
- `GET /api/export/:session_id?format=json|csv` - Export results

### Deliverables after Phase 1

- ✅ `data-model.md` with entity relationships and validation rules
- ✅ `contracts/openapi.yaml` - REST endpoint specifications
- ✅ `contracts/websocket-schema.json` - WebSocket message format
- ✅ `contracts/gemini-tools.json` - Tool definitions (get_sales_by_month, etc.)
- ✅ `quickstart.md` - Local development setup guide
- ✅ Updated agent context (environment for Phase 2 task generation)

## Phase 2: Task Generation

Triggers `/sp.tasks` to create:
- Sprint-organized task list with TDD test cases
- Backend tasks: Tool executor, Gemini streaming, WebSocket, rate limiting, DB models
- Frontend tasks: ChatKit integration, visualization rendering, WebSocket client
- Integration tasks: End-to-end conversation flows, export functionality

---

## Next Steps

1. **Phase 0 Complete**: All clarifications resolved ✅
2. **Phase 1 Ready**: Run `/sp.plan` to generate research.md, data-model.md, contracts/*, quickstart.md
3. **Phase 2 Ready**: Run `/sp.tasks` to generate task.md with TDD-driven development tasks
