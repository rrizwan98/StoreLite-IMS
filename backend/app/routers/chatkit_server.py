"""
Pure OpenAI ChatKit Server Integration

Uses the official openai-chatkit Python SDK (chatkit.server.ChatKitServer)
Connects ChatKit frontend to the IMS agent backend.
Updated: Force reload trigger
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, AsyncIterator, List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from starlette.responses import Response
from chatkit.server import (
    ChatKitServer,
    Store,
    Thread,
    ThreadMetadata,
    ThreadItem,
    UserMessageItem,
    ClientToolCallItem,
    ThreadStreamEvent,
)
from chatkit.types import (
    AssistantMessageContentPartTextDelta,
    AssistantMessageContentPartDone,
    ThreadItemDoneEvent,
    ThreadItemAddedEvent,
    AssistantMessageItem,
    AssistantMessageContent,
    # Native thinking/reasoning types
    ThoughtTask,
    WorkflowTaskAdded,
    WorkflowTaskUpdated,
)

from app.agents import OpenAIAgent, MCPClient, ConfirmationFlow
from app.database import get_db
from app.services.rate_limiter import get_rate_limiter
from app.services.auth_service import decode_token, get_user_by_id

logger = logging.getLogger(__name__)


async def extract_user_id_from_request(request: Request) -> Optional[int]:
    """
    Extract user_id from Authorization header in ChatKit requests.
    Returns None if no valid token is found (for backwards compatibility).
    """
    try:
        # Get Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header[7:]  # Remove "Bearer " prefix
        token_data = decode_token(token)

        if not token_data:
            return None

        return token_data.user_id
    except Exception as e:
        logger.warning(f"Failed to extract user_id from auth header: {e}")
        return None

router = APIRouter(prefix="/agent", tags=["chatkit"])


class SimpleStore(Store):
    """Simple in-memory store for ChatKit threads and messages."""
    
    def __init__(self):
        self._threads: dict[str, ThreadMetadata] = {}
        self._items: dict[str, list[ThreadItem]] = {}
        self._attachments: dict[str, Any] = {}
    
    def generate_thread_id(self, context: Any) -> str:
        import uuid
        return f"thread-{uuid.uuid4().hex[:12]}"
    
    def generate_item_id(self, item_type: str, thread: ThreadMetadata, context: Any) -> str:
        import uuid
        return f"{item_type}-{uuid.uuid4().hex[:12]}"
    
    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        self._threads[thread.id] = thread
        if thread.id not in self._items:
            self._items[thread.id] = []
    
    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata | None:
        # Auto-create thread if it doesn't exist
        if thread_id not in self._threads:
            from datetime import datetime
            new_thread = ThreadMetadata(
                id=thread_id,
                created_at=datetime.now().isoformat(),
            )
            self._threads[thread_id] = new_thread
            self._items[thread_id] = []
        return self._threads.get(thread_id)
    
    async def delete_thread(self, thread_id: str, context: Any) -> None:
        if thread_id in self._threads:
            del self._threads[thread_id]
        if thread_id in self._items:
            del self._items[thread_id]
    
    async def load_threads(
        self, 
        limit: int,
        after: str | None,
        order: str,
        context: Any
    ) -> Any:
        """Return threads as a Page object."""
        from chatkit.types import Page
        threads = list(self._threads.values())
        return Page(data=threads[:limit], has_more=len(threads) > limit)
    
    async def add_thread_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        self._items[thread_id].append(item)
    
    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: Any
    ) -> Any:
        """Return items as a Page object."""
        from chatkit.types import Page
        items = self._items.get(thread_id, [])
        return Page(data=items[:limit], has_more=len(items) > limit)
    
    async def load_item(self, thread_id: str, item_id: str, context: Any) -> ThreadItem | None:
        items = self._items.get(thread_id, [])
        for item in items:
            if hasattr(item, 'id') and item.id == item_id:
                return item
        return None
    
    async def save_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = []
        # Update existing or add new
        items = self._items[thread_id]
        for i, existing in enumerate(items):
            if hasattr(existing, 'id') and hasattr(item, 'id') and existing.id == item.id:
                items[i] = item
                return
        items.append(item)
    
    async def delete_thread_item(self, thread_id: str, item_id: str, context: Any) -> None:
        if thread_id in self._items:
            self._items[thread_id] = [
                item for item in self._items[thread_id]
                if not (hasattr(item, 'id') and item.id == item_id)
            ]
    
    async def save_attachment(self, attachment: Any, context: Any) -> None:
        if hasattr(attachment, 'id'):
            self._attachments[attachment.id] = attachment
    
    async def load_attachment(self, attachment_id: str, context: Any) -> Any:
        return self._attachments.get(attachment_id)
    
    async def delete_attachment(self, attachment_id: str, context: Any) -> None:
        if attachment_id in self._attachments:
            del self._attachments[attachment_id]


class IMSChatKitServer(ChatKitServer):
    """
    IMS-specific ChatKit Server implementation.

    Connects the OpenAI ChatKit frontend to our IMS agent backend.
    Supports user-scoped data isolation via user_id.
    """

    def __init__(self, store: Store):
        super().__init__(store)
        self._agent: OpenAIAgent | None = None
        self._current_user_id: Optional[int] = None  # Set before processing

    def set_user_id(self, user_id: Optional[int]):
        """Set the current user ID for data isolation."""
        self._current_user_id = user_id
    
    async def _get_agent(self) -> OpenAIAgent:
        """Get or initialize the OpenAI Agent."""
        if self._agent is None:
            logger.info("Initializing OpenAI Agent for ChatKit")
            
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is required")
            
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
            
            mcp_client = MCPClient(
                base_url=mcp_server_url,
                cache_ttl_seconds=int(os.getenv("MCP_TOOL_CACHE_TTL_SECONDS", "300")),
                timeout=10
            )
            
            confirmation_flow = ConfirmationFlow(
                timeout_seconds=int(os.getenv("AGENT_CONFIRMATION_TIMEOUT_SECONDS", "300"))
            )
            
            self._agent = OpenAIAgent(
                gemini_api_key=gemini_api_key,
                tools_client=mcp_client,
                confirmation_flow=confirmation_flow,
                temperature=float(os.getenv("AGENT_TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "8192")),
            )
            
            try:
                tools_discovered = await self._agent.discover_and_register_tools()
                if tools_discovered:
                    logger.info(f"Agent tools registered: {len(tools_discovered)} tools")
            except Exception as e:
                logger.error(f"Failed to discover tools: {e}")
        
        return self._agent
    
    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Process user message and yield streaming response events.
        
        Uses native ChatKit thinking UI (WorkflowTaskAdded/Updated with ThoughtTask)
        to show the "Thinking..." lightbulb indicator with collapsible reasoning.
        """
        import uuid
        import time
        import asyncio
        
        try:
            # If no user message, just return
            if input_user_message is None:
                return
            
            agent = await self._get_agent()
            
            # Extract user message text
            user_message = ""
            if hasattr(input_user_message, 'content'):
                for content in input_user_message.content:
                    if hasattr(content, 'text'):
                        user_message += content.text
            
            # Get session ID from thread
            session_id = thread.id if hasattr(thread, 'id') else str(id(thread))

            # === RATE LIMITING CHECK (Task T020) ===
            rate_limiter = get_rate_limiter()
            is_allowed, rate_limit_details = rate_limiter.consume(session_id)

            if not is_allowed:
                # Rate limit exceeded - return error message via ChatKit
                retry_after = rate_limit_details.get("retry_after", 60)
                reset_at = rate_limit_details.get("reset_at", "soon")

                rate_limit_message = (
                    f"**Rate Limit Exceeded**\n\n"
                    f"You've reached the maximum of {rate_limit_details['limit']} queries per hour.\n\n"
                    f"• Try again in: {retry_after} seconds\n"
                    f"• Limit resets at: {reset_at}\n\n"
                    f"_This limit helps ensure fair access for all users._"
                )

                # Create error response using ChatKit streaming
                error_item_id = f"msg-error-{uuid.uuid4().hex[:12]}"
                error_message_item = AssistantMessageItem(
                    id=error_item_id,
                    type="message",
                    role="assistant",
                    status="completed",
                    content=[AssistantMessageContent(type="text", text=rate_limit_message)]
                )

                yield ThreadItemAddedEvent(
                    type="thread.item.added",
                    item=error_message_item
                )
                yield ThreadItemDoneEvent(
                    type="thread.item.done",
                    item=error_message_item
                )

                logger.warning(f"Rate limit exceeded for session {session_id}: retry after {retry_after}s")
                return

            # Log rate limit status (include warning if approaching limit)
            if rate_limit_details.get("warning"):
                logger.info(
                    f"ChatKit session {session_id} approaching rate limit: "
                    f"{rate_limit_details['remaining']}/{rate_limit_details['limit']} remaining"
                )

            # === DEBUG: Print query details to console ===
            import sys
            print("\n" + "="*60)
            print("[CHATKIT ENDPOINT] IMS AI Analytics Assistant - Query Received")
            print("="*60)
            print(f"  Endpoint: /agent/chatkit (ChatKit Protocol)")
            print(f"  User ID: {self._current_user_id}")
            print(f"  Session ID: {session_id}")
            print(f"  Query: {user_message}")
            print("="*60 + "\n")
            sys.stdout.flush()

            logger.info(f"ChatKit processing message for session {session_id} (user_id={self._current_user_id}): {user_message[:50] if user_message else 'empty'}...")

            if not user_message:
                response_text = "I didn't receive any message. How can I help you?"
            else:
                # IMPORTANT: Prepend user_id context to ensure data isolation
                # The agent will use this user_id when calling MCP tools
                if self._current_user_id is not None:
                    user_message = f"[SYSTEM CONTEXT: Current logged-in user_id={self._current_user_id}. You MUST include user_id={self._current_user_id} in ALL tool calls for data isolation.]\n\nUser query: {user_message}"
                else:
                    logger.warning(f"No user_id available for session {session_id} - data will not be user-scoped!")
                # Track timing for thinking display
                start_time = time.time()
                
                # Generate thinking steps based on message
                thinking_steps = self._generate_thinking_steps(user_message)
                
                # === NATIVE CHATKIT THINKING UI ===
                # Step 1: Add thinking task with LOADING status (shows animated lightbulb)
                initial_thought = ThoughtTask(
                    type="thought",
                    status_indicator="loading",  # Shows animated thinking indicator!
                    title=thinking_steps[0] if thinking_steps else "Analyzing request...",
                    content=""
                )
                yield WorkflowTaskAdded(
                    type="workflow.task.added",
                    task_index=0,
                    task=initial_thought
                )
                
                # Step 2: Update thinking content progressively (keep loading status)
                accumulated_reasoning = ""
                for i, step in enumerate(thinking_steps):
                    step_time = time.time() - start_time
                    accumulated_reasoning += f"• {step}\n"
                    
                    # Update the thought task with accumulated reasoning
                    updated_thought = ThoughtTask(
                        type="thought",
                        status_indicator="loading",  # Keep showing thinking animation
                        title=step,
                        content=accumulated_reasoning
                    )
                    yield WorkflowTaskUpdated(
                        type="workflow.task.updated",
                        task_index=0,
                        task=updated_thought
                    )
                    
                    # Small delay to show streaming effect
                    await asyncio.sleep(0.15)
                
                # Process message with agent - pass user_id for auto-injection into tool calls
                result = await agent.process_message(
                    session_id=session_id,
                    user_message=user_message,
                    user_id=self._current_user_id,  # For data isolation
                )
                
                # Calculate total thinking time
                total_time = time.time() - start_time
                
                # Extract response and tool calls
                response_text = result.get("response", "I'm sorry, I couldn't process that request.")
                tool_calls = result.get("tool_calls", [])
                
                # Add tool usage to reasoning
                if tool_calls:
                    accumulated_reasoning += "\nTools used:\n"
                    for tc in tool_calls:
                        tool_name = tc.get("tool", "unknown")
                        accumulated_reasoning += f"  → {tool_name}\n"
                
                # Final thought update with COMPLETE status and timing
                final_thought = ThoughtTask(
                    type="thought",
                    status_indicator="complete",  # Shows completed indicator
                    title=f"Thought for {total_time:.0f}s",
                    content=accumulated_reasoning
                )
                yield WorkflowTaskUpdated(
                    type="workflow.task.updated",
                    task_index=0,
                    task=final_thought
                )
            
            # Generate message ID
            msg_id = f"msg-{uuid.uuid4().hex[:12]}"
            
            # Stream the actual response
            yield AssistantMessageContentPartTextDelta(
                type="assistant_message.content_part.text_delta",
                content_index=0,
                delta=response_text
            )
            
            # Signal content part is done
            yield AssistantMessageContentPartDone(
                type="assistant_message.content_part.done",
                content_index=0,
                content=AssistantMessageContent(
                    type="output_text",
                    text=response_text,
                    annotations=[]
                )
            )
            
            # Yield thread.item.added event
            assistant_msg = AssistantMessageItem(
                id=msg_id,
                thread_id=thread.id,
                created_at=datetime.now().isoformat(),
                type="assistant_message",
                content=[AssistantMessageContent(
                    type="output_text",
                    text=response_text,
                    annotations=[]
                )]
            )
            yield ThreadItemAddedEvent(type="thread.item.added", item=assistant_msg)
            
            # Finally, yield thread.item.done event
            yield ThreadItemDoneEvent(type="thread.item.done", item=assistant_msg)
                
        except Exception as e:
            logger.error(f"Error in ChatKit respond: {e}", exc_info=True)
            # Yield error response
            error_text = f"I'm sorry, an error occurred: {str(e)}"
            yield AssistantMessageContentPartTextDelta(
                type="assistant_message.content_part.text_delta",
                content_index=0,
                delta=error_text
            )
    
    def _generate_thinking_steps(self, user_message: str) -> list[str]:
        """
        Generate thinking steps based on the user's message.
        
        These steps show the reasoning process in the UI.
        """
        steps = []
        message_lower = user_message.lower()
        
        # Analyze message intent
        steps.append("📝 Analyzing your request...")
        
        # Check for inventory-related keywords
        if any(word in message_lower for word in ['inventory', 'stock', 'item', 'product', 'add', 'update', 'delete']):
            steps.append("📦 Detecting inventory operation...")
            if 'add' in message_lower:
                steps.append("➕ Preparing to add new item...")
            elif 'update' in message_lower or 'edit' in message_lower:
                steps.append("✏️ Preparing to update item...")
            elif 'delete' in message_lower or 'remove' in message_lower:
                steps.append("🗑️ Preparing to remove item...")
            elif 'show' in message_lower or 'list' in message_lower or 'check' in message_lower:
                steps.append("🔍 Fetching inventory data...")
        
        # Check for billing-related keywords
        elif any(word in message_lower for word in ['bill', 'invoice', 'payment', 'create bill', 'generate']):
            steps.append("🧾 Detecting billing operation...")
            if 'create' in message_lower or 'generate' in message_lower:
                steps.append("📝 Preparing new bill...")
            elif 'show' in message_lower or 'list' in message_lower:
                steps.append("🔍 Fetching billing records...")
        
        # Check for help/general
        elif any(word in message_lower for word in ['help', 'what can', 'how to', 'guide']):
            steps.append("ℹ️ Preparing help information...")
        
        # Default reasoning
        else:
            steps.append("🧠 Processing your request...")
        
        # Final step
        steps.append("⚡ Executing with AI agent...")
        
        return steps


