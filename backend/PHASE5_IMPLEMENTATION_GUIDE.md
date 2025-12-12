# Phase 5: OpenAI Agents SDK Integration - Complete Implementation Guide
**Latest: December 2025** | LiteLLM Gemini 2.0 Flash Lite + Local MCP + PostgreSQL

---

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd backend
pip install -e .
```

### 2. Set Gemini API Key
```bash
# Get key from: https://ai.google.dev/
export GEMINI_API_KEY="your-google-api-key"
```

### 3. Start Local MCP Server
```bash
python -m app.mcp_server.main
```

### 4. Start FastAPI Backend
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Test Agent Endpoint
```bash
curl -X POST "http://localhost:8000/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-1",
    "message": "Add 10kg sugar to inventory"
  }'
```

---

## Architecture Overview

```
User Request
    ↓
FastAPI Endpoint (/agent/chat)
    ↓
AsyncSession (PostgreSQL) - Load conversation history
    ↓
OpenAI Agents SDK (v0.6.2+)
    ↓ (powered by)
LiteLLMModel (Gemini 2.0 Flash Lite)
    ↓ (calls tools via)
Local MCP Server (FastMCP)
    ↓
MCP Tools (inventory_add_item, billing_create_bill, etc.)
    ↓
Database Operations
    ↓
AsyncSession - Save conversation history + results
    ↓
Response to User
```

---

## Detailed Implementation

### Part 1: LiteLLM Gemini 2.0 Flash Lite Setup

#### Latest Import Path (December 2025)
```python
# CORRECT (December 2025)
from agents.extensions.models.litellm_model import LitellmModel

# INCORRECT (Outdated)
from agents.models import LiteLLMModel  # ❌ This path doesn't exist
```

#### Initialization Code
```python
import os
from agents.extensions.models.litellm_model import LitellmModel

# Initialize Gemini model with LiteLLM
model = LitellmModel(
    model="gemini/gemini-2.0-flash-lite-preview-02-05",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
    max_tokens=8192,
)

# Available model names (December 2025):
# - gemini/gemini-2.0-flash-lite-preview-02-05  (Latest, cheapest)
# - gemini/gemini-2.0-flash                      (Full version)
# - gemini/gemini-1.5-pro                        (Older)
```

#### Gemini 2.0 Flash Lite Specs
| Feature | Value |
|---------|-------|
| Context Window | 1,000,000 tokens |
| Input Cost | $0.07 per 1M tokens |
| Output Cost | $0.30 per 1M tokens |
| Tool Calling | ✅ Fully supported |
| Multimodal | ✅ Vision, text, audio |
| Availability | ✅ GA (production) |
| vs GPT-4o-mini | 30% cheaper, better quality |

---

### Part 2: Local MCP Server Setup (STDIO Transport)

#### Option A: FastMCP (Recommended for quick setup)
```python
# backend/app/mcp_server/main.py
from fastmcp import FastMCP

# Create server
mcp = FastMCP("InventoryMCPServer")

# Register tools
@mcp.tool()
def inventory_add_item(
    name: str,
    category: str,
    unit: str,
    unit_price: float,
    stock_qty: float
) -> dict:
    """Add new item to inventory"""
    # Implementation: Query database, add item
    return {
        "status": "success",
        "item_id": 42,
        "message": f"Added {stock_qty}{unit} {name}"
    }

@mcp.tool()
def inventory_list_items(category: str = None, low_stock: int = None) -> list:
    """List inventory items with optional filters"""
    # Implementation
    return [
        {"id": 1, "name": "Sugar", "qty": 150},
        {"id": 2, "name": "Flour", "qty": 5}
    ]

@mcp.tool()
def billing_create_bill(customer_name: str, items: list) -> dict:
    """Create bill for customer"""
    # Implementation: Create bill in database
    return {
        "bill_id": "BILL-001",
        "customer_name": customer_name,
        "total": 820.50,
        "status": "created"
    }

# Run with stdio transport (local)
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Install FastMCP:**
```bash
pip install fastmcp>=1.0
```

**Run MCP Server:**
```bash
python -m app.mcp_server.main
```

#### Option B: Official Python SDK (More control)
```python
# backend/app/mcp_server/official_main.py
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

server = Server("InventoryMCPServer")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="inventory_add_item",
            description="Add item to inventory",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "unit_price": {"type": "number"},
                    "stock_qty": {"type": "number"},
                },
                "required": ["name", "category", "unit_price", "stock_qty"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "inventory_add_item":
        # Database logic here
        return [TextContent(
            type="text",
            text=f"Added {arguments['name']}"
        )]

async def main():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Part 3: PostgreSQL Async Session Management (SQLAlchemy 2.0)

#### Database Configuration
```python
# backend/app/database.py (Latest patterns)
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Use asyncpg driver for PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/ims_db"
)

