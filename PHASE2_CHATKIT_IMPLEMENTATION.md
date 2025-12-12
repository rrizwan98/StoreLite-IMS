# Phase 2 Implementation Guide: ChatKit Integration (Updated with Skill Patterns)

**Date**: 2025-12-09
**Status**: T006 Complete - Backend Schemas ✅
**Skill Used**: openai-chatkit-ui (official patterns)
**Next**: T007-T014 (Session Manager, Router, Frontend)

---

## ✅ T006: COMPLETE - ChatKit Pydantic Schemas

**File**: `backend/app/schemas.py`

Added three ChatKit-specific schema classes:

1. **ChatKitMessage** - Request schema for `/agent/chat` endpoint
   ```python
   - session_id: str (tab-lifetime session from client)
   - message: str (user's natural language input)
   - user_id: Optional[str] (from app auth)
   - thread_id: Optional[str] (for grouping)
   ```

2. **ChatKitResponse** - Response schema for `/agent/chat` endpoint
   ```python
   - session_id: str (echo back for tracking)
   - message: str (agent response)
   - type: str ("text", "item_created", "bill_created", "item_list", "error")
   - structured_data: Optional[dict] (JSON for UI rendering)
   - timestamp: datetime (response time)
   - error: Optional[str] (error message if type="error")
   ```

3. **ChatKitSession & ChatKitSessionResponse** - Session management
   ```python
   - session_id: str (generated unique ID)
   - created_at: datetime (session creation time)
   ```

**Key Design Decision**: Used official ChatKit patterns from skill file:
- JSON schemas with proper type hints
- Optional structured_data for bills, items, etc. (ChatKit renders these)
- Timestamp tracking for observability
- Error handling built into response schema

---

## 📋 T007: Session Manager (NEXT)

**File**: `backend/app/services/session_service.py` (NEW)

Based on ChatKit skill patterns for self-hosted backends:

```python
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Optional
import json

class ChatKitSessionManager:
    """
    Tab-lifetime session management for ChatKit.

    Sessions persist while tab is open, expire on page close or logout.
    Based on ChatKit skill pattern: https://openai.github.io/chatkit-js/
    """

    def __init__(self, session_timeout_minutes: int = 30):
        # In-memory store (use Redis/DB in production)
        self._sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create new ChatKit session for vanilla JS client.
        Called when ChatKit initializes on page load.
        """
        session_id = f"session-{int(datetime.utcnow().timestamp() * 1000)}-{uuid4().hex[:12]}"

        self._sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "messages": [],  # Store conversation history
            "is_active": True
        }

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session by ID"""
        session = self._sessions.get(session_id)

        if session and not self._is_expired(session):
            return session

        # Clean up expired session
        if session:
            self._sessions.pop(session_id, None)

        return None

    def _is_expired(self, session: Dict) -> bool:
        """Check if session has expired"""
        elapsed = datetime.utcnow() - session["last_activity"]
        return elapsed > self.session_timeout

    def update_activity(self, session_id: str) -> bool:
        """Update session's last activity timestamp"""
        session = self._sessions.get(session_id)
        if session:
            session["last_activity"] = datetime.utcnow()
            return True
        return False

    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """Store message in session history"""
        session = self.get_session(session_id)
        if session:
            session["messages"].append({
                "role": role,  # "user" or "assistant"
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })
            return True
        return False

    def get_conversation_history(self, session_id: str) -> list:
        """Get all messages in session for agent context"""
        session = self.get_session(session_id)
        if session:
            return session["messages"]
        return []

    def close_session(self, session_id: str) -> bool:
        """Close session on logout or tab close"""
        if session_id in self._sessions:
            self._sessions[session_id]["is_active"] = False
            del self._sessions[session_id]
            return True
        return False

    def cleanup_expired(self) -> int:
        """Clean up expired sessions (call periodically)"""
        expired_ids = [
            sid for sid, sess in self._sessions.items()
            if self._is_expired(sess)
        ]
        for sid in expired_ids:
            del self._sessions[sid]
        return len(expired_ids)


# Global instance
session_manager = ChatKitSessionManager()
```

