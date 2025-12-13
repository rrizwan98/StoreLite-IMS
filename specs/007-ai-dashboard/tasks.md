# Implementation Tasks: AI-Powered Analytics Dashboard

**Feature**: `007-ai-dashboard` | **Branch**: `007-ai-dashboard` | **Created**: 2025-12-10

## Overview

Comprehensive task breakdown for building an AI-powered analytics dashboard with natural language querying via Gemini LLM, real-time streaming visualizations, multi-turn conversations, and data export capabilities. Tasks organized by user story priority (P1 → P2) with independent test criteria for each story.

**MVP Scope**: User Stories 1-3 (P1) for initial release
- Natural Language Sales Comparison (US1)
- Real-Time Dashboard Updates (US2)
- Multi-Turn Analytics Conversations (US3)

**Post-MVP Scope**: User Stories 4-5 (P2) in subsequent releases

---

## Phase 1: Setup & Infrastructure

### Project Initialization

- [x] T001 Create backend project structure per implementation plan (`backend/app/`, `backend/tests/`) ✅ EXISTS
- [x] T002 Create frontend project structure per implementation plan (`frontend/components/`, `frontend/app/`, `frontend/lib/`) ✅ EXISTS
- [x] T003 Initialize FastAPI application in `backend/app/main.py` with CORS middleware, error handlers, and logging ✅ EXISTS
- [x] T004 Initialize React app with ChatKit dependencies (pure `<openai-chatkit>` web component via CDN) ✅ EXISTS
- [x] T005 Create `.env.example` files for backend and frontend with required API keys (GEMINI_API_KEY, DATABASE_URL, etc.) ✅ EXISTS
- [x] T006 [P] Setup PostgreSQL database connection in `backend/app/database.py` ✅ EXISTS (using Neon PostgreSQL)
- [x] T007 [P] Setup pytest configuration and async test fixtures in `backend/pyproject.toml` ✅ EXISTS
- [x] T008 [P] Create database connection pool and SQLAlchemy engine in `backend/app/database.py` ✅ EXISTS
- [ ] T009 Setup GitHub Actions CI/CD pipeline for automated testing and validation
- [ ] T010 Create `quickstart.md` with local development setup instructions (database, environment variables, running services)

---

## Phase 2: Foundational Components & Authentication

### Database Models & Schemas

- [x] T011 [P] Create ConversationSession model in `backend/app/models.py` (AgentSession exists with session_id, conversation_history, metadata) ✅ EXISTS
- [x] T012 [P] Create Query/Response model in `backend/app/models.py` (ConversationHistory exists with user_message, agent_response, structured_data) ✅ EXISTS
- [ ] T013 [P] Extend ConversationHistory model with visualizations_json field for analytics dashboard
- [ ] T014 [P] Create ToolCall model in `backend/app/models.py` (id, response_id, tool_name, parameters_json, result_json, latency_ms)
- [ ] T015 [P] Create DataSnapshot model in `backend/app/models.py` (id, created_at, inventory_data_json, sales_data_json)
- [ ] T016 Create database migrations for new models (ToolCall, DataSnapshot, analytics fields)

### Authentication & Authorization Middleware

- [x] T017 [P] Auth service inherited from existing inventory system ✅ EXISTS (uses existing auth)
- [x] T018 [P] Authentication middleware exists in `backend/app/main.py` ✅ EXISTS
- [x] T019 Create rate limiting service in `backend/app/services/rate_limiter.py` enforcing 50 queries/hour per user (in-memory) ✅ IMPLEMENTED
- [x] T020 Create rate limiting middleware in chatkit_server.py returning 429 when limit exceeded ✅ IMPLEMENTED

### Logging & Observability

- [x] T021 [P] Structured logging exists in `backend/app/routers/chatkit_server.py` ✅ EXISTS
- [x] T022 [P] Error handler exists in `backend/app/main.py` with exception handlers ✅ EXISTS
- [x] T023 Logging configuration exists in main.py with Python logging ✅ EXISTS

---

## Phase 3: User Story 1 - Natural Language Sales Comparison (P1)

**Goal**: Enable users to ask natural language questions about sales data and receive AI-analyzed responses with visualizations

**Independent Test Criteria**:
- [ ] User can submit query "Show me sales for last month" and receive response with summary metrics (total sales, top 5 products, daily trends)
- [ ] Response includes embedded visualizations (charts, tables) in chat message
- [ ] System correctly interprets "What changed between October and November?" and highlights percentage changes, new products, discontinued items

