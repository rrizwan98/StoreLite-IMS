# Tasks: Schema Query Agent Implementation

**Version:** 1.0
**Date:** December 15, 2025
**Spec Reference:** `specs/009-schema-query-agent/spec.md`
**Plan Reference:** `specs/009-schema-query-agent/plan.md`

---

## Task Overview

| Phase | Tasks | Priority |
|-------|-------|----------|
| Phase 1: Backend Infrastructure | 8 tasks | P0 |
| Phase 2: AI Agent | 6 tasks | P0 |
| Phase 3: Frontend | 10 tasks | P1 |
| Phase 4: Testing | 5 tasks | P1 |

---

## Phase 1: Backend Infrastructure

### Task 1.1: Update Database Models
**Priority:** P0
**File:** `backend/app/models.py`

- [ ] Add `SCHEMA_QUERY_ONLY = "schema_query_only"` to `ConnectionType` enum
- [ ] Add `connection_mode` column to `UserConnection` (default: 'full_ims')
- [ ] Add `schema_metadata` JSONB column to `UserConnection`
- [ ] Add `schema_last_updated` TIMESTAMP column
- [ ] Add `allowed_schemas` TEXT[] column (default: ['public'])

**Acceptance:** Model changes apply without breaking existing functionality.

---

### Task 1.2: Create Database Migration
**Priority:** P0
**File:** `backend/migrations/` or inline in database.py

- [ ] Create migration for new columns
- [ ] Handle existing `user_connections` rows
- [ ] Test migration on dev database
- [ ] Document rollback procedure

**Acceptance:** Migration runs cleanly on existing database.

---

### Task 1.3: Create Schema Discovery Service
**Priority:** P0
**File:** `backend/app/services/schema_discovery.py` (NEW)

- [ ] Implement `async def discover_schema(database_uri: str) -> dict`
- [ ] Implement `async def get_tables(conn) -> list[dict]`
- [ ] Implement `async def get_columns(conn, table_name: str) -> list[dict]`
- [ ] Implement `async def get_foreign_keys(conn) -> list[dict]`
- [ ] Implement `async def get_table_stats(conn, table_name: str) -> dict`
- [ ] Implement `async def format_schema_metadata(tables, columns, fks) -> dict`

**Acceptance:** Service returns complete schema metadata from any PostgreSQL database.

---

### Task 1.4: Create Schema Query MCP Tools
**Priority:** P0
**File:** `backend/app/mcp_server/tools_schema_query.py` (NEW)

- [ ] Implement `@mcp.tool() list_tables(schema: str = "public") -> list[dict]`
- [ ] Implement `@mcp.tool() describe_table(table_name: str) -> dict`
- [ ] Implement `@mcp.tool() execute_select_query(query: str) -> dict`
- [ ] Implement `@mcp.tool() get_sample_data(table_name: str, limit: int = 10) -> list[dict]`
- [ ] Implement `@mcp.tool() get_table_stats(table_name: str) -> dict`
- [ ] Implement `@mcp.tool() refresh_schema() -> dict`
- [ ] Add query validation (SELECT only)
- [ ] Add query timeout handling (30s)
- [ ] Add row limit enforcement (10K)

**Acceptance:** All tools work correctly with read-only enforcement.

---

### Task 1.5: Create Schema Agent Router
**Priority:** P0
**File:** `backend/app/routers/schema_agent.py` (NEW)

Endpoints to implement:
- [ ] `POST /schema-agent/connect` - Connect with schema mode
- [ ] `POST /schema-agent/discover-schema` - Discover database schema
- [ ] `GET /schema-agent/schema` - Get cached schema metadata
- [ ] `POST /schema-agent/refresh-schema` - Force schema refresh
- [ ] `GET /schema-agent/status` - Get connection status
- [ ] `DELETE /schema-agent/disconnect` - Disconnect from database

Request/Response schemas:
- [ ] Create `SchemaConnectRequest` Pydantic model
- [ ] Create `SchemaConnectResponse` Pydantic model
- [ ] Create `SchemaMetadataResponse` Pydantic model
- [ ] Create `QueryRequest` Pydantic model
- [ ] Create `QueryResponse` Pydantic model

**Acceptance:** All endpoints return correct responses with proper error handling.

---

### Task 1.6: Register Router in Main App
**Priority:** P0
**File:** `backend/app/main.py`

- [ ] Import `schema_agent` router
- [ ] Add router with prefix `/schema-agent`
- [ ] Add appropriate middleware/dependencies

**Acceptance:** Router accessible at `/schema-agent/*`.

---

### Task 1.7: Create Query Validation Utility
**Priority:** P0
**File:** `backend/app/services/query_validator.py` (NEW)

