---
id: phr-001
title: remove-custom-gmail-button-ui
stage: refactor
date: 2025-12-16
surface: claude-code
model: claude-opus-4-5-20251101
feature: ai-dashboard
branch: 007-ai-dashboard
user: rrizwan98
command: /sp.git.commit_pr
labels: [ui, chatkit, gmail-tool, cleanup]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/10
files:
  - frontend/app/dashboard/schema-agent/page.tsx
tests:
  - null
---

## Prompt

User requested to remove the custom green Gmail button from the Schema Agent UI and use only ChatKit's native + button for tool selection. The user explicitly said: "tool selection k lyia pure chatkit ko use kyia jay user + k button say email tool ko select kr lay. thats it. but jo tum uppper green color say mail k button ko use kr rhy ho on off us ki hatao"

## Response snapshot

Removed custom green Gmail ON/OFF button UI from `page.tsx`:
- Removed `activeTool` state and `selectTool`/`disconnectTool` callbacks
- Removed `toolPersistent` variable
- Removed the Tool Selection Bar JSX (lines 407-432)
- Kept ChatKit's `composer.tools` configuration for native + button
- Kept fetch interceptor for `[TOOL:GMAIL]` prefix injection
- Tool selection now handled entirely through ChatKit events

Changes: -56 lines, +14 lines (net cleanup of 42 lines)

## Outcome

- Impact: UI simplified, uses only ChatKit native tool selector
- Tests: N/A - UI refactor
- Files: frontend/app/dashboard/schema-agent/page.tsx
- Next prompts: Test tool selection from ChatKit + button in browser
- Reflection: Clean separation - backend handles tool logic, frontend just passes selection

## Evaluation notes (flywheel)

- Failure modes observed: None - straightforward UI cleanup
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Verify ChatKit log events fire correctly for tool selection
