# Developer Tools - Implementation Tasks

**Version:** 1.0.0
**Created:** 2025-01-13

---

## Task Overview

| Phase | Tasks | Estimated |
|-------|-------|-----------|
| Phase 1: Backend Models & Services | 6 tasks | 4-5 hours |
| Phase 2: Backend API Routes | 4 tasks | 3-4 hours |
| Phase 3: Frontend Pages | 6 tasks | 4-5 hours |
| Phase 4: Testing & Integration | 4 tasks | 2-3 hours |
| **Total** | **20 tasks** | **13-17 hours** |

---

## Phase 1: Backend Models & Services

### Task 1.1: Create Published Agent Model

**File:** `backend/app/models/published_agent.py`

**Description:** Create SQLAlchemy model for PublishedAgentConfig and PublishedAgentUsage.

**Acceptance Criteria:**
- [ ] PublishedAgentConfig model with all fields from data-model.md
- [ ] PublishedAgentUsage model for daily stats
- [ ] Proper indexes on api_key_hash, user_id, is_active
- [ ] Relationships defined (user, usage_records)
- [ ] Model imported in main models/__init__.py

**Code Location:**
```
backend/app/models/
├── __init__.py          # Add: from .published_agent import *
└── published_agent.py   # NEW FILE
```

**Dependencies:** None

---

### Task 1.2: Create API Key Service

**File:** `backend/app/services/api_key_service.py`

**Description:** Service for generating, hashing, and validating API keys.

**Functions to Implement:**
```python
def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        tuple: (full_key, hash, prefix)
        Example: ("pa_live_abc123...", "sha256...", "pa_live_abc1...")
    """

def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The full API key string

    Returns:
        SHA-256 hash of the key
    """

async def validate_api_key(
    api_key: str,
    db: AsyncSession
) -> PublishedAgentConfig:
    """
    Validate an API key and return the config.

    Args:
        api_key: The full API key from request header
        db: Database session

    Returns:
        PublishedAgentConfig if valid

    Raises:
        HTTPException(401): If key is invalid, inactive, or expired
    """
```

**Acceptance Criteria:**
- [ ] Key format: `pa_live_[32-char-hex]`
- [ ] Uses `secrets.token_hex(16)` for randomness
- [ ] SHA-256 hashing via `hashlib`
- [ ] Prefix extraction for display
- [ ] Validation checks: exists, is_active, expires_at

**Dependencies:** Task 1.1

---

### Task 1.3: Create Schema Filter Service

**File:** `backend/app/services/schema_filter_service.py`

**Description:** Service for filtering schema_metadata to only allowed tables.

**Functions to Implement:**
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
        full_schema: Complete schema_metadata from UserConnection
        allowed_tables: List of table names to include
        access_mode: "read_only" or "read_write"

    Returns:
        Filtered schema dict with same structure as original

    Example:
        Input:  {tables: [products, orders, users, admin]}
        Filter: ["products", "orders"]
        Output: {tables: [products, orders]}
    """
```

**Acceptance Criteria:**
- [ ] Filters tables by name (case-insensitive)
- [ ] Filters relationships (only between allowed tables)
- [ ] Preserves schema structure (database, schemas, discovered_at)
- [ ] Adds access_mode to filtered schema for agent prompt
- [ ] Updates table_count
- [ ] Handles empty allowed_tables gracefully

**Dependencies:** None

---

### Task 1.4: Create Rate Limit Service

**File:** `backend/app/services/rate_limit_service.py`

**Description:** In-memory sliding window rate limiter per API key.

**Class to Implement:**
```python
class RateLimitService:
    """
    In-memory sliding window rate limiter.

    Uses a deque to track request timestamps within the window.
    Thread-safe for async operations.
    """

    def __init__(self, window_seconds: int = 60):
        self._window = window_seconds
        self._cache: dict[str, deque] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        key_id: str,
        limit: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Args:
            key_id: The API key ID (or hash)
            limit: Max requests per window

        Returns:
            tuple: (allowed, remaining, reset_seconds)
        """

    async def get_headers(
        self,
        key_id: str,
        limit: int
    ) -> dict[str, str]:
        """
        Get rate limit headers for response.

        Returns:
            dict: {
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "95",
                "X-RateLimit-Reset": "45"
            }
        """
