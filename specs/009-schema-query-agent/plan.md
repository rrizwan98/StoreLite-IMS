# Implementation Plan: Schema Query Agent

**Version:** 1.0
**Date:** December 15, 2025
**Spec Reference:** `specs/009-schema-query-agent/spec.md`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │   Service   │  │   Schema    │  │   Schema    │  │  Schema Analytics  ││
│  │  Selection  │──│   Connect   │──│    Agent    │──│    Dashboard       ││
│  │   (Update)  │  │   (New)     │  │   (New)     │  │      (New)         ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │   /schema-agent/*   │  │   Schema Discovery  │  │   Schema Query      │ │
│  │   Router (New)      │──│   Service (New)     │──│   Agent (New)       │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         MCP Client (Updated)                            ││
│  │                    (Connects to PostgreSQL MCP Server)                  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ MCP Protocol
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL MCP SERVER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐│
│  │ list_tables  │  │describe_table│  │execute_query │  │  refresh_schema  ││
│  │    Tool      │  │    Tool      │  │   Tool       │  │      Tool        ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘│
│                                      │                                      │
│                           READ-ONLY ENFORCEMENT                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ SSL Connection
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        USER'S POSTGRESQL DATABASE                           │
│                         (Existing Schema - Untouched)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Backend Infrastructure

**Goal:** Create core backend components for schema discovery and query execution.

#### 1.1 Database Model Updates
- Add `SCHEMA_QUERY_ONLY` to `ConnectionType` enum
- Add `connection_mode` column to `user_connections`
- Add `schema_metadata` JSONB column
- Add `allowed_schemas` array column
- Create migration script

#### 1.2 Schema Discovery Service
- Create `backend/app/services/schema_discovery.py`
- Implement `discover_schema()` function
- Implement `get_table_info()` function
- Implement `get_relationships()` function
- Implement `cache_schema()` function

#### 1.3 Schema Query MCP Tools
- Create `backend/app/mcp_server/tools_schema_query.py`
- Implement `list_tables` tool
- Implement `describe_table` tool
- Implement `execute_select_query` tool with validation
- Implement `get_sample_data` tool
- Implement `get_table_stats` tool

#### 1.4 Schema Query Router
- Create `backend/app/routers/schema_agent.py`
- Implement `/connect` endpoint
- Implement `/discover-schema` endpoint
- Implement `/schema` endpoint (GET)
- Implement `/refresh-schema` endpoint
- Implement `/status` endpoint
- Implement `/disconnect` endpoint

---

### Phase 2: AI Agent Implementation

**Goal:** Create schema-aware AI agent with natural language query capability.

#### 2.1 Schema Query Agent
- Create `backend/app/agents/schema_query_agent.py`
- Implement `SchemaQueryAgent` class
- Generate dynamic system prompt from schema
- Implement query intent detection
- Implement SQL generation with schema context
- Add query validation (SELECT only)

#### 2.2 ChatKit Integration
- Implement `/schema-agent/chatkit` streaming endpoint
- Configure agent with schema metadata
- Add conversation history persistence
- Support visualization suggestions

#### 2.3 Security Layer
- Implement query validation middleware
- Add rate limiting per user
- Implement query timeout handling
- Add audit logging for queries

---

### Phase 3: Frontend Implementation

**Goal:** Create UI for schema connection and agent interaction.

#### 3.1 Service Selection Update
- Update `/dashboard/page.tsx` with third option
- Add "Agent + Analytics Only" card
- Update connection type handling
- Route to schema-connect page

#### 3.2 Schema Connect Page
- Create `/dashboard/schema-connect/page.tsx`
- Database URI input form
- Connection test functionality
- Schema preview display
- Allowed schemas configuration (optional)

#### 3.3 Schema Agent Page
- Create `/dashboard/schema-agent/page.tsx`
- ChatKit integration for agent chat
- Schema browser sidebar
- SQL preview panel
- Results display area

#### 3.4 Schema Analytics Page
- Create `/dashboard/schema-analytics/page.tsx`
- Visualization components
- Query history
- Export functionality

#### 3.5 Dashboard Layout Updates
- Conditional navigation based on connection_mode
- Hide Admin/POS for schema_query_only users
- Add schema browser toggle

---

### Phase 4: Integration & Testing

**Goal:** End-to-end integration and security testing.

#### 4.1 Integration Tests
- Connection flow tests
- Schema discovery tests
- Query execution tests
- ChatKit streaming tests

#### 4.2 Security Tests
- Query injection tests
- Write operation rejection tests
- Rate limit tests
- Timeout tests

#### 4.3 End-to-End Tests
- Full user flow testing
- Cross-browser testing
- Error handling verification

---

## Key Technical Decisions

### 1. PostgreSQL MCP Server Approach

**Decision:** Use separate MCP server instance per user connection.

**Rationale:**
- Isolation between users
- Independent connection management
- Easier to implement read-only enforcement
- Better error isolation

**Implementation:**
```python
# Each user gets dedicated MCP client
user_mcp_clients: dict[int, MCPClient] = {}

async def get_user_mcp_client(user_id: int, database_uri: str) -> MCPClient:
    if user_id not in user_mcp_clients:
        client = MCPClient()
        await client.connect_postgres(database_uri, read_only=True)
        user_mcp_clients[user_id] = client
    return user_mcp_clients[user_id]
```

### 2. Query Validation Strategy

**Decision:** Multi-layer validation.

**Layers:**
1. **Regex Pre-check:** Quick rejection of obvious non-SELECT
2. **SQL Parser:** Parse query AST for statement type
3. **MCP Server:** Final validation at execution layer

```python
def validate_query(query: str) -> bool:
    # Layer 1: Quick check
    normalized = query.strip().upper()
    if not normalized.startswith("SELECT"):
        return False

    # Layer 2: Check for dangerous patterns
    dangerous_patterns = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
    for pattern in dangerous_patterns:
        if pattern in normalized:
            return False

    # Layer 3: SQL parser validation
    try:
        parsed = sqlparse.parse(query)[0]
        if parsed.get_type() != "SELECT":
            return False
    except:
        return False

    return True
```

### 3. Schema Caching Strategy

**Decision:** Cache in database with configurable TTL.

**Implementation:**
- Store schema in `user_connections.schema_metadata` (JSONB)
- TTL: 1 hour default (configurable)
- Manual refresh option available
- Refresh on significant query errors

### 4. Agent Model Selection

**Decision:** Use same model as existing agent (Gemini 2.0 Flash Lite).

**Rationale:**
- Consistency with existing system
- Proven performance
- Cost effective
- Good SQL generation capability

---

## File Structure

```
backend/app/
├── routers/
│   ├── schema_agent.py              # NEW: Schema agent endpoints
│   └── ... (existing)
├── agents/
│   ├── schema_query_agent.py        # NEW: Schema-aware agent
│   └── ... (existing)
├── mcp_server/
│   ├── tools_schema_query.py        # NEW: Schema query tools
│   └── ... (existing)
├── services/
│   ├── schema_discovery.py          # NEW: Schema discovery
│   └── ... (existing)
└── models.py                         # UPDATE: New enum, columns

frontend/app/
├── dashboard/
│   ├── page.tsx                      # UPDATE: Third option
│   ├── schema-connect/
│   │   └── page.tsx                  # NEW: Connection page
│   ├── schema-agent/
│   │   └── page.tsx                  # NEW: Agent chat page
│   └── schema-analytics/
│       └── page.tsx                  # NEW: Analytics page
└── components/
    └── schema-agent/
        ├── SchemaViewer.tsx          # NEW: Schema browser
        ├── QueryHistory.tsx          # NEW: Query history
        ├── SQLPreview.tsx            # NEW: SQL display
        └── ResultsTable.tsx          # NEW: Results display
```

---

## Dependencies

### Backend
```python
# No new dependencies required
# Using existing:
# - asyncpg (PostgreSQL)
# - sqlparse (SQL parsing - already available or add)
# - fastmcp (MCP server)
```

### Frontend
```json
{
  "react-syntax-highlighter": "^15.5.0"  // For SQL highlighting
}
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SQL injection | Multi-layer validation + parameterized queries |
| Query timeout | 30s timeout with cancellation |
| Large result sets | Pagination + row limit (10K) |
| Schema changes | Refresh mechanism + error prompts |
| Connection exhaustion | Connection pooling (5 per user) |
| Data exposure | Schema filtering + allowed_schemas |

---

## Success Criteria

- [ ] User can connect existing PostgreSQL database
- [ ] No tables created in user's database
- [ ] Natural language queries work accurately
- [ ] Only SELECT queries executed
- [ ] Schema displayed correctly
- [ ] Visualizations generated from results
- [ ] Rate limiting enforced
- [ ] Query timeouts working
- [ ] Connection security (SSL) enforced
