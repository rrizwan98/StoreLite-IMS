#!/bin/bash
# Development server startup script

echo "Starting IMS FastAPI Backend..."
echo "Server will run on http://127.0.0.1:8001"
echo "Swagger UI: http://127.0.0.1:8001/docs"
echo ""

uvicorn app.main:app --reload --port 8001 --host 127.0.0.1
