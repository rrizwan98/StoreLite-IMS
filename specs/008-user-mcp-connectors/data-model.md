# Data Model: User MCP Connectors

**Feature**: 008-user-mcp-connectors | **Date**: 2025-12-21 | **Version**: 1.0

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA MODEL                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐         ┌───────────────────┐                            │
│   │    User      │────────<│  UserToolStatus   │                            │
│   │              │   1:N   │                   │                            │
│   │  id          │         │  user_id (FK)     │                            │
│   │  email       │         │  tool_id          │                            │
│   │  ...         │         │  is_connected     │                            │
│   └──────┬───────┘         │  config (JSONB)   │                            │
│          │                 └───────────────────┘                            │
│          │                                                                   │
│          │ 1:N             ┌───────────────────────┐                        │
│          └────────────────<│  UserMCPConnection    │                        │
│                            │                       │                        │
│                            │  id                   │                        │
│                            │  user_id (FK)         │                        │
│                            │  name                 │                        │
│                            │  description          │                        │
│                            │  server_url           │                        │
│                            │  auth_type            │                        │
│                            │  auth_config (enc)    │                        │
│                            │  is_active            │                        │
│                            │  is_verified          │                        │
│                            │  discovered_tools     │                        │
│                            └───────────────────────┘                        │
│                                                                              │
│   ┌───────────────────────────────────────────────────────────────┐         │
│   │  SystemTool (Code-based Registry - NOT a database table)     │         │
│   │                                                               │         │
│   │  id: str          # 'gmail', 'analytics', etc.               │         │
│   │  name: str        # Display name                              │         │
│   │  description: str # What it does                              │         │
│   │  icon: str        # Icon identifier                           │         │
│   │  category: str    # 'communication', 'insights', etc.        │         │
│   │  auth_type: str   # 'none', 'oauth'                          │         │
│   │  is_enabled: bool # Available for use                         │         │
│   │  is_beta: bool    # Coming soon flag                          │         │
│   └───────────────────────────────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Definitions

### 1. UserToolStatus

Tracks each user's connection status for **system tools** (Gmail, Analytics, etc.).

```sql
CREATE TABLE user_tool_status (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_id VARCHAR(50) NOT NULL,  -- 'gmail', 'analytics', 'export'
    is_connected BOOLEAN DEFAULT FALSE,
    config JSONB,  -- Tool-specific configuration
    connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT uq_user_tool UNIQUE (user_id, tool_id)
);

CREATE INDEX idx_user_tool_status_user ON user_tool_status(user_id);
CREATE INDEX idx_user_tool_status_tool ON user_tool_status(tool_id);
```

**Column Details**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Auto-increment ID |
| `user_id` | INTEGER | FK, NOT NULL | Reference to users table |
| `tool_id` | VARCHAR(50) | NOT NULL | System tool identifier (e.g., 'gmail') |
| `is_connected` | BOOLEAN | DEFAULT FALSE | Whether user has connected this tool |
| `config` | JSONB | NULLABLE | Tool-specific settings (e.g., default recipient) |
| `connected_at` | TIMESTAMP | NULLABLE | When the tool was connected |
| `created_at` | TIMESTAMP | NOT NULL | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL | Last update time |

**Example Data**:
```json
{
  "id": 1,
  "user_id": 42,
  "tool_id": "gmail",
  "is_connected": true,
  "config": {
    "default_recipient": "reports@company.com"
  },
  "connected_at": "2025-12-21T10:30:00Z"
}
```

---

### 2. UserMCPConnection

Stores user's **custom MCP server connections** (user connectors).

```sql
CREATE TABLE user_mcp_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    server_url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(50) DEFAULT 'none' NOT NULL,
    auth_config TEXT,  -- Encrypted JSON (Fernet)
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    discovered_tools JSONB,  -- Cached list of tools
    last_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT auth_type_check CHECK (auth_type IN ('none', 'oauth', 'api_key'))
);

CREATE INDEX idx_user_mcp_connections_user ON user_mcp_connections(user_id);
CREATE INDEX idx_user_mcp_connections_active ON user_mcp_connections(user_id, is_active);
```

