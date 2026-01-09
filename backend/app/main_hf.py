"""
Hugging Face Spaces Entry Point - Schema Agent API

This is the production entry point for Hugging Face Spaces deployment.
Includes Schema Agent, Authentication, and all connectors.

Features:
- User Authentication (signup, login, logout)
- Schema Query Agent with all 7 tools
- OAuth Connectors (Notion, Gmail, GDrive, RetellAI)
- File Upload & Analysis
- Full API with JWT authentication
"""

import logging
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Schema Query Agent API",
    description="""
    AI-powered natural language database query agent with full authentication.

    **Features:**
    - User authentication (signup, login, JWT tokens)
    - Natural language to SQL conversion
    - 7 integrated tools: WebSearch, FileSearch, Analytics, Gmail, GDrive, Notion, RetellAI
    - File upload and analysis (PDF, Excel, CSV, Images)
    - OAuth connectors for external services

    **Usage:**
    1. Sign up/Login via `/auth/signup` or `/auth/login`
    2. Connect your database via `/schema-agent/connect`
    3. Query using natural language via `/schema-agent/chatkit`

    Deployed on Hugging Face Spaces.
    """,
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware (allow all for public API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Exception Handlers ============

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc) if os.getenv("DEBUG") else "An unexpected error occurred.",
        },
    )


# ============ Lifecycle Events ============

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Schema Agent API on Hugging Face Spaces")

    # Log environment info
    logger.info(f"LLM Provider: {os.getenv('LLM_PROVIDER', 'gemini')}")
    logger.info(f"HTTP MCP Enabled: {os.getenv('USE_HTTP_MCP', 'true')}")

    # Initialize database (SQLite for HF, user provides their own PostgreSQL)
    try:
        from app.database import init_db
        await init_db()
        logger.info("Local database initialized")
    except Exception as e:
        logger.warning(f"Database init warning: {e}")

    # Initialize task scheduler (APScheduler)
    try:
        from app.services.scheduler_service import initialize_scheduler
        from app.database import get_database_url
        database_url = get_database_url()
        await initialize_scheduler(database_url)
        logger.info("Task scheduler initialized successfully")
    except Exception as e:
        logger.warning(f"Task scheduler initialization warning: {e}")
        logger.info("Scheduler features may be unavailable")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Schema Agent API")

    # Shutdown task scheduler
    try:
        from app.services.scheduler_service import shutdown_scheduler
        await shutdown_scheduler()
        logger.info("Task scheduler shut down")
    except Exception as e:
        logger.warning(f"Task scheduler shutdown warning: {e}")

    # Cleanup HTTP MCP servers
    try:
        from app.services.mcp_server_manager import shutdown_mcp_server_manager
        await shutdown_mcp_server_manager()
        logger.info("HTTP MCP servers cleaned up")
    except Exception as e:
        logger.warning(f"MCP cleanup warning: {e}")

    # Cleanup database
    try:
        from app.database import cleanup
        await cleanup()
    except Exception as e:
        logger.warning(f"Database cleanup warning: {e}")


# ============ Health Check ============

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for HF Spaces"""
    return {
        "status": "ok",
        "service": "Schema Query Agent",
        "platform": "Hugging Face Spaces",
        "version": "0.2.0"
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Schema Query Agent API",
        "version": "0.2.0",
        "platform": "Hugging Face Spaces",
        "docs": "/docs",
        "features": [
            "Natural Language Database Queries",
            "7 Integrated Tools (WebSearch, FileSearch, Analytics, Gmail, GDrive, Notion, RetellAI)",
            "File Upload & Analysis",
            "OAuth Connectors"
        ],
        "endpoints": {
            "connect": "/schema-agent/connect",
            "query": "/schema-agent/chatkit",
            "health": "/health"
        }
    }


# ============ Include Routers ============

# Authentication (Required for login/signup)
from app.routers import auth
app.include_router(auth.router)

# Schema Query Agent (Main feature)
from app.routers import schema_agent
app.include_router(schema_agent.router)

# User MCP Connectors
from app.routers import tools, connectors, oauth_connectors
app.include_router(tools.router)
app.include_router(connectors.router)
app.include_router(oauth_connectors.router)

# OAuth Connectors (Notion, GDrive, Gmail)
from app.routers import notion_mcp_oauth, gdrive_oauth, gmail_oauth
app.include_router(notion_mcp_oauth.router)
app.include_router(gdrive_oauth.router)
app.include_router(gmail_oauth.router)

# Retell AI Voice Connector
from app.routers import retellai_mcp
app.include_router(retellai_mcp.router)

# File Upload & Processing
from app.routers import files
app.include_router(files.router)

# Gemini File Search
from app.routers import gemini_file_search
app.include_router(gemini_file_search.router)

# User Settings
from app.routers import user_settings
app.include_router(user_settings.router)

# Task Scheduler (Feature 014 - Scheduled task automation)
from app.routers import scheduler
app.include_router(scheduler.router)

logger.info("Schema Agent API initialized - Ready for queries!")