```

**Acceptance Criteria:**
- [ ] Sliding window algorithm (not fixed window)
- [ ] Returns (allowed, remaining, reset_time)
- [ ] Thread-safe with asyncio.Lock
- [ ] Memory cleanup for old entries
- [ ] Generates rate limit headers

**Dependencies:** None

---

### Task 1.5: Create Published Agent Service

**File:** `backend/app/services/published_agent_service.py`

**Description:** Business logic layer for published agent CRUD operations.

**Class to Implement:**
```python
class PublishedAgentService:
    """
    Business logic for published agent management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_agent(
        self,
        user_id: int,
        config: CreateAgentRequest
    ) -> tuple[PublishedAgentConfig, str]:
        """
        Create a new published agent.

        Returns:
            tuple: (config, api_key)
            Note: api_key is only returned at creation time
        """

    async def list_agents(
        self,
        user_id: int
    ) -> list[PublishedAgentConfig]:
        """List all agents for a user."""

    async def get_agent(
        self,
        agent_id: str,
        user_id: int
    ) -> PublishedAgentConfig:
        """Get a specific agent (validates ownership)."""

    async def update_agent(
        self,
        agent_id: str,
        user_id: int,
        updates: UpdateAgentRequest
    ) -> PublishedAgentConfig:
        """Update agent configuration."""

    async def delete_agent(
        self,
        agent_id: str,
        user_id: int
    ) -> bool:
        """Delete an agent."""

    async def regenerate_key(
        self,
        agent_id: str,
        user_id: int
    ) -> str:
        """
        Regenerate API key for an agent.

        Returns:
            New API key (shown only once)
        """

    async def record_query(
        self,
        agent_id: str,
        success: bool,
        response_time_ms: int,
        tokens: int = 0
    ) -> None:
        """Record a query for usage stats."""

    async def get_usage_stats(
        self,
        agent_id: str,
        user_id: int,
        days: int = 30
    ) -> dict:
        """Get usage statistics for an agent."""
```

**Acceptance Criteria:**
- [ ] All CRUD operations with ownership validation
- [ ] API key generation on create
- [ ] Key regeneration revokes old key
- [ ] Usage stats aggregation from PublishedAgentUsage
- [ ] Proper error handling (404, 403)

**Dependencies:** Task 1.1, Task 1.2

---

### Task 1.6: Create Pydantic Schemas

**File:** `backend/app/schemas/developer_portal.py`

**Description:** Request/response models for API endpoints.

**Models to Implement:**
```python
# Request Models
class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    allowed_tables: list[str] = Field(..., min_items=1)
    access_mode: Literal["read_only", "read_write"] = "read_only"
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    allowed_domains: list[str] = Field(default=["*"])
    custom_instructions: Optional[str] = None

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_tables: Optional[list[str]] = None
    access_mode: Optional[Literal["read_only", "read_write"]] = None
    rate_limit_per_minute: Optional[int] = None
    allowed_domains: Optional[list[str]] = None
    custom_instructions: Optional[str] = None
    is_active: Optional[bool] = None

class PublicChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    thread_id: Optional[str] = None

# Response Models
class AgentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    api_key_prefix: str  # Only prefix shown
    allowed_tables: list[str]
    access_mode: str
    rate_limit_per_minute: int
    allowed_domains: list[str]
    is_active: bool
    total_queries: int
    last_used_at: Optional[datetime]
    created_at: datetime

class AgentCreatedResponse(AgentResponse):
    api_key: str  # Full key shown ONLY at creation
    endpoint: str
    embed_code: str

class PublicChatResponse(BaseModel):
    response: str
    thread_id: str
    metadata: Optional[dict] = None
```

**Acceptance Criteria:**
- [ ] All request models with validation
- [ ] All response models
- [ ] Proper Field constraints
- [ ] Config for ORM mode

**Dependencies:** None

---

## Phase 2: Backend API Routes

### Task 2.1: Create Developer Portal Router

**File:** `backend/app/routers/developer_portal.py`

**Description:** API endpoints for organization to manage published agents.

**Endpoints to Implement:**
```python
router = APIRouter(prefix="/api/developer", tags=["developer"])

@router.post("/agents", response_model=AgentCreatedResponse)
async def create_published_agent(
    body: CreateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new published agent."""

@router.get("/agents", response_model=list[AgentResponse])
async def list_published_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all published agents for current user."""

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_published_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific published agent."""

