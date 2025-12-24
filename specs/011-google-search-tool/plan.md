# Implementation Plan: Google Search Tool Integration

**Branch**: `011-google-search-tool` | **Date**: 2025-12-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-google-search-tool/spec.md`

## Summary

This feature integrates Google's Search Grounding tool (from Gemini API) as a System Tool in the IMS platform. The tool enables Schema Agent to access real-time web information with two modes: user-forced (when user explicitly selects the tool) and agent-autonomous (when agent decides based on query context).

## Technical Context

**Language/Version**: Python 3.12+ (Backend)
**Primary Dependencies**:
- Backend: google-genai (Google Gen AI Python SDK), FastAPI, existing OpenAI Agents SDK
**Testing**: pytest with pytest-asyncio
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (backend + frontend integration)
**Performance Goals**:
- Google Search response < 5 seconds for 95% of queries
- Apps menu load unchanged (< 2 seconds)
**Constraints**:
- GEMINI_API_KEY must be configured
- 15-second timeout for search requests
- Graceful degradation if API unavailable
**Scale/Scope**: All authenticated users, unlimited searches (rate limited by Gemini API)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Separation of Concerns | ✅ PASS | New service: `services/google_search.py`. Existing tools registry extended. |
| II. Test-Driven Development | ✅ PASS | Tests required for search service, tool registry, agent integration |
| III. Phased Implementation | ✅ PASS | Builds on Phase 9 (Schema Agent) - extends agent with web search capability |
| IV. Database-First Design | ✅ PASS | No database changes needed - uses existing tools registry |
| V. Contract-First APIs | ✅ PASS | Response format follows ChatKit standard (markdown with sources) |
| VI. Local-First Development | ✅ PASS | Works with GEMINI_API_KEY in .env |
| VII. Simplicity Over Abstraction | ✅ PASS | Direct Gemini SDK usage, no wrapper patterns |
| VIII. Observability by Default | ✅ PASS | Structured logging for search queries and responses |

**Gate Status**: ✅ ALL GATES PASSED

## Project Structure

### Documentation (this feature)

```text
specs/011-google-search-tool/
├── spec.md              # Feature specification
├── plan.md              # This file
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── tools/
│   │   └── registry.py           # MODIFY: Add google_search SystemTool
│   │
│   ├── services/
│   │   └── google_search.py      # NEW: Google Search service with Gemini
│   │
│   ├── agents/
│   │   └── schema_query_agent.py # MODIFY: Add Google Search handling
│   │
│   └── requirements.txt          # MODIFY: Add google-genai package
│
└── tests/
    ├── unit/
    │   ├── test_google_search_service.py   # NEW: Google Search service tests
    │   └── test_tools_registry.py          # MODIFY: Add google_search tests
    └── integration/
        └── test_google_search_agent.py     # NEW: Agent integration tests

frontend/
└── components/
    └── shared/
        └── ToolAttachButton.tsx  # Already supports tool selection (no changes needed)
