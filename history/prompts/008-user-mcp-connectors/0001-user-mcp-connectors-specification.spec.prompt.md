---
id: "0001"
title: User MCP Connectors Specification
stage: spec
date: 2025-12-21
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: developer
command: /sp.specify
labels: [mcp, connectors, chatkit, tools, specification]
links:
  spec: specs/008-user-mcp-connectors/spec.md
  ticket: ""
  adr: ""
  pr: ""
files:
  - specs/008-user-mcp-connectors/spec.md
  - specs/008-user-mcp-connectors/checklists/requirements.md
tests:
  - N/A (specification phase)
---

## Prompt

User requested a feature to allow users to connect their own MCP (Model Context Protocol) servers to the AI Agent. Key requirements discussed:

1. **Two Separate Systems**:
   - System Tools: Pre-defined integrations managed by developers (Gmail, Analytics, Export)
   - User Connectors: Custom MCP server connections added by users

2. **Apps Menu in ChatKit**:
   - Show all available tools (system + user-added) in ChatKit's + button menu
   - Visual separation between system tools and user connectors
   - "Manage Connectors" option to open connector management UI

3. **Add New Connector Form**:
   - Fields: Name (required), Description (optional), MCP Server URL (required), Authentication Type (No Auth, OAuth)
   - Test Connection button to validate before saving
   - Show discovered tools on successful connection
   - Save button DISABLED until connection test passes

4. **Connection Validation**:
   - URL format validation
   - Server reachability check
   - Authentication verification
   - MCP protocol validation
   - Tool discovery
   - Clear error messages with suggestions for each failure type

5. **Architecture**:
   - System Tools in code (`backend/app/tools/`) - developer-extensible
   - User Connectors in database (`backend/app/connectors/`) - user CRUD
   - Both integrate into ChatKit's composer.tools[]

6. **Tool Usage**:
   - When user selects a tool, agent MUST use that tool
   - Selected tool indicated visually in composer
   - Tool selection clears after message sent

## Response snapshot

Created comprehensive specification document with:

- **6 User Stories** covering all primary flows (P1: View Apps, Add Connector, Validation, Tool Usage; P2: Manage Connectors, System Tools)
- **24 Functional Requirements** organized by domain (System Tools, User Connectors, Connection Validation, ChatKit Integration, Agent Integration)
- **7 Measurable Success Criteria** (30s add time, 10s validation, 95% success rate, 2s load time, 100% tool usage, 10 connectors/user)
- **Edge Cases** documented with expected behavior
- **Assumptions and Out of Scope** clearly defined
- **Architecture Notes** for planning phase

Quality checklist passed all validation items.

## Outcome

- Impact: Created complete feature specification for User MCP Connectors feature
- Tests: N/A (specification phase - no code written)
- Files: spec.md, checklists/requirements.md
- Next prompts: /sp.clarify or /sp.plan
- Reflection: Thorough discussion before specification helped capture all requirements including connection validation flow and system/user tools separation

## Evaluation notes (flywheel)

- Failure modes observed: None - specification created successfully
- Graders run and results (PASS/FAIL): Manual checklist validation - PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Proceed to /sp.plan for implementation architecture
