# Developer Tools - Requirements Checklist

**Version:** 1.0.0
**Created:** 2025-01-13

---

## Pre-Implementation Checklist

### Architecture Review
- [ ] No modifications to existing schema_query_agent.py
- [ ] No modifications to existing schema_agent.py router
- [ ] No modifications to existing schema_discovery.py (only additions)
- [ ] No modifications to existing models.py (only imports)
- [ ] All new code in separate files
- [ ] Clean separation: models, services, routers

### Database Review
- [ ] PublishedAgentConfig model designed
- [ ] PublishedAgentUsage model designed
- [ ] Proper indexes defined
- [ ] No impact on existing tables

---

## Backend Implementation Checklist

### Models (`backend/app/models/published_agent.py`)
- [ ] PublishedAgentConfig model created
  - [ ] id (UUID, primary key)
  - [ ] user_id (FK to users)
  - [ ] api_key_hash (unique, indexed)
  - [ ] api_key_prefix
  - [ ] name
  - [ ] description
  - [ ] allowed_tables (JSONB)
  - [ ] access_mode
  - [ ] allowed_domains (JSONB)
  - [ ] rate_limit_per_minute
  - [ ] custom_instructions
  - [ ] allowed_tools (JSONB, future)
  - [ ] is_active
  - [ ] created_at, updated_at, expires_at
  - [ ] total_queries, last_used_at

- [ ] PublishedAgentUsage model created
  - [ ] id (serial)
  - [ ] published_agent_id (FK)
  - [ ] date
  - [ ] query_count, successful_count, failed_count
  - [ ] total_tokens, total_response_time_ms

- [ ] Models imported in `__init__.py`
- [ ] Tables auto-created on startup

### Services

#### API Key Service (`backend/app/services/api_key_service.py`)
- [ ] generate_api_key() → (key, hash, prefix)
- [ ] hash_api_key(key) → hash
- [ ] validate_api_key(key, db) → config or 401
- [ ] Key format: `pa_live_[32-hex]`
- [ ] Uses secrets.token_hex()
- [ ] Uses hashlib.sha256()

#### Schema Filter Service (`backend/app/services/schema_filter_service.py`)
- [ ] filter_schema_for_published_agent(full_schema, allowed_tables, access_mode)
- [ ] Filters tables correctly
- [ ] Filters relationships correctly
- [ ] Case-insensitive table matching
- [ ] Preserves schema structure
- [ ] Handles empty allowed_tables

#### Rate Limit Service (`backend/app/services/rate_limit_service.py`)
- [ ] RateLimitService class
- [ ] check_rate_limit(key_id, limit) → (allowed, remaining, reset)
- [ ] get_headers(key_id, limit) → dict
- [ ] Sliding window algorithm
- [ ] Thread-safe with asyncio.Lock
- [ ] Memory cleanup for old entries

#### Published Agent Service (`backend/app/services/published_agent_service.py`)
- [ ] create_agent(user_id, config) → (agent, api_key)
- [ ] list_agents(user_id) → list
- [ ] get_agent(agent_id, user_id) → agent
- [ ] update_agent(agent_id, user_id, updates) → agent
- [ ] delete_agent(agent_id, user_id) → bool
- [ ] regenerate_key(agent_id, user_id) → new_key
- [ ] record_query(agent_id, success, time_ms)
- [ ] get_usage_stats(agent_id, user_id, days)
- [ ] Validates table names against user's schema
- [ ] Ownership validation on all operations

#### Domain Validator (`backend/app/services/domain_validator.py`)
- [ ] validate_origin(origin, allowed_domains) → bool
- [ ] Supports exact match
- [ ] Supports wildcard subdomain (*.example.com)
- [ ] Supports wildcard port (localhost:*)
- [ ] Supports "*" for all
- [ ] Handles missing Origin header

### Schemas (`backend/app/schemas/developer_portal.py`)
- [ ] CreateAgentRequest
- [ ] UpdateAgentRequest
- [ ] PublicChatRequest
- [ ] AgentResponse
- [ ] AgentCreatedResponse
- [ ] PublicChatResponse
- [ ] Proper validation constraints
- [ ] ORM mode enabled

### Routers

#### Developer Portal (`backend/app/routers/developer_portal.py`)
- [ ] POST /api/developer/agents → create
- [ ] GET /api/developer/agents → list
- [ ] GET /api/developer/agents/{id} → get
- [ ] PUT /api/developer/agents/{id} → update
- [ ] DELETE /api/developer/agents/{id} → delete
- [ ] POST /api/developer/agents/{id}/regenerate-key
- [ ] GET /api/developer/agents/{id}/usage
- [ ] GET /api/developer/agents/{id}/embed-code
- [ ] JWT authentication on all endpoints
- [ ] Proper error responses

#### Public Agent API (`backend/app/routers/public_agent_api.py`)
- [ ] POST /api/v1/public/chat
- [ ] API key validation via X-API-Key header
- [ ] Rate limit checking
- [ ] CORS origin validation
- [ ] Schema filtering applied
- [ ] Uses existing SchemaQueryAgent
- [ ] Records usage stats
- [ ] Rate limit headers in response
- [ ] Proper error responses (401, 403, 429)

