# Developer Tools - Implementation Plan

**Version:** 1.0.0
**Created:** 2025-01-13

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXISTING SYSTEM (NO CHANGES)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐   │
│  │   Frontend   │     │   Backend    │     │   Schema Query Agent     │   │
│  │  (Next.js)   │────▶│  (FastAPI)   │────▶│   (OpenAI Agents SDK)    │   │
│  │              │     │              │     │                          │   │
│  │  /dashboard/ │     │ /schema-     │     │  - Full schema access    │   │
│  │  schema-agent│     │  agent/      │     │  - All tables visible    │   │
│  └──────────────┘     │  chatkit     │     │  - MCP postgres tools    │   │
│                       └──────────────┘     └──────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEW SYSTEM (ADDITIVE)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐   │
│  │   Frontend   │     │   Backend    │     │   Schema Query Agent     │   │
│  │  (Next.js)   │────▶│  (FastAPI)   │────▶│   (SAME, REUSED)         │   │
│  │              │     │              │     │                          │   │
│  │  /dashboard/ │     │ /api/        │     │  - FILTERED schema       │   │
│  │  developer-  │     │  developer/  │     │  - Only allowed tables   │   │
│  │  tools       │     │  agents      │     │  - Same MCP tools        │   │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘   │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐                                     │
│  │   External   │     │   Backend    │                                     │
│  │   Website    │────▶│  (FastAPI)   │────────────────────────────────────▶│
│  │              │     │              │                                     │
│  │  ChatKit     │     │ /api/v1/     │     Uses filtered schema            │
│  │  Widget      │     │  public/chat │     from PublishedAgentConfig       │
│  └──────────────┘     └──────────────┘                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND COMPONENTS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEW FILES (backend/app/)                                                   │
│  ├── models/                                                                │
│  │   └── published_agent.py          # PublishedAgentConfig model          │
│  │                                                                          │
│  ├── services/                                                              │
│  │   ├── published_agent_service.py  # CRUD operations                     │
│  │   ├── api_key_service.py          # Key generation, hashing, validation │
│  │   ├── schema_filter_service.py    # Schema filtering logic              │
│  │   └── rate_limit_service.py       # In-memory rate limiting             │
│  │                                                                          │
│  ├── routers/                                                               │
│  │   ├── developer_portal.py         # Organization management APIs        │
│  │   └── public_agent_api.py         # Public chat API                     │
│  │                                                                          │
│  └── middleware/                                                            │
│      └── api_key_auth.py             # API key authentication              │
│                                                                             │
│  EXISTING FILES (NO CHANGES)                                                │
│  ├── agents/schema_query_agent.py    # Reused as-is                        │
│  ├── services/schema_discovery.py    # Reused as-is                        │
│  ├── routers/schema_agent.py         # Untouched                           │
│  └── models.py                       # Only import new model               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             FRONTEND COMPONENTS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NEW FILES (frontend/app/)                                                  │
│  ├── dashboard/developer-tools/                                            │
│  │   ├── page.tsx                    # Main page                           │
│  │   └── components/                                                        │
│  │       ├── create-agent-modal.tsx  # Create agent wizard                 │
│  │       ├── agent-card.tsx          # Agent display card                  │
│  │       ├── table-selector.tsx      # Multi-select tables                 │
│  │       ├── embed-code-viewer.tsx   # Code snippet display                │
│  │       └── usage-stats.tsx         # Usage charts                        │
│  │                                                                          │
│  └── lib/                                                                   │
│      └── developer-tools-api.ts      # API client functions                │
│                                                                             │
│  EXISTING FILES (NO CHANGES)                                                │
│  ├── dashboard/schema-agent/         # Untouched                           │
│  └── lib/constants.ts                # Only add new endpoints              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Backend Design

