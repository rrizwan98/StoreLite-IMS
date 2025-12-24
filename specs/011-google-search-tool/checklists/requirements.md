# Requirements Checklist: Google Search Tool Integration

**Feature**: 011-google-search-tool
**Date**: 2025-12-24
**Status**: Implementation Complete

---

## Functional Requirements

### Google Search Tool Registration

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-001 | System MUST register Google Search as a System Tool in the tools registry with `auth_type: none` | ✅ DONE | Added to `registry.py` |
| FR-002 | System MUST display Google Search in the Apps menu under System Tools category | ✅ DONE | Category: utilities |
| FR-003 | System MUST always show Google Search as "Connected" (no user setup required) | ✅ DONE | auth_type: none |
| FR-004 | System MUST use GEMINI_API_KEY environment variable for Google Search functionality | ✅ DONE | Service reads from env |

### User-Forced Mode

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-005 | When user selects Google Search from Apps menu, agent MUST use Google Search for the request | ✅ DONE | Prefix detection in prompt |
| FR-006 | System MUST detect `[TOOL:GOOGLE_SEARCH]` prefix in user message to force Google Search usage | ✅ DONE | Added to system prompt |
| FR-007 | Selected tool indicator MUST be visible in ChatKit composer before sending | ✅ DONE | Existing ChatKit behavior |

### Agent-Autonomous Mode

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-008 | Agent MUST analyze each query to determine if Google Search is beneficial | ✅ DONE | System prompt rules |
| FR-009 | Agent SHOULD use Google Search for: current events, latest versions, real-time data, external documentation, tutorials, news | ✅ DONE | Listed in prompt |
| FR-010 | Agent SHOULD NOT use Google Search for: database queries, inventory data, internal analytics | ✅ DONE | Listed in prompt |
| FR-011 | Agent MUST have Google Search available as a tool even when not explicitly selected | ✅ DONE | Added to function_tools |

### Response Formatting

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-012 | Google Search results MUST include sources section with markdown-formatted links | ✅ DONE | format_response_with_sources() |
| FR-013 | Sources MUST display as: `[Page Title](URL)` format | ✅ DONE | SearchSource dataclass |
| FR-014 | Response MUST use ChatKit's standard message format (no custom HTML rendering) | ✅ DONE | Pure markdown |
| FR-015 | Sources section MUST be clearly separated from response text with a "Sources:" header | ✅ DONE | Added in formatting |

### Grounding Metadata

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-016 | System MUST extract grounding metadata from Gemini response (search queries, grounding chunks) | ✅ DONE | In search() method |
| FR-017 | System MUST parse grounding_chunks to extract source URLs and titles | ✅ DONE | SearchSource extraction |
| FR-018 | System MUST log search queries performed for debugging purposes | ✅ DONE | Logging in service |

---

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `backend/app/services/google_search.py` | Google Search service with Gemini integration |
| `backend/app/mcp_server/tools_google_search.py` | Function tool for agent integration |
| `specs/011-google-search-tool/spec.md` | Feature specification |
| `specs/011-google-search-tool/plan.md` | Implementation plan |
| `specs/011-google-search-tool/tasks.md` | Task breakdown |

### Modified Files

| File | Changes |
|------|---------|
| `backend/pyproject.toml` | Added google-genai dependency |
| `backend/app/tools/registry.py` | Added google_search SystemTool |
| `backend/app/agents/schema_query_agent.py` | Added Google Search rules to prompt, integrated tool |

---

## Test Coverage

| Component | Test File | Status |
|-----------|-----------|--------|
| Tool Registry | `test_tools_registry.py` | ⬜ Pending |
| Google Search Service | `test_google_search_service.py` | ⬜ Pending |
| Agent Integration | `test_google_search_agent.py` | ⬜ Pending |

---

## Manual Testing Checklist

| Scenario | Expected | Status |
|----------|----------|--------|
| Open Apps menu | Google Search visible with "search" icon | ⬜ |
| Google Search status | Shows as "Connected" | ⬜ |
| User-forced search | Response includes Sources section | ⬜ |
| Autonomous search (news) | Agent uses google_search automatically | ⬜ |
| Database query | Agent uses SQL, not search | ⬜ |
| Sources display | Links are clickable in ChatKit | ⬜ |

---

## Environment Requirements

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | Yes | Google Gemini API access for search grounding |
