-- Migration: Add email column to user_mcp_connections table
-- Date: 2024-12-29
-- Description: Separate email from name field for cleaner data storage

-- Add email column (nullable)
ALTER TABLE user_mcp_connections
ADD COLUMN IF NOT EXISTS email VARCHAR(255) NULL;

-- Update existing records: Extract email from name and update both columns
-- Pattern: "Gmail - user@gmail.com" -> name="Gmail", email="user@gmail.com"
UPDATE user_mcp_connections
SET
    email = SUBSTRING(name FROM '\s*-\s*([^\s@]+@[^\s@]+\.[^\s@]+)$'),
    name = TRIM(REGEXP_REPLACE(name, '\s*-\s*[^\s@]+@[^\s@]+\.[^\s@]+$', ''))
WHERE name ~ '\s*-\s*[^\s@]+@[^\s@]+\.[^\s@]+$';

-- Add comment for documentation
COMMENT ON COLUMN user_mcp_connections.email IS 'Connected account email address (e.g., user@gmail.com)';
COMMENT ON COLUMN user_mcp_connections.name IS 'Clean connector name without email (e.g., Gmail, Google Drive)';
