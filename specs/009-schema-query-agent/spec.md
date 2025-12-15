# Specification: Schema Query Agent (Agent + Analytics Only Mode)

**Version:** 1.0
**Date:** December 15, 2025
**Branch:** 009-schema-query-agent
**Status:** Draft

---

## 1. Goal

Introduce a new database connection approach for existing businesses that:
- Provides **AI Agent + Analytics only** (no Admin, no POS)
- **Does NOT create any tables** in user's database
- Queries user's **existing database schema** directly
- Uses **PostgreSQL MCP Server** for secure database access
- Enables natural language queries against arbitrary database schemas

---

## 2. Problem Statement

### Current Approach (Full IMS Connection)
- User provides PostgreSQL URI
- System creates inventory tables if missing
- User gets Admin + POS + Analytics
- Assumes user wants our table structure

### Gap for Existing Businesses
Many businesses already have:
- Established databases with custom schemas
- Existing tables (products, sales, customers, etc.)
- No desire to change their database structure
- Need for AI-powered querying without modifications

### Solution: Schema Query Mode
A read-only AI agent that:
- Discovers user's database schema automatically
- Answers natural language queries using existing tables
- Provides analytics visualizations from existing data
- Never modifies the database structure

---

## 3. Requirements

### 3.1 User Flow - Connection Type Selection

Update the service selection screen to offer **three options**:

| Option | Name | Services | Tables |
|--------|------|----------|--------|
| A | Use Our Database | Admin + POS + Analytics | Our tables |
| B | Full IMS Connection | Admin + POS + Analytics | Creates tables if needed |
| C | **Agent + Analytics Only** | AI Agent + Analytics | **No table creation** |

### 3.2 Option C Flow (New)

**Initial Connection:**
1. User selects "Agent + Analytics Only"
2. User provides PostgreSQL DATABASE_URI
3. System tests connection (read-only verification)
4. System discovers and caches database schema
5. User is presented with:
   - **AI Chat Agent** (for natural language queries)
   - **Analytics Dashboard** (for visualizations)
6. No Admin or POS access (grayed out or hidden)

**Returning User (Auto-Reconnect):**
1. User logs in after session expiry or logout
2. System detects existing `schema_query_only` connection config
3. System automatically reconnects using stored URI (silent)
4. If reconnection fails, show error with "Reconnect" option
5. User lands directly on Schema Agent page

**Mode Switching (Schema Query → Full IMS):**
1. User clicks "Upgrade to Full IMS" option in settings
2. System shows confirmation dialog: "This will create IMS tables (inventory_items, inventory_bills, inventory_bill_items) in your database. Continue?"
3. On confirm: Create tables, update `connection_mode` to `own_database`, unlock Admin/POS
4. On cancel: Remain in Schema Query Mode

### 3.3 Schema Discovery

On connection, the system must:

```sql
-- Discover all tables
SELECT table_name, table_schema
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema');

-- Discover columns for each table
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = '{table}' AND table_schema = '{schema}';

-- Discover relationships (foreign keys)
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

Store schema metadata in:
```sql
-- Add to user_connections table
ALTER TABLE user_connections ADD COLUMN schema_metadata JSONB;
ALTER TABLE user_connections ADD COLUMN schema_last_updated TIMESTAMP;
```

### 3.4 Schema-Aware AI Agent

#### Agent Responsibilities:
1. **Query Translation**: Convert natural language to SQL
2. **Schema Understanding**: Know all tables, columns, relationships
3. **Safe Execution**: Execute SELECT queries only (read-only)
4. **Result Formatting**: Return data in human-readable format
5. **Visualization Suggestions**: Recommend charts for data

#### Agent System Prompt (Template):
```
You are a database query assistant with access to the following schema:

{schema_metadata}

Tables:
- {table_name}: {description}
  Columns: {column_list}
  Relationships: {foreign_keys}

You can:
1. Query data using the `execute_query` tool
2. List available tables using `list_tables` tool
3. Describe table structure using `describe_table` tool

