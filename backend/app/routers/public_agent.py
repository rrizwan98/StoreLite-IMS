"""
Public Agent API Router (Phase 14 - Developer Tools)

Public-facing API endpoints for external users to interact with published agents.
Uses API key authentication (X-API-Key header) instead of JWT.

Key Security Features:
- API key validation (hashed comparison)
- Schema filtering (only allowed tables)
- Rate limiting (per-minute sliding window)
- Domain validation (Origin header check)
- Access mode enforcement (read_only/read_write)

Base path: /api/v1/public
"""

import os
import time
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import UserConnection
from app.models.published_agent import PublishedAgentConfig
from app.schemas.developer_portal import (
    PublicChatRequest,
    PublicChatResponse,
    RateLimitErrorResponse,
)
from app.services.api_key_service import validate_api_key
from app.services.schema_filter_service import filter_schema_for_published_agent
from app.services.published_agent_rate_limiter import check_and_record_rate_limit
from app.services.domain_validator import validate_origin
from app.services.published_agent_service import PublishedAgentService
from app.services.sql_table_validator import get_table_access_summary
from app.agents.schema_query_agent import create_schema_query_agent, SchemaQueryAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/public", tags=["public-agent-api"])


# =============================================================================
# Agent Cache for Published Agents
# =============================================================================

# Cache agents by published_agent_id for performance
# Key: published_agent_id, Value: SchemaQueryAgent instance
_published_agent_cache: Dict[str, SchemaQueryAgent] = {}


async def _get_or_create_agent(
    config: PublishedAgentConfig,
    user_connection: UserConnection,
    thread_id: str
) -> SchemaQueryAgent:
    """
    Get cached agent or create new one for the published agent.

    Args:
        config: PublishedAgentConfig for this API key
        user_connection: Owner's database connection
        thread_id: Thread ID for conversation

    Returns:
        SchemaQueryAgent instance with filtered schema

    IMPORTANT:
        - Caching is DISABLED for published agents to ensure table restrictions work
        - Each request creates a fresh agent with properly filtered schema
        - This is necessary because the agent prompt contains the schema
    """
    # NOTE: Cache disabled for security - each request gets fresh agent
    # This ensures table filtering is always applied correctly
    # cache_key = config.id
    # if cache_key in _published_agent_cache:
    #     cached_agent = _published_agent_cache[cache_key]
    #     logger.debug(f"[Public API] Using cached agent for {cache_key[:8]}...")
    #     return cached_agent

    # Filter schema based on allowed tables and access mode
    filtered_schema = filter_schema_for_published_agent(
        full_schema=user_connection.schema_metadata,
        allowed_tables=config.allowed_tables,
        access_mode=config.access_mode
    )

    # Log filtered schema for debugging
    filtered_tables = [t.get("name") for t in filtered_schema.get("tables", [])]
    logger.info(
        f"[Public API] Filtered schema for {config.id[:8]}...: "
        f"allowed={config.allowed_tables}, filtered_tables={filtered_tables}"
    )

    # Determine read_only based on access_mode
    read_only = config.access_mode == "read_only"

    # Create new agent with filtered schema
    agent = await create_schema_query_agent(
        database_uri=user_connection.database_uri,
        schema_metadata=filtered_schema,
        auto_initialize=True,
        read_only=read_only,
        user_id=config.user_id,
        thread_id=thread_id,
    )

    # NOTE: Caching disabled for security reasons
    # _published_agent_cache[cache_key] = agent

    logger.info(
        f"[Public API] Created fresh agent for {config.id[:8]}... "
        f"(tables={len(config.allowed_tables)}, mode={config.access_mode})"
    )

    return agent


# =============================================================================
# Dependency: Validate API Key
# =============================================================================

async def get_published_agent_config(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
) -> PublishedAgentConfig:
    """
    Dependency to validate API key and return PublishedAgentConfig.

    Also validates:
    - Origin header against allowed domains
    - Rate limit

    Raises:
        HTTPException(401): If API key is invalid
        HTTPException(403): If origin is not allowed
        HTTPException(429): If rate limit exceeded
    """
    # Validate API key presence
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": "API key is required. Provide it via X-API-Key header."
            },
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Validate API key
    try:
        config = await validate_api_key(x_api_key, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Public API] API key validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key."
            }
        )

    # Validate Origin header
    origin = request.headers.get("Origin")
    if not validate_origin(origin, config.allowed_domains):
        logger.warning(
            f"[Public API] Origin rejected: {origin} "
            f"(allowed: {config.allowed_domains})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "origin_not_allowed",
                "message": f"Origin '{origin}' is not in the allowed domains list.",
                "allowed_domains": config.allowed_domains
            }
        )

    return config


# =============================================================================
# Public API Endpoints
# =============================================================================