### 2.1 Service Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVICE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     published_agent_service.py                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  class PublishedAgentService:                                       │   │
│  │      """Business logic for published agents"""                      │   │
│  │                                                                     │   │
│  │      async def create_agent(user_id, config) -> AgentWithKey        │   │
│  │      async def list_agents(user_id) -> List[Agent]                  │   │
│  │      async def get_agent(agent_id, user_id) -> Agent                │   │
│  │      async def update_agent(agent_id, user_id, config) -> Agent     │   │
│  │      async def delete_agent(agent_id, user_id) -> bool              │   │
│  │      async def regenerate_key(agent_id, user_id) -> NewKey          │   │
│  │      async def get_usage_stats(agent_id, period) -> UsageStats      │   │
│  │      async def record_query(agent_id, success, time_ms) -> None     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        api_key_service.py                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  class ApiKeyService:                                               │   │
│  │      """API key generation and validation"""                        │   │
│  │                                                                     │   │
│  │      def generate_api_key() -> tuple[str, str, str]                 │   │
│  │          # Returns: (full_key, hash, prefix)                        │   │
│  │          # Example: ("pa_live_abc123...", "sha256...", "pa_live_ab")│   │
│  │                                                                     │   │
│  │      def hash_api_key(key: str) -> str                              │   │
│  │          # SHA-256 hash for storage                                 │   │
│  │                                                                     │   │
│  │      async def validate_api_key(key: str, db) -> AgentConfig        │   │
│  │          # Lookup by hash, check active, check expiry               │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      schema_filter_service.py                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  def filter_schema_for_published_agent(                             │   │
│  │      full_schema: dict,                                             │   │
│  │      allowed_tables: list[str],                                     │   │
│  │      access_mode: str                                               │   │
│  │  ) -> dict:                                                         │   │
│  │      """                                                            │   │
│  │      Filter schema metadata to only include allowed tables.         │   │
│  │                                                                     │   │
│  │      This is the KEY function enabling table-level access control.  │   │
│  │      The agent only sees tables in allowed_tables list.             │   │
│  │      """                                                            │   │
│  │      ...                                                            │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       rate_limit_service.py                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  class RateLimitService:                                            │   │
│  │      """In-memory sliding window rate limiter"""                    │   │
│  │                                                                     │   │
│  │      def __init__(self):                                            │   │
│  │          self._cache: dict[str, deque] = {}  # key -> timestamps    │   │
│  │                                                                     │   │
│  │      def check_rate_limit(key_id: str, limit: int) -> bool          │   │
│  │          # Returns True if allowed, False if exceeded               │   │
│  │                                                                     │   │
│  │      def get_remaining(key_id: str, limit: int) -> int              │   │
│  │          # Returns remaining requests in window                     │   │
│  │                                                                     │   │
│  │      def get_reset_time(key_id: str) -> int                         │   │
│  │          # Returns seconds until window resets                      │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Router Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ROUTER LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       developer_portal.py                            │   │
│  │                       (JWT Authentication)                           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  router = APIRouter(prefix="/api/developer", tags=["developer"])    │   │
│  │                                                                     │   │
│  │  POST   /agents              → create_published_agent()             │   │
│  │  GET    /agents              → list_published_agents()              │   │
│  │  GET    /agents/{id}         → get_published_agent()                │   │
│  │  PUT    /agents/{id}         → update_published_agent()             │   │
│  │  DELETE /agents/{id}         → delete_published_agent()             │   │
│  │  POST   /agents/{id}/regenerate-key → regenerate_api_key()          │   │
│  │  GET    /agents/{id}/usage   → get_usage_statistics()               │   │
│  │  GET    /agents/{id}/embed-code → get_embed_code()                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        public_agent_api.py                           │   │
│  │                        (API Key Authentication)                      │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  router = APIRouter(prefix="/api/v1/public", tags=["public"])       │   │
│  │                                                                     │   │
│  │  POST   /chat                → public_chat()                        │   │
│  │  POST   /chat/stream         → public_chat_stream()  (Future)       │   │
│  │                                                                     │   │
│  │  Middleware:                                                        │   │
│  │  - validate_api_key()        → Check X-API-Key header               │   │
│  │  - check_rate_limit()        → Enforce rate limits                  │   │
│  │  - validate_cors()           → Check Origin header                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Request Flow (Public API)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PUBLIC API REQUEST FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. External Request                                                        │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ POST /api/v1/public/chat                                         │   │
│     │ Headers:                                                         │   │
│     │   X-API-Key: pa_live_abc123...                                   │   │
│     │   Origin: https://mystore.com                                    │   │
│     │ Body: { "message": "Show top products", "thread_id": "..." }     │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  2. API Key Validation                                                      │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ api_key_service.validate_api_key(key)                            │   │
│     │   → Hash the key                                                 │   │
│     │   → Lookup PublishedAgentConfig by hash                          │   │
│     │   → Check is_active == True                                      │   │
│     │   → Check expires_at > now() or NULL                             │   │
│     │   → Return config or raise 401                                   │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  3. Rate Limit Check                                                        │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ rate_limit_service.check_rate_limit(config.id, config.rate_limit)│   │
│     │   → Check sliding window counter                                 │   │
│     │   → Return True/False                                            │   │
│     │   → If False: raise 429 with retry_after                         │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  4. CORS Validation                                                         │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ validate_origin(request.origin, config.allowed_domains)          │   │
│     │   → Check if origin matches any pattern                          │   │
│     │   → Support wildcards (*.mystore.com)                            │   │
│     │   → If no match: raise 403                                       │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  5. Load Owner's Database Config                                            │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ owner_connection = db.get(UserConnection, config.user_id)        │   │
│     │   → Get database_uri (encrypted → decrypt)                       │   │
│     │   → Get full schema_metadata                                     │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  6. Filter Schema (KEY STEP!)                                               │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ filtered_schema = filter_schema_for_published_agent(             │   │
│     │     full_schema=owner_connection.schema_metadata,                │   │
│     │     allowed_tables=config.allowed_tables,                        │   │
│     │     access_mode=config.access_mode                               │   │
│     │ )                                                                │   │
│     │                                                                  │   │
│     │ # Before: {tables: [products, orders, users, admin, logs]}       │   │
│     │ # After:  {tables: [products, orders]}  ← Only allowed!          │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  7. Create Agent with Filtered Schema                                       │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ agent = await create_schema_query_agent(                         │   │
│     │     database_uri=owner_connection.database_uri,                  │   │
│     │     schema_metadata=filtered_schema,   # ← FILTERED!             │   │
│     │     custom_instructions=config.custom_instructions,              │   │
│     │     thread_id=body.thread_id                                     │   │
│     │ )                                                                │   │
│     │                                                                  │   │
│     │ # Agent prompt will only show allowed tables                     │   │
│     │ # Agent cannot query tables it doesn't know about                │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  8. Execute Query & Return Response                                         │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │ response = await agent.query(body.message)                       │   │
│     │                                                                  │   │
│     │ # Record usage stats                                             │   │
│     │ await published_agent_service.record_query(                      │   │
│     │     agent_id=config.id,                                          │   │
│     │     success=True,                                                │   │
│     │     response_time_ms=elapsed_ms                                  │   │
│     │ )                                                                │   │
│     │                                                                  │   │
│     │ return {                                                         │   │
│     │     "response": response,                                        │   │
│     │     "thread_id": body.thread_id or new_thread_id                 │   │
│     │ }                                                                │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Frontend Design

