# Developer Tools - Published Agent API

**Version:** 1.0.0
**Created:** 2025-01-13
**Status:** Draft
**Phase:** 14

---

## 1. Overview

### 1.1 Summary

Developer Tools allows organizations to share their Schema Agent with external users/clients through a secure API key system. Organizations can create "Published Agents" with restricted access to specific tables and controlled permissions.

### 1.2 Problem Statement

Currently, organizations can only use Schema Agent internally. They cannot:
- Share database access with their customers/clients
- Control which tables are accessible to external users
- Provide embeddable chat widgets for their websites
- Track usage and manage API access

### 1.3 Solution

Reuse the **existing Schema Agent** with a **permission layer**:
- Organization creates a "Published Agent" configuration
- System generates a unique API Key
- External users hit a public endpoint with the API key
- Backend filters schema to only allowed tables
- Same agent processes query with restricted view

### 1.4 Key Principles

1. **Zero Impact on Existing Code** - No changes to current schema_agent, schema_discovery, or ChatKit integration
2. **Additive Only** - New models, new routers, new services (no modifications)
3. **Same Agent, Different View** - Reuse SchemaQueryAgent with filtered schema_metadata
4. **Future Extensible** - Design for future tool access (Gmail, Analytics, etc.)
5. **Security First** - API key hashing, rate limiting, domain whitelisting

---

## 2. User Stories

### 2.1 Organization (Agent Publisher)

```
AS an organization with a connected database
I WANT to create published agents with restricted table access
SO THAT my customers can query my data through their websites
```

### 2.2 External Developer (API Consumer)

```
AS an external developer
I WANT to embed a chat widget on my website using an API key
SO THAT my users can interact with the organization's data
```

### 2.3 End User (Widget User)

```
AS a website visitor
I WANT to ask questions in a chat widget
SO THAT I can get answers from the organization's database
```

---

## 3. Functional Requirements

### 3.1 Published Agent Management (Organization)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-001 | Organization can create multiple published agents | Must |
| FR-002 | Organization can select specific tables for each agent | Must |
| FR-003 | Organization can set access mode (read_only/read_write) | Must |
| FR-004 | Organization can set rate limits per agent | Must |
| FR-005 | Organization can whitelist allowed domains (CORS) | Must |
| FR-006 | Organization can add custom instructions to agent | Should |
| FR-007 | Organization can view usage statistics per agent | Should |
| FR-008 | Organization can regenerate API key | Must |
| FR-009 | Organization can deactivate/delete published agent | Must |
| FR-010 | Organization can set expiration date for API key | Could |

### 3.2 Public API (External Access)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-011 | Public endpoint accepts API key via header | Must |
| FR-012 | Public endpoint validates API key | Must |
| FR-013 | Public endpoint checks rate limits | Must |
| FR-014 | Public endpoint validates origin domain | Must |
| FR-015 | Public endpoint returns agent response | Must |
| FR-016 | Public endpoint supports conversation threads | Should |
| FR-017 | Public endpoint supports streaming responses | Could |

### 3.3 Embed Code Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-018 | System generates ChatKit embed code snippet | Must |
| FR-019 | Embed code includes API key configuration | Must |
| FR-020 | Embed code is copy-paste ready | Must |

### 3.4 Future Tool Access (Phase 2)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-021 | Support for enabling/disabling specific tools | Future |
| FR-022 | Tool-level permissions (e.g., Gmail send only) | Future |
| FR-023 | Custom tool configurations per published agent | Future |

---

## 4. Non-Functional Requirements

### 4.1 Security

| ID | Requirement |
|----|-------------|
| NFR-001 | API keys must be hashed before storage (only shown once) |
| NFR-002 | API key format: `pa_live_[32-char-hex]` (identifiable prefix) |
| NFR-003 | Rate limiting must be enforced per API key |
| NFR-004 | CORS validation must check Origin header |
| NFR-005 | Database credentials never exposed to public API |

