"""
Integration tests for GET /api/connectors endpoint.

TDD Phase: RED - Tests for viewing user MCP connectors (US1).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestGetUserConnectors:
    """Integration tests for GET /api/connectors endpoint"""

    @pytest.mark.integration
    def test_get_connectors_requires_auth(self, client):
        """Should require authentication"""
        response = client.get("/api/connectors")
        # Expect 401 or 403 for unauthenticated request
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_get_connectors_returns_list(self, client, auth_headers):
        """Should return list of user's connectors"""
        response = client.get("/api/connectors", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.integration
    def test_get_connectors_empty_for_new_user(self, client, auth_headers):
        """New user should have no connectors"""
        response = client.get("/api/connectors", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data == []

    @pytest.mark.integration
    def test_get_connectors_only_own_connectors(self, client, auth_headers, other_user_headers):
        """Should only return connectors for authenticated user"""
        # Create connector for user 1
        client.post("/api/connectors", headers=auth_headers, json={
            "name": "My Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })

        # User 2 should not see user 1's connector
        response = client.get("/api/connectors", headers=other_user_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 0

    @pytest.mark.integration
    def test_get_connectors_required_fields(self, client, auth_headers):
        """Connectors should have required fields in response"""
        # Create a connector first
        client.post("/api/connectors", headers=auth_headers, json={
            "name": "Test Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })

        response = client.get("/api/connectors", headers=auth_headers)
        assert response.status_code == 200

        required_fields = ["id", "name", "server_url", "auth_type", "is_active", "is_verified", "created_at"]

        data = response.json()
        for connector in data:
            for field in required_fields:
                assert field in connector, f"Connector missing field: {field}"

    @pytest.mark.integration
    def test_get_connectors_hides_credentials(self, client, auth_headers):
        """Should not expose auth_config (encrypted credentials) in list"""
        # Create connector with API key
        client.post("/api/connectors", headers=auth_headers, json={
            "name": "Secure Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "api_key",
            "auth_config": {"api_key": "secret-key-123"}
        })

        response = client.get("/api/connectors", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        for connector in data:
            # auth_config should not be in response or should be masked
            if "auth_config" in connector:
                assert connector["auth_config"] is None or "secret" not in str(connector["auth_config"]).lower()

    @pytest.mark.integration
    def test_get_connectors_filter_active(self, client, auth_headers):
        """Should filter by active status"""
        response = client.get("/api/connectors?active=true", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        for connector in data:
            assert connector["is_active"] is True


class TestGetConnectorById:
    """Integration tests for GET /api/connectors/{id} endpoint"""

    @pytest.mark.integration
    def test_get_connector_by_id_success(self, client, auth_headers):
        """Should return connector by ID"""
        # Create a connector
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Test Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # Get by ID
        response = client.get(f"/api/connectors/{connector_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == connector_id
        assert data["name"] == "Test Server"

    @pytest.mark.integration
    def test_get_connector_by_id_not_found(self, client, auth_headers):
        """Should return 404 for non-existent connector"""
        response = client.get("/api/connectors/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_connector_by_id_other_user(self, client, auth_headers, other_user_headers):
        """Should return 404 when accessing another user's connector"""
        # Create connector for user 1
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Private Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # User 2 tries to access
        response = client.get(f"/api/connectors/{connector_id}", headers=other_user_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_get_connector_includes_tools(self, client, auth_headers):
        """Should include discovered_tools when connector is verified"""
        # Create and verify a connector (mock the verification)
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Tool Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # Get connector details
        response = client.get(f"/api/connectors/{connector_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Should have discovered_tools field (even if empty)
        assert "discovered_tools" in data or "tools" in data


class TestCreateConnector:
    """Integration tests for POST /api/connectors endpoint"""

    @pytest.mark.integration
    def test_create_connector_success(self, client, auth_headers):
        """Should create a new connector"""
        response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "New Server",
            "description": "Test description",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "New Server"
        assert data["description"] == "Test description"
        assert data["server_url"] == "https://example.com/mcp"
        assert data["is_active"] is True
        assert data["is_verified"] is False

    @pytest.mark.integration
    def test_create_connector_requires_auth(self, client):
        """Should require authentication"""
        response = client.post("/api/connectors", json={
            "name": "Unauthenticated",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_create_connector_max_limit(self, client, auth_headers):
        """Should enforce 10 connector limit"""
        # Create 10 connectors
        for i in range(10):
            response = client.post("/api/connectors", headers=auth_headers, json={
                "name": f"Server {i+1}",
                "server_url": f"https://example{i}.com/mcp",
                "auth_type": "none"
            })
            assert response.status_code == 201

        # 11th should fail
        response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Overflow Server",
            "server_url": "https://overflow.com/mcp",
            "auth_type": "none"
        })
        assert response.status_code == 400
        assert "10" in response.json()["detail"].lower() or "maximum" in response.json()["detail"].lower()


class TestTestConnection:
    """Integration tests for POST /api/connectors/test endpoint"""

    @pytest.mark.integration
    def test_test_connection_requires_auth(self, client):
        """Should require authentication"""
        response = client.post("/api/connectors/test", json={
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_test_connection_returns_result(self, client, auth_headers):
        """Should return success/failure result"""
        response = client.post("/api/connectors/test", headers=auth_headers, json={
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert "message" in data


class TestUpdateConnector:
    """Integration tests for PUT /api/connectors/{id} endpoint"""

    @pytest.mark.integration
    def test_update_connector_success(self, client, auth_headers):
        """Should update connector"""
        # Create connector
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Original Name",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # Update connector
        response = client.put(f"/api/connectors/{connector_id}", headers=auth_headers, json={
            "name": "Updated Name",
            "description": "New description"
        })
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    @pytest.mark.integration
    def test_update_connector_not_found(self, client, auth_headers):
        """Should return 404 for non-existent connector"""
        response = client.put("/api/connectors/99999", headers=auth_headers, json={
            "name": "Ghost"
        })
        assert response.status_code == 404

    @pytest.mark.integration
    def test_update_connector_other_user(self, client, auth_headers, other_user_headers):
        """Should not update another user's connector"""
        # Create connector for user 1
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "User 1 Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # User 2 tries to update
        response = client.put(f"/api/connectors/{connector_id}", headers=other_user_headers, json={
            "name": "Hijacked"
        })
        assert response.status_code == 404


class TestDeleteConnector:
    """Integration tests for DELETE /api/connectors/{id} endpoint"""

    @pytest.mark.integration
    def test_delete_connector_success(self, client, auth_headers):
        """Should delete connector"""
        # Create connector
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "To Delete",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # Delete connector
        response = client.delete(f"/api/connectors/{connector_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/connectors/{connector_id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.integration
    def test_delete_connector_not_found(self, client, auth_headers):
        """Should return 404 for non-existent connector"""
        response = client.delete("/api/connectors/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_delete_connector_other_user(self, client, auth_headers, other_user_headers):
        """Should not delete another user's connector"""
        # Create connector for user 1
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Protected Server",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]

        # User 2 tries to delete
        response = client.delete(f"/api/connectors/{connector_id}", headers=other_user_headers)
        assert response.status_code == 404


class TestToggleConnector:
    """Integration tests for POST /api/connectors/{id}/toggle endpoint"""

    @pytest.mark.integration
    def test_toggle_connector_success(self, client, auth_headers):
        """Should toggle connector active status"""
        # Create connector (default is_active=True)
        create_response = client.post("/api/connectors", headers=auth_headers, json={
            "name": "Toggle Test",
            "server_url": "https://example.com/mcp",
            "auth_type": "none"
        })
        connector_id = create_response.json()["id"]
        assert create_response.json()["is_active"] is True

        # Toggle off
        toggle_response = client.post(f"/api/connectors/{connector_id}/toggle", headers=auth_headers)
        assert toggle_response.status_code == 200
        assert toggle_response.json()["is_active"] is False

        # Toggle on
        toggle_response = client.post(f"/api/connectors/{connector_id}/toggle", headers=auth_headers)
        assert toggle_response.status_code == 200
        assert toggle_response.json()["is_active"] is True

    @pytest.mark.integration
    def test_toggle_connector_not_found(self, client, auth_headers):
        """Should return 404 for non-existent connector"""
        response = client.post("/api/connectors/99999/toggle", headers=auth_headers)
        assert response.status_code == 404


class TestRefreshConnector:
    """Integration tests for POST /api/connectors/{id}/refresh endpoint"""

    @pytest.mark.integration
    def test_refresh_connector_not_found(self, client, auth_headers):
        """Should return 404 for non-existent connector"""
        response = client.post("/api/connectors/99999/refresh", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_refresh_connector_requires_auth(self, client):
        """Should require authentication"""
        response = client.post("/api/connectors/1/refresh")
        assert response.status_code in [401, 403]


# Auth fixtures are defined in conftest.py
