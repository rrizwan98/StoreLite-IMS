"""
FastAPI application entry point with error handlers and router setup
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.exceptions import (
    ValidationError,
    BusinessLogicError,
    NotFoundError,
    DatabaseError,
)
from app.database import init_db, cleanup, verify_connection

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IMS REST API",
    description="Inventory Management System REST API (Phase 2)",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Exception Handlers ============


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors (422 status)"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": exc.message,
            "fields": exc.fields,
        },
    )


@app.exception_handler(BusinessLogicError)
async def business_logic_error_handler(request: Request, exc: BusinessLogicError):
    """Handle business logic errors (400 status)"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Business logic error",
            "details": exc.message,
        },
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors (404 status)"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "details": exc.message,
        },
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors (500 status)"""
    logger.error(f"Database error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": "A database error occurred. Please try again later.",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions (500 status)"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": "An unexpected error occurred. Please try again later.",
        },
    )


# ============ Lifecycle Events ============


@app.on_event("startup")
async def startup_event():
    """Initialize database and verify connection on app startup"""
    logger.info("Starting up FastAPI application")
    try:
        # Initialize database tables
        await init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {str(e)}")
        logger.info("Using SQLite database for development")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown"""
    logger.info("Shutting down FastAPI application")
    await cleanup()
    logger.info("Cleanup complete")


# ============ Health Check ============


@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "IMS REST API"}


# ============ Root Endpoint ============


@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "IMS REST API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


# ============ Include Routers ============

from app.routers import inventory, billing, agent, chatkit_server

app.include_router(inventory.router)
app.include_router(billing.router)
app.include_router(agent.router)
app.include_router(chatkit_server.router)

logger.info("FastAPI application initialized")


