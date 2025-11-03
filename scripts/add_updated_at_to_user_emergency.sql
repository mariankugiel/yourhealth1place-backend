-- Add missing timestamp columns to existing user_emergency table
-- Run this script if your table already exists but is missing created_at or updated_at

-- Add created_at column if it doesn't exist
ALTER TABLE user_emergency ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add updated_at column if it doesn't exist
ALTER TABLE user_emergency ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add default values for timestamp columns on existing rows
UPDATE user_emergency SET created_at = NOW() WHERE created_at IS NULL;
UPDATE user_emergency SET updated_at = NOW() WHERE updated_at IS NULL;

-- Create index on user_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_user_emergency_user_id ON user_emergency(user_id);

-- Verify the columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'user_emergency' 
ORDER BY ordinal_position;

