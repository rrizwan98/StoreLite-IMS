"""
Simple test script to verify agent endpoint is operational.
Tests database connectivity, endpoint availability, and basic request/response structure.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db, get_db, verify_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_initialization():
    """Test that database tables are created successfully."""
    logger.info("Testing database initialization...")
    try:
        await init_db()
        is_connected = await verify_connection()
        assert is_connected, "Database connection failed"
        logger.info("✓ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {str(e)}")
        return False


async def test_agent_endpoint():
    """Test that agent endpoint responds correctly."""
    logger.info("Testing agent endpoint...")
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test health check
            logger.info("  - Testing /agent/health endpoint...")
            response = await client.get("/agent/health")
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
            health_data = response.json()
            logger.info(f"    Agent health: {health_data.get('status')}")

            # Test chat endpoint with valid request structure
            logger.info("  - Testing /agent/chat endpoint...")
            import uuid
            test_chat_session_id = f"chat-test-{uuid.uuid4().hex[:8]}"
            request_data = {
                "session_id": test_chat_session_id,
                "message": "What items do we have in inventory?",
                "metadata": {"user_id": "test-user", "store_name": "Test Store"}
            }

            response = await client.post("/agent/chat", json=request_data)

            # We expect either:
            # - 200 with valid response (if OpenAI API key is valid)
            # - 400/500 with clear error message (if OpenAI API key is invalid, which is expected in test)
            logger.info(f"    Response status: {response.status_code}")

            if response.status_code in [200, 400]:
                response_data = response.json()
                logger.info(f"    Response keys: {list(response_data.keys())}")

                # Validate response structure
                required_fields = ["session_id", "response", "status", "tool_calls"]
                if all(field in response_data for field in required_fields):
                    logger.info(f"✓ Agent endpoint responds with correct structure")
                    logger.info(f"  Status: {response_data.get('status')}")
                    logger.info(f"  Response: {response_data.get('response')[:100] if response_data.get('response') else 'N/A'}...")
                    return True
                else:
                    logger.error(f"✗ Missing required fields in response: {required_fields}")
                    return False
            elif response.status_code == 500:
                logger.warning(f"✗ Server error (500): {response.text}")
                return False
            else:
                logger.error(f"✗ Unexpected status code: {response.status_code}")
                logger.error(f"  Response: {response.text}")
                return False

    except Exception as e:
        logger.error(f"✗ Agent endpoint test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_session_persistence():
    """Test that conversation sessions are persisted."""
    logger.info("Testing session persistence...")
    try:
        import uuid
        from app.agents import SessionManager
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

        # Create an async session
        from app.database import ASYNC_DATABASE_URL, async_session

        async with async_session() as db_session:
            session_manager = SessionManager(db_session, context_size=5)

            # Create a session with unique ID
            test_session_id = f"persistence-test-{uuid.uuid4().hex[:8]}"
            logger.info("  - Creating test session...")
            session_data = await session_manager.create_session(
                session_id=test_session_id,
                metadata={"test": True}
            )
            assert session_data["session_id"] == test_session_id
            logger.info(f"    Created session: {session_data['session_id']}")

            # Save conversation history
            logger.info("  - Saving conversation history...")
            history = [
                {"role": "user", "content": "Add 10kg sugar"},
                {"role": "assistant", "content": "Added successfully"}
            ]
            saved = await session_manager.save_session(test_session_id, history)
            assert saved, "Failed to save session"

            # Retrieve session
            logger.info("  - Retrieving session...")
            retrieved = await session_manager.get_session(test_session_id)
            assert retrieved is not None, "Session not found"
            assert len(retrieved["conversation_history"]) == 2, "History not saved"
            logger.info(f"✓ Session persistence working (history length: {len(retrieved['conversation_history'])})")
            return True

    except Exception as e:
        logger.error(f"✗ Session persistence test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("AGENT ENDPOINT INTEGRATION TESTS")
    logger.info("=" * 60)

    results = {}

    # Test 1: Database
    results["database"] = await test_database_initialization()
    await asyncio.sleep(0.5)

    # Test 2: Session Persistence
    results["session_persistence"] = await test_session_persistence()
    await asyncio.sleep(0.5)

    # Test 3: Endpoint
    results["endpoint"] = await test_agent_endpoint()

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name:30} {status}")

    all_passed = all(results.values())
    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ ALL TESTS PASSED - Endpoint ready for use!")
    else:
        logger.info("✗ Some tests failed - See above for details")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
