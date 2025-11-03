-- Create user_privacy table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_privacy;

-- Create user_privacy table
CREATE TABLE user_privacy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Data sharing preferences
    share_anonymized_data BOOLEAN DEFAULT true,
    share_analytics BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_user_privacy_user_id ON user_privacy(user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE user_privacy ENABLE ROW LEVEL SECURITY;

-- Disable RLS for development (re-enable in production with proper policies)
ALTER TABLE user_privacy DISABLE ROW LEVEL SECURITY;

-- Add comment to table
COMMENT ON TABLE user_privacy IS 'Stores user privacy and data sharing preferences';

