# Feature Specification: Google Search Tool Integration

**Feature Branch**: `011-google-search-tool`
**Created**: 2025-12-24
**Status**: Draft
**Version**: 1.0
**Input**: Google Search Grounding tool integration with Schema Agent using Gemini's google_search capability. The tool provides real-time web search capabilities with two modes: user-forced (when user selects the tool) and agent-autonomous (when agent decides to search).

---

## Overview

This feature integrates Google's Search Grounding tool (from Gemini API) as a System Tool in the IMS platform. The Google Search tool enables the Schema Agent to access real-time web information to enhance responses with current data, documentation, and external resources.

**Key Capability**: The tool works in two modes:
1. **User-Forced Mode**: User explicitly selects the Google Search tool from the Apps menu, and the agent MUST use Google Search for the query
2. **Agent-Autonomous Mode**: Agent intelligently decides when to use Google Search based on query analysis (e.g., questions about current events, latest documentation, real-time data)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User-Forced Google Search (Priority: P1)

As a user, I want to explicitly select the Google Search tool from the Apps menu so that the agent is forced to search the web for my query.

**Why this priority**: Core functionality - users need explicit control over when web search is used.

**Independent Test**: Can be tested by selecting Google Search tool, asking a question, and verifying the response includes web sources.

**Acceptance Scenarios**:

1. **Given** I am on the Schema Agent page and open the Apps menu, **When** I view System Tools, **Then** I see "Google Search" with status "Connected" (always available)
2. **Given** I select "Google Search" from the Apps menu, **When** I type "What is the latest version of Python?", **Then** the agent MUST perform a Google Search and include web sources in the response
3. **Given** I have selected Google Search, **When** I send my message, **Then** the response includes a "Sources" section with clickable links to web pages used
4. **Given** I have selected Google Search, **When** the agent responds, **Then** the response is formatted professionally using ChatKit's standard message format (no custom rendering)

---

### User Story 2 - Agent-Autonomous Google Search (Priority: P1)

As a user, I want the agent to automatically decide when to use Google Search based on my query context so that I get real-time information when needed without manually selecting the tool.

**Why this priority**: Provides intelligent assistance without requiring user to know when web search is needed.

**Independent Test**: Can be tested by asking questions about current events without selecting the tool, and verifying the agent uses Google Search automatically.

**Acceptance Scenarios**:

1. **Given** I have NOT selected Google Search tool, **When** I ask "What's the weather in Karachi today?", **Then** the agent autonomously decides to use Google Search
2. **Given** I have NOT selected Google Search tool, **When** I ask "How many products do I have in inventory?", **Then** the agent does NOT use Google Search (uses database tools instead)
3. **Given** the agent decides to use Google Search autonomously, **When** I view the response, **Then** it includes sources just like when I manually select the tool
4. **Given** I ask about recent news or current events, **When** the agent responds, **Then** it uses Google Search and provides up-to-date information

---

### User Story 3 - Google Search with Sources Display (Priority: P1)

As a user, I want to see the sources used by Google Search in a professional format so that I can verify the information and access original sources.

**Why this priority**: Transparency and trust - users need to see where information comes from.

**Independent Test**: Can be tested by making a search query and verifying sources are displayed correctly.

**Acceptance Scenarios**:

1. **Given** the agent uses Google Search, **When** I view the response, **Then** I see web sources with titles and URLs formatted as markdown links
2. **Given** the agent uses Google Search, **When** I view the response, **Then** the sources section is clearly separated from the main response text
3. **Given** the agent uses Google Search, **When** I view the sources, **Then** each source shows the website title as a clickable link
4. **Given** the agent uses Google Search and finds multiple sources, **When** I view the response, **Then** sources are displayed as a bulleted list

---

### User Story 4 - Google Search Tool Always Connected (Priority: P2)

As a user, I want Google Search to always be available as a System Tool without requiring OAuth or manual connection so that I can use it immediately.

**Why this priority**: Simplifies user experience - no setup required.

**Independent Test**: Can be tested by logging in as a new user and verifying Google Search appears as "Connected" in Apps menu.

**Acceptance Scenarios**:

1. **Given** I am a new user, **When** I open the Apps menu, **Then** I see Google Search listed under System Tools with status "Connected"
2. **Given** I am any authenticated user, **When** I want to use Google Search, **Then** I do not need to go through any connection or OAuth process
3. **Given** Google Search is listed as a System Tool, **When** I view its details, **Then** I see it is marked as `auth_type: none`

---

### Edge Cases

- What if Google Search returns no results?
  - Agent should respond indicating no relevant web results found and offer alternative suggestions
- What if the Gemini API key is not configured?
  - System should log error and respond gracefully that web search is temporarily unavailable
- What if the search request times out?
  - Agent should timeout after 15 seconds and inform user to try again
- What if the user asks a question that could use both database and web search?
  - Agent should prioritize database for data queries, use web search for context/documentation