**Why**:
- Manages tab-lifetime sessions per spec (FR-017)
- Stores conversation history for context window
- Uses session_id format compatible with vanilla JS frontend
- Built-in expiry and cleanup for memory efficiency

---

## 📋 T008: Conversation History Model

**File**: `backend/app/models/conversation.py` (NEW)

```python
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ConversationHistory(Base):
    """
    Persistent storage for ChatKit conversations.
    Enables conversation recovery if user refreshes page (SC-005).
    """
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)

    # Message content
    user_message = Column(Text, nullable=False)  # What user typed
    agent_response = Column(Text, nullable=False)  # What agent said

    # Response metadata
    response_type = Column(
        String(50),
        nullable=True,
        default="text"  # "text", "item_created", "bill_created", "item_list"
    )
    structured_data = Column(Text, nullable=True)  # JSON for UI rendering

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Conversation session={self.session_id} type={self.response_type}>"
```

**Why**:
- Persistent audit trail of all conversations
- Enables recovery if user refreshes (SC-005)
- Structured data stored for analytics
- Indexed by session_id and created_at for queries

---

## 📋 T009: ChatKit Router

**File**: `backend/app/routers/chatkit.py` (NEW)

Based on official ChatKit self-hosted backend pattern:

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import json
from datetime import datetime
import logging

from app.schemas import ChatKitMessage, ChatKitResponse, ChatKitSession, ChatKitSessionResponse
from app.services.session_service import session_manager
from app.models.conversation import ConversationHistory
from app.database import get_db
from app.agents.agent import agent  # Phase 5 agent
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["chatkit"])

@router.post("/session", response_model=ChatKitSessionResponse)
async def create_chatkit_session(
    request: ChatKitSession,
):
    """
    Create new ChatKit session for vanilla JS client.
    Called when ChatKit initializes (on page load).

    Returns session_id that client stores in sessionStorage.
    """
    session_id = session_manager.create_session(user_id=request.user_id)

    logger.info(f"Created ChatKit session: {session_id[:20]}...")

    return ChatKitSessionResponse(
        session_id=session_id,
        created_at=datetime.utcnow()
    )


