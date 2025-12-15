"""
Database connection and session management for FastAPI application
"""

import os
from urllib.parse import urlparse, parse_qs
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ims_db")
print(f"DATABASE_URL: {DATABASE_URL}")

# Convert to async URL and handle asyncpg parameters
engine_kwargs = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("postgresql://"):
    # Parse URL to extract query parameters
    parsed = urlparse(DATABASE_URL)
    query_params = parse_qs(parsed.query) if parsed.query else {}

    # Remove query parameters from URL for asyncpg
    base_url = DATABASE_URL.split("?")[0] if "?" in DATABASE_URL else DATABASE_URL
    ASYNC_DATABASE_URL = base_url.replace("postgresql://", "postgresql+asyncpg://")

    # Add SSL settings if present
    if "sslmode" in query_params or "channel_binding" in query_params:
        engine_kwargs["connect_args"] = {
            "ssl": True,
            "server_settings": {
                "application_name": "ims_app",
            }
        }
elif DATABASE_URL.startswith("sqlite://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Default to SQLite if no database is configured
if ASYNC_DATABASE_URL == "postgresql+asyncpg://user:password@localhost:5432/ims_db" or not ASYNC_DATABASE_URL:
    ASYNC_DATABASE_URL = "sqlite+aiosqlite:///ims_dev.db"
    logger.info("Using SQLite for development. Set DATABASE_URL for PostgreSQL.")

# SQLAlchemy setup
engine = create_async_engine(ASYNC_DATABASE_URL, **engine_kwargs)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """Dependency injection for database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def verify_connection():
    """Verify database connection is working"""
    try:
        async with async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


async def cleanup():
    """Cleanup database connections"""
    await engine.dispose()