Rules:
- ONLY execute SELECT queries
- Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER
- Explain your queries before executing
- Format results clearly
- Suggest visualizations when appropriate
```

#### Agent Tools (MCP Functions):

| Tool | Purpose | Parameters |
|------|---------|------------|
| `list_tables` | Get all tables | `schema?: string` |
| `describe_table` | Get table structure | `table_name: string` |
| `execute_query` | Run SELECT query | `query: string` |
| `get_sample_data` | Preview table data | `table_name: string, limit?: number` |
| `get_relationships` | Get foreign keys | `table_name?: string` |
| `refresh_schema` | Update schema cache | - |

### 3.5 PostgreSQL MCP Server Integration

**Mandatory**: Use existing FastMCP infrastructure from project for database operations.

**Key Distinction from Full IMS Mode:**
- Full IMS Mode: Creates `inventory_items`, `inventory_bills`, `inventory_bill_items` tables
- Schema Query Mode: **Creates NO tables**. Queries user's existing tables directly.

#### Connection Flow:
```
User Query → AI Agent → MCP Client → FastMCP Server (read-only) → User's Database
```

#### MCP Server Configuration:
```python
# Reuse existing FastMCP infrastructure with read-only enforcement
# No IMS table creation - direct access to user's existing schema
schema_query_mcp = FastMCP(
    connection_uri=user.database_uri,
    read_only=True,  # CRITICAL: Enforce read-only
    schema_cache_ttl=3600  # Cache schema for 1 hour
)
```

### 3.6 Security Requirements

1. **Read-Only Enforcement**:
   - MCP server must reject non-SELECT queries
   - Database user should have SELECT-only permissions
   - Query validation before execution

2. **Query Limits**:
   - Maximum query execution time: 30 seconds
   - Maximum rows returned: 10,000
   - Rate limiting: 60 queries/minute per user

3. **Schema Access Control**:
   - Only access tables in allowed schemas
   - Exclude system schemas (pg_catalog, information_schema)
   - User can specify allowed schemas
   - **Maximum 100 tables** supported per connection
   - If table count exceeds 100, require user to filter via `allowed_schemas`

4. **Connection Security**:
   - Encrypted connection (SSL required)
   - Connection timeout: 10 seconds
   - Connection pool limit: 5 per user

---

## 4. Database Changes

### 4.1 Update UserConnection Model

```python
class ConnectionType(enum.Enum):
    OWN_DATABASE = "own_database"           # Full IMS (existing)
    OUR_DATABASE = "our_database"           # Platform DB (existing)
    SCHEMA_QUERY_ONLY = "schema_query_only" # NEW: Agent + Analytics only
```

### 4.2 New Columns for user_connections

```sql
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS
    connection_mode VARCHAR(50) DEFAULT 'full_ims';
-- Values: 'full_ims', 'schema_query_only'

ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS
    schema_metadata JSONB;

ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS
    schema_last_updated TIMESTAMP;

ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS
    allowed_schemas TEXT[] DEFAULT ARRAY['public'];
```

### 4.3 Schema Metadata Structure

```json
{
  "tables": [
    {
      "name": "products",
      "schema": "public",
      "columns": [
        {"name": "id", "type": "integer", "nullable": false, "primary_key": true},
        {"name": "name", "type": "varchar(255)", "nullable": false},
        {"name": "price", "type": "decimal(10,2)", "nullable": false},
        {"name": "category_id", "type": "integer", "nullable": true}
      ],
      "row_count_estimate": 15000,
      "relationships": [
        {"column": "category_id", "references": "categories.id"}
      ]
    }
  ],
  "discovered_at": "2025-12-15T10:30:00Z",
  "total_tables": 12,
  "version": "1.0"
}
```

---

## 5. API Endpoints

### 5.1 New Endpoints

```
POST   /schema-agent/connect           Connect with schema-only mode
POST   /schema-agent/discover-schema   Discover database schema
GET    /schema-agent/schema            Get cached schema metadata
POST   /schema-agent/refresh-schema    Force schema refresh
POST   /schema-agent/query             Execute query via agent
POST   /schema-agent/chatkit           ChatKit streaming endpoint
GET    /schema-agent/status            Get connection status
DELETE /schema-agent/disconnect        Disconnect from database
```

### 5.2 Endpoint Details

#### POST /schema-agent/connect
```json
// Request
{
  "database_uri": "postgresql://user:pass@host:5432/dbname",
  "allowed_schemas": ["public", "sales"],  // Optional
  "auto_discover_schema": true              // Default: true
}

