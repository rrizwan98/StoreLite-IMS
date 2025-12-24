# Tasks: Google Search Tool Integration

**Branch**: `011-google-search-tool` | **Date**: 2025-12-24 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Task Overview

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase 1: Core Infrastructure | 4 tasks | ⬜ Pending |
| Phase 2: Agent Integration | 4 tasks | ⬜ Pending |
| Phase 3: Testing & Validation | 3 tasks | ⬜ Pending |

---

## Phase 1: Core Infrastructure

### Task 1.1: Add google-genai Package

**Priority**: P0 (Blocker)
**Estimated Time**: 5 minutes
**Dependencies**: None

**Description**: Add the Google Gen AI Python SDK to backend requirements.

**TDD Cycle**:
- RED: N/A (dependency task)
- GREEN: Package installs successfully
- REFACTOR: N/A

**Acceptance Criteria**:
- [ ] `google-genai>=1.0.0` added to `backend/requirements.txt`
- [ ] Package installs without errors: `pip install -r requirements.txt`
- [ ] Import works: `from google import genai`

**File Changes**:
```
MODIFY: backend/requirements.txt
  - ADD: google-genai>=1.0.0
```

---

### Task 1.2: Add Google Search to Tools Registry

**Priority**: P0 (Blocker)
**Estimated Time**: 15 minutes
**Dependencies**: None

**Description**: Register Google Search as a System Tool in the tools registry with `auth_type: none`.

**TDD Cycle**:
- RED: Write tests in `tests/unit/test_tools_registry.py`
  - `test_google_search_in_registry`
  - `test_google_search_auth_type_none`
  - `test_google_search_is_enabled`
  - `test_google_search_not_beta`
- GREEN: Add SystemTool entry to `SYSTEM_TOOLS` dict
- REFACTOR: Ensure consistent formatting

**Acceptance Criteria**:
- [ ] Tests written and initially fail (RED)
- [ ] `google_search` SystemTool added to registry
- [ ] `auth_type` is "none"
- [ ] `is_enabled` is True
- [ ] `is_beta` is False
- [ ] Category is "utilities"
- [ ] All tests pass (GREEN)

**File Changes**:
```
CREATE: backend/tests/unit/test_google_search_registry.py
  - TestGoogleSearchToolRegistry class
  - 5 unit tests for registry entry

MODIFY: backend/app/tools/registry.py
  - ADD: google_search SystemTool entry
```

**Implementation Code**:
```python
# In registry.py, add to SYSTEM_TOOLS dict:
"google_search": SystemTool(
    id="google_search",
    name="Google Search",
    description="Search the web for real-time information, documentation, news, and current events",
    icon="search",
    category="utilities",
    auth_type="none",
    is_enabled=True,
    is_beta=False,
),
```

---

### Task 1.3: Create Google Search Service

**Priority**: P0 (Blocker)
**Estimated Time**: 45 minutes
**Dependencies**: Task 1.1

**Description**: Create the GoogleSearchService that uses Gemini's google_search tool to perform web searches and return formatted results with sources.

**TDD Cycle**:
- RED: Write tests in `tests/unit/test_google_search_service.py`
  - `test_search_returns_result`
  - `test_search_returns_sources`
  - `test_search_handles_error`
  - `test_format_with_sources`
  - `test_format_handles_empty_sources`
- GREEN: Implement GoogleSearchService class
- REFACTOR: Clean up async handling

**Acceptance Criteria**:
- [ ] Tests written and initially fail (RED)
- [ ] `GoogleSearchService` class created
- [ ] `SearchSource` dataclass with title and url
- [ ] `GoogleSearchResult` dataclass with text, sources, search_queries, success, error
- [ ] `search()` async method calls Gemini with google_search tool
- [ ] `format_response_with_sources()` returns markdown
- [ ] Sources formatted as `[Title](URL)` links
- [ ] Error handling returns graceful error message
- [ ] All tests pass (GREEN)

