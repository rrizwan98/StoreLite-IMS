"""
Agent router - FastAPI endpoints for Phase 5 OpenAI Agents SDK integration.
Provides natural language interface for inventory and billing operations.
"""

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import AgentMessageRequest, AgentMessageResponse, ToolCall
from app.agents import OpenAIAgent, SessionManager, ConfirmationFlow, MCPClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    responses={500: {"description": "Internal server error"}},
)

# Global agent instance (initialized on first request)
_agent: OpenAIAgent = None


async def get_agent() -> OpenAIAgent:
    """Get or initialize the OpenAI Agent instance with LiteLLM Gemini."""
    global _agent

    if _agent is None:
        logger.info("Initializing OpenAI Agent with LiteLLM Gemini 2.0 Flash Lite")

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        print(f"Gemini API Key: {gemini_api_key}")
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY not set in environment")
            raise ValueError("GEMINI_API_KEY environment variable is required")

        mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

        # Initialize components
        mcp_client = MCPClient(
            base_url=mcp_server_url,
            cache_ttl_seconds=int(os.getenv("MCP_TOOL_CACHE_TTL_SECONDS", "300")),
            timeout=10
        )

        confirmation_flow = ConfirmationFlow(
            timeout_seconds=int(os.getenv("AGENT_CONFIRMATION_TIMEOUT_SECONDS", "300"))
        )

        # Create agent with LiteLLM Gemini
        _agent = OpenAIAgent(
            gemini_api_key=gemini_api_key,
            tools_client=mcp_client,
            confirmation_flow=confirmation_flow,
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "8192")),
        )

        # Discover and register tools
        try:
            tools_discovered = await _agent.discover_and_register_tools()
            if tools_discovered:
                logger.info(f"Agent tools registered successfully: {len(tools_discovered)} tools")
            else:
                logger.warning("Agent initialized but no tools were registered")
        except Exception as e:
            logger.error(f"Failed to discover tools: {e}")
            # Continue with agent initialization even if tool discovery fails
            # This allows the server to start even if MCP server is temporarily unavailable

    return _agent


@router.post(
    "/chat-legacy",
    response_model=AgentMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with inventory/billing agent (Legacy endpoint - use /chat for ChatKit)",
    description="Send a natural language message to the agent. Agent will discover available tools, understand intent, and execute operations.",
)
async def chat(
    request: AgentMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentMessageResponse:
    """
    Process user message with OpenAI Agent.

    The agent will:
    1. Discover available MCP tools (inventory, billing operations)
    2. Parse user intent from natural language
    3. Call appropriate tools via MCP server
    4. Return results in natural language

    Args:
        request: Message request with session_id and user message
        db: Database session for conversation persistence

    Returns:
        Agent response with status, response text, and tool calls made

    Raises:
        HTTPException: If session cannot be loaded or agent processing fails
    """
    try:
        logger.info(f"Received chat request for session: {request.session_id}")

        # Get or initialize agent
        agent = await get_agent()

        # Inject session manager with current DB session
        agent.session_manager = SessionManager(
            db_session=db,
            context_size=int(os.getenv("SESSION_CONTEXT_SIZE", "5"))
        )

        # Process message with agent
        result = await agent.process_message(
            session_id=request.session_id,
            user_message=request.message,
        )

        # Handle error responses - return as successful response with error status
        # This allows clients to handle agent errors gracefully
        if result.get("status") == "error":
            logger.warning(f"Agent returned error status: {result.get('response')}")
            # Don't raise exception - return error as part of response
            tool_calls_data = result.get("tool_calls", [])
            tool_calls = [
                ToolCall(
                    tool=tc.get("name", "unknown"),
                    arguments=tc.get("arguments", {}),
                    result=tc.get("result"),
                )
                for tc in tool_calls_data
            ]

            response = AgentMessageResponse(
                session_id=request.session_id,
                response=result.get("response", "An error occurred"),
                status=result.get("status", "error"),
                tool_calls=tool_calls,
            )
            return response

        # Convert tool calls to response schema
        tool_calls_data = result.get("tool_calls", [])
        tool_calls = [
            ToolCall(
                tool=tc.get("name", "unknown"),
                arguments=tc.get("arguments", {}),
                result=tc.get("result"),
            )
            for tc in tool_calls_data
        ]

        response = AgentMessageResponse(
            session_id=request.session_id,
            response=result.get("response", "No response generated"),
            status=result.get("status", "success"),
            tool_calls=tool_calls,
        )

        logger.info(f"Chat response: status={response.status}, tools_called={len(response.tool_calls)}")
        return response

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your request. Please try again."
        )


@router.get(
    "/health",
    summary="Agent service health check",
    description="Check if agent service is ready and MCP server is reachable"
)
async def agent_health():
    """
    Health check endpoint for agent service.

    Returns:
        Status of agent and MCP server connectivity
    """
    try:
        agent = await get_agent()

        # Test MCP connectivity
        mcp_healthy = False
        if agent.tools_client:
            try:
                tools = agent.tools_client.discover_tools()
                mcp_healthy = len(tools) > 0
            except Exception as e:
                logger.warning(f"MCP health check failed: {str(e)}")

        return {
            "status": "ok" if mcp_healthy else "degraded",
            "agent_initialized": agent.agent is not None,
            "mcp_server": "reachable" if mcp_healthy else "unreachable",
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "agent_initialized": False,
            "mcp_server": "unknown",
            "error": str(e),
        }
