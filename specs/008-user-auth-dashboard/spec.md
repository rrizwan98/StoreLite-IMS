# Specification: User Authentication & Personalized Dashboard

**Version:** 1.0
**Date:** December 14, 2025
**Branch:** 008-user-auth-dashboard
**Status:** Draft

---

## 1. Goal

Transform the application from a single-session experience to a multi-user platform with:
- User authentication (Login/Signup)
- Personalized database connections per user
- User-specific AI Analytics Dashboard connected to user's own MCP server
- Data separation by user_id

---

## 2. Current State

### Current Architecture:
- **Landing Page**: Shows all features (Admin, POS, Connect DB, Analytics) without auth
- **DB Connect**: Connects to user's PostgreSQL via MCP, session-based (in-memory)
- **AI Analytics**: Uses shared backend database, not user-specific
- **No user authentication** - anyone can access all features

### Files to Modify:
- Frontend: `page.tsx` (landing), `layout.tsx`, `db-connect/page.tsx`, `analytics/page.tsx`
- Backend: `models.py`, new `routers/auth.py`, `routers/inventory_agent.py`
- Database: Add `users` table, `user_connections` table

---

## 3. Requirements

### 3.1 Landing Page (New)
- Static page showing project overview
- **StoreLite IMS** branding and feature highlights
- Two CTAs:
  - Login button → `/login`
  - Signup button → `/signup`
- No access to features without authentication

### 3.2 Authentication System

#### User Model (PostgreSQL)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP
);
```

#### User Preferences/Connection Storage
```sql
CREATE TABLE user_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL, -- 'own_database' or 'our_database'
    database_uri TEXT, -- Encrypted storage for user's DB URI
    mcp_server_status VARCHAR(50) DEFAULT 'disconnected', -- 'connected', 'disconnected'
    last_connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);
```

#### Authentication Endpoints
- `POST /auth/signup` - Create new user
- `POST /auth/login` - Login, return JWT token
- `POST /auth/logout` - Invalidate token
- `GET /auth/me` - Get current user info

### 3.3 First-Time User Flow

When user logs in for the first time:
1. Show service selection screen:
   - **Option A**: "Connect Your Own Database"
     - User provides PostgreSQL DATABASE_URI
     - Connect via MCP server
     - Store connection for future logins
   - **Option B**: "Use Our Database"
     - Use the shared IMS database
     - Standard inventory management

2. Store user's choice in `user_connections` table
3. On subsequent logins, restore their connection automatically

### 3.4 Dashboard (Post-Login)

#### If user chose "Connect Own Database":
- Show: DB Connection status, AI Analytics Dashboard
- AI Analytics connects to **user's MCP server** (not our database)
- Disconnect option available (returns to service selection)

#### If user chose "Our Database":
- Show: Admin, POS, AI Analytics (connected to our database)
- Full inventory management features

### 3.5 AI Analytics Dashboard - User MCP Integration

**Critical Change**: The Analytics Dashboard must connect to user's MCP server when user has their own database connected.

#### Current Flow (Analytics):
```
User Query → /agent/chatkit → Our Database
```

#### New Flow (User's Database):
```
User Query → /agent/chatkit?user_id=X → User's MCP Server → User's Database
```

#### Implementation:
1. Analytics page checks if user has MCP connection
2. If yes: Route through user's MCP server
3. If no: Use default database
4. ChatKit configuration includes user_id and session_id

---

## 4. UI Flow

```
[Landing Page]
    │
    ├─→ [Login] ──→ [Dashboard]
    │                   │
    │                   ├─→ (First time) [Service Selection]
    │                   │                    │
    │                   │                    ├─→ "Connect Own DB" → [DB Connect Flow]
    │                   │                    │                           │
    │                   │                    │                           └─→ [User Dashboard + Analytics]
    │                   │                    │
    │                   │                    └─→ "Use Our DB" → [Full IMS Dashboard]
    │                   │
    │                   └─→ (Returning user) → [Restore Connection] → [Dashboard]
    │
    └─→ [Signup] → [Login]
```

---

## 5. Page Structure

### 5.1 New Routes
- `/` - Landing page (public)
- `/login` - Login page (public)
- `/signup` - Signup page (public)
- `/dashboard` - User dashboard (protected)
- `/dashboard/connect` - DB connection page (protected)
- `/dashboard/analytics` - AI Analytics (protected, user-specific)
- `/dashboard/admin` - Inventory Admin (protected, our DB users only)
- `/dashboard/pos` - POS (protected, our DB users only)

### 5.2 Auth Protection
- All `/dashboard/*` routes require authentication
- Redirect to `/login` if not authenticated
- Store JWT in localStorage or httpOnly cookie

---

## 6. Backend Changes

### 6.1 New Files
- `backend/app/routers/auth.py` - Authentication endpoints
- `backend/app/services/auth_service.py` - Auth logic (JWT, password hashing)

### 6.2 Modified Files
- `backend/app/models.py` - Add User, UserConnection models
- `backend/app/routers/inventory_agent.py` - Add user_id support
- `backend/app/routers/analytics.py` - Route to user's MCP if connected

### 6.3 Dependencies to Add
- `python-jose[cryptography]` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data parsing

---

## 7. Frontend Changes

### 7.1 New Files
- `frontend/app/(public)/page.tsx` - New landing page
- `frontend/app/(public)/login/page.tsx` - Login page
- `frontend/app/(public)/signup/page.tsx` - Signup page
- `frontend/app/(protected)/dashboard/page.tsx` - User dashboard
- `frontend/app/(protected)/dashboard/layout.tsx` - Protected layout
- `frontend/lib/auth-context.tsx` - Auth state management
- `frontend/lib/auth-api.ts` - Auth API calls

### 7.2 Modified Files
- `frontend/app/layout.tsx` - Add auth provider
- `frontend/lib/constants.ts` - Add new routes

---

## 8. Security Considerations

1. **Password Storage**: bcrypt hashing with salt
2. **JWT**: Short-lived access tokens (1 hour), refresh tokens (7 days)
3. **Database URI**: Consider encryption at rest
4. **MCP Connection**: User's credentials never stored in our logs
5. **CORS**: Restrict to frontend origin only

---

## 9. Acceptance Criteria

- [ ] User can signup with email/password
- [ ] User can login and receive JWT
- [ ] First-time user sees service selection
- [ ] User can connect their own PostgreSQL database
- [ ] User's MCP connection persists across sessions
- [ ] AI Analytics Dashboard uses user's MCP when connected
- [ ] User can disconnect and choose different service
- [ ] Each user's data is completely separate
- [ ] Returning user's MCP connection is auto-restored

---

## 10. Out of Scope (v1.0)

- Social login (Google, GitHub)
- Email verification
- Password reset flow
- Multi-database per user
- Team/Organization features
- Audit logging

---

## 11. Migration Strategy

1. Add new tables without breaking existing functionality
2. Existing routes remain accessible during development
3. Feature flag to enable/disable auth requirement
4. Gradual rollout: Auth optional → Auth required