**Column Details**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK | Auto-increment ID |
| `user_id` | INTEGER | FK, NOT NULL | Reference to users table |
| `name` | VARCHAR(255) | NOT NULL | User-defined connector name |
| `description` | TEXT | NULLABLE | Optional description |
| `server_url` | VARCHAR(500) | NOT NULL | MCP server URL (HTTP/HTTPS) |
| `auth_type` | VARCHAR(50) | NOT NULL, CHECK | 'none', 'oauth', or 'api_key' |
| `auth_config` | TEXT | NULLABLE | **Encrypted** JSON with credentials |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Enabled/disabled state |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT FALSE | Connection validated |
| `discovered_tools` | JSONB | NULLABLE | Cached tools from server |
| `last_verified_at` | TIMESTAMP | NULLABLE | Last successful verification |
| `created_at` | TIMESTAMP | NOT NULL | Record creation time |
| `updated_at` | TIMESTAMP | NOT NULL | Last update time |

**Example Data**:
```json
{
  "id": 5,
  "user_id": 42,
  "name": "My Slack Bot",
  "description": "Slack integration for notifications",
  "server_url": "https://my-slack-mcp.example.com",
  "auth_type": "oauth",
  "auth_config": "gAAAAABn... (encrypted)",
  "is_active": true,
  "is_verified": true,
  "discovered_tools": [
    {
      "name": "send_message",
      "description": "Send a message to a Slack channel",
      "inputSchema": {
        "type": "object",
        "properties": {
          "channel": {"type": "string"},
          "message": {"type": "string"}
        },
        "required": ["channel", "message"]
      }
    },
    {
      "name": "list_channels",
      "description": "List available Slack channels",
      "inputSchema": {
        "type": "object",
        "properties": {}
      }
    }
  ],
  "last_verified_at": "2025-12-21T10:30:00Z"
}
```

---

## SQLAlchemy Models

### UserToolStatus Model

```python
# backend/app/models.py

class UserToolStatus(Base):
    """
    Track user's connection status for system tools.
    Each user can have one entry per system tool.
    """
    __tablename__ = "user_tool_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tool_id = Column(String(50), nullable=False, index=True)
    is_connected = Column(Boolean, default=False, nullable=False)
    config = Column(JSONB, nullable=True)
    connected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'tool_id', name='uq_user_tool'),
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="tool_statuses")

    def __repr__(self):
        return f"<UserToolStatus(user_id={self.user_id}, tool={self.tool_id}, connected={self.is_connected})>"
```

### UserMCPConnection Model

```python
# backend/app/models.py

class UserMCPConnection(Base):
    """
    User's custom MCP server connection.
    Stores connection details with encrypted credentials.
    """
    __tablename__ = "user_mcp_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    server_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="none", nullable=False)
    auth_config = Column(Text, nullable=True)  # Encrypted JSON
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    discovered_tools = Column(JSONB, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "auth_type IN ('none', 'oauth', 'api_key')",
            name="auth_type_check"
        ),
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="mcp_connections")

    def __repr__(self):
        return f"<UserMCPConnection(id={self.id}, name={self.name}, active={self.is_active})>"
```

---

## Pydantic Schemas

### Request/Response Schemas

```python
# backend/app/schemas.py (additions)

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class AuthType(str, Enum):
    NONE = "none"
    OAUTH = "oauth"
    API_KEY = "api_key"


# ============================================================================
# System Tools Schemas
# ============================================================================

class SystemToolResponse(BaseModel):
    """System tool with user's connection status"""
    id: str
    name: str
    description: str
    icon: str
    category: str
    auth_type: str
    is_enabled: bool
    is_beta: bool
    is_connected: bool = False  # User-specific
    config: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ToolConnectRequest(BaseModel):
    """Request to connect to a system tool"""
    config: Optional[Dict[str, Any]] = None


# ============================================================================
# User Connector Schemas
# ============================================================================

class DiscoveredTool(BaseModel):
    """Tool discovered from MCP server"""
    name: str
    description: Optional[str] = None
    inputSchema: Optional[Dict[str, Any]] = None


class ConnectorCreateRequest(BaseModel):
    """Request to create a new connector"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    server_url: HttpUrl
    auth_type: AuthType = AuthType.NONE
    auth_config: Optional[Dict[str, Any]] = None


class ConnectorUpdateRequest(BaseModel):
    """Request to update a connector"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class ConnectorTestRequest(BaseModel):
    """Request to test a connector before saving"""
    server_url: HttpUrl
    auth_type: AuthType = AuthType.NONE
    auth_config: Optional[Dict[str, Any]] = None


class ConnectorTestResponse(BaseModel):
    """Response from connection test"""
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    tools: Optional[List[DiscoveredTool]] = None


class ConnectorResponse(BaseModel):
    """Full connector response"""
    id: int
    name: str
    description: Optional[str]
    server_url: str
    auth_type: str
    is_active: bool
    is_verified: bool
    discovered_tools: Optional[List[DiscoveredTool]] = None
    tool_count: int = 0
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConnectorListResponse(BaseModel):
    """List of user's connectors"""
    connectors: List[ConnectorResponse]
    total: int


# ============================================================================
# Combined Tools Response (for Apps Menu)
# ============================================================================

class AppsTool(BaseModel):
    """Tool for Apps menu display"""
    id: str
    name: str
    description: Optional[str]
    type: str  # 'system' or 'connector'
    connector_id: Optional[int] = None  # For connector tools
    connector_name: Optional[str] = None
    is_connected: bool
    icon: Optional[str] = None


class AppsMenuResponse(BaseModel):
    """Response for Apps menu with all available tools"""
    system_tools: List[SystemToolResponse]
    user_connectors: List[ConnectorResponse]
```

