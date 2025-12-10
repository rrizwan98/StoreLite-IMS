"""ChatKit session management for tab-lifetime sessions"""

from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Optional


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
