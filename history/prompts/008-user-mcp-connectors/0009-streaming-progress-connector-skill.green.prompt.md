---
id: "0009"
title: "streaming-progress-connector-skill"
stage: green
date: 2025-12-28
surface: claude-code
model: claude-opus-4-5-20250514
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: rrizwan98
command: /sp.git.commit_pr
labels: [streaming, chatkit, skill, mcp-connector]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/14
files:
  - backend/app/agents/schema_query_agent.py
  - backend/app/routers/schema_agent.py
  - backend/app/connector_agents/notion_agent.py
  - .claude/skills/mcp-connector-integration/SKILL.md
  - .claude/skills/mcp-connector-integration/backend-reference.md
  - .claude/skills/mcp-connector-integration/frontend-reference.md
  - .claude/skills/mcp-connector-integration/agent-template.md
tests:
  - Manual test: streaming progress in ChatKit UI
---

## Prompt

Multiple tasks completed in this session:
1. Fix ChatKit streaming to show detailed progress (tool calls, outputs, agent activity)
2. Fix "unknown_tool" issue - show actual tool names
3. Add Notion connector streaming context
4. Create reusable MCP connector integration skill

## Response snapshot

### Streaming Enhancements
- Added `query_streamed()` method to `SchemaQueryAgent` using `Runner.run_streamed()`
- Fixed tool name extraction with multiple fallback methods (item.name, raw_item, call_id)
- Updated `SchemaChatKitServer.respond()` to use streaming with detailed progress messages
- Added emoji-prefixed messages for different tool types (SQL, Notion, Gmail, etc.)

### Notion Agent Updates
- Modified tool outputs to include `[Connector:tool_name]` format
- Added progress logging with connector context
- Enhanced error messages with connector info

### MCP Connector Skill Created
Created `.claude/skills/mcp-connector-integration/` with:
- `SKILL.md`: Complete checklist for adding new MCP connectors
- `backend-reference.md`: Registry, agents, MCP client patterns
- `frontend-reference.md`: OAuth flow, UI components, API client
- `agent-template.md`: GPT-5.2 optimized prompt templates for Slack, GitHub, Airtable, etc.

### Git Workflow
- Committed 7 files with streaming + skill changes
- Pushed to `008-user-mcp-connectors` branch
- Created PR #14

## Outcome

- ✅ Impact: ChatKit now shows detailed streaming progress with tool names, enabling users to see exactly what the agent is doing
- 🧪 Tests: Manual testing required for streaming UI
- 📁 Files: 7 files (3 modified, 4 new skill files)
- 🔁 Next prompts: Test with actual queries, add new connector using skill
- 🧠 Reflection: Skill creation enables faster future connector integrations

## Evaluation notes (flywheel)

- Failure modes observed: Initial `final_result()` method error fixed by using property access
- Graders run and results (PASS/FAIL): N/A - manual testing
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test streaming with complex multi-tool queries
