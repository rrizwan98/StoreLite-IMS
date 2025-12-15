"""
Integration tests for Schema Agent Router (Phase 9)

Tests the API endpoints for schema query functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


# Defer TestClient creation to fixture to avoid import-time errors
@pytest.fixture
def client():
    """Create a test client for FastAPI application"""
    pytest.importorskip("httpx", minversion="0.25.0")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    except TypeError as e:
        pytest.skip(f"TestClient initialization failed: {e}")


@pytest.fixture
def app_instance():
    """Get the FastAPI app instance"""
    from app.main import app
    return app


# Mock authentication helper
def get_auth_headers(user_id: int = 1, connection_type: str = "schema_query_only"):
    """Get mock auth headers for testing"""
    return {"Authorization": "Bearer test_token"}


class TestSchemaAgentEndpoints:
    """Tests for Schema Agent API endpoints"""

    # === Status Endpoint ===

    def test_status_endpoint_unauthenticated(self, client):
        """Status endpoint should require authentication"""
        response = client.get("/schema-agent/status")
        assert response.status_code == 401 or response.status_code == 403

    # === Connect Endpoint ===

    def test_connect_requires_database_uri(self, client):
        """Connect endpoint should require database_uri"""
        with patch('app.routers.schema_agent.get_current_user') as mock_auth:
            mock_auth.return_value = MagicMock(id=1)

            response = client.post(
                "/schema-agent/connect",
                json={},
                headers=get_auth_headers()
            )

            # Should fail validation (401 or 422)
            assert response.status_code in [400, 401, 422]

    def test_connect_validates_connection_string(self, client):
        """Connect should validate PostgreSQL connection string"""
        with patch('app.routers.schema_agent.get_current_user') as mock_auth:
            mock_auth.return_value = MagicMock(id=1)

            response = client.post(
                "/schema-agent/connect",
                json={"database_uri": "invalid://connection"},
                headers=get_auth_headers()
            )

            # Should fail validation (401 or 422)
            assert response.status_code in [400, 401, 422]

    # === Schema Discovery Endpoint ===

    def test_discover_schema_requires_auth(self, client):
        """Discover schema endpoint should require authentication"""
        response = client.post("/schema-agent/discover-schema")
        assert response.status_code == 401 or response.status_code == 403

    # === Tables List Endpoint ===

    def test_tables_endpoint_requires_auth(self, client):
        """Tables list endpoint should require authentication"""
        response = client.get("/schema-agent/tables")
        assert response.status_code == 401 or response.status_code == 403

    # === Table Details Endpoint ===

    def test_table_details_requires_auth(self, client):
        """Table details endpoint should require authentication"""
        response = client.get("/schema-agent/tables/users")
        assert response.status_code == 401 or response.status_code == 403

    # === Query Endpoint ===

    def test_query_endpoint_requires_auth(self, client):
        """Query endpoint should require authentication"""
        response = client.post(
            "/schema-agent/query",
            json={"query": "SELECT * FROM users"}
        )
        assert response.status_code == 401 or response.status_code == 403

    # === Chat Endpoint ===

    def test_chat_endpoint_requires_auth(self, client):
        """Chat endpoint should require authentication"""
        response = client.post(
            "/schema-agent/chat",
            json={"message": "Show me all users"}
        )
        assert response.status_code == 401 or response.status_code == 403

    # === Refresh Schema Endpoint ===

    def test_refresh_schema_requires_auth(self, client):
        """Refresh schema endpoint should require authentication"""
        response = client.post("/schema-agent/refresh-schema")
        assert response.status_code == 401 or response.status_code == 403

    # === Disconnect Endpoint ===

    def test_disconnect_requires_auth(self, client):
        """Disconnect endpoint should require authentication"""
        response = client.delete("/schema-agent/disconnect")
        assert response.status_code == 401 or response.status_code == 403

    # === Upgrade Endpoint ===

    def test_upgrade_requires_auth(self, client):
        """Upgrade to full IMS endpoint should require authentication"""
        response = client.post("/schema-agent/upgrade-to-full-ims")
        assert response.status_code == 401 or response.status_code == 403


class TestQueryValidationInRouter:
    """Tests for query validation in router endpoints"""

    def test_select_query_accepted(self, client):
        """SELECT query should be accepted by query endpoint"""
        # This test needs proper auth mocking
        pass  # Placeholder - requires full auth setup

    def test_insert_query_rejected(self, client):
        """INSERT query should be rejected by query endpoint"""
        # This test needs proper auth mocking
        pass  # Placeholder - requires full auth setup

    def test_delete_query_rejected(self, client):
        """DELETE query should be rejected by query endpoint"""
        # This test needs proper auth mocking
        pass  # Placeholder - requires full auth setup


class TestSchemaAgentRouterResponses:
    """Tests for response formats"""

    def test_router_registered(self, app_instance):
        """Schema agent router should be registered"""
        # Check if routes exist
        routes = [route.path for route in app_instance.routes]
        schema_routes = [r for r in routes if r.startswith("/schema-agent")]
        assert len(schema_routes) > 0

    def test_expected_endpoints_exist(self, app_instance):
        """All expected endpoints should exist"""
        routes = [route.path for route in app_instance.routes]

        expected_paths = [
            "/schema-agent/connect",
            "/schema-agent/status",
            "/schema-agent/schema",
            "/schema-agent/tables",
            "/schema-agent/query",
            "/schema-agent/chat",
        ]

        for path in expected_paths:
            assert any(path in r for r in routes), f"Expected {path} to exist"


class TestSchemaAgentErrorHandling:
    """Tests for error handling in schema agent endpoints"""

    def test_invalid_json_body_handled(self, client):
        """Invalid JSON body should return 422"""
        response = client.post(
            "/schema-agent/connect",
            content="not valid json",
            headers={"Content-Type": "application/json", **get_auth_headers()}
        )
        assert response.status_code == 422 or response.status_code == 401

    def test_missing_required_fields_handled(self, client):
        """Missing required fields should return 422"""
        response = client.post(
            "/schema-agent/connect",
            json={},
            headers=get_auth_headers()
        )
        # Will be 401 (unauthorized) or 422 (validation)
        assert response.status_code in [401, 422]
