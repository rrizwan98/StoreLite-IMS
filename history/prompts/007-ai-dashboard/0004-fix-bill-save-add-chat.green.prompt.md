---
id: "0004"
title: Fix Bill Save to MCP Database and Add Floating Chat
stage: green
date: 2025-12-14
surface: claude-code
model: claude-opus-4-5-20251101
feature: 007-ai-dashboard
branch: 007-ai-dashboard
user: rrizwan98
command: /sp.git.commit_pr
labels: [pos, mcp, bill, chatkit, floating-chat, bug-fix]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/9
files:
  - backend/app/routers/inventory_agent.py (modified)
  - frontend/app/dashboard/mcp-pos/page.tsx (modified)
  - frontend/app/dashboard/page.tsx (modified)
tests:
  - Manual testing of bill generation and database save
---

## Prompt

User reported multiple issues in sequence:
1. "bill bhoot dair ma generate ho rha h plz is ko very fast kro with in one secs or less. and also bill ko add bhi kro database tables mai" - Make bill generation fast and save to database
2. "POS mai yia error arha h: object of type 'CallToolResult' has no len()" - Fix CallToolResult handling error
3. "bill generate ho rha h but bill db tables mai save nh ho rha h. plz fix it" - Bill not saving to database
4. "connect your own database mai search products user k MCP server database say search ho kr nh arhy hyn" - Products not loading from MCP
5. "ab Your Database Dashboard section mai aik bottom right per aik button add kro chat k us mai openai chatkit ko use kro" - Add floating chat button
6. "chatkit UI load nh ho rhi h. plz fix it, AI Analytics mai jis tarna say use ki same as it is use kro" - Fix ChatKit loading

## Response snapshot

**Fixed Issues:**

1. **MCP Parameter Name Bug**: Changed `{"query": sql}` to `{"sql": sql}` in `execute_sql_direct()` - postgres-mcp expects parameter name "sql", not "query". This was causing default value "all" to be used, resulting in SQL syntax errors.

2. **Bill ID Extraction**: Added robust `extract_id_from_result()` helper function that handles:
   - List of dicts format `[{"id": 1}]`
   - JSON string parsing
   - Regex extraction from string like `"[{'id': 5}]"`

3. **Floating ChatKit Button**: Added to dashboard for MCP-connected users:
   - Blue circular button at bottom-right corner
   - Opens modal with ChatKit UI
   - Uses same script URL as Analytics page: `https://cdn.platform.openai.com/deployments/chatkit/chatkit.js`
   - Proper `handleScriptLoad` function with `customElements.get('openai-chatkit')` check
   - Connects to `/inventory-agent/chatkit` endpoint

4. **Detailed Logging**: Added comprehensive logging throughout bill creation flow for debugging.

## Outcome

- Impact: Bills now properly save to user's MCP-connected database with correct bill_id mapping in inventory_bill_items
- Tests: Manual testing - bill generation, database save, ChatKit loading all work correctly
- Files: 3 files modified, ~490 lines changed
- Next prompts: None specified
- Reflection: postgres-mcp parameter naming convention differs from expected - always check tool signatures

## Evaluation notes (flywheel)

- Failure modes observed: Wrong parameter name caused silent failure with default value
- Graders run and results (PASS/FAIL): Manual PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add parameter validation/logging when calling MCP tools
