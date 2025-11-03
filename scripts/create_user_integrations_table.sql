-- Create user_integrations table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_integrations;

-- Create user_integrations table
CREATE TABLE user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Wearable device integrations
    google_fit BOOLEAN DEFAULT false,
    fitbit BOOLEAN DEFAULT false,
    garmin BOOLEAN DEFAULT false,
    apple_health BOOLEAN DEFAULT false,
    withings BOOLEAN DEFAULT false,
    oura BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_user_integrations_user_id ON user_integrations(user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE user_integrations ENABLE ROW LEVEL SECURITY;

-- Disable RLS for development (re-enable in production with proper policies)
ALTER TABLE user_integrations DISABLE ROW LEVEL SECURITY;

-- Add comment to table
COMMENT ON TABLE user_integrations IS 'Stores wearable device integration preferences for users';