### Gemini Integration & Tool Definitions

- [x] T024 Gemini/LiteLLM service exists in `backend/app/agents/agent.py` (OpenAIAgent with LiteLLM + Gemini 2.0 Flash Lite) ✅ EXISTS
- [x] T025 [P] Add analytics tool definitions to MCP server `backend/app/mcp_server/tools_analytics.py` ✅ IMPLEMENTED:
  - `get_sales_by_month(year: int, month: int)` → returns sales summary with top products
  - `compare_sales(period1: str, period2: str)` → returns comparative analysis with percentage changes
  - `get_sales_trends(days: int)` → returns sales trends analysis
  - `get_inventory_analytics()` → returns inventory health, alerts, recommendations
- [x] T026 [P] Updated agent system prompt in `backend/app/agents/agent.py` with analytics tool instructions ✅ IMPLEMENTED
- [x] T027 Streaming response handler exists in `backend/app/routers/chatkit_server.py` (IMSChatKitServer.respond with AsyncIterator) ✅ EXISTS
- [x] T028 Query handler exists in `backend/app/agents/agent.py` (OpenAIAgent.process_message) ✅ EXISTS

### API Endpoints

- [x] T029 POST endpoint `/agent/chatkit` exists in `backend/app/routers/chatkit_server.py` ✅ EXISTS
- [x] T030 [P] Session management exists in `backend/app/services/session_service.py` ✅ EXISTS
- [x] T031 Pydantic schemas exist in `backend/app/schemas.py` ✅ EXISTS

### Frontend Chat Interface

- [x] T032 ChatInterface component exists in `frontend/components/shared/ChatKitWidget.tsx` (pure openai-chatkit web component) ✅ EXISTS
- [x] T033 [P] Chat state managed by ChatKit SDK internally ✅ EXISTS (via setOptions)
- [x] T034 [P] API client uses custom fetch in ChatKitWidget.tsx ✅ EXISTS
- [x] T035 Create dedicated analytics dashboard page in `frontend/app/analytics/page.tsx` for data visualizations ✅ IMPLEMENTED
- [x] T036 [P] Message rendering handled by ChatKit SDK ✅ EXISTS

### Visualization Components

- [x] T037 Create VisualizationPanel component in `frontend/components/analytics/VisualizationPanel.tsx` rendering charts and tables ✅ IMPLEMENTED
- [x] T038 [P] Implement line chart visualization for sales trends (CSS/SVG-based SimpleLineChart) ✅ IMPLEMENTED
- [x] T039 [P] Implement bar chart visualization for product comparisons (CSS-based SimpleBarChart) ✅ IMPLEMENTED
- [x] T040 [P] Implement table visualization for detailed data display with sorting/filtering (DataTable) ✅ IMPLEMENTED
- [x] T041 Create metric display component for KPIs (MetricCard) ✅ IMPLEMENTED

### Testing for US1

- [ ] T042 Write unit tests in `backend/tests/unit/test_gemini_service.py` for streaming response handling
- [ ] T043 Write integration tests in `backend/tests/integration/test_chat_endpoint.py` for POST /api/chat endpoint
- [ ] T044 Write contract tests in `backend/tests/contract/test_gemini_tools.py` verifying tool definitions match Gemini schema
- [ ] T045 Write component tests in `frontend/tests/components/ChatInterface.test.tsx` for message rendering
- [ ] T046 Write hook tests in `frontend/tests/hooks/useChat.test.ts` for chat state management
- [ ] T047 E2E test: User submits "Show me sales for last month" and verifies response with metrics and visualizations

---

## Phase 4: User Story 2 - Real-Time Dashboard Updates (P1)

**Goal**: Enable streaming responses with progressive visualization rendering as AI processes queries

**Independent Test Criteria**:
- [ ] Streaming response begins within 2 seconds of query submission
- [ ] Partial visualizations render progressively as response streams
- [ ] Charts and metrics update in real-time without blocking user interaction
- [ ] Complete visualizations render once response finishes within <10 seconds

### WebSocket Infrastructure

- [ ] T048 [P] Create WebSocket endpoint `/ws/chat/:session_id` in `backend/src/api/routes/chat.py` handling bidirectional streaming
- [ ] T049 Create WebSocket connection manager in `backend/src/services/websocket_manager.py` managing active client connections
- [ ] T050 [P] Implement message streaming logic for progressive visualization updates
- [ ] T051 Create WebSocket client in `frontend/src/services/websocket.ts` connecting to stream endpoint