@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_published_agent(
    agent_id: str,
    body: UpdateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a published agent."""

@router.delete("/agents/{agent_id}", status_code=204)
async def delete_published_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a published agent."""

@router.post("/agents/{agent_id}/regenerate-key")
async def regenerate_api_key(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate API key for an agent."""

@router.get("/agents/{agent_id}/usage")
async def get_usage_statistics(
    agent_id: str,
    period: int = Query(default=30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get usage statistics for an agent."""

@router.get("/agents/{agent_id}/embed-code")
async def get_embed_code(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get embed code snippet for an agent."""
```

**Acceptance Criteria:**
- [ ] All endpoints implemented
- [ ] JWT authentication via get_current_user
- [ ] Proper error responses (400, 401, 403, 404)
- [ ] Validates allowed_tables exist in user's schema
- [ ] Generates embed code on create/get

**Dependencies:** Task 1.5, Task 1.6

---

### Task 2.2: Create Public Agent API Router

**File:** `backend/app/routers/public_agent_api.py`

**Description:** Public API endpoint for external users to chat with published agents.

**Endpoints to Implement:**
```python
router = APIRouter(prefix="/api/v1/public", tags=["public"])

# Singleton rate limiter
_rate_limiter = RateLimitService()

async def get_api_key_config(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> PublishedAgentConfig:
    """Dependency to validate API key."""

@router.post("/chat", response_model=PublicChatResponse)
async def public_chat(
    request: Request,
    body: PublicChatRequest,
    config: PublishedAgentConfig = Depends(get_api_key_config),
    db: AsyncSession = Depends(get_db)
):
    """
    Public chat endpoint for published agents.

    Flow:
    1. Validate API key (via dependency)
    2. Check rate limit
    3. Validate CORS origin
    4. Load owner's database config
    5. Filter schema to allowed tables
    6. Create agent with filtered schema
    7. Execute query
    8. Record usage
    9. Return response
    """
```

**Acceptance Criteria:**
- [ ] API key validation via header
- [ ] Rate limiting with proper headers
- [ ] CORS origin validation
- [ ] Schema filtering applied
- [ ] Uses existing SchemaQueryAgent
- [ ] Records usage stats
- [ ] Proper error responses (401, 403, 429)

**Dependencies:** Task 1.2, Task 1.3, Task 1.4, Task 1.5

---

### Task 2.3: Create Domain Validation Utility

**File:** `backend/app/services/domain_validator.py`

**Description:** Utility for validating request origin against allowed domains.

**Function to Implement:**
```python
def validate_origin(
    origin: str,
    allowed_domains: list[str]
) -> bool:
    """
    Validate request origin against allowed domain patterns.

    Supports:
    - Exact match: "mystore.com"
    - Wildcard subdomain: "*.mystore.com"
    - Wildcard port: "localhost:*"
    - Any origin: "*"

    Args:
        origin: The Origin header value
        allowed_domains: List of allowed domain patterns

    Returns:
        True if origin is allowed

    Examples:
        validate_origin("https://shop.mystore.com", ["*.mystore.com"]) → True
        validate_origin("https://evil.com", ["*.mystore.com"]) → False
        validate_origin("http://localhost:3000", ["localhost:*"]) → True
    """
```

**Acceptance Criteria:**
- [ ] Exact domain matching
- [ ] Wildcard subdomain matching (*.example.com)
- [ ] Wildcard port matching (localhost:*)
- [ ] Protocol handling (strips https://)
- [ ] Empty origin handling
- [ ] "*" allows all

**Dependencies:** None

---

### Task 2.4: Register Routers in Main App

**File:** `backend/app/main.py`

**Description:** Register new routers in FastAPI app.

**Changes:**
```python
# Add imports
from app.routers import developer_portal, public_agent_api

# Add routers
app.include_router(developer_portal.router)
app.include_router(public_agent_api.router)

# Add CORS for public API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Public API handles its own CORS
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

**Acceptance Criteria:**
- [ ] Both routers registered
- [ ] CORS middleware updated
- [ ] No changes to existing routers
- [ ] API docs show new endpoints

**Dependencies:** Task 2.1, Task 2.2

---

## Phase 3: Frontend Pages

### Task 3.1: Create Developer Tools API Client

**File:** `frontend/lib/developer-tools-api.ts`

**Description:** TypeScript API client for developer tools endpoints.

**Functions to Implement:**
```typescript
// Types
interface PublishedAgent {
  id: string;
  name: string;
  description?: string;
  api_key_prefix: string;
  allowed_tables: string[];
  access_mode: 'read_only' | 'read_write';
  rate_limit_per_minute: number;
  allowed_domains: string[];
  is_active: boolean;
  total_queries: number;
  last_used_at?: string;
  created_at: string;
}

interface CreateAgentRequest {
  name: string;
  description?: string;
  allowed_tables: string[];
  access_mode?: 'read_only' | 'read_write';
  rate_limit_per_minute?: number;
  allowed_domains?: string[];
  custom_instructions?: string;
}

interface AgentCreatedResponse extends PublishedAgent {
  api_key: string;
  endpoint: string;
  embed_code: string;
}

// API Functions
export async function createPublishedAgent(
  data: CreateAgentRequest
): Promise<AgentCreatedResponse>;

export async function listPublishedAgents(): Promise<PublishedAgent[]>;

export async function getPublishedAgent(id: string): Promise<PublishedAgent>;

export async function updatePublishedAgent(
  id: string,
  data: Partial<CreateAgentRequest>
): Promise<PublishedAgent>;

export async function deletePublishedAgent(id: string): Promise<void>;

export async function regenerateApiKey(
  id: string
): Promise<{ api_key: string }>;

export async function getUsageStats(
  id: string,
  period?: number
): Promise<UsageStats>;

export async function getEmbedCode(
  id: string
): Promise<{ embed_code: string }>;
```

**Acceptance Criteria:**
- [ ] All API functions implemented
- [ ] Proper TypeScript types
- [ ] Uses existing auth token handling
- [ ] Error handling with typed responses

**Dependencies:** Phase 2 complete

---

### Task 3.2: Create Developer Tools Main Page

**File:** `frontend/app/dashboard/developer-tools/page.tsx`

**Description:** Main page for managing published agents.

**UI Components:**
- Header with title and "Create Agent" button
- Prerequisites check (database connected?)
- List of published agents (AgentCard components)
- Empty state when no agents

**Acceptance Criteria:**
- [ ] Page loads and fetches agents
- [ ] Shows prerequisite warning if no database
- [ ] Displays agent cards
- [ ] "Create Agent" opens modal
- [ ] Responsive design

**Dependencies:** Task 3.1

---

### Task 3.3: Create Agent Card Component

**File:** `frontend/app/dashboard/developer-tools/components/agent-card.tsx`

**Description:** Card component displaying published agent info.

**UI Elements:**
- Agent name and status badge
- API key prefix with copy button
- Allowed tables list
- Access mode and rate limit
- Usage stats (total queries, last used)
- Action buttons: View Code, Edit, Regenerate Key, Delete

**Acceptance Criteria:**
- [ ] Displays all agent info
- [ ] Copy API key prefix
- [ ] Action buttons work
- [ ] Confirmation for delete/regenerate
- [ ] Loading states

**Dependencies:** Task 3.1

---

### Task 3.4: Create Agent Modal Component

**File:** `frontend/app/dashboard/developer-tools/components/create-agent-modal.tsx`

**Description:** Modal wizard for creating new published agent.

**Steps:**
1. Basic Info (name, description)
2. Table Selection (multi-select from available tables)
3. Permissions (access mode, rate limit)
4. Domain Whitelist
5. Custom Instructions (optional)

**Acceptance Criteria:**
- [ ] Multi-step wizard
- [ ] Table selector fetches from user's schema
- [ ] Validation on each step
- [ ] Shows generated API key on success
- [ ] Copy API key functionality
- [ ] Shows embed code preview

**Dependencies:** Task 3.1, Task 3.5

---

### Task 3.5: Create Table Selector Component

**File:** `frontend/app/dashboard/developer-tools/components/table-selector.tsx`

**Description:** Multi-select component for choosing tables.

**Features:**
- List all tables from user's schema_metadata
- Checkbox selection
- Show column count per table
- Select All / Deselect All buttons
- Search/filter tables

**Acceptance Criteria:**
- [ ] Fetches tables from schema
- [ ] Multi-select functionality
- [ ] Shows table metadata
- [ ] Select/deselect all
- [ ] Filter by name

**Dependencies:** Task 3.1

---

### Task 3.6: Create Embed Code Viewer Component

**File:** `frontend/app/dashboard/developer-tools/components/embed-code-viewer.tsx`

**Description:** Modal/panel showing embed code snippet.

**Features:**
- Syntax highlighted code block
- Copy to clipboard button
- API details section
- Integration instructions

**Acceptance Criteria:**
- [ ] Displays formatted code
- [ ] Copy button works
- [ ] Shows API key and endpoint
- [ ] Basic integration guide

**Dependencies:** Task 3.1

---

## Phase 4: Testing & Integration

### Task 4.1: Backend Unit Tests

**Files:**
- `backend/tests/test_api_key_service.py`
- `backend/tests/test_schema_filter_service.py`
- `backend/tests/test_rate_limit_service.py`

**Test Cases:**
```python
# API Key Tests
def test_generate_api_key_format():
    """Key should match pa_live_[32 hex chars]"""

def test_hash_api_key_consistent():
    """Same key should produce same hash"""

def test_validate_api_key_success():
    """Valid key should return config"""

def test_validate_api_key_invalid():
    """Invalid key should raise 401"""

# Schema Filter Tests
def test_filter_tables_basic():
    """Should only include allowed tables"""

def test_filter_relationships():
    """Should only include relationships between allowed tables"""

def test_filter_empty_allowed():
    """Should handle empty allowed_tables"""

# Rate Limit Tests
def test_rate_limit_under():
    """Under limit should return allowed=True"""

def test_rate_limit_exceeded():
    """Exceeded limit should return allowed=False"""

def test_rate_limit_sliding_window():
    """Old requests should expire"""
```

**Acceptance Criteria:**
- [ ] All service functions tested
- [ ] Edge cases covered
- [ ] Tests pass

**Dependencies:** Phase 1 complete

---

### Task 4.2: Backend Integration Tests

**File:** `backend/tests/test_developer_portal_integration.py`

**Test Cases:**
```python
@pytest.mark.asyncio
async def test_create_agent_success():
    """Should create agent and return API key"""

@pytest.mark.asyncio
async def test_public_chat_valid_key():
    """Should process chat with valid API key"""

@pytest.mark.asyncio
async def test_public_chat_invalid_key():
    """Should return 401 for invalid key"""

@pytest.mark.asyncio
async def test_public_chat_rate_limited():
    """Should return 429 when rate limit exceeded"""

@pytest.mark.asyncio
async def test_schema_filtering_applied():
    """Agent should only see allowed tables"""
```

**Acceptance Criteria:**
- [ ] Full API flow tested
- [ ] Error cases tested
- [ ] Tests pass

**Dependencies:** Phase 2 complete

---

### Task 4.3: Frontend Component Tests

**Files:**
- `frontend/__tests__/developer-tools.test.tsx`

**Test Cases:**
- Page renders correctly
- Create modal opens/closes
- Form validation works
- API calls triggered correctly

**Acceptance Criteria:**
- [ ] Component rendering tested
- [ ] User interactions tested
- [ ] Tests pass

**Dependencies:** Phase 3 complete

---

### Task 4.4: End-to-End Testing

**Description:** Manual E2E testing of full flow.

**Test Scenarios:**
1. Organization creates published agent
2. Organization gets embed code
3. External site uses embed code
4. User queries via widget
5. Response returns successfully
6. Usage stats updated

**Acceptance Criteria:**
- [ ] Full flow works
- [ ] No console errors
- [ ] Proper error handling
- [ ] Performance acceptable

**Dependencies:** All phases complete

---

## Implementation Order

```
Week 1, Day 1:
├── Task 1.1: Create Published Agent Model
├── Task 1.2: Create API Key Service
├── Task 1.3: Create Schema Filter Service
└── Task 1.4: Create Rate Limit Service

Week 1, Day 2:
├── Task 1.5: Create Published Agent Service
├── Task 1.6: Create Pydantic Schemas
├── Task 2.1: Create Developer Portal Router
└── Task 2.2: Create Public Agent API Router

Week 1, Day 3:
├── Task 2.3: Create Domain Validation Utility
├── Task 2.4: Register Routers in Main App
├── Task 4.1: Backend Unit Tests
└── Task 4.2: Backend Integration Tests

Week 2, Day 1:
├── Task 3.1: Create Developer Tools API Client
├── Task 3.2: Create Developer Tools Main Page
└── Task 3.3: Create Agent Card Component

Week 2, Day 2:
├── Task 3.4: Create Agent Modal Component
├── Task 3.5: Create Table Selector Component
└── Task 3.6: Create Embed Code Viewer Component

Week 2, Day 3:
├── Task 4.3: Frontend Component Tests
├── Task 4.4: End-to-End Testing
└── Polish & Documentation
```

---

## Definition of Done

For each task:
- [ ] Code implemented
- [ ] Code reviewed (self-review for solo)
- [ ] Tests pass
- [ ] No TypeScript/Python errors
- [ ] Documented (inline comments)
- [ ] Committed to feature branch

For the feature:
- [ ] All tasks complete
- [ ] E2E testing passed
- [ ] No regressions in existing features
- [ ] Merged to main branch
- [ ] Deployed to staging