```

**Structure Decision**: Minimal file additions - one new service file, modifications to existing agent and registry. Frontend requires no changes as ChatKit already renders markdown links.

## Complexity Tracking

> No violations detected. All implementations follow constitution principles.

| Area | Approach | Rationale |
|------|----------|-----------|
| Google Search | Direct Gemini SDK | Simplicity - uses native google_search tool |
| Response Format | Markdown sources | Standard ChatKit rendering, no custom UI |
| Dual Mode | Prefix detection + system prompt | Agent autonomy via prompt engineering |

---

## Architecture Design

### Google Search Integration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     GOOGLE SEARCH INTEGRATION FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  USER-FORCED MODE                                                            │
│  ─────────────────                                                           │
│                                                                              │
│  1. User selects "Google Search" from Apps menu                             │
│  2. Frontend adds [TOOL:GOOGLE_SEARCH] prefix to message                    │
│  3. Schema Agent detects prefix in message                                  │
│  4. Agent calls GoogleSearchService.search(query)                           │
│  5. Service uses Gemini with google_search tool                             │
│  6. Response formatted with sources as markdown links                        │
│  7. ChatKit renders response with clickable links                           │
│                                                                              │
│  ┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ ChatKit  │ ──► │Schema Agent │ ──► │GoogleSearch  │ ──► │ Gemini API  │ │
│  │   UI     │ ◄── │  (prefix)   │ ◄── │  Service     │ ◄── │(google_search)│
│  └──────────┘     └─────────────┘     └──────────────┘     └─────────────┘ │
│       ↑                                      │                              │
│       └──────── Markdown with Sources ───────┘                              │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  AGENT-AUTONOMOUS MODE                                                       │
│  ─────────────────────                                                       │
│                                                                              │
│  1. User sends message WITHOUT selecting Google Search                      │
│  2. Schema Agent analyzes query (via system prompt)                         │
│  3. If query matches search criteria (current events, docs, etc.):          │
│     - Agent invokes google_search tool autonomously                         │
│  4. If query is about database:                                             │
│     - Agent uses MCP tools (execute_sql, etc.) instead                      │
│  5. Response formatted consistently (with or without sources)               │
│                                                                              │
│  ┌──────────┐     ┌─────────────┐     ┌──────────────┐                     │
│  │ ChatKit  │ ──► │Schema Agent │ ──► │ Decide:      │                     │
│  │   UI     │     │  (analyze)  │     │ DB or Web?   │                     │
│  └──────────┘     └─────────────┘     └───────┬──────┘                     │
│                                               │                             │
│                          ┌────────────────────┼────────────────────┐        │
│                          ▼                    ▼                    ▼        │
│                   ┌──────────────┐     ┌──────────────┐     ┌──────────┐   │
│                   │ MCP Tools    │     │GoogleSearch  │     │ Other    │   │
│                   │(execute_sql) │     │  Service     │     │ Tools    │   │
│                   └──────────────┘     └──────────────┘     └──────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Google Search Service Design

```python
# backend/app/services/google_search.py

from dataclasses import dataclass
from typing import List, Optional
from google import genai
from google.genai import types

@dataclass
class SearchSource:
    """A source from Google Search grounding."""
    title: str
    url: str

@dataclass
class GoogleSearchResult:
    """Result from Google Search with grounding."""
    text: str
    sources: List[SearchSource]
    search_queries: List[str]
    success: bool
    error: Optional[str] = None

class GoogleSearchService:
    """
    Service for performing web searches using Google Gemini's
    google_search grounding tool.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def search(self, query: str) -> GoogleSearchResult:
        """
        Perform a web search using Gemini's google_search tool.

        Args:
            query: The search query

        Returns:
            GoogleSearchResult with text, sources, and metadata
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(google_search=types.GoogleSearch())
                    ]
                ),
            )

            # Extract response text
            text = response.text

            # Extract grounding metadata
            grounding = response.candidates[0].grounding_metadata

            # Parse sources from grounding chunks
            sources = []
            if grounding and grounding.grounding_chunks:
                for chunk in grounding.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        sources.append(SearchSource(
                            title=chunk.web.title,
                            url=chunk.web.uri
                        ))

            # Get search queries
            search_queries = grounding.web_search_queries if grounding else []

            return GoogleSearchResult(
                text=text,
                sources=sources,
                search_queries=search_queries,
                success=True
            )

        except Exception as e:
            return GoogleSearchResult(
                text="",
                sources=[],
                search_queries=[],
                success=False,
                error=str(e)
            )

    def format_response_with_sources(self, result: GoogleSearchResult) -> str:
        """
        Format the search result with sources in markdown.

        Returns:
            Markdown-formatted response with sources section
        """
        if not result.success:
            return f"Web search is temporarily unavailable: {result.error}"

        # Build response with sources
        response = result.text

        if result.sources:
            response += "\n\nSources:\n"
            for source in result.sources:
                response += f"- [{source.title}]({source.url})\n"

        return response
