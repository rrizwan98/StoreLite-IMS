# Implementation Plan: ChatKit UI Integration (Phase 6)

**Branch**: `006-chatkit-ui` | **Date**: 2025-12-09 | **Spec**: [ChatKit UI Integration](spec.md)
**Input**: Feature specification from `/specs/006-chatkit-ui/spec.md`

**Note**: This plan designs the implementation architecture for Phase 6, following the specification clarifications from 2025-12-09.

## Summary

**Objective**: Integrate OpenAI's ChatKit UI component into the Next.js frontend (right-side corner widget) to expose the Phase 5 OpenAI Agent through a conversational chat interface.

**Technical Approach**:
1. **Frontend**: Add `@openai/chatkit-react` component to Next.js layout for persistent bottom-right widget across all routes (`/admin`, `/pos`, `/agent`)
2. **Backend**: Implement `/agent/chat` API endpoint that bridges ChatKit → Gemini 2.0 Flash Lite agent → MCP tools → PostgreSQL
3. **Data Contract**: Agent returns JSON-structured responses; ChatKit auto-formats bills/item lists into readable cards and tables
4. **Session Management**: Tab-lifetime session persistence; cleanup on page close or logout
5. **Error Handling**: One-time silent auto-retry + manual "Retry" button for persistent failures
6. **UX Feedback**: "Agent is thinking..." with elapsed time counter during processing

## Technical Context

**Frontend Language/Version**: TypeScript/Node.js 18+ running on Next.js 14+ (App Router)
**Backend Language/Version**: Python 3.10+ with FastAPI and OpenAI Agents SDK

**Primary Dependencies**:
- Frontend: `@openai/chatkit-react`, `@openai/chatkit`, React 18+, Next.js 14+, Tailwind CSS
- Backend: FastAPI, OpenAI Agents SDK, Gemini 2.0 Flash Lite (via LiteLLM), FastMCP 2.x, SQLAlchemy 2.x, asyncpg, Pydantic
- Agent Runtime: OpenAI Agents SDK with Gemini 2.0 Flash Lite model
- MCP: Local FastMCP server (Phase 4) exposing inventory and billing tools

**Storage**: PostgreSQL (existing database from Phase 1-5) for session persistence, conversation history, and agent interaction logs

**Testing**:
- Backend: pytest with pytest-asyncio (unit, integration, contract tests)
- Frontend: Jest + React Testing Library (optional for Phase 6)
- Agent: Conversation tests validating end-to-end ChatKit → Agent → MCP → DB flows

**Target Platform**: Web (modern browsers with ES2020+ support), Server (FastAPI on Linux/macOS/Windows)

**Project Type**: Web (frontend + backend monorepo with clear separation per Constitution Principle I)

**Performance Goals**:
- Agent response time: 3-5 seconds (SC-004: display within 5 seconds)
- ChatKit component load: <2 seconds after page load (SC-010)
- Message delivery: 100% without loss (SC-003)
- Bill creation accuracy: 95%+ (SC-007)
- Natural language interpretation: 90%+ accuracy (SC-009)

**Constraints**:
- Self-hosted backend mode only (not OpenAI Hosted MCP service) due to Gemini-lite model requirement
- ChatKit cannot use custom UI components or override internal styles
- Session lifetime tied to browser tab (expires on page close or logout)
- Text-only input/output (no voice, file uploads, or multimodal)
- All communication HTTP/REST with JSON payloads
- No authentication/authorization changes (assume existing app-level auth)

**Scale/Scope**:
- Single-user sessions (no multi-user collaboration in Phase 6)
- Persistent widget across 3 routes: `/admin`, `/pos`, `/agent`
- Message history maintained in memory + optional backend PostgreSQL storage
- Phase 6 builds on existing Phase 1-5 infrastructure without breaking changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **All 8 Core Principles Verified** (Constitution v1.1.0):

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| I. Separation of Concerns | ✅ PASS | Frontend (`@openai/chatkit-react` in Next.js) and backend (`/agent/chat` FastAPI endpoint) are completely separated. API contract only. |
| II. Test-Driven Development | ✅ PASS | Conversation tests will validate end-to-end flows; backend uses pytest + pytest-asyncio; frontend optional Jest/RTL. Target 80% coverage. |
| III. Phased Implementation | ✅ PASS | Phase 6 builds on Phase 1-5 without breaking changes. No reimplementation of prior work. Sequential dependency respected. |
| IV. Database-First Design | ✅ PASS | Session data, conversation history, and agent interaction logs stored in PostgreSQL (Principles of Single Source of Truth, Snapshots, Soft Deletes). |
| V. Contract-First APIs | ✅ PASS | `/agent/chat` endpoint contract defined in spec; JSON request/response with structured agent output documented in Assumption section. |
| VI. Local-First Development | ✅ PASS | FastAPI runs locally with DATABASE_URL in `.env`. MCP tools run locally. ChatKit connects to localhost `/agent/chat` endpoint. No cloud services. |
| VII. Simplicity Over Abstraction | ✅ PASS | ChatKit used as-is (no custom UI wrapping). Direct HTTP calls from frontend to backend. No repository patterns or unnecessary layers. |
| VIII. Observability by Default | ✅ PASS | Agent interactions logged; API response times tracked; message delivery status monitored. Error logging includes context for debugging. |

