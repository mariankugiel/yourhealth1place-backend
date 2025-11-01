-- Rollback script to restore removed columns from user_profiles table
-- Use this only if you need to restore the removed columns

-- Add back cellphone column
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS cellphone VARCHAR(20);

-- Add back cellphone_country_code column
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS cellphone_country_code VARCHAR(5);

-- Add back location column
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS location TEXT;

-- Add back country column
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS country VARCHAR(100);

-- Note: avatar_url and role columns are kept as they are beneficial additions
-- If you need to remove them, uncomment the lines below:
-- ALTER TABLE user_profiles DROP COLUMN IF EXISTS avatar_url;
-- ALTER TABLE user_profiles DROP COLUMN IF EXISTS role;

-- Verify the rollback
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'cellphone'
        ) THEN 'cellphone column restored'
        ELSE 'cellphone column not found'
    END as cellphone_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'cellphone_country_code'
        ) THEN 'cellphone_country_code column restored'
        ELSE 'cellphone_country_code column not found'
    END as cellphone_country_code_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'location'
        ) THEN 'location column restored'
        ELSE 'location column not found'
    END as location_status,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_profiles' AND column_name = 'country'
        ) THEN 'country column restored'
        ELSE 'country column not found'
    END as country_status;
