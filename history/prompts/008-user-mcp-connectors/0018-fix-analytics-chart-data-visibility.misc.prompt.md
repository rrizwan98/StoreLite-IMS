---
id: "0018"
title: fix-analytics-chart-data-visibility
stage: misc
date: 2026-01-01
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: developer
command: /sp.git.commit_pr
labels: [bugfix, analytics, chatkit, chart-data]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/15
files:
  - backend/app/routers/schema_agent.py
tests:
  - manual testing of analytics tool response
---

## Prompt

Fix the issue where raw `<!--CHART_DATA [...] -->` comment is visible to users when using the Analytics tool in ChatKit. The user should see a clean, concise response with bullet points, followed by a chart widget - NOT the raw JSON data comment.

## Response snapshot

Identified the root cause: CHART_DATA extraction was happening AFTER the response was already sent to the user.

**Fix applied to `backend/app/routers/schema_agent.py`:**

Moved CHART_DATA extraction logic BEFORE the response is yielded:

```
BEFORE (wrong order):
1. final_text = format_response (with CHART_DATA)
2. yield response to user (CHART_DATA visible!)
3. extract CHART_DATA (too late!)

AFTER (correct order):
1. Extract CHART_DATA from response_text
2. Remove CHART_DATA from response_text
3. final_text = format_response (clean)
4. yield response to user (clean!)
5. Generate chart from extracted data
```

## Outcome

- ✅ Impact: Users no longer see raw `<!--CHART_DATA [...] -->` in Analytics tool responses
- 🧪 Tests: Manual testing - chart displays correctly without raw data visible
- 📁 Files: 1 file modified (schema_agent.py: +34, -22 lines)
- 🔁 Next prompts: Test with various query types to ensure charts render properly
- 🧠 Reflection: Order of operations matters - always process/clean data before sending to user

## Evaluation notes (flywheel)

- Failure modes observed: Response sent before data extraction completed
- Graders run and results (PASS/FAIL): PASS - visual verification
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add more chart types support
