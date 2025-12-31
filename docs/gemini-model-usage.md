# Gemini Model Usage in Codebase

## 1. Direct Agent Usage (Agent mein directly model use)

| File | Line | Model | Purpose |
|------|------|-------|---------|
| `agents/schema_query_agent.py` | 46, 56 | `gemini/gemini-robotics-er-1.5-preview` | Schema Query Agent (main AI chat) |
| `agents/agent.py` | 78 | `gemini/gemini-2.5-flash-lite` | Base Agent class |
| `connector_agents/base.py` | 108 | `gemini/gemini-2.5-flash` | MCP Connector Agents (Gmail, Notion, etc.) |
| `routers/inventory_agent.py` | 69, 80 | `gemini/gemini-2.5-flash-lite` | Inventory Agent |

## 2. Function/Service mein Model Usage

| File | Line | Model | Function/Purpose |
|------|------|-------|------------------|
| `services/gemini_file_search_service.py` | 433 | `gemini-robotics-er-1.5-preview` | `search_files()` - File search |
| `services/google_search.py` | 90 | `gemini-2.5-flash` | `GoogleSearchService.__init__()` - Google search |

## Summary Table

| Location | Model Used | Type |
|----------|-----------|------|
| Schema Query Agent | `gemini-robotics-er-1.5-preview` | Agent |
| Base Agent | `gemini-2.5-flash-lite` | Agent |
| Connector Agents | `gemini-2.5-flash` | Agent |
| Inventory Agent | `gemini-2.5-flash-lite` | Agent |
| File Search Service | `gemini-robotics-er-1.5-preview` | Function |
| Google Search Service | `gemini-2.5-flash` | Function |