// Response
{
  "status": "connected",
  "tables_found": 12,
  "schema_summary": {
    "schemas": ["public"],
    "table_count": 12,
    "column_count": 87
  },
  "mcp_session_id": "abc123"
}
```

#### POST /schema-agent/query
```json
// Request
{
  "query": "Show me top 10 products by sales",
  "include_sql": true,
  "visualization_hint": "bar_chart"
}

// Response
{
  "natural_response": "Here are the top 10 products by sales...",
  "sql_executed": "SELECT p.name, SUM(s.quantity) as total_sales...",
  "data": [...],
  "visualization": {
    "type": "bar_chart",
    "config": {...}
  }
}
```

#### POST /schema-agent/chatkit
```
Same structure as existing ChatKit endpoint
Streaming response with schema-aware agent
```

---

## 6. Frontend Changes

### 6.1 Service Selection Update

**File**: `frontend/app/dashboard/page.tsx`

Add third option:
```tsx
<ServiceOption
  id="schema_query_only"
  title="Agent + Analytics Only"
  description="Connect your existing database. AI agent queries your data without modifying anything."
  icon={<BrainIcon />}
  features={[
    "AI-powered natural language queries",
    "Analytics dashboard",
    "No table modifications",
    "Works with any PostgreSQL schema"
  ]}
  limitations={[
    "No Admin interface",
    "No POS system"
  ]}
/>
```

### 6.2 New Pages

| Route | Page | Purpose |
|-------|------|---------|
| `/dashboard/schema-connect` | SchemaConnectPage | DB connection for schema mode |
| `/dashboard/schema-agent` | SchemaAgentPage | AI Chat interface |
| `/dashboard/schema-analytics` | SchemaAnalyticsPage | Visualizations |

### 6.3 Schema Connect Flow

```
[Service Selection]
      │
      └─→ [Schema Connect Page]
               │
               ├─→ Enter PostgreSQL URI
               │
               ├─→ [Test Connection]
               │        │
               │        └─→ Success: Show schema preview
               │
               ├─→ [Configure Allowed Schemas] (optional)
               │
               └─→ [Connect] → [Schema Agent Page]
```

### 6.4 Schema Agent UI

Components needed:
- `SchemaViewer.tsx` - Display database schema tree
- `QueryHistory.tsx` - Show past queries
- `SQLPreview.tsx` - Display generated SQL
- `ResultsTable.tsx` - Data table with pagination
- `VisualizationPanel.tsx` - Charts from query results

### 6.5 Dashboard Layout Changes

For users with `connection_mode = 'schema_query_only'`:
- Show: Schema Agent, Analytics
- Hide: Admin, POS
- Show: Schema browser sidebar

---

## 7. Backend Implementation

### 7.1 New Files

```
backend/app/
├── routers/
│   └── schema_agent.py          # New router for schema agent
├── agents/
│   └── schema_query_agent.py    # New agent for schema queries
├── mcp_server/
│   └── tools_schema_query.py    # MCP tools for schema operations
└── services/
    └── schema_discovery.py      # Schema discovery service
```

### 7.2 Schema Query Agent

```python
# backend/app/agents/schema_query_agent.py

class SchemaQueryAgent:
    """Agent for querying user's existing database schema."""

    def __init__(self, user_id: int, schema_metadata: dict):
        self.user_id = user_id
        self.schema_metadata = schema_metadata
        self.mcp_client = None

    async def initialize(self, database_uri: str):
        """Initialize MCP connection to user's database."""
        # Start PostgreSQL MCP server with read-only mode
        # ...

    async def process_query(self, natural_query: str) -> QueryResult:
        """Process natural language query."""
        # 1. Understand query intent
        # 2. Generate SQL from natural language
        # 3. Validate SQL (SELECT only)
        # 4. Execute via MCP
        # 5. Format and return results

    def _generate_system_prompt(self) -> str:
        """Generate prompt with schema context."""
        return f"""
        You are a database query assistant.

        Available tables:
        {self._format_schema()}

        Rules:
        - Only SELECT queries allowed
        - Explain your reasoning
        - Suggest visualizations
        """