@router.post("/chat", response_model=ChatKitResponse)
async def chat_with_agent(
    request: ChatKitMessage,
    db: Session = Depends(get_db),
):
    """
    Main ChatKit endpoint for vanilla JS integration.

    Flow:
    1. Validate session exists
    2. Call OpenAI Agent with user message
    3. Route response to appropriate handler (inventory, billing, query)
    4. Store in conversation_history
    5. Return ChatKitResponse for vanilla JS to render

    Self-hosted backend pattern (NOT OpenAI Hosted):
    - Uses local OpenAI Agents SDK + MCP tools
    - ChatKit vanilla JS component calls this endpoint
    """

    try:
        # 1. Validate session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=401,
                detail="Session expired. Please refresh the page."
            )

        # 2. Update activity
        session_manager.update_activity(request.session_id)

        # 3. Get conversation history for agent context
        history = session_manager.get_conversation_history(request.session_id)

        # 4. Call OpenAI Agent
        logger.info(f"Chat message from {request.session_id}: {request.message[:50]}...")

        # Build prompt with history context
        context_text = _build_context(history)
        full_prompt = f"{context_text}\nUser: {request.message}"

        # Call agent
        agent_result = await agent.process_message(
            message=full_prompt,
            session_id=request.session_id,
            user_id=request.user_id
        )

        # 5. Parse agent response
        response_data = _parse_agent_response(agent_result)

        # 6. Store in conversation_history table
        history_entry = ConversationHistory(
            session_id=request.session_id,
            user_id=request.user_id,
            user_message=request.message,
            agent_response=response_data["message"],
            response_type=response_data["type"],
            structured_data=json.dumps(response_data.get("structured_data")) if response_data.get("structured_data") else None,
            created_at=datetime.utcnow()
        )
        db.add(history_entry)
        db.commit()

        # 7. Store in session memory for immediate retrieval
        session_manager.add_message(request.session_id, "user", request.message)
        session_manager.add_message(request.session_id, "assistant", response_data["message"])

        # 8. Return ChatKitResponse
        return ChatKitResponse(
            session_id=request.session_id,
            message=response_data["message"],
            type=response_data["type"],
            structured_data=response_data.get("structured_data"),
            timestamp=datetime.utcnow(),
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ChatKit error: {str(e)}", exc_info=True)

        return ChatKitResponse(
            session_id=request.session_id,
            message="An error occurred processing your request.",
            type="error",
            structured_data=None,
            timestamp=datetime.utcnow(),
            error=str(e)
        )


@router.post("/chat/stream")
async def stream_chat_with_agent(
    request: ChatKitMessage,
    db: Session = Depends(get_db),
):
    """
    Streaming chat endpoint for real-time responses (optional).

    For non-streaming: use regular /chat endpoint above.
    """

    async def generate():
        try:
            session = session_manager.get_session(request.session_id)
            if not session:
                yield f"data: {json.dumps({'error': 'Session expired'})}\n\n"
                return

            # Stream agent response
            async for chunk in agent.stream_message(request.message):
                yield f"data: {json.dumps({'delta': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


def _build_context(history: list) -> str:
    """Build context string from conversation history"""
    if not history:
        return "New conversation session."

    context_lines = ["Recent conversation history:"]
    for msg in history[-5:]:  # Last 5 messages
        role = "User" if msg["role"] == "user" else "Assistant"
        context_lines.append(f"{role}: {msg['content'][:200]}")

    return "\n".join(context_lines)


def _parse_agent_response(agent_result) -> dict:
    """
    Parse agent response into ChatKitResponse format.

    Agent returns different types based on intent:
    - "Add 10kg sugar..." → type="item_created" with structured_data
    - "Create bill for Ali..." → type="bill_created" with bill details
    - "Show inventory..." → type="item_list" with items
    """

    # For now, basic text response
    # User Story phases will enhance this with structured parsing

    return {
        "message": str(agent_result),
        "type": "text",
        "structured_data": None
    }
```

**Why**:
- Implements official ChatKit self-hosted backend pattern
- Session validation ensures security
- Conversation history stored in both memory (fast) and DB (persistent)
- Streaming support for real-time responses (optional)
- Error handling with proper HTTPException codes

---

## 📋 T010: FastAPI Integration

**File**: `backend/app/main.py` (UPDATE)

Add to existing main.py:

```python
# Add imports at top
from app.routers import chatkit

# Add to app setup (before running)
app.include_router(chatkit.router)

# CORS configuration (update if needed)
# Make sure to allow frontend origin:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend dev
        "http://localhost:8000",  # Swagger UI
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Result**:
- POST `/agent/session` - Create ChatKit session
- POST `/agent/chat` - Main chat endpoint (vanilla JS)
- POST `/agent/chat/stream` - Streaming endpoint (optional)

---

## 📋 T011: Pure Vanilla ChatKit Web Component

**File**: `frontend/public/chatkit-embed.html` (NEW)

Official ChatKit vanilla JS pattern (NO React):

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatKit Widget</title>

    <!-- Import ChatKit web component -->
    <script type="module">
        import '@openai/chatkit';
    </script>

    <style>
        /* Pure vanilla ChatKit - use CSS variables only */
        openai-chatkit {
            /* Official theme variables */
            --ck-accent-color: #3b82f6;
            --ck-background-color: #ffffff;
            --ck-text-color: #1f2937;
            --ck-border-radius: 8px;
            --ck-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

            /* Dimensions */
            height: 600px;
            width: 400px;
            border-radius: var(--ck-border-radius);
            box-shadow: var(--ck-shadow);
        }

        /* Fixed positioning for bottom-right corner */
        .chatkit-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
        }
    </style>
