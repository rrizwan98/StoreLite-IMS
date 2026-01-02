---
id: "0016"
title: "OpenAI ChatKit UI Skill Creation"
stage: misc
date: 2026-01-01
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: rrizwan98
command: /sp.git.commit_pr
labels: [skill, chatkit, documentation, reusable]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/15
files:
  - .claude/skills/openai-chatkit-ui/SKILL.md
  - .claude/skills/openai-chatkit-ui/references/backend-integration.md
  - .claude/skills/openai-chatkit-ui/references/frontend-widget.md
  - .claude/skills/openai-chatkit-ui/references/streaming-workflow.md
  - .claude/skills/openai-chatkit-ui/references/history-persistence.md
  - .claude/skills/openai-chatkit-ui/references/theming.md
  - .claude/skills/openai-chatkit-ui/references/events-api.md
tests:
  - null
---

## Prompt

User requested creation of a reusable Claude Code skill for OpenAI ChatKit UI implementation. Key requirements:
- Analyze existing ChatKit implementation in schema_agent.py and frontend
- Document streaming WorkflowItem patterns (tool display, tick marks, collapse)
- Document history persistence (PostgreSQL threads/messages)
- Ensure pure ChatKit usage (NO custom UI, NO React wrapper)
- Make it globally reusable across any project

## Response snapshot

Created comprehensive `openai-chatkit-ui` skill with:

1. **SKILL.md** - Main documentation with:
   - Critical rules (pure ChatKit, no React, no custom UI)
   - Tech stack reference
   - Quick start code examples
   - Implementation checklist

2. **Reference Files**:
   - `backend-integration.md` - FastAPI ChatKitServer, respond() method, SSE streaming
   - `frontend-widget.md` - CDN loading, setOptions(), session management
   - `streaming-workflow.md` - WorkflowItem, CustomTask, SearchTask, ThoughtTask patterns
   - `history-persistence.md` - PostgreSQL store, user-scoped queries, serialization
   - `theming.md` - CSS variables, theme presets
   - `events-api.md` - Event listeners, API methods

Key patterns documented:
- Auto-generated thread titles from first message
- Tool icon mapping for ChatKit
- Source URL extraction and formatting
- WorkflowItem collapse with DurationSummary

## Outcome

- ✅ Impact: High - Enables rapid ChatKit implementation in new projects
- 🧪 Tests: N/A (documentation skill)
- 📁 Files: 7 files created/modified in .claude/skills/openai-chatkit-ui/
- 🔁 Next prompts: Use skill in new project to validate patterns
- 🧠 Reflection: Extracting patterns from working implementation into reusable skill saves significant time

## Evaluation notes (flywheel)

- Failure modes observed: None - straightforward documentation extraction
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test skill invocation in fresh project
