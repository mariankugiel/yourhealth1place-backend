-- Create user_data_sharing table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_data_sharing;

-- Create user_data_sharing table
CREATE TABLE user_data_sharing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    share_health_data BOOLEAN DEFAULT false,
    share_with_other_providers BOOLEAN DEFAULT false,
    share_with_researchers BOOLEAN DEFAULT false,
    share_with_insurance BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_user_data_sharing_user_id ON user_data_sharing(user_id);

-- Disable RLS for development (re-enable in production with proper policies)
ALTER TABLE user_data_sharing DISABLE ROW LEVEL SECURITY;

-- Add comment to table
COMMENT ON TABLE user_data_sharing IS 'Stores data sharing preferences for users';

