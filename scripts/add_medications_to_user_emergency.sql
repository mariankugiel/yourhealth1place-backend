-- Add medications column to user_emergency table
-- Run this script in your Supabase SQL editor

-- Add medications column if it doesn't exist
ALTER TABLE user_emergency ADD COLUMN IF NOT EXISTS medications TEXT;

-- Add comment
COMMENT ON COLUMN user_emergency.medications IS 'List of current medications and dosages for emergency use';

-- Verify the column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'user_emergency' 
ORDER BY ordinal_position;

