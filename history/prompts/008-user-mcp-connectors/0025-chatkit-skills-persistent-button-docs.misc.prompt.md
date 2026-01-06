---
id: "0025"
title: "ChatKit Skills Persistent Button Docs"
stage: misc
date: 2026-01-06
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: rrizwan98
command: null
labels: [chatkit, skills, documentation, persistent-buttons]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/17
files:
  - .claude/skills/chatkit-data-visualization/SKILL.md
  - .claude/skills/openai-chatkit-ui/SKILL.md
tests:
  - null
---

## Prompt

User requested to add the persistent/pinned button pattern documentation to both ChatKit skills (openai-chatkit-ui and chatkit-data-visualization) so that this pattern doesn't need to be re-explained in future ChatKit implementations across projects.

Original message (Urdu/Roman): "ok hamary pass chatkit k 2 skills bnay hway hyn aik Visualization, or aik chatkit UI dono mai yia update add kr kro takay kbhi bhi in future chatkit ksi bhi project mai implement kryn tu yia baat bar bar na btani prhy."

## Response snapshot

Added comprehensive "Persistent Tool/Connector Selection (Pinned Buttons)" section to both skills:

1. **openai-chatkit-ui/SKILL.md** - Added section with:
   - Problem explanation (tool deselects after each message)
   - Solution code example with `persistent: true` and `pinned: true`
   - Key properties table
   - Bad vs Good code patterns (don't auto-reset)
   - Behavior comparison table

2. **chatkit-data-visualization/SKILL.md** - Added section with:
   - Why persistence matters for data exploration workflows
   - Implementation example for visualization tools
   - Added mistake #8 to common mistakes list
   - Scenario-based behavior comparison for analytics use case

## Outcome

- Impact: Documentation improvement for reusable pattern
- Tests: N/A (documentation only)
- Files: 2 skill files updated (+212 lines)
- Next prompts: None required
- Reflection: Good pattern to document learnings in skills for future reuse

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
