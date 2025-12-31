---
id: "0015"
title: "Source Formatting for Web Search Responses"
stage: misc
date: 2025-12-31
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: human
command: /sp.git.commit_pr
labels: [chatkit, sources, web-search, formatting]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/14
files:
  - backend/app/routers/schema_agent.py
tests:
  - null
---

## Prompt

User requested better source formatting for web search responses in ChatKit. The raw Sources section was showing as plain text with markdown link syntax visible (like `[xyz.pk](https://www.xyz.pk)`). User wanted:

1. Clean domain names inline (not markdown syntax)
2. Clickable URLs in the Sources section
3. Proper formatting with numbered sources

## Response snapshot

Implemented `format_response_with_sources()` function that:
- Extracts URLs from markdown links `[Title](URL)` format
- Extracts URLs from plain text format `- Name: https://...`
- Removes duplicate Sources sections from agent responses
- Adds a clean **Sources:** section with numbered items
- Uses bare URLs for ChatKit auto-linking since markdown links don't render

Key changes:
- Added Annotation import (for future use)
- Changed search_urls to search_sources (dict with url+title)
- Fixed created_at to use datetime object instead of isoformat string
- Added format_response_with_sources() helper function

## Outcome

- Impact: Web search responses now display sources cleanly with numbered list and bare URLs
- Tests: Manual testing required
- Files: backend/app/routers/schema_agent.py (+150, -9)
- Next prompts: May need to explore ChatKit annotation support further
- Reflection: ChatKit's custom API mode doesn't render markdown links, so bare URLs are the solution

## Evaluation notes (flywheel)

- Failure modes observed: ChatKit annotations don't work with custom API setup, markdown links render as raw text
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Test if ChatKit auto-links bare URLs correctly
