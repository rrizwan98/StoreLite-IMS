# Session Management with PostgreSQL

Patterns for persistent conversation history and session management.

## Database Schema

```sql
-- sessions/schema.sql
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'tool'
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_call_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON agent_sessions(user_id);
CREATE INDEX idx_messages_session_id ON conversation_messages(session_id);
CREATE INDEX idx_messages_created_at ON conversation_messages(created_at);
```

## PostgreSQL Session Store

```python
# sessions/postgres_store.py
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import asyncpg


@dataclass
class Message:
    role: str
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


@dataclass
class Session:
    id: UUID
    user_id: str
    agent_name: str
    messages: list[Message]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PostgresSessionStore:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        """Initialize connection pool."""
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
        )

    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def create_session(
        self,
        user_id: str,
        agent_name: str,
        metadata: dict | None = None,
    ) -> Session:
        """Create a new session."""
        session_id = uuid4()
        now = datetime.utcnow()
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_sessions (id, user_id, agent_name, metadata, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                session_id,
                user_id,
                agent_name,
                json.dumps(metadata or {}),
                now,
                now,
            )
        
        return Session(
            id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            messages=[],
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )

    async def get_session(self, session_id: UUID) -> Session | None:
        """Get session with all messages."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_sessions WHERE id = $1",
                session_id,
            )
            if not row:
                return None
            
            message_rows = await conn.fetch(
                """
                SELECT * FROM conversation_messages 
                WHERE session_id = $1 
                ORDER BY created_at ASC
                """,
                session_id,
            )
        
        messages = [
            Message(
                role=msg["role"],
                content=msg["content"],
                tool_calls=json.loads(msg["tool_calls"]) if msg["tool_calls"] else None,
                tool_call_id=msg["tool_call_id"],
            )
            for msg in message_rows
        ]
        
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            agent_name=row["agent_name"],
            messages=messages,
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> None:
        """Add a message to a session."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_messages 
                (session_id, role, content, tool_calls, tool_call_id)
                VALUES ($1, $2, $3, $4, $5)
                """,
                session_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls else None,
                tool_call_id,
            )
            
            await conn.execute(
                "UPDATE agent_sessions SET updated_at = NOW() WHERE id = $1",
                session_id,
            )

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 10,
    ) -> list[Session]:
        """Get recent sessions for a user."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM agent_sessions 
                WHERE user_id = $1 
                ORDER BY updated_at DESC 
                LIMIT $2
                """,
                user_id,
                limit,
            )
        
        sessions = []
        for row in rows:
            session = await self.get_session(row["id"])
            if session:
                sessions.append(session)
        
        return sessions

    async def delete_session(self, session_id: UUID) -> None:
        """Delete a session and its messages."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM agent_sessions WHERE id = $1",
                session_id,
            )
```

## Integration with Agent

```python
# agents/session_agent.py
import os
from uuid import UUID
from agents import Agent, Runner
from sessions.postgres_store import PostgresSessionStore, Message


class SessionAgent:
    def __init__(
        self,
        agent: Agent,
        store: PostgresSessionStore,
    ):
        self.agent = agent
        self.store = store

    async def run(
        self,
        user_input: str,
        session_id: UUID | None = None,
        user_id: str = "default",
    ) -> str:
        """Run agent with session context."""
        
        # Get or create session
        if session_id:
            session = await self.store.get_session(session_id)
        else:
            session = await self.store.create_session(
                user_id=user_id,
                agent_name=self.agent.name,
            )
        
        # Build message history for context
        history = self._build_history(session.messages)
        
        # Add current user message
        await self.store.add_message(
            session_id=session.id,
            role="user",
            content=user_input,
        )
        
        # Run agent with history
        result = await Runner.run(
            self.agent,
            user_input,
            context={"history": history},
        )
        
        # Save assistant response
        await self.store.add_message(
            session_id=session.id,
            role="assistant",
            content=result.final_output,
        )
        
        return result.final_output

    def _build_history(self, messages: list[Message]) -> list[dict]:
        """Convert stored messages to agent format."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]


# Usage
async def main():
    database_url = os.environ["DATABASE_URL"]
    
    async with PostgresSessionStore(database_url) as store:
        agent = Agent(
            name="MemoryAgent",
            instructions="Help users and remember past conversations.",
        )
        
        session_agent = SessionAgent(agent, store)
        
        # Start new conversation
        response1 = await session_agent.run(
            "My name is Alice",
            user_id="user_123",
        )
        print(response1)
        
        # Continue in same session
        response2 = await session_agent.run(
            "What's my name?",
            session_id=session_agent.current_session_id,
            user_id="user_123",
        )
        print(response2)  # Should remember "Alice"
```

## Built-in SDK Session Support

The OpenAI Agents SDK also has built-in session support:

```python
from agents import Agent, Runner

agent = Agent(
    name="SessionAgent",
    instructions="Help users and maintain context.",
)

# First interaction
result1 = await Runner.run(agent, "My favorite color is blue")

# Continue with context using to_input_list()
result2 = await Runner.run(
    agent,
    "What's my favorite color?",
    input_filter=lambda msgs: result1.to_input_list() + msgs,
)
```

## Session Cleanup

```python
# sessions/cleanup.py
import asyncio
from datetime import datetime, timedelta
from sessions.postgres_store import PostgresSessionStore


async def cleanup_old_sessions(
    store: PostgresSessionStore,
    days_old: int = 30,
) -> int:
    """Delete sessions older than specified days."""
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    
    async with store._pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM agent_sessions WHERE updated_at < $1",
            cutoff,
        )
    
    # Parse count from result string like "DELETE 5"
    count = int(result.split()[-1])
    return count


# Run as cron job
async def main():
    async with PostgresSessionStore(os.environ["DATABASE_URL"]) as store:
        deleted = await cleanup_old_sessions(store, days_old=30)
        print(f"Cleaned up {deleted} old sessions")
```

## Best Practices

1. **Connection pooling** - Use `asyncpg` pool for efficient connections
2. **Indexes** - Index `user_id` and `session_id` for fast lookups
3. **Cleanup jobs** - Regularly delete old sessions to manage storage
4. **Metadata** - Store additional context in the `metadata` JSONB field
5. **Message limits** - Consider truncating very long conversations
6. **Error handling** - Handle database connection failures gracefully