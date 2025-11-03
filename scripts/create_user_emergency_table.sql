-- Create user_emergency table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_emergency;

-- Create user_emergency table
CREATE TABLE user_emergency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    contacts JSONB,
    allergies TEXT,
    health_problems TEXT,
    pregnancy_status TEXT,
    organ_donor BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_user_emergency_user_id ON user_emergency(user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE user_emergency ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own emergency data
CREATE POLICY "Users can view their own emergency data"
    ON user_emergency FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy: Users can insert their own emergency data
CREATE POLICY "Users can insert their own emergency data"
    ON user_emergency FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can update their own emergency data
CREATE POLICY "Users can update their own emergency data"
    ON user_emergency FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can delete their own emergency data
CREATE POLICY "Users can delete their own emergency data"
    ON user_emergency FOR DELETE
    USING (auth.uid() = user_id);

-- Add comment to table
COMMENT ON TABLE user_emergency IS 'Stores emergency contact information and medical data for users';

