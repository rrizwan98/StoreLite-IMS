---
id: "0023"
title: retellai-mcp-param-fix-commit
stage: misc
date: 2026-01-05
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: rrizwan98
command: /sp.git.commit_pr
labels: [retellai, mcp, fix, commit]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/16
files:
  - backend/app/connector_agents/retellai_agent.py
  - backend/app/agents/schema_query_agent.py
tests:
  - null
---

## Prompt

User requested to commit and create PR for Retell AI agent fixes. The changes included:
1. Fixing MCP parameter naming (snake_case to camelCase) - agent_id→agentId, from_number→fromNumber, to_number→toNumber
2. Enhancing system prompt for autonomous call execution with clear parameter format
3. Adding professional response format with tables and call details
4. Adding Retell AI connector section to schema agent for automatic routing

## Response snapshot

Executed autonomous git workflow:
1. Gathered context - identified branch `008-user-mcp-connectors` with existing PR #16
2. Staged relevant files (retellai_agent.py, schema_query_agent.py)
3. Committed with descriptive message: "fix(retellai): fix MCP parameter naming and enhance call response"
4. Pushed to remote, updating existing PR #16
5. Confirmed PR URL: https://github.com/rrizwan98/StoreLite-IMS/pull/16

## Outcome

- ✅ Impact: Fixed critical bug where MCP server rejected calls due to parameter naming mismatch
- 🧪 Tests: Manual testing confirmed calls now work correctly
- 📁 Files: 2 files changed, 223 insertions(+), 117 deletions(-)
- 🔁 Next prompts: Test call functionality with various scenarios
- 🧠 Reflection: MCP servers expect camelCase params while Python convention is snake_case - always verify API expectations

## Evaluation notes (flywheel)

- Failure modes observed: MCP validation error due to parameter naming convention mismatch
- Graders run and results (PASS/FAIL): PASS - calls now initiate successfully
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add more detailed call status tracking