- [ ] Implement `def validate_select_query(query: str) -> bool`
- [ ] Check query starts with SELECT
- [ ] Check no dangerous keywords (INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE)
- [ ] Optionally use SQL parser for deeper validation
- [ ] Return detailed error message on failure

**Acceptance:** Rejects all write operations, accepts valid SELECT queries.

---

### Task 1.8: Update MCP Server Registration
**Priority:** P0
**File:** `backend/app/mcp_server/server.py`

- [ ] Import schema query tools
- [ ] Register tools with MCP server
- [ ] Handle user-specific database connections

**Acceptance:** Schema query tools available via MCP.

---

## Phase 2: AI Agent Implementation

### Task 2.1: Create Schema Query Agent Class
**Priority:** P0
**File:** `backend/app/agents/schema_query_agent.py` (NEW)

- [ ] Create `SchemaQueryAgent` class
- [ ] Implement `__init__(self, user_id: int, schema_metadata: dict)`
- [ ] Implement `async def initialize(self, database_uri: str)`
- [ ] Implement MCP client connection
- [ ] Store schema context

**Acceptance:** Agent initializes with schema context.

---

### Task 2.2: Implement Dynamic System Prompt
**Priority:** P0
**File:** `backend/app/agents/schema_query_agent.py`

- [ ] Implement `def _generate_system_prompt(self) -> str`
- [ ] Include all tables and columns
- [ ] Include relationships
- [ ] Include query rules (SELECT only)
- [ ] Include visualization suggestions

**Acceptance:** System prompt accurately describes user's schema.

---

### Task 2.3: Implement Query Processing
**Priority:** P0
**File:** `backend/app/agents/schema_query_agent.py`

- [ ] Implement `async def process_query(self, natural_query: str) -> QueryResult`
- [ ] Generate SQL from natural language
- [ ] Validate generated SQL
- [ ] Execute via MCP tools
- [ ] Format results
- [ ] Suggest visualizations

**Acceptance:** Natural language queries return correct SQL and results.

---

### Task 2.4: Implement ChatKit Streaming Endpoint
**Priority:** P0
**File:** `backend/app/routers/schema_agent.py`

- [ ] Implement `POST /schema-agent/chatkit` endpoint
- [ ] Configure streaming response
- [ ] Integrate with SchemaQueryAgent
- [ ] Handle conversation history
- [ ] Support structured data responses

**Acceptance:** ChatKit streaming works with schema agent.

---

### Task 2.5: Add Conversation History Persistence
**Priority:** P1
**File:** `backend/app/agents/schema_query_agent.py`

- [ ] Use existing `ConversationHistory` model
- [ ] Store user queries and agent responses
- [ ] Store generated SQL
- [ ] Enable context across sessions

**Acceptance:** Conversation persists across page refreshes.

---

### Task 2.6: Add Rate Limiting
**Priority:** P1
**File:** `backend/app/routers/schema_agent.py`

- [ ] Add rate limiter middleware
- [ ] 60 queries per minute per user
- [ ] Return 429 with retry-after header

**Acceptance:** Rate limiting enforced correctly.

---

## Phase 3: Frontend Implementation

### Task 3.1: Update Service Selection Page
**Priority:** P1
**File:** `frontend/app/dashboard/page.tsx`

- [ ] Add third option card: "Agent + Analytics Only"
- [ ] Include description and feature list
- [ ] Include limitations (no Admin, no POS)
- [ ] Handle selection and routing

**Acceptance:** Three options displayed, routing works correctly.

---

### Task 3.2: Update Auth Context
**Priority:** P1
**File:** `frontend/lib/auth-context.tsx`

- [ ] Add `connection_mode` to connection status
- [ ] Update `chooseConnection` to support new mode
- [ ] Add schema metadata to context if needed

**Acceptance:** Context correctly tracks schema_query_only mode.

---

### Task 3.3: Update Auth API
**Priority:** P1
**File:** `frontend/lib/auth-api.ts`

- [ ] Add `connectSchemaOnly(databaseUri: string)` function
- [ ] Add `getSchemaMetadata()` function
- [ ] Add `refreshSchema()` function
- [ ] Add `disconnectSchema()` function

**Acceptance:** API functions work correctly.

---

### Task 3.4: Create Schema Connect Page
**Priority:** P1
**File:** `frontend/app/dashboard/schema-connect/page.tsx` (NEW)

- [ ] Database URI input form
- [ ] Test connection button
- [ ] Schema preview component
- [ ] Allowed schemas selector (optional)
- [ ] Connect button
- [ ] Error handling

**Acceptance:** User can connect their database.

---

### Task 3.5: Create Schema Viewer Component
**Priority:** P1
**File:** `frontend/components/schema-agent/SchemaViewer.tsx` (NEW)

