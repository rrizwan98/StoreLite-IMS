# Developer Tools - Data Model

**Version:** 1.0.0
**Created:** 2025-01-13

---

## 1. Overview

This document defines the database schema for the Developer Tools feature. All models are **additive** - no changes to existing tables.

---

## 2. Entity Relationship Diagram

```
┌─────────────────┐          ┌──────────────────────────┐
│     users       │          │  published_agent_configs │
│  (EXISTING)     │          │  (NEW)                   │
├─────────────────┤          ├──────────────────────────┤
│ id (PK)         │──1────M──│ user_id (FK)             │
│ email           │          │ id (PK, UUID)            │
│ ...             │          │ api_key_hash             │
└─────────────────┘          │ api_key_prefix           │
                             │ name                     │
                             │ allowed_tables           │
                             │ access_mode              │
                             │ allowed_domains          │
                             │ rate_limit_per_minute    │
                             │ custom_instructions      │
                             │ is_active                │
                             │ created_at               │
                             │ expires_at               │
                             └──────────┬───────────────┘
                                        │
                                        │ 1
                                        │
                                        │ M
                             ┌──────────┴───────────────┐
                             │  published_agent_usage   │
                             │  (NEW)                   │
                             ├──────────────────────────┤
                             │ id (PK)                  │
                             │ published_agent_id (FK)  │
                             │ date                     │
                             │ query_count              │
                             │ successful_count         │
                             │ failed_count             │
                             │ total_tokens             │
                             │ avg_response_time_ms     │
                             └──────────────────────────┘

┌─────────────────────┐
│  user_connections   │
│  (EXISTING)         │
├─────────────────────┤
│ user_id (FK)        │  ← Owner's database_uri and schema_metadata
│ database_uri        │    used by PublishedAgentConfig
│ schema_metadata     │
│ ...                 │
└─────────────────────┘
```

---

## 3. New Tables

### 3.1 published_agent_configs

Stores configuration for each published agent created by an organization.

```sql
CREATE TABLE published_agent_configs (
    -- Primary Key
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Owner (Organization)
    user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- API Key (Security)
    api_key_hash            VARCHAR(64) NOT NULL,      -- SHA-256 hash of full key
    api_key_prefix          VARCHAR(20) NOT NULL,      -- "pa_live_abc1..." for display

    -- Agent Configuration
    name                    VARCHAR(255) NOT NULL,      -- Human-friendly name
    description             TEXT,                       -- Optional description

    -- Access Control
    allowed_tables          JSONB NOT NULL DEFAULT '[]',  -- ["products", "orders"]
    access_mode             VARCHAR(20) NOT NULL DEFAULT 'read_only',  -- read_only | read_write
    allowed_domains         JSONB NOT NULL DEFAULT '["*"]',  -- CORS whitelist

    -- Rate Limiting
    rate_limit_per_minute   INTEGER NOT NULL DEFAULT 60,

    -- Customization
    custom_instructions     TEXT,                       -- Additional prompt text

    -- Future: Tool Access (Phase 2)
    allowed_tools           JSONB DEFAULT '[]',         -- ["database"] for now, future: ["gmail", "analytics"]
    tool_configs            JSONB DEFAULT '{}',         -- Tool-specific settings

    -- Status
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at              TIMESTAMP WITH TIME ZONE,   -- NULL = never expires

    -- Usage Stats (Denormalized for quick access)
    total_queries           INTEGER NOT NULL DEFAULT 0,
    last_used_at            TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT access_mode_check CHECK (access_mode IN ('read_only', 'read_write'))
);

-- Indexes
CREATE INDEX idx_published_agent_configs_user_id ON published_agent_configs(user_id);
CREATE UNIQUE INDEX idx_published_agent_configs_api_key_hash ON published_agent_configs(api_key_hash);
CREATE INDEX idx_published_agent_configs_is_active ON published_agent_configs(is_active) WHERE is_active = TRUE;
```

### 3.2 published_agent_usage

Daily usage statistics for each published agent.

```sql
CREATE TABLE published_agent_usage (
    -- Primary Key
    id                      SERIAL PRIMARY KEY,

    -- Foreign Key
    published_agent_id      UUID NOT NULL REFERENCES published_agent_configs(id) ON DELETE CASCADE,

    -- Date (Partitioning key)
    date                    DATE NOT NULL,

    -- Counters
    query_count             INTEGER NOT NULL DEFAULT 0,
    successful_count        INTEGER NOT NULL DEFAULT 0,
    failed_count            INTEGER NOT NULL DEFAULT 0,

    -- Performance Metrics
    total_tokens            INTEGER NOT NULL DEFAULT 0,
    total_response_time_ms  BIGINT NOT NULL DEFAULT 0,

    -- Timestamps
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Unique constraint (one row per agent per day)
    CONSTRAINT unique_agent_date UNIQUE (published_agent_id, date)
);

-- Indexes
CREATE INDEX idx_published_agent_usage_agent_id ON published_agent_usage(published_agent_id);
CREATE INDEX idx_published_agent_usage_date ON published_agent_usage(date);
```