@router.post("/chat", response_model=PublicChatResponse)
async def public_chat(
    request: Request,
    chat_request: PublicChatRequest,
    config: PublishedAgentConfig = Depends(get_published_agent_config),
    db: AsyncSession = Depends(get_db)
):
    """
    Chat with a published agent using natural language.

    This is the main endpoint for external users to interact with the agent.
    Authentication is via API key (X-API-Key header).

    Args:
        chat_request: Message and optional thread_id

    Returns:
        Agent response and thread_id for conversation continuity

    Rate Limit Headers:
        - X-RateLimit-Limit: Max requests per minute
        - X-RateLimit-Remaining: Remaining requests
        - X-RateLimit-Reset: Seconds until reset
    """
    start_time = time.time()

    # Check rate limit
    allowed, rate_headers = await check_and_record_rate_limit(
        key_id=config.id,
        limit=config.rate_limit_per_minute
    )

    if not allowed:
        logger.warning(f"[Public API] Rate limit exceeded for {config.id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": int(rate_headers.get("X-RateLimit-Reset", 60)),
                "limit": config.rate_limit_per_minute,
                "remaining": 0
            },
            headers=rate_headers
        )

    # Get owner's database connection
    result = await db.execute(
        select(UserConnection).where(UserConnection.user_id == config.user_id)
    )
    user_connection = result.scalar_one_or_none()

    if not user_connection or not user_connection.schema_metadata:
        logger.error(f"[Public API] No database connection for owner of {config.id[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "database_unavailable",
                "message": "The agent's database is not available. Please contact the administrator."
            }
        )

    # Generate or use thread_id for conversation continuity
    thread_id = chat_request.thread_id or f"public-{config.id[:8]}-{uuid.uuid4().hex[:8]}"

    try:
        # Get or create agent with filtered schema
        agent = await _get_or_create_agent(config, user_connection, thread_id)

        # Build MANDATORY table restriction context
        # This is added to EVERY message to ensure agent respects table limits
        table_restriction = get_table_access_summary(config.allowed_tables, config.access_mode)
        restriction_context = f"\n\n[IMPORTANT RESTRICTION: {table_restriction} Do NOT query any other tables.]"

        # Build optional custom instructions
        custom_context = ""
        if config.custom_instructions:
            custom_context = f"\n\nAdditional context: {config.custom_instructions}"

        # Process the query - ALWAYS add restriction context
        message_with_context = f"{chat_request.message}{restriction_context}{custom_context}"

        logger.debug(f"[Public API] Message with context: {message_with_context[:200]}...")

        result = await agent.query(message_with_context, thread_id=thread_id)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Record usage (async, don't wait)
        service = PublishedAgentService(db)
        await service.record_query(
            agent_id=config.id,
            success=result.get("success", False),
            response_time_ms=response_time_ms,
            tokens=0  # TODO: Get actual token count from agent
        )

        logger.info(
            f"[Public API] Query processed for {config.id[:8]}... "
            f"(time={response_time_ms}ms, success={result.get('success')})"
        )

        # Build response
        response = PublicChatResponse(
            response=result.get("response", ""),
            thread_id=thread_id,
            metadata={
                "success": result.get("success", False),
                "response_time_ms": response_time_ms,
                "visualization_hint": result.get("visualization_hint"),
            }
        )

        # Create JSONResponse with rate limit headers
        return JSONResponse(
            content=response.model_dump(),
            headers=rate_headers
        )

    except HTTPException:
        raise
    except Exception as e:
        # Calculate response time for error case
        response_time_ms = int((time.time() - start_time) * 1000)

        # Record failed query
        try:
            service = PublishedAgentService(db)
            await service.record_query(
                agent_id=config.id,
                success=False,
                response_time_ms=response_time_ms,
            )
        except Exception as record_error:
            logger.error(f"[Public API] Failed to record error: {record_error}")

        logger.error(f"[Public API] Query failed for {config.id[:8]}...: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "query_failed",
                "message": "An error occurred while processing your request. Please try again."
            },
            headers=rate_headers
        )


@router.get("/health")
async def public_health_check(
    config: PublishedAgentConfig = Depends(get_published_agent_config),
):
    """
    Health check endpoint for published agent API.

    Use this to verify your API key is valid and the agent is available.

    Returns:
        Agent status and configuration summary
    """
    return {
        "status": "healthy",
        "agent_name": config.name,
        "agent_id": config.id[:8] + "...",
        "access_mode": config.access_mode,
        "rate_limit": config.rate_limit_per_minute,
        "tables_available": len(config.allowed_tables),
        "is_active": config.is_active,
    }


@router.options("/chat")
async def public_chat_options(request: Request):
    """
    CORS preflight handler for /chat endpoint.

    Returns CORS headers for browser-based integrations.
    """
    origin = request.headers.get("Origin", "*")

    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, X-API-Key",
            "Access-Control-Max-Age": "86400",  # 24 hours
        }
    )


# =============================================================================
# Cache Management (Admin/Internal)
# =============================================================================

async def clear_published_agent_cache(agent_id: Optional[str] = None) -> int:
    """
    Clear cached agent(s).

    Args:
        agent_id: Specific agent to clear, or None to clear all

    Returns:
        Number of agents cleared
    """
    global _published_agent_cache

    if agent_id:
        if agent_id in _published_agent_cache:
            # Close the agent if it has a close method
            try:
                agent = _published_agent_cache[agent_id]
                if hasattr(agent, 'close'):
                    await agent.close()
            except Exception as e:
                logger.warning(f"[Public API] Error closing agent {agent_id[:8]}...: {e}")

            del _published_agent_cache[agent_id]
            logger.info(f"[Public API] Cleared cached agent: {agent_id[:8]}...")
            return 1
        return 0

    # Clear all
    count = len(_published_agent_cache)
    for aid, agent in list(_published_agent_cache.items()):
        try:
            if hasattr(agent, 'close'):
                await agent.close()
        except Exception:
            pass

    _published_agent_cache.clear()
    logger.info(f"[Public API] Cleared all cached agents: {count}")
    return count
