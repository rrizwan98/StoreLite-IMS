"""
Developer Portal Router (Phase 14 - Developer Tools)

API endpoints for managing Published Agents via Developer Portal.
All endpoints require JWT authentication (organization user).

This router allows organizations to:
- Create/manage published agents with API keys
- Configure table access, rate limits, and domain restrictions
- View usage statistics and embed code
- Generate embeddable code snippets for external integration

Base path: /api/developer
"""

import os
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserConnection
from app.routers.auth import get_current_user
from app.schemas.developer_portal import (
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentResponse,
    AgentCreatedResponse,
    AgentListResponse,
    UsageStatsResponse,
    EmbedCodeResponse,
    RegenerateKeyResponse,
    TableSummary,
)
from app.services.published_agent_service import (
    PublishedAgentService,
    generate_embed_code,
    MAX_AGENTS_PER_USER,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/developer", tags=["developer-portal"])

# Security scheme
security = HTTPBearer(auto_error=False)


# =============================================================================
# Helper Functions
# =============================================================================

def _build_agent_response(config, include_stats: bool = True) -> AgentResponse:
    """
    Convert PublishedAgentConfig model to AgentResponse schema.

    Args:
        config: PublishedAgentConfig model instance
        include_stats: Whether to include usage stats

    Returns:
        AgentResponse schema
    """
    return AgentResponse(
        id=config.id,
        name=config.name,
        description=config.description,
        api_key_prefix=config.api_key_prefix,
        allowed_tables=config.allowed_tables,
        access_mode=config.access_mode,
        rate_limit_per_minute=config.rate_limit_per_minute,
        allowed_domains=config.allowed_domains,
        is_active=config.is_active,
        total_queries=config.total_queries if include_stats else 0,
        last_used_at=config.last_used_at,
        created_at=config.created_at,
        updated_at=config.updated_at,
        expires_at=config.expires_at,
    )


def _get_backend_url() -> str:
    """Get backend URL from environment or default."""
    return os.getenv("BACKEND_URL", "http://localhost:8000")


# =============================================================================
# Developer Portal Endpoints
# =============================================================================

@router.get("/tables", response_model=List[TableSummary])
async def list_available_tables(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all tables available in the user's connected database.

    Use this endpoint to populate the table selection dropdown when
    creating or updating a published agent.

    Returns:
        List of table summaries with name and column info
    """
    from sqlalchemy import select

    # Get user's connection
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == user.id)
    )
    connection = result.scalar_one_or_none()

    if not connection or not connection.schema_metadata:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "no_database",
                "message": "No database connected. Please connect your database first."
            }
        )

    # Extract tables from schema metadata
    schema = connection.schema_metadata
    tables = schema.get("tables", [])

    if not tables:
        return []

    # Build table summaries
    summaries = []
    for table in tables:
        table_name = table.get("name", "")
        columns = table.get("columns", [])
        column_names = [c.get("name", "") for c in columns[:5]]  # First 5 columns

        preview = ", ".join(column_names)
        if len(columns) > 5:
            preview += f", ... (+{len(columns) - 5} more)"

        summaries.append(TableSummary(
            name=table_name,
            column_count=len(columns),
            column_preview=preview
        ))

    logger.info(f"[Developer Portal] Listed {len(summaries)} tables for user {user.id}")

    return summaries


@router.post("/agents", response_model=AgentCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_published_agent(
    request: CreateAgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new published agent with API key.

    IMPORTANT: The API key is only returned once at creation time!
    Store it securely - it cannot be retrieved again.

    Args:
        request: Agent configuration (name, allowed_tables, access_mode, etc.)

    Returns:
        Agent details including:
        - api_key: Full API key (SAVE THIS!)
        - endpoint: API endpoint URL for chat requests
        - embed_code: Ready-to-use ChatKit embed code
    """
    service = PublishedAgentService(db)

    try:
        config, api_key = await service.create_agent(
            user_id=user.id,
            name=request.name,
            allowed_tables=request.allowed_tables,
            access_mode=request.access_mode,
            rate_limit_per_minute=request.rate_limit_per_minute,
            allowed_domains=request.allowed_domains,
            custom_instructions=request.custom_instructions,
            description=request.description,
        )

        # Build response with API key and embed code
        backend_url = _get_backend_url()
        endpoint = f"{backend_url}/api/v1/public/chat"
        embed_code = generate_embed_code(
            agent_id=config.id,
            agent_name=config.name,
            api_key=api_key,
            backend_url=backend_url
        )

        logger.info(
            f"[Developer Portal] Created agent: id={config.id[:8]}..., "
            f"name='{config.name}', user={user.id}"
        )

        return AgentCreatedResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            api_key_prefix=config.api_key_prefix,
            allowed_tables=config.allowed_tables,
            access_mode=config.access_mode,
            rate_limit_per_minute=config.rate_limit_per_minute,
            allowed_domains=config.allowed_domains,
            is_active=config.is_active,
            total_queries=config.total_queries,
            last_used_at=config.last_used_at,
            created_at=config.created_at,
            updated_at=config.updated_at,
            expires_at=config.expires_at,
            api_key=api_key,
            endpoint=endpoint,
            embed_code=embed_code,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "creation_failed",
                "message": "Failed to create published agent. Please try again."
            }
        )