### 4.2 Performance

| ID | Requirement |
|----|-------------|
| NFR-006 | API key lookup must be O(1) via indexed column |
| NFR-007 | Schema filtering must not add >10ms latency |
| NFR-008 | Rate limit checks must use in-memory cache |

### 4.3 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-009 | All new code in separate files (no modification to existing) |
| NFR-010 | Clear separation: models, services, routers |
| NFR-011 | Comprehensive logging for debugging |

---

## 5. Architecture Constraints

### 5.1 DO NOT Modify (Existing Code)

```
backend/app/
├── agents/
│   └── schema_query_agent.py    ❌ NO CHANGES
├── services/
│   └── schema_discovery.py      ❌ NO CHANGES (only ADD new function)
├── routers/
│   └── schema_agent.py          ❌ NO CHANGES
├── models.py                    ❌ NO CHANGES (only ADD new model)
└── database.py                  ❌ NO CHANGES

frontend/app/
├── dashboard/schema-agent/      ❌ NO CHANGES
└── components/                  ❌ NO CHANGES (only ADD new)
```

### 5.2 ADD New Files (Clean Separation)

```
backend/app/
├── models/
│   └── published_agent.py       ✅ NEW - PublishedAgentConfig model
├── services/
│   └── published_agent_service.py  ✅ NEW - Business logic
│   └── schema_filter_service.py    ✅ NEW - Schema filtering
│   └── api_key_service.py          ✅ NEW - API key generation/validation
│   └── rate_limit_service.py       ✅ NEW - Rate limiting
├── routers/
│   └── developer_portal.py      ✅ NEW - Organization management endpoints
│   └── public_agent_api.py      ✅ NEW - Public API endpoints
└── middleware/
    └── api_key_auth.py          ✅ NEW - API key authentication

frontend/app/
├── dashboard/developer-tools/
│   └── page.tsx                 ✅ NEW - Main developer tools page
│   └── components/
│       └── create-agent-modal.tsx   ✅ NEW
│       └── agent-card.tsx           ✅ NEW
│       └── table-selector.tsx       ✅ NEW
│       └── embed-code-viewer.tsx    ✅ NEW
│       └── usage-stats.tsx          ✅ NEW
└── lib/
    └── developer-tools-api.ts   ✅ NEW - API client
```

---

## 6. Data Flow

### 6.1 Current Flow (Organization - Unchanged)

```
┌─────────────────────────────────────────────────────────────┐
│  EXISTING FLOW (NO CHANGES)                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User Login → JWT Token                                     │
│       ↓                                                     │
│  POST /schema-agent/chatkit                                 │
│       ↓                                                     │
│  Validate JWT → get_current_user()                          │
│       ↓                                                     │
│  Load UserConnection → database_uri, schema_metadata (FULL) │
│       ↓                                                     │
│  Create SchemaQueryAgent(schema_metadata)                   │
│       ↓                                                     │
│  Execute Query → Return Response                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 New Flow (Published Agent API)

```
┌─────────────────────────────────────────────────────────────┐
│  NEW FLOW (ADDITIVE)                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  External Request with X-API-Key header                     │
│       ↓                                                     │
│  POST /api/v1/public/chat                                   │
│       ↓                                                     │
│  Validate API Key → get_published_agent_config()            │
│       ↓                                                     │
│  Check Rate Limit → rate_limit_service.check()              │
│       ↓                                                     │
│  Check CORS → validate_origin(allowed_domains)              │
│       ↓                                                     │
│  Load Owner's UserConnection → database_uri, schema_metadata│
│       ↓                                                     │
│  FILTER Schema → filter_schema(allowed_tables) ← KEY STEP   │
│       ↓                                                     │
│  Create SchemaQueryAgent(FILTERED_schema_metadata)          │
│       ↓                                                     │
│  Execute Query → Return Response                            │
│       ↓                                                     │
│  Log Usage → update_usage_stats()                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. API Specification