- How does the agent decide when to autonomously use Google Search?
  - Agent analyzes query for keywords indicating need for real-time/external data (news, latest, today, current, documentation, how to, tutorial, etc.)

---

## Requirements *(mandatory)*

### Functional Requirements

#### Google Search Tool Registration

- **FR-001**: System MUST register Google Search as a System Tool in the tools registry with `auth_type: none`
- **FR-002**: System MUST display Google Search in the Apps menu under System Tools category
- **FR-003**: System MUST always show Google Search as "Connected" (no user setup required)
- **FR-004**: System MUST use GEMINI_API_KEY environment variable for Google Search functionality

#### User-Forced Mode

- **FR-005**: When user selects Google Search from Apps menu, agent MUST use Google Search for the request
- **FR-006**: System MUST detect `[TOOL:GOOGLE_SEARCH]` prefix in user message to force Google Search usage
- **FR-007**: Selected tool indicator MUST be visible in ChatKit composer before sending

#### Agent-Autonomous Mode

- **FR-008**: Agent MUST analyze each query to determine if Google Search is beneficial
- **FR-009**: Agent SHOULD use Google Search for queries about: current events, latest versions, real-time data, external documentation, tutorials, news
- **FR-010**: Agent SHOULD NOT use Google Search for: database queries, inventory data, internal analytics (use existing tools instead)
- **FR-011**: Agent MUST have Google Search available as a tool even when not explicitly selected

#### Response Formatting

- **FR-012**: Google Search results MUST include sources section with markdown-formatted links
- **FR-013**: Sources MUST display as: `[Page Title](URL)` format
- **FR-014**: Response MUST use ChatKit's standard message format (no custom HTML rendering)
- **FR-015**: Sources section MUST be clearly separated from response text with a "Sources:" header

#### Grounding Metadata

- **FR-016**: System MUST extract grounding metadata from Gemini response (search queries, grounding chunks)
- **FR-017**: System MUST parse grounding_chunks to extract source URLs and titles
- **FR-018**: System MUST log search queries performed for debugging purposes

### Key Entities

- **SystemTool (google_search)**: The Google Search tool registration in system tools registry
- **GoogleSearchResult**: Response structure containing text, sources, and grounding metadata
- **GroundingChunk**: Web source with URL and title from Gemini's grounding metadata

---

## Technical Design

### Google Search Tool Implementation

The Google Search tool is implemented using Google Gemini's built-in `google_search` tool capability, NOT as a custom function_tool.

**Integration Approach**:

```python
from google import genai
from google.genai import types

# Create Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# Generate content with Google Search grounding
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=user_query,
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ]
    ),
)

# Extract response and sources
text = response.text
sources = response.candidates[0].grounding_metadata.grounding_chunks
search_queries = response.candidates[0].grounding_metadata.web_search_queries
```

### Dual-Mode Implementation

#### Mode 1: User-Forced (via [TOOL:GOOGLE_SEARCH] prefix)

When user selects Google Search tool:
1. Frontend adds `[TOOL:GOOGLE_SEARCH]` prefix to message
2. Schema Agent detects this prefix
3. Agent bypasses LiteLLM and calls Google Gemini directly with google_search tool
4. Response is formatted with sources

#### Mode 2: Agent-Autonomous (agent decides)

When user does NOT select Google Search:
1. Agent receives query normally via LiteLLM/Gemini
2. Agent has google_search as an available tool in its tool list
3. Agent decides based on query context whether to invoke google_search
4. If invoked, response includes sources; otherwise, normal response

### System Prompt Updates

Add to Schema Agent system prompt:

```
############################################
GOOGLE SEARCH TOOL (WEB GROUNDING)
############################################
<google_search_rules>
You have access to Google Search for real-time web information.

WHEN TO USE GOOGLE SEARCH:
1. User explicitly selects the Google Search tool (message starts with [TOOL:GOOGLE_SEARCH])
2. Query asks about current events, news, or real-time information
3. Query asks about latest versions, updates, or recent changes
4. Query asks for external documentation, tutorials, or how-to guides
5. Query asks about information that changes frequently (weather, stocks, etc.)

WHEN NOT TO USE GOOGLE SEARCH:
1. Query is about the user's database or inventory data
2. Query can be answered using the database tools (execute_sql, etc.)
3. Query is about internal business data

RESPONSE FORMAT WITH SOURCES:
When using Google Search, always include sources at the end:

[Your response here with information from web search]

Sources:
- [Source Title 1](https://example.com/1)
- [Source Title 2](https://example.com/2)

CRITICAL: When [TOOL:GOOGLE_SEARCH] prefix is present, you MUST use Google Search!
</google_search_rules>
```

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Google Search appears in Apps menu for all users within 1 second of opening menu
- **SC-002**: User-forced Google Search responds with sources within 5 seconds for 95% of queries
- **SC-003**: Agent autonomously uses Google Search for 90% of current events/news queries
- **SC-004**: Agent does NOT use Google Search for 95% of database-only queries
- **SC-005**: Sources are displayed as clickable links in 100% of Google Search responses
- **SC-006**: Google Search tool shows as "Connected" for 100% of authenticated users