@router.get("/agents", response_model=AgentListResponse)
async def list_published_agents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all published agents for the current user.

    Returns:
        List of agents with their configurations and usage stats
    """
    service = PublishedAgentService(db)

    try:
        configs = await service.list_agents(user.id)

        agents = [_build_agent_response(config) for config in configs]

        logger.info(
            f"[Developer Portal] Listed {len(agents)} agents for user {user.id}"
        )

        return AgentListResponse(
            agents=agents,
            total_count=len(agents),
            max_allowed=MAX_AGENTS_PER_USER
        )

    except Exception as e:
        logger.error(f"[Developer Portal] Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "list_failed",
                "message": "Failed to list published agents."
            }
        )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_published_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific published agent.

    Args:
        agent_id: Agent UUID

    Returns:
        Agent configuration and usage stats
    """
    service = PublishedAgentService(db)

    try:
        config = await service.get_agent(agent_id, user.id)

        return _build_agent_response(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error getting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_failed",
                "message": "Failed to get published agent."
            }
        )


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_published_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a published agent's configuration.

    Args:
        agent_id: Agent UUID
        request: Fields to update (only provided fields are updated)

    Returns:
        Updated agent configuration
    """
    service = PublishedAgentService(db)

    try:
        config = await service.update_agent(
            agent_id=agent_id,
            user_id=user.id,
            name=request.name,
            description=request.description,
            allowed_tables=request.allowed_tables,
            access_mode=request.access_mode,
            rate_limit_per_minute=request.rate_limit_per_minute,
            allowed_domains=request.allowed_domains,
            custom_instructions=request.custom_instructions,
            is_active=request.is_active,
        )

        logger.info(
            f"[Developer Portal] Updated agent: id={agent_id[:8]}..., user={user.id}"
        )

        return _build_agent_response(config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error updating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_failed",
                "message": "Failed to update published agent."
            }
        )


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_published_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a published agent.

    This immediately revokes the API key and removes all configuration.
    Usage statistics are preserved for audit purposes.

    Args:
        agent_id: Agent UUID
    """
    service = PublishedAgentService(db)

    try:
        await service.delete_agent(agent_id, user.id)

        logger.info(
            f"[Developer Portal] Deleted agent: id={agent_id[:8]}..., user={user.id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error deleting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "delete_failed",
                "message": "Failed to delete published agent."
            }
        )


@router.post("/agents/{agent_id}/regenerate-key", response_model=RegenerateKeyResponse)
async def regenerate_api_key(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Regenerate the API key for a published agent.

    WARNING: This immediately revokes the old API key!
    All existing integrations using the old key will stop working.

    Args:
        agent_id: Agent UUID

    Returns:
        New API key (SAVE THIS! It will not be shown again)
    """
    service = PublishedAgentService(db)

    try:
        new_api_key = await service.regenerate_key(agent_id, user.id)

        # Get updated config for prefix
        config = await service.get_agent(agent_id, user.id)

        logger.info(
            f"[Developer Portal] Regenerated key for agent: id={agent_id[:8]}..., user={user.id}"
        )

        return RegenerateKeyResponse(
            api_key=new_api_key,
            api_key_prefix=config.api_key_prefix,
            message="Previous API key has been revoked. Update your integrations with the new key."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error regenerating key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "regenerate_failed",
                "message": "Failed to regenerate API key."
            }
        )


@router.get("/agents/{agent_id}/usage", response_model=UsageStatsResponse)
async def get_usage_statistics(
    agent_id: str,
    days: int = Query(default=30, ge=1, le=90, description="Number of days to include"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for a published agent.

    Args:
        agent_id: Agent UUID
        days: Number of days to include (1-90, default: 30)

    Returns:
        Aggregate stats and daily breakdown
    """
    service = PublishedAgentService(db)

    try:
        stats = await service.get_usage_stats(agent_id, user.id, days)

        return UsageStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error getting usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "stats_failed",
                "message": "Failed to get usage statistics."
            }
        )


@router.get("/agents/{agent_id}/embed-code", response_model=EmbedCodeResponse)
async def get_embed_code(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the embed code for a published agent.

    Note: The embed code includes the API key prefix, not the full key.
    You'll need to replace it with the actual API key.

    Args:
        agent_id: Agent UUID

    Returns:
        HTML/JS embed code snippet and integration instructions
    """
    service = PublishedAgentService(db)

    try:
        config = await service.get_agent(agent_id, user.id)

        # Generate embed code with placeholder for API key
        backend_url = _get_backend_url()
        endpoint = f"{backend_url}/api/v1/public/chat"

        # Use placeholder since we can't show full key
        embed_code = generate_embed_code(
            agent_id=config.id,
            agent_name=config.name,
            api_key="YOUR_API_KEY_HERE",  # Placeholder
            backend_url=backend_url
        )

        return EmbedCodeResponse(
            agent_id=config.id,
            agent_name=config.name,
            embed_code=embed_code,
            endpoint=endpoint,
            instructions=(
                "1. Replace 'YOUR_API_KEY_HERE' with your actual API key.\n"
                "2. Copy this code into your website's HTML.\n"
                "3. The chat widget will appear in the designated container.\n"
                "Note: Keep your API key secure and never expose it in public repositories."
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Developer Portal] Error getting embed code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "embed_failed",
                "message": "Failed to get embed code."
            }
        )
