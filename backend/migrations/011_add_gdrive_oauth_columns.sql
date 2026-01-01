-- Migration: Add Google Drive OAuth columns to user_connections table
-- Phase: Google Drive Integration
-- Date: 2025-12-28

-- Google Drive OAuth2 tokens (encrypted)
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gdrive_access_token TEXT;
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gdrive_refresh_token TEXT;
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gdrive_token_expiry TIMESTAMP;
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gdrive_email VARCHAR(255);
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gdrive_connected_at TIMESTAMP;
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gdrive_scopes JSONB;

-- Add comments for documentation
COMMENT ON COLUMN user_connections.gdrive_access_token IS 'Encrypted Google Drive OAuth2 access token';
COMMENT ON COLUMN user_connections.gdrive_refresh_token IS 'Encrypted Google Drive OAuth2 refresh token';
COMMENT ON COLUMN user_connections.gdrive_token_expiry IS 'When the access token expires';
COMMENT ON COLUMN user_connections.gdrive_email IS 'Connected Google account email';
COMMENT ON COLUMN user_connections.gdrive_connected_at IS 'When Google Drive was connected';
COMMENT ON COLUMN user_connections.gdrive_scopes IS 'Granted OAuth2 scopes';
