-- Add preference fields to user_profiles table in Supabase
-- Run this script in your Supabase SQL editor

-- Add theme field for user theme preference
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS theme VARCHAR(20);

-- Add language field for user language preference
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS language VARCHAR(20);

-- Add timezone field for user timezone preference
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS timezone VARCHAR(100);

-- Verify the changes by checking the table structure
-- You can run this query to see the updated columns:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'user_profiles' 
-- ORDER BY ordinal_position;

