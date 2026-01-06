# Hugging Face Spaces Dockerfile for Schema Agent
# Platform: Hugging Face Spaces (Free Tier)
# SDK: Docker

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install postgres-mcp globally (required for MCP server)
RUN pip install postgres-mcp

# Copy requirements first for caching
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    httpx>=0.24.0 \
    sqlalchemy>=2.0.0 \
    asyncpg>=0.29.0 \
    psycopg2-binary>=2.9.0 \
    aiosqlite>=0.19.0 \
    python-dotenv>=1.0.0 \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    openai>=1.3.0 \
    openai-agents>=0.6.2 \
    litellm>=1.76.1 \
    fastmcp>=1.0 \
    python-json-logger>=2.0.7 \
    typing-extensions>=4.0.0 \
    python-jose[cryptography]>=3.3.0 \
    passlib[bcrypt]>=1.7.4 \
    python-multipart>=0.0.6 \
    google-auth>=2.25.0 \
    google-auth-oauthlib>=1.2.0 \
    google-api-python-client>=2.111.0 \
    cryptography>=41.0.0 \
    google-genai>=1.0.0 \
    markdown2>=2.4.0 \
    pandas>=2.0.0 \
    openpyxl>=3.1.0 \
    pdfplumber>=0.10.0 \
    Pillow>=10.0.0 \
    aiofiles>=23.0.0 \
    chatkit

# Copy application code
COPY app/ ./app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/data

# Expose port (HF Spaces uses 7860)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application
CMD ["uvicorn", "app.main_hf:app", "--host", "0.0.0.0", "--port", "7860"]