```

### System Prompt Update

Add the following section to Schema Agent's system prompt:

```python
GOOGLE_SEARCH_PROMPT = """
############################################
GOOGLE SEARCH TOOL (WEB GROUNDING)
############################################
You have access to Google Search for real-time web information.

<google_search_detection>
FIRST: Check if user's message starts with [TOOL:GOOGLE_SEARCH].
If YES: You MUST call the google_search tool. This is MANDATORY.
</google_search_detection>

<when_to_use_google_search>
Use Google Search when:
1. Message starts with [TOOL:GOOGLE_SEARCH] (MANDATORY)
2. Query asks about current events, news, or today's information
3. Query asks about latest versions, updates, or recent releases
4. Query asks for external documentation, tutorials, or how-to guides
5. Query asks about weather, stocks, or real-time data
6. Query asks "what is" about technology, concepts, or topics not in the database
</when_to_use_google_search>

<when_not_to_use_google_search>
Do NOT use Google Search when:
1. Query is about user's database inventory or sales data
2. Query asks about counts, totals, or aggregations from database
3. Query can be answered using execute_sql or other database tools
4. Query is about internal business data stored in the database
</when_not_to_use_google_search>

<response_format_with_sources>
When using Google Search, ALWAYS include sources at the end:

[Your response with information from web search]

Sources:
- [Source Title 1](https://example.com/1)
- [Source Title 2](https://example.com/2)
- [Source Title 3](https://example.com/3)

CRITICAL: When [TOOL:GOOGLE_SEARCH] prefix is present, ALWAYS use Google Search!
</response_format_with_sources>
"""
```

### Tool Registry Update

```python
# backend/app/tools/registry.py - ADD this entry

SYSTEM_TOOLS["google_search"] = SystemTool(
    id="google_search",
    name="Google Search",
    description="Search the web for real-time information, documentation, news, and current events",
    icon="search",
    category="utilities",
    auth_type="none",  # No user auth needed - uses server's GEMINI_API_KEY
    is_enabled=True,
    is_beta=False,
)
```

---

## Test-Driven Development (TDD) Implementation Plan

**MANDATORY**: All code MUST be written following the Red-Green-Refactor cycle. NO feature code without a failing test first.

### TDD Execution Order

Implementation follows this strict order - tests FIRST, then code:

#### Phase 1: Core Infrastructure (Tests First)

| Order | Component | Test File | Key Tests |
|-------|-----------|-----------|-----------|
| 1.1 | Tool Registry | `test_tools_registry.py` | `test_google_search_registered`, `test_google_search_auth_none`, `test_google_search_enabled` |
| 1.2 | Google Search Service | `test_google_search_service.py` | `test_search_returns_result`, `test_search_returns_sources`, `test_search_timeout`, `test_format_with_sources` |

#### Phase 2: Agent Integration (Tests First)

| Order | Component | Test File | Key Tests |
|-------|-----------|-----------|-----------|
| 2.1 | Prefix Detection | `test_google_search_agent.py` | `test_detects_google_search_prefix`, `test_strips_prefix_from_query` |
| 2.2 | Autonomous Decision | `test_google_search_agent.py` | `test_autonomous_for_current_events`, `test_no_search_for_db_query` |
| 2.3 | Response Format | `test_google_search_agent.py` | `test_includes_sources_in_response` |

### TDD Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TDD CYCLE FOR EACH COMPONENT                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 1: RED - Write Failing Tests                                     │
│  ─────────────────────────────────                                     │
│  • Create test file: tests/unit/test_<component>.py                    │
│  • Write tests for ALL expected behaviors                              │
│  • Run tests: pytest tests/unit/test_<component>.py                    │
│  • Verify: ALL TESTS FAIL (no implementation yet)                      │
│                                                                         │
│  STEP 2: GREEN - Implement Minimal Code                                │
│  ───────────────────────────────────────                               │
│  • Create implementation file                                          │
│  • Write MINIMUM code to pass tests                                    │
│  • Run tests: pytest tests/unit/test_<component>.py                    │
│  • Verify: ALL TESTS PASS                                              │
│                                                                         │
│  STEP 3: REFACTOR - Clean Up                                           │
│  ───────────────────────────────                                       │
│  • Improve code quality (no new features!)                             │
│  • Run tests: pytest tests/unit/test_<component>.py                    │
│  • Verify: ALL TESTS STILL PASS                                        │
│                                                                         │
│  STEP 4: COMMIT                                                         │
│  ─────────────                                                          │
│  • Commit with message: "feat(search): add <component> with tests"     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Test Coverage Requirements

| Component | Target | Minimum |
|-----------|--------|---------|
| `services/google_search.py` | 90% | 85% |
| `tools/registry.py` (google_search) | 100% | 100% |
| `agents/schema_query_agent.py` (search handling) | 80% | 75% |
| **Overall Feature** | ≥80% | 80% |

### Example Test Structure

```python
# tests/unit/test_tools_registry.py
# ═══════════════════════════════════════════════════════════════════════
# WRITE THESE TESTS FIRST - BEFORE ANY IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

