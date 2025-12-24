"""
Unit tests for system tools registry.

TDD Phase: Tests for the tools registry module.
"""

import pytest
import os
import sys

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestSystemToolRegistry:
    """Tests for system tools registry"""

    def test_get_all_system_tools(self):
        """Should return all system tools as list of dicts"""
        from app.tools.registry import get_all_system_tools

        tools = get_all_system_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 3  # gmail, analytics, export

    def test_get_system_tool_gmail(self):
        """Should return Gmail tool by ID"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("gmail")
        assert tool is not None
        assert tool.id == "gmail"
        assert tool.name == "Gmail"
        assert tool.auth_type == "oauth"
        assert tool.is_enabled is True

    def test_get_system_tool_not_found(self):
        """Should return None for unknown tool ID"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("unknown-tool")
        assert tool is None

    def test_get_enabled_tools(self):
        """Should return only enabled, non-beta tools"""
        from app.tools.registry import get_enabled_tools

        tools = get_enabled_tools()
        assert isinstance(tools, list)

        # All returned tools should be enabled and not beta
        for tool in tools:
            assert tool["is_enabled"] is True
            assert tool["is_beta"] is False

    def test_get_tools_by_category(self):
        """Should filter tools by category"""
        from app.tools.registry import get_tools_by_category

        comm_tools = get_tools_by_category("communication")
        assert len(comm_tools) >= 1
        assert all(t["category"] == "communication" for t in comm_tools)

        insights_tools = get_tools_by_category("insights")
        assert len(insights_tools) >= 1
        assert all(t["category"] == "insights" for t in insights_tools)

    def test_system_tool_has_required_fields(self):
        """System tools should have all required fields"""
        from app.tools.registry import get_all_system_tools

        required_fields = ["id", "name", "description", "icon", "category", "auth_type", "is_enabled", "is_beta"]

        for tool in get_all_system_tools():
            for field in required_fields:
                assert field in tool, f"Tool missing field: {field}"

    def test_gmail_is_oauth(self):
        """Gmail tool should require OAuth"""
        from app.tools.registry import get_system_tool

        gmail = get_system_tool("gmail")
        assert gmail.auth_type == "oauth"

    def test_analytics_is_no_auth(self):
        """Analytics tool should not require auth"""
        from app.tools.registry import get_system_tool

        analytics = get_system_tool("analytics")
        assert analytics.auth_type == "none"

    def test_export_is_beta(self):
        """Export tool should be marked as beta"""
        from app.tools.registry import get_system_tool

        export = get_system_tool("export")
        assert export is not None
        assert export.is_beta is True
        assert export.is_enabled is False


class TestGoogleSearchToolRegistry:
    """Tests for Google Search tool in registry"""

    def test_google_search_in_registry(self):
        """Google Search should be registered in SYSTEM_TOOLS"""
        from app.tools.registry import SYSTEM_TOOLS

        assert "google_search" in SYSTEM_TOOLS

    def test_google_search_by_id(self):
        """Should return Google Search tool by ID"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("google_search")
        assert tool is not None
        assert tool.id == "google_search"
        assert tool.name == "Google Search"

    def test_google_search_auth_type_none(self):
        """Google Search should have auth_type 'none'"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("google_search")
        assert tool.auth_type == "none"

    def test_google_search_is_enabled(self):
        """Google Search should be enabled by default"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("google_search")
        assert tool.is_enabled is True

    def test_google_search_not_beta(self):
        """Google Search should not be marked as beta"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("google_search")
        assert tool.is_beta is False

    def test_google_search_category_utilities(self):
        """Google Search should be in utilities category"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("google_search")
        assert tool.category == "utilities"

    def test_google_search_has_description(self):
        """Google Search should have a meaningful description"""
        from app.tools.registry import get_system_tool

        tool = get_system_tool("google_search")
        assert tool.description is not None
        assert len(tool.description) > 10
        assert "search" in tool.description.lower()

    def test_google_search_in_enabled_tools(self):
        """Google Search should appear in enabled tools list"""
        from app.tools.registry import get_enabled_tools

        tools = get_enabled_tools()
        tool_ids = [t["id"] for t in tools]
        assert "google_search" in tool_ids