</head>
<body>
    <!-- ChatKit web component container -->
    <div class="chatkit-container">
        <openai-chatkit id="chat"></openai-chatkit>
    </div>

    <!-- Configuration script (vanilla JS, no React) -->
    <script type="module">
        import '@openai/chatkit';

        const chatkit = document.getElementById('chat');
        const API_URL = process.env.REACT_APP_AGENT_API_URL || 'http://localhost:8000/agent/chat';

        // Initialize session
        let sessionId = null;

        async function createSession() {
            try {
                const response = await fetch('http://localhost:8000/agent/session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: null })
                });

                if (!response.ok) throw new Error('Failed to create session');

                const data = await response.json();
                sessionId = data.session_id;

                // Store in sessionStorage for persistence across navigation
                sessionStorage.setItem('chatkit-session-id', sessionId);

                console.log('ChatKit session created:', sessionId);
            } catch (error) {
                console.error('Session creation failed:', error);
            }
        }

        // Configure ChatKit web component
        async function initializeChatKit() {
            // Create or restore session
            sessionId = sessionStorage.getItem('chatkit-session-id');
            if (!sessionId) {
                await createSession();
            }

            // Configure ChatKit (official pattern)
            chatkit.setOptions({
                // API configuration (self-hosted backend)
                api: {
                    url: API_URL,

                    // Custom fetch for session management
                    fetch: async (url, options) => {
                        // Add session_id to request body
                        const body = options.body ? JSON.parse(options.body) : {};
                        body.session_id = sessionId;

                        return fetch(url, {
                            ...options,
                            body: JSON.stringify(body),
                            headers: {
                                ...options.headers,
                                'Content-Type': 'application/json',
                            },
                        });
                    },
                },

                // Theme (official CSS variables)
                theme: {
                    colorScheme: 'light',
                    accentColor: '#3b82f6',
                    density: 'normal',
                },

                // Header with title
                header: {
                    title: 'AI Assistant',
                    showTitle: true,
                    icons: [
                        { type: 'new-thread' },
                        { type: 'settings' }
                    ],
                },

                // Start screen (initial greeting)
                startScreen: {
                    greeting: 'Hello! I can help you manage inventory and create bills. How can I assist?',
                    prompts: [
                        { text: 'Add item', prompt: 'Help me add a new inventory item' },
                        { text: 'Create bill', prompt: 'I need to create a bill' },
                        { text: 'Check inventory', prompt: 'Show me current inventory' },
                    ],
                },

                // Composer (input area)
                composer: {
                    placeholder: 'Type your message...',
                    allowAttachments: false,  // Phase 6 spec: text-only
                },

                // Disclaimer
                disclaimer: {
                    text: 'AI may make mistakes. Verify important information.',
                    position: 'bottom',
                },
            });

            // Event listeners (official events)

            // Log messages for debugging
            chatkit.addEventListener('message', (e) => {
                console.log('ChatKit message event:', e.detail);
            });

            // Handle errors
            chatkit.addEventListener('error', (e) => {
                console.error('ChatKit error:', e.detail);
            });

            // Track message end for analytics
            chatkit.addEventListener('message-end', (e) => {
                console.log('Message completed:', e.detail);
            });
        }

        // Initialize on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeChatKit);
        } else {
            initializeChatKit();
        }
    </script>
</body>
</html>
```

**Why**:
- Pure vanilla ChatKit web component (NO React)
- Session management in vanilla JS
- Official configuration via setOptions()
- Theme via CSS variables only
- Auto-initializes on page load

---

## 📋 T012: API Client TypeScript

**File**: `frontend/lib/chatkit-api.ts` (NEW)

```typescript
export interface ChatKitSession {
  session_id: string;
  created_at: string;
}