import pytest
from app.tools.registry import SYSTEM_TOOLS, get_system_tool

class TestGoogleSearchToolRegistry:
    """Test Google Search tool registration - RED phase tests"""

    def test_google_search_in_registry(self):
        """Google Search should be registered in SYSTEM_TOOLS"""
        assert "google_search" in SYSTEM_TOOLS

    def test_google_search_auth_type_none(self):
        """Google Search should have auth_type 'none'"""
        tool = get_system_tool("google_search")
        assert tool.auth_type == "none"

    def test_google_search_is_enabled(self):
        """Google Search should be enabled by default"""
        tool = get_system_tool("google_search")
        assert tool.is_enabled is True

    def test_google_search_not_beta(self):
        """Google Search should not be marked as beta"""
        tool = get_system_tool("google_search")
        assert tool.is_beta is False

    def test_google_search_category_utilities(self):
        """Google Search should be in utilities category"""
        tool = get_system_tool("google_search")
        assert tool.category == "utilities"


# tests/unit/test_google_search_service.py
# ═══════════════════════════════════════════════════════════════════════
# WRITE THESE TESTS FIRST - BEFORE ANY IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.google_search import (
    GoogleSearchService,
    GoogleSearchResult,
    SearchSource
)

class TestGoogleSearchService:
    """Test Google Search service - RED phase tests"""

    @pytest.fixture
    def mock_gemini_response(self):
        """Create a mock Gemini response with grounding metadata"""
        mock = Mock()
        mock.text = "Python 3.12 is the latest version."
        mock.candidates = [Mock()]
        mock.candidates[0].grounding_metadata = Mock()
        mock.candidates[0].grounding_metadata.grounding_chunks = [
            Mock(web=Mock(title="Python.org", uri="https://python.org")),
            Mock(web=Mock(title="Python Releases", uri="https://python.org/downloads")),
        ]
        mock.candidates[0].grounding_metadata.web_search_queries = ["latest Python version"]
        return mock

    @pytest.mark.asyncio
    async def test_search_returns_result(self, mock_gemini_response):
        """Search should return a GoogleSearchResult"""
        with patch.object(
            GoogleSearchService, '_get_client',
            return_value=AsyncMock()
        ) as mock_client:
            mock_client.return_value.aio.models.generate_content = AsyncMock(
                return_value=mock_gemini_response
            )

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("What is the latest Python version?")

            assert isinstance(result, GoogleSearchResult)
            assert result.success is True
            assert result.text != ""

    @pytest.mark.asyncio
    async def test_search_returns_sources(self, mock_gemini_response):
        """Search should return sources from grounding metadata"""
        with patch.object(
            GoogleSearchService, '_get_client',
            return_value=AsyncMock()
        ) as mock_client:
            mock_client.return_value.aio.models.generate_content = AsyncMock(
                return_value=mock_gemini_response
            )

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("What is the latest Python version?")

            assert len(result.sources) > 0
            assert all(isinstance(s, SearchSource) for s in result.sources)
            assert all(s.url.startswith("http") for s in result.sources)

    @pytest.mark.asyncio
    async def test_search_timeout_returns_error(self):
        """Search should handle timeout gracefully"""
        with patch.object(
            GoogleSearchService, '_get_client',
            return_value=AsyncMock()
        ) as mock_client:
            mock_client.return_value.aio.models.generate_content = AsyncMock(
                side_effect=TimeoutError("Request timed out")
            )

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("What is the weather?")

            assert result.success is False
            assert "timeout" in result.error.lower()

    def test_format_with_sources(self):
        """Should format response with markdown sources"""
        result = GoogleSearchResult(
            text="Python 3.12 is the latest version.",
            sources=[
                SearchSource(title="Python.org", url="https://python.org"),
                SearchSource(title="Python Releases", url="https://python.org/downloads"),
            ],
            search_queries=["latest Python version"],
            success=True
        )

        service = GoogleSearchService(api_key="test-key")
        formatted = service.format_response_with_sources(result)

        assert "Sources:" in formatted
        assert "[Python.org](https://python.org)" in formatted
        assert "[Python Releases](https://python.org/downloads)" in formatted


