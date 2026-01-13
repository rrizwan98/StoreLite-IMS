"""
Pydantic Schemas for Developer Portal APIs (Phase 14)

Request and response models for:
- Developer Portal (organization management)
- Public Agent API (external access)

All models use Pydantic v2 syntax.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


# =============================================================================
# Request Models
# =============================================================================

class CreateAgentRequest(BaseModel):
    """Request body for creating a published agent."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-friendly agent name",
        examples=["Customer Support Agent", "Product Catalog Bot"]
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description of this agent"
    )

    allowed_tables: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of table names this agent can access",
        examples=[["products", "orders", "categories"]]
    )

    access_mode: Literal["read_only", "read_write"] = Field(
        "read_only",
        description="Access mode: read_only (SELECT only) or read_write (full CRUD)"
    )

    rate_limit_per_minute: int = Field(
        60,
        ge=1,
        le=1000,
        description="Maximum requests per minute for this API key"
    )

    allowed_domains: List[str] = Field(
        ["*"],
        max_length=20,
        description="CORS whitelist domains (e.g., ['*.mystore.com', 'localhost:*'])"
    )

    custom_instructions: Optional[str] = Field(
        None,
        max_length=2000,
        description="Additional instructions added to agent prompt"
    )

    @field_validator("allowed_tables")
    @classmethod
    def validate_table_names(cls, v):
        """Validate table names are non-empty strings."""
        if not v:
            raise ValueError("At least one table must be specified")
        for table in v:
            if not table or not table.strip():
                raise ValueError("Table names cannot be empty")
        return [t.strip() for t in v]

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v):
        """Validate domain patterns."""
        if not v:
            return ["*"]
        return [d.strip() for d in v if d and d.strip()]


class UpdateAgentRequest(BaseModel):
    """Request body for updating a published agent."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Agent name"
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Agent description"
    )

    allowed_tables: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=50,
        description="List of allowed table names"
    )

    access_mode: Optional[Literal["read_only", "read_write"]] = Field(
        None,
        description="Access mode"
    )

    rate_limit_per_minute: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        description="Rate limit per minute"
    )

    allowed_domains: Optional[List[str]] = Field(
        None,
        max_length=20,
        description="CORS whitelist domains"
    )

    custom_instructions: Optional[str] = Field(
        None,
        max_length=2000,
        description="Custom instructions"
    )

    is_active: Optional[bool] = Field(
        None,
        description="Whether agent is active"
    )


class PublicChatRequest(BaseModel):
    """Request body for public chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User's message/query"
    )

    thread_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Optional thread ID for conversation continuity"
    )

    # Future: Add support for attachments, tools, etc.


# =============================================================================
# Response Models
# =============================================================================

class TableSummary(BaseModel):
    """Summary of a database table for frontend display."""

    name: str = Field(..., description="Table name")
    column_count: int = Field(..., description="Number of columns")
    column_preview: str = Field(..., description="Preview of column names")

    model_config = ConfigDict(from_attributes=True)


class AgentResponse(BaseModel):
    """Response model for a published agent (without API key)."""

    id: str = Field(..., description="Agent UUID")
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")

    # API key prefix (full key never returned after creation)
    api_key_prefix: str = Field(..., description="API key prefix for display")

    # Configuration
    allowed_tables: List[str] = Field(..., description="Allowed table names")
    access_mode: str = Field(..., description="Access mode")
    rate_limit_per_minute: int = Field(..., description="Rate limit")
    allowed_domains: List[str] = Field(..., description="Allowed domains")

    # Status
    is_active: bool = Field(..., description="Whether agent is active")

    # Usage stats (denormalized)
    total_queries: int = Field(..., description="Total queries processed")
    last_used_at: Optional[datetime] = Field(None, description="Last query timestamp")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    model_config = ConfigDict(from_attributes=True)


class AgentCreatedResponse(AgentResponse):
    """
    Response model for newly created agent (includes full API key).

    IMPORTANT: The full API key is only returned at creation time!
    Store it securely - it cannot be retrieved again.
    """

    api_key: str = Field(
        ...,
        description="Full API key - SAVE THIS! It will not be shown again."
    )
    endpoint: str = Field(
        ...,
        description="API endpoint URL for chat requests"
    )
    embed_code: str = Field(
        ...,
        description="Ready-to-use ChatKit embed code"
    )


class AgentListResponse(BaseModel):
    """Response model for listing published agents."""

    agents: List[AgentResponse] = Field(..., description="List of agents")
    total_count: int = Field(..., description="Total number of agents")
    max_allowed: int = Field(..., description="Maximum agents allowed per user")


class PublicChatResponse(BaseModel):
    """Response model for public chat endpoint."""

    response: str = Field(..., description="Agent's response text")
    thread_id: str = Field(..., description="Thread ID for conversation continuity")

    # Optional metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (tables queried, response time, etc.)"
    )


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""

    agent_id: str = Field(..., description="Agent UUID")
    agent_name: str = Field(..., description="Agent name")
    period_days: int = Field(..., description="Number of days in period")

    # Aggregate stats
    total_queries: int = Field(..., description="Total queries")
    successful_queries: int = Field(..., description="Successful queries")
    failed_queries: int = Field(..., description="Failed queries")
    success_rate: float = Field(..., description="Success rate percentage")
    total_tokens: int = Field(..., description="Total tokens consumed")
    avg_response_time_ms: float = Field(..., description="Average response time in ms")

    # Daily breakdown
    daily_breakdown: List[Dict[str, Any]] = Field(
        ...,
        description="Daily usage breakdown"
    )


class EmbedCodeResponse(BaseModel):
    """Response model for embed code retrieval."""

    agent_id: str = Field(..., description="Agent UUID")
    agent_name: str = Field(..., description="Agent name")
    embed_code: str = Field(..., description="HTML/JS embed code snippet")
    endpoint: str = Field(..., description="API endpoint URL")
    instructions: str = Field(
        default="Copy this code and paste it into your website's HTML.",
        description="Integration instructions"
    )


class RegenerateKeyResponse(BaseModel):
    """Response model for API key regeneration."""

    api_key: str = Field(
        ...,
        description="New API key - SAVE THIS! The old key has been revoked."
    )
    api_key_prefix: str = Field(..., description="New key prefix")
    message: str = Field(
        default="Previous API key has been revoked.",
        description="Status message"
    )


# =============================================================================
# Error Response Models
# =============================================================================

class ErrorDetail(BaseModel):
    """Standard error detail format."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class RateLimitErrorResponse(BaseModel):
    """Response model for rate limit exceeded errors."""

    error: str = Field("rate_limit_exceeded", description="Error code")
    message: str = Field(..., description="Error message")
    retry_after: int = Field(..., description="Seconds until rate limit resets")
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(0, description="Remaining requests")
