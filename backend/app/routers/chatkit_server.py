"""
Pure OpenAI ChatKit Server Integration

Uses the official openai-chatkit Python SDK (chatkit.server.ChatKitServer)
Connects ChatKit frontend to the IMS agent backend.
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
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
)

from app.agents import OpenAIAgent, MCPClient, ConfirmationFlow
from app.database import get_db

logger = logging.getLogger(__name__)

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
    """
    
    def __init__(self, store: Store):
        super().__init__(store)
        self._agent: OpenAIAgent | None = None
    
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
        
        This is the main entry point for ChatKit messages.
        """
        import uuid
        
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
            
            logger.info(f"ChatKit processing message for session {session_id}: {user_message[:50] if user_message else 'empty'}...")
            
            if not user_message:
                response_text = "I didn't receive any message. How can I help you?"
            else:
                # Process message with agent
                result = await agent.process_message(
                    session_id=session_id,
                    user_message=user_message,
                )
                response_text = result.get("response", "I'm sorry, I couldn't process that request.")
            
            # Generate message ID
            msg_id = f"msg-{uuid.uuid4().hex[:12]}"
            
            # Stream the response as text deltas
            # First, yield a text delta for the content
            yield AssistantMessageContentPartTextDelta(
                type="assistant_message.content_part.text_delta",
                content_index=0,
                delta=response_text
            )
            
            # Then signal content part is done with proper AssistantMessageContent
            yield AssistantMessageContentPartDone(
                type="assistant_message.content_part.done",
                content_index=0,
                content=AssistantMessageContent(
                    type="output_text",
                    text=response_text,
                    annotations=[]
                )
            )
            
            # First, yield thread.item.added event
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


# Global instances
_store = SimpleStore()
_server = IMSChatKitServer(_store)


@router.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """
    Main ChatKit endpoint.
    
    Handles all ChatKit protocol requests (messages, threads, etc.)
    Uses the official ChatKit server protocol.
    """
    try:
        body = await request.body()
        logger.info(f"ChatKit request received: {body[:200]}...")
        
        # Get context from request
        context = {
            "headers": dict(request.headers),
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
