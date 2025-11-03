-- Create user_shared_access table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_shared_access;

-- Create user_shared_access table
CREATE TABLE user_shared_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    health_professionals JSONB,
    family_friends JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_user_shared_access_user_id ON user_shared_access(user_id);

-- Disable RLS for development (re-enable in production with proper policies)
ALTER TABLE user_shared_access DISABLE ROW LEVEL SECURITY;

-- Add comment to table
COMMENT ON TABLE user_shared_access IS 'Stores user shared access permissions for health professionals and family/friends';