---

## Data Constraints

### Business Rules

| Constraint | Rule | Enforcement |
|------------|------|-------------|
| Max connectors per user | 10 | Application-level check |
| Unique tool per user | 1 entry per (user_id, tool_id) | Database UNIQUE constraint |
| Valid auth types | 'none', 'oauth', 'api_key' | Database CHECK constraint |
| URL format | Must be valid HTTP/HTTPS | Pydantic HttpUrl validation |
| Name length | 1-255 characters | Pydantic Field validation |
| Verified before save | is_verified must be true | Application-level check |

### Encryption Rules

| Field | Encrypted | Key Source |
|-------|-----------|------------|
| `auth_config` | Yes (Fernet) | `TOKEN_ENCRYPTION_KEY` env var |
| `server_url` | No | - |
| `discovered_tools` | No | - |

---

## Migration Script

```python
# backend/alembic/versions/xxx_add_user_mcp_connectors.py

"""Add User MCP Connectors tables

Revision ID: xxx
Revises: previous_revision
Create Date: 2025-12-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxx_user_mcp_connectors'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_tool_status table
    op.create_table(
        'user_tool_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tool_id', sa.String(50), nullable=False),
        sa.Column('is_connected', sa.Boolean(), nullable=False, default=False),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('connected_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tool_id', name='uq_user_tool')
    )
    op.create_index('idx_user_tool_status_user', 'user_tool_status', ['user_id'])
    op.create_index('idx_user_tool_status_tool', 'user_tool_status', ['tool_id'])

    # Create user_mcp_connections table
    op.create_table(
        'user_mcp_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('server_url', sa.String(500), nullable=False),
        sa.Column('auth_type', sa.String(50), nullable=False, default='none'),
        sa.Column('auth_config', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('discovered_tools', postgresql.JSONB(), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "auth_type IN ('none', 'oauth', 'api_key')",
            name='auth_type_check'
        )
    )
    op.create_index('idx_user_mcp_connections_user', 'user_mcp_connections', ['user_id'])
    op.create_index(
        'idx_user_mcp_connections_active',
        'user_mcp_connections',
        ['user_id', 'is_active']
    )


def downgrade():
    op.drop_table('user_mcp_connections')
    op.drop_table('user_tool_status')
```

---

## Query Patterns

### Common Queries

```python
# Get all system tools with user's status
async def get_system_tools_with_status(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(UserToolStatus).where(UserToolStatus.user_id == user_id)
    )
    statuses = {s.tool_id: s for s in result.scalars().all()}

    tools = []
    for tool in get_system_tools():
        status = statuses.get(tool.id)
        tools.append({
            **asdict(tool),
            "is_connected": status.is_connected if status else False,
            "config": status.config if status else None
        })
    return tools


# Get user's active connectors with tool count
async def get_active_connectors(user_id: int, session: AsyncSession):
    result = await session.execute(
        select(UserMCPConnection)
        .where(
            UserMCPConnection.user_id == user_id,
            UserMCPConnection.is_active == True
        )
        .order_by(UserMCPConnection.name)
    )
    return result.scalars().all()


# Count user's connectors (for limit check)
async def count_user_connectors(user_id: int, session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(UserMCPConnection.id))
        .where(UserMCPConnection.user_id == user_id)
    )
    return result.scalar() or 0
```