### 3.1 Page Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPER TOOLS PAGE                                │
│                          /dashboard/developer-tools                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Header                                                              │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │   │
│  │ │ Developer Tools                          [+ Create Agent]    │   │   │
│  │ │ Share your AI assistant with your customers                  │   │   │
│  │ └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Prerequisites Check                                                 │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │   │
│  │ │ ⚠️  Database not connected                                   │   │   │
│  │ │     Connect your database first in Schema Agent page         │   │   │
│  │ │     [Go to Schema Agent →]                                   │   │   │
│  │ └──────────────────────────────────────────────────────────────┘   │   │
│  │ OR                                                                  │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │   │
│  │ │ ✅ Database connected: mydb@postgres.example.com             │   │   │
│  │ │    15 tables discovered                                      │   │   │
│  │ └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Published Agents List                                               │   │
│  │                                                                     │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │   │
│  │ │ AgentCard: Customer Support Agent                            │   │   │
│  │ │ ┌────────────────────────────────────────────────────────┐   │   │   │
│  │ │ │ Name: Customer Support Agent         Status: ✅ Active │   │   │   │
│  │ │ │ API Key: pa_live_abc1... [Copy]                        │   │   │   │
│  │ │ │ Tables: products, orders, categories                   │   │   │   │
│  │ │ │ Access: Read Only | Rate: 100/min                      │   │   │   │
│  │ │ │ Usage: 1,234 queries | Last: 5 min ago                 │   │   │   │
│  │ │ │                                                        │   │   │   │
│  │ │ │ [View Code] [Edit] [Regenerate Key] [Delete]          │   │   │   │
│  │ │ └────────────────────────────────────────────────────────┘   │   │   │
│  │ └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │   │
│  │ │ AgentCard: Analytics Dashboard Bot                           │   │   │
│  │ │ ...                                                          │   │   │
│  │ └──────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Create Agent Modal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CREATE AGENT MODAL                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Create Published Agent                          │   │
│  │                                                               [X]   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Step 1: Basic Info                                                 │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ Agent Name *                                                  │  │   │
│  │  │ [Customer Support Agent                              ]        │  │   │
│  │  │                                                               │  │   │
│  │  │ Description (optional)                                        │  │   │
│  │  │ [Help customers find products and track orders       ]        │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  Step 2: Table Access                                               │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ Select tables this agent can access:                         │  │   │
│  │  │                                                               │  │   │
│  │  │ ☑️ products (12 columns)                                     │  │   │
│  │  │ ☑️ orders (8 columns)                                        │  │   │
│  │  │ ☑️ categories (4 columns)                                    │  │   │
│  │  │ ☐ users (sensitive - email, password_hash)                  │  │   │
│  │  │ ☐ payments (sensitive - card info)                          │  │   │
│  │  │ ☐ admin_logs (internal)                                     │  │   │
│  │  │                                                               │  │   │
│  │  │ [Select All] [Deselect All]                                  │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  Step 3: Permissions                                                │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ Access Mode:                                                  │  │   │
│  │  │ ◉ Read Only (SELECT queries only) - Recommended              │  │   │
│  │  │ ○ Read & Write (SELECT, INSERT, UPDATE, DELETE)              │  │   │
│  │  │   ⚠️ Warning: Allows data modification                       │  │   │
│  │  │                                                               │  │   │
│  │  │ Rate Limit: [100] requests per minute                        │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  Step 4: Domain Whitelist                                           │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ Allowed domains (one per line):                              │  │   │
│  │  │ ┌────────────────────────────────────────────────────────┐   │  │   │
│  │  │ │ *.mystore.com                                          │   │  │   │
│  │  │ │ localhost:3000                                         │   │  │   │
│  │  │ │                                                        │   │  │   │
│  │  │ └────────────────────────────────────────────────────────┘   │  │   │
│  │  │ Tip: Use * to allow all domains (not recommended)            │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  Step 5: Custom Instructions (optional)                             │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ Additional instructions for the agent:                       │  │   │
│  │  │ ┌────────────────────────────────────────────────────────┐   │  │   │
│  │  │ │ You are a helpful shopping assistant for MyStore.      │   │  │   │
│  │  │ │ Always be polite and suggest related products.         │   │  │   │
│  │  │ │                                                        │   │  │   │
│  │  │ └────────────────────────────────────────────────────────┘   │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                    [Cancel]    [Create Agent]                │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Embed Code Viewer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EMBED CODE MODAL                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │           Embed Code - Customer Support Agent                       │   │
│  │                                                               [X]   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  Copy this code and paste it into your website:                     │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ <!-- Customer Support Agent Widget -->                       │  │   │
│  │  │ <div id="chat-widget-abc123"></div>                          │  │   │
│  │  │                                                              │  │   │
│  │  │ <script src="https://cdn.openai.com/chatkit/..."></script>   │  │   │
│  │  │ <script>                                                     │  │   │
│  │  │ (function() {                                                │  │   │
│  │  │   const API_KEY = 'pa_live_abc123...';                       │  │   │
│  │  │   const ENDPOINT = 'https://api.example.com/...';            │  │   │
│  │  │   ...                                                        │  │   │
│  │  │ })();                                                        │  │   │
│  │  │ </script>                                                    │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  [📋 Copy to Clipboard]                    Copied! ✓               │   │
│  │                                                                     │   │
│  │  ────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  API Details:                                                       │   │
│  │  • Endpoint: https://api.example.com/api/v1/public/chat            │   │
│  │  • API Key: pa_live_abc123... [Copy]                               │   │
│  │  • Method: POST                                                     │   │
│  │  • Header: X-API-Key                                               │   │
│  │                                                                     │   │
│  │  ────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  [View API Documentation]                                           │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. File Structure (Final)