### Streaming Response Format

- [ ] T052 Define streaming message schema in `backend/contracts/websocket-schema.json`:
  - Message type: "text_chunk", "visualization", "metadata", "complete", "error"
  - Payload structure for each message type with visualization metadata
- [ ] T053 [P] Implement chunked response formatter in `backend/src/services/gemini_service.py` converting Gemini stream to message format
- [ ] T054 Create useStreamingResponse hook in `frontend/src/hooks/useStreamingResponse.ts` handling progressive message rendering

### Frontend Streaming UI

- [ ] T055 [P] Implement progressive visualization rendering in VisualizationPanel component with loading states
- [ ] T056 [P] Create loading indicator component for streaming responses
- [ ] T057 [P] Implement real-time chart updates using Chart.js/Recharts ref updates for smooth animation
- [ ] T058 Create streaming status display (processing, chunks received, ETA)

### Testing for US2

- [ ] T059 Write unit tests in `backend/tests/unit/test_websocket_manager.py` for connection management
- [ ] T060 Write integration tests in `backend/tests/integration/test_websocket.py` verifying streaming message flow
- [ ] T061 Write component tests in `frontend/tests/components/VisualizationPanel.test.tsx` for progressive rendering
- [ ] T062 E2E test: Submit query and verify first visualization appears within 2 seconds, complete in <10 seconds

---

## Phase 5: User Story 3 - Multi-Turn Analytics Conversations (P1)

**Goal**: Enable context-aware follow-up questions maintaining conversation state across messages

**Independent Test Criteria**:
- [ ] User asks "Which products have high returns?" then "Show me the reasons for returns" and AI understands scope from first message
- [ ] Multi-turn conversation with "Compare to last month" correctly infers previous context
- [ ] Topic switches reset context appropriately for new analysis
- [ ] Context accuracy: 95% of follow-up questions understood correctly

### Conversation Context Management

- [ ] T063 [P] Implement conversation context manager in `backend/src/services/context_manager.py` maintaining message history per session
- [ ] T064 [P] Create context formatter in `backend/src/services/query_handler.py` building full message history for Gemini API calls
- [ ] T065 Create session state service in `backend/src/services/session_service.py` managing active sessions and context lifecycle
- [ ] T066 Implement context reset logic detecting topic changes and clearing irrelevant context

### API Enhancements for Multi-Turn

- [ ] T067 [P] Update POST `/api/chat` endpoint to accept optional `session_id` parameter for continuing conversations
- [ ] T068 [P] Create GET `/api/conversations/:id` endpoint in `backend/src/api/routes/conversation.py` retrieving conversation history
- [ ] T069 Create Pydantic schema for conversation history response in `backend/src/api/schemas/conversation.py`

### Frontend Multi-Turn Support

- [ ] T070 [P] Update useChat hook in `frontend/src/hooks/useChat.ts` to manage session_id and send with each query
- [ ] T071 [P] Implement conversation history display in ChatInterface component showing all prior messages
- [ ] T072 Create "New Conversation" button in `frontend/src/components/ChatInterface.tsx` initializing fresh session
- [ ] T073 [P] Implement session persistence in frontend localStorage preventing loss on page refresh

### Context Accuracy Improvements

- [ ] T074 Add system prompt engineering in `backend/src/services/gemini_service.py` instructing Gemini on context handling
- [ ] T075 Implement context relevance scoring to identify when user switches topics
- [ ] T076 Create clarification prompt generation for ambiguous references (e.g., "those products" → list options)

### Testing for US3

- [ ] T077 Write unit tests in `backend/tests/unit/test_context_manager.py` for message history management
- [ ] T078 Write integration tests in `backend/tests/integration/test_context_management.py` for multi-turn accuracy
- [ ] T079 Write component tests in `frontend/tests/components/ConversationHistory.test.tsx` for history display
- [ ] T080 E2E test: 3-turn conversation with context carried through each question

---

## Phase 6: User Story 4 - Actionable Data Insights (P2)

**Goal**: Provide AI-generated recommendations based on inventory and sales data analysis

**Independent Test Criteria**:
- [ ] System returns 3+ actionable recommendations (reorder, discontinue, promote) with reasoning for inventory analysis
- [ ] Sales trend analysis generates 2-3 strategic recommendations
- [ ] Profitability analysis identifies high-margin products for marketing focus

