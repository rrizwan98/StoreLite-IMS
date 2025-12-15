-- Migration: Add Schema Agent columns to user_connections table
-- Date: 2024-12-15
-- Description: Adds columns required for Schema Query Agent (Phase 9)

-- Add connection_mode column
ALTER TABLE user_connections
ADD COLUMN IF NOT EXISTS connection_mode VARCHAR(50) DEFAULT 'full_ims';

-- Add schema_metadata column (JSONB for PostgreSQL)
ALTER TABLE user_connections
ADD COLUMN IF NOT EXISTS schema_metadata JSONB;

-- Add schema_last_updated column
ALTER TABLE user_connections
ADD COLUMN IF NOT EXISTS schema_last_updated TIMESTAMP;

-- Add allowed_schemas column (JSONB array)
ALTER TABLE user_connections
ADD COLUMN IF NOT EXISTS allowed_schemas JSONB DEFAULT '["public"]'::jsonb;

-- Add comment for documentation
COMMENT ON COLUMN user_connections.connection_mode IS 'Connection mode: full_ims or schema_query';
COMMENT ON COLUMN user_connections.schema_metadata IS 'Cached schema metadata for schema_query mode';
COMMENT ON COLUMN user_connections.schema_last_updated IS 'When schema was last discovered';
COMMENT ON COLUMN user_connections.allowed_schemas IS 'PostgreSQL schemas allowed for querying';