**File Changes**:
```
CREATE: backend/tests/unit/test_google_search_service.py
  - TestGoogleSearchService class
  - 5+ unit tests with mocks

CREATE: backend/app/services/google_search.py
  - SearchSource dataclass
  - GoogleSearchResult dataclass
  - GoogleSearchService class
    - __init__(api_key, model)
    - search(query) -> GoogleSearchResult
    - format_response_with_sources(result) -> str
```

---

### Task 1.4: Create Helper Functions for Tool Detection

**Priority**: P1
**Estimated Time**: 20 minutes
**Dependencies**: None

**Description**: Create helper functions to detect Google Search tool prefix and strip it from queries.

**TDD Cycle**:
- RED: Write tests
  - `test_should_use_google_search_with_prefix`
  - `test_should_use_google_search_without_prefix`
  - `test_strip_tool_prefix`
  - `test_strip_preserves_query`
- GREEN: Implement helper functions
- REFACTOR: N/A

**Acceptance Criteria**:
- [ ] Tests written and initially fail (RED)
- [ ] `should_use_google_search(query) -> bool` detects `[TOOL:GOOGLE_SEARCH]` prefix
- [ ] `strip_tool_prefix(query) -> str` removes prefix and returns clean query
- [ ] Functions handle edge cases (whitespace, case)
- [ ] All tests pass (GREEN)

**File Changes**:
```
CREATE: backend/app/services/google_search.py (extend from Task 1.3)
  - ADD: should_use_google_search(query) function
  - ADD: strip_tool_prefix(query) function

CREATE: backend/tests/unit/test_google_search_helpers.py
  - TestGoogleSearchHelpers class
  - 4 unit tests
```

**Implementation Code**:
```python
GOOGLE_SEARCH_PREFIX = "[TOOL:GOOGLE_SEARCH]"

def should_use_google_search(query: str) -> bool:
    """Check if query starts with Google Search tool prefix."""
    return query.strip().startswith(GOOGLE_SEARCH_PREFIX)

def strip_tool_prefix(query: str) -> str:
    """Remove [TOOL:GOOGLE_SEARCH] prefix from query."""
    query = query.strip()
    if query.startswith(GOOGLE_SEARCH_PREFIX):
        return query[len(GOOGLE_SEARCH_PREFIX):].strip()
    return query
```

---

## Phase 2: Agent Integration

### Task 2.1: Update Schema Agent System Prompt

**Priority**: P0 (Blocker)
**Estimated Time**: 20 minutes
**Dependencies**: None

**Description**: Add Google Search rules to the Schema Agent's system prompt to enable both user-forced and agent-autonomous search modes.

**TDD Cycle**:
- RED: N/A (prompt is tested via integration)
- GREEN: Add GOOGLE_SEARCH_PROMPT to system prompt generator
- REFACTOR: N/A

**Acceptance Criteria**:
- [ ] Google Search section added to `generate_schema_agent_prompt()`
- [ ] Includes `[TOOL:GOOGLE_SEARCH]` detection rule
- [ ] Includes when-to-use and when-not-to-use rules
- [ ] Includes response format with sources template
- [ ] Prompt clearly separates database queries from web searches

**File Changes**:
```
MODIFY: backend/app/agents/schema_query_agent.py
  - ADD: GOOGLE_SEARCH_PROMPT constant
  - MODIFY: generate_schema_agent_prompt() to include Google Search section
```

---

### Task 2.2: Add Google Search Tool to Agent

**Priority**: P0 (Blocker)
**Estimated Time**: 30 minutes
**Dependencies**: Task 1.3, Task 2.1

**Description**: Integrate GoogleSearchService as a function tool that the Schema Agent can invoke.

**TDD Cycle**:
- RED: Write integration tests
  - `test_agent_has_google_search_tool`
  - `test_agent_invokes_google_search_on_prefix`
- GREEN: Add function_tool wrapper for Google Search
- REFACTOR: Clean up tool registration

**Acceptance Criteria**:
- [ ] Tests written and initially fail (RED)
- [ ] `google_search` function tool created with `@function_tool` decorator
- [ ] Tool added to agent's tools list
- [ ] Tool receives query and returns formatted response with sources
- [ ] All tests pass (GREEN)