### 3.3 published_agent_query_logs (Optional - For Debugging)

Individual query logs for detailed analysis (optional, can be enabled/disabled).

```sql
CREATE TABLE published_agent_query_logs (
    -- Primary Key
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    published_agent_id      UUID NOT NULL REFERENCES published_agent_configs(id) ON DELETE CASCADE,

    -- Request Info
    thread_id               VARCHAR(64),                -- Conversation thread
    origin_domain           VARCHAR(255),               -- Request origin
    user_agent              VARCHAR(500),               -- Client user agent

    -- Query Details
    query_text              TEXT NOT NULL,              -- User's question
    response_text           TEXT,                       -- Agent's response (truncated)

    -- Performance
    response_time_ms        INTEGER,
    tokens_used             INTEGER,

    -- Status
    status                  VARCHAR(20) NOT NULL,       -- success | error | rate_limited
    error_message           TEXT,

    -- Timestamps
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Auto-expire (for GDPR compliance)
    expires_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '30 days'
);

-- Indexes
CREATE INDEX idx_query_logs_agent_id ON published_agent_query_logs(published_agent_id);
CREATE INDEX idx_query_logs_created_at ON published_agent_query_logs(created_at);
CREATE INDEX idx_query_logs_thread_id ON published_agent_query_logs(thread_id);

-- Auto-cleanup job (run daily)
-- DELETE FROM published_agent_query_logs WHERE expires_at < NOW();
```

---

## 4. SQLAlchemy Models

### 4.1 PublishedAgentConfig

```python
# backend/app/models/published_agent.py

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime,
    Text, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base, PortableJSON


class PublishedAgentConfig(Base):
    """
    Configuration for a published/shared agent.

    Organizations create these to allow external users
    to access their Schema Agent with restricted permissions.
    """
    __tablename__ = "published_agent_configs"

    # Primary Key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier (UUID)"
    )

    # Owner (Organization)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner organization's user ID"
    )

    # API Key (Security)
    api_key_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of the API key"
    )
    api_key_prefix = Column(
        String(20),
        nullable=False,
        comment="Prefix for display (e.g., 'pa_live_abc1...')"
    )

    # Agent Configuration
    name = Column(
        String(255),
        nullable=False,
        comment="Human-friendly agent name"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Optional description"
    )

    # Access Control
    allowed_tables = Column(
        PortableJSON,
        nullable=False,
        default=list,
        comment="List of allowed table names"
    )
    access_mode = Column(
        String(20),
        nullable=False,
        default="read_only",
        comment="'read_only' or 'read_write'"
    )
    allowed_domains = Column(
        PortableJSON,
        nullable=False,
        default=lambda: ["*"],
        comment="CORS whitelist domains"
    )

    # Rate Limiting
    rate_limit_per_minute = Column(
        Integer,
        nullable=False,
        default=60,
        comment="Max requests per minute"
    )

    # Customization
    custom_instructions = Column(
        Text,
        nullable=True,
        comment="Additional prompt instructions"
    )

    # Future: Tool Access (Phase 2)
    allowed_tools = Column(
        PortableJSON,
        default=lambda: ["database"],
        comment="Allowed tools: ['database', 'gmail', 'analytics']"
    )
    tool_configs = Column(
        PortableJSON,
        default=dict,
        comment="Tool-specific configurations"
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether agent is active"
    )

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last update timestamp"
    )
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Expiration timestamp (NULL = never)"
    )

    # Usage Stats (Denormalized)
    total_queries = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total query count"
    )
    last_used_at = Column(
        DateTime,
        nullable=True,
        comment="Last query timestamp"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "access_mode IN ('read_only', 'read_write')",
            name="published_agent_access_mode_check"
        ),
        {"extend_existing": True},
    )

    # Relationships
    user = relationship("User", backref="published_agents")
    usage_records = relationship(
        "PublishedAgentUsage",
        back_populates="agent",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<PublishedAgentConfig(id={self.id}, name={self.name}, owner={self.user_id})>"


class PublishedAgentUsage(Base):
    """
    Daily usage statistics for a published agent.

    One row per agent per day for efficient aggregation.
    """
    __tablename__ = "published_agent_usage"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign Key
    published_agent_id = Column(
        String(36),
        ForeignKey("published_agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to published agent"
    )

    # Date
    date = Column(
        DateTime,
        nullable=False,
        comment="Usage date (day granularity)"
    )

    # Counters
    query_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total queries on this day"
    )
    successful_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Successful queries"
    )
    failed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Failed queries"
    )

    # Performance Metrics
    total_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens used"
    )
    total_response_time_ms = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total response time in ms"
    )

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    agent = relationship("PublishedAgentConfig", back_populates="usage_records")

    # Unique constraint
    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<PublishedAgentUsage(agent={self.published_agent_id}, date={self.date}, queries={self.query_count})>"
```

