"""
T013: Unit Tests for Agent Orchestration (December 2025)

Tests for OpenAIAgent class:
- Agent initialization with LiteLLM Gemini
- Tool discovery with retry logic and exponential backoff
- Message processing with session persistence
- Error handling (connection, model behavior, max turns)
- Confirmation flow integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
import asyncio

from app.agents.agent import OpenAIAgent
from app.agents.tools_client import MCPClient
from app.agents.session_manager import SessionManager
from app.agents.confirmation_flow import ConfirmationFlow

# Mock function_tool since it's used in agent.py but not imported there
def function_tool(func):
    """Mock decorator for function_tool"""
    return func


class TestAgentInitialization:
    """Test OpenAI Agent initialization"""

    def test_init_with_gemini_api_key(self):
        """Test: Agent initializes with GEMINI_API_KEY from env or param"""
        # Arrange
        api_key = "test-gemini-key-123"

        # Act
        agent = OpenAIAgent(gemini_api_key=api_key)

        # Assert
        assert agent.gemini_api_key == api_key
        assert agent.model_name == "gemini/gemini-2.0-flash-lite-preview-02-05"
        assert agent.temperature == 0.7
        assert agent.max_tokens == 8192

    def test_init_with_custom_parameters(self):
        """Test: Agent initializes with custom temperature and max_tokens"""
        # Arrange
        api_key = "test-key"
        temperature = 0.3
        max_tokens = 4096

        # Act
        agent = OpenAIAgent(
            gemini_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Assert
        assert agent.temperature == temperature
        assert agent.max_tokens == max_tokens

    def test_init_missing_api_key_raises_error(self):
        """Test: Agent raises ValueError if GEMINI_API_KEY not provided"""
        # Arrange & Act & Assert
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                OpenAIAgent()

            assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_init_with_custom_session_manager(self):
        """Test: Agent accepts custom SessionManager"""
        # Arrange
        api_key = "test-key"
        mock_manager = MagicMock(spec=SessionManager)

        # Act
        agent = OpenAIAgent(
            gemini_api_key=api_key,
            session_manager=mock_manager
        )

        # Assert
        assert agent.session_manager == mock_manager

    def test_init_with_custom_tools_client(self):
        """Test: Agent accepts custom MCPClient"""
        # Arrange
        api_key = "test-key"
        mock_client = MagicMock(spec=MCPClient)

        # Act
        agent = OpenAIAgent(
            gemini_api_key=api_key,
            tools_client=mock_client
        )

        # Assert
        assert agent.tools_client == mock_client


class TestToolDiscovery:
    """Test tool discovery with retry logic"""

    @pytest.mark.asyncio
    async def test_discover_and_register_tools_success(self):
        """Test: discover_and_register_tools() successfully discovers and registers tools"""
        # Arrange
        api_key = "test-key"
        mock_tools = [
            {
                "name": "inventory_add_item",
                "description": "Add item to inventory",
                "schema": {"type": "object"}
            },
            {
                "name": "billing_create_bill",
                "description": "Create bill",
                "schema": {"type": "object"}
            }
        ]

        agent = OpenAIAgent(gemini_api_key=api_key)
        agent.tools_client = MagicMock()
        agent.tools_client.discover_tools.return_value = mock_tools

        # Patch function_tool before running the test
        with patch.dict('sys.modules', {'agents': MagicMock()}):
            # Mock LiteLLMModel
            with patch('app.agents.agent.LitellmModel') as MockModel:
                mock_model_instance = MagicMock()
                MockModel.return_value = mock_model_instance

                # Mock Agent
                with patch('app.agents.agent.Agent'):
                    # Mock function_tool in the module namespace
                    import app.agents.agent as agent_module
                    original_function_tool = getattr(agent_module, 'function_tool', None)
                    agent_module.function_tool = function_tool

                    try:
                        # Act
                        tools = await agent.discover_and_register_tools()

                        # Assert
                        assert len(tools) == 2
                        assert tools[0]["name"] == "inventory_add_item"
                        assert agent._model == mock_model_instance
                        assert agent.agent is not None
                    finally:
                        # Restore original
                        if original_function_tool:
                            agent_module.function_tool = original_function_tool

    @pytest.mark.asyncio
    async def test_discover_tools_with_retry_on_connection_error(self):
        """Test: Retries tool discovery with exponential backoff on connection error"""
        # Arrange
        api_key = "test-key"
        mock_tools = [{"name": "test_tool", "description": "Test"}]

        agent = OpenAIAgent(gemini_api_key=api_key)
        agent.tools_client = MagicMock()

        # First call fails, second succeeds
        agent.tools_client.discover_tools.side_effect = [
            ConnectionError("Connection failed"),
            mock_tools
        ]

        with patch('app.agents.agent.LitellmModel'):
            with patch('app.agents.agent.Agent'):
                # Mock function_tool in the module namespace
                import app.agents.agent as agent_module
                original_function_tool = getattr(agent_module, 'function_tool', None)
                agent_module.function_tool = function_tool

                try:
                    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                        # Act
                        tools = await agent.discover_and_register_tools(max_retries=3)

                        # Assert
                        assert len(tools) == 1
                        assert agent.tools_client.discover_tools.call_count == 2
                        # Verify exponential backoff: first sleep should be 2^0 = 1
                        mock_sleep.assert_called_once_with(1)
                finally:
                    # Restore original
                    if original_function_tool:
                        agent_module.function_tool = original_function_tool

    @pytest.mark.asyncio
    async def test_discover_tools_max_retries_exceeded(self):
        """Test: Raises ConnectionError after max retries exceeded"""
        # Arrange
        api_key = "test-key"

        agent = OpenAIAgent(gemini_api_key=api_key)
        agent.tools_client = MagicMock()
        agent.tools_client.discover_tools.side_effect = ConnectionError("Connection failed")

        with patch('app.agents.agent.LitellmModel'):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                # Act & Assert
                with pytest.raises(ConnectionError) as exc_info:
                    await agent.discover_and_register_tools(max_retries=2)

                assert "Unable to reach local MCP server" in str(exc_info.value)
                assert agent.tools_client.discover_tools.call_count == 2

    @pytest.mark.asyncio
    async def test_discover_tools_empty_list(self):
        """Test: Handles empty tool list gracefully"""
        # Arrange
        api_key = "test-key"

        agent = OpenAIAgent(gemini_api_key=api_key)
        agent.tools_client = MagicMock()
        agent.tools_client.discover_tools.return_value = []

        with patch('app.agents.agent.LitellmModel'):
            with patch('app.agents.agent.Agent'):
                # Act
                tools = await agent.discover_and_register_tools()

                # Assert
                assert tools == []
                assert agent._discovered_tools == []

    @pytest.mark.asyncio
    async def test_discover_tools_model_initialization_error(self):
        """Test: Raises error if LiteLLMModel initialization fails"""
        # Arrange
        api_key = "test-key"

        agent = OpenAIAgent(gemini_api_key=api_key)

        with patch('app.agents.agent.LitellmModel', side_effect=Exception("API error")):
            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await agent.discover_and_register_tools()

            assert "Model initialization failed" in str(exc_info.value)


class TestMessageProcessing:
    """Test user message processing"""

    @pytest.mark.asyncio
    async def test_process_message_empty_message(self):
        """Test: Empty message returns default response"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()

        # Act
        result = await agent.process_message("session-1", "   ")

        # Assert
        assert result["status"] == "success"
        assert "How can I help" in result["response"]
        assert result["session_id"] == "session-1"

    @pytest.mark.asyncio
    async def test_process_message_creates_new_session_if_not_exists(self):
        """Test: Creates new session if not found in database"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()
        agent.confirmation_flow = MagicMock()
        agent.confirmation_flow.get_pending_confirmation.return_value = None
        agent.confirmation_flow.is_destructive_action.return_value = False

        mock_new_session = MagicMock()
        mock_new_session.conversation_history = []

        agent.session_manager.get_session.return_value = None
        agent.session_manager.create_session.return_value = mock_new_session
        agent.session_manager.save_session = AsyncMock()

        agent.agent = MagicMock()

        mock_result = MagicMock()
        mock_result.output = "Added item successfully"

        with patch('app.agents.agent.Runner') as MockRunner:
            MockRunner.run_async = AsyncMock(return_value=mock_result)

            # Act
            result = await agent.process_message("new-session", "Add 10kg sugar")

            # Assert
            agent.session_manager.create_session.assert_called_once_with("new-session")
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_message_loads_existing_session(self):
        """Test: Loads existing session from database"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()
        agent.confirmation_flow = MagicMock()
        agent.confirmation_flow.get_pending_confirmation.return_value = None
        agent.confirmation_flow.is_destructive_action.return_value = False

        mock_session = MagicMock()
        mock_session.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        agent.session_manager.get_session.return_value = mock_session
        agent.session_manager.save_session = AsyncMock()
        agent.agent = MagicMock()

        mock_result = MagicMock()
        mock_result.output = "Found 5 items"

        with patch('app.agents.agent.Runner') as MockRunner:
            MockRunner.run_async = AsyncMock(return_value=mock_result)

            # Act
            result = await agent.process_message("existing-session", "List inventory")

            # Assert
            agent.session_manager.get_session.assert_called_with("existing-session")
            agent.session_manager.create_session.assert_not_called()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_process_message_handles_pending_confirmation(self):
        """Test: Handles pending confirmation flow"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()
        agent.confirmation_flow = MagicMock()

        mock_session = MagicMock()
        mock_session.conversation_history = []

        agent.session_manager.get_session.return_value = mock_session

        pending = {"action_type": "bill_creation", "details": {}}
        agent.confirmation_flow.get_pending_confirmation.return_value = pending
        agent.confirmation_flow.handle_confirmation_response.return_value = True
        agent.confirmation_flow.clear_pending_confirmation = MagicMock()

        # Act
        result = await agent.process_message("session-1", "yes")

        # Assert
        agent.confirmation_flow.handle_confirmation_response.assert_called_once_with("yes")
        agent.confirmation_flow.clear_pending_confirmation.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_model_behavior_error(self):
        """Test: Handles ModelBehaviorError gracefully"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()
        agent.confirmation_flow = MagicMock()
        agent.confirmation_flow.get_pending_confirmation.return_value = None
        agent.confirmation_flow.is_destructive_action.return_value = False

        mock_session = MagicMock()
        mock_session.conversation_history = []

        agent.session_manager.get_session.return_value = mock_session
        agent.session_manager.save_session = AsyncMock()
        agent.agent = MagicMock()

        # Mock ModelBehaviorError
        with patch('app.agents.agent.Runner') as MockRunner:
            from agents.exceptions import ModelBehaviorError
            MockRunner.run_async = AsyncMock(
                side_effect=ModelBehaviorError("Invalid output")
            )

            # Act
            result = await agent.process_message("session-1", "Add item")

            # Assert
            assert result["status"] == "error"
            assert "rephra" in result["response"].lower()  # Covers "rephrase" and "rephrasing"

    @pytest.mark.asyncio
    async def test_process_message_max_turns_exceeded(self):
        """Test: Handles MaxTurnsExceeded exception"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()
        agent.confirmation_flow = MagicMock()
        agent.confirmation_flow.get_pending_confirmation.return_value = None
        agent.confirmation_flow.is_destructive_action.return_value = False

        mock_session = MagicMock()
        mock_session.conversation_history = []

        agent.session_manager.get_session.return_value = mock_session
        agent.session_manager.save_session = AsyncMock()
        agent.agent = MagicMock()

        # Mock MaxTurnsExceeded
        with patch('app.agents.agent.Runner') as MockRunner:
            from agents.exceptions import MaxTurnsExceeded
            MockRunner.run_async = AsyncMock(
                side_effect=MaxTurnsExceeded("Max turns exceeded")
            )

            # Act
            result = await agent.process_message("session-1", "Complex query")

            # Assert
            assert result["status"] == "error"
            assert "simpler" in result["response"].lower()

    @pytest.mark.asyncio
    async def test_process_message_saves_conversation_history(self):
        """Test: Saves conversation history to database"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        agent.session_manager = AsyncMock()
        agent.confirmation_flow = MagicMock()
        agent.confirmation_flow.get_pending_confirmation.return_value = None
        agent.confirmation_flow.is_destructive_action.return_value = False

        mock_session = MagicMock()
        original_history = [{"role": "user", "content": "Previous"}]
        mock_session.conversation_history = original_history

        agent.session_manager.get_session.return_value = mock_session
        agent.session_manager.save_session = AsyncMock()
        agent.agent = MagicMock()

        mock_result = MagicMock()
        mock_result.output = "Done"

        with patch('app.agents.agent.Runner') as MockRunner:
            MockRunner.run_async = AsyncMock(return_value=mock_result)

            # Act
            result = await agent.process_message("session-1", "Add item")

            # Assert
            agent.session_manager.save_session.assert_called_once()
            call_args = agent.session_manager.save_session.call_args
            saved_history = call_args[0][1]
            assert len(saved_history) == 3  # Original + user + assistant
            assert saved_history[1]["role"] == "user"
            assert saved_history[2]["role"] == "assistant"