### Advanced Tool Definitions

- [ ] T081 [P] Add new tool definitions in `backend/src/services/tool_definitions.py`:
  - `analyze_inventory_health()` → returns low stock alerts, reorder recommendations
  - `analyze_sales_trends(days: int)` → identifies declining/growing categories
  - `analyze_profitability()` → calculates margins, identifies high-value products
- [ ] T082 [P] Implement tool executors for each analysis tool accessing appropriate data sources

### Recommendation Engine

- [ ] T083 Create recommendation engine in `backend/src/services/recommendation_engine.py` generating actionable insights
- [ ] T084 Implement business rules in `backend/src/utils/business_rules.py` for reorder thresholds, profitability targets
- [ ] T085 Create insight formatter in `backend/src/services/query_handler.py` converting analysis to human-readable recommendations

### Frontend Insights Display

- [ ] T086 Create RecommendationPanel component in `frontend/src/components/RecommendationPanel.tsx` displaying insights
- [ ] T087 Implement insight visualization (cards showing recommendation, justification, impact)
- [ ] T088 Create insight action buttons (e.g., "Create PO for reorder recommendation")

### Testing for US4

- [ ] T089 Write unit tests in `backend/tests/unit/test_recommendation_engine.py` for insight generation
- [ ] T090 Write integration tests in `backend/tests/integration/test_insights.py` verifying recommendation accuracy
- [ ] T091 E2E test: Query inventory health and verify 3+ recommendations generated with reasoning

---

## Phase 7: User Story 5 - Visual Customization and Export (P2)

**Goal**: Enable dynamic chart customization and data export in JSON/CSV formats

**Independent Test Criteria**:
- [ ] User changes chart from line to bar and visualization updates within 1 second
- [ ] Export to JSON includes all visualizations and query metadata
- [ ] Export to CSV includes data tables with proper formatting
- [ ] Exported files download without errors

### Chart Customization

- [ ] T092 [P] Implement chart type selector in VisualizationPanel component (line, bar, area, pie options)
- [ ] T093 [P] Create chart configuration hook in `frontend/src/hooks/useChartConfig.ts` managing visualization preferences
- [ ] T094 [P] Implement date range picker for filtering visualization data
- [ ] T095 Implement chart re-rendering on configuration changes using Recharts ref updates

### Export Functionality

- [ ] T096 Create ExportButton component in `frontend/src/components/ExportButton.tsx` with format selector (JSON, CSV)
- [ ] T097 Create export service in `frontend/src/services/export.ts` preparing data for download
- [ ] T098 [P] Implement JSON export function serializing dashboard state (visualizations, queries, results)
- [ ] T099 [P] Implement CSV export function converting data tables to CSV format
- [ ] T100 Create GET `/api/export/:session_id?format=json|csv` endpoint in `backend/src/api/routes/export.py`
- [ ] T101 [P] Implement server-side JSON/CSV generation in `backend/src/services/export_service.py`

### Frontend Export UI

- [ ] T102 Create export confirmation dialog with format selection
- [ ] T103 [P] Implement file download triggering in browser
- [ ] T104 Add export success notification (toast/snackbar)

### Testing for US5

- [ ] T105 Write unit tests in `backend/tests/unit/test_export_service.py` for JSON/CSV generation
- [ ] T106 Write integration tests in `backend/tests/integration/test_export.py` for endpoint functionality
- [ ] T107 Write component tests in `frontend/tests/components/ExportButton.test.tsx` for UI interaction
- [ ] T108 E2E test: Export as JSON and CSV, verify file content and format

---

## Phase 8: Edge Cases & Error Handling

### Out-of-Domain Query Handling

- [ ] T109 Implement out-of-domain detection in `backend/src/services/query_handler.py`
- [ ] T110 Create relevant query suggestions when user asks off-topic questions
- [ ] T111 Test: User asks "What's the weather?" system gracefully declines and suggests inventory/sales queries

### Data Unavailability Handling

- [ ] T112 [P] Implement cached data fallback in `backend/src/services/tool_executor.py`
- [ ] T113 [P] Create timestamp notification showing data freshness
- [ ] T114 Test: System unavailable, system returns cached data with "last updated X hours ago" message

### Query Timeout Handling

- [ ] T115 Implement 30-second timeout with partial response streaming in `backend/src/services/gemini_service.py`
- [ ] T116 Create timeout error message and partial result display in frontend
- [ ] T117 Test: Complex query takes >30s, system streams intermediate results then timeout message

