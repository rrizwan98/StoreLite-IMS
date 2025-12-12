# Phase 0 Research: OpenAI Agents SDK Integration

**Date**: 2025-12-09 | **Feature**: Phase 5 - OpenAI Agents Integration

---

## Research Tasks Completed

### 1. OpenAI Agents SDK Capabilities & Limitations

**Decision**: Use OpenAI Agents SDK (Python) for agent orchestration.

**Rationale**:
- Agents SDK provides built-in tool calling, message history, error recovery
- Supports dynamic tool registration via tool schema
- Integrates seamlessly with OpenAI models (GPT-4o-mini, GPT-4 Turbo)
- Production-ready; used in many commercial AI applications
- Good documentation and community support

**Key Capabilities**:
- **Tool Registration**: Define tools as Python functions with type hints; SDK auto-generates schema
- **Message History**: Built-in conversation context management
- **Tool Calling**: Automatic parsing of model's tool-use tokens; calls Python functions
- **Streaming**: Supports streaming token and tool-call events
- **Error Recovery**: Gracefully handles tool errors; can retry or ask for clarification

**Limitations**:
- Tool discovery from external sources (like MCP servers) requires custom integration
- Conversation history managed in-memory by default (we use PostgreSQL instead)
- Streaming requires SSE or WebSocket on the HTTP layer (not built into SDK)
- Costs ~$0.01 per 1k tokens (for gpt-4o-mini); should monitor usage

**Alternatives Considered**:
- **Gemini 2.5 Flash Lite** (mentioned in spec as budget-friendly) - similar capabilities, lower cost (~$0.00015 per 1k tokens), but less mature for tool calling in 2025; could be added as secondary model later
- **LangChain** - heavier, more abstraction; Agents SDK is lighter and more direct
- **Custom agent loop** - reinventing the wheel; SDK does this better

