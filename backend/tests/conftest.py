"""
Pytest configuration and fixtures for IMS API tests
"""

import asyncio
import pytest
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
import os

# Use in-memory SQLite for testing with proper async setup
# Note: Using file-based SQLite for better compatibility with async/await
import tempfile
import os as _os
_temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
_temp_db.close()
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_temp_db.name.replace(chr(92), '/')}"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create test database engine and session"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async_session_local = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session_local() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield async_session_local

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client(test_db):
    """Create a test client for FastAPI application"""
    return TestClient(app)


@pytest.fixture
async def db_session(test_db):
    """Get a database session for tests"""
    async with test_db() as session:
        yield session


# Test markers
def pytest_configure(config):
    """Register pytest markers"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "contract: mark test as contract test")
