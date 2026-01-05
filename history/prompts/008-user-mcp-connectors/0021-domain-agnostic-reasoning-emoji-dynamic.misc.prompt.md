---
id: "0021"
title: domain-agnostic-reasoning-emoji-dynamic
stage: misc
date: 2026-01-02
surface: claude-code
model: claude-opus-4-5-20251101
feature: 008-user-mcp-connectors
branch: 008-user-mcp-connectors
user: HP
command: /sp.git.commit_pr
labels: [agent, prompt-engineering, domain-agnostic, reasoning, emoji, formatting]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/15
files:
  - backend/app/agents/schema_query_agent.py
  - .claude/settings.local.json
  - history/prompts/008-user-mcp-connectors/0020-schema-formatting-git-commit-pr.misc.prompt.md
tests:
  - null
---

## Prompt

User requested improvements to schema_query_agent to make it domain-agnostic with proper reasoning, dynamic emoji generation, and professional formatting. Key requirements:
1. Remove all hardcoded domain-specific examples (Rice, PKR, products, sales)
2. Add reasoning capability before generating responses
3. Make emoji selection fully dynamic (agent generates based on domain/context)
4. Ensure proper formatting: bold headings, bullet points, tables, clickable links
5. Use professional English throughout (no Roman Urdu in prompt)

## Response snapshot

Implemented comprehensive improvements to schema_query_agent v2.5.0:

1. **Reasoning Section Added** - 4-step internal reasoning process:
   - Step 1: Domain Detection (from schema tables/columns)
   - Step 2: Query Intent Classification (data, analysis, action, question, search)
   - Step 3: Emotional Context Detection (worried, positive, neutral, curious, frustrated)
   - Step 4: Response Planning (heading, emoji, structure, insights)

2. **Fully Dynamic Emoji Selection** - Removed all predefined emoji lists:
   - Agent analyzes response content, query intent, domain, and emotional context
   - Generates contextually appropriate emojis from Unicode standard
   - Works for any domain: medical, education, finance, etc.

3. **Domain-Agnostic Examples** - Replaced all specific examples:
   - `Rice, Sugar` → `[entity]`, `[record]`
   - `PKR` → Detect from data context
   - `sales_2023` → `[table]_2023`
   - `products by price` → `[entities] by [metric]`

4. **Proper Formatting Rules**:
   - Headings: `###` with bold and contextual emoji
   - Tables: Proper separator, concise cells
   - Links: Clickable `[Text](URL)` format
   - Lists: Bullets, numbers, nesting rules

Commit: 874b9c2
Version: 2.5.0-domain-agnostic-reasoning

## Outcome

- Impact: Agent now supports any data domain without hardcoded assumptions
- Tests: N/A (prompt engineering changes)
- Files: 3 files committed (+273/-95 lines)
- Next prompts: Test with different domain databases (medical, education)
- Reflection: Moving from hardcoded to agent-driven selection provides flexibility for N domains

## Evaluation notes (flywheel)

- Failure modes observed: Initial implementation still had hardcoded emoji palette
- Graders run and results (PASS/FAIL): PASS - all domain-specific terms removed
- Prompt variant (if applicable): v2.5.0-domain-agnostic-reasoning
- Next experiment (smallest change to try): Test response quality across different domains