### Main App (`backend/app/main.py`)
- [ ] developer_portal router included
- [ ] public_agent_api router included
- [ ] CORS middleware updated
- [ ] No changes to existing routers

---

## Frontend Implementation Checklist

### API Client (`frontend/lib/developer-tools-api.ts`)
- [ ] TypeScript interfaces defined
- [ ] createPublishedAgent()
- [ ] listPublishedAgents()
- [ ] getPublishedAgent()
- [ ] updatePublishedAgent()
- [ ] deletePublishedAgent()
- [ ] regenerateApiKey()
- [ ] getUsageStats()
- [ ] getEmbedCode()
- [ ] Uses existing auth handling
- [ ] Proper error handling

### Main Page (`frontend/app/dashboard/developer-tools/page.tsx`)
- [ ] Page renders
- [ ] Fetches published agents
- [ ] Shows prerequisite warning if no database
- [ ] Displays agent cards
- [ ] "Create Agent" button works
- [ ] Empty state handling
- [ ] Loading state
- [ ] Error handling

### Agent Card (`frontend/app/dashboard/developer-tools/components/agent-card.tsx`)
- [ ] Displays agent info
- [ ] Status badge (active/inactive)
- [ ] API key prefix with copy
- [ ] Tables list
- [ ] Access mode and rate limit
- [ ] Usage stats
- [ ] View Code button
- [ ] Edit button
- [ ] Regenerate Key button (with confirm)
- [ ] Delete button (with confirm)

### Create Agent Modal (`frontend/app/dashboard/developer-tools/components/create-agent-modal.tsx`)
- [ ] Opens/closes correctly
- [ ] Step 1: Basic info
- [ ] Step 2: Table selection
- [ ] Step 3: Permissions
- [ ] Step 4: Domain whitelist
- [ ] Step 5: Custom instructions
- [ ] Validation on each step
- [ ] Submit creates agent
- [ ] Shows API key on success
- [ ] Copy API key functionality
- [ ] Shows embed code

### Table Selector (`frontend/app/dashboard/developer-tools/components/table-selector.tsx`)
- [ ] Fetches tables from schema
- [ ] Multi-select checkboxes
- [ ] Column count per table
- [ ] Select All button
- [ ] Deselect All button
- [ ] Filter/search

### Embed Code Viewer (`frontend/app/dashboard/developer-tools/components/embed-code-viewer.tsx`)
- [ ] Displays formatted code
- [ ] Syntax highlighting
- [ ] Copy to clipboard
- [ ] API details section
- [ ] Integration instructions

---

## Testing Checklist

### Backend Unit Tests
- [ ] test_generate_api_key_format
- [ ] test_hash_api_key_consistent
- [ ] test_validate_api_key_success
- [ ] test_validate_api_key_invalid
- [ ] test_filter_tables_basic
- [ ] test_filter_relationships
- [ ] test_filter_empty_allowed
- [ ] test_rate_limit_under
- [ ] test_rate_limit_exceeded
- [ ] test_rate_limit_sliding_window
- [ ] All tests pass

### Backend Integration Tests
- [ ] test_create_agent_success
- [ ] test_public_chat_valid_key
- [ ] test_public_chat_invalid_key
- [ ] test_public_chat_rate_limited
- [ ] test_schema_filtering_applied
- [ ] All tests pass

### Frontend Tests
- [ ] Page rendering tests
- [ ] Component tests
- [ ] User interaction tests
- [ ] All tests pass

### E2E Testing
- [ ] Create agent flow works
- [ ] Embed code generated correctly
- [ ] Public API accepts key
- [ ] Query returns response
- [ ] Rate limiting works
- [ ] CORS validation works
- [ ] Usage stats updated

---

## Security Checklist

- [ ] API keys hashed before storage
- [ ] API keys shown only once
- [ ] Rate limiting enforced
- [ ] CORS validation enforced
- [ ] Database credentials never exposed
- [ ] SQL injection prevented (via MCP)
- [ ] Ownership validation on all operations
- [ ] Expired keys rejected

---

## Performance Checklist

- [ ] API key lookup is O(1) via index
- [ ] Schema filtering < 10ms
- [ ] Rate limit check < 1ms
- [ ] No N+1 queries
- [ ] Memory cleanup for rate limiter

---

## Documentation Checklist

- [ ] spec.md complete
- [ ] data-model.md complete
- [ ] plan.md complete
- [ ] tasks.md complete
- [ ] API documented (OpenAPI/Swagger)
- [ ] Embed code has integration guide

---

## Deployment Checklist

- [ ] Database migrations run
- [ ] New tables created
- [ ] Environment variables set (if any)
- [ ] CORS configured
- [ ] API accessible
- [ ] No errors in logs

---

## Post-Implementation Checklist

- [ ] No regressions in existing features
- [ ] Schema Agent still works
- [ ] Organization flow unchanged
- [ ] All tests pass
- [ ] Code committed to feature branch
- [ ] PR created and reviewed
- [ ] Merged to main
- [ ] Deployed to production