**Sources**:
- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [Tool Use Best Practices](https://platform.openai.com/docs/guides/agents)

---

### 2. FastAPI Server-Sent Events (SSE) Streaming

**Decision**: Implement SSE streaming for `/agent/chat/stream` endpoint using FastAPI's `StreamingResponse`.

**Rationale**:
- SSE is HTTP-based (no WebSocket complexity)
- Browsers natively support EventSource API
- Simple to implement: yield events as newline-delimited JSON
- Compatible with any HTTP client (curl, fetch, httpx)
- Automatic reconnection on client disconnect

**Implementation Pattern** (FastAPI):
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

@app.get("/agent/chat/stream")
async def agent_chat_stream(session_id: str, message: str):
    async def event_generator():
        # Yield SSE-formatted events
        yield f"event: token\ndata: {json.dumps({'chunk': 'Hello'})}\n\n"
        yield f"event: token\ndata: {json.dumps({'chunk': ' world'})}\n\n"
        yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Alternatives Considered**:
- **WebSocket**: More complex (separate connection handler); overkill for one-way streaming
- **Chunked Transfer-Encoding**: Works but no event semantics; client must parse chunks
- **Polling**: Client inefficiency; high latency

**Cost**: No additional cost; uses existing HTTP infrastructure.

**Sources**:
- [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/streaming-response/)
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

### 3. PostgreSQL JSONB for Session History

**Decision**: Use PostgreSQL `agent_sessions` table with JSONB `conversation_history` column to store recent message pairs.

**Rationale**:
- JSONB is fast (indexed, compressed)
- Flexible: can store variable-length conversations
- Queryable: can search conversation content if needed
- Native to PostgreSQL; no additional dependencies
- Proven at scale: used by major applications

**Schema Design**:
```sql
CREATE TABLE agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    conversation_history JSONB NOT NULL DEFAULT '[]',  -- Array of {role, content, timestamp}
    metadata JSONB NOT NULL DEFAULT '{}',               -- {user_context, store_name, etc.}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_session_id (session_id)
);
```

**Conversation History Example**:
```json
[
  {
    "role": "user",
    "content": "Add 10kg sugar at 160 per kg",
    "timestamp": "2025-12-09T10:00:00Z"
  },
  {
    "role": "assistant",
    "content": "I've added 10kg Sugar at 160 per kg to Grocery category.",
    "timestamp": "2025-12-09T10:00:02Z"
  }
]
```

**Performance Notes**:
- 5-message rolling window: ~1-2 KB per session (negligible)
- Retrieving 1M sessions: ~100-200ms with proper indexing
- Insertion: < 10ms per session update
- Suitable for Phase 5 scale (10 concurrent sessions, < 500 requests/min)

**Alternatives Considered**:
- **Redis**: Fast but non-persistent; not suitable for audit trails
- **Separate conversation_messages table**: Normalized but more complex queries
- **Text field with serialization**: Slower than JSONB; harder to query
- **In-memory only**: No persistence across restarts; not production-ready

**Cost**: Uses existing PostgreSQL instance; no additional infrastructure.

**Sources**:
- [PostgreSQL JSONB Performance](https://www.postgresql.org/docs/current/datatype-json.html)
- [JSONB Indexing](https://www.postgresql.org/docs/current/datatype-json.html#JSON-INDEXING)

---

### 4. MCP HTTP Client for Tool Discovery & Calling

**Decision**: Implement custom HTTP client to communicate with FastMCP server via `http://localhost:8001`.

**Rationale**:
- FastMCP server exposes HTTP endpoints (from Phase 4 design)
- HTTP is simple, standards-compliant, debuggable
- No need for MCP SDK client complexity; simple POST/GET calls suffice
- Allows agent to be decoupled from MCP server implementation

**HTTP Interface Spec** (derived from MCP standard + FastMCP):

**Tool Discovery** (at agent startup):
```
GET http://localhost:8001/mcp/tools
Response: {"tools": [{"name": "...", "description": "...", "schema": {...}}, ...]}
```

**Tool Invocation**:
```
POST http://localhost:8001/mcp/call
Body: {"tool": "inventory_add_item", "arguments": {"name": "Sugar", ...}}
Response: {"status": "success", "result": {...}}
```

**Error Response**:
```
{"status": "error", "error": "Item not found"}
```

**Implementation** (Python httpx):
```python
import httpx

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=10)

    def discover_tools(self) -> List[dict]:
        response = self.client.get(f"{self.base_url}/mcp/tools")
        response.raise_for_status()
        return response.json()["tools"]

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        response = self.client.post(
            f"{self.base_url}/mcp/call",
            json={"tool": tool_name, "arguments": arguments}
        )
        response.raise_for_status()
        return response.json()["result"]
```

**Error Handling**:
- Connection timeout → Return agent error: "Unable to reach system. Try again."
- Tool not found → Agent fallback: "That action isn't available."
- Tool execution failure → Return MCP error message to agent for user-friendly translation

**Caching**:
- Tool discovery result cached for 5 minutes (TTL)
- Prevents repeated HTTP calls during agent operation

**Alternatives Considered**:
- **MCP Python SDK**: More heavyweight; would require vendoring Phase 4 code into Phase 5
- **Direct database queries**: Violates separation of concerns; couples agent to DB
- **Stdio transport**: Simpler for local testing but less suitable for production multi-instance deployments

**Cost**: No additional infrastructure; uses existing FastMCP server.

**Sources**:
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [httpx Documentation](https://www.python-httpx.org/)

---

### 5. Session Persistence Strategy

**Decision**: Store sessions in PostgreSQL with 5-message rolling window, fetched on each request.

**Rationale**:
- Enables multi-instance deployments (load balancing)
- Provides audit trail for compliance
- Survives server restarts
- Session data is structured (JSONB) and queryable

**Persistence Flow**:
1. Request arrives with `session_id` (user-provided or UUID-generated)
2. `SessionManager.get_session(session_id)` queries PostgreSQL → retrieves conversation history
3. Agent uses conversation history for context
4. Agent processes request, generates response
5. `SessionManager.save_session(session_id, new_history)` updates PostgreSQL
6. Return response to client

**Session Lifecycle**:
- **Create**: First message creates new session, assigned UUID if not provided
- **Retrieve**: Subsequent messages fetch session from DB
- **Update**: After each agent response, save updated conversation history
- **Expire**: Sessions older than 30 days deleted (automated via scheduled job)

**Alternatives Considered**:
- **In-memory only**: Simpler code but no persistence; not production-ready
- **Redis cache + PostgreSQL fallback**: Complex; not needed at Phase 5 scale
- **File-based (JSON files)**: Not suitable for multi-instance deployments

**Cost**: Uses existing PostgreSQL instance; minimal storage (<1 MB per 1k sessions at 5-message window).

**Sources**:
- [PostgreSQL Session Management Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

### 6. Confirmation Flow Design

**Decision**: Implement inline confirmation as agent conversation turn: agent asks yes/no question, user replies with "yes" or "no".

**Rationale**:
- Natural conversational flow (no special syntax)
- Easy for users to understand and use
- No state machine complexity; agent handles it
- Reuses existing message handling

**Confirmation State Machine**:
```
[User sends destructive request]
    ↓
[Agent generates confirmation question]
    ↓
[Agent returns response with status: "pending_confirmation"]
    ↓
[User sends follow-up message: "yes" or "no"]
    ↓
[If "yes": Agent calls MCP tool; If "no": Agent cancels action]
    ↓
[Return result]
```

**Example Conversation**:
```
User: "Create a bill for Ali: 2kg sugar and 1 shampoo"
Agent: "Are you sure you want to create a bill for Ali with 2kg sugar and 1 shampoo (Total: $820)? Reply 'yes' to confirm."
User: "yes"
Agent: "Bill created! Bill ID: 42. Total: $820."
```

**Timeout**: If user doesn't confirm within 5 minutes, conversation context expires (agent forgets pending action).

**Alternatives Considered**:
- **Explicit `/confirm` endpoint**: Requires custom client logic; not conversational
- **Checkbox in JSON response**: Not user-friendly; requires structured client response
- **Silent confirmation (auto-execute)**: Risky; users might accidentally delete data

**Cost**: No additional infrastructure; implemented in agent logic.

---

### 7. Environment Variable Strategy

**Decision**: Use `.env` file with `DATABASE_URL`, `OPENAI_API_KEY`, `MCP_SERVER_URL`, agent config.

**Rationale**:
- Standard practice; tools like `python-dotenv` automate loading
- Separates secrets from code
- Easy to rotate credentials
- Supports multiple environments (dev, staging, prod)

**Required Variables**:
```
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# MCP Server
MCP_SERVER_URL=http://localhost:8001

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/storelite_ims

# Agent Config
SESSION_CONTEXT_SIZE=5
MCP_TOOL_CACHE_TTL_SECONDS=300
AGENT_CONFIRMATION_TIMEOUT_SECONDS=300
```

**Loading** (in Python):
```python
from dotenv import load_dotenv
import os

load_dotenv()
database_url = os.getenv("DATABASE_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
```

**Alternatives Considered**:
- **Config file (JSON/YAML)**: Harder to hide secrets; not recommended
- **Environment-only (no .env)**: Fine for CI/CD but inconvenient for local development
- **Command-line arguments**: Exposes secrets in process lists

**Cost**: None; uses `python-dotenv` (lightweight, standard package).

---

## Summary of Decisions

| Decision | Choice | Rationale | Risk |
|----------|--------|-----------|------|
| Agent SDK | OpenAI Agents SDK | Production-ready, tool calling built-in | Cost (~$0.01/1k tokens) |
| Streaming | Server-Sent Events (SSE) | HTTP-native, simple | Client reconnection handling |
| Session Storage | PostgreSQL JSONB | Persistent, queryable, fast | Schema migration overhead |
| MCP Communication | HTTP client (httpx) | Simple, decoupled, debuggable | Network latency (~50ms) |
| Session Persistence | DB-backed with 5-message window | Multi-instance support, audit trail | Storage growth (mitigated with TTL) |
| Confirmation Flow | Inline yes/no questions | Natural, conversational | User might forget to confirm (5-min timeout) |
| Environment Config | .env file | Standard, secret-safe | Developers must create .env locally |

---

## Technology Stack Validated

✅ **Python 3.11+** - Latest stable; good async support
✅ **OpenAI Agents SDK** - Mature, production-ready
✅ **FastAPI** - Async, streaming support
✅ **PostgreSQL** - JSONB for session storage
✅ **httpx** - Modern async HTTP client
✅ **python-dotenv** - Standard env loading
✅ **pytest** - Standard test framework (already used in Phases 1-4)

---

## Next Steps (Phase 1: Design)

1. ✅ Research completed (this document)
2. Generate `data-model.md` with database migration
3. Generate `contracts/agent-api.yaml` with OpenAPI spec
4. Generate `quickstart.md` with developer setup
5. Proceed to Phase 2: Implementation (TDD)