**Constitution Gate Status**: ✅ **CLEAR TO PROCEED**

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

**Web Application Structure** (frontend + backend separation per Constitution Principle I):

**Backend** (`backend/`):
```text
backend/
├── app/
│   ├── models/                    # SQLAlchemy ORM models
│   │   └── schemas.py            # Pydantic models for requests/responses
│   ├── routers/
│   │   ├── inventory.py          # Inventory endpoints (Phase 2)
│   │   ├── billing.py            # Billing endpoints (Phase 2)
│   │   └── agent.py              # Agent endpoints (Phase 5-6) ← /agent/chat endpoint
│   ├── services/
│   │   ├── inventory.py          # Inventory business logic
│   │   ├── billing.py            # Billing business logic
│   │   └── agent.py              # Agent service (call OpenAI Agents SDK)
│   ├── agents/
│   │   └── agent.py              # OpenAI Agent definition with Gemini-lite (Phase 5)
│   ├── mcp_server/
│   │   ├── tools_inventory.py    # Inventory MCP tools (Phase 4)
│   │   ├── tools_billing.py      # Billing MCP tools (Phase 4)
│   │   └── utils.py              # MCP utilities
│   └── main.py                   # FastAPI app initialization
├── tests/
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── agent/                     # Conversation/agent tests
├── pyproject.toml                 # Python dependencies
└── .env.example                   # Environment variables template
```

**Frontend** (`frontend/` or repository root if Next.js):
```text
app/                              # Next.js 14 App Router
├── admin/                        # Inventory management routes
│   └── page.tsx                 # Admin dashboard
├── pos/                          # Billing/POS routes
│   └── page.tsx                 # POS interface
├── agent/                        # Agent-dedicated routes
│   └── page.tsx                 # Agent interface
└── layout.tsx                   # Root layout with ChatKit widget (Phase 6)

lib/
├── api.ts                       # API client for calling /agent/chat endpoint
└── hooks/                       # React hooks (chat session, etc.)

components/
├── ChatKitWidget.tsx            # ChatKit wrapper component (Phase 6)
└── [existing admin/pos components]

public/                          # Static assets

.env.local.example               # Frontend environment (API endpoint URL)
package.json                     # Frontend dependencies
```

**Phase 6 Key Additions**:
- `app/layout.tsx`: Embed `<ChatKitWidget>` for all routes (bottom-right corner)
- `components/ChatKitWidget.tsx`: Wrapper for `@openai/chatkit-react` with session management
- `lib/api.ts`: Add `chatWithAgent()` function to call `/agent/chat` endpoint
- `backend/app/routers/agent.py`: Implement POST `/agent/chat` endpoint (Phase 5 exists; Phase 6 integrates)
- `backend/tests/agent/`: Conversation tests for ChatKit → Agent → MCP → DB flows

**Structure Decision**: Web application (Option 2) with strict separation per Constitution Principle I. Frontend and backend have independent dependencies, configs, and deployment. Both are versioned in the same repository for ease of coordination.

## Complexity Tracking

**Status**: ✅ **NO VIOLATIONS** - All Constitution principles satisfied without added complexity.

No additional complexity beyond what Constitution already permits. Phase 6 uses:
- **Direct HTTP calls** from frontend to backend (not repository patterns)
- **ChatKit as-is** without custom UI wrapping or abstraction layers
- **Existing database schema** without new tables or migrations
- **Local-first development** with no cloud infrastructure
- **Simple service layer** in backend to call OpenAI Agent SDK

This approach maintains simplicity while building new feature (Constitution Principle VII).
