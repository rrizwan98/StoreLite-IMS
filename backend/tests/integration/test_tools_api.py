"""
Integration tests for GET /api/tools endpoint.

TDD Phase: RED - Tests for viewing available system tools (US1).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestGetSystemTools:
    """Integration tests for GET /api/tools endpoint"""

    @pytest.mark.integration
    def test_get_all_tools_returns_list(self, client):
        """Should return list of all system tools"""
        response = client.get("/api/tools")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # gmail, analytics, export

    @pytest.mark.integration
    def test_get_tools_includes_gmail(self, client):
        """Should include Gmail tool in response"""
        response = client.get("/api/tools")
        assert response.status_code == 200

        data = response.json()
        gmail_tools = [t for t in data if t["id"] == "gmail"]
        assert len(gmail_tools) == 1

        gmail = gmail_tools[0]
        assert gmail["name"] == "Gmail"
        assert gmail["auth_type"] == "oauth"
        assert gmail["category"] == "communication"
        assert gmail["is_enabled"] is True

    @pytest.mark.integration
    def test_get_tools_includes_analytics(self, client):
        """Should include Analytics tool in response"""
        response = client.get("/api/tools")
        assert response.status_code == 200

        data = response.json()
        analytics_tools = [t for t in data if t["id"] == "analytics"]
        assert len(analytics_tools) == 1

        analytics = analytics_tools[0]
        assert analytics["name"] == "Analytics"
        assert analytics["auth_type"] == "none"
        assert analytics["category"] == "insights"

    @pytest.mark.integration
    def test_get_tools_includes_export_beta(self, client):
        """Should include Export tool marked as beta"""
        response = client.get("/api/tools")
        assert response.status_code == 200

        data = response.json()
        export_tools = [t for t in data if t["id"] == "export"]
        assert len(export_tools) == 1

        export = export_tools[0]
        assert export["name"] == "Export"
        assert export["is_beta"] is True
        assert export["is_enabled"] is False

    @pytest.mark.integration
    def test_get_tools_required_fields(self, client):
        """All tools should have required fields"""
        response = client.get("/api/tools")
        assert response.status_code == 200

        required_fields = ["id", "name", "description", "icon", "category", "auth_type", "is_enabled", "is_beta"]

        data = response.json()
        for tool in data:
            for field in required_fields:
                assert field in tool, f"Tool missing field: {field}"

    @pytest.mark.integration
    def test_get_tools_filter_enabled(self, client):
        """Should filter to only enabled tools when enabled=true"""
        response = client.get("/api/tools?enabled=true")
        assert response.status_code == 200

        data = response.json()
        # All returned tools should be enabled and not beta
        for tool in data:
            assert tool["is_enabled"] is True
            assert tool["is_beta"] is False

    @pytest.mark.integration
    def test_get_tools_filter_category(self, client):
        """Should filter tools by category"""
        response = client.get("/api/tools?category=communication")
        assert response.status_code == 200

        data = response.json()
        # All returned tools should be in the communication category
        for tool in data:
            assert tool["category"] == "communication"

    @pytest.mark.integration
    def test_get_tools_filter_invalid_category(self, client):
        """Should return empty list for invalid category"""
        response = client.get("/api/tools?category=nonexistent")
        assert response.status_code == 200

        data = response.json()
        assert data == []


class TestGetToolById:
    """Integration tests for GET /api/tools/{tool_id} endpoint"""

    @pytest.mark.integration
    def test_get_tool_by_id_gmail(self, client):
        """Should return Gmail tool by ID"""
        response = client.get("/api/tools/gmail")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "gmail"
        assert data["name"] == "Gmail"
        assert data["auth_type"] == "oauth"

    @pytest.mark.integration
    def test_get_tool_by_id_analytics(self, client):
        """Should return Analytics tool by ID"""
        response = client.get("/api/tools/analytics")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "analytics"
        assert data["name"] == "Analytics"

    @pytest.mark.integration
    def test_get_tool_by_id_not_found(self, client):
        """Should return 404 for unknown tool ID"""
        response = client.get("/api/tools/unknown-tool")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data


class TestConnectTool:
    """Integration tests for POST /api/tools/{tool_id}/connect endpoint"""

    @pytest.mark.integration
    def test_connect_tool_requires_auth(self, client):
        """Should require authentication"""
        response = client.post("/api/tools/gmail/connect")
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_connect_tool_not_found(self, client, auth_headers):
        """Should return 404 for unknown tool"""
        response = client.post("/api/tools/unknown-tool/connect", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_connect_none_auth_tool(self, client, auth_headers):
        """Should connect tool with no auth required"""
        response = client.post("/api/tools/analytics/connect", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["is_connected"] is True

    @pytest.mark.integration
    def test_connect_oauth_tool_returns_redirect(self, client, auth_headers):
        """OAuth tools should return redirect URL"""
        response = client.post("/api/tools/gmail/connect", headers=auth_headers)
        # Either returns success with redirect URL or handles OAuth flow
        assert response.status_code in [200, 202]


class TestDisconnectTool:
    """Integration tests for POST /api/tools/{tool_id}/disconnect endpoint"""

    @pytest.mark.integration
    def test_disconnect_tool_requires_auth(self, client):
        """Should require authentication"""
        response = client.post("/api/tools/gmail/disconnect")
        assert response.status_code in [401, 403]

    @pytest.mark.integration
    def test_disconnect_tool_not_found(self, client, auth_headers):
        """Should return 404 for unknown tool"""
        response = client.post("/api/tools/unknown-tool/disconnect", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    def test_disconnect_connected_tool(self, client, auth_headers):
        """Should disconnect a connected tool"""
        # First connect
        client.post("/api/tools/analytics/connect", headers=auth_headers)

        # Then disconnect
        response = client.post("/api/tools/analytics/disconnect", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["is_connected"] is False
