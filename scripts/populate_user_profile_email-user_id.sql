-- Populate email field in user_profiles table from auth.users
-- Run this script if your user_profiles table uses user_id (not id)
-- Use populate_user_profile_email.sql if your table uses id

-- Add email column to user_profiles if it doesn't exist
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Populate email from auth.users for existing user_profiles that don't have email set
-- Note: user_profiles.user_id references auth.users.id
UPDATE user_profiles
SET email = auth.users.email
FROM auth.users
WHERE user_profiles.user_id = auth.users.id
  AND (user_profiles.email IS NULL OR user_profiles.email = '');

-- Verify the changes by checking which users have email populated
-- You can run this query to verify:
-- SELECT user_id, email, full_name 
-- FROM user_profiles 
-- WHERE email IS NOT NULL 
-- LIMIT 10;

-- Optional: Create a trigger to automatically populate email for new users
CREATE OR REPLACE FUNCTION populate_user_profile_email()
RETURNS TRIGGER AS $$
BEGIN
  -- Insert email when new user is created
  -- Since user_profiles.user_id references auth.users.id, we need to match on user_id
  INSERT INTO user_profiles (user_id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (user_id) DO UPDATE
  SET email = NEW.email
  WHERE user_profiles.email IS NULL OR user_profiles.email = '';
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_insert_populate_email ON auth.users;
CREATE TRIGGER on_auth_user_insert_populate_email
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION populate_user_profile_email();

-- Create trigger on auth.users update to sync email changes
DROP TRIGGER IF EXISTS on_auth_user_update_sync_email ON auth.users;
CREATE TRIGGER on_auth_user_update_sync_email
  AFTER UPDATE OF email ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION populate_user_profile_email();

-- Add comment to explain the triggers
COMMENT ON FUNCTION populate_user_profile_email() IS 'Automatically syncs email from auth.users to user_profiles when users sign up or change email';

