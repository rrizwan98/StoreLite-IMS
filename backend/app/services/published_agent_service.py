"""
Published Agent Service for Developer Tools (Phase 14)

Main business logic layer for published agent CRUD operations.
Handles creation, updates, deletion, and usage tracking.

Key Responsibilities:
- Create published agents with API key generation
- List/get/update/delete agents with ownership validation
- Regenerate API keys
- Record and retrieve usage statistics
- Validate table names against owner's schema
"""

import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models import UserConnection
from app.models.published_agent import PublishedAgentConfig, PublishedAgentUsage
from app.services.api_key_service import generate_api_key, hash_api_key
from app.services.schema_filter_service import validate_allowed_tables

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Maximum published agents per user
MAX_AGENTS_PER_USER = 10

# Default rate limit if not specified
DEFAULT_RATE_LIMIT = 60


# =============================================================================
# Published Agent Service Class
# =============================================================================

class PublishedAgentService:
    """
    Business logic for published agent management.

    All operations validate ownership (user_id match).
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize service with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    async def create_agent(
        self,
        user_id: int,
        name: str,
        allowed_tables: List[str],
        access_mode: str = "read_only",
        rate_limit_per_minute: int = DEFAULT_RATE_LIMIT,
        allowed_domains: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tuple[PublishedAgentConfig, str]:
        """
        Create a new published agent.

        Args:
            user_id: Owner's user ID
            name: Agent name
            allowed_tables: List of table names to allow
            access_mode: "read_only" or "read_write"
            rate_limit_per_minute: Rate limit (default: 60)
            allowed_domains: CORS whitelist (default: ["*"])
            custom_instructions: Additional prompt instructions
            description: Optional description

        Returns:
            Tuple of (config, api_key)
            Note: api_key is only returned at creation time!

        Raises:
            HTTPException(400): If validation fails
            HTTPException(403): If user has max agents
        """
        # Check agent limit
        agent_count = await self._count_user_agents(user_id)
        if agent_count >= MAX_AGENTS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "agent_limit_exceeded",
                    "message": f"Maximum {MAX_AGENTS_PER_USER} published agents allowed per user."
                }
            )

        # Get owner's schema to validate tables
        user_connection = await self._get_user_connection(user_id)
        if not user_connection or not user_connection.schema_metadata:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "no_schema",
                    "message": "Database not connected. Connect your database first."
                }
            )

        # Validate table names
        valid_tables, invalid_tables = validate_allowed_tables(
            allowed_tables,
            user_connection.schema_metadata
        )

        if invalid_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_tables",
                    "message": f"Tables not found in your database: {invalid_tables}",
                    "invalid_tables": invalid_tables,
                    "valid_tables": valid_tables,
                }
            )

        if not valid_tables:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "no_valid_tables",
                    "message": "At least one valid table must be selected."
                }
            )

        # Generate API key
        api_key, api_key_hash, api_key_prefix = generate_api_key()

        # Create config
        config = PublishedAgentConfig(
            user_id=user_id,
            api_key_hash=api_key_hash,
            api_key_prefix=api_key_prefix,
            name=name,
            description=description,
            allowed_tables=valid_tables,
            access_mode=access_mode,
            rate_limit_per_minute=rate_limit_per_minute,
            allowed_domains=allowed_domains or ["*"],
            custom_instructions=custom_instructions,
            allowed_tools=["database"],  # Future: add more tools
        )

        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        logger.info(
            f"[Published Agent] Created: id={config.id[:8]}..., "
            f"name='{name}', owner={user_id}, tables={len(valid_tables)}"
        )

        return config, api_key

    async def list_agents(self, user_id: int) -> List[PublishedAgentConfig]:
        """
        List all published agents for a user.

        Args:
            user_id: Owner's user ID

        Returns:
            List of PublishedAgentConfig (ordered by created_at desc)
        """
        result = await self.db.execute(
            select(PublishedAgentConfig)
            .where(PublishedAgentConfig.user_id == user_id)
            .order_by(PublishedAgentConfig.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_agent(
        self,
        agent_id: str,
        user_id: int
    ) -> PublishedAgentConfig:
        """
        Get a specific published agent (with ownership validation).

        Args:
            agent_id: Agent UUID
            user_id: Owner's user ID (for validation)

        Returns:
            PublishedAgentConfig

        Raises:
            HTTPException(404): If not found or not owned by user
        """
        result = await self.db.execute(
            select(PublishedAgentConfig).where(
                and_(
                    PublishedAgentConfig.id == agent_id,
                    PublishedAgentConfig.user_id == user_id
                )
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "agent_not_found",
                    "message": "Published agent not found."
                }
            )

        return config

    async def update_agent(
        self,
        agent_id: str,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        allowed_tables: Optional[List[str]] = None,
        access_mode: Optional[str] = None,
        rate_limit_per_minute: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> PublishedAgentConfig:
        """
        Update a published agent.

        Args:
            agent_id: Agent UUID
            user_id: Owner's user ID
            ... (fields to update, None = no change)

        Returns:
            Updated PublishedAgentConfig

        Raises:
            HTTPException(404): If not found
            HTTPException(400): If validation fails
        """
        config = await self.get_agent(agent_id, user_id)

        # Validate tables if provided
        if allowed_tables is not None:
            user_connection = await self._get_user_connection(user_id)
            valid_tables, invalid_tables = validate_allowed_tables(
                allowed_tables,
                user_connection.schema_metadata if user_connection else {}
            )

            if invalid_tables:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "invalid_tables",
                        "message": f"Tables not found: {invalid_tables}",
                    }
                )

            config.allowed_tables = valid_tables

        # Update fields if provided
        if name is not None:
            config.name = name
        if description is not None:
            config.description = description
        if access_mode is not None:
            config.access_mode = access_mode
        if rate_limit_per_minute is not None:
            config.rate_limit_per_minute = rate_limit_per_minute
        if allowed_domains is not None:
            config.allowed_domains = allowed_domains
        if custom_instructions is not None:
            config.custom_instructions = custom_instructions
        if is_active is not None:
            config.is_active = is_active

        config.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(config)

        logger.info(f"[Published Agent] Updated: id={agent_id[:8]}...")

        return config

    async def delete_agent(
        self,
        agent_id: str,
        user_id: int
    ) -> bool:
        """
        Delete a published agent.

        Args:
            agent_id: Agent UUID
            user_id: Owner's user ID

        Returns:
            True if deleted

        Raises:
            HTTPException(404): If not found
        """
        config = await self.get_agent(agent_id, user_id)

        await self.db.delete(config)
        await self.db.commit()

        logger.info(f"[Published Agent] Deleted: id={agent_id[:8]}...")

        return True

    async def regenerate_key(
        self,
        agent_id: str,
        user_id: int
    ) -> str:
        """
        Regenerate API key for an agent (revokes old key).

        Args:
            agent_id: Agent UUID
            user_id: Owner's user ID

        Returns:
            New API key (shown only once!)

        Raises:
            HTTPException(404): If not found
        """
        config = await self.get_agent(agent_id, user_id)

        # Generate new key
        api_key, api_key_hash, api_key_prefix = generate_api_key()

        # Update config
        config.api_key_hash = api_key_hash
        config.api_key_prefix = api_key_prefix
        config.updated_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"[Published Agent] Key regenerated: id={agent_id[:8]}...")

        return api_key

    # =========================================================================
    # Usage Tracking
    # =========================================================================

    async def record_query(
        self,
        agent_id: str,
        success: bool,
        response_time_ms: int,
        tokens: int = 0
    ) -> None:
        """
        Record a query for usage statistics.

        Uses upsert pattern to update daily stats.

        Args:
            agent_id: Agent UUID
            success: Whether query succeeded
            response_time_ms: Response time in milliseconds
            tokens: Tokens consumed (optional)
        """
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Find or create usage record for today
        result = await self.db.execute(
            select(PublishedAgentUsage).where(
                and_(
                    PublishedAgentUsage.published_agent_id == agent_id,
                    PublishedAgentUsage.date == today
                )
            )
        )
        usage = result.scalar_one_or_none()

        if usage:
            # Update existing record
            usage.query_count += 1
            if success:
                usage.successful_count += 1
            else:
                usage.failed_count += 1
            usage.total_tokens += tokens
            usage.total_response_time_ms += response_time_ms
            usage.updated_at = datetime.utcnow()
        else:
            # Create new record
            usage = PublishedAgentUsage(
                published_agent_id=agent_id,
                date=today,
                query_count=1,
                successful_count=1 if success else 0,
                failed_count=0 if success else 1,
                total_tokens=tokens,
                total_response_time_ms=response_time_ms,
            )
            self.db.add(usage)

        # Also update denormalized stats on config
        result = await self.db.execute(
            select(PublishedAgentConfig).where(
                PublishedAgentConfig.id == agent_id
            )
        )
        config = result.scalar_one_or_none()
        if config:
            config.total_queries += 1
            config.last_used_at = datetime.utcnow()

        await self.db.commit()

    async def get_usage_stats(
        self,
        agent_id: str,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics for an agent.

        Args:
            agent_id: Agent UUID
            user_id: Owner's user ID
            days: Number of days to include (default: 30)

        Returns:
            Dict with usage statistics

        Raises:
            HTTPException(404): If agent not found
        """
        # Validate ownership
        config = await self.get_agent(agent_id, user_id)

        # Get date range
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)

        # Get usage records
        result = await self.db.execute(
            select(PublishedAgentUsage)
            .where(
                and_(
                    PublishedAgentUsage.published_agent_id == agent_id,
                    PublishedAgentUsage.date >= start_date
                )
            )
            .order_by(PublishedAgentUsage.date.desc())
        )
        records = list(result.scalars().all())

        # Aggregate stats
        total_queries = sum(r.query_count for r in records)
        total_successful = sum(r.successful_count for r in records)
        total_failed = sum(r.failed_count for r in records)
        total_tokens = sum(r.total_tokens for r in records)
        total_response_time = sum(r.total_response_time_ms for r in records)

        avg_response_time = (
            total_response_time / total_queries if total_queries > 0 else 0
        )

        # Build daily breakdown
        daily_breakdown = [
            {
                "date": r.date.strftime("%Y-%m-%d"),
                "queries": r.query_count,
                "successful": r.successful_count,
                "failed": r.failed_count,
                "avg_response_ms": r.avg_response_time_ms,
            }
            for r in records
        ]

        return {
            "agent_id": agent_id,
            "agent_name": config.name,
            "period_days": days,
            "total_queries": total_queries,
            "successful_queries": total_successful,
            "failed_queries": total_failed,
            "success_rate": (
                (total_successful / total_queries * 100) if total_queries > 0 else 0
            ),
            "total_tokens": total_tokens,
            "avg_response_time_ms": round(avg_response_time, 2),
            "daily_breakdown": daily_breakdown,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _count_user_agents(self, user_id: int) -> int:
        """Count published agents for a user."""
        result = await self.db.execute(
            select(func.count(PublishedAgentConfig.id)).where(
                PublishedAgentConfig.user_id == user_id
            )
        )
        return result.scalar() or 0

    async def _get_user_connection(self, user_id: int) -> Optional[UserConnection]:
        """Get user's database connection."""
        result = await self.db.execute(
            select(UserConnection).where(
                UserConnection.user_id == user_id
            )
        )
        return result.scalar_one_or_none()


# =============================================================================
# Embed Code Generation
# =============================================================================

def generate_embed_code(
    agent_id: str,
    agent_name: str,
    api_key: str,
    backend_url: Optional[str] = None
) -> str:
    """
    Generate ChatKit embed code for a published agent.

    Args:
        agent_id: Agent UUID
        agent_name: Agent name for display
        api_key: Full API key
        backend_url: Backend URL (defaults to env var or localhost)

    Returns:
        HTML/JS code snippet
    """
    # Get backend URL from env or use default
    if backend_url is None:
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    endpoint = f"{backend_url}/api/v1/public/chat"

    return f'''<!-- {agent_name} Chat Widget -->
<!-- Generated: {datetime.utcnow().isoformat()}Z -->

<div id="chat-widget-{agent_id[:8]}"></div>

<script src="https://cdn.openai.com/chatkit/v1/chatkit.min.js"></script>
<script>
(function() {{
  const API_KEY = '{api_key}';
  const ENDPOINT = '{endpoint}';

  const chatkit = new ChatKit({{
    container: '#chat-widget-{agent_id[:8]}',
    api: {{
      url: ENDPOINT,
      fetch: async (url, options) => {{
        const response = await fetch(url, {{
          ...options,
          headers: {{
            ...options.headers,
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json'
          }}
        }});
        return response;
      }}
    }},
    theme: {{
      colorScheme: 'light'
    }},
    header: {{
      enabled: true,
      title: {{ text: '{agent_name}' }}
    }},
    composer: {{
      placeholder: 'Ask a question...'
    }},
    disclaimer: {{
      text: 'Powered by AI'
    }}
  }});
}})();
</script>'''