### 7.1 Developer Portal APIs (Organization - JWT Auth)

#### Create Published Agent

```
POST /api/developer/agents
Authorization: Bearer {jwt_token}

Request:
{
  "name": "Customer Support Agent",
  "allowed_tables": ["products", "orders", "categories"],
  "access_mode": "read_only",
  "rate_limit_per_minute": 60,
  "allowed_domains": ["*.mystore.com", "localhost:*"],
  "custom_instructions": "You are a helpful shopping assistant..."
}

Response (201):
{
  "id": "uuid-xxx",
  "name": "Customer Support Agent",
  "api_key": "pa_live_abc123...",  // SHOWN ONLY ONCE
  "endpoint": "https://api.example.com/api/v1/public/chat",
  "embed_code": "<script>...</script>",
  "created_at": "2025-01-13T10:00:00Z"
}
```

#### List Published Agents

```
GET /api/developer/agents
Authorization: Bearer {jwt_token}

Response (200):
{
  "agents": [
    {
      "id": "uuid-xxx",
      "name": "Customer Support Agent",
      "api_key_prefix": "pa_live_abc1...",  // Only prefix shown
      "allowed_tables": ["products", "orders"],
      "access_mode": "read_only",
      "is_active": true,
      "total_queries": 1234,
      "last_used_at": "2025-01-13T09:30:00Z",
      "created_at": "2025-01-10T10:00:00Z"
    }
  ]
}
```

#### Update Published Agent

```
PUT /api/developer/agents/{agent_id}
Authorization: Bearer {jwt_token}

Request:
{
  "name": "Updated Name",
  "allowed_tables": ["products"],
  "rate_limit_per_minute": 100,
  "is_active": false
}

Response (200):
{
  "id": "uuid-xxx",
  "name": "Updated Name",
  ...
}
```

#### Regenerate API Key

```
POST /api/developer/agents/{agent_id}/regenerate-key
Authorization: Bearer {jwt_token}

Response (200):
{
  "api_key": "pa_live_new123...",  // NEW KEY - SHOWN ONLY ONCE
  "message": "Previous API key has been revoked"
}
```

#### Delete Published Agent

```
DELETE /api/developer/agents/{agent_id}
Authorization: Bearer {jwt_token}

Response (204): No Content
```

#### Get Usage Statistics

```
GET /api/developer/agents/{agent_id}/usage?period=30d
Authorization: Bearer {jwt_token}

Response (200):
{
  "agent_id": "uuid-xxx",
  "period": "30d",
  "total_queries": 5000,
  "successful_queries": 4850,
  "failed_queries": 150,
  "avg_response_time_ms": 2300,
  "daily_breakdown": [
    {"date": "2025-01-13", "queries": 200},
    {"date": "2025-01-12", "queries": 180}
  ]
}
```

### 7.2 Public API (External - API Key Auth)

#### Chat Endpoint

```
POST /api/v1/public/chat
Headers:
  X-API-Key: pa_live_abc123...
  Origin: https://mystore.com

Request:
{
  "message": "Show me top 10 products by sales",
  "thread_id": "optional-thread-id"
}

Response (200):
{
  "response": "Here are the top 10 products...",
  "thread_id": "thread-uuid-xxx",
  "metadata": {
    "tables_queried": ["products", "orders"],
    "query_time_ms": 1500
  }
}
```

#### Error Responses

```
401 Unauthorized:
{
  "error": "invalid_api_key",
  "message": "The provided API key is invalid or expired"
}

403 Forbidden:
{
  "error": "domain_not_allowed",
  "message": "Origin domain is not in the allowed list"
}

429 Too Many Requests:
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit of 60 requests/minute exceeded",
  "retry_after": 45
}
```

---

## 8. Security Model

### 8.1 API Key Structure

