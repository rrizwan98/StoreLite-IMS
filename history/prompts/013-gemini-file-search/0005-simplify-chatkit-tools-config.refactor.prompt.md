---
id: "0005"
title: simplify-chatkit-tools-config
stage: refactor
date: 2026-01-12
surface: claude-code
model: claude-opus-4-5-20251101
feature: schema-agent-chatkit
branch: feat/schema-agent-chatkit-dark-theme
user: developer
command: manual
labels: [chatkit, tools, refactor, simplification]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/40
files:
  - frontend/app/dashboard/schema-agent/page.tsx
tests:
  - manual verification of tools dropdown
---

## Prompt

User reported that the "See more tools" button in schema-agent ChatKit UI was not working correctly. When clicked, the button would become invisible and require clicking the "+" button again to see all tools. User wanted ChatKit's native tool overflow handling instead of custom code.

## Response snapshot

Investigated ChatKit documentation via Context7 and found that:
1. ChatKit natively handles tool overflow with scrollable dropdown menu
2. The `pinned` property controls whether tools appear as buttons (true) or in dropdown (false)
3. Custom pagination logic was conflicting with ChatKit's native behavior

Removed:
- `showAllTools` state variable
- `MAX_VISIBLE_TOOLS` constant
- Custom `__see_more__` tool option
- Related event handlers for see more button clicks

Simplified `buildChatKitTools` to pass all tools directly to ChatKit, letting it handle the dropdown menu natively.

## Outcome

- Impact: Simplified code, removed ~50 lines of custom logic
- Tests: Manual - verified build passes
- Files: 1 file modified (page.tsx)
- Next prompts: None - feature complete
- Reflection: ChatKit SDK handles tool overflow natively; custom implementations can conflict with SDK behavior

## Evaluation notes (flywheel)

- Failure modes observed: Custom tool pagination conflicted with ChatKit's native dropdown behavior
- Graders run and results (PASS/FAIL): Build PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Trust SDK defaults before implementing custom solutions
