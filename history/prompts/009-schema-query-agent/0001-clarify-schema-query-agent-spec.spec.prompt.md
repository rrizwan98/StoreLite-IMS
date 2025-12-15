---
id: "0001"
title: clarify-schema-query-agent-spec
stage: spec
date: 2025-12-15
surface: claude-code
model: claude-opus-4-5-20251101
feature: 009-schema-query-agent
branch: 007-ai-dashboard
user: developer
command: /sp.clarify
labels: [clarification, schema-query, agent, mcp]
links:
  spec: specs/009-schema-query-agent/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-schema-query-agent/spec.md
tests:
  - null
---

## Prompt

User requested `/sp.clarify` to identify and resolve ambiguities in the newly created Schema Query Agent specification (Phase 9). The spec introduces a new "Agent + Analytics Only" connection mode for existing businesses who want AI-powered querying without modifying their database schema.

## Response snapshot

Performed structured ambiguity scan across 15 taxonomy categories. Identified 5 critical clarification questions:

1. **MCP Server Implementation** → Reuse existing FastMCP infrastructure (no new dependencies)
2. **Analytics Data Source** → User's schema only (no platform data mixing)
3. **Reconnection Behavior** → Auto-reconnect on login using stored URI
4. **Table Limit for Schema Discovery** → Max 100 tables (require allowed_schemas filter if exceeded)
5. **Mode Switching** → Allow switching to Full IMS with confirmation dialog

All questions answered. Spec updated with:
- Clarifications section with 5 Q&A entries
- Updated MCP integration section (FastMCP, no table creation)
- Added auto-reconnect and mode switching flows
- Added 100 table limit to security requirements
- Added data isolation note to analytics user story
- Added >100 tables edge case

## Outcome

- ✅ Impact: High - Resolved 5 critical ambiguities that would affect architecture and UX
- 🧪 Tests: N/A (clarification phase)
- 📁 Files: specs/009-schema-query-agent/spec.md (updated 6 sections)
- 🔁 Next prompts: /sp.plan to generate implementation plan
- 🧠 Reflection: Clarification workflow effectively identified key decision points around MCP reuse, data isolation, reconnection UX, scale limits, and mode flexibility

## Evaluation notes (flywheel)

- Failure modes observed: None - all questions answered clearly
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): standard /sp.clarify
- Next experiment (smallest change to try): Consider adding question about error notification preferences (email vs in-app) for connection failures