export interface ChatKitMessage {
  session_id: string;
  message: string;
  user_id?: string | null;
  thread_id?: string | null;
}

export interface ChatKitResponse {
  session_id: string;
  message: string;
  type: 'text' | 'item_created' | 'bill_created' | 'item_list' | 'error';
  structured_data?: Record<string, any>;
  timestamp: string;
  error?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_AGENT_API_URL || 'http://localhost:8000/agent';

export async function createChatKitSession(userId?: string | null): Promise<ChatKitSession> {
  const response = await fetch(`${API_BASE}/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId || null }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create session: ${response.statusText}`);
  }

  return response.json();
}

export async function sendChatKitMessage(request: ChatKitMessage): Promise<ChatKitResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  return response.json();
}

export async function streamChatKitMessage(request: ChatKitMessage): Promise<ReadableStream> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to stream message: ${response.statusText}`);
  }

  return response.body!;
}
```

**Why**:
- Typed API calls for ChatKit endpoints
- Session management helpers
- Supports both regular and streaming responses
- Proper error handling

---

## 📋 T013: Session Hook

**File**: `frontend/lib/hooks/useChatKitSession.ts` (NEW)

```typescript
import { useEffect, useState } from 'react';
import { createChatKitSession } from '../chatkit-api';

export function useChatKitSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initializeSession() {
      try {
        // Check sessionStorage first (for page refresh recovery)
        const stored = sessionStorage.getItem('chatkit-session-id');

        if (stored) {
          setSessionId(stored);
          setIsLoading(false);
          return;
        }

        // Create new session
        const session = await createChatKitSession();
        sessionStorage.setItem('chatkit-session-id', session.session_id);
        setSessionId(session.session_id);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setIsLoading(false);
      }
    }

    initializeSession();

    // Cleanup on unmount
    return () => {
      // Session persists until tab closes (per spec)
    };
  }, []);

  return { sessionId, isLoading, error };
}
```

**Why**:
- React hook for session management
- Persists across navigation via sessionStorage
- Recovers session on page refresh
- Typed with proper error handling

---

## 📋 T014: Layout Integration

**File**: `frontend/app/layout.tsx` (UPDATE)

Update root layout to include vanilla ChatKit:

```typescript
import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/shared/Header';
import Navigation from '@/components/shared/Navigation';
import { APP_METADATA } from '@/lib/constants';

export const metadata: Metadata = {
  title: `${APP_METADATA.NAME} - ${APP_METADATA.SUBTITLE}`,
  description: APP_METADATA.DESCRIPTION,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        {/* Import ChatKit web component (vanilla JS) */}
        <script type="module">
          {`import '@openai/chatkit';`}
        </script>
      </head>
      <body className="bg-gray-50">
        <Header />
        <Navigation />
        <main className="container mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="bg-gray-100 border-t border-gray-200 mt-8 py-4">
          <div className="container mx-auto px-4 text-center text-sm text-gray-600">
            <p>{APP_METADATA.NAME} v{APP_METADATA.VERSION}</p>
          </div>
        </footer>

        {/* ChatKit Web Component - Pure vanilla (no React wrapper) */}
        <ChatKitWidgetContainer />
      </body>
    </html>
  );
}

/**
 * ChatKit Widget Container
 * Pure vanilla ChatKit integration - no custom UI
 */
function ChatKitWidgetContainer() {
  return (
    <>
      <style>{`
        #chatkit-container {
          position: fixed;
          bottom: 20px;
          right: 20px;
          z-index: 1000;
        }

        openai-chatkit {
          --ck-accent-color: #3b82f6;
          --ck-background-color: #ffffff;
          --ck-text-color: #1f2937;
          --ck-border-radius: 8px;

          height: 600px;
          width: 400px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
      `}</style>

      <div id="chatkit-container">
        <openai-chatkit id="chat"></openai-chatkit>
      </div>

      <script type="module">{`
        // Initialize ChatKit vanilla JS
        const API_BASE = '${process.env.NEXT_PUBLIC_AGENT_API_URL || 'http://localhost:8000/agent'}';
        const chatkit = document.getElementById('chat');

        let sessionId = sessionStorage.getItem('chatkit-session-id');

        async function createSession() {
          const res = await fetch(API_BASE + '/session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: null })
          });
          const data = await res.json();
          sessionId = data.session_id;
          sessionStorage.setItem('chatkit-session-id', sessionId);
          return sessionId;
        }

        async function init() {
          if (!sessionId) await createSession();

          chatkit.setOptions({
            api: {
              url: API_BASE + '/chat',
              fetch: async (url, opts) => {
                const body = opts.body ? JSON.parse(opts.body) : {};
                body.session_id = sessionId;
                return fetch(url, {
                  ...opts,
                  body: JSON.stringify(body),
                  headers: { ...opts.headers, 'Content-Type': 'application/json' }
                });
              }
            },
            theme: { colorScheme: 'light', accentColor: '#3b82f6' },
            header: { title: 'AI Assistant' },
            startScreen: {
              greeting: 'Hello! How can I help?',
              prompts: [
                { text: 'Add item', prompt: 'Add a new inventory item' },
                { text: 'Create bill', prompt: 'Create a bill' }
              ]
            }
          });
        }

        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', init);
        } else {
          init();
        }
      `}</script>
    </>
  );
}
```