```
Format: pa_[env]_[32-char-random-hex]

Examples:
- pa_live_a1b2c3d4e5f6...  (Production)
- pa_test_x9y8z7w6v5u4...  (Testing - future)

Storage:
- Original key shown ONCE at creation
- Only SHA-256 hash stored in database
- Prefix stored separately for display (pa_live_a1b2...)
```

### 8.2 Validation Flow

```python
def validate_api_key(api_key: str) -> PublishedAgentConfig:
    # 1. Parse prefix and key
    prefix, key_part = parse_api_key(api_key)  # "pa_live", "a1b2c3..."

    # 2. Hash the full key
    key_hash = sha256(api_key)

    # 3. Lookup by hash (indexed)
    config = db.query(PublishedAgentConfig).filter(
        api_key_hash == key_hash,
        is_active == True
    ).first()

    # 4. Validate expiration
    if config.expires_at and config.expires_at < now():
        raise ExpiredKeyError()

    return config
```

### 8.3 Domain Validation

```python
def validate_origin(origin: str, allowed_domains: list) -> bool:
    """
    Validate request origin against allowed domains.

    Supports:
    - Exact match: "mystore.com"
    - Wildcard subdomain: "*.mystore.com"
    - Wildcard port: "localhost:*"
    - All domains: ["*"] (not recommended)
    """
    for pattern in allowed_domains:
        if pattern == "*":
            return True
        if fnmatch(origin_host, pattern):
            return True
    return False
```

### 8.4 Rate Limiting

```python
# In-memory rate limiting (per API key)
# Uses sliding window algorithm

RATE_LIMIT_WINDOW = 60  # seconds

def check_rate_limit(api_key_id: str, limit: int) -> bool:
    """
    Check if request is within rate limit.

    Returns True if allowed, False if exceeded.
    """
    key = f"rate_limit:{api_key_id}"
    current_count = cache.get(key, 0)

    if current_count >= limit:
        return False

    cache.incr(key)
    cache.expire(key, RATE_LIMIT_WINDOW)
    return True
```

---

## 9. Schema Filtering (Core Logic)

### 9.1 Filter Function

```python
def filter_schema_for_published_agent(
    full_schema: dict,
    allowed_tables: list[str],
    access_mode: str = "read_only"
) -> dict:
    """
    Filter schema metadata to only include allowed tables.

    This is the KEY function that enables table-level access control
    without modifying the existing SchemaQueryAgent.

    Args:
        full_schema: Complete schema_metadata from owner's UserConnection
        allowed_tables: List of table names organization has allowed
        access_mode: "read_only" or "read_write"

    Returns:
        Filtered schema dict with same structure as original
    """
    allowed_set = {t.lower() for t in allowed_tables}

    filtered = {
        "database": full_schema.get("database"),
        "schemas": full_schema.get("schemas", []),
        "discovered_at": full_schema.get("discovered_at"),
        "tables": [],
        "relationships": [],
        "access_mode": access_mode,  # Added for agent prompt
    }

    # Filter tables
    for table in full_schema.get("tables", []):
        if table.get("name", "").lower() in allowed_set:
            filtered["tables"].append(table)

    # Filter relationships (only between allowed tables)
    for rel in full_schema.get("relationships", []):
        from_t = rel.get("from_table", "").lower()
        to_t = rel.get("to_table", "").lower()
        if from_t in allowed_set and to_t in allowed_set:
            filtered["relationships"].append(rel)

    filtered["table_count"] = len(filtered["tables"])

    return filtered
```

### 9.2 Usage in Public API