# tests/integration/test_google_search_agent.py
# ═══════════════════════════════════════════════════════════════════════
# WRITE THESE TESTS FIRST - BEFORE ANY IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════

import pytest

class TestGoogleSearchAgentIntegration:
    """Integration tests for Google Search in Schema Agent"""

    def test_detects_google_search_prefix(self):
        """Agent should detect [TOOL:GOOGLE_SEARCH] prefix"""
        from app.agents.schema_query_agent import should_use_google_search

        query = "[TOOL:GOOGLE_SEARCH] What is the latest Python version?"
        assert should_use_google_search(query) is True

    def test_no_prefix_returns_false(self):
        """Agent should return False when prefix is absent"""
        from app.agents.schema_query_agent import should_use_google_search

        query = "How many products are in inventory?"
        assert should_use_google_search(query) is False

    def test_strips_prefix_from_query(self):
        """Agent should strip [TOOL:GOOGLE_SEARCH] prefix from query"""
        from app.agents.schema_query_agent import strip_tool_prefix

        query = "[TOOL:GOOGLE_SEARCH] What is the latest Python version?"
        clean = strip_tool_prefix(query)
        assert clean == "What is the latest Python version?"

    def test_autonomous_decision_current_events(self):
        """Agent should decide to search for current events"""
        from app.agents.schema_query_agent import should_autonomously_search

        assert should_autonomously_search("What happened in the news today?") is True
        assert should_autonomously_search("What is the weather in Karachi?") is True
        assert should_autonomously_search("Latest React documentation") is True

    def test_autonomous_decision_database_query(self):
        """Agent should NOT search for database queries"""
        from app.agents.schema_query_agent import should_autonomously_search

        assert should_autonomously_search("How many products in inventory?") is False
        assert should_autonomously_search("Show me top selling items") is False
        assert should_autonomously_search("Total sales this month") is False
```

---

## Implementation Phases

### Phase 1: Tool Registry & Service (1-2 hours)

1. **Add google-genai package to requirements**
2. **Add Google Search to tools registry**
3. **Create GoogleSearchService**
4. **Write unit tests**

### Phase 2: Agent Integration (1-2 hours)

1. **Add prefix detection helpers**
2. **Update system prompt with Google Search rules**
3. **Integrate GoogleSearchService with Schema Agent**
4. **Write integration tests**

### Phase 3: Testing & Validation (1 hour)

1. **Run full test suite**
2. **Manual testing with ChatKit**
3. **Verify sources display correctly**

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Gemini API unavailable | Graceful error message, agent falls back to normal response |
| Rate limiting | Implement retry with exponential backoff |
| Empty search results | Agent informs user, suggests rephrasing query |
| Slow response | 15-second timeout, loading indicator in ChatKit |

---

## Dependencies

### New Package

```txt
# backend/requirements.txt - ADD
google-genai>=1.0.0  # Google Gen AI Python SDK
```

### Environment Variable

```bash
# .env - REQUIRED
GEMINI_API_KEY=your-gemini-api-key
```

---

## Success Criteria Validation

| Criteria | How to Validate |
|----------|-----------------|
| SC-001: Apps menu shows Google Search | Manual test: Open Apps menu, verify "Google Search" visible |
| SC-002: Response < 5 seconds | Automated test: Measure response time for 10 queries |
| SC-003: Autonomous search for current events | Integration test: Query "What's in the news?" without selecting tool |
| SC-004: No search for database queries | Integration test: Query "Show inventory" without selecting tool |
| SC-005: Sources as clickable links | Manual test: Verify links in ChatKit response |
| SC-006: Connected status | Manual test: Verify "Connected" status for all users |