**Why**:
- Integrates vanilla ChatKit into Next.js root layout
- ChatKit appears on all routes (`/admin`, `/pos`, `/agent`)
- Pure vanilla JS (NO React wrappers)
- Session management persists across navigation
- Official ChatKit configuration via setOptions()

---

## 🎯 Summary of Phase 2

| Task | File | Purpose | Status |
|------|------|---------|--------|
| T006 | `backend/app/schemas.py` | ChatKit Pydantic schemas | ✅ **DONE** |
| T007 | `backend/app/services/session_service.py` | Tab-lifetime session manager | 📋 Ready |
| T008 | `backend/app/models/conversation.py` | Conversation history persistence | 📋 Ready |
| T009 | `backend/app/routers/chatkit.py` | `/agent/session` and `/agent/chat` endpoints | 📋 Ready |
| T010 | `backend/app/main.py` | Register ChatKit router in FastAPI | 📋 Ready |
| T011 | `frontend/public/chatkit-embed.html` | Pure vanilla ChatKit web component | 📋 Ready |
| T012 | `frontend/lib/chatkit-api.ts` | TypeScript API client | 📋 Ready |
| T013 | `frontend/lib/hooks/useChatKitSession.ts` | React hook for session management | 📋 Ready |
| T014 | `frontend/app/layout.tsx` | Layout integration with ChatKit | 📋 Ready |

---

## ✅ Checkpoint: Phase 2 Foundation Ready

After completing T007-T014, you will have:

1. ✅ Backend session management with tab-lifetime persistence
2. ✅ PostgreSQL conversation history storage for audit trail
3. ✅ `/agent/session` endpoint for session creation
4. ✅ `/agent/chat` endpoint for ChatKit messages
5. ✅ Pure vanilla ChatKit web component (NO React code)
6. ✅ Session recovery across page navigation
7. ✅ Proper error handling and logging
8. ✅ Official ChatKit styling via CSS variables

**Next Phase**: T015-T022 (User Story 1 MVP - Inventory add via natural language)

---

**Key Design Principles**:
✅ Pure vanilla ChatKit (official web component)
✅ Self-hosted backend (NOT OpenAI Hosted MCP)
✅ Tab-lifetime sessions (expire on page close)
✅ Conversation history persistence
✅ Type-safe Pydantic schemas
✅ Official ChatKit patterns from skill file