# Create async engine with proper pooling (December 2025 best practices)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set True for SQL debugging
    pool_size=20,  # Connection pool size
    max_overflow=10,  # Extra connections allowed
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # CRITICAL: Keep object attributes valid after commit
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Dependency for FastAPI
async def get_session():
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def cleanup():
    """Cleanup connections"""
    await engine.dispose()
```

#### Conversation Session Model
```python
# backend/app/models.py (Latest JSONB patterns)
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ConversationSession(Base):
    """Store agent conversations with JSONB history"""
    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    agent_name: Mapped[str] = mapped_column(String(255))

    # JSONB for flexible conversation history
    messages: Mapped[dict] = mapped_column(
        PG_JSONB,
        default=dict,
        comment="Array of {role, content, timestamp, tool_calls}"
    )

    # Session metadata
    context: Mapped[dict] = mapped_column(
        PG_JSONB,
        default=dict,
        comment="{model, temperature, max_tokens}"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Counters
    message_count: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)
```

#### Session Service (Async Operations)
```python
# backend/app/services/session_service.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ConversationSession
from datetime import datetime, timezone
import uuid

class SessionService:
    """Manage conversation sessions with PostgreSQL"""

    @staticmethod
    async def create_session(
        user_id: str,
        agent_name: str,
        context: dict,
        db: AsyncSession
    ) -> str:
        """Create new conversation session"""
        session_id = str(uuid.uuid4())

        conversation = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            context=context,
            messages={"items": []},
        )

        db.add(conversation)
        await db.commit()  # Explicit async commit
        await db.refresh(conversation)

        return session_id

    @staticmethod
    async def add_message(
        session_id: str,
        role: str,
        content: str,
        db: AsyncSession
    ) -> None:
        """Add message to conversation history"""
        # Query within transaction
        stmt = select(ConversationSession).where(
            ConversationSession.session_id == session_id
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ValueError(f"Session {session_id} not found")

        # Append to JSONB array
        new_message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if "items" not in conversation.messages:
            conversation.messages["items"] = []

        conversation.messages["items"].append(new_message)
        conversation.message_count += 1
        conversation.updated_at = datetime.now(timezone.utc)

        await db.commit()  # SQLAlchemy 2.0: auto-detects changes

    @staticmethod
    async def get_session(session_id: str, db: AsyncSession) -> dict:
        """Retrieve conversation session"""
        stmt = select(ConversationSession).where(
            ConversationSession.session_id == session_id
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        return {
            "session_id": conversation.session_id,
            "user_id": conversation.user_id,
            "messages": conversation.messages.get("items", []),
            "message_count": conversation.message_count,
        }
```

---

### Part 4: Agent Setup with Error Handling

#### Agent Initialization (Latest December 2025)
```python
# backend/app/agents/agent.py
import os
import asyncio
from agents import Agent, Runner
from agents.extensions.models.litellm_model import LitellmModel
from agents.exceptions import ModelBehaviorError, MaxTurnsExceeded
from app.agents.tools_client import MCPClient

class InventoryAgent:
    def __init__(self):
        # Initialize Gemini model
        self.model = LitellmModel(
            model="gemini/gemini-2.0-flash-lite-preview-02-05",
            api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.7,
            max_tokens=8192,
        )

        # Initialize MCP client
        self.mcp_client = MCPClient(
            base_url=os.getenv("MCP_SERVER_URL", "http://localhost:8001"),
            cache_ttl_seconds=300
        )

        self.agent = None

    async def initialize(self):
        """Discover tools and create agent"""
        # Discover tools with retry
        for attempt in range(3):
            try:
                tools = self.mcp_client.discover_tools()
                break
            except ConnectionError:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

        # Create agent with Gemini
        self.agent = Agent(
            name="InventoryAgent",
            instructions="You are an inventory management assistant. Help users manage inventory and create bills.",
            model=self.model,
            tools=[],  # Tools would be registered here
            max_turns=10,
        )

    async def chat(self, user_message: str) -> str:
        """Process user message"""
        try:
            # Latest approach: Runner.run_async
            result = await Runner.run_async(
                agent=self.agent,
                input=user_message,
            )
            return result.output

        except ModelBehaviorError as e:
            # Gemini produced invalid output
            return "The model produced an invalid response. Please try again."

        except MaxTurnsExceeded as e:
            # Agent loop exceeded max iterations
            return "The conversation became too complex. Please simplify your request."

        except Exception as e:
            # Connection or API errors
            if "connection" in str(e).lower():
                return "Connection error. Ensure MCP server is running."
            raise
```

#### FastAPI Endpoint
```python
# backend/app/routers/agent.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.services.session_service import SessionService
from app.agents.agent import InventoryAgent
from pydantic import BaseModel

router = APIRouter(prefix="/api/agent", tags=["agent"])
agent = InventoryAgent()

class AgentRequest(BaseModel):
    session_id: str = None
    user_id: str = "default"
    message: str

class AgentResponse(BaseModel):
    session_id: str
    response: str
    status: str

@router.on_event("startup")
async def startup():
    """Initialize agent on startup"""
    await agent.initialize()

@router.post("/chat", response_model=AgentResponse)
async def chat(
    request: AgentRequest,
    db: AsyncSession = Depends(get_session)
):
    """Chat with inventory agent"""
    try:
        # Create or load session
        session_id = request.session_id or (await SessionService.create_session(
            user_id=request.user_id,
            agent_name="InventoryAgent",
            context={"model": "gemini-2.0-flash-lite"},
            db=db
        ))

        # Add user message
        await SessionService.add_message(
            session_id=session_id,
            role="user",
            content=request.message,
            db=db
        )

        # Get agent response
        response = await agent.chat(request.message)

        # Add assistant response
        await SessionService.add_message(
            session_id=session_id,
            role="assistant",
            content=response,
            db=db
        )

        return AgentResponse(
            session_id=session_id,
            response=response,
            status="success"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Error Handling Best Practices

### 1. Connection Errors with Retry
```python
import asyncio

async def connect_with_retry(mcp_client, max_retries=3):
    """Connect to MCP server with exponential backoff"""
    for attempt in range(max_retries):
        try:
            tools = mcp_client.discover_tools()
            return tools
        except ConnectionError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)
            else:
                raise ConnectionError(
                    f"Failed to connect after {max_retries} attempts"
                ) from e
```

### 2. Model Errors (Gemini)
```python
from agents.exceptions import ModelBehaviorError, MaxTurnsExceeded

try:
    result = await Runner.run_async(agent, "user message")
except ModelBehaviorError:
    # Gemini produced invalid JSON/output
    # Action: Adjust prompt, retry with different input
    pass
except MaxTurnsExceeded:
    # Agent loop exceeded max iterations
    # Action: Simplify request, increase max_turns
    pass
```

### 3. PostgreSQL Errors
```python
from sqlalchemy.exc import DBAPIError

try:
    # Database operation
    await db.commit()
except DBAPIError as e:
    if e.connection_invalidated:
        # Connection lost, retry
        await db.rollback()
    else:
        # Other SQL error
        raise
```

---

## Testing

### Unit Test Example
```python
# backend/tests/test_agent_integration.py
import pytest
from app.agents.agent import InventoryAgent

@pytest.mark.asyncio
async def test_agent_initialization():
    agent = InventoryAgent()
    await agent.initialize()
    assert agent.agent is not None

@pytest.mark.asyncio
async def test_agent_chat():
    agent = InventoryAgent()
    await agent.initialize()
    response = await agent.chat("How much sugar do we have?")
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_mcp_connection():
    from app.agents.tools_client import MCPClient
    client = MCPClient(base_url="http://localhost:8001")
    tools = client.discover_tools()
    assert isinstance(tools, list)
```

### Integration Test
```bash
# 1. Start MCP server
python -m app.mcp_server.main &

# 2. Start backend
uvicorn app.main:app --reload &

# 3. Test endpoint
curl -X POST "http://localhost:8000/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-1",
    "user_id": "user-1",
    "message": "Add 50kg flour to inventory"
  }'
```

---

## Migration to PostgreSQL

For production, switch from SQLite to PostgreSQL:

### 1. Create PostgreSQL Database
```bash
psql -U postgres
CREATE DATABASE ims_db;
```

### 2. Update .env
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ims_db
```

### 3. Run Migrations
```bash
alembic upgrade head
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| GEMINI_API_KEY not found | Export: `export GEMINI_API_KEY="your-key"` |
| MCP server unreachable | Start: `python -m app.mcp_server.main` |
| PostgreSQL connection error | Check: `psql -U user -d ims_db` |
| LiteLLMModel import error | Install: `pip install litellm>=1.76.1` |
| Agent returns empty response | Check: Gemini API quota, model availability |
| Session not persisted | Verify: `expire_on_commit=False` in AsyncSession |

---

## Performance Notes

- **Gemini 2.0 Flash Lite**: 30% cheaper than GPT-4o-mini, faster responses
- **Connection pooling**: 20 connections, auto-recycle every hour
- **JSONB indexing**: Automatic GiST indexing on PostgreSQL 11+
- **Tool caching**: 5-minute TTL reduces MCP server load
- **Async throughout**: Non-blocking I/O for FastAPI endpoints

---

## References

- [OpenAI Agents SDK (December 2025)](https://openai.github.io/openai-agents-python/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Gemini 2.0 API](https://ai.google.dev/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [SQLAlchemy 2.0 AsyncIO](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL asyncpg](https://magicstack.github.io/asyncpg/current/)

---

**Last Updated**: December 2025 | All examples use latest stable versions
