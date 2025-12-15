# PHR-0012: PostgreSQL Session Persistence for MCP Connections

## Date: 2025-12-13
## Status: GREEN (Completed Successfully)
## Type: Feature Implementation

---

## User Request (Original - Urdu/English)

> "ok ab connect database section mai jb hum database ko URL k through connect krty hyn, or successfull connect ho jata h sub kuch bilkul perfect work kr rha ho h. but jb mai page ko refreash krta hon yia subra wapsi page per aata hon tu mujy again mcp connect krna prh rha h. tu plz is ko aesa kro jb tk mai khud disconnect na kron tu mcp server disconnect na ho. aik disconnect ka button jis say mcp disconnect ho jay."

> "local storage ko use na kro, postgress sql mai session ko manage kro posgress sql ka URL .env file mai h is database mai add krna."

## Translation

- MCP database sessions should persist across page refreshes
- Session should remain connected until user manually clicks "Disconnect"
- **DO NOT use localStorage** - use PostgreSQL database for session storage
- Database URL is available in `.env` file (`DATABASE_URL`)
- Add a prominent disconnect button for manual disconnection

---

## Solution Implemented

### 1. Backend: SessionPersistence Class (`backend/app/routers/inventory_agent.py`)

Created a new `SessionPersistence` class with asyncpg for PostgreSQL session management:

```python
class SessionPersistence:
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def get_pool(cls) -> Optional[asyncpg.Pool]:
        # Creates asyncpg connection pool
        # Handles channel_binding parameter removal (not supported by asyncpg)

    @classmethod
    async def init_table(cls) -> bool:
        # Creates mcp_sessions table if not exists

    @classmethod
    async def save_session(cls, session_id: str, database_uri: str, mcp_tools: List[str]) -> bool:
        # Saves/updates session in database (UPSERT)

    @classmethod
    async def get_active_session(cls) -> Optional[Dict[str, Any]]:
        # Returns most recent active session

    @classmethod
    async def deactivate_session(cls, session_id: str) -> bool:
        # Marks session as inactive
```

### 2. Database Schema: `mcp_sessions` Table

```sql
CREATE TABLE IF NOT EXISTS mcp_sessions (
    session_id TEXT PRIMARY KEY,
    user_database_uri TEXT NOT NULL,
    mcp_tools TEXT[] DEFAULT '{}',
    connected_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
)
```

### 3. New API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/inventory-agent/active-session` | GET | Check for active session in PostgreSQL |
| `/inventory-agent/restore` | POST | Restore session from database and reconnect MCP |

### 4. Frontend: Auto-Restore Logic (`frontend/app/db-connect/page.tsx`)

- Added `restoring` state (starts as `true`)
- Added `activeSession` state to track restored session
- Created `checkAndRestoreSession()` effect that:
  1. Checks MCP status
  2. Checks for active session via `/inventory-agent/active-session`
  3. Automatically restores session if found via `/inventory-agent/restore`
  4. Goes directly to chat step if restore successful
- Added loading UI while restoring
- Made disconnect button prominent (red color with icon)

---

## Test Results

All API endpoints tested successfully:

```bash
# 1. Connect to database
POST /inventory-agent/connect
Response: {"success":true,"session_id":"ffd1cede",...}

# 2. Verify session saved to PostgreSQL
GET /inventory-agent/active-session
Response: {"has_active_session":true,"session":{"session_id":"ffd1cede",...}}

# 3. Test restore (simulating page refresh)
POST /inventory-agent/restore
Response: {"success":true,"session_id":"ffd1cede","message":"Session already active",...}

# 4. Test disconnect
DELETE /inventory-agent/disconnect/ffd1cede
Response: {"success":true,"message":"MCP session closed successfully"}

# 5. Verify session deactivated
GET /inventory-agent/active-session
Response: {"has_active_session":false,"session":null,"mcp_server_running":false}
```

---

## Key Technical Decisions

1. **asyncpg over SQLAlchemy**: Used asyncpg directly for better async performance and simpler connection pooling
2. **channel_binding removal**: DATABASE_URL from Neon includes `channel_binding=require` which asyncpg doesn't support - code strips this parameter
3. **UPSERT pattern**: Session save uses `ON CONFLICT DO UPDATE` for idempotent saves
4. **Auto-restore on mount**: Frontend checks and restores session immediately on page load

---

## Files Modified

- `backend/app/routers/inventory_agent.py` - Added SessionPersistence class and new endpoints
- `frontend/app/db-connect/page.tsx` - Added auto-restore logic and prominent disconnect button

---

## User Benefit

- No need to reconnect MCP after page refresh
- Session persists until manual disconnect
- Clear visual disconnect button (red) for user control
- Seamless experience across browser sessions