### Ambiguous Product Names

- [ ] T118 Implement product name disambiguation in `backend/src/services/tool_executor.py`
- [ ] T119 Create clarification UI component displaying matching options in `frontend/src/components/Disambiguator.tsx`
- [ ] T120 Test: Query with ambiguous product name, system asks for clarification with options

### Unsupported Input Types

- [ ] T121 Implement file/image upload rejection in frontend
- [ ] T122 Create helpful message explaining text-only support
- [ ] T123 Test: User uploads image, system acknowledges and explains text-only limitation

---

## Phase 9: Performance Optimization & Rate Limiting

### Response Time Optimization

- [ ] T124 [P] Profile Gemini API calls using APM tools (CloudTracing, Datadog)
- [ ] T125 [P] Optimize database queries for inventory/sales data retrieval
- [ ] T126 Implement response caching for repeated queries in `backend/src/services/cache_service.py`
- [ ] T127 Implement lazy loading for visualization data in frontend

### Rate Limiting Validation

- [ ] T128 [P] Create rate limiter tests in `backend/tests/unit/test_rate_limiter.py` verifying 50/hour enforcement
- [ ] T129 [P] Implement rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] T130 Create rate limit warning UI component in `frontend/src/components/RateLimitWarning.tsx`
- [ ] T131 Display remaining queries in frontend UI

### Concurrency Testing

- [ ] T132 Load test backend supporting 10+ concurrent users with Apache JMeter
- [ ] T133 Test WebSocket stability under concurrent streaming messages
- [ ] T134 Verify database connection pooling doesn't exhaust under load

---

## Phase 10: Security & Compliance

### Query Sanitization

- [ ] T135 [P] Implement SQL injection prevention in `backend/src/services/tool_executor.py`
- [ ] T136 [P] Add input validation for all tool call parameters
- [ ] T137 Create security tests in `backend/tests/contract/test_security.py` for injection attacks

### Data Privacy

- [ ] T138 [P] Encrypt sensitive data at rest (PII, API keys) in PostgreSQL
- [ ] T139 [P] Implement TLS for data in transit (HTTPS, WSS)
- [ ] T140 Create GDPR-compliant data deletion in conversation archival process

### Audit Logging

- [ ] T141 [P] Log all tool calls with results in `backend/src/services/tool_call_logger.py`
- [ ] T142 [P] Implement query history retention (30-day user conversations + indefinite audit logs)
- [ ] T143 Create audit log export functionality for compliance reviews

### Authentication & Authorization

- [ ] T144 [P] Verify inherited auth properly restricts data based on user role
- [ ] T145 Create authorization tests in `backend/tests/integration/test_authorization.py`
- [ ] T146 Implement role-based query filtering preventing unauthorized data access

---

## Phase 11: Documentation & Deployment

### Developer Documentation

- [ ] T147 [P] Create API documentation in `backend/openapi.yaml` (auto-generated from FastAPI)
- [ ] T148 [P] Create deployment guide in `DEPLOYMENT.md` for staging/production
- [ ] T149 Create troubleshooting guide for common issues (Gemini API errors, database connections)
- [ ] T150 Create architecture diagram showing component interactions

### Local Development

- [ ] T151 Update `quickstart.md` with:
  - Environment setup steps
  - Database initialization
  - Running local services
  - Testing the full flow locally
- [ ] T152 Create `.env.example` files with all required variables and instructions

### Deployment Preparation

- [ ] T153 [P] Create Dockerfile for backend service
- [ ] T154 [P] Create docker-compose.yml for local development with PostgreSQL, Redis
- [ ] T155 [P] Setup environment variables for staging environment
- [ ] T156 [P] Create database backup/restore procedures
- [ ] T157 Create monitoring dashboard (Grafana) for production metrics

---

## Task Summary & Metrics

**Total Tasks**: 157

**Task Distribution**:
- Phase 1 (Setup): 10 tasks
- Phase 2 (Foundational): 12 tasks
- Phase 3 (US1 - Natural Language): 24 tasks
- Phase 4 (US2 - Real-Time): 15 tasks
- Phase 5 (US3 - Multi-Turn): 18 tasks
- Phase 6 (US4 - Insights): 11 tasks
- Phase 7 (US5 - Export): 17 tasks
- Phase 8 (Edge Cases): 15 tasks
- Phase 9 (Performance): 11 tasks
- Phase 10 (Security): 12 tasks
- Phase 11 (Docs): 11 tasks

