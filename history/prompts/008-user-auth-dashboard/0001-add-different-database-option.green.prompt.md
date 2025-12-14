---
id: "0001"
title: "add-different-database-option"
stage: green
date: 2025-12-14
surface: claude-code
model: claude-opus-4-5-20251101
feature: "008-user-auth-dashboard"
branch: "007-ai-dashboard"
user: rrizwan98
command: /sp.git.commit_pr
labels: [auth, dashboard, connect-page, mcp]
links:
  spec: specs/008-user-auth-dashboard/spec.md
  ticket: null
  adr: null
  pr: https://github.com/rrizwan98/StoreLite-IMS/pull/9
files:
  - frontend/app/dashboard/connect/page.tsx
  - backend/app/routers/inventory_agent.py
tests:
  - null
---

## Prompt

dashboard mai yia featcher add kro k jis account say user login h check kro k user nay apna database connect yia hwa h k nh. usining URL, if yes tu user ko dubra say `PostgreSQL Database URI` show nh krwao use ko direct connect ka option do yia phr user ko option do k user dfferent database jb user user differnt database option chose kry tu, phr user `PostgreSQL Database URI` ka option do takay user differnt URL day sakay.

(Translation: Add a feature to the dashboard that checks if the logged-in user has already connected their database. If yes, don't show the PostgreSQL Database URI input again - give them a direct connect option. Also give an option to "Use Different Database", and when selected, show the URI input field so user can enter a different URL.)

## Response snapshot

Implemented "Use Different Database" feature on Connect page:

**Frontend (connect/page.tsx):**
1. Added state variables: `useDifferentDb`, `newDatabaseUri`, `savingUri`
2. Modified `connectDatabase()` to accept `useNewUri` parameter
3. Updated UI in Step 1:
   - If URI stored and not using different DB: Show "Database URI Configured" badge + "Connect" button + "Use Different Database" option
   - If no URI stored OR using different DB: Show URI input field with Cancel option

**Backend (inventory_agent.py):**
1. Modified `/connect` endpoint to prioritize user-provided `database_uri` over stored one
2. If new URI provided and connection succeeds, updates `user_connections` table with the new URI
3. Added `should_save_new_uri` flag to track when to save

## Outcome

- Impact: Users can now quickly connect with stored credentials or switch to different database
- Tests: Manual testing required
- Files: 2 files modified (frontend/app/dashboard/connect/page.tsx, backend/app/routers/inventory_agent.py)
- Next prompts: Test the feature with actual database connections
- Reflection: Clean separation of concerns - frontend handles UI state, backend handles URI storage

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A - manual feature
- Prompt variant (if applicable): N/A
- Next experiment: Add confirmation dialog before switching databases