**File Changes**:
```
CREATE: backend/app/mcp_server/tools_google_search.py
  - google_search function tool with @function_tool decorator
  - Uses GoogleSearchService internally

MODIFY: backend/app/agents/schema_query_agent.py
  - Import google_search tool
  - Add to agent's function_tools list
```

**Implementation Code**:
```python
# backend/app/mcp_server/tools_google_search.py
from agents import function_tool
from app.services.google_search import GoogleSearchService, should_use_google_search, strip_tool_prefix
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@function_tool
async def google_search(query: str) -> str:
    """
    Search the web using Google Search for real-time information.

    Use this tool when:
    - User explicitly requests web search
    - Query is about current events, news, or latest information
    - Query asks for documentation, tutorials, or external resources

    Args:
        query: The search query to perform

    Returns:
        Search results with sources as markdown links
    """
    if not GEMINI_API_KEY:
        return "Google Search is not configured. Please set GEMINI_API_KEY."

    service = GoogleSearchService(api_key=GEMINI_API_KEY)
    result = await service.search(query)
    return service.format_response_with_sources(result)
```

---

### Task 2.3: Handle User-Forced Mode (Prefix Detection)

**Priority**: P1
**Estimated Time**: 25 minutes
**Dependencies**: Task 1.4, Task 2.2

**Description**: Modify Schema Agent's query processing to detect `[TOOL:GOOGLE_SEARCH]` prefix and force Google Search usage.

**TDD Cycle**:
- RED: Write integration test `test_prefix_forces_google_search`
- GREEN: Add prefix detection in query method
- REFACTOR: N/A

**Acceptance Criteria**:
- [ ] Test written and initially fails (RED)
- [ ] When query starts with `[TOOL:GOOGLE_SEARCH]`:
  - Prefix is stripped from query
  - Google Search tool is invoked directly
  - Response includes sources
- [ ] Test passes (GREEN)

**File Changes**:
```
MODIFY: backend/app/agents/schema_query_agent.py
  - MODIFY: query() method to detect prefix
  - ADD: Direct invocation of google_search tool when prefix detected

CREATE: backend/tests/integration/test_google_search_agent.py
  - TestGoogleSearchAgentIntegration class
  - Integration tests for forced mode
```

---

### Task 2.4: Handle Agent-Autonomous Mode

**Priority**: P2
**Estimated Time**: 20 minutes
**Dependencies**: Task 2.1, Task 2.2

**Description**: Ensure agent can autonomously decide to use Google Search based on system prompt guidance.

**TDD Cycle**:
- RED: Write integration tests
  - `test_autonomous_search_for_news`
  - `test_no_autonomous_search_for_db`
- GREEN: Verify system prompt enables autonomous decision
- REFACTOR: N/A

**Acceptance Criteria**:
- [ ] Tests written and initially fail (RED)
- [ ] Agent autonomously uses Google Search for:
  - Current events / news queries
  - "Latest version" queries
  - External documentation queries
- [ ] Agent does NOT use Google Search for:
  - Inventory queries
  - Sales data queries
  - Database aggregation queries
- [ ] Tests pass (GREEN)

**File Changes**:
```
MODIFY: backend/tests/integration/test_google_search_agent.py
  - ADD: Tests for autonomous mode
```

---

## Phase 3: Testing & Validation

### Task 3.1: Run Full Test Suite

**Priority**: P0 (Blocker)
**Estimated Time**: 15 minutes
**Dependencies**: All previous tasks

**Description**: Run all unit and integration tests to ensure everything works together.

**Acceptance Criteria**:
- [ ] All unit tests pass: `pytest tests/unit/test_google_search*.py`
- [ ] All integration tests pass: `pytest tests/integration/test_google_search*.py`
- [ ] Coverage meets targets (≥80%)
- [ ] No regressions in existing tests

**Commands**:
```bash
# Run Google Search tests
pytest tests/unit/test_google_search*.py -v

# Run integration tests
pytest tests/integration/test_google_search*.py -v

# Run with coverage
pytest tests/ --cov=app/services/google_search --cov=app/mcp_server/tools_google_search --cov-report=term-missing
```

---

### Task 3.2: Manual Testing with ChatKit

**Priority**: P1
**Estimated Time**: 20 minutes
**Dependencies**: Task 3.1