**Task Markers**:
- [P] Parallelizable tasks: 76 tasks (can run independently)
- [US#] User story tasks: 85 tasks (broken down by story)

**MVP Tasks** (User Stories 1-3):
- Setup & Infrastructure: 10 tasks (Phase 1)
- Foundational Components: 12 tasks (Phase 2)
- US1 (Natural Language): 24 tasks (Phase 3)
- US2 (Real-Time): 15 tasks (Phase 4)
- US3 (Multi-Turn): 18 tasks (Phase 5)
- **MVP Total**: 79 tasks

**Post-MVP Tasks** (User Stories 4-5 + Polish):
- US4 (Insights): 11 tasks (Phase 6)
- US5 (Export): 17 tasks (Phase 7)
- Edge Cases: 15 tasks (Phase 8)
- Performance: 11 tasks (Phase 9)
- Security: 12 tasks (Phase 10)
- Documentation: 11 tasks (Phase 11)
- **Post-MVP Total**: 77 tasks

---

## Execution Strategy

### Recommended Execution Order

1. **Setup Phase (Phase 1)**: Complete all infrastructure tasks (T001-T010) sequentially
   - Enables all downstream phases

2. **Foundation Phase (Phase 2)**: Complete database, auth, logging (T011-T023) in parallel where marked [P]
   - Prerequisite for all user story phases

3. **MVP Delivery (Phases 3-5)**: Execute user stories in parallel:
   - **Parallel US1 + US2**: US2 depends on US1 chat endpoint, start after T029
   - **US3 Independent**: Can run in parallel with US2 after T011-T023 complete

4. **Post-MVP (Phases 6-11)**: Execute sequentially after MVP release or in parallel if resources available

### Parallel Execution Example (MVP)

```
Timeline:
Day 1-2: Phase 1 (Setup) - T001-T010 sequentially
Day 3-4: Phase 2 (Foundations) - T011-T023 [P] parallel where marked
Day 5-9:
  - US1 Phase 3: T024-T047 (Gemini + Chat)
  - US2 Phase 4: T048-T062 (WebSocket + Streaming) - starts after T029
  - US3 Phase 5: T063-T080 (Context) - starts after T011-T023
Day 10: Integration & Testing
Day 11: MVP Release
```

### Test-Driven Development (TDD)

Each phase includes test tasks organized as:
1. Write test (RED)
2. Implement feature (GREEN)
3. Refactor (REFACTOR)

Example for US1 (Tasks T024-T047):
- Write tests first: T042-T047 (unit, integration, e2e)
- Implement features: T024-T041
- Refactor for performance & clarity

### Definition of Done (Per Phase)

- ✅ All tests in phase passing (80%+ coverage for backend)
- ✅ Code review approved by at least one team member
- ✅ Constitution compliance verified
- ✅ All acceptance criteria from spec met
- ✅ Performance targets met (latency, throughput)
- ✅ Security review passed
- ✅ Documentation updated

---

## Dependencies & Blockers

### Critical Dependencies

1. **Database Setup (T006, T011-T016)** → Required before API endpoints
2. **Authentication (T017-T020)** → Required before protected endpoints
3. **Gemini Integration (T024-T028)** → Required for all AI features
4. **Chat Endpoint (T029-T031)** → Required for US2 (WebSocket depends on it)

### No Blockers

- US1, US2, US3 can start in parallel after Phase 2
- Frontend components can be built in parallel with backend API development
- All parallelizable tasks ([P]) have no dependencies on sequential tasks in same phase

---

## Success Criteria

**MVP Release Gates**:
- [ ] US1 complete: Natural language → visualization pipeline working
- [ ] US2 complete: Real-time streaming with <2 second first response
- [ ] US3 complete: Multi-turn context maintained with 95% accuracy
- [ ] All acceptance scenarios from spec passing
- [ ] 80%+ test coverage for backend
- [ ] Zero security vulnerabilities
- [ ] Performance targets met (10s initial, 2s streaming start, 5s queries 90% of time)

---

## Notes

- Tests marked as optional per constitution (can implement TDD or post-development)
- All tasks use absolute file paths for clarity
- [P] markers enable parallel execution planning
- Edge cases (Phase 8) can be deprioritized post-MVP
- Security tasks (Phase 10) should not be deferred - complete as part of MVP
