@echo off
REM Development server startup script for Windows

echo Starting IMS FastAPI Backend...
echo Server will run on http://127.0.0.1:8001
echo Swagger UI: http://127.0.0.1:8001/docs
echo.

python -m uvicorn app.main:app --reload --port 8001 --host 127.0.0.1
pause
