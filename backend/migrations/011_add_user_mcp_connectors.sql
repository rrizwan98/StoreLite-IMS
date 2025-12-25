-- Migration: 011_add_user_mcp_connectors
-- Feature: 008-user-mcp-connectors
-- Description: Add tables for User MCP Connectors feature
-- Date: 2025-12-23

-- ============================================================================
-- Create user_tool_status table
-- Tracks user's connection status for system tools (Gmail, Analytics, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_tool_status (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tool_id VARCHAR(50) NOT NULL,  -- 'gmail', 'analytics', 'export'
    is_connected BOOLEAN DEFAULT FALSE NOT NULL,
    config JSONB,  -- Tool-specific configuration
    connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Unique constraint: one entry per user per tool
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_tool ON user_tool_status(user_id, tool_id);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_tool_status_user ON user_tool_status(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tool_status_tool ON user_tool_status(tool_id);


-- ============================================================================
-- Create user_mcp_connections table
-- Stores user's custom MCP server connections with encrypted credentials
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_mcp_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    server_url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(50) DEFAULT 'none' NOT NULL,
    auth_config TEXT,  -- Encrypted JSON (Fernet)
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    discovered_tools JSONB,  -- Cached list of tools from server
    last_verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraint: auth_type must be one of: 'none', 'oauth', 'api_key'
    CONSTRAINT auth_type_check CHECK (auth_type IN ('none', 'oauth', 'api_key'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_mcp_connections_user ON user_mcp_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mcp_connections_active ON user_mcp_connections(user_id, is_active);


-- ============================================================================
-- Verification queries (run these to verify migration success)
-- ============================================================================
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('user_tool_status', 'user_mcp_connections');