- [ ] Tree view of tables
- [ ] Expandable columns
- [ ] Show data types
- [ ] Show foreign key relationships
- [ ] Refresh button

**Acceptance:** Schema displayed in readable tree format.

---

### Task 3.6: Create Schema Agent Page
**Priority:** P1
**File:** `frontend/app/dashboard/schema-agent/page.tsx` (NEW)

- [ ] ChatKit integration
- [ ] Schema browser sidebar (collapsible)
- [ ] Query input area
- [ ] Results display
- [ ] SQL preview toggle

**Acceptance:** Full chat interface with schema context.

---

### Task 3.7: Create SQL Preview Component
**Priority:** P2
**File:** `frontend/components/schema-agent/SQLPreview.tsx` (NEW)

- [ ] SQL syntax highlighting
- [ ] Copy to clipboard
- [ ] Expandable/collapsible

**Acceptance:** Generated SQL displayed with highlighting.

---

### Task 3.8: Create Results Table Component
**Priority:** P1
**File:** `frontend/components/schema-agent/ResultsTable.tsx` (NEW)

- [ ] Data table with pagination
- [ ] Column sorting
- [ ] Export to CSV option
- [ ] Handle large datasets

**Acceptance:** Query results displayed in table format.

---

### Task 3.9: Create Schema Analytics Page
**Priority:** P2
**File:** `frontend/app/dashboard/schema-analytics/page.tsx` (NEW)

- [ ] Query-based visualizations
- [ ] Chart components (bar, line, pie)
- [ ] Query history
- [ ] Saved queries (optional)

**Acceptance:** Analytics visualizations work from queries.

---

### Task 3.10: Update Dashboard Layout
**Priority:** P1
**File:** `frontend/app/dashboard/layout.tsx`

- [ ] Conditional navigation based on connection_mode
- [ ] Hide Admin link for schema_query_only
- [ ] Hide POS link for schema_query_only
- [ ] Show Schema Agent link
- [ ] Show Schema Analytics link

**Acceptance:** Navigation reflects user's connection mode.

---

## Phase 4: Testing & Security

### Task 4.1: Write Unit Tests - Schema Discovery
**Priority:** P1
**File:** `backend/tests/test_schema_discovery.py` (NEW)

- [ ] Test table discovery
- [ ] Test column discovery
- [ ] Test FK discovery
- [ ] Test schema caching
- [ ] Test error handling

**Acceptance:** All schema discovery tests pass.

---

### Task 4.2: Write Unit Tests - Query Validation
**Priority:** P1
**File:** `backend/tests/test_query_validator.py` (NEW)

- [ ] Test valid SELECT queries
- [ ] Test INSERT rejection
- [ ] Test UPDATE rejection
- [ ] Test DELETE rejection
- [ ] Test DROP rejection
- [ ] Test SQL injection attempts

**Acceptance:** All write operations rejected.

---

### Task 4.3: Write Integration Tests - Schema Agent
**Priority:** P1
**File:** `backend/tests/test_schema_agent.py` (NEW)

- [ ] Test connection flow
- [ ] Test query execution
- [ ] Test ChatKit streaming
- [ ] Test rate limiting

**Acceptance:** Full flow works correctly.

---

### Task 4.4: Write Security Tests
**Priority:** P0
**File:** `backend/tests/test_schema_security.py` (NEW)

- [ ] Test SQL injection prevention
- [ ] Test query type validation
- [ ] Test timeout enforcement
- [ ] Test rate limiting
- [ ] Test row limit enforcement

**Acceptance:** All security measures working.

---

### Task 4.5: End-to-End Testing
**Priority:** P1
**Manual or Playwright**

- [ ] Test full user flow (connect → query → visualize)
- [ ] Test error scenarios
- [ ] Test disconnection
- [ ] Test reconnection
- [ ] Cross-browser testing

**Acceptance:** Full flow works in all scenarios.

---

## Checklist Summary

### Must-Have (P0)
- [ ] Database model updates
- [ ] Schema discovery service
- [ ] MCP tools (read-only)
- [ ] Schema agent router
- [ ] Query validation
- [ ] Schema query agent
- [ ] ChatKit endpoint
- [ ] Security tests

### Should-Have (P1)
- [ ] Service selection UI update
- [ ] Schema connect page
- [ ] Schema agent page
- [ ] Results table
- [ ] Dashboard navigation
- [ ] Unit/integration tests
- [ ] Rate limiting

### Nice-to-Have (P2)
- [ ] SQL preview component
- [ ] Schema analytics page
- [ ] Query history
- [ ] Export functionality

---

## Definition of Done

A task is complete when:
1. Code implemented and working
2. Unit tests passing
3. No regressions in existing features
4. Code reviewed (self or peer)
5. Documentation updated if needed
6. Acceptance criteria met
