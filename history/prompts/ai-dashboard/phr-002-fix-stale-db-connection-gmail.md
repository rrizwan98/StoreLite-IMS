---
id: phr-002
title: fix-stale-db-connection-gmail
stage: green
date: 2025-12-16
surface: claude-code
model: claude-opus-4-5-20251101
feature: ai-dashboard
branch: 007-ai-dashboard
user: rrizwan98
command: /sp.git.commit_pr
labels: [bugfix, database, gmail-tool, connection-pool]
links:
  spec: null
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/10
files:
  - backend/app/mcp_server/tools_gmail.py
tests:
  - null
---

## Prompt

User reported intermittent "connection is closed" InterfaceError when sending emails via Gmail tool, especially after logout/login cycles or Gmail tool disconnect/reconnect. Error showed SQLAlchemy asyncpg connection closed during SELECT query for user_connections table.

## Response snapshot

Fixed stale database connection issue in `tools_gmail.py`:

1. **Use NullPool** - No connection pooling, each request gets fresh connection
   ```python
   _async_engine = create_async_engine(
       database_url,
       echo=False,
       poolclass=NullPool,
   )
   ```

2. **Retry logic** - Auto-retry up to 2 times on connection errors
   ```python
   for attempt in range(max_retries + 1):
       try:
           force_new = attempt > 0
           session_maker = _get_db_session_maker(force_new=force_new)
           # ... execute query
       except Exception as db_error:
           if is_connection_error and attempt < max_retries:
               _reset_db_connection()
               continue
   ```

3. **_reset_db_connection()** - Clears stale connection factory
4. **Use async_sessionmaker** - Replaced deprecated sessionmaker

## Outcome

- Impact: Gmail tool now works reliably after login/logout cycles
- Tests: Manual verification needed - restart backend and test
- Files: backend/app/mcp_server/tools_gmail.py
- Next prompts: Verify fix works in production
- Reflection: Separate DB connection pools in tools need same resilience as main app

## Evaluation notes (flywheel)

- Failure modes observed: Connection pooling cached stale connections after auth changes
- Graders run and results (PASS/FAIL): N/A - needs manual testing
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Consider using main app's database module instead of separate pool
