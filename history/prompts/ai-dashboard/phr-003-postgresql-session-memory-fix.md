---
id: phr-003
title: PostgreSQL Session Memory Fix
stage: green
feature: ai-dashboard
date: 2025-12-16
tags: [session, postgresql, openai-agents-sdk, memory, neon]
---

# PHR-003: PostgreSQL Session Memory Fix

## Prompt

User requested PostgreSQL-backed session memory for Schema Agent to persist conversation history across page reloads. Initial implementation using `SQLAlchemySession` from OpenAI Agents SDK failed with `NotNullViolationError` due to:
1. Existing `agent_sessions` table with incompatible schema (had extra `id` column)
2. Neon pooler URL causing prepared statement cache issues after schema changes

## Response

### Root Cause Analysis
- Old `agent_sessions` table had schema: `id`, `session_id`, `conversation_history`, `session_metadata`, `created_at`, `updated_at`
- SDK expected: `session_id` (PK), `created_at`, `updated_at`
- Neon pooler (`-pooler.` in URL) caches prepared statements server-side, causing errors after schema changes

### Solution Implemented

1. **Dropped old tables** via direct SQL to allow SDK to recreate with correct schema

2. **Created `agent_session_service.py`**:
   - Uses `SQLAlchemySession.from_url()` for proper table creation
   - Converts Neon pooler URLs to direct URLs (removes `-pooler`)
   - Implements session caching to avoid recreating instances
   - Provides `AgentSessionManager` class for convenient session handling

3. **Updated `schema_query_agent.py`**:
   - Integrated `AgentSessionManager` for session persistence
   - Fixed async/sync mismatch (changed `await get_session()` to sync call)
   - Passes session to `Runner.run()` for automatic history persistence

4. **Updated `schema_agent.py` router**:
   - Passes `thread_id` from ChatKit to agent for session identification

5. **Added cleanup in `main.py`**:
   - Session cache cleared on app shutdown

### Key Technical Details
- Direct Neon connection avoids PgBouncer prepared statement cache issues
- SDK auto-manages `agent_sessions` and `agent_messages` tables
- Session ID format: `user-{user_id}-{thread_id[:20]}`

## Learnings

1. **Neon pooler vs direct connection**: Pooler uses PgBouncer which caches prepared statements. After schema changes, this causes `InvalidCachedStatementError`. Use direct connection for session management.

2. **OpenAI SDK SQLAlchemySession**: Use `from_url()` method, not engine constructor, for reliable table creation.

3. **Schema conflicts**: When using SDK-managed tables, ensure no conflicting tables exist from previous implementations.

4. **Session caching**: Cache session instances in memory to avoid recreating database connections on every message.
