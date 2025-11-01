-- Verification script to check user_profiles table structure
-- Run this before and after the cleanup script to verify changes

-- Check current table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'user_profiles' 
ORDER BY ordinal_position;

-- Check if unnecessary columns still exist
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'cellphone'
        ) THEN 'cellphone column still exists'
        ELSE 'cellphone column removed successfully'
    END as cellphone_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'cellphone_country_code'
        ) THEN 'cellphone_country_code column still exists'
        ELSE 'cellphone_country_code column removed successfully'
    END as cellphone_country_code_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'location'
        ) THEN 'location column still exists'
        ELSE 'location column removed successfully'
    END as location_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'country'
        ) THEN 'country column still exists'
        ELSE 'country column removed successfully'
    END as country_status;

-- Check if essential columns exist
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'phone_number'
        ) THEN 'phone_number column exists'
        ELSE 'phone_number column missing'
    END as phone_number_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'phone_country_code'
        ) THEN 'phone_country_code column exists'
        ELSE 'phone_country_code column missing'
    END as phone_country_code_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'avatar_url'
        ) THEN 'avatar_url column exists'
        ELSE 'avatar_url column missing'
    END as avatar_url_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'role'
        ) THEN 'role column exists'
        ELSE 'role column missing'
    END as role_status;