```
backend/app/
├── models/
│   ├── __init__.py                    # Export all models
│   └── published_agent.py             # NEW: PublishedAgentConfig, PublishedAgentUsage
│
├── services/
│   ├── published_agent_service.py     # NEW: CRUD + business logic
│   ├── api_key_service.py             # NEW: Key generation/validation
│   ├── schema_filter_service.py       # NEW: Schema filtering
│   └── rate_limit_service.py          # NEW: Rate limiting
│
├── routers/
│   ├── developer_portal.py            # NEW: Organization management APIs
│   └── public_agent_api.py            # NEW: Public chat API
│
├── schemas/
│   └── developer_portal.py            # NEW: Pydantic request/response models
│
└── main.py                            # ADD: Include new routers


frontend/
├── app/
│   └── dashboard/
│       └── developer-tools/
│           ├── page.tsx               # NEW: Main page
│           └── components/
│               ├── create-agent-modal.tsx
│               ├── agent-card.tsx
│               ├── table-selector.tsx
│               ├── embed-code-viewer.tsx
│               └── usage-stats.tsx
│
└── lib/
    └── developer-tools-api.ts         # NEW: API client
```

---

## 5. Dependencies

### 5.1 No New Dependencies Required

All functionality uses existing packages:
- `hashlib` - SHA-256 hashing (Python stdlib)
- `secrets` - Secure random generation (Python stdlib)
- `fnmatch` - Domain pattern matching (Python stdlib)
- `collections.deque` - Rate limiting (Python stdlib)