---

## 5. Migration Strategy

### 5.1 Alembic Migration

```python
# alembic/versions/xxx_add_published_agent_tables.py

"""Add published agent tables for Developer Tools

Revision ID: xxx
Revises: previous_revision
Create Date: 2025-01-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


def upgrade():
    # Create published_agent_configs table
    op.create_table(
        'published_agent_configs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('api_key_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('api_key_prefix', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('allowed_tables', JSONB, nullable=False, server_default='[]'),
        sa.Column('access_mode', sa.String(20), nullable=False, server_default='read_only'),
        sa.Column('allowed_domains', JSONB, nullable=False, server_default='["*"]'),
        sa.Column('rate_limit_per_minute', sa.Integer, nullable=False, server_default='60'),
        sa.Column('custom_instructions', sa.Text, nullable=True),
        sa.Column('allowed_tools', JSONB, server_default='["database"]'),
        sa.Column('tool_configs', JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('total_queries', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.CheckConstraint("access_mode IN ('read_only', 'read_write')", name='published_agent_access_mode_check'),
    )

    op.create_index('idx_published_agent_configs_user_id', 'published_agent_configs', ['user_id'])
    op.create_index('idx_published_agent_configs_api_key_hash', 'published_agent_configs', ['api_key_hash'], unique=True)
    op.create_index('idx_published_agent_configs_is_active', 'published_agent_configs', ['is_active'])

    # Create published_agent_usage table
    op.create_table(
        'published_agent_usage',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('published_agent_id', sa.String(36), sa.ForeignKey('published_agent_configs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('query_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('successful_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_response_time_ms', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('published_agent_id', 'date', name='unique_agent_date'),
    )

    op.create_index('idx_published_agent_usage_agent_id', 'published_agent_usage', ['published_agent_id'])
    op.create_index('idx_published_agent_usage_date', 'published_agent_usage', ['date'])


def downgrade():
    op.drop_table('published_agent_usage')
    op.drop_table('published_agent_configs')
```

### 5.2 Auto-Create (Development)

For development, tables are auto-created via `Base.metadata.create_all()` in `database.py`. No migration needed for local dev.

---

## 6. Sample Data

```sql
-- Sample published agent config
INSERT INTO published_agent_configs (
    id, user_id, api_key_hash, api_key_prefix, name,
    allowed_tables, access_mode, allowed_domains, rate_limit_per_minute
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    1,  -- Organization user ID
    'sha256_hash_of_pa_live_abc123xyz789...',
    'pa_live_abc1...',
    'Customer Support Agent',
    '["products", "orders", "categories"]',
    'read_only',
    '["*.mystore.com", "localhost:*"]',
    100
);

-- Sample usage data
INSERT INTO published_agent_usage (
    published_agent_id, date, query_count, successful_count, failed_count
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '2025-01-13',
    150,
    145,
    5
);
```

---

## 7. Indexes Summary

| Table | Column(s) | Type | Purpose |
|-------|-----------|------|---------|
| published_agent_configs | user_id | B-tree | List agents by owner |
| published_agent_configs | api_key_hash | Unique | O(1) key lookup |
| published_agent_configs | is_active | Partial | Filter active agents |
| published_agent_usage | published_agent_id | B-tree | Aggregate by agent |
| published_agent_usage | date | B-tree | Time-range queries |

---

## 8. Data Retention

| Table | Retention | Cleanup |
|-------|-----------|---------|
| published_agent_configs | Permanent | Manual delete |
| published_agent_usage | 90 days | Scheduled job |
| published_agent_query_logs | 30 days | Auto-expire (TTL) |

---

## 9. Relationships with Existing Tables

```
EXISTING (NO CHANGES):
├── users
│   ├── id ← published_agent_configs.user_id (Owner)
│   └── ...
├── user_connections
│   ├── user_id ← Used to get database_uri and schema_metadata
│   ├── database_uri ← Connection string for MCP
│   └── schema_metadata ← Full schema (filtered for published agent)
└── ...

NEW (ADDITIVE):
├── published_agent_configs
│   ├── user_id → users.id
│   └── ...
└── published_agent_usage
    └── published_agent_id → published_agent_configs.id
```

---

## 10. Notes

1. **No Foreign Key to user_connections**: Published agents use `user_id` to lookup owner's connection dynamically. This allows flexibility if user reconnects with different database.

2. **JSONB for Arrays**: Using JSONB for `allowed_tables`, `allowed_domains`, `allowed_tools` for PostgreSQL-native array operations and indexing.

3. **Denormalized Usage Stats**: `total_queries` and `last_used_at` in config table for quick dashboard display without joins.

4. **PortableJSON Type**: Uses existing `PortableJSON` from `database.py` for SQLite compatibility in development.
