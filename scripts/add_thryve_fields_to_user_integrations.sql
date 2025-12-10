-- Add Thryve integration fields to user_integrations table in Supabase
-- Run this script in your Supabase SQL editor

-- Add thryve_access_token column (stores the Thryve access token/end_user_id)
ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS thryve_access_token TEXT;

-- Add thryve_connections JSONB column (stores connection status for each data source)
ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS thryve_connections JSONB DEFAULT '{}'::jsonb;

-- Add individual Thryve data source boolean fields for quick access
ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS fitbit BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS garmin BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS polar BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS withings BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS strava BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS omron_connect BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS suunto BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS oura BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS beurer BOOLEAN DEFAULT false;

ALTER TABLE user_integrations 
ADD COLUMN IF NOT EXISTS huawei_health BOOLEAN DEFAULT false;

-- Add comments
COMMENT ON COLUMN user_integrations.thryve_access_token IS 'Thryve access token (end_user_id) for the user. This is set when user connects their first Thryve data source.';
COMMENT ON COLUMN user_integrations.thryve_connections IS 'JSON object storing connection status for each Thryve data source. Format: {"dataSourceId": {"connected": true/false, "connected_at": "ISO date", "disconnected_at": "ISO date"}}';

-- Create index on thryve_access_token for faster lookups (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_user_integrations_thryve_access_token 
ON user_integrations(thryve_access_token) 
WHERE thryve_access_token IS NOT NULL;

-- Create GIN index on thryve_connections JSONB for efficient JSON queries (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_user_integrations_thryve_connections 
ON user_integrations USING GIN (thryve_connections);

