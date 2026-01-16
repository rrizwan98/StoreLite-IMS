---
id: "0003"
title: "Published Agent Prompt Improvements"
stage: green
date: 2026-01-15
surface: claude-code
model: claude-opus-4-5-20251101
feature: 014-developer-tools
branch: feat/published-agent-prompt-improvements
user: rrizwan98
command: /sp.git.commit_pr
labels: [developer-tools, published-agent, prompt-engineering, env-config]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/42
files:
  - backend/app/services/published_agent_service.py
  - backend/app/routers/public_agent.py
  - backend/app/agents/schema_query_agent.py
  - backend/.env.example
  - frontend/.env.local.example
tests:
  - null
---

## Prompt

User requested:
1. Configure API URLs to dynamically switch between localhost and HF cloud (BACKEND_URL env variable)
2. Make published agents act as organization representatives instead of database assistants
3. Hide table names and technical database details from end users
4. Enable dynamic industry adaptation (e-commerce, healthcare, education, etc.)

## Response snapshot

Implemented a comprehensive solution:

1. **Environment Configuration**: Added `BACKEND_URL` to backend/.env and .env.example for proper embed code URL generation (local: localhost:8000, production: HF Spaces URL)

2. **Specialized Prompt Generator**: Created `generate_published_agent_prompt()` function in `published_agent_service.py` that:
   - Hides all database/technical terminology from responses
   - Acts as organization employee/representative
   - Dynamically adapts to industry based on data context
   - Provides professional, user-friendly responses

3. **Schema Query Agent Updates**: Added `_custom_system_prompt` attribute support to allow published agents to use custom prompts instead of default schema agent prompt

4. **Public Agent Router**: Modified `_get_or_create_agent()` to generate and use specialized prompt for published agents

## Outcome

- Impact: Published agents now behave professionally, hiding technical details and adapting to organization context
- Tests: Manual testing required - create published agent and verify no table names exposed
- Files: 5 files modified (3 backend, 2 frontend env examples)
- Next prompts: Test with different industry data to verify adaptation
- Reflection: Clean separation - only developer tools affected, main schema agent unchanged

## Evaluation notes (flywheel)

- Failure modes observed: None during implementation
- Graders run and results (PASS/FAIL): N/A - manual testing required
- Prompt variant (if applicable): N/A
- Next experiment: Test with real e-commerce and healthcare datasets to validate industry detection
