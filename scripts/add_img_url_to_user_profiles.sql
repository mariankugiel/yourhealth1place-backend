-- Add img_url column to user_profiles table in Supabase
-- This stores the signed URL for the user's profile picture
-- Run this script in your Supabase SQL editor

-- Add img_url column if it doesn't exist
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS img_url VARCHAR(500);

-- Optional: If you want to migrate existing avatar_url to img_url
-- UPDATE user_profiles SET img_url = avatar_url WHERE img_url IS NULL AND avatar_url IS NOT NULL;

-- Verify the column was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_profiles' AND column_name = 'img_url';

