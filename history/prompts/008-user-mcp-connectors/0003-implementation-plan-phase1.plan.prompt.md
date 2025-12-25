---
id: "0003"
title: Implementation Plan Phase 1 Complete
stage: plan
date: 2025-12-21
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: developer
command: /sp.plan (continued)
labels: [planning, research, data-model, api-contracts, quickstart, fastmcp]
links:
  spec: specs/008-user-mcp-connectors/spec.md
  plan: specs/008-user-mcp-connectors/plan.md
  research: specs/008-user-mcp-connectors/research.md
  data-model: specs/008-user-mcp-connectors/data-model.md
files:
  - specs/008-user-mcp-connectors/research.md
  - specs/008-user-mcp-connectors/data-model.md
  - specs/008-user-mcp-connectors/contracts/tools-api.yaml
  - specs/008-user-mcp-connectors/contracts/connectors-api.yaml
  - specs/008-user-mcp-connectors/quickstart.md
tests:
  - N/A (planning phase)
---

## Prompt

User confirmed to continue with rest of plan after TDD sections were added. User also clarified to use **FastMCP** (which is already in use in the codebase) instead of raw MCP SDK.

## Response snapshot

Completed Phase 0 (Research) and Phase 1 (Design Artifacts) for User MCP Connectors feature:

### Research Findings (research.md)

1. **FastMCP** already implemented in `backend/app/mcp_server/server.py`
   - SSE transport on port 8001
   - `@server.tool()` decorator pattern

2. **MCPClient** exists in `backend/app/agents/tools_client.py`
   - HTTP-based with httpx
   - 10-second timeout (matches spec)
   - Tool caching with 300s TTL

3. **EncryptionService** ready in `backend/app/services/encryption_service.py`
   - Fernet (AES-128-CBC with HMAC)
   - `encrypt_token()` and `decrypt_token()` functions
   - Key from `TOKEN_ENCRYPTION_KEY` env var

4. **SQLAlchemy models** pattern established in `backend/app/models.py`

### Data Model (data-model.md)

Created two new tables:
- `user_tool_status` - Tracks user's connection status for system tools
- `user_mcp_connections` - User's custom MCP server connections

Key fields:
- `auth_config` - Encrypted JSON for credentials
- `discovered_tools` - JSONB cache of tools from server
- `is_verified` - Must be true before save (connection tested)

### API Contracts

**tools-api.yaml** (System Tools):
- `GET /api/tools` - List all system tools with user status
- `POST /api/tools/{toolId}/connect` - Connect to tool
- `POST /api/tools/{toolId}/disconnect` - Disconnect from tool

**connectors-api.yaml** (User Connectors):
- `GET /api/connectors` - List user's connectors
- `POST /api/connectors` - Create connector (must test first)
- `POST /api/connectors/test` - Test connection before save
- `PUT /api/connectors/{id}` - Update connector
- `DELETE /api/connectors/{id}` - Delete connector
- `POST /api/connectors/{id}/toggle` - Enable/disable

### Quickstart Guide (quickstart.md)

- Prerequisites and environment setup
- TDD workflow with example tests
- Implementation order (backend then frontend)
- Quick code examples for key components
- API testing with curl examples
- Common issues and solutions

## Outcome

- Impact: All Phase 1 design artifacts complete
- Tests: N/A (planning phase - tests come during implementation)
- Files: 5 new files created
- Next prompts: `/sp.tasks` to generate implementation tasks
- Reflection: FastMCP is already well-integrated; extending existing patterns will be straightforward

## Documents Created

```
specs/008-user-mcp-connectors/
├── plan.md              # Already existed (with TDD)
├── research.md          # NEW: FastMCP patterns, codebase analysis
├── data-model.md        # NEW: Database schema, SQLAlchemy models
├── quickstart.md        # NEW: Development setup guide
└── contracts/
    ├── tools-api.yaml       # NEW: System tools OpenAPI spec
    └── connectors-api.yaml  # NEW: User connectors OpenAPI spec
```

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results: Manual review - PASS
- Key insight: Codebase already uses FastMCP, MCPClient, and EncryptionService - minimal new dependencies needed
- Next experiment: Proceed to /sp.tasks for implementation task generation