class TestActionDetection:
    """Test destructive action detection"""

    def test_detect_action_type_bill_creation(self):
        """Test: Detects bill creation action"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        tool_calls = [
            {"tool": "billing_create_bill", "arguments": {"amount": 100}}
        ]

        # Act
        action_type = agent._detect_action_type(tool_calls)

        # Assert
        assert action_type == "bill_creation"

    def test_detect_action_type_item_deletion(self):
        """Test: Detects item deletion action"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        tool_calls = [
            {"tool": "inventory_delete_item", "arguments": {"item_id": 1}}
        ]

        # Act
        action_type = agent._detect_action_type(tool_calls)

        # Assert
        assert action_type == "item_deletion"

    def test_detect_action_type_unknown(self):
        """Test: Returns 'unknown_action' for non-destructive tools"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        tool_calls = [
            {"tool": "inventory_list_items", "arguments": {}}
        ]

        # Act
        action_type = agent._detect_action_type(tool_calls)

        # Assert
        assert action_type == "unknown_action"


class TestSystemPromptGeneration:
    """Test system prompt generation"""

    def test_system_prompt_includes_key_instructions(self):
        """Test: System prompt contains key instructions"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")

        # Act
        prompt = agent._generate_system_prompt()

        # Assert
        assert "inventory" in prompt.lower()
        assert "billing" in prompt.lower()
        assert "tools" in prompt.lower()


class TestConversationHistoryFormatting:
    """Test conversation history formatting"""

    def test_format_conversation_history(self):
        """Test: Formats conversation history correctly"""
        # Arrange
        agent = OpenAIAgent(gemini_api_key="test-key")
        history = [
            {"role": "user", "content": "Hello", "timestamp": "2025-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there", "extra_field": "ignored"},
        ]

        # Act
        formatted = agent._format_conversation_history(history)

        # Assert
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello"
        assert "timestamp" not in formatted[0]  # Timestamp removed
        assert "extra_field" not in formatted[1]  # Extra fields removed


# Markers for pytest
pytestmark = pytest.mark.unit