```

### 7.3 MCP Tools

```python
# backend/app/mcp_server/tools_schema_query.py

@mcp.tool()
async def list_tables(schema: str = "public") -> list[dict]:
    """List all tables in the specified schema."""

@mcp.tool()
async def describe_table(table_name: str) -> dict:
    """Get detailed structure of a table."""

@mcp.tool()
async def execute_select_query(query: str) -> dict:
    """Execute a SELECT query and return results."""
    # CRITICAL: Validate query is SELECT only
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")

@mcp.tool()
async def get_sample_data(table_name: str, limit: int = 10) -> list[dict]:
    """Get sample rows from a table."""

@mcp.tool()
async def get_table_stats(table_name: str) -> dict:
    """Get statistics about a table (row count, etc.)."""
```

---

## 8. User Stories & Acceptance Criteria

### US-1: Connect Existing Database (Schema Mode)
**As a** business owner with an existing database
**I want to** connect my database without creating new tables
**So that** I can use AI to query my existing data

**Acceptance Criteria:**
- [ ] Can select "Agent + Analytics Only" option
- [ ] Can provide PostgreSQL connection string
- [ ] Connection is tested before saving
- [ ] No new tables are created in user's database
- [ ] Schema is discovered and displayed

### US-2: Natural Language Queries
**As a** connected user
**I want to** ask questions in natural language
**So that** I can get data without writing SQL

**Acceptance Criteria:**
- [ ] Can type questions like "Show me top sellers"
- [ ] Agent generates appropriate SQL
- [ ] Only SELECT queries are executed
- [ ] Results are displayed in readable format
- [ ] Generated SQL can be viewed

### US-3: Schema Browser
**As a** connected user
**I want to** see my database schema
**So that** I know what data is available

**Acceptance Criteria:**
- [ ] Can see list of tables
- [ ] Can expand table to see columns
- [ ] Can see relationships between tables
- [ ] Can refresh schema when needed

### US-4: Analytics Visualizations
**As a** connected user
**I want to** see visualizations of my data
**So that** I can understand trends and patterns

**Data Isolation:** Analytics Dashboard shows data exclusively from user's connected database. No platform-level analytics or cross-user data is displayed.

**Acceptance Criteria:**
- [ ] Agent suggests appropriate visualizations
- [ ] Can view bar charts, line charts, tables
- [ ] Can export visualization data
- [ ] Visualizations update with new queries
- [ ] Analytics data sourced only from user's connected database

### US-5: Security Enforcement
**As a** system administrator
**I want to** ensure read-only access
**So that** user databases are protected

**Acceptance Criteria:**
- [ ] INSERT/UPDATE/DELETE queries are rejected
- [ ] DROP/CREATE/ALTER queries are rejected
- [ ] Query timeout prevents long-running queries
- [ ] Rate limiting prevents abuse
- [ ] Connection is encrypted (SSL)

---

## 9. Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| Invalid connection string | Show clear error, suggest format |
| Connection timeout | Retry with backoff, then error |
| No tables found | Show message, check schema permissions |
| Empty table | Return empty results, not error |
| Query timeout (30s) | Cancel query, suggest simpler query |
| Rate limit exceeded | Show message with retry time |
| Schema changed | Prompt to refresh schema |
| Large result set | Paginate, warn about size |
| Unsupported data types | Show as string, warn user |
| Connection dropped | Attempt reconnect, show status |
| **>100 tables found** | Warn user, require `allowed_schemas` filter before proceeding |

---

## 10. Out of Scope (v1.0)

- Write operations (INSERT, UPDATE, DELETE)
- Stored procedure execution
- Custom query builder UI
- Schema migration suggestions
- Multi-database connections
- Real-time data sync
- Query scheduling/automation
- Non-PostgreSQL databases (MySQL, etc.)
- Query optimization suggestions

---

## 11. Dependencies

### New Python Packages
```txt
# None required - using existing packages
# PostgreSQL MCP Server provided by existing setup
```

### Frontend Dependencies
```json
{
  "react-syntax-highlighter": "^15.5.0"  // For SQL highlighting
}
```

---

## 12. Testing Strategy

### Unit Tests
- Schema discovery functions
- Query validation (SELECT only)
- MCP tool functions
- Schema metadata parsing

### Integration Tests
- Full connection flow
- Query execution pipeline
- ChatKit streaming

### Security Tests
- Injection attempt prevention
- Query type validation
- Rate limiting verification

---

## 13. Rollout Plan

1. **Phase 1**: Backend API + Schema Agent (1 week)
2. **Phase 2**: MCP Tools + Security (3 days)
3. **Phase 3**: Frontend UI (1 week)
4. **Phase 4**: Integration Testing (3 days)
5. **Phase 5**: Documentation + Deploy (2 days)

---

## 14. Success Metrics

- Connection success rate > 95%
- Average query response time < 5s
- Zero write operations executed
- User satisfaction with query accuracy

---

## Clarifications

### Session 2025-12-15
- Q: Which PostgreSQL MCP Server implementation should be used? → A: Reuse existing FastMCP infrastructure from project. No IMS tables (inventory_items, inventory_bills, inventory_bill_items) will be created; agent queries user's existing tables directly via MCP.
- Q: Should Analytics Dashboard show platform data or user's schema only? → A: User's schema only. Analytics displays data exclusively from user's connected database; no platform-level analytics mixed in.
- Q: How should reconnection behave after logout/session expiry? → A: Auto-reconnect on login. System silently restores connection using stored URI when user returns.
- Q: Maximum tables for schema discovery? → A: Max 100 tables. If exceeded, warn user and require filtering via allowed_schemas.
- Q: Can user switch from Schema Query Mode to Full IMS Mode? → A: Yes, with confirmation dialog warning that IMS tables will be created in their database.

---

## Appendix A: Example Queries

| Natural Language | Generated SQL |
|-----------------|---------------|
| "Show all products" | `SELECT * FROM products LIMIT 100` |
| "Top 10 customers by orders" | `SELECT c.name, COUNT(o.id) as orders FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY orders DESC LIMIT 10` |
| "Sales this month" | `SELECT SUM(total) FROM orders WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)` |
| "Products low on stock" | `SELECT name, stock_qty FROM products WHERE stock_qty < 10 ORDER BY stock_qty ASC` |

---

## Appendix B: Schema Metadata Example

```json
{
  "tables": [
    {
      "name": "customers",
      "schema": "public",
      "columns": [
        {"name": "id", "type": "serial", "nullable": false, "pk": true},
        {"name": "name", "type": "varchar(255)", "nullable": false},
        {"name": "email", "type": "varchar(255)", "nullable": true},
        {"name": "created_at", "type": "timestamp", "nullable": false}
      ],
      "indexes": ["customers_pkey", "customers_email_idx"],
      "estimated_rows": 5000
    },
    {
      "name": "orders",
      "schema": "public",
      "columns": [
        {"name": "id", "type": "serial", "nullable": false, "pk": true},
        {"name": "customer_id", "type": "integer", "nullable": false, "fk": "customers.id"},
        {"name": "total", "type": "decimal(10,2)", "nullable": false},
        {"name": "status", "type": "varchar(50)", "nullable": false},
        {"name": "created_at", "type": "timestamp", "nullable": false}
      ],
      "estimated_rows": 25000
    }
  ],
  "relationships": [
    {
      "from": {"table": "orders", "column": "customer_id"},
      "to": {"table": "customers", "column": "id"},
      "type": "many-to-one"
    }
  ],
  "discovered_at": "2025-12-15T10:30:00Z"
}
```