**Description**: Perform manual testing through the ChatKit UI to verify end-to-end functionality.

**Acceptance Criteria**:
- [ ] Google Search appears in Apps menu
- [ ] Shows as "Connected" (no setup needed)
- [ ] User-forced mode works:
  - Select Google Search from Apps menu
  - Ask "What is the latest version of React?"
  - Response includes sources as clickable links
- [ ] Agent-autonomous mode works:
  - Do NOT select any tool
  - Ask "What happened in tech news today?"
  - Agent uses Google Search automatically
  - Response includes sources
- [ ] Database queries work without search:
  - Do NOT select any tool
  - Ask "How many products in inventory?"
  - Agent uses database tools, NOT Google Search
- [ ] Sources display as markdown links in ChatKit

**Test Scenarios**:
| Scenario | Query | Expected Behavior |
|----------|-------|-------------------|
| Forced Mode | [Select Google Search] "Latest Python version" | Uses Google Search, shows sources |
| Autonomous - News | "What's in the news today?" | Uses Google Search automatically |
| Autonomous - Docs | "React hooks documentation" | Uses Google Search automatically |
| No Search - DB | "Show top 5 products" | Uses execute_sql, no sources |
| No Search - Count | "How many items in stock?" | Uses execute_sql, no sources |

---

### Task 3.3: Documentation Update

**Priority**: P2
**Estimated Time**: 15 minutes
**Dependencies**: Task 3.2

**Description**: Update any relevant documentation with Google Search tool information.

**Acceptance Criteria**:
- [ ] Environment variable documented: `GEMINI_API_KEY`
- [ ] Tool listed in system tools documentation
- [ ] Usage examples documented

**File Changes**:
```
MODIFY: backend/.env.example (if exists)
  - ADD: GEMINI_API_KEY=your-gemini-api-key

OPTIONAL: Update README if system tools are documented
```

---

## Task Dependency Graph

```
Phase 1: Core Infrastructure
├── Task 1.1: Add google-genai Package (P0)
├── Task 1.2: Add Google Search to Registry (P0)
│   └── depends on: None
├── Task 1.3: Create Google Search Service (P0)
│   └── depends on: Task 1.1
└── Task 1.4: Create Helper Functions (P1)
    └── depends on: None

Phase 2: Agent Integration
├── Task 2.1: Update System Prompt (P0)
│   └── depends on: None
├── Task 2.2: Add Google Search Tool (P0)
│   └── depends on: Task 1.3, Task 2.1
├── Task 2.3: Handle User-Forced Mode (P1)
│   └── depends on: Task 1.4, Task 2.2
└── Task 2.4: Handle Agent-Autonomous Mode (P2)
    └── depends on: Task 2.1, Task 2.2

Phase 3: Testing & Validation
├── Task 3.1: Run Full Test Suite (P0)
│   └── depends on: All previous tasks
├── Task 3.2: Manual Testing (P1)
│   └── depends on: Task 3.1
└── Task 3.3: Documentation Update (P2)
    └── depends on: Task 3.2
```

---

## Execution Order

Execute tasks in this order for optimal flow:

1. **Task 1.1**: Add google-genai Package
2. **Task 1.2**: Add Google Search to Registry (parallel with 1.1)
3. **Task 1.4**: Create Helper Functions (parallel with 1.2)
4. **Task 1.3**: Create Google Search Service (after 1.1)
5. **Task 2.1**: Update System Prompt (parallel with 1.3)
6. **Task 2.2**: Add Google Search Tool (after 1.3, 2.1)
7. **Task 2.3**: Handle User-Forced Mode (after 2.2)
8. **Task 2.4**: Handle Agent-Autonomous Mode (after 2.2)
9. **Task 3.1**: Run Full Test Suite
10. **Task 3.2**: Manual Testing
11. **Task 3.3**: Documentation Update

---

## Estimated Total Time

| Phase | Time |
|-------|------|
| Phase 1: Core Infrastructure | ~1.5 hours |
| Phase 2: Agent Integration | ~1.5 hours |
| Phase 3: Testing & Validation | ~1 hour |
| **Total** | **~4 hours** |
