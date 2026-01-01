---
id: "0017"
title: "ChatKit Analytics Chart Visualization"
stage: misc
date: 2026-01-01
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: rrizwan98
command: /sp.git.commit_pr
labels: [chatkit, analytics, charts, visualization, widgets]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/15
files:
  - backend/app/routers/schema_agent.py
  - backend/app/agents/schema_query_agent.py
  - backend/app/tools/registry.py
tests:
  - null
---

## Prompt

User requested implementation of analytics chart visualization in ChatKit responses. Requirements:
- Use existing "Use Analytics" tool in ChatKit
- When user selects tool, agent should generate chart (bar, line, or area) based on query
- Auto-detect chart type based on query keywords (trends=line, comparison=bar, volume=area)
- Show chart in ChatKit response using pure ChatKit widgets (no custom UI)
- Support both user-selected mode and agent auto-mode for chart suggestions
- Make chart full-screen responsive with proper sizing

## Response snapshot

Implemented comprehensive analytics chart visualization:

1. **Chart Widget Integration** (schema_agent.py):
   - Added imports: Chart, BarSeries, LineSeries, AreaSeries, Card, Box, Title
   - Created helper functions: `detect_chart_type()`, `detect_chart_columns()`, `create_chart_widget()`
   - Analytics mode detection via `[TOOL:ANALYTICS]` prefix
   - Data capture from tool output with fallback extraction from response text
   - Chart streaming using ChatKit's `stream_widget()` function

2. **Chart Styling**:
   - Responsive sizing: `height="55vh"`, `width="100%"`, `aspectRatio="16/9"`
   - Bar spacing: `barGap=4`, `barCategoryGap=24`
   - Card wrapper with `size="full"`, `background="surface-elevated"`
   - Box containers for proper padding and layout

3. **Agent Prompt Updates** (schema_query_agent.py):
   - Added `[TOOL:ANALYTICS]` handling with concise response format
   - CHART_DATA comment block for hidden data embedding
   - Auto-analytics mode with TIP suggestions for chart-worthy queries

4. **Tool Registry Update**:
   - Renamed to "Use Analytics"
   - Updated description: "Visualize data with charts (bar, line, area graphs)"

## Outcome

- ✅ Impact: High - Enables visual data analysis in ChatKit responses
- 🧪 Tests: Manual testing (chart displays correctly)
- 📁 Files: 3 files modified (+433 lines)
- 🔁 Next prompts: Test with various query types, add more chart customization
- 🧠 Reflection: Pure ChatKit widget approach works well; CHART_DATA extraction provides reliable fallback

## Evaluation notes (flywheel)

- Failure modes observed: Initial f-string escaping issue with `{}` in JSON examples (fixed with `{{}}`)
- Graders run and results (PASS/FAIL): N/A (manual testing)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add color customization options for chart series
