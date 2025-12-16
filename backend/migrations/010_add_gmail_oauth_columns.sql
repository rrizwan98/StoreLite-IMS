-- Migration: Add Gmail OAuth2 columns to user_connections table
-- Phase: 10 - Gmail Tool Integration
-- Date: 2025-12-16
--
-- Description:
--   Adds columns for storing Gmail OAuth2 tokens and settings.
--   These enable the Gmail Send Email tool in the Schema Agent.
--
-- Run with:
--   python migrations/run_migration.py 010_add_gmail_oauth_columns.sql
--   OR
--   psql -U your_user -d your_database -f migrations/010_add_gmail_oauth_columns.sql

-- Gmail OAuth2 tokens (encrypted)
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_access_token TEXT;
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_refresh_token TEXT;

-- Token expiry for auto-refresh
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_token_expiry TIMESTAMP;

-- Connected Gmail account email
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_email VARCHAR(255);

-- When Gmail was connected
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_connected_at TIMESTAMP;

-- Default recipient email for sending
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_recipient_email VARCHAR(255);

-- Granted OAuth2 scopes (for future scope expansion)
ALTER TABLE user_connections ADD COLUMN IF NOT EXISTS gmail_scopes JSONB;

-- Add comments for documentation
COMMENT ON COLUMN user_connections.gmail_access_token IS 'Encrypted Gmail OAuth2 access token';
COMMENT ON COLUMN user_connections.gmail_refresh_token IS 'Encrypted Gmail OAuth2 refresh token';
COMMENT ON COLUMN user_connections.gmail_token_expiry IS 'Access token expiry timestamp';
COMMENT ON COLUMN user_connections.gmail_email IS 'Connected Gmail account email address';
COMMENT ON COLUMN user_connections.gmail_connected_at IS 'When Gmail was connected';
COMMENT ON COLUMN user_connections.gmail_recipient_email IS 'Default recipient for agent emails';
COMMENT ON COLUMN user_connections.gmail_scopes IS 'Granted OAuth2 scopes array';
