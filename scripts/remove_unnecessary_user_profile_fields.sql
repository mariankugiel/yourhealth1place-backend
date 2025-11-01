-- Script to remove unnecessary fields from user_profiles table in Supabase
-- Run this script in your Supabase SQL editor

-- Remove unnecessary columns from user_profiles table
-- These columns are redundant or not needed for user profiles

-- Remove cellphone column (redundant with phone_number)
ALTER TABLE user_profiles DROP COLUMN IF EXISTS cellphone;

-- Remove cellphone_country_code column (redundant with phone_country_code)
ALTER TABLE user_profiles DROP COLUMN IF EXISTS cellphone_country_code;

-- Remove location column (not needed for user profiles)
ALTER TABLE user_profiles DROP COLUMN IF EXISTS location;

-- Remove country column (not needed for user profiles)
ALTER TABLE user_profiles DROP COLUMN IF EXISTS country;

-- Add avatar field for user profile pictures
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);

-- Add role field for user roles (patient, doctor, admin)
-- Store in lowercase to match Supabase convention
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'patient';

-- Verify the changes by checking the table structure
-- You can run this query to see the remaining columns:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'user_profiles' 
-- ORDER BY ordinal_position;

-- Expected remaining columns after cleanup:
-- - id (primary key)
-- - user_id (foreign key to auth.users)
-- - full_name
-- - date_of_birth
-- - phone_number
-- - phone_country_code
-- - address
-- - avatar_url (NEW - user profile picture)
-- - role (NEW - user role: patient, doctor, admin)
-- - emergency_contact_name
-- - emergency_contact_phone
-- - emergency_contact_relationship
-- - emergency_contact_country_code
-- - gender
-- - height
-- - weight
-- - waist_diameter
-- - blood_type
-- - allergies
-- - current_medications
-- - emergency_medical_info
-- - onboarding_completed
-- - onboarding_skipped
-- - onboarding_skipped_at
-- - is_new_user
-- - created_at
-- - updated_at
