---
id: "0006"
title: notion-mcp-oauth-integration
stage: green
date: 2025-12-24
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: developer
command: /sp.git.commit_pr
labels: [notion, oauth, mcp, connectors, agent-cache]
links:
  spec: specs/008-user-mcp-connectors/spec.md
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/12
files:
  - backend/app/routers/notion_mcp_oauth.py
  - backend/app/connectors/mcp_client.py
  - backend/app/connectors/agent_tools.py
  - backend/app/routers/schema_agent.py
  - backend/app/agents/schema_query_agent.py
  - frontend/app/connectors/callback/page.tsx
  - frontend/app/dashboard/settings/page.tsx
  - frontend/lib/connectors-api.ts
tests:
  - backend/tests/unit/test_agent_connector_integration.py
  - backend/tests/unit/test_oauth_connectors.py
---

## Prompt

Multiple user requests to implement and fix Notion MCP integration:
1. Redesign Add MCP Connector UI with predefined Notion connector
2. Implement browser-based OAuth flow like ChatGPT (no developer credentials needed)
3. Fix 400 Bad Request errors with token exchange
4. Fix 406 Not Acceptable with MCP Streamable HTTP transport
5. Fix agent tool function signature for OpenAI SDK
6. Fix agent cache invalidation on database disconnect/reconnect
7. Auto-load ALL user connector tools for Schema Agent

## Response snapshot

Implemented complete Notion MCP OAuth integration with zero-config approach:

1. **Dynamic Client Registration (RFC 7591)**: No NOTION_OAUTH_CLIENT_ID needed in .env
2. **OAuth Metadata Discovery (RFC 8414)**: Auto-discover endpoints from mcp.notion.com
3. **PKCE Support**: Secure OAuth flow for public clients
4. **MCP Streamable HTTP Transport**: Fixed Accept header to include both application/json and text/event-stream
5. **Form-Encoded Token Exchange**: Fixed Content-Type from JSON to application/x-www-form-urlencoded
6. **Agent Tool Signature Fix**: Changed from (ctx, **kwargs) to (ctx, args: str) for OpenAI SDK
7. **Agent Cache Fix**: Updated cache key format and clear function to handle new key pattern

Key endpoints:
- POST /api/notion-mcp/connect - Start OAuth with DCR
- POST /api/notion-mcp/callback - Exchange code for token
- GET /api/notion-mcp/status - Check connection status
- DELETE /api/notion-mcp/disconnect - Disconnect Notion

## Outcome

- ✅ Impact: Users can connect Notion without developer portal setup, agent cache properly invalidates on reconnect
- 🧪 Tests: Unit tests added for OAuth connectors and agent integration
- 📁 Files: 48 files changed, 6427 insertions, 429 deletions
- 🔁 Next prompts: Test Notion tool execution, add more predefined connectors
- 🧠 Reflection: MCP Streamable HTTP transport requires specific headers; OAuth token exchange must use form-urlencoded

## Evaluation notes (flywheel)

- Failure modes observed: Cache key mismatch after format change, wrong Content-Type for token endpoint, missing Accept header for MCP
- Graders run and results (PASS/FAIL): Manual testing PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add Google Drive as second predefined connector