---

## Assumptions

1. GEMINI_API_KEY environment variable is configured on the server
2. The Gemini model (gemini-2.5-flash or similar) supports the google_search tool
3. ChatKit can display markdown-formatted links in responses
4. The Schema Agent can use both LiteLLM (for normal queries) and direct Gemini client (for Google Search)
5. Google Search grounding is available in the user's region

---

## Out of Scope

1. Custom search filters or domain restrictions
2. Image search or visual search results
3. Caching of search results
4. Search history or analytics
5. Paid/premium search features
6. Google Search result previews or cards
7. Integration with other search engines (Bing, DuckDuckGo)

---

## Architecture Notes

### Files to Create/Modify

```
backend/app/
├── tools/
│   └── registry.py          # ADD: google_search SystemTool
├── services/
│   └── google_search.py     # NEW: Google Search service with Gemini
├── agents/
│   └── schema_query_agent.py # MODIFY: Add Google Search handling
└── requirements.txt          # ADD: google-genai package
```

### Dependencies

```txt
google-genai>=1.0.0  # Google Gen AI Python SDK
```

---

## Development Approach: Test-Driven Development (TDD)

**MANDATORY**: All implementation MUST follow the Red-Green-Refactor TDD cycle.

### Test Coverage Requirements

| Component | Test Type | Coverage Target |
|-----------|-----------|-----------------|
| `services/google_search.py` | Unit + Integration | 90% |
| `tools/registry.py` (google_search) | Unit | 100% |
| `agents/schema_query_agent.py` (search handling) | Unit + Integration | 80% |

### Test Examples (Must Write Before Code)

```python
# Example: RED phase - Write this test BEFORE implementing
def test_google_search_tool_registered():
    """Google Search tool should be in system tools registry"""
    from app.tools.registry import SYSTEM_TOOLS
    assert "google_search" in SYSTEM_TOOLS
    assert SYSTEM_TOOLS["google_search"].auth_type == "none"
    assert SYSTEM_TOOLS["google_search"].is_enabled == True

def test_google_search_returns_sources():
    """Google Search should return response with sources"""
    from app.services.google_search import perform_google_search
    result = perform_google_search("What is Python?")
    assert result.text is not None
    assert len(result.sources) > 0
    assert result.sources[0].url.startswith("http")

def test_agent_detects_google_search_prefix():
    """Agent should detect [TOOL:GOOGLE_SEARCH] prefix"""
    query = "[TOOL:GOOGLE_SEARCH] What is the latest Python version?"
    assert should_use_google_search(query) == True

def test_agent_autonomous_search_decision():
    """Agent should decide to use search for current events"""
    query = "What happened in the news today?"
    assert should_autonomously_search(query) == True

    query = "How many products are in my inventory?"
    assert should_autonomously_search(query) == False
```

---

## Clarifications

### Session 2025-12-24

- Q: Should Google Search require any user setup? → A: No, it should be always available as a System Tool with `auth_type: none`
- Q: How should sources be displayed? → A: As markdown links in a "Sources:" section, using ChatKit's standard message format
- Q: When should agent autonomously use Google Search? → A: For current events, latest versions, real-time data, external docs, tutorials
- Q: What happens if Gemini API is unavailable? → A: Graceful degradation with error message that web search is temporarily unavailable

---

## Appendix A: Response Format Example

**Query**: "What is the latest version of React?"

**Response**:
```
The latest stable version of React is **18.2.0**, released in June 2022. The React team is actively working on React 19, which is currently in beta and expected to bring significant improvements including:

- React Server Components as a stable feature
- Improved Suspense handling
- New hooks like `useOptimistic` and `useFormStatus`

For production applications, React 18.2.0 is recommended.

Sources:
- [React – A JavaScript library for building user interfaces](https://react.dev/)
- [React Releases - GitHub](https://github.com/facebook/react/releases)
- [React 19 Beta - React Blog](https://react.dev/blog/2024/04/25/react-19)
```

---

## Appendix B: Grounding Metadata Structure

```python
# Response from Gemini with google_search
response.candidates[0].grounding_metadata = {
    "web_search_queries": ["latest Python version 2024"],
    "grounding_chunks": [
        {
            "web": {
                "uri": "https://www.python.org/",
                "title": "Welcome to Python.org"
            }
        },
        {
            "web": {
                "uri": "https://docs.python.org/release/",
                "title": "Python Release History"
            }
        }
    ],
    "grounding_supports": [...],
    "search_entry_point": {
        "rendered_content": "<html>..."  # Pre-rendered HTML for sources
    }
}
```
