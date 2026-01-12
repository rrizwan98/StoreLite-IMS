---
id: phr-2026-01-11-001
title: Fix Scheduler Connector Tools
stage: green
date: 2026-01-11
feature: scheduler-task-automation
tags: [scheduler, connector-tools, bugfix]
---

# Fix Scheduler Connector Tools

## Prompt

User reported scheduled tasks failing with error:
```
Tool gdrive_connector_list_files not found in agent Schema Query Agent
```

The scheduler was manually building tools using functions that didn't exist. Need to fix task_executor_service.py to use the same connector tools that ChatKit uses.

## Response

Fixed by:
1. Replaced custom `_build_selected_tools()` with `get_connector_agent_tools(db, user_id)` from registry
2. Added `_utc_now_naive()` helper for PostgreSQL datetime compatibility
3. Added `_build_tool_hints()` for natural language tool guidance
4. Now uses exact same code path as ChatKit for loading connector tools

## Learnings

- **Use shared infrastructure**: Instead of duplicating tool-building logic, use the existing `get_connector_agent_tools()` from connector registry
- **PostgreSQL datetime**: `TIMESTAMP WITHOUT TIME ZONE` columns require naive datetimes (no timezone info)
- **Tool hints**: Natural language hints help LLM understand which tools to prioritize

## Outcome

- PR #31 created: https://github.com/rrizwan98/StoreLite-IMS/pull/31
- All connector tools (gdrive, gmail, notion, retell_ai) now work in scheduler
