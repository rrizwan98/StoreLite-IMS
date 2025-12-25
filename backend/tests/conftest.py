"""
Pytest configuration and fixtures for IMS API tests
"""

import asyncio
import pytest
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import httpx
from starlette.testclient import TestClient
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
async def async_client(test_db):
    """Create an async test client for FastAPI application"""
    # Use ASGITransport for httpx 0.28+ compatibility with Starlette 0.35+
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
def client(test_db):
    """Create a sync test client wrapper for FastAPI application (runs async under the hood)"""
    import asyncio

    transport = httpx.ASGITransport(app=app)

    class SyncClientWrapper:
        """Wrapper that provides sync-like interface over async client"""
        def __init__(self):
            self._client = httpx.AsyncClient(transport=transport, base_url="http://testserver")

        def _run(self, coro):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(coro)

        def get(self, url, **kwargs):
            return self._run(self._client.get(url, **kwargs))

        def post(self, url, **kwargs):
            return self._run(self._client.post(url, **kwargs))

        def put(self, url, **kwargs):
            return self._run(self._client.put(url, **kwargs))

        def patch(self, url, **kwargs):
            return self._run(self._client.patch(url, **kwargs))

        def delete(self, url, **kwargs):
            return self._run(self._client.delete(url, **kwargs))

        def close(self):
            self._run(self._client.aclose())

    wrapper = SyncClientWrapper()
    yield wrapper
    wrapper.close()


@pytest.fixture
async def db_session(test_db):
    """Get a database session for tests"""
    async with test_db() as session:
        yield session


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for test user"""
    # Create test user
    signup_response = client.post("/auth/signup", json={
        "email": "testuser@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })

    # If user already exists, login instead
    if signup_response.status_code == 400:
        login_response = client.post("/auth/login", json={
            "email": "testuser@example.com",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
    else:
        token = signup_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_user_headers(client):
    """Get authentication headers for a different test user"""
    # Create different test user
    signup_response = client.post("/auth/signup", json={
        "email": "otheruser@example.com",
        "password": "otherpass123",
        "full_name": "Other User"
    })

    # If user already exists, login instead
    if signup_response.status_code == 400:
        login_response = client.post("/auth/login", json={
            "email": "otheruser@example.com",
            "password": "otherpass123"
        })
        token = login_response.json()["access_token"]
    else:
        token = signup_response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


# Test markers
def pytest_configure(config):
    """Register pytest markers"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "contract: mark test as contract test")
