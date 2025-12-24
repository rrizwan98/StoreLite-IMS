"""
Unit tests for Google Search Service.

TDD Phase: Tests for the Google Search service using Gemini's search grounding.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.services.google_search import (
    GoogleSearchService,
    GoogleSearchResult,
    SearchSource,
    should_use_google_search,
    strip_tool_prefix,
    GOOGLE_SEARCH_PREFIX,
)


class TestGoogleSearchHelpers:
    """Tests for Google Search helper functions"""

    def test_should_use_google_search_with_prefix(self):
        """Should return True when query has [TOOL:GOOGLE_SEARCH] prefix"""
        query = "[TOOL:GOOGLE_SEARCH] What is the latest Python version?"
        assert should_use_google_search(query) is True

    def test_should_use_google_search_with_prefix_lowercase(self):
        """Should work with lowercase prefix"""
        query = "[tool:google_search] What is the latest Python version?"
        assert should_use_google_search(query) is True

    def test_should_use_google_search_without_prefix(self):
        """Should return False when query has no prefix"""
        query = "How many products are in inventory?"
        assert should_use_google_search(query) is False

    def test_should_use_google_search_with_whitespace(self):
        """Should handle leading whitespace"""
        query = "   [TOOL:GOOGLE_SEARCH] Test query"
        assert should_use_google_search(query) is True

    def test_strip_tool_prefix_removes_prefix(self):
        """Should remove [TOOL:GOOGLE_SEARCH] prefix"""
        query = "[TOOL:GOOGLE_SEARCH] What is the latest Python version?"
        clean = strip_tool_prefix(query)
        assert clean == "What is the latest Python version?"

    def test_strip_tool_prefix_preserves_query_without_prefix(self):
        """Should preserve query when no prefix present"""
        query = "How many products in stock?"
        clean = strip_tool_prefix(query)
        assert clean == query

    def test_strip_tool_prefix_handles_whitespace(self):
        """Should handle whitespace in prefix removal"""
        query = "  [TOOL:GOOGLE_SEARCH]   What is React?  "
        clean = strip_tool_prefix(query)
        assert clean == "What is React?"

    def test_google_search_prefix_constant(self):
        """Prefix constant should be correct"""
        assert GOOGLE_SEARCH_PREFIX == "[TOOL:GOOGLE_SEARCH]"


class TestSearchSource:
    """Tests for SearchSource dataclass"""

    def test_search_source_creation(self):
        """Should create SearchSource with title and URL"""
        source = SearchSource(title="Python.org", url="https://python.org")
        assert source.title == "Python.org"
        assert source.url == "https://python.org"

    def test_search_source_equality(self):
        """SearchSource with same values should be equal"""
        source1 = SearchSource(title="Test", url="https://test.com")
        source2 = SearchSource(title="Test", url="https://test.com")
        assert source1 == source2


class TestGoogleSearchResult:
    """Tests for GoogleSearchResult dataclass"""

    def test_successful_result(self):
        """Should create successful result with sources"""
        result = GoogleSearchResult(
            text="Python 3.12 is the latest version.",
            sources=[
                SearchSource(title="Python.org", url="https://python.org"),
            ],
            search_queries=["latest Python version"],
            success=True,
        )
        assert result.success is True
        assert result.text == "Python 3.12 is the latest version."
        assert len(result.sources) == 1
        assert result.error is None

    def test_failed_result(self):
        """Should create failed result with error"""
        result = GoogleSearchResult(
            text="",
            sources=[],
            search_queries=[],
            success=False,
            error="API key not configured",
        )
        assert result.success is False
        assert result.error == "API key not configured"


class TestGoogleSearchService:
    """Tests for GoogleSearchService class"""

    def test_service_initialization_with_api_key(self):
        """Should initialize with provided API key"""
        service = GoogleSearchService(api_key="test-key")
        assert service.api_key == "test-key"
        assert service.model == "gemini-2.5-flash"

    def test_service_initialization_custom_model(self):
        """Should initialize with custom model"""
        service = GoogleSearchService(api_key="test-key", model="gemini-2.0-flash")
        assert service.model == "gemini-2.0-flash"

    def test_service_initialization_from_env(self):
        """Should read API key from environment variable"""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}):
            service = GoogleSearchService()
            assert service.api_key == "env-key"

    def test_service_no_api_key_warning(self):
        """Should handle missing API key gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove GEMINI_API_KEY if exists
            os.environ.pop("GEMINI_API_KEY", None)
            service = GoogleSearchService(api_key=None)
            assert service.api_key is None

    @pytest.mark.asyncio
    async def test_search_without_api_key(self):
        """Should return error when API key not configured"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)
            service = GoogleSearchService(api_key=None)
            result = await service.search("test query")

            assert result.success is False
            assert "not configured" in result.error.lower()

    def test_format_response_with_sources(self):
        """Should format response with markdown sources"""
        result = GoogleSearchResult(
            text="Python 3.12 is the latest version.",
            sources=[
                SearchSource(title="Python.org", url="https://python.org"),
                SearchSource(title="Python Releases", url="https://python.org/downloads"),
            ],
            search_queries=["latest Python version"],
            success=True,
        )

        service = GoogleSearchService(api_key="test-key")
        formatted = service.format_response_with_sources(result)

        assert "Python 3.12 is the latest version." in formatted
        assert "Sources:" in formatted
        assert "[Python.org](https://python.org)" in formatted
        assert "[Python Releases](https://python.org/downloads)" in formatted

    def test_format_response_with_empty_sources(self):
        """Should handle response with no sources"""
        result = GoogleSearchResult(
            text="Here is some information.",
            sources=[],
            search_queries=["test"],
            success=True,
        )

        service = GoogleSearchService(api_key="test-key")
        formatted = service.format_response_with_sources(result)

        assert "Here is some information." in formatted
        assert "Sources:" not in formatted

    def test_format_response_with_error(self):
        """Should format error response"""
        result = GoogleSearchResult(
            text="",
            sources=[],
            search_queries=[],
            success=False,
            error="API quota exceeded",
        )

        service = GoogleSearchService(api_key="test-key")
        formatted = service.format_response_with_sources(result)

        assert "temporarily unavailable" in formatted.lower()
        assert "API quota exceeded" in formatted

    def test_format_response_deduplicates_sources(self):
        """Should deduplicate sources by URL"""
        result = GoogleSearchResult(
            text="Test response.",
            sources=[
                SearchSource(title="Python.org", url="https://python.org"),
                SearchSource(title="Python Website", url="https://python.org"),  # Duplicate URL
                SearchSource(title="Other Site", url="https://other.com"),
            ],
            search_queries=["test"],
            success=True,
        )

        service = GoogleSearchService(api_key="test-key")
        formatted = service.format_response_with_sources(result)

        # Should only have 2 unique URLs
        assert formatted.count("https://python.org") == 1
        assert formatted.count("https://other.com") == 1

    def test_format_response_no_text(self):
        """Should handle empty text response"""
        result = GoogleSearchResult(
            text="",
            sources=[],
            search_queries=["test"],
            success=True,
        )

        service = GoogleSearchService(api_key="test-key")
        formatted = service.format_response_with_sources(result)

        assert "no results found" in formatted.lower()


class TestGoogleSearchServiceWithMock:
    """Tests for GoogleSearchService with mocked Gemini API"""

    @pytest.fixture
    def mock_gemini_response(self):
        """Create a mock Gemini response with grounding metadata"""
        mock = MagicMock()
        mock.text = "Python 3.12 is the latest stable version."

        # Mock grounding metadata
        grounding = MagicMock()

        # Mock grounding chunks
        chunk1 = MagicMock()
        chunk1.web = MagicMock()
        chunk1.web.title = "Python.org"
        chunk1.web.uri = "https://python.org"

        chunk2 = MagicMock()
        chunk2.web = MagicMock()
        chunk2.web.title = "Python Releases"
        chunk2.web.uri = "https://python.org/downloads"

        grounding.grounding_chunks = [chunk1, chunk2]
        grounding.web_search_queries = ["latest Python version 2024"]

        # Mock candidate
        candidate = MagicMock()
        candidate.grounding_metadata = grounding
        mock.candidates = [candidate]

        return mock

    @pytest.mark.asyncio
    async def test_search_returns_result_with_sources(self, mock_gemini_response):
        """Search should return GoogleSearchResult with sources"""
        with patch("app.services.google_search.GoogleSearchService._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gemini_response)
            mock_get_client.return_value = mock_client

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("What is the latest Python version?")

            assert isinstance(result, GoogleSearchResult)
            assert result.success is True
            assert "Python 3.12" in result.text
            assert len(result.sources) == 2
            assert result.sources[0].url == "https://python.org"

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self):
        """Search should handle timeout gracefully"""
        with patch("app.services.google_search.GoogleSearchService._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=TimeoutError("Request timed out")
            )
            mock_get_client.return_value = mock_client

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("test query")

            assert result.success is False
            assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_search_handles_quota_error(self):
        """Search should handle quota exceeded error"""
        with patch("app.services.google_search.GoogleSearchService._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=Exception("Quota exceeded for resource")
            )
            mock_get_client.return_value = mock_client

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("test query")

            assert result.success is False
            assert "quota" in result.error.lower()

    @pytest.mark.asyncio
    async def test_search_handles_generic_error(self):
        """Search should handle generic errors"""
        with patch("app.services.google_search.GoogleSearchService._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(
                side_effect=Exception("Unknown error")
            )
            mock_get_client.return_value = mock_client

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("test query")

            assert result.success is False
            assert "Unknown error" in result.error

    @pytest.mark.asyncio
    async def test_search_handles_empty_grounding(self):
        """Search should handle response with no grounding metadata"""
        mock_response = MagicMock()
        mock_response.text = "Here is some information."

        candidate = MagicMock()
        candidate.grounding_metadata = None
        mock_response.candidates = [candidate]

        with patch("app.services.google_search.GoogleSearchService._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            service = GoogleSearchService(api_key="test-key")
            result = await service.search("test query")

            assert result.success is True
            assert result.text == "Here is some information."
            assert len(result.sources) == 0
