-- Complete fix for user_emergency table
-- This adds missing columns and fixes RLS for service role access
-- Run this script in your Supabase SQL editor

-- Step 1: Add missing columns if they don't exist
ALTER TABLE user_emergency ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE user_emergency ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE user_emergency ADD COLUMN IF NOT EXISTS medications TEXT;

-- Step 2: Set default values for existing rows
UPDATE user_emergency SET created_at = NOW() WHERE created_at IS NULL;
UPDATE user_emergency SET updated_at = NOW() WHERE updated_at IS NULL;

-- Step 3: Create index on user_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_user_emergency_user_id ON user_emergency(user_id);

-- Step 4: Fix RLS - disable for development (re-enable in production with proper policies)
ALTER TABLE user_emergency DISABLE ROW LEVEL SECURITY;

-- Step 5: Verify the table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'user_emergency' 
ORDER BY ordinal_position;

-- Expected output:
-- id, user_id, contacts, allergies, medications, health_problems, pregnancy_status, organ_donor, created_at, updated_at

