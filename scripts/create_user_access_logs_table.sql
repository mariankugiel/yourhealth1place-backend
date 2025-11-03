-- Create user_access_logs table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_access_logs;

-- Create user_access_logs table
CREATE TABLE user_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    date VARCHAR(255),
    authorized BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_user_access_logs_user_id ON user_access_logs(user_id);
CREATE INDEX idx_user_access_logs_created_at ON user_access_logs(created_at DESC);
CREATE INDEX idx_user_access_logs_authorized ON user_access_logs(authorized);

-- Disable RLS for development (re-enable in production with proper policies)
ALTER TABLE user_access_logs DISABLE ROW LEVEL SECURITY;

-- Add comment to table
COMMENT ON TABLE user_access_logs IS 'Stores access logs for user permissions and security';

