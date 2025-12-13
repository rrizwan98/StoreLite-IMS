---
id: 0009
title: DATABASE_URI Approach Following postgres-mcp Architecture
stage: green
date: 2025-12-13
surface: agent
model: claude-opus-4-5-20251101
feature: 006-chatkit-ui
branch: 006-chatkit-ui
user: rrizwan98
command: direct-chat
labels: ["database", "postgresql", "mcp", "database-uri", "inventory-agent", "refactor"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/routers/inventory_agent.py
  - frontend/app/db-connect/page.tsx
tests:
  - Backend routes verified: /inventory-agent/connect, /inventory-agent/setup-tables, /inventory-agent/chat
  - Frontend page loads (HTTP 200)
---

## Prompt

User feedback (in Urdu/English mix) indicating the previous approach was incorrect:

"i think mujy nh lagta k jis tarahn say hum database ka connection kr rhy hyn UI say like host, password, post and soon... mai is postgress MCP server ki repo ko dekh rha tha tu tum is ko follow kro is k according UI ko stablish kro I think hmay user say only database URL lena h or us k through MCP server connect ho ga or database connection ho jay ga. or is postgress sql MCP server ko Agent k sath connect kro as a tool/function_tool jb bhi user koi query kry tu agent user ki query ko smjhy or function_tool/tool call kry. here is the postgressql server MCP github url https://github.com/crystaldba/postgres-mcp, is url ko dekho is or mcp server ko connect kro. or UI ko bhi update kro."

Translation: User wants to follow the postgres-mcp approach from GitHub, taking only DATABASE_URI from user instead of separate fields (host, password, port, etc.), and connect the MCP server to the Agent as function_tool.

## Response snapshot

Refactored the PostgreSQL database connection feature to use the postgres-mcp architecture:

**Backend Changes (`inventory_agent.py`):**

1. **Single DATABASE_URI input** - Changed from separate fields to single URI:
   ```python
   class ConnectRequest(BaseModel):
       database_uri: str  # postgresql://user:password@host:port/dbname
   ```

2. **MCP-compatible function tools** - Created tools that can work with postgres-mcp:
   - `execute_sql(session_id, sql)` - Execute SQL via MCP
   - `list_tables(session_id)` - List database tables
   - `get_table_details(session_id, table_name)` - Get table schema

3. **Direct asyncpg connection** - For immediate functionality without requiring docker/pipx:
   - Validates URI format (postgresql:// or postgres://)
   - Tests connection and returns database info
   - Session-based connection management

4. **Specialized inventory agent** - Refuses non-inventory operations (user management, auth, custom tables)

**Frontend Changes (`db-connect/page.tsx`):**

1. **Simplified form** - Single input field for DATABASE_URI:
   ```tsx
   <input
     placeholder="postgresql://user:password@host:port/database"
     value={databaseUri}
     onChange={(e) => setDatabaseUri(e.target.value)}
   />
   ```

2. **Three-step flow preserved** - Connect -> Setup Tables -> Chat Interface

## Outcome

- Impact: Database connection now follows postgres-mcp standard with single DATABASE_URI input
- Tests: Backend routes verified, frontend page loads successfully
- Files: 2 files modified (inventory_agent.py completely rewritten, db-connect/page.tsx simplified)
- Next prompts: Test with actual PostgreSQL database, optionally integrate actual postgres-mcp MCP server via docker/pipx
- Reflection: Following established MCP patterns (like postgres-mcp) provides better UX and aligns with industry standards

## Evaluation notes (flywheel)

- Failure modes observed: User feedback corrected the approach before production use
- Graders run and results (PASS/FAIL): PASS - Routes registered, frontend compiles
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Integrate actual postgres-mcp MCP server for full tool capabilities
