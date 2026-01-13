---
id: "0001"
title: "Developer Tools Published Agent API Spec"
stage: spec
date: 2025-01-13
surface: cli
model: claude-opus-4-5-20250114
feature: 014-developer-tools
branch: feat/developer-tools-published-agent-api
user: developer
command: manual-conversation
labels: [developer-tools, published-agent, api-key, multi-tenant]
links:
  spec: specs/014-developer-tools/spec.md
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/41
files:
  - specs/014-developer-tools/spec.md
  - specs/014-developer-tools/data-model.md
  - specs/014-developer-tools/plan.md
  - specs/014-developer-tools/tasks.md
  - specs/014-developer-tools/checklists/requirements.md
tests:
  - null
---

## Prompt

User requested to review the schema-agent code and design a Developer Tools feature that allows organizations to share their Schema Agent with external users/clients via API keys.

Key requirements:
1. Organization should be able to create published agents with restricted table access
2. Generate unique API keys for each published agent
3. External users can embed ChatKit widget on their websites
4. Organization controls: read-only vs read-write, which tables, rate limits
5. Same Schema Agent should be reused (no new agent code)
6. Previous code logic (frontend + backend + database) should not be modified

User later clarified: Instead of creating new agents, reuse the existing Schema Agent with filtered schema_metadata for table-level access control.

## Response snapshot

Created comprehensive specification documents for Developer Tools (Phase 14):

1. **spec.md**: Complete requirements including:
   - 21 functional requirements (FR-001 to FR-023)
   - 11 non-functional requirements (security, performance, maintainability)
   - API specifications for Developer Portal and Public API
   - Security model (API key hashing, rate limiting, CORS validation)
   - Schema filtering as core mechanism

2. **data-model.md**: Database schema including:
   - PublishedAgentConfig model (all fields, constraints, indexes)
   - PublishedAgentUsage model for daily stats
   - SQLAlchemy model code ready for implementation
   - Migration strategy

3. **plan.md**: Architecture design including:
   - Component diagrams (backend services, routers)
   - Request flow diagrams for public API
   - Frontend page structure and components
   - File structure for new code

4. **tasks.md**: 20 implementation tasks including:
   - Phase 1: Backend models & services (6 tasks)
   - Phase 2: Backend API routes (4 tasks)
   - Phase 3: Frontend pages (6 tasks)
   - Phase 4: Testing & integration (4 tasks)

5. **checklists/requirements.md**: Pre/post implementation checklist

Key design decision: Use `filter_schema_for_published_agent()` function to filter organization's full schema_metadata to only allowed tables, then pass filtered schema to existing SchemaQueryAgent.

## Outcome

- ✅ Impact: Complete specification for Developer Tools feature created
- 🧪 Tests: N/A (spec phase, no code yet)
- 📁 Files: 5 new spec files (3,355 lines total)
- 🔁 Next prompts: Implementation of Task 1.1 (PublishedAgentConfig model)
- 🧠 Reflection: Reusing existing agent with filtered schema is simpler and more maintainable than creating new agent code

## Evaluation notes (flywheel)

- Failure modes observed: None - spec creation was straightforward
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Start implementation with backend models