```python
# In public_agent_api.py

async def handle_public_chat(request, config, db):
    # 1. Get owner's full schema
    owner_connection = await db.get(UserConnection, config.user_id)
    full_schema = owner_connection.schema_metadata

    # 2. Filter to allowed tables only
    filtered_schema = filter_schema_for_published_agent(
        full_schema=full_schema,
        allowed_tables=config.allowed_tables,
        access_mode=config.access_mode
    )

    # 3. Agent only sees filtered schema
    # (It doesn't know about other tables - they don't exist in its view)
    agent = await create_schema_query_agent(
        database_uri=owner_connection.database_uri,
        schema_metadata=filtered_schema,  # FILTERED!
        custom_instructions=config.custom_instructions
    )

    return await agent.query(request.message)
```

---

## 10. Embed Code Template

### 10.1 Generated Code

```html
<!-- Published Agent Chat Widget -->
<!-- Agent: {agent_name} -->
<!-- Generated: {timestamp} -->

<div id="chat-widget-{agent_id}"></div>

<script src="https://cdn.openai.com/chatkit/v1/chatkit.min.js"></script>
<script>
(function() {
  const API_KEY = '{api_key}';
  const ENDPOINT = '{backend_url}/api/v1/public/chat';

  const chatkit = new ChatKit({
    container: '#chat-widget-{agent_id}',
    api: {
      url: ENDPOINT,
      fetch: async (url, options) => {
        const response = await fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
          }
        });
        return response;
      }
    },
    theme: {
      colorScheme: 'light'
    },
    header: {
      enabled: true,
      title: { text: '{agent_name}' }
    },
    composer: {
      placeholder: 'Ask a question...'
    },
    disclaimer: {
      text: 'Powered by AI'
    }
  });
})();
</script>
```

---

## 11. Database Schema

See: [data-model.md](./data-model.md)

---

## 12. Testing Requirements

### 12.1 Unit Tests

- [ ] API key generation (format, uniqueness)
- [ ] API key hashing and validation
- [ ] Schema filtering (tables, relationships)
- [ ] Rate limit checking
- [ ] Domain validation (wildcards)

### 12.2 Integration Tests

- [ ] Create published agent flow
- [ ] Public API with valid key
- [ ] Public API with invalid key
- [ ] Public API rate limiting
- [ ] Public API CORS validation
- [ ] Schema filtering with real data

### 12.3 E2E Tests

- [ ] Organization creates agent, gets embed code
- [ ] External site uses embed code successfully
- [ ] Query returns only allowed table data

---

## 13. Acceptance Criteria

### 13.1 Must Have (MVP)

- [ ] Organization can create published agent with table selection
- [ ] System generates unique API key
- [ ] Public API validates key and returns responses
- [ ] Schema filtering works correctly
- [ ] Rate limiting enforced
- [ ] Embed code generated and functional

### 13.2 Should Have

- [ ] Usage statistics displayed
- [ ] API key regeneration
- [ ] Custom instructions support
- [ ] Domain whitelisting

### 13.3 Could Have

- [ ] Streaming responses
- [ ] API key expiration
- [ ] Detailed analytics dashboard

---

## 14. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SQL injection via filtered schema | High | MCP server handles query execution (already secured) |
| API key leakage | High | Hash storage, show once, regeneration option |
| Rate limit bypass | Medium | Per-key tracking, sliding window algorithm |
| Schema filter bypass | High | Filter at data layer, not query layer |
| Performance degradation | Medium | Indexed lookups, caching |

---

## 15. Future Enhancements (Phase 2+)

1. **Tool Access Control**
   - Enable/disable specific tools per published agent
   - Tool-level permissions (e.g., Gmail read vs send)

2. **Advanced Analytics**
   - Query patterns analysis
   - Cost tracking per agent
   - Anomaly detection

3. **Webhook Notifications**
   - Notify organization on high usage
   - Alert on errors

4. **White-label Support**
   - Custom branding for embed widget
   - Custom domain for API endpoint

---

## 16. References

- [OpenAI ChatKit Documentation](https://platform.openai.com/docs/guides/chatkit)
- [Schema Agent Spec (Phase 9)](../009-schema-query-agent/spec.md)
- [Current Models](../../backend/app/models.py)
