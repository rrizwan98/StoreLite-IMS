"""
Published Agent Models for Developer Tools Feature (Phase 14)

These models enable organizations to share their Schema Agent with external
users/clients through a secure API key system with restricted access.

Key Features:
- PublishedAgentConfig: Configuration for each published agent
- PublishedAgentUsage: Daily usage statistics tracking

Design Principle: Reuse existing SchemaQueryAgent with filtered schema_metadata
(no new agent code, only access control layer)
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base, PortableJSON


class PublishedAgentConfig(Base):
    """
    Configuration for a published/shared agent.

    Organizations create these to allow external users to access their
    Schema Agent with restricted permissions (table-level access control).

    Key Security Features:
    - API key stored as SHA-256 hash (original shown only once)
    - Rate limiting per API key
    - CORS domain whitelisting
    - Table-level access control via allowed_tables

    Usage Flow:
    1. Organization creates PublishedAgentConfig with allowed_tables
    2. System generates API key (pa_live_xxx...) - shown once
    3. External user calls /api/v1/public/chat with X-API-Key header
    4. Backend filters schema_metadata to only allowed_tables
    5. Same SchemaQueryAgent processes query with filtered view
    """

    __tablename__ = "published_agent_configs"

    # =========================================================================
    # Primary Key
    # =========================================================================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier (UUID)"
    )

    # =========================================================================
    # Owner (Organization)
    # =========================================================================
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner organization's user ID"
    )

    # =========================================================================
    # API Key (Security)
    # =========================================================================
    api_key_hash = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of the API key (original never stored)"
    )
    api_key_prefix = Column(
        String(20),
        nullable=False,
        comment="Prefix for display (e.g., 'pa_live_abc1...')"
    )

    # =========================================================================
    # Agent Configuration
    # =========================================================================
    name = Column(
        String(255),
        nullable=False,
        comment="Human-friendly agent name"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Optional description of this published agent"
    )

    # =========================================================================
    # Access Control - Tables
    # =========================================================================
    allowed_tables = Column(
        PortableJSON,
        nullable=False,
        default=list,
        comment="List of table names this agent can access (e.g., ['products', 'orders'])"
    )
    access_mode = Column(
        String(20),
        nullable=False,
        default="read_only",
        comment="Access mode: 'read_only' (SELECT only) or 'read_write' (full CRUD)"
    )

    # =========================================================================
    # Access Control - Domains (CORS)
    # =========================================================================
    allowed_domains = Column(
        PortableJSON,
        nullable=False,
        default=lambda: ["*"],
        comment="CORS whitelist domains (e.g., ['*.mystore.com', 'localhost:*'])"
    )

    # =========================================================================
    # Rate Limiting
    # =========================================================================
    rate_limit_per_minute = Column(
        Integer,
        nullable=False,
        default=60,
        comment="Maximum requests per minute for this API key"
    )

    # =========================================================================
    # Customization
    # =========================================================================
    custom_instructions = Column(
        Text,
        nullable=True,
        comment="Additional prompt instructions added to agent (e.g., 'Be extra helpful')"
    )

    # =========================================================================
    # Future: Tool Access Control (Phase 2)
    # =========================================================================
    allowed_tools = Column(
        PortableJSON,
        nullable=False,
        default=lambda: ["database"],
        comment="Tools this agent can use: ['database', 'gmail', 'analytics'] - for future expansion"
    )
    tool_configs = Column(
        PortableJSON,
        nullable=False,
        default=dict,
        comment="Tool-specific configurations (for future use)"
    )

    # =========================================================================
    # Status
    # =========================================================================
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this published agent is active and can receive requests"
    )

    # =========================================================================
    # Timestamps
    # =========================================================================
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When this agent was created"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="When this agent was last updated"
    )
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Optional expiration timestamp (NULL = never expires)"
    )

    # =========================================================================
    # Usage Stats (Denormalized for quick dashboard display)
    # =========================================================================
    total_queries = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of queries processed (denormalized)"
    )
    last_used_at = Column(
        DateTime,
        nullable=True,
        comment="Timestamp of last query"
    )

    # =========================================================================
    # Constraints & Indexes
    # =========================================================================
    __table_args__ = (
        CheckConstraint(
            "access_mode IN ('read_only', 'read_write')",
            name="published_agent_access_mode_check"
        ),
        CheckConstraint(
            "rate_limit_per_minute >= 1 AND rate_limit_per_minute <= 10000",
            name="published_agent_rate_limit_check"
        ),
        # Composite index for listing user's agents
        Index("idx_published_agent_user_active", "user_id", "is_active"),
        {"extend_existing": True},
    )

    # =========================================================================
    # Relationships
    # =========================================================================
    user = relationship("User", backref="published_agents")
    usage_records = relationship(
        "PublishedAgentUsage",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="PublishedAgentUsage.date.desc()"
    )

    # =========================================================================
    # Properties
    # =========================================================================
    @property
    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_usable(self) -> bool:
        """Check if the agent can be used (active and not expired)."""
        return self.is_active and not self.is_expired

    @property
    def table_count(self) -> int:
        """Return number of allowed tables."""
        if self.allowed_tables:
            return len(self.allowed_tables)
        return 0

    def __repr__(self) -> str:
        return (
            f"<PublishedAgentConfig("
            f"id={self.id[:8]}..., "
            f"name='{self.name}', "
            f"owner={self.user_id}, "
            f"tables={self.table_count}, "
            f"active={self.is_active}"
            f")>"
        )


class PublishedAgentUsage(Base):
    """
    Daily usage statistics for a published agent.

    Aggregates query counts and performance metrics by day for efficient
    dashboard display and usage analytics.

    One row per agent per day (upsert pattern used for updates).
    """

    __tablename__ = "published_agent_usage"

    # =========================================================================
    # Primary Key
    # =========================================================================
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Auto-incrementing primary key"
    )

    # =========================================================================
    # Foreign Key
    # =========================================================================
    published_agent_id = Column(
        String(36),
        ForeignKey("published_agent_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to published agent"
    )

    # =========================================================================
    # Date (Partition Key)
    # =========================================================================
    date = Column(
        DateTime,
        nullable=False,
        comment="Usage date (day granularity, time part ignored)"
    )

    # =========================================================================
    # Query Counters
    # =========================================================================
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
        comment="Successful queries (returned response)"
    )
    failed_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Failed queries (errors)"
    )

    # =========================================================================
    # Performance Metrics
    # =========================================================================
    total_tokens = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total tokens consumed (for cost tracking)"
    )
    total_response_time_ms = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total response time in milliseconds (for avg calculation)"
    )

    # =========================================================================
    # Timestamps
    # =========================================================================
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When this record was created"
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="When this record was last updated"
    )

    # =========================================================================
    # Constraints & Indexes
    # =========================================================================
    __table_args__ = (
        # Unique constraint: one row per agent per day
        Index(
            "idx_published_agent_usage_unique",
            "published_agent_id",
            "date",
            unique=True
        ),
        # Index for time-range queries
        Index("idx_published_agent_usage_date", "date"),
        {"extend_existing": True},
    )

    # =========================================================================
    # Relationships
    # =========================================================================
    agent = relationship("PublishedAgentConfig", back_populates="usage_records")

    # =========================================================================
    # Properties
    # =========================================================================
    @property
    def avg_response_time_ms(self) -> float:
        """Calculate average response time in milliseconds."""
        if self.query_count == 0:
            return 0.0
        return self.total_response_time_ms / self.query_count

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.query_count == 0:
            return 0.0
        return (self.successful_count / self.query_count) * 100

    def __repr__(self) -> str:
        return (
            f"<PublishedAgentUsage("
            f"agent={self.published_agent_id[:8] if self.published_agent_id else 'None'}..., "
            f"date={self.date.strftime('%Y-%m-%d') if self.date else 'None'}, "
            f"queries={self.query_count}"
            f")>"
        )