### 5.2 Existing Dependencies Used

- `sqlalchemy` - Database models
- `fastapi` - API routing
- `pydantic` - Request validation
- OpenAI Agents SDK - Already installed

---

## 6. Testing Strategy

### 6.1 Unit Tests

```
tests/
├── test_api_key_service.py
│   ├── test_generate_api_key_format()
│   ├── test_hash_api_key()
│   └── test_validate_api_key()
│
├── test_schema_filter_service.py
│   ├── test_filter_tables()
│   ├── test_filter_relationships()
│   └── test_empty_allowed_tables()
│
└── test_rate_limit_service.py
    ├── test_under_limit()
    ├── test_at_limit()
    └── test_sliding_window()
```

### 6.2 Integration Tests

```
tests/
├── test_developer_portal_api.py
│   ├── test_create_agent()
│   ├── test_list_agents()
│   ├── test_update_agent()
│   └── test_delete_agent()
│
└── test_public_agent_api.py
    ├── test_valid_api_key()
    ├── test_invalid_api_key()
    ├── test_rate_limiting()
    └── test_cors_validation()
```

---

## 7. Rollout Plan

### Phase 1: Backend Core (Day 1)
1. Create database models
2. Implement api_key_service
3. Implement schema_filter_service
4. Implement rate_limit_service
5. Write unit tests

### Phase 2: Backend APIs (Day 1-2)
1. Implement developer_portal router
2. Implement public_agent_api router
3. Write integration tests
4. Test with Postman/curl

### Phase 3: Frontend (Day 2-3)
1. Create developer-tools page
2. Implement create-agent-modal
3. Implement agent-card
4. Implement embed-code-viewer
5. Connect to backend APIs

### Phase 4: Testing & Polish (Day 3)
1. End-to-end testing
2. Error handling improvements
3. UI polish
4. Documentation

---

## 8. Future Enhancements (Out of Scope)

1. **Tool Access Control** - Enable/disable tools per agent
2. **Streaming Responses** - SSE for public API
3. **Analytics Dashboard** - Detailed usage charts
4. **Webhook Notifications** - Alert on high usage
5. **API Key Rotation** - Automatic key rotation