# Global instances
_store = SimpleStore()
_server = IMSChatKitServer(_store)


@router.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """
    Main ChatKit endpoint.

    Handles all ChatKit protocol requests (messages, threads, etc.)
    Uses the official ChatKit server protocol.
    Extracts user_id from Authorization header for data isolation.
    """
    try:
        body = await request.body()
        logger.info(f"ChatKit request received: {body[:200]}...")

        # Extract user_id from Authorization header for data isolation
        user_id = await extract_user_id_from_request(request)
        _server.set_user_id(user_id)
        logger.info(f"ChatKit endpoint: user_id={user_id}")

        # Get context from request
        context = {
            "headers": dict(request.headers),
            "user_id": user_id,  # Include user_id in context
        }

        # Process with ChatKit server
        result = await _server.process(body, context)
        
        # Handle different result types
        if hasattr(result, '__aiter__'):
            # StreamingResult - events are already SSE formatted bytes
            async def generate():
                try:
                    async for event in result:
                        # Events from ChatKit server are already SSE formatted bytes
                        if isinstance(event, bytes):
                            yield event
                        elif isinstance(event, str):
                            yield event.encode('utf-8')
                        elif hasattr(event, 'model_dump_json'):
                            yield f"data: {event.model_dump_json()}\n\n".encode('utf-8')
                        elif hasattr(event, 'model_dump'):
                            yield f"data: {json.dumps(event.model_dump())}\n\n".encode('utf-8')
                        else:
                            data = json.dumps(event) if isinstance(event, dict) else str(event)
                            yield f"data: {data}\n\n".encode('utf-8')
                except Exception as e:
                    logger.error(f"Streaming error: {e}", exc_info=True)
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n".encode('utf-8')
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        elif hasattr(result, 'model_dump_json'):
            return Response(
                content=result.model_dump_json(),
                media_type="application/json"
            )
        elif hasattr(result, 'model_dump'):
            return Response(
                content=json.dumps(result.model_dump()),
                media_type="application/json"
            )
        else:
            return Response(
                content=json.dumps(result) if isinstance(result, dict) else str(result),
                media_type="application/json"
            )
            
    except Exception as e:
        logger.error(f"ChatKit endpoint error: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@router.get("/chatkit/health")
async def chatkit_health():
    """Health check for ChatKit server."""
    return {
        "status": "ok",
        "service": "ChatKit Server",
        "version": "1.0.0"
    }


@router.get("/chatkit/rate-limit/{session_id}")
async def get_rate_limit_status(session_id: str):
    """
    Get rate limit status for a session (Task T020).

    Returns current usage and remaining quota.
    Frontend can use this to display rate limit warnings.
    """
    rate_limiter = get_rate_limiter()
    usage = rate_limiter.get_usage(session_id)
    return {
        "status": "ok",
        "rate_limit": usage
    }


# === SIMPLE CHAT ENDPOINT (Fallback for when ChatKit CDN is unavailable) ===

class SimpleChatMessage(BaseModel):
    role: str
    content: str

class SimpleChatRequest(BaseModel):
    session_id: str
    message: str
    history: Optional[List[SimpleChatMessage]] = []
    user_id: Optional[int] = None  # Optional user_id for data isolation


@router.post("/chat")
async def simple_chat_endpoint(request_body: SimpleChatRequest, request: Request):
    """
    Simple chat endpoint for fallback UI.

    Accepts a plain JSON request with session_id and message,
    returns a JSON response with the assistant's reply.

    Extracts user_id from Authorization header for data isolation.
    This is a simpler alternative to the ChatKit protocol endpoint.
    """
    try:
        # Extract user_id from auth header or request body
        user_id = await extract_user_id_from_request(request)
        if user_id is None and request_body.user_id is not None:
            user_id = request_body.user_id

        # Rate limiting check
        rate_limiter = get_rate_limiter()
        is_allowed, rate_limit_details = rate_limiter.consume(request_body.session_id)

        if not is_allowed:
            retry_after = rate_limit_details.get("retry_after", 60)
            return JSONResponse(
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "retry_after": retry_after,
                    "rate_limit": rate_limit_details
                },
                status_code=429
            )

        # Get the agent
        agent = await _server._get_agent()

        # Build conversation history for context
        history_text = ""
        if request_body.history:
            for msg in request_body.history[-5:]:  # Last 5 messages for context
                role = "User" if msg.role == "user" else "Assistant"
                history_text += f"{role}: {msg.content}\n"

        # Process with agent - prepend user_id context for data isolation
        full_prompt = request_body.message
        if user_id is not None:
            full_prompt = f"[SYSTEM CONTEXT: Current logged-in user_id={user_id}. You MUST include user_id={user_id} in ALL tool calls for data isolation.]\n\nUser query: {request_body.message}"
        else:
            logger.warning(f"No user_id available for session {request_body.session_id} - data will not be user-scoped!")

        if history_text:
            full_prompt = f"Previous conversation:\n{history_text}\n\n{full_prompt}"

        # === DEBUG: Print query details to console ===
        import sys
        print("\n" + "="*60)
        print("[SIMPLE CHAT ENDPOINT] IMS AI Analytics Assistant - Query Received")
        print("="*60)
        print(f"  Endpoint: /agent/chat (Simple Chat)")
        print(f"  User ID: {user_id}")
        print(f"  Session ID: {request_body.session_id}")
        print(f"  Query: {request_body.message}")
        print("="*60 + "\n")
        sys.stdout.flush()

        logger.info(f"Simple chat processing for session {request_body.session_id} (user_id={user_id}): {request_body.message[:50]}...")

        # Use process_message instead of run - pass user_id for data isolation
        result = await agent.process_message(
            session_id=request_body.session_id,
            user_message=full_prompt,
            user_id=user_id,  # For data isolation
        )
        response_text = result.get("response", "I couldn't process that request.")

        return {
            "content": response_text,
            "session_id": request_body.session_id,
            "rate_limit": rate_limiter.get_usage(request_body.session_id)
        }

    except Exception as e:
        logger.error(f"Simple chat error: {e}", exc_info=True)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
